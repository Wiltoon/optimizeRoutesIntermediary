"use client";

import { useEffect, useRef } from "react";
import type { GeoJSONResponse } from "@/types";

interface RouteMapProps {
  geojson: GeoJSONResponse;
}

export default function RouteMap({ geojson }: RouteMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<unknown>(null);

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    // Dynamic import: Leaflet requires window
    import("leaflet").then((L) => {
      import("leaflet/dist/leaflet.css");

      const map = L.map(mapRef.current!).setView([-3.0, -47.0], 8);
      mapInstanceRef.current = map;

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "© OpenStreetMap contributors",
      }).addTo(map);

      const bounds: [number, number][] = [];

      geojson.features.forEach((feature) => {
        const color = (feature.properties.color as string) ?? "#3b82f6";

        if (feature.geometry.type === "LineString") {
          const coords = feature.geometry.coordinates as number[][];
          const latlngs = coords.map(([lng, lat]) => [lat, lng] as [number, number]);
          bounds.push(...latlngs);

          L.polyline(latlngs, { color, weight: 3, opacity: 0.85 })
            .bindPopup(`
              <b>Veículo ${feature.properties.vehicle_id}</b><br/>
              ${feature.properties.num_deliveries} entregas<br/>
              ${(feature.properties.distance_km as number).toFixed(2)} km<br/>
              Ocupação: ${feature.properties.occupation_pct}%
            `)
            .addTo(map);
        }

        if (feature.geometry.type === "Point") {
          const [lng, lat] = feature.geometry.coordinates as number[];
          bounds.push([lat, lng]);

          const icon = L.circleMarker([lat, lng], {
            radius: 5,
            fillColor: color,
            color: "#fff",
            weight: 1,
            fillOpacity: 0.9,
          });
          icon
            .bindPopup(`
              <b>Entrega ${feature.properties.delivery_id}</b><br/>
              Tamanho: ${feature.properties.size}<br/>
              Veículo ${feature.properties.vehicle_id}
            `)
            .addTo(map);
        }
      });

      if (bounds.length > 0) {
        map.fitBounds(bounds, { padding: [30, 30] });
      }
    });

    return () => {
      if (mapInstanceRef.current) {
        (mapInstanceRef.current as { remove: () => void }).remove();
        mapInstanceRef.current = null;
      }
    };
  }, [geojson]);

  return <div ref={mapRef} className="w-full h-full rounded-xl" />;
}
