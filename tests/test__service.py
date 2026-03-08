"""Tests for the service module."""

from fastapi.testclient import TestClient

from asset_service.service import app

client = TestClient(app)


# load


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


def test__load__valid_file(valid_json_file, tmp_db):
    """Test the load command valid file."""
    response = client.post("/v1/load", json={"filename": str(valid_json_file), "registry": str(tmp_db)})
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": f"Loaded assets from: {valid_json_file}",
    }


def test__load__partial_file(partial_json_file, tmp_db):
    """Test the load command partial file."""
    response = client.post("/v1/load", json={"filename": str(partial_json_file), "registry": str(tmp_db)})
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": f"Loaded assets from: {partial_json_file}",
    }


def test__load__bad_file(bad_json_file, tmp_db):
    """Test the load command bad file."""
    response = client.post("/v1/load", json={"filename": str(bad_json_file), "registry": str(tmp_db)})
    assert response.status_code == 422
    assert response.json() == {
        "detail": f"File failed validation: {bad_json_file}",
    }


# add asset


def test__add_asset__valid(tmp_db):
    """Test the add asset command with valid payload."""
    response = client.post("/v1/add", json={"name": "banana", "asset_type": "prop", "registry": str(tmp_db)})
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": f"Added asset: registry='{tmp_db}' name='banana' asset_type='prop'",
    }


def test__add_asset__invalid(tmp_db):
    """Test the add asset command with invalid payload."""
    response = client.post("/v1/add", json={"name": "banana", "asset_type": "bad", "registry": str(tmp_db)})
    assert response.status_code == 422
    assert response.json() == {
        "detail": f"Asset failed validation: registry='{tmp_db}' name='banana' asset_type='bad'",
    }


# add version


def test__add_version__valid(tmp_db):
    """Test the add version command with valid payload."""
    response = client.post(
        "/v1/versions/add",
        json={
            "name": "banana",
            "asset_type": "prop",
            "department": "department",
            "version": 1,
            "status": "active",
            "registry": str(tmp_db),
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": f"Added version: registry='{tmp_db}' name='banana' asset_type='prop' department='department' version=1 status='active'",
    }


def test__add_version__bad_asset(tmp_db):
    """Test the add version command with a bad asset."""
    response = client.post(
        "/v1/versions/add",
        json={
            "name": "banana",
            "asset_type": "bad type",
            "department": "department",
            "version": 1,
            "status": "active",
            "registry": str(tmp_db),
        },
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": f"Asset failed validation: registry='{tmp_db}' name='banana' asset_type='bad type' department='department' version=1 status='active'"
    }


def test__add_version__bad_version(tmp_db):
    """Test the add version command with a bad version."""
    response = client.post(
        "/v1/versions/add",
        json={
            "name": "banana",
            "asset_type": "prop",
            "department": "department",
            "version": 1,
            "status": "bad",
            "registry": str(tmp_db),
        },
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": f"Version failed validation: registry='{tmp_db}' name='banana' asset_type='prop' department='department' version=1 status='bad'"
    }
