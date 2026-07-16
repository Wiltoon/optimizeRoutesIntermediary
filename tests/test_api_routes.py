"""
Integration tests for all 5 API endpoints using FastAPI TestClient.
Redis and OSRM are mocked — no external services required.
"""
import json

import pytest

# fixtures are imported from conftest.py automatically


# ─────────────────────────────────────────────────────────────
# GET /health
# ─────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


# ─────────────────────────────────────────────────────────────
# API 1 — POST /api/v1/routes/optimize
# ─────────────────────────────────────────────────────────────

class TestOptimizeRoute:

    def test_returns_200(self, client, optimize_payload):
        resp = client.post("/api/v1/routes/optimize", json=optimize_payload)
        assert resp.status_code == 200

    def test_response_has_expected_keys(self, client, optimize_payload):
        resp = client.post("/api/v1/routes/optimize", json=optimize_payload)
        data = resp.json()
        assert "solution_id" in data
        assert "vehicles" in data
        assert "total_distance_km" in data
        assert "num_vehicles" in data
        assert "time_s" in data

    def test_solution_id_is_string(self, client, optimize_payload):
        resp = client.post("/api/v1/routes/optimize", json=optimize_payload)
        assert isinstance(resp.json()["solution_id"], str)

    def test_num_vehicles_positive(self, client, optimize_payload):
        resp = client.post("/api/v1/routes/optimize", json=optimize_payload)
        assert resp.json()["num_vehicles"] > 0

    def test_total_distance_positive(self, client, optimize_payload):
        resp = client.post("/api/v1/routes/optimize", json=optimize_payload)
        assert resp.json()["total_distance_km"] > 0

    def test_second_call_returns_same_solution_id(self, client, optimize_payload):
        """Identical request must hit cache and return same solution_id."""
        id1 = client.post("/api/v1/routes/optimize", json=optimize_payload).json()["solution_id"]
        id2 = client.post("/api/v1/routes/optimize", json=optimize_payload).json()["solution_id"]
        assert id1 == id2

    def test_different_iterations_different_id(self, client, optimize_payload):
        """Different parameters must produce a different cache key."""
        payload_a = {**optimize_payload, "iterations": 1}
        payload_b = {**optimize_payload, "iterations": 2}
        id_a = client.post("/api/v1/routes/optimize", json=payload_a).json()["solution_id"]
        id_b = client.post("/api/v1/routes/optimize", json=payload_b).json()["solution_id"]
        assert id_a != id_b

    def test_invalid_payload_returns_422(self, client):
        resp = client.post("/api/v1/routes/optimize", json={"iterations": 5})
        assert resp.status_code == 422

    def test_vehicle_capacity_zero_returns_422(self, client, optimize_payload):
        bad = json.loads(json.dumps(optimize_payload))
        bad["instance"]["vehicle_capacity"] = 0
        resp = client.post("/api/v1/routes/optimize", json=bad)
        assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────
# API 2 — GET /api/v1/solutions/{id}/metrics
# ─────────────────────────────────────────────────────────────

class TestMetricsRoute:

    def test_returns_200_for_stored_solution(self, client, stored_solution_id):
        resp = client.get(f"/api/v1/solutions/{stored_solution_id}/metrics")
        assert resp.status_code == 200

    def test_metrics_keys(self, client, stored_solution_id):
        resp = client.get(f"/api/v1/solutions/{stored_solution_id}/metrics")
        data = resp.json()
        assert "solution_id" in data
        assert "total_distance_km" in data
        assert "num_vehicles" in data
        assert "vehicles" in data
        assert "gain_pct" in data

    def test_gain_pct_none_without_baseline(self, client, stored_solution_id):
        resp = client.get(f"/api/v1/solutions/{stored_solution_id}/metrics")
        assert resp.json()["gain_pct"] is None

    def test_gain_pct_present_with_baseline(self, client, stored_solution_id):
        resp = client.get(f"/api/v1/solutions/{stored_solution_id}/metrics?baseline_km=999")
        assert resp.json()["gain_pct"] is not None

    def test_unknown_id_returns_404(self, client):
        resp = client.get("/api/v1/solutions/nonexistent_id/metrics")
        assert resp.status_code == 404

    def test_occupation_pct_in_range(self, client, stored_solution_id):
        resp = client.get(f"/api/v1/solutions/{stored_solution_id}/metrics")
        for v in resp.json()["vehicles"]:
            assert 0 <= v["occupation_pct"] <= 100


# ─────────────────────────────────────────────────────────────
# API 3 — GET /api/v1/instances/{city}/solutions/compare
# ─────────────────────────────────────────────────────────────

class TestCompareRoute:

    def test_returns_200(self, client):
        resp = client.get(
            "/api/v1/instances/pa-0/solutions/compare",
            params={"instance_name": "cvrp-0-pa-100.json", "methods": ["kpmip"]},
        )
        assert resp.status_code == 200

    def test_response_structure(self, client):
        resp = client.get(
            "/api/v1/instances/pa-0/solutions/compare",
            params={"instance_name": "cvrp-0-pa-100.json", "methods": ["kpmip"]},
        )
        data = resp.json()
        assert data["city"] == "pa-0"
        assert data["instance_name"] == "cvrp-0-pa-100.json"
        assert isinstance(data["results"], list)

    def test_missing_method_returns_error_entry(self, client):
        """When the output file doesn't exist, the entry has an 'error' field."""
        resp = client.get(
            "/api/v1/instances/pa-0/solutions/compare",
            params={"instance_name": "nonexistent.json", "methods": ["kpmip"]},
        )
        assert resp.status_code == 200
        result = resp.json()["results"][0]
        assert "error" in result

    def test_missing_instance_name_returns_422(self, client):
        resp = client.get("/api/v1/instances/pa-0/solutions/compare")
        assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────
# API 4 — POST /api/v1/routes/simulate-dynamic (SSE)
# ─────────────────────────────────────────────────────────────

class TestDynamicRoute:

    def test_returns_200_streaming(self, client, optimize_payload):
        payload = {**optimize_payload, "num_lotes": 2}
        resp = client.post("/api/v1/routes/simulate-dynamic", json=payload)
        assert resp.status_code == 200

    def test_content_type_is_event_stream(self, client, optimize_payload):
        payload = {**optimize_payload, "num_lotes": 2}
        resp = client.post("/api/v1/routes/simulate-dynamic", json=payload)
        assert "text/event-stream" in resp.headers["content-type"]

    def test_stream_contains_data_events(self, client, optimize_payload):
        payload = {**optimize_payload, "num_lotes": 2}
        resp = client.post("/api/v1/routes/simulate-dynamic", json=payload)
        lines = [l for l in resp.text.splitlines() if l.startswith("data:")]
        assert len(lines) >= 2  # at least num_lotes events + done

    def test_stream_events_are_valid_json(self, client, optimize_payload):
        payload = {**optimize_payload, "num_lotes": 2}
        resp = client.post("/api/v1/routes/simulate-dynamic", json=payload)
        for line in resp.text.splitlines():
            if line.startswith("data:"):
                json.loads(line[len("data:"):].strip())  # must not raise

    def test_invalid_payload_returns_422(self, client):
        resp = client.post("/api/v1/routes/simulate-dynamic", json={"num_lotes": 2})
        assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────
# API 5 — GET /api/v1/routes/{id}/geojson
# ─────────────────────────────────────────────────────────────

class TestGeoJSONRoute:

    def test_returns_200(self, client, stored_solution_id):
        resp = client.get(f"/api/v1/routes/{stored_solution_id}/geojson")
        assert resp.status_code == 200

    def test_is_feature_collection(self, client, stored_solution_id):
        data = client.get(f"/api/v1/routes/{stored_solution_id}/geojson").json()
        assert data["type"] == "FeatureCollection"

    def test_has_features(self, client, stored_solution_id):
        data = client.get(f"/api/v1/routes/{stored_solution_id}/geojson").json()
        assert len(data["features"]) > 0

    def test_linestring_and_point_present(self, client, stored_solution_id):
        data = client.get(f"/api/v1/routes/{stored_solution_id}/geojson").json()
        geom_types = {f["geometry"]["type"] for f in data["features"]}
        assert "LineString" in geom_types
        assert "Point" in geom_types

    def test_linestring_properties(self, client, stored_solution_id):
        data = client.get(f"/api/v1/routes/{stored_solution_id}/geojson").json()
        lines = [f for f in data["features"] if f["geometry"]["type"] == "LineString"]
        for line in lines:
            props = line["properties"]
            assert "vehicle_id" in props
            assert "color" in props
            assert "num_deliveries" in props

    def test_unknown_id_returns_404(self, client):
        resp = client.get("/api/v1/routes/nonexistent_id/geojson")
        assert resp.status_code == 404

