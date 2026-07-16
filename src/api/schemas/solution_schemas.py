from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VehicleMetrics(BaseModel):
    vehicle_id: int
    distance_km: float
    occupation_pct: float = Field(..., ge=0, le=100)
    num_deliveries: int


class MetricsResponse(BaseModel):
    solution_id: str
    total_distance_km: float
    num_vehicles: int
    vehicles: List[VehicleMetrics]
    gain_pct: Optional[float] = Field(
        default=None,
        description="Percentage improvement over the baseline solution. "
                    "Null when no baseline is available.",
    )


class CompareEntry(BaseModel):
    method: str
    total_distance_km: Optional[float] = None
    num_vehicles: Optional[int] = None
    time_s: Optional[float] = None
    error: Optional[str] = None


class CompareResponse(BaseModel):
    city: str
    instance_name: str
    results: List[CompareEntry]


class GeoJSONGeometry(BaseModel):
    type: str
    coordinates: List[Any]


class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: GeoJSONGeometry
    properties: Dict[str, Any]


class GeoJSONResponse(BaseModel):
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]

