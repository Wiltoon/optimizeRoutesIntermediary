"""
Unit tests for OptimizationService and DistanceService.
OSRM HTTP calls are fully mocked — no network required.
"""
import numpy as np
import pytest

from src.classes.types import (
    CVRPInstance,
    CVRPSolution,
    CVRPSolutionVehicle,
    Delivery,
    Point,
)
from src.services.distance_service import DistanceService
from src.services.optimization_service import OptimizationService
from src.services.solution_service import SolutionService


# ─────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────

@pytest.fixture()
def small_instance():
    origin = Point(lng=-47.93, lat=-1.29)
    deliveries = [
        Delivery(id=f"d{i}", point=Point(lng=-47.93 + i * 0.01, lat=-1.29 + i * 0.01), size=10, idu=i)
        for i in range(4)
    ]
    return CVRPInstance(
        name="test-instance",
        region="test",
        origin=origin,
        vehicle_capacity=30,
        deliveries=deliveries,
    )


@pytest.fixture()
def initial_solution(small_instance):
    vehicles = [
        CVRPSolutionVehicle(origin=small_instance.origin, deliveries=[d])
        for d in small_instance.deliveries
    ]
    return CVRPSolution(name=small_instance.name, vehicles=vehicles)


@pytest.fixture()
def fixed_matrix():
    """5×5 deterministic distance matrix (origin + 4 deliveries)."""
    rng = np.random.default_rng(0)
    n = 5
    m = rng.integers(500, 15_000, size=(n, n)).astype(float)
    np.fill_diagonal(m, 0)
    return m


@pytest.fixture()
def dist_service(fixed_matrix, monkeypatch):
    from src.services import distance_service as ds_mod
    monkeypatch.setattr(ds_mod, "calculate_distance_matrix_m", lambda *a, **kw: fixed_matrix)
    return DistanceService()


@pytest.fixture()
def opt_service(dist_service):
    return OptimizationService(distance_service=dist_service)


@pytest.fixture()
def sol_service(dist_service):
    return SolutionService(distance_service=dist_service)


# ─────────────────────────────────────────────────────────────
# DistanceService tests
# ─────────────────────────────────────────────────────────────

class TestDistanceService:

    def test_build_matrix_returns_numpy_array(self, dist_service, small_instance):
        matrix = dist_service.build_matrix(small_instance)
        assert isinstance(matrix, np.ndarray)

    def test_matrix_shape(self, dist_service, small_instance, fixed_matrix):
        matrix = dist_service.build_matrix(small_instance)
        assert matrix.shape == fixed_matrix.shape

    def test_total_distance_km_is_positive(self, dist_service, small_instance, initial_solution, fixed_matrix):
        total = dist_service.total_distance_km(initial_solution, fixed_matrix)
        assert total > 0

    def test_vehicle_distance_km_length(self, dist_service, initial_solution, fixed_matrix):
        breakdown = dist_service.vehicle_distance_km(initial_solution, fixed_matrix)
        assert len(breakdown) == len(initial_solution.vehicles)

    def test_vehicle_distance_km_ids(self, dist_service, initial_solution, fixed_matrix):
        breakdown = dist_service.vehicle_distance_km(initial_solution, fixed_matrix)
        ids = [v["vehicle_id"] for v in breakdown]
        assert ids == list(range(len(initial_solution.vehicles)))


# ─────────────────────────────────────────────────────────────
# OptimizationService tests
# ─────────────────────────────────────────────────────────────

class TestOptimizationService:

    def test_optimize_returns_expected_keys(self, opt_service, small_instance, initial_solution):
        result = opt_service.optimize(small_instance, initial_solution, iterations=1)
        assert set(result.keys()) == {"solution", "total_distance_km", "num_vehicles", "time_s"}

    def test_optimize_solution_covers_all_deliveries(self, opt_service, small_instance, initial_solution):
        result = opt_service.optimize(small_instance, initial_solution, iterations=1)
        solution = result["solution"]
        # solutionJson rebuilds deliveries using idu as the key, so compare by idu
        delivered_idus = {d.idu for v in solution.vehicles for d in v.deliveries}
        expected_idus = {d.idu for d in small_instance.deliveries}
        assert delivered_idus == expected_idus

    def test_optimize_respects_vehicle_capacity(self, opt_service, small_instance, initial_solution):
        result = opt_service.optimize(small_instance, initial_solution, iterations=1)
        cap = small_instance.vehicle_capacity
        for vehicle in result["solution"].vehicles:
            total = sum(d.size for d in vehicle.deliveries)
            assert total <= cap, f"Vehicle over capacity: {total} > {cap}"

    def test_optimize_time_is_positive(self, opt_service, small_instance, initial_solution):
        result = opt_service.optimize(small_instance, initial_solution, iterations=1)
        assert result["time_s"] > 0

    def test_optimize_dynamic_yields_batches(self, opt_service, small_instance, initial_solution):
        num_lotes = 2
        batches = list(opt_service.optimize_dynamic(small_instance, initial_solution, num_lotes=num_lotes, iterations=1))
        assert len(batches) == num_lotes

    def test_optimize_dynamic_batch_keys(self, opt_service, small_instance, initial_solution):
        batches = list(opt_service.optimize_dynamic(small_instance, initial_solution, num_lotes=2, iterations=1))
        for batch in batches:
            assert "batch_index" in batch
            assert "solution" in batch
            assert "total_distance_km" in batch


# ─────────────────────────────────────────────────────────────
# SolutionService tests
# ─────────────────────────────────────────────────────────────

class TestSolutionService:

    def test_calculate_metrics_structure(self, sol_service, small_instance, initial_solution, fixed_matrix):
        metrics = sol_service.calculate_metrics(small_instance, initial_solution, fixed_matrix)
        assert "total_distance_km" in metrics
        assert "num_vehicles" in metrics
        assert "vehicles" in metrics
        assert "gain_pct" in metrics

    def test_calculate_metrics_gain_pct_none_without_baseline(self, sol_service, small_instance, initial_solution, fixed_matrix):
        metrics = sol_service.calculate_metrics(small_instance, initial_solution, fixed_matrix)
        assert metrics["gain_pct"] is None

    def test_calculate_metrics_gain_pct_with_baseline(self, sol_service, small_instance, initial_solution, fixed_matrix):
        metrics = sol_service.calculate_metrics(small_instance, initial_solution, fixed_matrix, baseline_distance_km=999.0)
        assert metrics["gain_pct"] is not None

    def test_calculate_metrics_occupation_pct_in_range(self, sol_service, small_instance, initial_solution, fixed_matrix):
        metrics = sol_service.calculate_metrics(small_instance, initial_solution, fixed_matrix)
        for v in metrics["vehicles"]:
            assert 0 <= v["occupation_pct"] <= 100

    def test_to_geojson_is_feature_collection(self, sol_service, small_instance, initial_solution, fixed_matrix):
        geojson = sol_service.to_geojson(initial_solution, small_instance, fixed_matrix)
        assert geojson["type"] == "FeatureCollection"
        assert isinstance(geojson["features"], list)

    def test_to_geojson_has_linestrings_and_points(self, sol_service, small_instance, initial_solution, fixed_matrix):
        geojson = sol_service.to_geojson(initial_solution, small_instance, fixed_matrix)
        types = {f["geometry"]["type"] for f in geojson["features"]}
        assert "LineString" in types
        assert "Point" in types

