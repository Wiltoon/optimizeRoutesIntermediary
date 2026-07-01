from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_distance_service, get_redis, get_solution_service
from ..schemas.solution_schemas import MetricsResponse, VehicleMetrics
from ...classes.types import CVRPInstance, CVRPSolution
from ...services.solution_service import SolutionService
from ...services.distance_service import DistanceService

router = APIRouter(prefix="/api/v1/solutions", tags=["solutions"])


def _load_solution_from_redis(solution_id: str, redis) -> dict:
    if redis is None:
        raise HTTPException(status_code=503, detail="Cache unavailable")
    raw = redis.get(f"solution:{solution_id}")
    if raw is None:
        raise HTTPException(status_code=404, detail=f"Solution '{solution_id}' not found")
    return json.loads(raw)


# ─────────────────────────────────────────────
# API 2 — GET /api/v1/solutions/{solution_id}/metrics
# ─────────────────────────────────────────────
@router.get(
    "/{solution_id}/metrics",
    response_model=MetricsResponse,
    summary="Detailed metrics for a stored solution",
)
def get_solution_metrics(
    solution_id: str,
    baseline_km: Optional[float] = None,
    redis=Depends(get_redis),
    sol_service: SolutionService = Depends(get_solution_service),
    dist_service: DistanceService = Depends(get_distance_service),
):
    """
    Return per-vehicle distance, capacity occupation % and overall gain
    compared to `baseline_km` (optional query param).
    """
    data = _load_solution_from_redis(solution_id, redis)

    vehicles_metrics = []
    total_km = 0.0
    for v in data.get("vehicles", []):
        dist = v.get("distance_km", 0.0)
        total_km += dist
        vehicles_metrics.append(
            VehicleMetrics(
                vehicle_id=v["vehicle_id"],
                distance_km=dist,
                occupation_pct=v.get("occupation_pct", 0.0),
                num_deliveries=v.get("num_deliveries", len(v.get("deliveries", []))),
            )
        )

    gain_pct = None
    if baseline_km and baseline_km > 0:
        gain_pct = round((baseline_km - total_km) / baseline_km * 100, 2)

    return MetricsResponse(
        solution_id=solution_id,
        total_distance_km=round(total_km, 4),
        num_vehicles=len(vehicles_metrics),
        vehicles=vehicles_metrics,
        gain_pct=gain_pct,
    )

