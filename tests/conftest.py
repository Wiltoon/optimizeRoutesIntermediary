import json
import pathlib
from unittest.mock import MagicMock

import numpy as np
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.dependencies import get_redis, get_osrm_config
from src.classes.distances import OSRMConfig


# ─────────────────────────────────────────────────────────────
# Helpers / shared data
# ─────────────────────────────────────────────────────────────

INSTANCE_PATH = pathlib.Path("inputs/pa-0/cvrp-0-pa-100.json")


def load_raw_instance(n_deliveries: int = 6) -> dict:
    raw = json.loads(INSTANCE_PATH.read_text())
    raw["deliveries"] = raw["deliveries"][:n_deliveries]
    # ensure idu is set sequentially (mirrors how the core sets it)
    for i, d in enumerate(raw["deliveries"]):
        d["idu"] = i
    return raw


# ─────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────

@pytest.fixture()
def mock_redis():
    """In-memory dict that mimics Redis get/set/setex/ping."""
    store = {}
    r = MagicMock()
    r.ping.return_value = True
    r.get.side_effect = lambda k: store.get(k)
    r.set.side_effect = lambda k, v: store.__setitem__(k, v)
    r.setex.side_effect = lambda k, ttl, v: store.__setitem__(k, v)
    return r


@pytest.fixture()
def mock_osrm_config():
    return OSRMConfig(host="http://mock-osrm", timeout_s=5)


@pytest.fixture()
def small_distance_matrix():
    """7×7 matrix (origin + 6 deliveries) with deterministic distances."""
    n = 7
    rng = np.random.default_rng(42)
    m = rng.integers(1000, 20_000, size=(n, n)).astype(float)
    np.fill_diagonal(m, 0)
    return m


@pytest.fixture()
def client(mock_redis, mock_osrm_config, small_distance_matrix, monkeypatch):
    """TestClient with Redis and OSRM fully mocked."""
    from src.api import dependencies
    from src.services import distance_service as ds_mod

    # Patch Redis dependency
    app.dependency_overrides[get_redis] = lambda: mock_redis
    app.dependency_overrides[get_osrm_config] = lambda: mock_osrm_config

    # Patch calculate_distance_matrix_m / calculate_route_geometry so no real HTTP calls are made
    monkeypatch.setattr(ds_mod, "calculate_distance_matrix_m", lambda *a, **kw: small_distance_matrix)
    monkeypatch.setattr(
        ds_mod,
        "calculate_route_geometry",
        lambda points, config=None: [[p.lng, p.lat] for p in points],
    )

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture()
def optimize_payload():
    return {"instance": load_raw_instance(), "iterations": 1, "city": "pa-0"}


@pytest.fixture()
def stored_solution_id(client, optimize_payload):
    """
    Run the optimize endpoint once and return the solution_id so other tests
    can use the cached result without re-running the optimiser.
    """
    resp = client.post("/api/v1/routes/optimize", json=optimize_payload)
    assert resp.status_code == 200
    return resp.json()["solution_id"]

