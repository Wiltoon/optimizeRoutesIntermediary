"use client";

import { useState } from "react";
import { compareMethods } from "@/lib/api";
import type { CompareResponse } from "@/types";

const METHODS = ["kpmip", "krs", "krso", "dinamic"];

export default function ComparePage() {
  const [city, setCity] = useState("pa-0");
  const [instanceName, setInstanceName] = useState("cvrp-0-pa-100.json");
  const [selectedMethods, setSelectedMethods] = useState(METHODS);
  const [result, setResult] = useState<CompareResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function toggleMethod(m: string) {
    setSelectedMethods((prev) =>
      prev.includes(m) ? prev.filter((x) => x !== m) : [...prev, m]
    );
  }

  async function handleCompare() {
    setLoading(true);
    setError(null);
    try {
      setResult(await compareMethods(city, instanceName, selectedMethods));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro");
    } finally {
      setLoading(false);
    }
  }

  const best = result?.results
    .filter((r) => r.total_distance_km != null)
    .reduce((a, b) => (a.total_distance_km! < b.total_distance_km! ? a : b), {} as (typeof result.results)[0]);

  return (
    <div className="p-8 max-w-4xl mx-auto flex flex-col gap-8">
      <div>
        <h1 className="text-3xl font-bold text-blue-400">Comparar Métodos</h1>
        <p className="text-gray-400 mt-1">Compare os resultados de diferentes algoritmos para uma mesma instância</p>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 flex flex-col gap-5">
        <div className="grid grid-cols-2 gap-4">
          <div className="flex flex-col gap-1">
            <label className="text-sm text-gray-400">Cidade</label>
            <input
              value={city} onChange={(e) => setCity(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
              placeholder="pa-0"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-gray-400">Arquivo da instância</label>
            <input
              value={instanceName} onChange={(e) => setInstanceName(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
              placeholder="cvrp-0-pa-100.json"
            />
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <label className="text-sm text-gray-400">Métodos</label>
          <div className="flex gap-2 flex-wrap">
            {METHODS.map((m) => (
              <button
                key={m}
                onClick={() => toggleMethod(m)}
                className={`px-3 py-1 rounded-lg text-sm font-mono transition-colors ${
                  selectedMethods.includes(m)
                    ? "bg-blue-600 text-white"
                    : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                }`}
              >
                {m}
              </button>
            ))}
          </div>
        </div>

        {error && <p className="text-red-400 text-sm bg-red-950 rounded-lg px-4 py-2">{error}</p>}

        <button
          onClick={handleCompare}
          disabled={loading || selectedMethods.length === 0}
          className="bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-semibold py-2.5 rounded-xl transition-colors"
        >
          {loading ? "Comparando..." : "Comparar"}
        </button>
      </div>

      {result && (
        <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-800">
            <p className="text-sm text-gray-400">{result.city} / {result.instance_name}</p>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-400 text-xs uppercase tracking-wide border-b border-gray-800">
                <th className="px-6 py-3 text-left">Método</th>
                <th className="px-6 py-3 text-right">Distância (km)</th>
                <th className="px-6 py-3 text-right">Veículos</th>
                <th className="px-6 py-3 text-right">Tempo (s)</th>
              </tr>
            </thead>
            <tbody>
              {result.results.map((r) => (
                <tr
                  key={r.method}
                  className={`border-b border-gray-800 last:border-0 transition-colors ${
                    best?.method === r.method ? "bg-green-950/40" : "hover:bg-gray-800/50"
                  }`}
                >
                  <td className="px-6 py-4 font-mono font-medium">
                    {r.method}
                    {best?.method === r.method && (
                      <span className="ml-2 text-xs text-green-400">✓ melhor</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right">
                    {r.error ? <span className="text-red-400 text-xs">não encontrado</span> : (r.total_distance_km?.toFixed(2) ?? "—")}
                  </td>
                  <td className="px-6 py-4 text-right">{r.num_vehicles ?? "—"}</td>
                  <td className="px-6 py-4 text-right">{r.time_s?.toFixed(2) ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
