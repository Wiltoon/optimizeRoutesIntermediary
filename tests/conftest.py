import pytest


@pytest.fixture
def sample_instance():
    """Load a real CVRPInstance from inputs/ for testing."""
    from src.classes.types import CVRPInstance
    return CVRPInstance.from_file("inputs/pa-0/cvrp-0-pa-0.json")
