/**
 * WebSocket client placeholder for live streaming of agent events.
 *
 * Will connect to the backend WebSocket endpoint and stream:
 * - High-level agent steps (which agent ran, when)
 * - Expandable tool call details (input, execution, result)
 *
 * Usage (to be implemented in later tasks):
 *   const { status, lastMessage, send } = useWebSocket(wsUrl);
 *   // status: 'connecting' | 'open' | 'closed' | 'error'
 *   // lastMessage: parsed event for UI (agent_id, step, tool_calls, payload)
 */

export type WebSocketStatus = "connecting" | "open" | "closed" | "error";

export interface AgentStreamEvent {
  type: string;
  agent_id?: string;
  step?: string;
  tool_calls?: unknown[];
  payload?: unknown;
  timestamp?: string;
}

export interface UseWebSocketReturn {
  status: WebSocketStatus;
  lastMessage: AgentStreamEvent | null;
  send: (data: string | object) => void;
}

export function useWebSocket(_url: string): UseWebSocketReturn {
  // Placeholder: real implementation will connect, parse messages, and expose status/lastMessage/send
  return {
    status: "closed",
    lastMessage: null,
    send: () => {},
  };
}
