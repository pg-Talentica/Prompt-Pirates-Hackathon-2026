/**
 * Basic metrics derived from stream: latency, tool call count, escalation.
 */

import { useMemo } from "react";
import type { AgentStreamEvent, DonePayload } from "../types/stream";

interface MetricsPanelProps {
  events: AgentStreamEvent[];
}

export function MetricsPanel({ events }: MetricsPanelProps) {
  const metrics = useMemo(() => {
    let firstTs: number | null = null;
    let doneTs: number | null = null;
    let toolCount = 0;
    let escalated = false;
    for (const e of events) {
      const ts = e.timestamp ? new Date(e.timestamp).getTime() : null;
      if (ts != null && firstTs == null) firstTs = ts;
      if (e.type === "tool_call") toolCount += e.tool_calls?.length ?? 1;
      if (e.type === "done") {
        if (ts != null) doneTs = ts;
        const p = e.payload as DonePayload | undefined;
        if (p?.escalate) escalated = true;
      }
    }
    const latencyMs =
      firstTs != null && doneTs != null ? doneTs - firstTs : null;
    return { latencyMs, toolCount, escalated };
  }, [events]);

  return (
    <div className="metrics-panel">
      <h3>Metrics</h3>
      <ul className="metrics-list">
        <li>
          <span className="metrics-label">Latency</span>
          <span className="metrics-value">
            {metrics.latencyMs != null
              ? `${(metrics.latencyMs / 1000).toFixed(2)} s`
              : "—"}
          </span>
        </li>
        <li>
          <span className="metrics-label">Tool calls</span>
          <span className="metrics-value">{metrics.toolCount}</span>
        </li>
        <li>
          <span className="metrics-label">Token usage</span>
          <span className="metrics-value" title="Not yet provided by backend">
            —
          </span>
        </li>
        <li>
          <span className="metrics-label">Escalation</span>
          <span className="metrics-value" data-escalated={metrics.escalated}>
            {metrics.escalated ? "Yes" : "No"}
          </span>
        </li>
      </ul>
    </div>
  );
}
