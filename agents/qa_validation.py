"""QA/Validation Agent: Automated black-box testing of Customer Support Agent.

This agent validates the behavior of the Customer Support Agent using black-box testing.
It does NOT read dataset files directly and tests the agent through its API/interface.

Execution Flow:
1. Load test cases from JSON
2. For each test case, invoke the Customer Support Agent
3. Capture full structured response
4. Run mandatory assertions
5. Generate JSON and console reports
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    """Single QA test case."""

    id: str
    query: str
    expected_behavior: str  # "answer", "no_answer", "escalate"
    description: str = ""
    expected_guardrail: str | None = None
    should_use_rag: bool | None = None
    should_use_memory: bool | None = None


@dataclass
class AgentResponse:
    """Captured response from Customer Support Agent."""

    final_answer: str
    final_action: str  # "answer", "no_answer", "escalate"
    rag_docs_used: int
    memory_used: bool
    guardrails_triggered: bool
    agents_ran: list[str]
    confidence_score: float | None = None
    intent_result: dict[str, Any] | None = None
    guardrails_result: dict[str, Any] | None = None
    retrieval_result: list[dict[str, Any]] | None = None
    memory_result: dict[str, Any] | None = None


@dataclass
class AssertionResult:
    """Result of a single assertion."""

    rule_name: str
    passed: bool
    message: str
    expected: Any = None
    actual: Any = None


@dataclass
class TestResult:
    """Result of a single test case execution."""

    test_id: str
    query: str
    expected_behavior: str
    passed: bool
    failed_rules: list[str] = field(default_factory=list)
    assertion_results: list[AssertionResult] = field(default_factory=list)
    actual_response: dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0


@dataclass
class QASummary:
    """Summary of all test results."""

    total_tests: int
    passed: int
    failed: int
    breakdown: dict[str, int] = field(default_factory=dict)
    execution_time_ms: float = 0.0


class QAAgent:
    """QA/Validation Agent for Customer Support Agent."""

    def __init__(self, api_url: str | None = None, use_api: bool = False):
        """Initialize QA Agent.

        Args:
            api_url: URL of the Customer Support Agent API (if use_api=True)
            use_api: If True, use HTTP API. If False, use direct graph invocation (black-box)
        """
        self.api_url = api_url or "http://localhost:8000"
        self.use_api = use_api
        self._graph = None

    def _get_graph(self):
        """Get graph instance (lazy load, only if not using API)."""
        if self.use_api:
            return None
        if self._graph is None:
            from agents.graph import get_graph
            self._graph = get_graph()
        return self._graph

    def invoke_agent(self, query: str, session_id: str = "qa-test") -> AgentResponse:
        """Invoke Customer Support Agent and capture full response.

        This is black-box testing - we don't read dataset files, only invoke the agent.
        """
        import time

        start_time = time.time()

        if self.use_api:
            # Use HTTP API (true black-box)
            import requests

            try:
                response = requests.post(
                    f"{self.api_url}/api/chat",
                    json={"query": query, "session_id": session_id},
                    timeout=60,
                )
                response.raise_for_status()
                data = response.json()
                # API response doesn't include all details, so we need to infer
                return self._parse_api_response(data, query)
            except Exception as e:
                logger.error("API call failed: %s", e)
                raise

        else:
            # Use direct graph invocation (still black-box - we don't read dataset files)
            graph = self._get_graph()
            if graph is None:
                raise RuntimeError("Graph not available")

            # Track which agents ran by monitoring state updates
            agents_ran = []
            state = graph.invoke(
                {"query": query, "session_id": session_id},
                config={"configurable": {"thread_id": session_id}},
            )

            # Determine which agents ran based on state
            if state.get("normalized_query"):
                agents_ran.append("IngestionAgent")
            if state.get("intent_result"):
                agents_ran.append("IntentAgent")
            if state.get("retrieval_result"):
                agents_ran.append("RAGAgent")
            if state.get("memory_result"):
                agents_ran.append("MemoryAgent")
            if state.get("reasoning_result"):
                agents_ran.append("ReasoningAgent")
            if state.get("draft_response"):
                agents_ran.append("SynthesisAgent")
            if state.get("guardrails_result"):
                agents_ran.append("GuardrailsAgent")

            # Extract response details
            retrieval_result = state.get("retrieval_result") or []
            rag_docs_used = len(retrieval_result) if retrieval_result else 0

            memory_result = state.get("memory_result") or {}
            memory_used = bool(
                memory_result.get("working")
                or memory_result.get("episodic")
                or memory_result.get("semantic")
            )

            guardrails_result = state.get("guardrails_result") or {}
            guardrails_triggered = bool(guardrails_result)

            escalate = state.get("escalate", False)
            final_response = state.get("final_response", "")

            # Determine final action
            if escalate:
                final_action = "escalate"
            elif not final_response or self._is_no_answer_response(final_response):
                final_action = "no_answer"
            else:
                final_action = "answer"

            execution_time = (time.time() - start_time) * 1000

            return AgentResponse(
                final_answer=final_response,
                final_action=final_action,
                rag_docs_used=rag_docs_used,
                memory_used=memory_used,
                guardrails_triggered=guardrails_triggered,
                agents_ran=agents_ran,
                confidence_score=None,  # Not available in current state
                intent_result=state.get("intent_result"),
                guardrails_result=guardrails_result,
                retrieval_result=retrieval_result,
                memory_result=memory_result,
            )

    def _parse_api_response(self, data: dict[str, Any], query: str) -> AgentResponse:
        """Parse API response (limited info available from API)."""
        final_response = data.get("final_response", "")
        escalate = data.get("escalate", False)

        # Infer from response
        if escalate:
            final_action = "escalate"
        elif not final_response or self._is_no_answer_response(final_response):
            final_action = "no_answer"
        else:
            final_action = "answer"

        # API doesn't provide these details, so we infer
        # For true black-box API testing, we'd need API to return more info
        guardrails_result = data.get("guardrails_result") or {}
        guardrails_triggered = bool(guardrails_result)

        # We can't know RAG/memory usage from API response alone
        # This is a limitation of API-only testing
        return AgentResponse(
            final_answer=final_response,
            final_action=final_action,
            rag_docs_used=0,  # Unknown from API
            memory_used=False,  # Unknown from API
            guardrails_triggered=guardrails_triggered,
            agents_ran=[],  # Unknown from API
            guardrails_result=guardrails_result,
            intent_result=data.get("intent_result"),
        )

    def _is_no_answer_response(self, response: str) -> bool:
        """Check if response indicates 'no answer'."""
        response_lower = response.lower()
        no_answer_phrases = [
            "i don't have information",
            "i don't know",
            "outside my knowledge base",
            "not in my knowledge base",
            "i can't help",
            "outside our scope",
            "not related to",
        ]
        return any(phrase in response_lower for phrase in no_answer_phrases)

    def run_assertions(
        self, test_case: TestCase, response: AgentResponse
    ) -> list[AssertionResult]:
        """Run all mandatory assertions on the response."""
        results = []

        # 1. RAG Grounding
        if test_case.expected_behavior == "answer":
            passed = response.rag_docs_used > 0
            results.append(
                AssertionResult(
                    rule_name="RAG_Grounding_Answer",
                    passed=passed,
                    message=f"Expected RAG docs > 0, got {response.rag_docs_used}",
                    expected="> 0",
                    actual=response.rag_docs_used,
                )
            )
        elif test_case.expected_behavior == "no_answer":
            passed = response.rag_docs_used == 0
            results.append(
                AssertionResult(
                    rule_name="RAG_Grounding_NoAnswer",
                    passed=passed,
                    message=f"Expected RAG docs == 0, got {response.rag_docs_used}",
                    expected=0,
                    actual=response.rag_docs_used,
                )
            )

        # 2. Hallucination Prevention
        if response.rag_docs_used == 0:
            passed = (
                response.final_action == "no_answer"
                and self._is_no_answer_response(response.final_answer)
            )
            results.append(
                AssertionResult(
                    rule_name="Hallucination_Prevention",
                    passed=passed,
                    message=f"When RAG docs == 0, must return no_answer with uncertainty message. Got action={response.final_action}",
                    expected="no_answer with uncertainty message",
                    actual=f"{response.final_action}: {response.final_answer[:100]}",
                )
            )

        # 3. Out-of-Scope Enforcement
        # This is validated by expected_behavior == "no_answer" for out-of-scope queries
        if test_case.expected_behavior == "no_answer":
            passed = response.final_action == "no_answer"
            results.append(
                AssertionResult(
                    rule_name="Out_of_Scope_Enforcement",
                    passed=passed,
                    message=f"Out-of-scope query must return no_answer. Got {response.final_action}",
                    expected="no_answer",
                    actual=response.final_action,
                )
            )

        # 4. Guardrails & Escalation
        if test_case.expected_guardrail:
            passed = response.guardrails_triggered and response.final_action == "escalate"
            results.append(
                AssertionResult(
                    rule_name="Guardrails_Escalation",
                    passed=passed,
                    message=f"Expected guardrail trigger and escalate. Got guardrails={response.guardrails_triggered}, action={response.final_action}",
                    expected="guardrails_triggered=True, action=escalate",
                    actual=f"guardrails={response.guardrails_triggered}, action={response.final_action}",
                )
            )

        # 5. Memory Usage
        if test_case.should_use_memory is True:
            passed = response.memory_used is True
            results.append(
                AssertionResult(
                    rule_name="Memory_Usage",
                    passed=passed,
                    message=f"Expected memory_used=True, got {response.memory_used}",
                    expected=True,
                    actual=response.memory_used,
                )
            )

        # 6. Agentic Planning (for complex queries)
        # Check if required agents ran
        if test_case.expected_behavior == "answer" and test_case.should_use_rag:
            required_agents = ["IntentAgent", "RAGAgent"]
            passed = all(agent in response.agents_ran for agent in required_agents)
            results.append(
                AssertionResult(
                    rule_name="Agentic_Planning",
                    passed=passed,
                    message=f"Expected agents {required_agents} to run. Got {response.agents_ran}",
                    expected=required_agents,
                    actual=response.agents_ran,
                )
            )

        # 7. Expected Behavior Match
        passed = response.final_action == test_case.expected_behavior
        results.append(
            AssertionResult(
                rule_name="Expected_Behavior_Match",
                passed=passed,
                message=f"Expected {test_case.expected_behavior}, got {response.final_action}",
                expected=test_case.expected_behavior,
                actual=response.final_action,
            )
        )

        return results

    def run_test_case(self, test_case: TestCase) -> TestResult:
        """Run a single test case and return result."""
        import time

        start_time = time.time()
        logger.info("Running test case %s: %s", test_case.id, test_case.query[:60])

        try:
            response = self.invoke_agent(test_case.query)
            assertion_results = self.run_assertions(test_case, response)

            failed_rules = [
                r.rule_name for r in assertion_results if not r.passed
            ]
            passed = len(failed_rules) == 0

            execution_time = (time.time() - start_time) * 1000

            return TestResult(
                test_id=test_case.id,
                query=test_case.query,
                expected_behavior=test_case.expected_behavior,
                passed=passed,
                failed_rules=failed_rules,
                assertion_results=assertion_results,
                actual_response={
                    "final_answer": response.final_answer[:500],
                    "final_action": response.final_action,
                    "rag_docs_used": response.rag_docs_used,
                    "memory_used": response.memory_used,
                    "guardrails_triggered": response.guardrails_triggered,
                    "agents_ran": response.agents_ran,
                },
                execution_time_ms=execution_time,
            )
        except Exception as e:
            logger.error("Test case %s failed with error: %s", test_case.id, e)
            execution_time = (time.time() - start_time) * 1000
            return TestResult(
                test_id=test_case.id,
                query=test_case.query,
                expected_behavior=test_case.expected_behavior,
                passed=False,
                failed_rules=["EXECUTION_ERROR"],
                assertion_results=[
                    AssertionResult(
                        rule_name="EXECUTION_ERROR",
                        passed=False,
                        message=str(e),
                    )
                ],
                execution_time_ms=execution_time,
            )

    def load_test_cases(self, test_cases_path: str | Path) -> list[TestCase]:
        """Load test cases from JSON file."""
        path = Path(test_cases_path)
        if not path.exists():
            raise FileNotFoundError(f"Test cases file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        test_cases = []
        for tc_data in data.get("test_cases", []):
            test_cases.append(
                TestCase(
                    id=tc_data["id"],
                    query=tc_data["query"],
                    expected_behavior=tc_data["expected_behavior"],
                    description=tc_data.get("description", ""),
                    expected_guardrail=tc_data.get("expected_guardrail"),
                    should_use_rag=tc_data.get("should_use_rag"),
                    should_use_memory=tc_data.get("should_use_memory"),
                )
            )

        return test_cases

    def run_all_tests(
        self, test_cases_path: str | Path, output_dir: str | Path | None = None
    ) -> tuple[list[TestResult], QASummary]:
        """Run all test cases and generate reports."""
        import time

        start_time = time.time()
        test_cases = self.load_test_cases(test_cases_path)
        results = []

        logger.info("Running %d test cases...", len(test_cases))

        for test_case in test_cases:
            result = self.run_test_case(test_case)
            results.append(result)

        execution_time = (time.time() - start_time) * 1000

        # Generate summary
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed

        # Breakdown by failure type
        breakdown = {
            "hallucination": 0,
            "rag_missing": 0,
            "out_of_scope_violation": 0,
            "guardrail_failure": 0,
            "memory_failure": 0,
            "execution_error": 0,
        }

        for result in results:
            if not result.passed:
                if "EXECUTION_ERROR" in result.failed_rules:
                    breakdown["execution_error"] += 1
                elif "Hallucination_Prevention" in result.failed_rules:
                    breakdown["hallucination"] += 1
                elif "RAG_Grounding" in str(result.failed_rules):
                    breakdown["rag_missing"] += 1
                elif "Out_of_Scope" in str(result.failed_rules):
                    breakdown["out_of_scope_violation"] += 1
                elif "Guardrails" in str(result.failed_rules):
                    breakdown["guardrail_failure"] += 1
                elif "Memory" in str(result.failed_rules):
                    breakdown["memory_failure"] += 1

        summary = QASummary(
            total_tests=len(results),
            passed=passed,
            failed=failed,
            breakdown=breakdown,
            execution_time_ms=execution_time,
        )

        # Generate reports
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            self._generate_json_report(results, summary, output_dir)
            self._generate_console_report(results, summary)

        return results, summary

    def _generate_json_report(
        self, results: list[TestResult], summary: QASummary, output_dir: Path
    ):
        """Generate machine-readable JSON report."""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_tests": summary.total_tests,
                "passed": summary.passed,
                "failed": summary.failed,
                "breakdown": summary.breakdown,
                "execution_time_ms": summary.execution_time_ms,
            },
            "test_results": [
                {
                    "test_id": r.test_id,
                    "query": r.query,
                    "expected_behavior": r.expected_behavior,
                    "passed": r.passed,
                    "failed_rules": r.failed_rules,
                    "assertion_results": [
                        {
                            "rule_name": a.rule_name,
                            "passed": a.passed,
                            "message": a.message,
                            "expected": str(a.expected) if a.expected is not None else None,
                            "actual": str(a.actual) if a.actual is not None else None,
                        }
                        for a in r.assertion_results
                    ],
                    "actual_response": r.actual_response,
                    "execution_time_ms": r.execution_time_ms,
                }
                for r in results
            ],
        }

        report_path = output_dir / f"qa_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info("JSON report saved to: %s", report_path)

    def _generate_console_report(
        self, results: list[TestResult], summary: QASummary
    ):
        """Generate human-readable console report."""
        print("\n" + "=" * 80)
        print("QA VALIDATION REPORT")
        print("=" * 80)
        print(f"\nTimestamp: {datetime.utcnow().isoformat()}")
        print(f"\nSummary:")
        print(f"  Total Tests: {summary.total_tests}")
        print(f"  Passed: {summary.passed} ({summary.passed/summary.total_tests*100:.1f}%)")
        print(f"  Failed: {summary.failed} ({summary.failed/summary.total_tests*100:.1f}%)")
        print(f"  Execution Time: {summary.execution_time_ms:.0f} ms")

        if summary.breakdown:
            print(f"\nFailure Breakdown:")
            for failure_type, count in summary.breakdown.items():
                if count > 0:
                    print(f"  - {failure_type}: {count}")

        print(f"\n{'=' * 80}")
        print("DETAILED RESULTS")
        print("=" * 80)

        for result in results:
            status = "✓ PASS" if result.passed else "✗ FAIL"
            print(f"\n[{status}] {result.test_id}")
            print(f"  Query: {result.query[:70]}...")
            print(f"  Expected: {result.expected_behavior}")
            print(f"  Actual: {result.actual_response.get('final_action', 'unknown')}")
            print(f"  Execution Time: {result.execution_time_ms:.0f} ms")

            if not result.passed:
                print(f"  Failed Rules: {', '.join(result.failed_rules)}")
                for assertion in result.assertion_results:
                    if not assertion.passed:
                        print(f"    - {assertion.rule_name}: {assertion.message}")

        print("\n" + "=" * 80)


def main():
    """Main entry point for QA Agent."""
    import argparse

    parser = argparse.ArgumentParser(description="QA/Validation Agent for Customer Support Agent")
    parser.add_argument(
        "--test-cases",
        type=str,
        default="tests/qa/test_cases.json",
        help="Path to test cases JSON file",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="tests/qa/reports",
        help="Directory for output reports",
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default=None,
        help="API URL (if using API mode)",
    )
    parser.add_argument(
        "--use-api",
        action="store_true",
        help="Use HTTP API instead of direct graph invocation",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run QA Agent
    qa_agent = QAAgent(api_url=args.api_url, use_api=args.use_api)
    results, summary = qa_agent.run_all_tests(args.test_cases, args.output_dir)

    # Exit with error code if tests failed
    sys.exit(0 if summary.failed == 0 else 1)


if __name__ == "__main__":
    main()
