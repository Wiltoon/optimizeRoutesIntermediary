import type {
  CVRPInstance,
  OptimizeResponse,
  CompareResponse,
  GeoJSONResponse,
  MetricsResponse,
  DynamicBatchEvent,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function handleJsonResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API error ${res.status}: ${body || res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export async function optimizeRoutes(payload: {
  instance: CVRPInstance;
  iterations?: number;
  method?: string;
  city?: string;
}): Promise<OptimizeResponse> {
  const res = await fetch(`${API_BASE}/api/v1/routes/optimize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleJsonResponse<OptimizeResponse>(res);
}

export async function compareMethods(
  city: string,
  instanceName: string,
  methods: string[]
): Promise<CompareResponse> {
  const params = new URLSearchParams({ instance_name: instanceName });
  methods.forEach((m) => params.append("methods", m));

  const res = await fetch(
    `${API_BASE}/api/v1/instances/${encodeURIComponent(city)}/solutions/compare?${params.toString()}`
  );
  return handleJsonResponse<CompareResponse>(res);
}

export async function getGeoJSON(solutionId: string): Promise<GeoJSONResponse> {
  const res = await fetch(`${API_BASE}/api/v1/routes/${encodeURIComponent(solutionId)}/geojson`);
  return handleJsonResponse<GeoJSONResponse>(res);
}

export async function getSolutionMetrics(
  solutionId: string,
  baselineKm?: number
): Promise<MetricsResponse> {
  const query = baselineKm != null ? `?baseline_km=${baselineKm}` : "";
  const res = await fetch(
    `${API_BASE}/api/v1/solutions/${encodeURIComponent(solutionId)}/metrics${query}`
  );
  return handleJsonResponse<MetricsResponse>(res);
}

/**
 * Streams /api/v1/routes/simulate-dynamic (Server-Sent Events over POST).
 * Native EventSource can't POST a body, so the SSE framing is parsed by hand
 * from a fetch() ReadableStream instead.
 *
 * Returns a `stop` function that aborts the in-flight request.
 */
export function streamDynamicOptimize(
  payload: {
    instance: CVRPInstance;
    num_lotes: number;
    iterations: number;
    delay_ms: number;
  },
  onBatch: (batch: DynamicBatchEvent) => void,
  onDone: () => void,
  onError: (err: unknown) => void
): () => void {
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/routes/simulate-dynamic`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      if (!res.ok || !res.body) {
        throw new Error(`API error ${res.status}: ${res.statusText}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const frames = buffer.split("\n\n");
        buffer = frames.pop() ?? "";

        for (const frame of frames) {
          const line = frame.trim();
          if (!line.startsWith("data:")) continue;

          const json = line.slice("data:".length).trim();
          if (!json) continue;

          const parsed = JSON.parse(json) as DynamicBatchEvent & { done?: boolean };
          if (parsed.done) {
            onDone();
            return;
          }
          onBatch(parsed);
        }
      }

      onDone();
    } catch (err) {
      if (controller.signal.aborted) return;
      onError(err);
    }
  })();

  return () => controller.abort();
}
