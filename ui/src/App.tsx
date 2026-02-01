/**
 * Support AI Agent – chat UI with live stream, memory CRUD, and metrics.
 */

import { useEffect, useState } from "react";
import { ChatPanel } from "./components/ChatPanel";
import { MemoryPanel } from "./components/MemoryPanel";
import "./App.css";

const THEME_KEY = "support-copilot-theme";

type TabId = "chat" | "memory";
type Theme = "light" | "dark";

function App() {
  const [tab, setTab] = useState<TabId>("chat");
  const [theme, setTheme] = useState<Theme>(() => {
    try {
      const stored = localStorage.getItem(THEME_KEY) as Theme | null;
      return stored === "dark" || stored === "light" ? stored : "dark";
    } catch {
      return "dark";
    }
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    try {
      localStorage.setItem(THEME_KEY, theme);
    } catch {
      /* ignore */
    }
  }, [theme]);

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header-top">
          <h1>Support AI Agent</h1>
          <button
            type="button"
            className="theme-toggle"
            onClick={() => setTheme((t) => (t === "light" ? "dark" : "light"))}
            aria-label={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}
            title={theme === "light" ? "Dark mode" : "Light mode"}
          >
            {theme === "light" ? (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
              </svg>
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="5" />
                <line x1="12" y1="1" x2="12" y2="3" />
                <line x1="12" y1="21" x2="12" y2="23" />
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                <line x1="1" y1="12" x2="3" y2="12" />
                <line x1="21" y1="12" x2="23" y2="12" />
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
              </svg>
            )}
          </button>
        </div>
        <p className="app-tagline">
          Intelligent Support & Incident AI Agent – collaborative agent system.
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
