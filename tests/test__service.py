"""
Tests for the service module.
"""

import pytest
from fastapi.testclient import TestClient

from asset_service import api, db
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
    response = client.post(
        "/v1/load", json={"filename": str(valid_json_file), "registry": str(tmp_db)}
    )
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": f"Loaded assets from: {valid_json_file}",
    }


def test__load__partial_file(partial_json_file, tmp_db):
    """Test the load command partial file."""
    response = client.post(
        "/v1/load", json={"filename": str(partial_json_file), "registry": str(tmp_db)}
    )
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": f"Loaded assets from: {partial_json_file}",
    }


def test__load__bad_file(bad_json_file, tmp_db):
    """Test the load command bad file."""
    response = client.post(
        "/v1/load", json={"filename": str(bad_json_file), "registry": str(tmp_db)}
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": f"File failed validation: {bad_json_file}",
    }


# add asset


def test__add_asset__valid(tmp_db):
    """Test the add asset command with valid payload."""
    response = client.post(
        "/v1/add",
        json={"name": "banana", "asset_type": "prop", "registry": str(tmp_db)},
    )
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": f"Added asset: registry='{tmp_db}' name='banana' asset_type='prop'",
    }


def test__add_asset__invalid(tmp_db):
    """Test the add asset command with invalid payload."""
    response = client.post(
        "/v1/add", json={"name": "banana", "asset_type": "bad", "registry": str(tmp_db)}
    )
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


# get asset


def test__get_asset__not_found(tmp_db):
    """Test get_asset with an empty database (not found)."""
    response = client.get(f"/v1/get/banana/prop?registry={tmp_db}")
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Asset not found: banana/prop",
    }


def test__get_asset__valid(tmp_db):
    """Test get_asset after adding the item."""
    db.AssetRegistry(tmp_db).register_asset("banana", db.AssetType.PROP)
    response = client.get(f"/v1/get/banana/prop?registry={tmp_db}")
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "asset": {"name": "banana", "asset_type": "prop"},
    }


# list


@pytest.mark.parametrize(
    "name, asset_type, expected",
    [
        (None, None, [("hero", "character"), ("hero", "fx"), ("spoon", "prop")]),
        ("hero", None, [("hero", "character"), ("hero", "fx")]),
        (None, "fx", [("hero", "fx")]),
        ("spoon", "prop", [("spoon", "prop")]),
    ],
)
def test__list__found(name, asset_type, expected, tmp_db, valid_json_file):
    """Test list when finding something."""
    api.load_from_json(valid_json_file, registry=db.AssetRegistry(tmp_db))
    url = f"/v1/list?registry={tmp_db}"
    if name:
        url = f"{url}&name={name}"
    if asset_type:
        url = f"{url}&asset_type={asset_type}"
    response = client.get(url)
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "assets": [{"name": it[0], "asset_type": it[1]} for it in expected],
    }


def test__list__not_found(tmp_db):
    """Test list when not finding something."""
    response = client.get(f"/v1/list?registry={tmp_db}")
    assert response.status_code == 404
    assert response.json() == {
        "detail": "No Assets found: name='' asset_type=''",
    }


# get version


def test__versions__get__not_found(tmp_db):
    """Test get_versions when not finding something."""
    response = client.get(f"/v1/versions/get/hero/fx/texturing/1?registry={tmp_db}")
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Version not found: hero/fx - texturing:1",
    }


def test__versions__get__valid(tmp_db, valid_json_file):
    """Test get_versions when finding something."""
    api.load_from_json(valid_json_file, registry=db.AssetRegistry(tmp_db))
    response = client.get(f"/v1/versions/get/hero/fx/texturing/1?registry={tmp_db}")
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "version": {
            "name": "hero",
            "asset_type": "fx",
            "department": "texturing",
            "version": 1,
            "status": "active",
        },
    }


# list versions


def test__versions__list__not_found(tmp_db):
    """Test versions list with empty database."""
    response = client.get(f"/v1/versions/list/hero/character?registry={tmp_db}")
    assert response.status_code == 404
    assert response.json() == {
        "detail": "No Versions found: hero/character filters: None None None"
    }


def test__versions__list__valid(tmp_db, valid_json_file):
    """Test versions list with valid database."""
    api.load_from_json(valid_json_file, registry=db.AssetRegistry(tmp_db))
    response = client.get(
        f"/v1/versions/list/hero/character?department=texturing&registry={tmp_db}"
    )
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "versions": [
            {
                "asset": {"name": "hero", "asset_type": "character"},
                "department": "texturing",
                "version": 1,
                "status": "active",
            },
        ],
    }


# latest version


def test__versions__latest__not_found(tmp_db):
    """Test versions list with empty database."""
    response = client.get(f"/v1/versions/latest/hero/fx/texturing?registry={tmp_db}")
    assert response.status_code == 404
    assert response.json() == {
        "detail": "No versions found: hero/fx - texturing active_only=True",
    }


@pytest.mark.parametrize("active, expected", [("true", 2), ("false", 3)])
def test__versions__latest__valid(active, expected, tmp_db, valid_json_file):
    """Test versions list with valid database."""
    registry = db.AssetRegistry(tmp_db)
    asset = db.Asset("hero", db.AssetType.FX)
    api.add_asset_version(asset, "texturing", 1, "active", registry=registry)
    api.add_asset_version(asset, "texturing", 2, "active", registry=registry)
    api.add_asset_version(asset, "texturing", 3, "inactive", registry=registry)
    response = client.get(
        f"v1/versions/latest/hero/fx/texturing?active_only={active}&registry={tmp_db}"
    )
    assert response.status_code == 200
    assert response.json() == {"status": "success", "version": expected}
