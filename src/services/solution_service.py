import json
from pathlib import Path
from typing import List, Optional

import numpy as np

from ..classes.types import CVRPInstance, CVRPSolution
from .distance_service import DistanceService


class SolutionService:
    """Handles metrics calculation, method comparison and GeoJSON export."""

    def __init__(self, distance_service: Optional[DistanceService] = None):
        self.distance_service = distance_service or DistanceService()

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def calculate_metrics(
        self,
        instance: CVRPInstance,
        solution: CVRPSolution,
        matrix_distance: np.ndarray,
        baseline_distance_km: Optional[float] = None,
    ) -> dict:
        """
        Return a metrics dict for a solution:
          - total_distance_km
          - num_vehicles
          - vehicles: list of per-vehicle breakdown
          - gain_pct: improvement over baseline (None if not provided)
        """
        vehicle_distances = self.distance_service.vehicle_distance_km(
            solution, matrix_distance
        )
        total_km = self.distance_service.total_distance_km(solution, matrix_distance)
        cap = instance.vehicle_capacity

        vehicles_metrics = []
        for idx, vehicle in enumerate(solution.vehicles):
            occupation = sum(d.size for d in vehicle.deliveries)
            occupation_pct = round(occupation / cap * 100, 1) if cap > 0 else 0.0
            vehicles_metrics.append(
                {
                    **vehicle_distances[idx],
                    "occupation_pct": occupation_pct,
                    "num_deliveries": len(vehicle.deliveries),
                }
            )

        gain_pct = None
        if baseline_distance_km and baseline_distance_km > 0:
            gain_pct = round(
                (baseline_distance_km - total_km) / baseline_distance_km * 100, 2
            )

        return {
            "total_distance_km": total_km,
            "num_vehicles": len(solution.vehicles),
            "vehicles": vehicles_metrics,
            "gain_pct": gain_pct,
        }

    # ------------------------------------------------------------------
    # Comparison across methods
    # ------------------------------------------------------------------

    def compare_methods(
        self,
        city: str,
        instance_name: str,
        methods: List[str],
        out_dir: str = "out",
    ) -> List[dict]:
        """
        Load previously saved solution files and return a comparison list.
        Each entry: { method, total_distance_km, num_vehicles, time_s }
        """
        results = []
        for method in methods:
            path = Path(out_dir) / method / city / instance_name
            if not path.exists():
                results.append(
                    {
                        "method": method,
                        "error": f"File not found: {path}",
                    }
                )
                continue
            with open(path) as f:
                data = json.load(f)

            results.append(
                {
                    "method": method,
                    "num_vehicles": len(data.get("vehicles", [])),
                    "time_s": data.get("time_exec", data.get("time_execution", None)),
                }
            )
        return results

    # ------------------------------------------------------------------
    # GeoJSON export
    # ------------------------------------------------------------------

    def to_geojson(
        self,
        solution: CVRPSolution,
        instance: CVRPInstance,
        matrix_distance: np.ndarray,
    ) -> dict:
        """
        Convert a CVRPSolution to a GeoJSON FeatureCollection.

        Each vehicle route becomes a LineString feature.
        Each delivery becomes a Point feature.
        """
        palette = [
            "#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231",
            "#911eb4", "#42d4f4", "#f032e6", "#bfef45", "#fabed4",
        ]
        cap = instance.vehicle_capacity
        vehicle_distances = self.distance_service.vehicle_distance_km(
            solution, matrix_distance
        )

        features = []
        for idx, vehicle in enumerate(solution.vehicles):
            color = palette[idx % len(palette)]
            occupation = sum(d.size for d in vehicle.deliveries)
            occupation_pct = round(occupation / cap * 100, 1) if cap > 0 else 0.0
            dist_km = vehicle_distances[idx]["distance_km"]

            coords = (
                [[vehicle.origin.lng, vehicle.origin.lat]]
                + [[d.point.lng, d.point.lat] for d in vehicle.deliveries]
                + [[vehicle.origin.lng, vehicle.origin.lat]]
            )

            features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": coords},
                    "properties": {
                        "vehicle_id": idx,
                        "color": color,
                        "distance_km": dist_km,
                        "occupation_pct": occupation_pct,
                        "num_deliveries": len(vehicle.deliveries),
                    },
                }
            )

            for delivery in vehicle.deliveries:
                features.append(
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [delivery.point.lng, delivery.point.lat],
                        },
                        "properties": {
                            "delivery_id": delivery.id,
                            "size": delivery.size,
                            "vehicle_id": idx,
                            "color": color,
                        },
                    }
                )

        return {"type": "FeatureCollection", "features": features}
