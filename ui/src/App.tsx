/**
 * Support Co-Pilot – chat UI with live stream, memory CRUD, and metrics.
 */

import { useState } from "react";
import { ChatPanel } from "./components/ChatPanel";
import { MemoryPanel } from "./components/MemoryPanel";
import "./App.css";

type TabId = "chat" | "memory";

function App() {
  const [tab, setTab] = useState<TabId>("chat");

  return (
    <div className="app">
      <header className="app-header">
        <h1>Support Co-Pilot</h1>
        <p className="app-tagline">
          Intelligent Support & Incident Co-Pilot – collaborative agent system.
        </p>
        <nav className="app-tabs" role="tablist" aria-label="Main sections">
          <button
            type="button"
            role="tab"
            aria-selected={tab === "chat"}
            aria-controls="panel-chat"
            id="tab-chat"
            className={`app-tab ${tab === "chat" ? "app-tab--active" : ""}`}
            onClick={() => setTab("chat")}
          >
            Chat
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={tab === "memory"}
            aria-controls="panel-memory"
            id="tab-memory"
            className={`app-tab ${tab === "memory" ? "app-tab--active" : ""}`}
            onClick={() => setTab("memory")}
          >
            Memories
          </button>
        </nav>
      </header>
      <main className="app-main">
        <section
          id="panel-chat"
          role="tabpanel"
          aria-labelledby="tab-chat"
          hidden={tab !== "chat"}
          className="app-panel"
        >
          <ChatPanel />
        </section>
        <section
          id="panel-memory"
          role="tabpanel"
          aria-labelledby="tab-memory"
          hidden={tab !== "memory"}
          className="app-panel"
        >
          <MemoryPanel />
        </section>
      </main>
    </div>
  );
}

export default App;
