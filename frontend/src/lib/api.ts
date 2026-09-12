const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

interface FetchOptions extends RequestInit {
  params?: Record<string, string>;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private getEffectiveBaseUrl(): string {
    if (this.baseUrl && this.baseUrl.startsWith("http")) {
      return this.baseUrl;
    }
    if (typeof window !== "undefined") {
      return `${window.location.origin}${this.baseUrl}`;
    }
    return `http://127.0.0.1:8000${this.baseUrl}`;
  }

  private buildUrl(path: string, params?: Record<string, string>): string {
    const base = this.getEffectiveBaseUrl();
    const url = new URL(`${base}${path}`);
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value) url.searchParams.append(key, value);
      });
    }
    return url.toString();
  }

  async get<T>(path: string, params?: Record<string, string>): Promise<T> {
    const res = await fetch(this.buildUrl(path, params), {
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(error.detail || `API error: ${res.status}`);
    }
    return res.json();
  }

  async post<T>(path: string, body?: unknown): Promise<T> {
    const res = await fetch(this.buildUrl(path), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(error.detail || `API error: ${res.status}`);
    }
    return res.json();
  }

  async postForm<T>(path: string, formData: FormData): Promise<T> {
    const res = await fetch(this.buildUrl(path), {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(error.detail || `API error: ${res.status}`);
    }
    return res.json();
  }

  async delete(path: string): Promise<void> {
    const res = await fetch(this.buildUrl(path), {
      method: "DELETE",
    });
    if (!res.ok && res.status !== 204) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(error.detail || `API error: ${res.status}`);
    }
  }

  async put<T>(path: string, body?: unknown): Promise<T> {
    const res = await fetch(this.buildUrl(path), {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(error.detail || `API error: ${res.status}`);
    }
    return res.json();
  }

  streamUrl(path: string): string {
    return this.buildUrl(path);
  }

  get base(): string {
    return this.getEffectiveBaseUrl();
  }
}

const apiBase = API_BASE ? `${API_BASE}/api` : "/api";
export const api = new ApiClient(apiBase);
export default api;
