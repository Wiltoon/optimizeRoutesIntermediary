import os
from functools import lru_cache
from typing import Optional

import redis as redis_lib

from ..classes.distances import OSRMConfig
from ..services.distance_service import DistanceService
from ..services.optimization_service import OptimizationService
from ..services.solution_service import SolutionService


@lru_cache(maxsize=1)
def get_osrm_config() -> OSRMConfig:
    return OSRMConfig(
        host=os.getenv("OSRM_HOST", "http://localhost:5000"),
        timeout_s=int(os.getenv("OSRM_TIMEOUT_S", "600")),
        route_timeout_s=int(os.getenv("OSRM_ROUTE_TIMEOUT_S", "5")),
    )


def get_redis() -> Optional[redis_lib.Redis]:
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        client = redis_lib.from_url(url, decode_responses=True, socket_connect_timeout=2)
        client.ping()
        return client
    except Exception:
        return None


def get_distance_service() -> DistanceService:
    return DistanceService(osrm_config=get_osrm_config())


def get_optimization_service() -> OptimizationService:
    return OptimizationService(distance_service=get_distance_service())


def get_solution_service() -> SolutionService:
    return SolutionService(distance_service=get_distance_service())

