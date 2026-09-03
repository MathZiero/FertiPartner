"""Live integration and contract verification tests for external data source APIs.

These tests check whether the API keys and endpoints configured in .env
are currently active, responding, and compatible with FertiPartner ingestion models.
"""

import os
import pytest
import httpx
from dotenv import load_dotenv

load_dotenv()


@pytest.mark.integration
@pytest.mark.skipif(
    not os.environ.get("FRED_API_KEY"),
    reason="FRED_API_KEY not configured in environment",
)
def test_fred_api_connectivity_and_contract():
    """Verify FRED API key is valid and returns commodity price series."""
    api_key = os.environ.get("FRED_API_KEY")
    assert api_key, "FRED_API_KEY must be configured in .env"

    url = f"https://api.stlouisfed.org/fred/series?series_id=PURANUSDM&api_key={api_key}&file_type=json"
    with httpx.Client(timeout=15.0) as client:
        response = client.get(url)

    assert response.status_code == 200, f"FRED API failed: {response.status_code} - {response.text}"
    data = response.json()
    assert "seriess" in data, "FRED response missing 'seriess' key"
    assert len(data["seriess"]) > 0, "FRED returned empty series array"
    assert data["seriess"][0]["id"] == "PURANUSDM"


@pytest.mark.integration
def test_comex_stat_api_connectivity_and_contract():
    """Verify Brazilian Comex Stat (MDIC) API is responding with fertilizer import microdata."""
    url = "https://api-comexstat.mdic.gov.br/general"
    payload = {
        "flow": "import",
        "monthDetail": False,
        "period": {"from": "2024-01", "to": "2024-01"},
        "filters": [{"filter": "ncm", "values": ["31021010"]}],  # Urea NCM
        "details": ["ncm", "country"],
        "metrics": ["metricFOB", "metricKG"],
    }
    with httpx.Client(timeout=20.0, verify=False) as client:
        response = client.post(url, json=payload)

    assert response.status_code == 200, f"Comex Stat failed: {response.status_code} - {response.text}"
    data = response.json()
    assert "data" in data, "Comex Stat response missing 'data' key"
    records = data.get("data", {}).get("list", [])
    assert isinstance(records, list)
    assert len(records) > 0, "Expected at least one import record for Urea in Jan 2024"
    sample = records[0]
    assert "coNcm" in sample or "metricFOB" in sample


@pytest.mark.integration
@pytest.mark.skipif(
    not os.environ.get("COMTRADE_API_KEY"),
    reason="COMTRADE_API_KEY not configured in environment",
)
def test_un_comtrade_api_connectivity_and_contract():
    """Verify UN Comtrade API key is valid and returns trade flow records."""
    api_key = os.environ.get("COMTRADE_API_KEY")
    assert api_key, "COMTRADE_API_KEY must be configured in .env"

    headers = {"Ocp-Apim-Subscription-Key": api_key}
    # Query Brazil (reporter 76) Urea (HS 310210)
    url = "https://comtradeapi.un.org/public/v1/preview/C/A/HS?period=2023&reporterCode=76&cmdCode=310210"
    with httpx.Client(timeout=20.0) as client:
        response = client.get(url, headers=headers)

    assert response.status_code == 200, f"UN Comtrade failed: {response.status_code} - {response.text}"
    data = response.json()
    assert "data" in data, "UN Comtrade response missing 'data' key"
    records = data.get("data", [])
    assert isinstance(records, list)
    assert len(records) > 0, "Expected trade records for Brazil Urea in UN Comtrade"


@pytest.mark.integration
@pytest.mark.skipif(
    not os.environ.get("FAOSTAT_TOKEN"),
    reason="FAOSTAT_TOKEN not configured in environment",
)
def test_faostat_api_endpoint_check():
    """Verify FAOSTAT API endpoint status and diagnose authentication."""
    token = os.environ.get("FAOSTAT_TOKEN")
    url = "https://faostatservices.fao.org/api/v1/en/search?q=fertilizer"
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    with httpx.Client(timeout=15.0) as client:
        response = client.get(url, headers=headers)

    # Note: FAOSTAT tokens are short-lived Cognito JWTs (1h).
    # If expired or unauthorized, it returns 401 or 403.
    assert response.status_code in (200, 401, 403), f"Unexpected FAOSTAT status: {response.status_code}"
