/**
 * Live stream: agent steps and tool calls in animated cards with expand/collapse.
 */

import { useState } from "react";
import type { AgentStreamEvent, ToolCallPayload } from "../types/stream";
import type { WebSocketStatus } from "../hooks/useWebSocket";
import {
  IconShieldCheck,
  IconCompass,
  IconTarget,
  IconSearch,
  IconDatabase,
  IconLightbulb,
  IconSparkles,
  IconShield,
  IconWrench,
  IconCheck,
  IconAlert,
  IconX,
  IconZap,
} from "./Icons";
import { IconLoader } from "./Icons";

const PIPELINE_ORDER = ["ingestion", "planner", "intent", "retrieval", "memory", "reasoning", "synthesis", "guardrails"] as const;

const AGENT_LABELS: Record<string, string> = {
  ingestion: "Ingestion",
  planner: "Planner",
  intent: "Intent & Classification",
  retrieval: "Knowledge Retrieval",
  memory: "Memory",
  reasoning: "Reasoning",
  synthesis: "Response Synthesis",
  guardrails: "Guardrails",
};

function hasExpandableContent(event: AgentStreamEvent): boolean {
  if (event.type === "agent_step") {
    const p = event.payload as Record<string, unknown> | undefined;
    if (!p || typeof p !== "object") return false;
    const keys = Object.keys(p).filter((k) => p[k] !== undefined && p[k] !== null);
    return keys.length > 0;
  }
  if (event.type === "tool_call") {
    const tcs = event.tool_calls ?? (event.payload ? [event.payload as ToolCallPayload] : []);
    if (!tcs.length) return false;
    return tcs.some((tc) => {
      const hasInput = tc.input !== undefined && tc.input !== null && Object.keys(tc.input || {}).length > 0;
      const hasResult = tc.result !== undefined;
      const hasError = !!tc.error;
      return hasInput || hasResult || hasError;
    });
  }
  return false;
}

function getAgentIcon(agentId: string) {
  const icons: Record<string, typeof IconShieldCheck> = {
    ingestion: IconShieldCheck,
    planner: IconCompass,
    intent: IconTarget,
    retrieval: IconSearch,
    memory: IconDatabase,
    reasoning: IconLightbulb,
    synthesis: IconSparkles,
    guardrails: IconShield,
  };
  return icons[agentId] ?? IconTarget;
}

interface StreamPanelProps {
  events: AgentStreamEvent[];
  status: WebSocketStatus;
}

function getStepState(
  agentId: string,
  events: AgentStreamEvent[],
  status: WebSocketStatus
): "completed" | "running" | "pending" {
  const completed = new Set(
    events
      .filter((e): e is AgentStreamEvent & { agent_id: string } => e.type === "agent_step" && !!e.agent_id)
      .map((e) => e.agent_id)
  );
  if (completed.has(agentId)) return "completed";
  if (status !== "open") return "pending";
  const parallel = ["intent", "retrieval", "memory"];
  if (agentId === "ingestion") return completed.size === 0 ? "running" : "pending";
  if (agentId === "planner") return completed.has("ingestion") ? "running" : "pending";
  if (parallel.includes(agentId)) return completed.has("planner") ? "running" : "pending";
  if (agentId === "reasoning") return parallel.every((a) => completed.has(a)) ? "running" : "pending";
  if (agentId === "synthesis") return completed.has("reasoning") ? "running" : "pending";
  if (agentId === "guardrails") return completed.has("synthesis") ? "running" : "pending";
  return "pending";
}

export function StreamPanel({ events, status }: StreamPanelProps) {
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  const toggle = (index: number) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(index)) next.delete(index);
      else next.add(index);
      return next;
    });
  };

  const statusLabel =
    status === "connecting"
      ? "Connecting"
      : status === "open"
        ? "Streaming"
        : status === "error"
          ? "Error"
          : "Closed";

  const isOpen = status === "connecting" || status === "open";

  return (
    <div className="stream-panel stream-panel--revamp">
      <div className="stream-panel-header">
        <h3 className="stream-panel-title">
          <IconZap size={18} />
          <span>Agent Pipeline</span>
        </h3>
        <span
          className={`stream-status-badge stream-status-badge--${status}`}
          data-status={status}
        >
          <span className="stream-status-indicator" />
          {statusLabel}
        </span>
      </div>
      {isOpen && (
        <div className="stream-pipeline-progress">
          {PIPELINE_ORDER.map((agentId) => {
            const stepState = getStepState(agentId, events, status);
            const AgentIcon = getAgentIcon(agentId);
            return (
              <div key={agentId} className={`stream-progress-step stream-progress-step--${stepState}`}>
                <span className="stream-progress-icon">
                  {stepState === "completed" && <IconCheck size={14} />}
                  {stepState === "running" && <IconLoader size={14} />}
                  {stepState === "pending" && <AgentIcon size={14} />}
                </span>
                <span className="stream-progress-label">{AGENT_LABELS[agentId] ?? agentId}</span>
                <span className="stream-progress-status">
                  {stepState === "completed" && "Done"}
                  {stepState === "running" && "Processing"}
                  {stepState === "pending" && "—"}
                </span>
              </div>
            );
          })}
        </div>
      )}
      <ul className="stream-list" aria-label="Agent events">
        {events.map((event, i) => (
          <li
            key={i}
            className={`stream-card stream-card--${event.type} animate-slide-in`}
            style={{ animationDelay: `${i * 40}ms` }}
          >
            {event.type === "agent_step" && (
              <div className="stream-card-inner">
                {hasExpandableContent(event) ? (
                  <button
                    type="button"
                    className="stream-card-trigger"
                    onClick={() => toggle(i)}
                    aria-expanded={expanded.has(i)}
                    aria-controls={`stream-content-${i}`}
                  >
                    <span className="stream-card-icon stream-card-icon--agent">
                      {(() => {
                        const AgentIcon = getAgentIcon(event.agent_id ?? "");
                        return <AgentIcon size={18} />;
                      })()}
                    </span>
                    <span className="stream-card-name">
                      {AGENT_LABELS[event.agent_id ?? ""] ?? event.agent_id ?? event.step ?? "Agent"}
                    </span>
                    <span className="stream-step-state stream-step-state--completed" data-state="completed">
                      <IconCheck size={14} />
                      <span>Completed</span>
                    </span>
                    <span className={`stream-card-chevron ${expanded.has(i) ? "stream-card-chevron--open" : ""}`}>
                      <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                        <path d="M2.5 4.5L6 8l3.5-3.5" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" />
                      </svg>
                    </span>
                  </button>
                ) : (
                  <div className="stream-card-trigger stream-card-trigger--no-expand">
                    <span className="stream-card-icon stream-card-icon--agent">
                      {(() => {
                        const AgentIcon = getAgentIcon(event.agent_id ?? "");
                        return <AgentIcon size={18} />;
                      })()}
                    </span>
                    <span className="stream-card-name">
                      {AGENT_LABELS[event.agent_id ?? ""] ?? event.agent_id ?? event.step ?? "Agent"}
                    </span>
                    <span className="stream-step-state stream-step-state--completed" data-state="completed">
                      <IconCheck size={14} />
                      <span>Completed</span>
                    </span>
                  </div>
                )}
                {hasExpandableContent(event) && (
                <div
                  id={`stream-content-${i}`}
                  className={`stream-card-content ${expanded.has(i) ? "stream-card-content--open" : ""}`}
                >
                  {event.payload && (
                    <pre className="stream-payload">{JSON.stringify(event.payload, null, 2)}</pre>
                  )}
                </div>
                )}
              </div>
            )}
            {event.type === "tool_call" && (
              <div className="stream-card-inner">
                {hasExpandableContent(event) ? (
                  <button
                    type="button"
                    className="stream-card-trigger"
                    onClick={() => toggle(i)}
                    aria-expanded={expanded.has(i)}
                  >
                    <span className="stream-card-icon stream-card-icon--tool">
                      <IconWrench size={18} />
                    </span>
                    <span className="stream-card-name">Tool call</span>
                    <span className={`stream-card-chevron ${expanded.has(i) ? "stream-card-chevron--open" : ""}`}>
                      <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                        <path d="M2.5 4.5L6 8l3.5-3.5" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" />
                      </svg>
                    </span>
                  </button>
                ) : (
                  <div className="stream-card-trigger stream-card-trigger--no-expand">
                    <span className="stream-card-icon stream-card-icon--tool">
                      <IconWrench size={18} />
                    </span>
                    <span className="stream-card-name">Tool call</span>
                  </div>
                )}
                {hasExpandableContent(event) && (
                <div className={`stream-card-content ${expanded.has(i) ? "stream-card-content--open" : ""}`}>
                  {(event.tool_calls ?? (event.payload ? [event.payload as ToolCallPayload] : [])).map(
                    (tc: ToolCallPayload, j: number) => (
                      <div key={j} className="stream-tool-card">
                        <div className="stream-tool-header">
                          <strong>{tc.tool_name ?? "tool"}</strong>
                          {(tc.duration_ms != null || tc.started_at) && (
                            <span className="stream-tool-meta">
                              {tc.duration_ms != null && <span>{tc.duration_ms} ms</span>}
                              {tc.started_at && <span>{tc.started_at}</span>}
                            </span>
                          )}
                        </div>
                        <details className="stream-tool-details">
                          <summary>Input</summary>
                          <pre>{JSON.stringify(tc.input ?? tc, null, 2)}</pre>
                        </details>
                        {tc.result !== undefined && (
                          <details className="stream-tool-details">
                            <summary>Result</summary>
                            <pre>{JSON.stringify(tc.result, null, 2)}</pre>
                          </details>
                        )}
                        {tc.error && <p className="stream-tool-error">{tc.error}</p>}
                      </div>
                    )
                  )}
                </div>
                )}
              </div>
            )}
            {event.type === "escalation" && (
              <div className="stream-card-inner stream-card--escalation-inner">
                <div className="stream-escalation-badge">
                  <span className="stream-escalation-icon"><IconAlert size={18} /></span>
                  <strong>Escalated</strong>
                </div>
                {event.payload && (
                  <pre className="stream-payload">{JSON.stringify(event.payload, null, 2)}</pre>
                )}
              </div>
            )}
            {event.type === "done" && (
              <div className="stream-card-inner stream-card--done-inner">
                <div className="stream-done-badge">
                  <span className="stream-done-icon"><IconCheck size={18} /></span>
                  <strong>Complete</strong>
                </div>
                {event.payload && (
                  <pre className="stream-payload stream-payload--compact">{JSON.stringify(event.payload, null, 2)}</pre>
                )}
              </div>
            )}
            {event.type === "error" && (
              <div className="stream-card-inner stream-card--error-inner">
                <div className="stream-error-header">
                  <span className="stream-error-icon"><IconX size={18} /></span>
                  <strong>Error</strong>
                </div>
                {event.payload && typeof (event.payload as { message?: string }).message === "string" && (
                  <p>{(event.payload as { message: string }).message}</p>
                )}
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
