/**
 * Loader / status indicator for agent processing states.
 * Shows Thinking, Retrieving, etc. with state-specific icons.
 */

import type { AgentStreamEvent } from "../types/stream";
import type { WebSocketStatus } from "../hooks/useWebSocket";
import {
  IconConnecting,
  IconLoader,
  IconShieldCheck,
  IconCompass,
  IconTarget,
  IconSearch,
  IconDatabase,
  IconLightbulb,
  IconSparkles,
  IconShield,
  IconWrench,
} from "./Icons";

const AGENT_LABELS: Record<string, string> = {
  ingestion: "Ingesting & validating",
  planner: "Planning workflow",
  intent: "Classifying intent",
  retrieval: "Retrieving knowledge",
  memory: "Loading memory",
  reasoning: "Reasoning & correlating",
  synthesis: "Generating response",
  guardrails: "Applying guardrails",
};

function getStatusLabel(status: WebSocketStatus, lastEvent: AgentStreamEvent | null): string {
  if (status === "connecting") return "Connecting…";
  if (status === "error" || status === "closed") return "";
  if (!lastEvent) return "Processing…";
  if (lastEvent.type === "agent_step" && lastEvent.agent_id) {
    const label = AGENT_LABELS[lastEvent.agent_id] ?? lastEvent.agent_id;
    return `${label}…`;
  }
  if (lastEvent.type === "tool_call") return "Running tools…";
  if (lastEvent.type === "done") return "";
  return "Processing…";
}

function getStatusIcon(status: WebSocketStatus, lastEvent: AgentStreamEvent | null) {
  if (status === "connecting") return IconConnecting;
  if (!lastEvent || status === "error" || status === "closed") return IconLoader;
  if (lastEvent.type === "agent_step" && lastEvent.agent_id) {
    const icons: Record<string, typeof IconLoader> = {
      ingestion: IconShieldCheck,
      planner: IconCompass,
      intent: IconTarget,
      retrieval: IconSearch,
      memory: IconDatabase,
      reasoning: IconLightbulb,
      synthesis: IconSparkles,
      guardrails: IconShield,
    };
    return icons[lastEvent.agent_id] ?? IconLoader;
  }
  if (lastEvent.type === "tool_call") return IconWrench;
  return IconLoader;
}

interface AgentStatusLoaderProps {
  status: WebSocketStatus;
  lastEvent: AgentStreamEvent | null;
  isActive: boolean;
}

export function AgentStatusLoader({ status, lastEvent, isActive }: AgentStatusLoaderProps) {
  const label = getStatusLabel(status, lastEvent);
  if (!label || !isActive) return null;

  const Icon = getStatusIcon(status, lastEvent);
  const isSpinning = Icon === IconLoader || status === "connecting";

  return (
    <div className="agent-status-loader animate-fade-in" role="status" aria-live="polite">
      <span className={`agent-status-icon ${isSpinning ? "agent-status-icon--spin" : ""}`}>
        <Icon size={20} />
      </span>
      <span className="agent-status-label">{label}</span>
    </div>
  );
}
