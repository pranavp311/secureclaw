// Change this to your Flask server's address.
// iOS simulator: http://localhost:5000
// Android emulator: http://10.0.2.2:5000
// Physical device: http://<your-machine-ip>:5000
export const BASE_URL = "http://10.249.7.250:5001";

// On-device inference can take a while; use a generous timeout.
const TIMEOUT_MS = 120_000;

function fetchWithTimeout(url: string, options: RequestInit = {}): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  return fetch(url, { ...options, signal: controller.signal }).finally(() =>
    clearTimeout(timer),
  );
}

export async function checkOpenClawStatus(): Promise<{
  available: boolean;
  version: string | null;
}> {
  const res = await fetchWithTimeout(`${BASE_URL}/api/openclaw-status`);
  return res.json();
}

export async function analyze(
  message: string,
  tools: string[],
  threshold: number,
) {
  const res = await fetchWithTimeout(`${BASE_URL}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, tools, threshold }),
  });
  return res.json();
}

export async function execute(
  message: string,
  tools: string[],
  mode: string,
  cachedResult?: {
    function_calls: unknown[];
    total_time_ms: number;
    confidence: number;
  },
) {
  const body: Record<string, unknown> = { message, tools, mode };
  if (mode === "local" && cachedResult) {
    body.cached_result = cachedResult;
  }
  const res = await fetchWithTimeout(`${BASE_URL}/api/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return res.json();
}
