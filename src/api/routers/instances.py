from typing import List

from fastapi import APIRouter, Depends, Query

from ..dependencies import get_solution_service
from ..schemas.solution_schemas import CompareResponse, CompareEntry
from ...services.solution_service import SolutionService

router = APIRouter(prefix="/api/v1/instances", tags=["instances"])

AVAILABLE_METHODS = ["kpmip", "krs", "krso", "dinamic"]


# ─────────────────────────────────────────────
# API 3 — GET /api/v1/instances/{city}/solutions/compare
# ─────────────────────────────────────────────
@router.get(
    "/{city}/solutions/compare",
    response_model=CompareResponse,
    summary="Compare optimisation methods for a city instance",
)
def compare_solutions(
    city: str,
    instance_name: str = Query(..., description="JSON filename, e.g. cvrp-0-pa-100.json"),
    methods: List[str] = Query(
        default=AVAILABLE_METHODS,
        description="Methods to compare",
    ),
    out_dir: str = Query(default="out", description="Root output directory"),
    sol_service: SolutionService = Depends(get_solution_service),
):
    """
    Load pre-computed solution files from `out/{method}/{city}/{instance_name}`
    and return a side-by-side comparison table.
    """
    results_raw = sol_service.compare_methods(
        city=city,
        instance_name=instance_name,
        methods=methods,
        out_dir=out_dir,
    )

    results = [CompareEntry(**r) for r in results_raw]

    return CompareResponse(
        city=city,
        instance_name=instance_name,
        results=results,
    )

