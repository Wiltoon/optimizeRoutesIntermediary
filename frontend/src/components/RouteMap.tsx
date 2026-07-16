"use client";

import { useEffect, useRef } from "react";
import type { GeoJSONResponse } from "@/types";

interface RouteMapProps {
  geojson: GeoJSONResponse;
}

export default function RouteMap({ geojson }: RouteMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<unknown>(null);
  const layerGroupRef = useRef<unknown>(null);

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;
    let cancelled = false;

    // Dynamic import: Leaflet requires window
    import("leaflet").then((L) => {
      if (cancelled || !mapRef.current || mapInstanceRef.current) return;
      import("leaflet/dist/leaflet.css");

      const map = L.map(mapRef.current!).setView([-3.0, -47.0], 8);
      mapInstanceRef.current = map;
      layerGroupRef.current = L.layerGroup().addTo(map);

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "© OpenStreetMap contributors",
      }).addTo(map);
    });

    return () => {
      cancelled = true;
      if (mapInstanceRef.current) {
        (mapInstanceRef.current as { remove: () => void }).remove();
        mapInstanceRef.current = null;
        layerGroupRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!mapInstanceRef.current || !layerGroupRef.current) return;
    let cancelled = false;

    import("leaflet").then((L) => {
      if (cancelled) return;

      const map = mapInstanceRef.current as {
        fitBounds: (bounds: [number, number][], options?: { padding: [number, number] }) => void;
      };
      const layerGroup = layerGroupRef.current as { clearLayers: () => void };
      layerGroup.clearLayers();

      const bounds: [number, number][] = [];

      geojson.features.forEach((feature) => {
        const color = (feature.properties.color as string) ?? "#3b82f6";
        const lineOpacity = Number(feature.properties.line_opacity ?? 0.85);
        const lineWeight = Number(feature.properties.line_weight ?? 3);
        const pointOpacity = Number(feature.properties.point_opacity ?? 0.9);
        const pointColor = (feature.properties.point_color as string) ?? color;
        const pointRadius = Number(feature.properties.point_radius ?? 5);

        if (feature.geometry.type === "LineString") {
          // Geometry is already road-following (computed server-side via OSRM,
          // with a straight-waypoint fallback baked in) — draw it as-is.
          const coords = feature.geometry.coordinates as number[][];
          const latlngs = coords.map(([lng, lat]) => [lat, lng] as [number, number]);
          bounds.push(...latlngs);

          L.polyline(latlngs, { color, weight: lineWeight, opacity: lineOpacity })
            .bindPopup(`
              <b>Veículo ${feature.properties.vehicle_id}</b><br/>
              ${feature.properties.num_deliveries} entregas<br/>
              ${(feature.properties.distance_km as number).toFixed(2)} km<br/>
              Ocupação: ${feature.properties.occupation_pct}%
            `)
            .addTo(layerGroup as unknown as L.LayerGroup);
        }

        if (feature.geometry.type === "Point") {
          const [lng, lat] = feature.geometry.coordinates as number[];
          bounds.push([lat, lng]);

          const icon = L.circleMarker([lat, lng], {
            radius: pointRadius,
            fillColor: pointColor,
            color: "#fff",
            weight: 1,
            fillOpacity: pointOpacity,
            opacity: pointOpacity,
          });
          icon
            .bindPopup(`
              <b>Entrega ${feature.properties.delivery_id}</b><br/>
              Tamanho: ${feature.properties.size}<br/>
              Veículo ${feature.properties.vehicle_id}
            `)
            .addTo(layerGroup as unknown as L.LayerGroup);
        }
      });

      if (bounds.length > 0) {
        map.fitBounds(bounds, { padding: [30, 30] });
      }
    });

    return () => {
      cancelled = true;
    };
  }, [geojson]);

  return <div ref={mapRef} className="w-full h-full rounded-xl" />;
}
