"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { optimizeRoutes } from "@/lib/api";
import type { CVRPInstance } from "@/types";

export default function HomePage() {
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);
  const [instance, setInstance] = useState<CVRPInstance | null>(null);
  const [iterations, setIterations] = useState(10);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    try {
      setInstance(JSON.parse(text) as CVRPInstance);
      setError(null);
    } catch {
      setError("Arquivo JSON inválido.");
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!instance) return;
    setLoading(true);
    setError(null);
    try {
      const result = await optimizeRoutes({ instance, iterations });
      router.push(`/dashboard?id=${result.solution_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] gap-8 p-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-blue-400 mb-2">Otimização de Rotas</h1>
        <p className="text-gray-400">Carregue uma instância CVRP e encontre as rotas otimizadas</p>
      </div>

      <form onSubmit={handleSubmit} className="bg-gray-900 border border-gray-800 rounded-2xl p-8 w-full max-w-lg flex flex-col gap-6">
        <div
          onClick={() => fileRef.current?.click()}
          className="border-2 border-dashed border-gray-700 rounded-xl p-8 text-center cursor-pointer hover:border-blue-500 transition-colors"
        >
          <input ref={fileRef} type="file" accept=".json" className="hidden" onChange={handleFile} />
          {instance ? (
            <div className="text-green-400">
              <p className="font-semibold">✓ {instance.name}</p>
              <p className="text-sm text-gray-400">{instance.deliveries.length} entregas · capacidade {instance.vehicle_capacity}</p>
            </div>
          ) : (
            <p className="text-gray-500">Clique para carregar um arquivo <span className="text-blue-400">.json</span> de instância CVRP</p>
          )}
        </div>

        <div className="flex flex-col gap-2">
          <label className="text-sm text-gray-400 font-medium">Iterações do 2-opt*</label>
          <div className="flex items-center gap-4">
            <input
              type="range" min={1} max={50} value={iterations}
              onChange={(e) => setIterations(Number(e.target.value))}
              className="flex-1 accent-blue-500"
            />
            <span className="w-8 text-right font-mono text-blue-400">{iterations}</span>
          </div>
        </div>

        {error && <p className="text-red-400 text-sm bg-red-950 rounded-lg px-4 py-2">{error}</p>}

        <button
          type="submit"
          disabled={!instance || loading}
          className="bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-xl transition-colors"
        >
          {loading ? "Otimizando..." : "🚀 Otimizar rotas"}
        </button>
      </form>

      <div className="flex gap-4 text-sm text-gray-500">
        <a href="/compare" className="hover:text-blue-400 transition-colors">→ Comparar métodos</a>
        <a href="/simulate" className="hover:text-blue-400 transition-colors">→ Simulação dinâmica</a>
      </div>
    </div>
  );
}
