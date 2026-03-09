"""Tests for api module."""

from pathlib import Path
from unittest.mock import MagicMock, call

import pytest

from asset_service import api, db


@pytest.fixture
def mock_asset_registry(mocker):
    """A fixture that mocks the AssetRegistry class."""
    mock_registry = MagicMock()
    mocker.patch("asset_service.api.db.AssetRegistry", return_value=mock_registry)
    return mock_registry


# load


def test__load_from_json__invalid_filename_type(caplog):
    """Test load_from_json with invalid filename type."""
    assert api.load_from_json(1) is False
    assert "filename must be a string or Path. Got: <class 'int'>" in caplog.text


def test__load_from_json__file_does_not_exist(tmp_path, caplog):
    """Test load_from_json with a file that does not exist."""
    filename = tmp_path / "test.json"
    assert api.load_from_json(filename) is False
    assert f"file does not exist: {filename}" in caplog.text


def test__load_from_json__wrong_data_type(tmp_path, caplog):
    """Test load_from_json with a wrong data type."""
    filename = tmp_path / "test.json"
    filename.write_text('{"problem": "wrong data type"}')
    assert api.load_from_json(filename) is False
    assert "did not contain a list. Got: <class 'dict'>" in caplog.text


@pytest.mark.parametrize("cast", [str, Path])
def test__load_from_json__string_or_path(valid_json_file, cast, mock_asset_registry):
    """Test load_from_json with a string or path."""
    assert api.load_from_json(cast(valid_json_file)) is True
    mock_asset_registry.register_asset.assert_has_calls(
        [
            call("hero", "character"),
            call("hero", "fx"),
        ]
    )
    mock_asset_registry.register_version.assert_has_calls(
        [
            call(
                db.Asset("hero", db.AssetType.CHARACTER),
                "modeling",
                1,
                db.AssetVersionStatus.INACTIVE,
            ),
            call(
                db.Asset("hero", db.AssetType.CHARACTER),
                "modeling",
                2,
                db.AssetVersionStatus.ACTIVE,
            ),
            call(
                db.Asset("hero", db.AssetType.CHARACTER),
                "texturing",
                1,
                db.AssetVersionStatus.ACTIVE,
            ),
            call(
                db.Asset("hero", db.AssetType.FX),
                "texturing",
                1,
                db.AssetVersionStatus.ACTIVE,
            ),
        ]
    )
    assert mock_asset_registry.register_asset.call_count == 3
    assert mock_asset_registry.register_version.call_count == 5


def test__load_from_json__empty_file(tmp_path, tmp_db):
    """Test load_from_json with an empty list file."""
    filename = tmp_path / "empty.json"
    filename.write_text("[]")
    registry = db.AssetRegistry(tmp_db)
    assert api.load_from_json(filename, registry=registry) is False


# add_asset


@pytest.mark.parametrize("input_type", ["fx", db.AssetType.FX])
def test__add_asset__valid(input_type, mock_asset_registry):
    """Test add_asset with valid data."""
    assert api.add_asset("name", input_type) is not None
    mock_asset_registry.register_asset.assert_has_calls([call("name", db.AssetType.FX)])


def test__add_asset__invalid(mock_asset_registry):
    """Test add_asset with invalid data."""
    assert api.add_asset("name", "bad type") is None
    mock_asset_registry.register_asset.assert_not_called()


# add_version


@pytest.mark.parametrize("status_type", ["active", db.AssetVersionStatus.ACTIVE, None])
def test__add_version__valid(status_type, mock_asset_registry):
    """Test add_version with valid data."""
    asset = db.Asset("hero", db.AssetType.CHARACTER)
    assert api.add_asset_version(asset, "department", 1, status_type) is not None
    mock_asset_registry.register_version.assert_has_calls(
        [
            call(asset, "department", 1, db.AssetVersionStatus.ACTIVE),
        ]
    )


def test__add_version__invalid(mock_asset_registry):
    """Test add_version with invalid data."""
    asset = db.Asset("hero", db.AssetType.CHARACTER)
    assert api.add_asset_version(asset, "department", 1, "bad") is None
    mock_asset_registry.register_version.assert_not_called()


# get_asset


@pytest.mark.parametrize("asset_type", ["character", db.AssetType.CHARACTER])
def test__get_asset__valid(asset_type, mock_asset_registry, caplog):
    """Test get_asset with valid data."""
    assert api.get_asset("hero", asset_type) is not None
    assert "Invalid Asset type: " not in caplog.text
    mock_asset_registry.get_asset.assert_has_calls(
        [call("hero", db.AssetType.CHARACTER)]
    )


def test__get_asset__bad_type(mock_asset_registry, caplog):
    """Test get_asset with invalid data."""
    assert api.get_asset("hero", "bad type") is None
    assert "Invalid Asset type: hero/bad type" in caplog.text


# get_assets


def test__get_asset__not_found(tmp_db, caplog):
    """Test get_asset with empty database."""
    assert list(api.list_assets(registry=db.AssetRegistry(tmp_db))) == []
    assert "Invalid Asset type: " not in caplog.text


@pytest.mark.parametrize("asset_type", ["character", db.AssetType.CHARACTER])
def test__get_assets__valid(asset_type, valid_json_file, tmp_db, caplog):
    """Test get_assets with valid data."""
    registry = db.AssetRegistry(tmp_db)
    api.load_from_json(valid_json_file, registry=registry)
    assert list(api.list_assets(asset_type=asset_type, registry=registry)) == [
        db.Asset("hero", db.AssetType.CHARACTER)
    ]
    assert "Invalid Asset type: " not in caplog.text


def test__get_assets__bad_type(mock_asset_registry, caplog):
    """Test get_assets with invalid data."""
    registry = db.AssetRegistry(mock_asset_registry)
    assert list(api.list_assets(asset_type="bad type", registry=registry)) == []
    assert "Invalid Asset type: bad type" in caplog.text
    mock_asset_registry.get_asset.assert_not_called()


# get_version


def test__get_version__not_found(tmp_db, caplog):
    """Test get_version with empty database (not found)."""
    registry = db.AssetRegistry(tmp_db)
    result = api.get_asset_version("hero", "fx", "texturing", 1, registry=registry)
    assert result is None
    assert "Invalid Asset type: " not in caplog.text


@pytest.mark.parametrize("asset_type", ["fx", db.AssetType.FX])
def test__get_version__valid(asset_type, valid_json_file, tmp_db, caplog):
    """Test get_assets with valid data."""
    registry = db.AssetRegistry(tmp_db)
    api.load_from_json(valid_json_file, registry=registry)
    result = api.get_asset_version(
        "hero", asset_type, "texturing", 1, registry=registry
    )
    assert result is not None
    assert result.key.asset == db.Asset("hero", db.AssetType.FX)
    assert result.key.department == "texturing"
    assert result.key.version == 1
    assert "Invalid Asset type: " not in caplog.text


def test__get_version__bad_type(mock_asset_registry, caplog):
    """Test get_version with invalid data."""
    registry = db.AssetRegistry(mock_asset_registry)
    result = api.get_asset_version(
        "hero", "bad type", "texturing", 1, registry=registry
    )
    assert result is None
    assert "Invalid Asset type: bad type" in caplog.text


# list_asset_versions


def test__list_asset_versions__not_found(tmp_db, caplog):
    """Test list_asset_versions with empty database."""
    registry = db.AssetRegistry(tmp_db)
    result = list(api.list_asset_versions("hero", "character", registry=registry))
    assert result == []
    assert "Invalid Asset Version input: " not in caplog.text


@pytest.mark.parametrize("asset_type", ["character", db.AssetType.CHARACTER])
def test__list_asset_versions__valid(asset_type, tmp_db, valid_json_file, caplog):
    """Test list_asset_versions with valid data."""
    registry = db.AssetRegistry(tmp_db)
    api.load_from_json(valid_json_file, registry=registry)
    result = list(
        api.list_asset_versions(
            "hero", asset_type, department="texturing", registry=registry
        )
    )
    assert result == [
        db.AssetVersion(
            db.AssetVersionKey(
                db.Asset("hero", db.AssetType.CHARACTER), "texturing", 1
            ),
            db.AssetVersionState(db.AssetVersionStatus.ACTIVE),
        )
    ]
    assert "Invalid Asset Version input: " not in caplog.text


@pytest.mark.parametrize("status", ["inactive", db.AssetVersionStatus.INACTIVE])
def test__list_asset_versions__status(status, tmp_db, valid_json_file, caplog):
    """Test list_asset_versions with different status types."""
    registry = db.AssetRegistry(tmp_db)
    api.load_from_json(valid_json_file, registry=registry)
    result = list(
        api.list_asset_versions("hero", "character", status=status, registry=registry)
    )
    assert result == [
        db.AssetVersion(
            db.AssetVersionKey(db.Asset("hero", db.AssetType.CHARACTER), "modeling", 1),
            db.AssetVersionState(db.AssetVersionStatus.INACTIVE),
        )
    ]
    assert "Invalid Asset Version input: " not in caplog.text


def test__list_asset_versions__bad_status(mock_asset_registry, caplog):
    """Test list_asset_versions with invalid status."""
    registry = db.AssetRegistry(mock_asset_registry)
    result = list(
        api.list_asset_versions("hero", "character", status="bad", registry=registry)
    )
    assert result == []
    assert "Invalid Asset Version input: asset_type=character status=bad" in caplog.text
