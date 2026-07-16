"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import { getGeoJSON, getSolutionMetrics } from "@/lib/api";
import type { GeoJSONResponse, MetricsResponse } from "@/types";

const RouteMap = dynamic(() => import("@/components/RouteMap"), { ssr: false });
const H3Heatmap = dynamic(() => import("@/components/H3Heatmap"), { ssr: false });

type Tab = "routes" | "heatmap";

function DashboardContent() {
  const params = useSearchParams();
  const solutionId = params.get("id") ?? "";

  const [geojson, setGeojson] = useState<GeoJSONResponse | null>(null);
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [tab, setTab] = useState<Tab>("routes");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!solutionId) return;
    Promise.all([getGeoJSON(solutionId), getSolutionMetrics(solutionId)])
      .then(([geo, met]) => { setGeojson(geo); setMetrics(met); })
      .catch((e) => setError(e.message));
  }, [solutionId]);

  if (error) return <p className="p-8 text-red-400">{error}</p>;
  if (!geojson || !metrics) {
    return (
      <div className="flex items-center justify-center h-[80vh] text-gray-400">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <p>Carregando solução...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-57px)]">
      <div className="flex-1 flex flex-col">
        <div className="flex gap-2 p-3 bg-gray-900 border-b border-gray-800">
          {(["routes", "heatmap"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                tab === t ? "bg-blue-600 text-white" : "text-gray-400 hover:text-white"
              }`}
            >
              {t === "routes" ? "🗺 Rotas" : "🔷 Heatmap H3"}
            </button>
          ))}
          <span className="ml-auto text-xs text-gray-500 self-center">ID: {solutionId}</span>
        </div>
        <div className="flex-1 p-3">
          {tab === "routes" ? <RouteMap geojson={geojson} /> : <H3Heatmap geojson={geojson} />}
        </div>
      </div>

      <aside className="w-80 bg-gray-900 border-l border-gray-800 flex flex-col overflow-y-auto">
        <div className="p-5 border-b border-gray-800">
          <h2 className="font-bold text-lg text-blue-400 mb-4">Métricas</h2>
          <div className="grid grid-cols-2 gap-3">
            <StatCard label="Distância total" value={`${metrics.total_distance_km.toFixed(2)} km`} />
            <StatCard label="Veículos usados" value={String(metrics.num_vehicles)} />
            <StatCard label="Ganho" value={metrics.gain_pct != null ? `${metrics.gain_pct}%` : "—"} highlight={!!metrics.gain_pct} />
            <StatCard label="Entregas" value={String(metrics.vehicles.reduce((s, v) => s + v.num_deliveries, 0))} />
          </div>
        </div>
        <div className="p-5 flex flex-col gap-3 overflow-y-auto">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">Por veículo</h3>
          {metrics.vehicles.map((v) => (
            <div key={v.vehicle_id} className="bg-gray-800 rounded-xl p-4 flex flex-col gap-2">
              <div className="flex justify-between text-sm">
                <span className="font-medium">Veículo {v.vehicle_id}</span>
                <span className="text-gray-400">{v.num_deliveries} entregas</span>
              </div>
              <div className="flex justify-between text-xs text-gray-400">
                <span>{v.distance_km.toFixed(2)} km</span>
                <span>{v.occupation_pct}% ocupado</span>
              </div>
              <div className="h-1.5 bg-gray-700 rounded-full">
                <div className="h-full rounded-full bg-blue-500" style={{ width: `${v.occupation_pct}%` }} />
              </div>
            </div>
          ))}
        </div>
      </aside>
    </div>
  );
}

function StatCard({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="bg-gray-800 rounded-xl p-3">
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      <p className={`font-bold text-lg ${highlight ? "text-green-400" : "text-white"}`}>{value}</p>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center h-[80vh] text-gray-400">
        <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    }>
      <DashboardContent />
    </Suspense>
  );
}
