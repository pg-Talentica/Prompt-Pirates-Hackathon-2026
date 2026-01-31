/**
 * Single-channel chat: messages list, input, send via WebSocket.
 * Shows Escalated state and explainability (reason + evidence) from done payload.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import type { ChatMessage } from "../types/chat";
import type { AgentStreamEvent, DonePayload } from "../types/stream";
import { useWebSocket } from "../hooks/useWebSocket";
import { StreamPanel } from "./StreamPanel";
import { MetricsPanel } from "./MetricsPanel";

const SESSION_KEY = "support-copilot-session";
const MAX_MESSAGES_VISIBLE = 100;

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export function ChatPanel() {
  const [sessionId, setSessionId] = useState(() => {
    try {
      return localStorage.getItem(SESSION_KEY) ?? "default";
    } catch {
      return "default";
    }
  });
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const onDone = useCallback((event: AgentStreamEvent) => {
    if (event.type !== "done" || !event.payload) return;
    const p = event.payload as DonePayload;
    const content = p.final_response ?? "";
    if (!content && !p.escalate) return;
    setMessages((prev) => {
      const next = [...prev];
      let pendingIndex = -1;
      for (let i = next.length - 1; i >= 0; i--) {
        const m = next[i];
        if (m.role === "assistant" && m.content === "" && m.id.startsWith("pending-")) {
          pendingIndex = i;
          break;
        }
      }
      const replacement: ChatMessage = {
        id: generateId(),
        role: "assistant",
        content: content || "Your request has been escalated for further assistance.",
        escalate: p.escalate,
        intent_result: p.intent_result,
        guardrails_result: p.guardrails_result,
        recommended_actions: p.recommended_actions,
        timestamp: new Date().toISOString(),
      };
      if (pendingIndex >= 0) {
        next[pendingIndex] = replacement;
        return next;
      }
      next.push(replacement);
      return next;
    });
  }, []);

  const { status, events, send, clearEvents } = useWebSocket("/api/chat/ws", {
    onEvent: (event) => {
      if (event.type === "done") onDone(event);
    },
  });

  const handleSend = useCallback(() => {
    const text = input.trim();
    if (!text) return;
    setInput("");
    setMessages((prev) => {
      const next = [...prev];
      if (next.length >= MAX_MESSAGES_VISIBLE) next.shift();
      next.push({
        id: generateId(),
        role: "user",
        content: text,
        timestamp: new Date().toISOString(),
      });
      return next;
    });
    setMessages((prev) => {
      const next = [...prev];
      next.push({
        id: `pending-${Date.now()}`,
        role: "assistant",
        content: "",
        timestamp: new Date().toISOString(),
      });
      return next;
    });
    try {
      localStorage.setItem(SESSION_KEY, sessionId);
    } catch {
      // ignore
    }
    clearEvents();
    send({ query: text, session_id: sessionId });
  }, [input, sessionId, send, clearEvents]);

  const displayMessages = messages.slice(-MAX_MESSAGES_VISIBLE);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [displayMessages.length]);

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <h2>Chat</h2>
        <label className="session-label">
          Session:{" "}
          <input
            type="text"
            value={sessionId}
            onChange={(e) => setSessionId(e.target.value)}
            placeholder="default"
            className="session-input"
          />
        </label>
      </div>
      <div className="chat-messages" role="log" aria-live="polite">
        {displayMessages.map((msg) => (
          <div
            key={msg.id}
            className={`message message--${msg.role}`}
            data-role={msg.role}
          >
            <div className="message-header">
              <span className="message-role">{msg.role === "user" ? "You" : "Co-Pilot"}</span>
              {msg.escalate && (
                <span className="message-badge message-badge--escalated" aria-label="Escalated">
                  Escalated
                </span>
              )}
              <span className="message-time">
                {new Date(msg.timestamp).toLocaleTimeString()}
              </span>
            </div>
            {msg.content && <div className="message-content">{msg.content}</div>}
            {msg.role === "assistant" && (msg.intent_result ?? msg.guardrails_result) && (
              <details className="message-explainability">
                <summary>Reason & evidence</summary>
                {msg.intent_result && (
                  <pre className="message-evidence">
                    {JSON.stringify(msg.intent_result, null, 2)}
                  </pre>
                )}
                {msg.guardrails_result && (
                  <pre className="message-evidence">
                    {JSON.stringify(msg.guardrails_result, null, 2)}
                  </pre>
                )}
              </details>
            )}
            {msg.role === "assistant" &&
              Array.isArray(msg.recommended_actions) &&
              msg.recommended_actions.length > 0 && (
                <div className="message-actions">
                  <strong>Recommended actions:</strong>
                  <ul>
                    {msg.recommended_actions.map((a, i) => (
                      <li key={i}>{typeof a === "object" ? JSON.stringify(a) : String(a)}</li>
                    ))}
                  </ul>
                </div>
              )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <div className="chat-input-row">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
          placeholder="Type a message..."
          className="chat-input"
          disabled={status === "connecting" || status === "open"}
          aria-label="Message input"
        />
        <button
          type="button"
          onClick={handleSend}
          disabled={!input.trim() || status === "connecting" || status === "open"}
          className="chat-send"
          aria-label="Send message"
        >
          {status === "connecting" ? "Connecting…" : status === "open" ? "Sending…" : "Send"}
        </button>
      </div>
      <div className="chat-sidebars">
        <StreamPanel events={events} status={status} />
        <MetricsPanel events={events} />
      </div>
    </div>
  );
}
