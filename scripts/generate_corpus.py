#!/usr/bin/env python3
"""Generate synthetic knowledge-base corpus for support/incident Co-Pilot.

Produces 100+ documents (runbooks, FAQs, incident summaries, product docs)
of ~5–6 pages each (~1,500–2,000 words), written to data/kb/ as .txt and .pdf.

Usage:
    python scripts/generate_corpus.py [--output-dir DATA/KB] [--count 110]
"""

import argparse
import random
import re
from pathlib import Path
from typing import Iterator

# Target ~300 words per page; 5–6 pages => 1,500–2,000 words per doc
WORDS_PER_PAGE = 300
PAGES_PER_DOC = (5, 6)
MIN_WORDS_PER_DOC = WORDS_PER_PAGE * PAGES_PER_DOC[0]
MAX_WORDS_PER_DOC = WORDS_PER_PAGE * PAGES_PER_DOC[1]


def _word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def _ensure_word_count(text: str, min_w: int, max_w: int) -> str:
    words = text.split()
    if len(words) <= max_w:
        return text
    return " ".join(words[: max_w + 1])


# --- Templates (paragraphs) for runbooks, FAQs, incidents, product docs ---

RUNBOOK_INTROS = [
    "This runbook describes the procedure for {topic} in the {product} environment.",
    "Use this runbook when {trigger}. It applies to {product} versions {version} and later.",
    "This document provides step-by-step instructions for {topic} to restore or maintain service.",
]

RUNBOOK_SECTIONS = [
    "Prerequisites: Ensure you have access to the {system} dashboard and the role {role}. "
    "Verify that the incident ticket is assigned and the severity is set correctly.",
    "Step 1: Log into the {system} console and navigate to the section indicated in the alert. "
    "Note the timestamp and any error codes displayed (e.g. {code}).",
    "Step 2: Run the diagnostic command: `{command}`. Capture the full output to a file for later analysis. "
    "If the command times out, increase the timeout value in the config.",
    "Step 3: Compare the output with the baseline stored in the knowledge base. "
    "Look for deviations in {metric} or {metric2}.",
    "Step 4: If the issue matches known pattern {pattern}, apply the mitigation from section 4. "
    "Otherwise, escalate to the on-call engineer with the captured logs.",
    "Step 5: After applying the fix, run the health check endpoint: `{endpoint}`. "
    "Confirm that the response code is 200 and latency is within SLA.",
    "Rollback: If the change causes regression, revert using `{rollback_cmd}` and notify the team in {channel}.",
]

FAQ_ITEMS = [
    ("Why does {product} show error {code}?", "Error {code} usually indicates {cause}. "
     "Check the {component} logs and ensure {condition}. If the issue persists, run the diagnostic in the runbook."),
    ("How do I reset the {feature} configuration?", "Navigate to Settings > {feature} and click Reset. "
     "This restores defaults. Custom mappings will be lost; export them first if needed."),
    ("What is the SLA for {service}?", "The SLA for {service} is {sla}. "
     "Incidents are triaged within {time} and resolved according to severity."),
    ("How do I add a new user to {product}?", "Use the Admin API: POST /users with the required fields. "
     "See the API documentation for rate limits and required permissions."),
    ("Why is my dashboard not loading?", "Dashboard load failures are often due to {cause}. "
     "Clear cache, check network tab for failed requests, and verify your role has access to the dashboard."),
]

INCIDENT_TEMPLATES = [
    "Incident Summary: On {date}, {service} experienced {issue}. Impact: {impact}. "
    "Duration: {duration}. Root cause: {cause}. Resolution: {resolution}.",
    "Post-incident summary for incident {id}. Service {service} was affected between {start} and {end}. "
    "Root cause was identified as {cause}. Mitigation involved {action}. Follow-up: {followup}.",
]

PRODUCT_INTROS = [
    "{product} is the {description} used by support and operations teams.",
    "This document describes the {feature} feature of {product} and how to use it for common tasks.",
]

PRODUCT_SECTIONS = [
    "Overview: {feature} allows you to {capability}. It is available in the {product} console under the {menu} menu.",
    "Configuration: Set the following options in the config file or UI: {options}. "
    "Default values are suitable for most environments; tune only if you need higher throughput.",
    "Limits: Maximum {limit} per request. Rate limits apply; see the API documentation for current quotas.",
    "Troubleshooting: If you see {error}, check {step}. Common causes include {cause1} and {cause2}.",
]


def _pick(items: list, rng: random.Random) -> str:
    return rng.choice(items)


def _runbook_content(rng: random.Random, product: str, topic: str) -> str:
    topics = ["restoring service after an outage", "running diagnostics", "applying a hotfix", "scaling the cluster"]
    triggers = ["alerts fire for high latency", "error rate exceeds threshold", "a deployment fails"]
    systems = ["monitoring", "orchestration", "billing", "api-gateway"]
    codes = ["ERR_502", "ERR_TIMEOUT", "ERR_QUOTA", "ERR_AUTH"]
    commands = ["diagnose --env prod", "health-check --full", "audit-logs --since 1h"]
    metrics = ["response time", "error rate", "queue depth", "CPU usage"]
    patterns = ["P001", "P002", "P003"]
    endpoints = ["/health", "/ready", "/live"]
    rollback_cmds = ["rollback last", "revert --deploy id", "restore from backup"]
    channels = ["#incidents", "#ops", "PagerDuty"]

    intro = _pick(RUNBOOK_INTROS, rng).format(
        topic=topic or _pick(topics, rng),
        product=product,
        trigger=_pick(triggers, rng),
        version=rng.choice(["1.x", "2.x", "3.x"]),
    )
    parts = [intro]
    used = set()
    while _word_count(" ".join(parts)) < MIN_WORDS_PER_DOC:
        s = _pick(RUNBOOK_SECTIONS, rng)
        s = s.format(
            system=_pick(systems, rng),
            role=rng.choice(["admin", "operator", "viewer"]),
            code=_pick(codes, rng),
            command=_pick(commands, rng),
            metric=_pick(metrics, rng),
            metric2=_pick(metrics, rng),
            pattern=_pick(patterns, rng),
            endpoint=_pick(endpoints, rng),
            rollback_cmd=_pick(rollback_cmds, rng),
            channel=_pick(channels, rng),
        )
        parts.append(s)
    return _ensure_word_count("\n\n".join(parts), MIN_WORDS_PER_DOC, MAX_WORDS_PER_DOC)


def _faq_content(rng: random.Random, product: str) -> str:
    products = [product, "the API", "the dashboard", "billing"]
    codes = ["E100", "E201", "E302", "E404"]
    causes = ["a misconfiguration", "rate limiting", "an expired token", "network timeout"]
    components = ["auth", "gateway", "database", "cache"]
    conditions = ["credentials are valid", "the service is up", "DNS resolves"]
    features = ["notifications", "SSO", "webhooks", "export"]
    services = ["API", "dashboard", "data pipeline"]
    slas = ["99.9%", "99.5%", "99.0%"]
    times = ["15 minutes", "30 minutes", "1 hour"]

    parts = [f"FAQ for {product}. Frequently asked questions and answers.\n"]
    seen = set()
    while _word_count(" ".join(parts)) < MIN_WORDS_PER_DOC:
        q, a = _pick(FAQ_ITEMS, rng)
        key = (q, a)
        if key in seen:
            continue
        seen.add(key)
        q = q.format(product=_pick(products, rng), code=_pick(codes, rng), feature=_pick(features, rng), service=_pick(services, rng))
        a = a.format(
            code=_pick(codes, rng),
            cause=_pick(causes, rng),
            component=_pick(components, rng),
            condition=_pick(conditions, rng),
            feature=_pick(features, rng),
            service=_pick(services, rng),
            sla=_pick(slas, rng),
            time=_pick(times, rng),
        )
        parts.append(f"Q: {q}\nA: {a}\n")
    return _ensure_word_count("\n".join(parts), MIN_WORDS_PER_DOC, MAX_WORDS_PER_DOC)


def _incident_content(rng: random.Random, service: str) -> str:
    dates = ["2024-01-15", "2024-02-20", "2024-03-10", "2024-04-05"]
    issues = ["elevated error rates", "increased latency", "partial outage", "deployment failure"]
    impacts = ["some users affected", "EU region impacted", "read-only mode", "degraded performance"]
    durations = ["45 minutes", "2 hours", "1 hour 15 minutes"]
    causes = ["a bad deployment", "database failover", "third-party API outage", "config change"]
    resolutions = ["rollback and fix", "failover to standby", "revert config and redeploy"]
    ids = [f"INC-{rng.randint(1000, 9999)}" for _ in range(5)]
    actions = ["rollback", "cache clear", "config revert"]
    followups = ["add monitoring", "update runbook", "post-mortem scheduled"]

    parts = []
    while _word_count(" ".join(parts)) < MIN_WORDS_PER_DOC:
        t = _pick(INCIDENT_TEMPLATES, rng)
        t = t.format(
            date=_pick(dates, rng),
            service=service,
            issue=_pick(issues, rng),
            impact=_pick(impacts, rng),
            duration=_pick(durations, rng),
            cause=_pick(causes, rng),
            resolution=_pick(resolutions, rng),
            id=_pick(ids, rng),
            start=_pick(dates, rng) + " 14:00 UTC",
            end=_pick(dates, rng) + " 16:00 UTC",
            action=_pick(actions, rng),
            followup=_pick(followups, rng),
        )
        parts.append(t)
    return _ensure_word_count("\n\n".join(parts), MIN_WORDS_PER_DOC, MAX_WORDS_PER_DOC)


def _product_content(rng: random.Random, product: str, feature: str) -> str:
    descriptions = ["central monitoring and alerting platform", "API gateway and rate-limiting service", "dashboard and reporting tool"]
    capabilities = ["view metrics and create alerts", "manage API keys and quotas", "export reports and run ad-hoc queries"]
    menus = ["Settings", "Admin", "Analytics"]
    options = ["timeout, retries, cache_ttl", "log_level, sampling_rate", "theme, language"]
    limits = ["1000 requests", "100 MB payload", "50 concurrent connections"]
    errors = ["Connection refused", "Timeout", "Quota exceeded"]
    steps = ["connectivity and firewall rules", "the service status page", "your plan limits"]
    causes = ["network issues", "misconfiguration", "rate limits"]

    intro = _pick(PRODUCT_INTROS, rng).format(
        product=product,
        description=_pick(descriptions, rng),
        feature=feature or _pick(["alerts", "API", "dashboard"], rng),
    )
    parts = [intro]
    while _word_count(" ".join(parts)) < MIN_WORDS_PER_DOC:
        s = _pick(PRODUCT_SECTIONS, rng)
        s = s.format(
            feature=feature or "this feature",
            capability=_pick(capabilities, rng),
            product=product,
            menu=_pick(menus, rng),
            options=_pick(options, rng),
            limit=_pick(limits, rng),
            error=_pick(errors, rng),
            step=_pick(steps, rng),
            cause1=_pick(causes, rng),
            cause2=_pick(causes, rng),
        )
        parts.append(s)
    return _ensure_word_count("\n\n".join(parts), MIN_WORDS_PER_DOC, MAX_WORDS_PER_DOC)


def _generate_documents(count: int, seed: int) -> Iterator[tuple[str, str, str]]:
    """Yield (doc_type, filename_stem, content) for count documents."""
    rng = random.Random(seed)
    products = ["Support Co-Pilot", "API Gateway", "Billing Service", "Dashboard", "Alerting"]
    services = ["Payment Service", "Auth Service", "API Gateway", "Data Pipeline", "Dashboard"]
    doc_types = ["runbook", "faq", "incident", "product"]
    weights = [0.25, 0.25, 0.25, 0.25]

    for i in range(count):
        doc_type = rng.choices(doc_types, weights=weights)[0]
        idx = i + 1
        stem = f"{doc_type}_{idx:03d}"

        if doc_type == "runbook":
            product = _pick(products, rng)
            content = _runbook_content(rng, product, "")
        elif doc_type == "faq":
            product = _pick(products, rng)
            content = _faq_content(rng, product)
        elif doc_type == "incident":
            service = _pick(services, rng)
            content = _incident_content(rng, service)
        else:
            product = _pick(products, rng)
            feature = _pick(["Alerts", "API", "Dashboard", "Export"], rng)
            content = _product_content(rng, product, feature)

        yield doc_type, stem, content


def _write_txt(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _write_pdf(path: Path, content: str) -> bool:
    """Write content to PDF. Returns True if written, False if fpdf2 not installed."""
    try:
        from fpdf import FPDF
    except ImportError:
        return False

    pdf = FPDF()
    pdf.set_auto_page_break(True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    for block in content.split("\n\n"):
        block = block.replace("\n", " ").strip()
        if block:
            pdf.multi_cell(0, 6, txt=block)
            pdf.ln(3)
    pdf.output(str(path))
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic KB corpus (100+ docs, 5–6 pages each).")
    parser.add_argument("--output-dir", type=Path, default=Path("data/kb"), help="Output directory for generated files")
    parser.add_argument("--count", type=int, default=110, help="Number of documents to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--txt-only", action="store_true", help="Generate only .txt (no PDF)")
    args = parser.parse_args()

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    txt_count = 0
    pdf_count = 0
    for doc_type, stem, content in _generate_documents(args.count, args.seed):
        txt_path = out / f"{stem}.txt"
        _write_txt(txt_path, content)
        txt_count += 1

        if not args.txt_only:
            pdf_path = out / f"{stem}.pdf"
            if _write_pdf(pdf_path, content):
                pdf_count += 1

    print(f"Generated {txt_count} .txt and {pdf_count} .pdf files in {out.absolute()}")


if __name__ == "__main__":
    main()
