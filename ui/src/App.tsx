/**
 * Support Co-Pilot – chat UI.
 * Live streaming of agent events will use the WebSocket hook (see hooks/useWebSocket).
 */
function App() {
  return (
    <main style={{ padding: "2rem", maxWidth: "48rem", margin: "0 auto" }}>
      <h1>Support Co-Pilot</h1>
      <p>Intelligent Support & Incident Co-Pilot – collaborative agent system.</p>
      <p>
        <em>WebSocket client for live streaming will be wired in later tasks.</em>
      </p>
    </main>
  );
}

export default App;
