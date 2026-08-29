"""Global pytest fixtures for FertiPartner test suite."""

import pytest


@pytest.fixture
def sample_fertilizer_payload():
    """Fixture providing a standard raw fertilizer sample."""
    return {
        "name": "Urea",
        "category": "Nitrogenados",
        "nitrogen_percentage": 46.0,
        "phosphorus_percentage": 0.0,
        "potassium_percentage": 0.0,
    }
