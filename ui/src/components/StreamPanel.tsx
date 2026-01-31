/**
 * Live stream: high-level agent steps and expandable tool call details.
 */

import { useState } from "react";
import type { AgentStreamEvent, ToolCallPayload } from "../types/stream";
import type { WebSocketStatus } from "../hooks/useWebSocket";

interface StreamPanelProps {
  events: AgentStreamEvent[];
  status: WebSocketStatus;
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

  return (
    <div className="stream-panel">
      <h3>Live stream</h3>
      <p className="stream-status" data-status={status}>
        Status: {status}
      </p>
      <ul className="stream-list" aria-label="Agent events">
        {events.map((event, i) => (
          <li key={i} className={`stream-item stream-item--${event.type}`}>
            {event.type === "agent_step" && (
              <>
                <button
                  type="button"
                  className="stream-step"
                  onClick={() => toggle(i)}
                  aria-expanded={expanded.has(i)}
                >
                  <span className="stream-step-name">Agent: {event.agent_id ?? event.step ?? "—"}</span>
                  <span className="stream-step-toggle">{expanded.has(i) ? "▼" : "▶"}</span>
                </button>
                {expanded.has(i) && event.payload && (
                  <pre className="stream-payload">{JSON.stringify(event.payload, null, 2)}</pre>
                )}
              </>
            )}
            {event.type === "tool_call" && (
              <>
                <button
                  type="button"
                  className="stream-step"
                  onClick={() => toggle(i)}
                  aria-expanded={expanded.has(i)}
                >
                  <span className="stream-step-name">Tool call</span>
                  <span className="stream-step-toggle">{expanded.has(i) ? "▼" : "▶"}</span>
                </button>
                {expanded.has(i) &&
                  (event.tool_calls ?? (event.payload ? [event.payload as ToolCallPayload] : [])).map(
                    (tc: ToolCallPayload, j: number) => (
                        <div key={j} className="stream-tool-detail">
                        <strong>{tc.tool_name ?? "tool"}</strong>
                        <div className="stream-tool-meta">
                          {tc.duration_ms != null && (
                            <span>{tc.duration_ms} ms</span>
                          )}
                          {tc.started_at && (
                            <span>{tc.started_at}</span>
                          )}
                        </div>
                        <details>
                          <summary>Input</summary>
                          <pre>{JSON.stringify(tc.input ?? tc, null, 2)}</pre>
                        </details>
                        {tc.result !== undefined && (
                          <details>
                            <summary>Result</summary>
                            <pre>{JSON.stringify(tc.result, null, 2)}</pre>
                          </details>
                        )}
                        {tc.error && (
                          <p className="stream-tool-error">{tc.error}</p>
                        )}
                      </div>
                    )
                  )}
              </>
            )}
            {event.type === "escalation" && (
              <div className="stream-escalation">
                <strong>Escalation</strong>
                {event.payload && (
                  <pre className="stream-payload">{JSON.stringify(event.payload, null, 2)}</pre>
                )}
              </div>
            )}
            {event.type === "done" && (
              <div className="stream-done">
                <strong>Done</strong>
                {event.payload && (
                  <pre className="stream-payload">{JSON.stringify(event.payload, null, 2)}</pre>
                )}
              </div>
            )}
            {event.type === "error" && (
              <div className="stream-error">
                <strong>Error</strong>
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
