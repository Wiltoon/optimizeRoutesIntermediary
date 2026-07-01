"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import { streamDynamicOptimize } from "@/lib/api";
import type { CVRPInstance, DynamicBatchEvent, GeoJSONResponse } from "@/types";

const RouteMap = dynamic(() => import("@/components/RouteMap"), { ssr: false });

export default function SimulatePage() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [instance, setInstance] = useState<CVRPInstance | null>(null);
  const [numLotes, setNumLotes] = useState(4);
  const [iterations, setIterations] = useState(5);
  const [running, setRunning] = useState(false);
  const [batches, setBatches] = useState<DynamicBatchEvent[]>([]);
  const [currentGeo, setCurrentGeo] = useState<GeoJSONResponse | null>(null);
  const [done, setDone] = useState(false);
  const stopRef = useRef<(() => void) | null>(null);

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setInstance(JSON.parse(await file.text()) as CVRPInstance);
    setBatches([]);
    setCurrentGeo(null);
    setDone(false);
  }

  function buildGeoFromBatch(batch: DynamicBatchEvent): GeoJSONResponse {
    const palette = ["#e6194b","#3cb44b","#ffe119","#4363d8","#f58231","#911eb4","#42d4f4","#f032e6"];
    const features: GeoJSONResponse["features"] = [];

    batch.vehicles.forEach((v, idx) => {
      const color = palette[idx % palette.length];
      const coords = [
        [v.origin.lng, v.origin.lat],
        ...v.deliveries.map((d) => [d.point.lng, d.point.lat]),
        [v.origin.lng, v.origin.lat],
      ];
      features.push({
        type: "Feature",
        geometry: { type: "LineString", coordinates: coords },
        properties: { vehicle_id: idx, color, num_deliveries: v.deliveries.length, distance_km: 0, occupation_pct: 0 },
      });
      v.deliveries.forEach((d) => {
        features.push({
          type: "Feature",
          geometry: { type: "Point", coordinates: [d.point.lng, d.point.lat] },
          properties: { delivery_id: d.id, size: d.size, vehicle_id: idx, color },
        });
      });
    });
    return { type: "FeatureCollection", features };
  }

  function handleStart() {
    if (!instance) return;
    setBatches([]);
    setCurrentGeo(null);
    setDone(false);
    setRunning(true);

    const stop = streamDynamicOptimize(
      { instance, num_lotes: numLotes, iterations },
      (batch) => {
        setBatches((prev) => [...prev, batch]);
        setCurrentGeo(buildGeoFromBatch(batch));
      },
      () => { setRunning(false); setDone(true); },
      () => { setRunning(false); }
    );
    stopRef.current = stop;
  }

  function handleStop() {
    stopRef.current?.();
    setRunning(false);
  }

  return (
    <div className="flex h-[calc(100vh-57px)]">
      {/* ── Map ── */}
      <div className="flex-1 p-3">
        {currentGeo ? (
          <RouteMap geojson={currentGeo} />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-600 border-2 border-dashed border-gray-800 rounded-xl">
            <p>O mapa aparece aqui em tempo real durante a simulação</p>
          </div>
        )}
      </div>

      {/* ── Controls & log ── */}
      <aside className="w-80 bg-gray-900 border-l border-gray-800 flex flex-col overflow-hidden">
        <div className="p-5 border-b border-gray-800 flex flex-col gap-4">
          <h2 className="font-bold text-lg text-blue-400">Simulação Dinâmica</h2>

          <div
            onClick={() => fileRef.current?.click()}
            className="border border-dashed border-gray-700 rounded-xl p-4 text-center cursor-pointer hover:border-blue-500 transition-colors text-sm"
          >
            <input ref={fileRef} type="file" accept=".json" className="hidden" onChange={handleFile} />
            {instance ? (
              <span className="text-green-400">✓ {instance.name} <span className="text-gray-500">({instance.deliveries.length} entregas)</span></span>
            ) : (
              <span className="text-gray-500">Carregar instância .json</span>
            )}
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-400">Lotes: <span className="text-blue-400 font-mono">{numLotes}</span></label>
            <input type="range" min={2} max={20} value={numLotes} onChange={(e) => setNumLotes(+e.target.value)} className="accent-blue-500" />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-400">Iterações por lote: <span className="text-blue-400 font-mono">{iterations}</span></label>
            <input type="range" min={1} max={20} value={iterations} onChange={(e) => setIterations(+e.target.value)} className="accent-blue-500" />
          </div>

          {running ? (
            <button onClick={handleStop} className="bg-red-600 hover:bg-red-500 text-white font-semibold py-2.5 rounded-xl transition-colors">
              ⏹ Parar
            </button>
          ) : (
            <button
              onClick={handleStart}
              disabled={!instance}
              className="bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-semibold py-2.5 rounded-xl transition-colors"
            >
              ▶ Iniciar simulação
            </button>
          )}

          {done && <p className="text-center text-green-400 text-sm">✓ Simulação concluída</p>}
        </div>

        {/* Batch log */}
        <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-2">
          <p className="text-xs text-gray-500 uppercase tracking-wide">Log de lotes</p>
          {batches.length === 0 && <p className="text-xs text-gray-600">Aguardando...</p>}
          {[...batches].reverse().map((b) => (
            <div key={b.batch_index} className="bg-gray-800 rounded-lg p-3 text-xs flex flex-col gap-1">
              <div className="flex justify-between font-medium">
                <span>Lote {b.batch_index + 1}</span>
                <span className="text-gray-400">{b.time_s.toFixed(2)}s</span>
              </div>
              <div className="flex justify-between text-gray-400">
                <span>{b.num_vehicles} veículos</span>
                <span>{b.total_distance_km.toFixed(2)} km</span>
              </div>
            </div>
          ))}
        </div>
      </aside>
    </div>
  );
}
