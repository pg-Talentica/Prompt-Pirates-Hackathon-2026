/**
 * Memory types matching backend memory API (memory/models, memory/service).
 */

export type MemoryType = "working" | "episodic" | "semantic";

export interface MemoryRecord {
  id: string;
  type: MemoryType;
  session_id: string | null;
  content: string;
  metadata: Record<string, unknown>;
  created_at: string | null;
  updated_at: string | null;
}

export interface MemoryCreate {
  type: MemoryType;
  session_id?: string | null;
  content: string;
  metadata?: Record<string, unknown>;
}

export interface MemoryUpdate {
  content?: string | null;
  metadata?: Record<string, unknown> | null;
}

export interface SessionItem {
  session_id: string;
  latest_activity: string;
}
