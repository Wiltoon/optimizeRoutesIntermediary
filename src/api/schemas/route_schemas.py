from typing import List, Optional, Union
from pydantic import BaseModel, Field


class PointSchema(BaseModel):
    lng: float = Field(..., description="Longitude")
    lat: float = Field(..., description="Latitude")


class DeliverySchema(BaseModel):
    id: Union[str, int]
    point: PointSchema
    size: int = Field(..., gt=0)
    idu: int = Field(default=0)


class CVRPInstanceSchema(BaseModel):
    name: str
    region: str = ""
    origin: PointSchema
    vehicle_capacity: int = Field(..., gt=0)
    deliveries: List[DeliverySchema] = Field(..., min_length=1)


class OptimizeRequest(BaseModel):
    instance: CVRPInstanceSchema
    solution_id: Optional[str] = Field(
        default=None,
        description="ID of an existing solution to use as starting point. "
                    "If omitted the service uses the instance as-is.",
    )
    iterations: int = Field(default=10, ge=1, le=100)
    method: str = Field(default="api")
    city: str = Field(default="unknown")


class VehicleRouteSchema(BaseModel):
    vehicle_id: int
    deliveries: List[DeliverySchema]
    origin: PointSchema
    geometry: Optional[List[List[float]]] = Field(
        default=None,
        description="Road-following [lng, lat] path from OSRM; falls back to "
                    "straight waypoints if OSRM is unavailable.",
    )
    distance_km: Optional[float] = Field(default=None, description="Route distance in km")
    occupation_pct: Optional[float] = Field(
        default=None, description="Vehicle capacity used, as a percentage"
    )


class OptimizeResponse(BaseModel):
    solution_id: str
    vehicles: List[VehicleRouteSchema]
    total_distance_km: float
    num_vehicles: int
    time_s: float


class DynamicOptimizeRequest(BaseModel):
    instance: CVRPInstanceSchema
    num_lotes: int = Field(default=4, ge=1, le=50)
    iterations: int = Field(default=10, ge=1, le=100)
    delay_ms: int = Field(default=0, ge=0, le=5000)


class DynamicBatchEvent(BaseModel):
    batch_index: int
    vehicles: List[VehicleRouteSchema]
    total_distance_km: float
    num_vehicles: int
    time_s: float

