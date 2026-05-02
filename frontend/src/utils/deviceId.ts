const DEVICE_ID_KEY = 'eldergo_device_id';

export function getOrCreateDeviceId(): string {
  // Stable local identifier enables anonymous profile restore across sessions.
  const existing = localStorage.getItem(DEVICE_ID_KEY);
  if (existing) return existing;

  const deviceId = `device_${crypto.randomUUID()}`;
  localStorage.setItem(DEVICE_ID_KEY, deviceId);
  return deviceId;
}
