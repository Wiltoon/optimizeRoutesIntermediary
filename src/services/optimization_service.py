import copy
import time
from itertools import combinations
from typing import Generator, Optional

import numpy as np

from ..classes.types import CVRPInstance, CVRPSolution
from ..classes.distances import OSRMConfig
from ..interRoute import twoOptStar, twoOptStarModificated
from ..operations import (
    createVehiclesPossibles,
    solutionJson,
    solutionJsonWithTime,
)
from ..computeDistances import calculateSolutionMatrix
from .distance_service import DistanceService


class OptimizationService:
    """Encapsulates the 2-opt* neighbourhood search (rotineIntermediary)."""

    def __init__(self, distance_service: Optional[DistanceService] = None):
        self.distance_service = distance_service or DistanceService()

    def optimize(
        self,
        instance: CVRPInstance,
        solution: CVRPSolution,
        iterations: int = 10,
        city: str = "unknown",
        method: str = "api",
    ) -> dict:
        """
        Run 2-opt* and 2-opt*-modified for `iterations` rounds.

        Returns a dict with:
          - solution: optimised CVRPSolution
          - total_distance_km: float
          - num_vehicles: int
          - time_s: float
        """
        matrix_distance = self.distance_service.build_matrix(instance)

        new_solution = copy.copy(solution)
        vehiclesPossibles = createVehiclesPossibles(new_solution)

        all_ids = list(range(len(vehiclesPossibles)))
        combs = list(combinations(all_ids, 2))

        start = time.time()

        for _ in range(iterations):
            for c in combs:
                vehiclesPossibles[c[0]], vehiclesPossibles[c[1]] = twoOptStar(
                    vehiclesPossibles[c[0]],
                    vehiclesPossibles[c[1]],
                    matrix_distance,
                    instance,
                )
            for c in combs:
                vehiclesPossibles[c[0]], vehiclesPossibles[c[1]] = twoOptStarModificated(
                    vehiclesPossibles[c[0]],
                    vehiclesPossibles[c[1]],
                    matrix_distance,
                    instance,
                )
            new_solution = solutionJson(instance, vehiclesPossibles)

        elapsed = round(time.time() - start, 4)

        total_km = calculateSolutionMatrix(new_solution, matrix_distance)

        return {
            "solution": new_solution,
            "total_distance_km": total_km,
            "num_vehicles": len(new_solution.vehicles),
            "time_s": elapsed,
        }

    def optimize_dynamic(
        self,
        instance: CVRPInstance,
        solution: CVRPSolution,
        num_lotes: int,
        iterations: int = 10,
    ) -> Generator[dict, None, None]:
        """
        Yield partial optimised solutions, one per batch.

        Always uses the full instance for constraint checks so that idu values
        from previous batches remain valid when new deliveries are added.

        Each yielded dict has the same shape as `optimize()` return value,
        plus `batch_index: int`.
        """
        matrix_distance = self.distance_service.build_matrix(instance)
        deliveries = instance.deliveries

        batch_size = max(1, len(deliveries) // num_lotes)
        batches = [
            deliveries[i : i + batch_size]
            for i in range(0, len(deliveries), batch_size)
        ]

        vehiclesPossibles: dict = {}

        for batch_idx, batch in enumerate(batches):
            # Add each new delivery as its own vehicle
            for d in batch:
                new_key = len(vehiclesPossibles)
                vehiclesPossibles[new_key] = [0, d.idu]

            all_ids = list(range(len(vehiclesPossibles)))
            combs = list(combinations(all_ids, 2))

            start = time.time()
            for _ in range(iterations):
                for c in combs:
                    if c[0] in vehiclesPossibles and c[1] in vehiclesPossibles:
                        vehiclesPossibles[c[0]], vehiclesPossibles[c[1]] = twoOptStar(
                            vehiclesPossibles[c[0]],
                            vehiclesPossibles[c[1]],
                            matrix_distance,
                            instance,
                        )
                for c in combs:
                    if c[0] in vehiclesPossibles and c[1] in vehiclesPossibles:
                        vehiclesPossibles[c[0]], vehiclesPossibles[c[1]] = twoOptStarModificated(
                            vehiclesPossibles[c[0]],
                            vehiclesPossibles[c[1]],
                            matrix_distance,
                            instance,
                        )
            elapsed = round(time.time() - start, 4)

            partial_solution = solutionJson(instance, vehiclesPossibles)
            total_km = calculateSolutionMatrix(partial_solution, matrix_distance)

            yield {
                "batch_index": batch_idx,
                "solution": partial_solution,
                "total_distance_km": total_km,
                "num_vehicles": len(partial_solution.vehicles),
                "time_s": elapsed,
            }
