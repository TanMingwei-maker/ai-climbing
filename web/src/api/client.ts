const API_ORIGIN = import.meta.env.VITE_API_ORIGIN ?? 'http://127.0.0.1:8000';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? `${API_ORIGIN}/api`;

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}

export function getApiErrorMessage(error: unknown, fallback = '请求失败，请稍后再试') {
  if (isApiError(error)) {
    return error.detail;
  }
  return error instanceof Error ? error.message : fallback;
}

export function toApiUrl(path: string): string {
  return path.startsWith('http://') || path.startsWith('https://')
    ? path
    : `${API_ORIGIN}${path}`;
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let detail = `请求失败 (${response.status})`;

    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        detail = payload.detail;
      }
    } catch {
      try {
        const text = await response.text();
        if (text) {
          detail = text;
        }
      } catch {
        // Ignore parse failures and keep the fallback message.
      }
    }

    throw new ApiError(response.status, detail);
  }

  return response.json() as Promise<T>;
}
