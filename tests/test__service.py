"""Tests for the service module."""

from fastapi.testclient import TestClient

from asset_service.service import app

client = TestClient(app)


def test__load__missing_payload():
    """Test the load command missing the payload."""
    response = client.post("/v1/load")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {"type": "missing", "loc": ["body"], "msg": "Field required", "input": None}
        ]
    }


def test__load__missing_file(tmp_path):
    """Test the load command missing the file."""
    bad_file = tmp_path / "bad_file.txt"
    response = client.post("/v1/load", json={"filename": str(bad_file)})
    assert response.status_code == 404
    assert response.json() == {
        "detail": f"File not found: {bad_file}",
    }


def test__load__valid_file(valid_json_file):
    """Test the load command valid file."""
    response = client.post("/v1/load", json={"filename": str(valid_json_file)})
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": f"Loaded assets from: {valid_json_file}",
    }


def test__load__partial_file(partial_json_file):
    """Test the load command partial file."""
    response = client.post("/v1/load", json={"filename": str(partial_json_file)})
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": f"Loaded assets from: {partial_json_file}",
    }


def test__load__bad_file(bad_json_file):
    """Test the load command bad file."""
    response = client.post("/v1/load", json={"filename": str(bad_json_file)})
    assert response.status_code == 422
    assert response.json() == {
        "detail": f"File failed validation: {bad_json_file}",
    }


def test__add_asset__valid():
    """Test the add asset command with valid payload."""
    response = client.post(
        "/v1/add_asset", json={"name": "banana", "asset_type": "prop"}
    )
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Added asset: name='banana' asset_type='prop'",
    }


def test__add_asset__invalid():
    """Test the add asset command with invalid payload."""
    response = client.post(
        "/v1/add_asset", json={"name": "banana", "asset_type": "bad"}
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": "Asset failed validation: name='banana' asset_type='bad'",
    }
