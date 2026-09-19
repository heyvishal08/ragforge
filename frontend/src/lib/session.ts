/**
 * Browser session isolation helper.
 * Generates and persists a stable anonymous session token in localStorage.
 * Ensures each visitor has their own private knowledge bases, documents, and chats.
 */

const SESSION_KEY = "ragforge_session_id";

export function getSessionId(): string {
  if (typeof window === "undefined") {
    return "server-default";
  }

  try {
    let sessionId = localStorage.getItem(SESSION_KEY);
    if (!sessionId) {
      sessionId = "sess_" + (typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID().replace(/-/g, "") : Math.random().toString(36).substring(2) + Date.now().toString(36));
      localStorage.setItem(SESSION_KEY, sessionId);
    }
    return sessionId;
  } catch {
    return "fallback-session";
  }
}
