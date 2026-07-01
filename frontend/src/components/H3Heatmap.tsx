"use client";

import { useEffect, useRef } from "react";
import type { GeoJSONResponse } from "@/types";

// Resolution level for H3 hexagons (7 = ~5km², good for city-level)
const H3_RESOLUTION = 7;

interface H3HeatmapProps {
  geojson: GeoJSONResponse;
}

export default function H3Heatmap({ geojson }: H3HeatmapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<unknown>(null);

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    Promise.all([
      import("leaflet"),
      import("h3-js"),
    ]).then(([L, h3]) => {
      import("leaflet/dist/leaflet.css");

      const map = L.map(mapRef.current!).setView([-3.0, -47.0], 8);
      mapInstanceRef.current = map;

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "© OpenStreetMap contributors",
      }).addTo(map);

      // Count deliveries per H3 cell
      const cellCount: Record<string, number> = {};

      geojson.features
        .filter((f) => f.geometry.type === "Point")
        .forEach((f) => {
          const [lng, lat] = f.geometry.coordinates as number[];
          const cell = h3.latLngToCell(lat, lng, H3_RESOLUTION);
          cellCount[cell] = (cellCount[cell] ?? 0) + 1;
        });

      const maxCount = Math.max(...Object.values(cellCount), 1);

      // Render each H3 cell as a polygon
      Object.entries(cellCount).forEach(([cell, count]) => {
        const boundary = h3.cellToBoundary(cell);
        const latlngs = boundary.map(([lat, lng]) => [lat, lng] as [number, number]);
        const intensity = count / maxCount;

        const hue = Math.round((1 - intensity) * 240); // blue → red
        const color = `hsl(${hue}, 90%, 55%)`;

        L.polygon(latlngs, {
          fillColor: color,
          fillOpacity: 0.5,
          color: "#fff",
          weight: 0.5,
        })
          .bindPopup(`<b>${count} entregas</b> nesta região`)
          .addTo(map);
      });

      const bounds = geojson.features
        .filter((f) => f.geometry.type === "Point")
        .map((f) => {
          const [lng, lat] = f.geometry.coordinates as number[];
          return [lat, lng] as [number, number];
        });

      if (bounds.length > 0) map.fitBounds(bounds, { padding: [30, 30] });
    });

    return () => {
      if (mapInstanceRef.current) {
        (mapInstanceRef.current as { remove: () => void }).remove();
        mapInstanceRef.current = null;
      }
    };
  }, [geojson]);

  return (
    <div className="flex flex-col gap-2 h-full">
      <div className="flex items-center gap-3 text-xs text-gray-400 px-1">
        <span>Baixa densidade</span>
        <div className="flex-1 h-2 rounded" style={{ background: "linear-gradient(to right, hsl(240,90%,55%), hsl(0,90%,55%))" }} />
        <span>Alta densidade</span>
      </div>
      <div ref={mapRef} className="flex-1 rounded-xl" />
    </div>
  );
}
