"use client";

import { useState, useRef } from "react";
import dynamic from "next/dynamic";
import { streamDynamicOptimize } from "@/lib/api";
import type { CVRPInstance, DynamicBatchEvent, GeoJSONResponse } from "@/types";

const RouteMap = dynamic(() => import("@/components/RouteMap"), { ssr: false });

export default function SimulatePage() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [instance, setInstance] = useState<CVRPInstance | null>(null);
  const [numLotes, setNumLotes] = useState(4);
  const [iterations, setIterations] = useState(5);
  const [delayMs, setDelayMs] = useState(350);
  const [running, setRunning] = useState(false);
  const [batches, setBatches] = useState<DynamicBatchEvent[]>([]);
  const [selectedVehicleIds, setSelectedVehicleIds] = useState<number[]>([]);
  const [expandedVehicleIds, setExpandedVehicleIds] = useState<number[]>([]);
  const [selectedDeliveryKey, setSelectedDeliveryKey] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const stopRef = useRef<(() => void) | null>(null);

  const currentBatch = batches.length > 0 ? batches[batches.length - 1] : null;

  const isVehicleSelected = (vehicleId: number) => selectedVehicleIds.includes(vehicleId);
  const isVehicleExpanded = (vehicleId: number) => expandedVehicleIds.includes(vehicleId);

  const vehicleLoad = (vehicleId: number) => {
    const vehicle = currentBatch?.vehicles.find((v) => v.vehicle_id === vehicleId);
    if (!vehicle) return 0;
    return vehicle.deliveries.reduce((sum, d) => sum + d.size, 0);
  };

  const vehicleOccupationPct = (vehicleId: number) => {
    if (!instance || instance.vehicle_capacity <= 0) return 0;
    return Math.min(100, (vehicleLoad(vehicleId) / instance.vehicle_capacity) * 100);
  };

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setInstance(JSON.parse(await file.text()) as CVRPInstance);
    setBatches([]);
    setSelectedVehicleIds([]);
    setExpandedVehicleIds([]);
    setSelectedDeliveryKey(null);
    setDone(false);
  }

  function buildGeoFromBatch(
    batch: DynamicBatchEvent,
    focusedVehicleIds: number[],
    focusedDeliveryKey: string | null
  ): GeoJSONResponse {
    const palette = ["#e6194b","#3cb44b","#ffe119","#4363d8","#f58231","#911eb4","#42d4f4","#f032e6"];
    const features: GeoJSONResponse["features"] = [];
    const hasVehicleSelection = focusedVehicleIds.length > 0;

    batch.vehicles.forEach((v, idx) => {
      const color = palette[idx % palette.length];
      const isSelectedVehicle = !hasVehicleSelection || focusedVehicleIds.includes(v.vehicle_id);
      // Road-following path computed server-side via OSRM; fall back to
      // straight waypoints only if the backend couldn't provide one.
      const coords =
        v.geometry && v.geometry.length > 1
          ? v.geometry
          : [
              [v.origin.lng, v.origin.lat],
              ...v.deliveries.map((d) => [d.point.lng, d.point.lat]),
              [v.origin.lng, v.origin.lat],
            ];
      features.push({
        type: "Feature",
        geometry: { type: "LineString", coordinates: coords },
        properties: {
          vehicle_id: v.vehicle_id,
          color,
          num_deliveries: v.deliveries.length,
          distance_km: v.distance_km ?? 0,
          occupation_pct: v.occupation_pct ?? 0,
          line_opacity: isSelectedVehicle ? 0.95 : 0.15,
          line_weight: isSelectedVehicle ? 5 : 2,
        },
      });
        v.deliveries.forEach((d, deliveryIdx) => {
          const deliveryKey = `${v.vehicle_id}-${String(d.id)}-${deliveryIdx}`;
          const isSelectedDelivery = focusedDeliveryKey === deliveryKey;
        features.push({
          type: "Feature",
          geometry: { type: "Point", coordinates: [d.point.lng, d.point.lat] },
          properties: {
            delivery_id: d.id,
            size: d.size,
            vehicle_id: v.vehicle_id,
            color,
            delivery_key: deliveryKey,
            point_color: isSelectedDelivery ? "#22d3ee" : color,
            point_radius: isSelectedDelivery ? 8 : 5,
            point_opacity: isSelectedVehicle ? 0.95 : 0.2,
          },
        });
      });
    });
    return { type: "FeatureCollection", features };
  }

  function computeFocusBounds(
    batch: DynamicBatchEvent,
    focusedVehicleIds: number[],
    focusedDeliveryKey: string | null
  ): [number, number][] | undefined {
    // A selected package wins: zoom to it plus its immediate neighbours on
    // the route, so you see the package within its route context.
    if (focusedDeliveryKey) {
      for (const v of batch.vehicles) {
        const idx = v.deliveries.findIndex(
          (d, i) => `${v.vehicle_id}-${String(d.id)}-${i}` === focusedDeliveryKey
        );
        if (idx === -1) continue;

        const prev = idx > 0 ? v.deliveries[idx - 1].point : v.origin;
        const current = v.deliveries[idx].point;
        const next = idx < v.deliveries.length - 1 ? v.deliveries[idx + 1].point : v.origin;
        return [
          [prev.lat, prev.lng],
          [current.lat, current.lng],
          [next.lat, next.lng],
        ];
      }
      return undefined;
    }

    // Otherwise, if vehicle(s) are selected, zoom to just their routes.
    if (focusedVehicleIds.length > 0) {
      const points: [number, number][] = [];
      batch.vehicles
        .filter((v) => focusedVehicleIds.includes(v.vehicle_id))
        .forEach((v) => {
          points.push([v.origin.lat, v.origin.lng]);
          v.deliveries.forEach((d) => points.push([d.point.lat, d.point.lng]));
        });
      return points.length > 0 ? points : undefined;
    }

    return undefined;
  }

  const currentGeo = currentBatch
    ? buildGeoFromBatch(currentBatch, selectedVehicleIds, selectedDeliveryKey)
    : null;

  const focusBounds = currentBatch
    ? computeFocusBounds(currentBatch, selectedVehicleIds, selectedDeliveryKey)
    : undefined;

  function toggleVehicleCard(vehicleId: number) {
    setSelectedVehicleIds((prev) => {
      if (prev.includes(vehicleId)) return prev.filter((id) => id !== vehicleId);
      return [...prev, vehicleId];
    });

    setExpandedVehicleIds((prev) => {
      if (prev.includes(vehicleId)) return prev.filter((id) => id !== vehicleId);
      return [...prev, vehicleId];
    });
  }

  function toggleDelivery(vehicleId: number, deliveryId: string | number, deliveryIdx: number) {
    const key = `${vehicleId}-${String(deliveryId)}-${deliveryIdx}`;
    setSelectedDeliveryKey((prev) => (prev === key ? null : key));
  }

  function handleStart() {
    if (!instance) return;
    setBatches([]);
    setSelectedVehicleIds([]);
    setExpandedVehicleIds([]);
    setSelectedDeliveryKey(null);
    setDone(false);
    setRunning(true);

    const stop = streamDynamicOptimize(
      { instance, num_lotes: numLotes, iterations, delay_ms: delayMs },
      (batch) => {
        setBatches((prev) => [...prev, batch]);
        setSelectedVehicleIds((prev) => prev.filter((id) => batch.vehicles.some((v) => v.vehicle_id === id)));
        setExpandedVehicleIds((prev) => prev.filter((id) => batch.vehicles.some((v) => v.vehicle_id === id)));
        setSelectedDeliveryKey((prev) => {
          if (!prev) return null;
          const validKeys = new Set(
            batch.vehicles.flatMap((v) =>
              v.deliveries.map((d, idx) => `${v.vehicle_id}-${String(d.id)}-${idx}`)
            )
          );
          return validKeys.has(prev) ? prev : null;
        });
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
      {/* ── Vehicle details ── */}
      <aside className="w-96 bg-gray-900 border-r border-gray-800 flex flex-col overflow-hidden">
        <div className="p-5 border-b border-gray-800">
          <h2 className="font-bold text-lg text-blue-400">Detalhes da Rota</h2>
          <p className="text-xs text-gray-500 mt-1">Selecione um veículo para destacar a rota no mapa.</p>
        </div>

        <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
          {!currentBatch || currentBatch.vehicles.length === 0 ? (
            <p className="text-xs text-gray-600">Sem rotas para exibir no lote atual.</p>
          ) : (
            <>
              <p className="text-[11px] text-gray-500">
                Padrão: todas as rotas destacadas. Clique nos cards para selecionar rotas específicas.
              </p>

              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setSelectedVehicleIds([]);
                    setSelectedDeliveryKey(null);
                  }}
                  className="bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded px-2 py-1 text-[11px] text-gray-200"
                >
                  Mostrar todas
                </button>
                <button
                  type="button"
                  onClick={() => setExpandedVehicleIds([])}
                  className="bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded px-2 py-1 text-[11px] text-gray-200"
                >
                  Recolher cards
                </button>
              </div>

              <div className="flex flex-col gap-2">
                {currentBatch.vehicles.map((vehicle) => {
                  const selected = isVehicleSelected(vehicle.vehicle_id);
                  const expanded = isVehicleExpanded(vehicle.vehicle_id);
                  const load = vehicleLoad(vehicle.vehicle_id);
                  const occupation = vehicleOccupationPct(vehicle.vehicle_id);

                  return (
                    <div
                      key={vehicle.vehicle_id}
                      className={`rounded-lg border ${selected ? "border-cyan-400 bg-cyan-500/10" : "border-gray-700 bg-gray-800"}`}
                    >
                      <button
                        type="button"
                        onClick={() => toggleVehicleCard(vehicle.vehicle_id)}
                        className="w-full text-left px-3 py-2 flex items-center justify-between"
                      >
                        <div className="flex flex-col">
                          <span className="text-xs font-medium text-gray-100">Veículo {vehicle.vehicle_id}</span>
                          <span className="text-[11px] text-gray-400">
                            {vehicle.deliveries.length} entregas | carga {load}
                          </span>
                        </div>
                        <span className="text-[11px] text-gray-300">{expanded ? "Ocultar" : "Detalhar"}</span>
                      </button>

                      {expanded && (
                        <div className="px-3 pb-3 text-xs flex flex-col gap-2 border-t border-gray-700/70">
                          <div className="pt-2 flex justify-between text-gray-300">
                            <span>Ocupação</span>
                            <span>{occupation.toFixed(1)}%</span>
                          </div>
                          <div className="flex justify-between text-gray-300">
                            <span>Origem</span>
                            <span>{vehicle.origin.lat.toFixed(5)}, {vehicle.origin.lng.toFixed(5)}</span>
                          </div>

                          <div className="text-gray-400 mt-1">Sequência da rota</div>
                          <div className="max-h-40 overflow-y-auto flex flex-col gap-1 pr-1">
                            {vehicle.deliveries.map((d, idx) => {
                              const key = `${vehicle.vehicle_id}-${String(d.id)}-${idx}`;
                              const selectedDelivery = selectedDeliveryKey === key;
                              return (
                                <button
                                  type="button"
                                  key={key}
                                  onClick={() => toggleDelivery(vehicle.vehicle_id, d.id, idx)}
                                  className={`text-left rounded px-2 py-1 text-[11px] ${selectedDelivery ? "bg-cyan-500/20 text-cyan-200 border border-cyan-500/40" : "bg-gray-900/70 text-gray-300 border border-transparent"}`}
                                >
                                  <div>{idx + 1}. Entrega {String(d.id)} | size {d.size}</div>
                                  <div className="text-gray-500">Lat {d.point.lat.toFixed(5)} | Lng {d.point.lng.toFixed(5)}</div>
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>
      </aside>

      {/* ── Map ── */}
      <div className="flex-1 p-3">
        {currentGeo ? (
          <RouteMap geojson={currentGeo} focusBounds={focusBounds} />
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

          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-400">Delay entre lotes: <span className="text-blue-400 font-mono">{delayMs} ms</span></label>
            <input type="range" min={0} max={2000} step={50} value={delayMs} onChange={(e) => setDelayMs(+e.target.value)} className="accent-blue-500" />
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
