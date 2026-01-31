/**
 * Chat message and run state for the UI.
 */

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  /** Set when this assistant reply was escalated (Guardrails). */
  escalate?: boolean;
  /** Optional evidence / reason from payload (explainability). */
  intent_result?: Record<string, unknown>;
  guardrails_result?: Record<string, unknown>;
  recommended_actions?: Array<Record<string, unknown>>;
  timestamp: string;
}
