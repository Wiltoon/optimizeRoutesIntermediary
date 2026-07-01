from typing import Optional, List
import numpy as np

from ..classes.types import CVRPInstance, CVRPSolution
from ..classes.distances import (
    OSRMConfig,
    calculate_distance_matrix_m,
    calculate_distance_matrix_great_circle_m,
)


class DistanceService:
    """Wraps OSRM and great-circle distance computation with an injectable config."""

    def __init__(self, osrm_config: Optional[OSRMConfig] = None):
        self.config = osrm_config or OSRMConfig()

    def build_matrix(self, instance: CVRPInstance) -> np.ndarray:
        """Return a full distance matrix (meters) for origin + all deliveries."""
        origin = [instance.origin]
        deliveries = [d.point for d in instance.deliveries]
        points = [*origin, *deliveries]
        return calculate_distance_matrix_m(points, self.config)

    def build_matrix_great_circle(self, instance: CVRPInstance) -> np.ndarray:
        """Fallback matrix using great-circle distances (no OSRM required)."""
        origin = [instance.origin]
        deliveries = [d.point for d in instance.deliveries]
        points = [*origin, *deliveries]
        return calculate_distance_matrix_great_circle_m(points)

    def total_distance_km(
        self, solution: CVRPSolution, matrix_distance: np.ndarray
    ) -> float:
        """Return total route distance in kilometres for a given solution."""
        total = 0.0
        for vehicle in solution.vehicles:
            route = [0] + [d.idu + 1 for d in vehicle.deliveries]
            for i in range(len(route) - 1):
                total += matrix_distance[route[i]][route[i + 1]]
        return round(total / 1_000, 4)

    def vehicle_distance_km(
        self, solution: CVRPSolution, matrix_distance: np.ndarray
    ) -> List[dict]:
        """Return per-vehicle distance breakdown in kilometres."""
        result = []
        for idx, vehicle in enumerate(solution.vehicles):
            route = [0] + [d.idu + 1 for d in vehicle.deliveries]
            dist = 0.0
            for i in range(len(route) - 1):
                dist += matrix_distance[route[i]][route[i + 1]]
            result.append({"vehicle_id": idx, "distance_km": round(dist / 1_000, 4)})
        return result
