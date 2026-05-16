export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

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
    throw error;
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
