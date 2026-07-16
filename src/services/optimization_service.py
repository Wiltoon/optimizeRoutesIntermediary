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

    @staticmethod
    def _compact_active_routes(vehicles_possible: dict) -> dict:
        # A valid route must contain depot + at least one delivery.
        active = [route for route in vehicles_possible.values() if len(route) > 1]
        return {idx: route for idx, route in enumerate(active)}

    @staticmethod
    def _route_load(instance: CVRPInstance, route: list[int]) -> int:
        return sum(instance.deliveries[idu].size for idu in route[1:])

    def _consolidate_routes_by_capacity(
        self, instance: CVRPInstance, vehicles_possible: dict
    ) -> dict:
        """
        Greedy consolidation pass: move all deliveries from a lighter route
        into a heavier route whenever capacity allows.
        """
        routes = [route[:] for route in vehicles_possible.values() if len(route) > 1]
        if len(routes) < 2:
            return {idx: route for idx, route in enumerate(routes)}

        cap = instance.vehicle_capacity

        changed = True
        while changed:
            changed = False
            indexed = list(enumerate(routes))
            # Try to eliminate lighter routes first.
            indexed.sort(key=lambda item: self._route_load(instance, item[1]))

            for src_idx, src_route in indexed:
                if len(src_route) <= 1:
                    continue

                src_load = self._route_load(instance, src_route)
                targets = [
                    (idx, route)
                    for idx, route in enumerate(routes)
                    if idx != src_idx and len(route) > 1
                ]
                # Prefer tighter packing to reduce vehicle count quickly.
                targets.sort(
                    key=lambda item: self._route_load(instance, item[1]),
                    reverse=True,
                )

                for dst_idx, dst_route in targets:
                    dst_load = self._route_load(instance, dst_route)
                    if dst_load + src_load <= cap:
                        routes[dst_idx] = dst_route + src_route[1:]
                        routes[src_idx] = [0]
                        changed = True
                        break

                if changed:
                    routes = [route for route in routes if len(route) > 1]
                    break

        return {idx: route for idx, route in enumerate(routes)}

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
            vehiclesPossibles = self._compact_active_routes(vehiclesPossibles)
            all_ids = list(range(len(vehiclesPossibles)))
            combs = list(combinations(all_ids, 2))

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

            vehiclesPossibles = self._compact_active_routes(vehiclesPossibles)

        vehiclesPossibles = self._consolidate_routes_by_capacity(instance, vehiclesPossibles)
        new_solution = solutionJson(instance, vehiclesPossibles)

        elapsed = round(time.time() - start, 4)

        total_km = calculateSolutionMatrix(new_solution, matrix_distance)

        return {
            "solution": new_solution,
            "total_distance_km": total_km,
            "num_vehicles": len(new_solution.vehicles),
            "time_s": elapsed,
            "matrix_distance": matrix_distance,
        }

    def optimize_dynamic(
        self,
        instance: CVRPInstance,
        solution: CVRPSolution,
        num_lotes: int,
        iterations: int = 10,
        delay_ms: int = 0,
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

            start = time.time()
            for _ in range(iterations):
                vehiclesPossibles = self._compact_active_routes(vehiclesPossibles)
                all_ids = list(range(len(vehiclesPossibles)))
                combs = list(combinations(all_ids, 2))

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

            vehiclesPossibles = self._compact_active_routes(vehiclesPossibles)
            vehiclesPossibles = self._consolidate_routes_by_capacity(instance, vehiclesPossibles)
            elapsed = round(time.time() - start, 4)

            partial_solution = solutionJson(instance, vehiclesPossibles)
            total_km = calculateSolutionMatrix(partial_solution, matrix_distance)

            if delay_ms > 0:
                time.sleep(delay_ms / 1000)

            yield {
                "batch_index": batch_idx,
                "solution": partial_solution,
                "total_distance_km": total_km,
                "num_vehicles": len(partial_solution.vehicles),
                "time_s": elapsed,
                "matrix_distance": matrix_distance,
            }
