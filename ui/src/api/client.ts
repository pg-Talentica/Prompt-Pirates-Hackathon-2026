/**
 * API client for Support Co-Pilot backend.
 * Uses relative /api for Vite proxy to backend.
 */

import type { MemoryRecord, MemoryCreate, MemoryUpdate } from "../types/memory";
import type { SessionItem } from "../types/memory";

const API_BASE = "/api";

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = path.startsWith("http") ? path : `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(res.status === 404 ? "Not found" : text || `HTTP ${res.status}`);
  }
  if (res.status === 204 || res.headers.get("content-length") === "0") {
    return undefined as T;
  }
  return res.json() as Promise<T>;
}

// --- Memories ---

export async function listMemories(params?: {
  type?: "working" | "episodic" | "semantic";
  session_id?: string;
  limit?: number;
  offset?: number;
}): Promise<MemoryRecord[]> {
  const search = new URLSearchParams();
  if (params?.type) search.set("type", params.type);
  if (params?.session_id) search.set("session_id", params.session_id);
  if (params?.limit != null) search.set("limit", String(params.limit));
  if (params?.offset != null) search.set("offset", String(params.offset));
  const q = search.toString();
  return request<MemoryRecord[]>(`/memories${q ? `?${q}` : ""}`);
}

export async function getMemory(id: string): Promise<MemoryRecord> {
  return request<MemoryRecord>(`/memories/${encodeURIComponent(id)}`);
}

export async function createMemory(payload: MemoryCreate): Promise<MemoryRecord> {
  return request<MemoryRecord>("/memories", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateMemory(
  id: string,
  payload: MemoryUpdate
): Promise<MemoryRecord> {
  return request<MemoryRecord>(`/memories/${encodeURIComponent(id)}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteMemory(id: string): Promise<{ deleted: string }> {
  return request<{ deleted: string }>(`/memories/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
}

// --- Sessions ---

export async function listSessions(params?: {
  limit?: number;
}): Promise<{ sessions: SessionItem[] }> {
  const search = new URLSearchParams();
  if (params?.limit != null) search.set("limit", String(params.limit));
  const q = search.toString();
  return request<{ sessions: SessionItem[] }>(
    `/sessions${q ? `?${q}` : ""}`
  );
}
