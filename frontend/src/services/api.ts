/** Default API host on Render (overridden by VITE_API_BASE_URL at build time). */
const RENDER_API_DEFAULT = 'https://eldergo-kl-api.onrender.com';

function resolveApiBaseUrl(): string {
  const fromEnv = import.meta.env.VITE_API_BASE_URL;
  if (typeof fromEnv === 'string' && fromEnv.trim()) {
    return fromEnv.trim().replace(/\/$/, '');
  }
  // Dev: use Vite proxy (vite.config.ts) — same origin as the UI at 127.0.0.1:5173.
  if (import.meta.env.DEV) {
    return '';
  }
  // Production static build (e.g. Render): use deployed API unless env was set at build.
  if (import.meta.env.PROD) {
    return RENDER_API_DEFAULT;
  }
  return 'http://127.0.0.1:8000';
}

export const API_BASE_URL = resolveApiBaseUrl();

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

function parseErrorDetail(detail: unknown): { message: string; code?: string } {
  if (typeof detail === 'string') {
    return { message: detail };
  }
  if (detail && typeof detail === 'object') {
    const record = detail as Record<string, unknown>;
    const message = typeof record.message === 'string' ? record.message : undefined;
    const code = typeof record.code === 'string' ? record.code : undefined;
    if (message || code) {
      return { message: message || 'Something went wrong. Please try again.', code };
    }
  }
  return { message: 'Something went wrong. Please try again.' };
}

const DEFAULT_REQUEST_TIMEOUT_MS = 90_000;

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const timeoutController = new AbortController();
  const timeoutId = window.setTimeout(() => timeoutController.abort(), DEFAULT_REQUEST_TIMEOUT_MS);
  const parentSignal = init?.signal;
  if (parentSignal) {
    if (parentSignal.aborted) {
      timeoutController.abort();
    } else {
      parentSignal.addEventListener('abort', () => timeoutController.abort(), { once: true });
    }
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      signal: timeoutController.signal,
      headers: {
        'Content-Type': 'application/json',
        ...(init?.headers || {}),
      },
    });
  } catch (error) {
    if (timeoutController.signal.aborted && !parentSignal?.aborted) {
      throw new ApiError(
        'The server is taking too long to respond. Please wait a moment and try again.',
        408,
        'request_timeout',
      );
    }
    const hint = import.meta.env.DEV
      ? 'Start the backend on port 8000, then refresh.'
      : 'Check that the API service is running on Render, then refresh.';
    throw new ApiError(`Cannot reach the ElderGo server. ${hint}`, 0, 'network_error');
  } finally {
    window.clearTimeout(timeoutId);
  }

  if (!response.ok) {
    let message = 'Something went wrong. Please try again.';
    let code: string | undefined;
    try {
      const body = await response.json();
      const parsed = parseErrorDetail(body.detail);
      message = parsed.message;
      code = parsed.code;
    } catch {
      // Keep the elderly-friendly default message.
    }
    throw new ApiError(message, response.status, code);
  }

  return response.json() as Promise<T>;
}
