/**
 * WebSocket client for live streaming of agent events.
 * Connects to /api/chat/ws; buffers events for UI (agent steps + expandable tool calls).
 */

import { useCallback, useEffect, useRef, useState } from "react";
import type { AgentStreamEvent } from "../types/stream";

export type WebSocketStatus = "connecting" | "open" | "closed" | "error";

export interface UseWebSocketOptions {
  /** Called when a new event is received (optional; events also stored in buffer). */
  onEvent?: (event: AgentStreamEvent) => void;
  /** Called when connection closes (done or error). */
  onClose?: () => void;
}

export interface UseWebSocketReturn {
  status: WebSocketStatus;
  /** All events received in this run (cleared when send() is called for a new query). */
  events: AgentStreamEvent[];
  /** Last event (convenience). */
  lastMessage: AgentStreamEvent | null;
  /** Send JSON (query + session_id). Clears event buffer. */
  send: (data: { query: string; session_id?: string }) => void;
  /** Clear event buffer manually. */
  clearEvents: () => void;
}

function getWsUrl(path: string): string {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = window.location.host;
  return `${protocol}//${host}${path}`;
}

export function useWebSocket(
  path: string = "/api/chat/ws",
  options: UseWebSocketOptions = {}
): UseWebSocketReturn {
  const { onEvent, onClose } = options;
  const [status, setStatus] = useState<WebSocketStatus>("closed");
  const [events, setEvents] = useState<AgentStreamEvent[]>([]);
  const [lastMessage, setLastMessage] = useState<AgentStreamEvent | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const pendingRef = useRef<{ query: string; session_id: string } | null>(null);

  const clearEvents = useCallback(() => {
    setEvents([]);
    setLastMessage(null);
  }, []);

  const connectAndSend = useCallback(
    (query: string, session_id: string) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
      clearEvents();
      setStatus("connecting");
      const url = getWsUrl(path);
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus("open");
        ws.send(JSON.stringify({ query, session_id }));
      };

      ws.onmessage = (ev) => {
        try {
          const raw = JSON.parse(ev.data as string) as AgentStreamEvent;
          const event: AgentStreamEvent = {
            ...raw,
            timestamp: raw.timestamp ?? new Date().toISOString(),
          };
          if (raw.type === "tool_call" && raw.payload && !raw.tool_calls) {
            event.tool_calls = [raw.payload as AgentStreamEvent["tool_calls"][0]];
          }
          setEvents((prev) => [...prev, event]);
          setLastMessage(event);
          onEvent?.(event);
        } catch {
          // ignore parse errors
        }
      };

      ws.onerror = () => setStatus("error");
      ws.onclose = () => {
        if (wsRef.current === ws) wsRef.current = null;
        setStatus("closed");
        onClose?.();
      };
    },
    [path, clearEvents, onEvent, onClose]
  );

  const send = useCallback(
    (data: { query: string; session_id?: string }) => {
      const query = (data.query ?? "").trim();
      const session_id = (data.session_id ?? "default").trim() || "default";
      if (!query) return;
      pendingRef.current = { query, session_id };
      connectAndSend(query, session_id);
    },
    [connectAndSend]
  );

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);

  return {
    status,
    events,
    lastMessage,
    send,
    clearEvents,
  };
}
