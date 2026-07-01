import json

import numpy as np
from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_distance_service, get_redis, get_solution_service
from ..schemas.solution_schemas import GeoJSONFeature, GeoJSONGeometry, GeoJSONResponse
from ...classes.types import (
    CVRPInstance,
    CVRPSolution,
    CVRPSolutionVehicle,
    Delivery,
    Point,
)
from ...services.solution_service import SolutionService
from ...services.distance_service import DistanceService

router = APIRouter(prefix="/api/v1/routes", tags=["visualization"])

PALETTE = [
    "#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231",
    "#911eb4", "#42d4f4", "#f032e6", "#bfef45", "#fabed4",
]


def _rebuild_solution(data: dict) -> tuple:
    """Reconstruct lightweight CVRPSolution and CVRPInstance from cached JSON."""
    vehicles = []
    all_deliveries = []
    for v in data.get("vehicles", []):
        origin = Point(lng=v["origin"]["lng"], lat=v["origin"]["lat"])
        deliveries = [
            Delivery(
                id=d["id"],
                point=Point(lng=d["point"]["lng"], lat=d["point"]["lat"]),
                size=d["size"],
                idu=d["idu"],
            )
            for d in v.get("deliveries", [])
        ]
        all_deliveries.extend(deliveries)
        vehicles.append(CVRPSolutionVehicle(origin=origin, deliveries=deliveries))

    solution = CVRPSolution(
        name=data.get("solution_id", "unknown"),
        vehicles=vehicles,
    )
    return solution, all_deliveries


# ─────────────────────────────────────────────
# API 5 — GET /api/v1/routes/{solution_id}/geojson
# ─────────────────────────────────────────────
@router.get(
    "/{solution_id}/geojson",
    response_model=GeoJSONResponse,
    summary="Export solution as GeoJSON FeatureCollection",
)
def get_geojson(
    solution_id: str,
    redis=Depends(get_redis),
):
    """
    Convert a stored solution into a GeoJSON FeatureCollection.
    Each vehicle route becomes a LineString; each delivery becomes a Point.
    Ready for direct use in Mapbox / Leaflet / Google Maps.
    """
    if redis is None:
        raise HTTPException(status_code=503, detail="Cache unavailable")

    raw = redis.get(f"solution:{solution_id}")
    if raw is None:
        raise HTTPException(status_code=404, detail=f"Solution '{solution_id}' not found")

    data = json.loads(raw)
    features = []

    for idx, vehicle in enumerate(data.get("vehicles", [])):
        color = PALETTE[idx % len(PALETTE)]
        origin = vehicle["origin"]
        deliveries = vehicle.get("deliveries", [])
        occupation_pct = vehicle.get("occupation_pct", 0.0)
        dist_km = vehicle.get("distance_km", 0.0)

        route_coords = (
            [[origin["lng"], origin["lat"]]]
            + [[d["point"]["lng"], d["point"]["lat"]] for d in deliveries]
            + [[origin["lng"], origin["lat"]]]
        )

        features.append(
            GeoJSONFeature(
                geometry=GeoJSONGeometry(type="LineString", coordinates=route_coords),
                properties={
                    "vehicle_id": idx,
                    "color": color,
                    "distance_km": dist_km,
                    "occupation_pct": occupation_pct,
                    "num_deliveries": len(deliveries),
                },
            )
        )

        for delivery in deliveries:
            features.append(
                GeoJSONFeature(
                    geometry=GeoJSONGeometry(
                        type="Point",
                        coordinates=[delivery["point"]["lng"], delivery["point"]["lat"]],
                    ),
                    properties={
                        "delivery_id": delivery["id"],
                        "size": delivery["size"],
                        "vehicle_id": idx,
                        "color": color,
                    },
                )
            )

    return GeoJSONResponse(features=features)

