const DEBUG_ENDPOINT = 'http://127.0.0.1:7267/ingest/af3fa6c2-77fe-4e06-a79f-1e670577b9b2';
const DEBUG_SESSION = 'ce83c2';

export function debugLog(
  location: string,
  message: string,
  data: Record<string, unknown> = {},
  hypothesisId?: string
) {
  const payload = {
    sessionId: DEBUG_SESSION,
    location,
    message,
    data,
    hypothesisId,
    timestamp: Date.now(),
    runId: (data.runId as string | undefined) ?? 'pre-fix'
  };
  // #region agent log
  fetch(DEBUG_ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Debug-Session-Id': DEBUG_SESSION },
    body: JSON.stringify(payload)
  }).catch(() => {});
  // #endregion
}
