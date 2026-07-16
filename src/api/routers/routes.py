import hashlib
import json
from dataclasses import asdict
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ..dependencies import get_optimization_service, get_redis, get_solution_service
from ..schemas.route_schemas import (
    DynamicBatchEvent,
    DynamicOptimizeRequest,
    OptimizeRequest,
    OptimizeResponse,
    VehicleRouteSchema,
)
from ...classes.types import (
    CVRPInstance,
    CVRPSolution,
    CVRPSolutionVehicle,
    Delivery,
    Point,
)
from ...services.distance_service import DistanceService
from ...services.optimization_service import OptimizationService
from ...services.solution_service import SolutionService

router = APIRouter(prefix="/api/v1/routes", tags=["routes"])

SOLUTION_TTL = 3600  # seconds


def _build_instance(data) -> CVRPInstance:
    origin = Point(lng=data.origin.lng, lat=data.origin.lat)
    deliveries = [
        Delivery(
            id=d.id,
            point=Point(lng=d.point.lng, lat=d.point.lat),
            size=d.size,
            idu=d.idu,
        )
        for d in data.deliveries
    ]
    return CVRPInstance(
        name=data.name,
        region=data.region,
        origin=origin,
        vehicle_capacity=data.vehicle_capacity,
        deliveries=deliveries,
    )


def _solution_to_response_vehicles(
    solution: CVRPSolution,
    dist_service: DistanceService,
    matrix_distance,
    vehicle_capacity: int,
):
    vehicle_distances = dist_service.vehicle_distance_km(solution, matrix_distance)

    vehicles = []
    for idx, v in enumerate(solution.vehicles):
        load = sum(d.size for d in v.deliveries)
        occupation_pct = round(load / vehicle_capacity * 100, 1) if vehicle_capacity > 0 else 0.0

        vehicles.append(
            VehicleRouteSchema(
                vehicle_id=idx,
                origin={"lng": v.origin.lng, "lat": v.origin.lat},
                deliveries=[
                    {
                        "id": d.id,
                        "point": {"lng": d.point.lng, "lat": d.point.lat},
                        "size": d.size,
                        "idu": d.idu,
                    }
                    for d in v.deliveries
                ],
                geometry=dist_service.vehicle_route_geometry(v),
                distance_km=vehicle_distances[idx]["distance_km"],
                occupation_pct=occupation_pct,
            )
        )
    return vehicles


def _make_solution_id(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ─────────────────────────────────────────────
# API 1 — POST /api/v1/routes/optimize
# ─────────────────────────────────────────────
@router.post("/optimize", response_model=OptimizeResponse, summary="Optimise routes (2-opt*)")
def optimize_routes(
    body: OptimizeRequest,
    opt_service: OptimizationService = Depends(get_optimization_service),
    sol_service: SolutionService = Depends(get_solution_service),
    redis=Depends(get_redis),
):
    solution_id = _make_solution_id(body.model_dump())

    # return cached result if available
    if redis:
        cached = redis.get(f"solution:{solution_id}")
        if cached:
            return json.loads(cached)

    instance = _build_instance(body.instance)

    # build a trivial initial solution (one vehicle per delivery) when no
    # starting solution is provided
    vehicles = [
        CVRPSolutionVehicle(origin=instance.origin, deliveries=[d])
        for d in instance.deliveries
    ]
    initial_solution = CVRPSolution(name=instance.name, vehicles=vehicles)

    result = opt_service.optimize(
        instance=instance,
        solution=initial_solution,
        iterations=body.iterations,
        city=body.city,
        method=body.method,
    )

    dist_service = opt_service.distance_service
    response = OptimizeResponse(
        solution_id=solution_id,
        vehicles=_solution_to_response_vehicles(
            result["solution"], dist_service, result["matrix_distance"], instance.vehicle_capacity
        ),
        total_distance_km=result["total_distance_km"],
        num_vehicles=result["num_vehicles"],
        time_s=result["time_s"],
    )

    if redis:
        redis.setex(
            f"solution:{solution_id}",
            SOLUTION_TTL,
            response.model_dump_json(),
        )

    return response


# ─────────────────────────────────────────────
# API 4 — POST /api/v1/routes/simulate-dynamic
# ─────────────────────────────────────────────
@router.post("/simulate-dynamic", summary="Dynamic batch optimisation (SSE stream)")
def simulate_dynamic(
    body: DynamicOptimizeRequest,
    opt_service: OptimizationService = Depends(get_optimization_service),
):
    instance = _build_instance(body.instance)

    vehicles = [
        CVRPSolutionVehicle(origin=instance.origin, deliveries=[d])
        for d in instance.deliveries
    ]
    initial_solution = CVRPSolution(name=instance.name, vehicles=vehicles)

    dist_service = opt_service.distance_service

    def event_stream():
        for batch in opt_service.optimize_dynamic(
            instance=instance,
            solution=initial_solution,
            num_lotes=body.num_lotes,
            iterations=body.iterations,
            delay_ms=body.delay_ms,
        ):
            event = DynamicBatchEvent(
                batch_index=batch["batch_index"],
                vehicles=_solution_to_response_vehicles(
                    batch["solution"], dist_service, batch["matrix_distance"], instance.vehicle_capacity
                ),
                total_distance_km=batch["total_distance_km"],
                num_vehicles=batch["num_vehicles"],
                time_s=batch["time_s"],
            )
            yield f"data: {event.model_dump_json()}\n\n"
        yield "data: {\"done\": true}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

