/**
 * Single-channel chat: messages list, input, send via WebSocket.
 * Shows Escalated state and explainability (reason + evidence) from done payload.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import type { ChatMessage } from "../types/chat";
import type { AgentStreamEvent, DonePayload } from "../types/stream";
import { useWebSocket } from "../hooks/useWebSocket";
import { AgentStatusLoader } from "./AgentStatusLoader";
import { MetricsPanel } from "./MetricsPanel";
import { StreamPanel } from "./StreamPanel";

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
  const [rightTab, setRightTab] = useState<"pipeline" | "metrics">("pipeline");
  const [rightPanelVisible, setRightPanelVisible] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const toggleRightPanel = () => setRightPanelVisible((v) => !v);

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

  const { status, events, send, clearEvents, lastMessage } = useWebSocket("/api/chat/ws", {
    onEvent: (event) => {
      if (event.type === "done") onDone(event);
    },
  });

  const isProcessing = status === "connecting" || status === "open";

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
    <div className="chat-layout">
      <div className="chat-main">
        <div className="chat-header">
          <h2>Chat</h2>
          <button
            type="button"
            className="right-panel-toggle"
            onClick={toggleRightPanel}
            aria-label={rightPanelVisible ? "Hide pipeline & metrics" : "Show pipeline & metrics"}
            title={rightPanelVisible ? "Hide right panel" : "Show right panel"}
          >
            {rightPanelVisible ? (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M11 17 6 12l5-5M18 17l-5-5 5-5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M13 17l5-5-5-5M6 17l5-5-5-5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            )}
          </button>
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
            className={`message message--${msg.role} animate-slide-in`}
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
            {msg.role === "assistant" && msg.content === "" && isProcessing && (
              <AgentStatusLoader status={status} lastEvent={lastMessage} isActive={true} />
            )}
            {msg.role === "assistant" &&
              Array.isArray(msg.recommended_actions) &&
              msg.recommended_actions.length > 0 && (
                <div className="message-actions message-actions--readable">
                  <strong>What you can do next:</strong>
                  <ul>
                    {msg.recommended_actions.map((a, i) => {
                      const desc =
                        typeof a === "object" && a != null && "description" in a && typeof (a as { description?: unknown }).description === "string"
                          ? (a as { description: string }).description
                          : typeof a === "object" && a != null && "action" in a
                            ? String((a as { action: unknown }).action).replace(/_/g, " ")
                            : typeof a === "string"
                              ? a
                              : null;
                      return (
                        <li key={i}>
                          {desc ?? (typeof a === "object" && a != null ? Object.values(a).filter(Boolean).join(" • ") : String(a))}
                        </li>
                      );
                    })}
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
            disabled={isProcessing}
            aria-label="Message input"
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={!input.trim() || isProcessing}
            className="chat-send"
            aria-label="Send message"
          >
            {status === "connecting" ? "Connecting…" : status === "open" ? "Processing…" : "Send"}
          </button>
        </div>
      </div>
      {rightPanelVisible && (
      <div className="chat-right-panel">
        <nav className="right-panel-tabs" role="tablist" aria-label="Agent details">
          <button
            type="button"
            role="tab"
            aria-selected={rightTab === "pipeline"}
            aria-controls="panel-pipeline"
            id="tab-pipeline"
            className={`right-panel-tab ${rightTab === "pipeline" ? "right-panel-tab--active" : ""}`}
            onClick={() => setRightTab("pipeline")}
          >
            Agent Pipeline
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={rightTab === "metrics"}
            aria-controls="panel-metrics"
            id="tab-metrics"
            className={`right-panel-tab ${rightTab === "metrics" ? "right-panel-tab--active" : ""}`}
            onClick={() => setRightTab("metrics")}
          >
            Metrics
          </button>
        </nav>
        <div
          id="panel-pipeline"
          role="tabpanel"
          aria-labelledby="tab-pipeline"
          hidden={rightTab !== "pipeline"}
          className={`right-panel-content ${rightTab === "pipeline" ? "right-panel-content--active" : ""}`}
        >
          <StreamPanel events={events} status={status} />
        </div>
        <div
          id="panel-metrics"
          role="tabpanel"
          aria-labelledby="tab-metrics"
          hidden={rightTab !== "metrics"}
          className={`right-panel-content ${rightTab === "metrics" ? "right-panel-content--active" : ""}`}
        >
          <MetricsPanel events={events} />
        </div>
      </div>
      )}
    </div>
  );
}
