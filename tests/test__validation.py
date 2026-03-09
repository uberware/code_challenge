"""Unit tests for the db module."""

import pytest

from asset_service import db, validation


def test__validate_version_list__valid__one_department():
    """Test validate_version_list works as expected with valid version list from a single department."""
    asset = db.Asset("asset_name", db.AssetType.FX)
    versions = [db.make_asset_version(asset, "dept", it) for it in range(1, 6)]
    assert validation.validate_version_list(versions) == {}


def test__validate_version_list__valid__multiple_departments():
    """Test validate_version_list works as expected with valid version list."""
    asset = db.Asset("asset_name", db.AssetType.FX)
    versions = [db.make_asset_version(asset, str(it)) for it in range(1, 6)]
    assert validation.validate_version_list(versions) == {}


def test__validate_version_list__fails_with_version_0():
    """Test validate_version_list works as expected with version 0."""
    asset = db.Asset("asset_name", db.AssetType.FX)
    with pytest.raises(ValueError):
        db.make_asset_version(asset, "dept", 0)


def test__validate_version_list__does_not_start_at_1():
    """Test validate_version_list works as expected with versions that start above 1."""
    asset = db.Asset("asset_name", db.AssetType.FX)
    versions = [db.make_asset_version(asset, "dept", it) for it in range(2, 6)]
    assert validation.validate_version_list(versions) == {
        "dept": ["Versions do not start at 1: 2"]
    }


def test__validate_version_list__gaps():
    """Test validate_version_list works as expected with versions that have gaps."""
    asset = db.Asset("asset_name", db.AssetType.FX)
    versions = [db.make_asset_version(asset, "dept", it) for it in range(1, 6)]
    del versions[2]
    assert validation.validate_version_list(versions) == {
        "dept": ["Has version gaps: [1, 2, 4, 5]"]
    }


def test__validate_version_list__duplicate():
    """Test validate_version_list works as expected with versions that have duplicates."""
    asset = db.Asset("asset_name", db.AssetType.FX)
    versions = [db.make_asset_version(asset, "dept", it) for it in range(1, 6)]
    versions.append(db.make_asset_version(asset, "dept", 2))
    assert validation.validate_version_list(versions) == {
        "dept": ["Has duplicate versions: [1, 2, 3, 4, 5, 2]"]
    }


def test__validate_asset_version__valid_with_extra_fields(valid_data, caplog):
    """Test find_good_versions works as expected with valid versions with extra fields."""
    raw_data = valid_data[0]
    raw_data["extra"] = None
    asset = db.Asset("hero", db.AssetType.CHARACTER)
    assert validation.validate_asset_version(raw_data) == (
        asset,
        db.make_asset_version(asset, "modeling", 1, False),
    )
    assert "Ignoring unknown key: extra" in caplog.text


def test__validate_asset_version__not_a_dict(caplog):
    """Test validate_asset_version works as expected with invalid asset data."""
    assert validation.validate_asset_version([]) == (None, None)
    assert "Item is not a dictionary" in caplog.text


def test__validate_asset_version__missing_asset(caplog):
    """Test find_good_versions works as expected with missing asset."""
    bad_data = {
        "department": "modeling",
        "version": 1,
        "status": "active",
    }
    assert validation.validate_asset_version(bad_data) == (None, None)
    assert "Item missing asset information" in caplog.text


@pytest.mark.parametrize("missing", ["name", "type"])
def test__validate_asset_version__missing__asset_value(missing, valid_data, caplog):
    """Test find_good_versions works as expected with missing asset values."""
    raw_data = valid_data[0]
    del raw_data["asset"][missing]
    assert validation.validate_asset_version(raw_data) == (None, None)
    assert f"Unable to determine asset {missing}" in caplog.text


@pytest.mark.parametrize("missing", ["department", "version", "status"])
def test__validate_asset_version__missing__value(missing, valid_data, caplog):
    """Test find_good_versions works as expected with missing values."""
    raw_data = valid_data[0]
    del raw_data[missing]
    assert validation.validate_asset_version(raw_data) == (None, None)
    assert f"Unable to determine {missing}" in caplog.text


def test__validate_asset_version__validation_error__asset(valid_data, caplog):
    """Test find_good_versions works as expected with invalid asset name."""
    raw_data = valid_data[0]
    raw_data["asset"]["name"] = None
    assert validation.validate_asset_version(raw_data) == (None, None)
    assert "Invalid item:" in caplog.text
    assert "1 validation error for Asset" in caplog.text
    assert "input_value=None" in caplog.text


@pytest.mark.parametrize("missing", ["department", "version"])
def test__validate_asset_version__validation_error__asset_version_key(
    missing, valid_data, caplog
):
    """Test find_good_versions works as expected with invalid asset version key data."""
    raw_data = valid_data[0]
    raw_data[missing] = None
    assert validation.validate_asset_version(raw_data) == (None, None)
    assert "Invalid item:" in caplog.text
    assert "1 validation error for AssetVersionKey" in caplog.text
    assert "input_value=None" in caplog.text


def test__find_good_versions__valid(valid_data, caplog):
    """Test find_good_versions works as expected with valid versions."""
    expected_character = db.Asset("hero", db.AssetType.CHARACTER)
    expected_fx = db.Asset("hero", db.AssetType.FX)
    expected_prop = db.Asset("spoon", db.AssetType.PROP)
    assert validation.find_good_versions(valid_data) == {
        expected_character: [
            db.make_asset_version(expected_character, "modeling", 1, False),
            db.make_asset_version(expected_character, "modeling", 2),
            db.make_asset_version(expected_character, "texturing", 1),
        ],
        expected_fx: [
            db.make_asset_version(expected_fx, "texturing", 1),
        ],
        expected_prop: [
            db.make_asset_version(expected_prop, "modeling", 1),
        ],
    }
    assert caplog.text == ""


def test__find_good_versions__validate_issue(valid_data, caplog):
    """Test find_good_versions works as expected when _validate_asset_version fails."""
    valid_data[3]["asset"]["name"] = None
    expected_character = db.Asset("hero", db.AssetType.CHARACTER)
    expected_prop = db.Asset("spoon", db.AssetType.PROP)
    assert validation.find_good_versions(valid_data) == {
        expected_character: [
            db.make_asset_version(expected_character, "modeling", 1, False),
            db.make_asset_version(expected_character, "modeling", 2),
            db.make_asset_version(expected_character, "texturing", 1),
        ],
        expected_prop: [
            db.make_asset_version(expected_prop, "modeling", 1),
        ],
    }
    assert "1 validation error for Asset" in caplog.text


def test__find_good_versions__version_issue(valid_data, caplog):
    """Test find_good_versions works as expected when _validate_version_list fails."""
    valid_data[1]["version"] = 3
    del valid_data[2]
    expected_fx = db.Asset("hero", db.AssetType.FX)
    expected_prop = db.Asset("spoon", db.AssetType.PROP)
    assert validation.find_good_versions(valid_data) == {
        expected_fx: [db.make_asset_version(expected_fx, "texturing", 1)],
        expected_prop: [db.make_asset_version(expected_prop, "modeling", 1)],
    }
    assert (
        "Asset(name='hero', asset_type=<AssetType.CHARACTER: 'character'>)"
        in caplog.text
    )
    assert "No good versions supplied for: " in caplog.text
    assert "Has version gaps: [1, 3]" in caplog.text
