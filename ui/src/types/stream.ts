/**
 * WebSocket stream event types matching backend api/schemas/stream.py.
 * Used for live agent steps and expandable tool details.
 */

export type StreamEventType =
  | "agent_step"
  | "tool_call"
  | "escalation"
  | "done"
  | "error";

export interface AgentStreamEvent {
  type: StreamEventType;
  agent_id?: string;
  step?: string;
  tool_calls?: ToolCallPayload[];
  payload?: StreamEventPayload;
  timestamp?: string;
}

export interface ToolCallPayload {
  tool_name: string;
  input: Record<string, unknown>;
  result?: unknown;
  error?: string;
  started_at?: string;
  finished_at?: string;
  duration_ms?: number;
}

export interface DonePayload {
  final_response: string;
  escalate: boolean;
  recommended_actions: Array<Record<string, unknown>>;
  intent_result?: Record<string, unknown>;
  guardrails_result?: { reason?: string; confidence?: number; no_answer?: boolean; [k: string]: unknown };
}

export interface EscalationPayload {
  final_response?: string;
  guardrails_result?: Record<string, unknown>;
}

export interface ErrorPayload {
  message: string;
  [k: string]: unknown;
}

export type StreamEventPayload =
  | DonePayload
  | EscalationPayload
  | ErrorPayload
  | Record<string, unknown>;

export function isDoneEvent(e: AgentStreamEvent): e is AgentStreamEvent & { payload: DonePayload } {
  return e.type === "done" && e.payload != null;
}

export function isToolCallEvent(e: AgentStreamEvent): boolean {
  return e.type === "tool_call" && Array.isArray(e.tool_calls);
}

export function isEscalationEvent(e: AgentStreamEvent): boolean {
  return e.type === "escalation";
}

export function isErrorEvent(e: AgentStreamEvent): boolean {
  return e.type === "error";
}
