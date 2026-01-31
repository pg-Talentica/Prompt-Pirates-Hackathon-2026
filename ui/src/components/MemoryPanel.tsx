/**
 * Memory CRUD: list (filter by type/session), edit, delete.
 */

import { useCallback, useEffect, useState } from "react";
import type { MemoryRecord, MemoryType, MemoryUpdate } from "../types/memory";
import * as api from "../api/client";

export function MemoryPanel() {
  const [memories, setMemories] = useState<MemoryRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState<MemoryType | "">("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await api.listMemories({
        type: typeFilter || undefined,
        limit: 100,
      });
      setMemories(Array.isArray(list) ? list : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load memories");
      setMemories([]);
    } finally {
      setLoading(false);
    }
  }, [typeFilter]);

  useEffect(() => {
    load();
  }, [load]);

  const handleDelete = useCallback(
    async (id: string) => {
      if (!confirm("Delete this memory?")) return;
      try {
        await api.deleteMemory(id);
        setMemories((prev) => prev.filter((m) => m.id !== id));
      } catch (e) {
        setError(e instanceof Error ? e.message : "Delete failed");
      }
    },
    []
  );

  const startEdit = useCallback((rec: MemoryRecord) => {
    setEditingId(rec.id);
    setEditContent(rec.content);
  }, []);

  const saveEdit = useCallback(async () => {
    if (!editingId) return;
    try {
      const updated = await api.updateMemory(editingId, {
        content: editContent,
      } as MemoryUpdate);
      setMemories((prev) =>
        prev.map((m) => (m.id === editingId ? updated : m))
      );
      setEditingId(null);
      setEditContent("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Update failed");
    }
  }, [editingId, editContent]);

  const cancelEdit = useCallback(() => {
    setEditingId(null);
    setEditContent("");
  }, []);

  return (
    <div className="memory-panel">
      <h3>Memories</h3>
      <div className="memory-filters">
        <label>
          Type:{" "}
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter((e.target.value || "") as MemoryType | "")}
            aria-label="Filter by type"
          >
            <option value="">All</option>
            <option value="working">working</option>
            <option value="episodic">episodic</option>
            <option value="semantic">semantic</option>
          </select>
        </label>
        <button type="button" onClick={load} className="memory-refresh" aria-label="Refresh">
          Refresh
        </button>
      </div>
      {error && <p className="memory-error" role="alert">{error}</p>}
      {loading ? (
        <p className="memory-loading">Loading…</p>
      ) : (
        <ul className="memory-list" aria-label="Memory list">
          {memories.map((rec) => (
            <li key={rec.id} className="memory-item">
              <div className="memory-item-header">
                <span className="memory-type">{rec.type}</span>
                {rec.session_id && (
                  <span className="memory-session">{rec.session_id}</span>
                )}
                <span className="memory-id">{rec.id.slice(0, 8)}…</span>
              </div>
              {editingId === rec.id ? (
                <div className="memory-edit">
                  <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    rows={4}
                    className="memory-edit-input"
                    aria-label="Edit content"
                  />
                  <div className="memory-edit-actions">
                    <button type="button" onClick={saveEdit}>
                      Save
                    </button>
                    <button type="button" onClick={cancelEdit}>
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <pre className="memory-content">{rec.content}</pre>
                  <div className="memory-actions">
                    <button
                      type="button"
                      onClick={() => startEdit(rec)}
                      aria-label={`Edit ${rec.id}`}
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDelete(rec.id)}
                      aria-label={`Delete ${rec.id}`}
                      className="memory-delete"
                    >
                      Delete
                    </button>
                  </div>
                </>
              )}
            </li>
          ))}
        </ul>
      )}
      {!loading && memories.length === 0 && (
        <p className="memory-empty">No memories found.</p>
      )}
    </div>
  );
}
