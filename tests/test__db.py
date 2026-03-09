"""Test the db module."""

import pytest

from asset_service import api, db


def test__asset_registry_init(memory_db):
    """Test the tables are created when initializing an AssetRegistry."""
    db.AssetRegistry(connection=memory_db)

    cursor = memory_db.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name IN ('assets', 'asset_versions')"
    )
    rows = cursor.fetchall()
    assert rows == [(2,)]


def test__asset_registry_init__idempotent(memory_db):
    """Test the tables are created only once without issues."""
    registry = db.AssetRegistry(connection=memory_db)
    registry._init_db()

    cursor = memory_db.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name IN ('assets', 'asset_versions')"
    )
    rows = cursor.fetchall()
    assert rows == [(2,)]


def test__register_asset(memory_db):
    """Test an asset is saved into the database."""
    registry = db.AssetRegistry(connection=memory_db)
    asset = registry.register_asset("test", db.AssetType.FX)
    cursor = memory_db.cursor()
    cursor.execute("SELECT name, asset_type FROM assets")
    rows = cursor.fetchall()
    assert rows == [("test", db.AssetType.FX)]
    assert asset.name == "test"
    assert asset.asset_type == db.AssetType.FX


def test__register_asset__idempotent(memory_db):
    """Test an asset is saved into the database only once without issues."""
    registry = db.AssetRegistry(connection=memory_db)
    registry.register_asset("test", db.AssetType.FX)
    asset = registry.register_asset("test", db.AssetType.FX)
    cursor = memory_db.cursor()
    cursor.execute("SELECT name, asset_type FROM assets")
    rows = cursor.fetchall()
    assert rows == [("test", db.AssetType.FX)]
    assert asset.name == "test"
    assert asset.asset_type == db.AssetType.FX


def test__register_asset_version(memory_db):
    """Test an asset version is saved into the database."""
    registry = db.AssetRegistry(connection=memory_db)
    state = registry.register_version(db.Asset("name", db.AssetType.FX), "texturing", 1)
    cursor = memory_db.cursor()
    cursor.execute(
        "SELECT name, asset_type, department, version, status FROM asset_versions"
    )
    rows = cursor.fetchall()
    assert rows == [("name", "fx", "texturing", 1, "active")]
    assert state.status == db.AssetVersionStatus.ACTIVE


def test__register_asset_version__idempotent(memory_db):
    """Test an asset version is saved into the database only once without issues."""
    registry = db.AssetRegistry(connection=memory_db)
    registry.register_version(db.Asset("name", db.AssetType.FX), "texturing", 1)
    state = registry.register_version(db.Asset("name", db.AssetType.FX), "texturing", 1)
    cursor = memory_db.cursor()
    cursor.execute(
        "SELECT name, asset_type, department, version, status FROM asset_versions"
    )
    rows = cursor.fetchall()
    assert rows == [("name", "fx", "texturing", 1, "active")]
    assert state.status == db.AssetVersionStatus.ACTIVE


def test__get_asset__not_found(tmp_db):
    """Test the get_asset function on an empty database (not found)."""
    registry = db.AssetRegistry(tmp_db)
    assert registry.get_asset("test", db.AssetType.FX) is None


def test__get_asset__found(tmp_db):
    """Test the get_asset function after adding the asset."""
    registry = db.AssetRegistry(tmp_db)
    registry.register_asset("test", db.AssetType.FX)
    assert registry.get_asset("test", db.AssetType.FX) == db.Asset(
        "test", db.AssetType.FX
    )


def test__get_assets__empty(tmp_db):
    """Test the get_assets function on an empty database."""
    registry = db.AssetRegistry(tmp_db)
    assert list(registry.get_assets()) == []


@pytest.mark.parametrize(
    "name, asset_type, expected",
    [
        (
            None,
            None,
            [
                db.Asset("hero", db.AssetType.CHARACTER),
                db.Asset("hero", db.AssetType.FX),
                db.Asset("spoon", db.AssetType.PROP),
            ],
        ),
        (
            "hero",
            None,
            [
                db.Asset("hero", db.AssetType.CHARACTER),
                db.Asset("hero", db.AssetType.FX),
            ],
        ),
        (None, db.AssetType.PROP, [db.Asset("spoon", db.AssetType.PROP)]),
        ("hero", db.AssetType.FX, [db.Asset("hero", db.AssetType.FX)]),
        ("spoon", db.AssetType.FX, []),
    ],
)
def test__get_assets__no_filter(name, asset_type, expected, tmp_db, valid_json_file):
    """Test the get_assets function with data."""
    registry = db.AssetRegistry(tmp_db)
    api.load_from_json(valid_json_file, registry=registry)
    assert list(registry.get_assets(name=name, asset_type=asset_type)) == expected


def test__get_version__not_found(tmp_db):
    """Test the get_version function on an empty database."""
    registry = db.AssetRegistry(tmp_db)
    assert (
        registry.get_version(db.Asset("hero", db.AssetType.FX), "texturing", 1) is None
    )


def test__get_version__found(tmp_db, valid_json_file):
    """Test the get_version function after adding the asset."""
    registry = db.AssetRegistry(tmp_db)
    api.load_from_json(valid_json_file, registry=registry)
    result = registry.get_version(db.Asset("hero", db.AssetType.FX), "texturing", 1)
    assert isinstance(result, db.AssetVersion)
    assert result.key.asset == db.Asset("hero", db.AssetType.FX)
    assert result.key.department == "texturing"
    assert result.key.version == 1


def test__get_versions__not_found(tmp_db):
    """Test the get_version function on an empty database."""
    registry = db.AssetRegistry(tmp_db)
    assert list(registry.get_versions(db.Asset("hero", db.AssetType.CHARACTER))) == []


def test__get_versions__found(tmp_db, valid_json_file):
    """Test the get_version function after adding data."""
    registry = db.AssetRegistry(tmp_db)
    api.load_from_json(valid_json_file, registry=registry)
    result = list(registry.get_versions(db.Asset("hero", db.AssetType.CHARACTER)))
    assert result == [
        db.AssetVersion(
            db.AssetVersionKey(db.Asset("hero", db.AssetType.CHARACTER), "modeling", 1),
            db.AssetVersionState(db.AssetVersionStatus.INACTIVE),
        ),
        db.AssetVersion(
            db.AssetVersionKey(db.Asset("hero", db.AssetType.CHARACTER), "modeling", 2),
            db.AssetVersionState(db.AssetVersionStatus.ACTIVE),
        ),
        db.AssetVersion(
            db.AssetVersionKey(
                db.Asset("hero", db.AssetType.CHARACTER), "texturing", 1
            ),
            db.AssetVersionState(db.AssetVersionStatus.ACTIVE),
        ),
    ]


def test__get_versions__found__department(tmp_db, valid_json_file):
    """Test the get_version with a department after adding data."""
    registry = db.AssetRegistry(tmp_db)
    api.load_from_json(valid_json_file, registry=registry)
    result = list(
        registry.get_versions(
            db.Asset("hero", db.AssetType.CHARACTER), department="texturing"
        )
    )
    assert result == [
        db.AssetVersion(
            db.AssetVersionKey(
                db.Asset("hero", db.AssetType.CHARACTER), "texturing", 1
            ),
            db.AssetVersionState(db.AssetVersionStatus.ACTIVE),
        ),
    ]


def test__get_versions__found__version(tmp_db, valid_json_file):
    """Test the get_version with a version after adding data."""
    registry = db.AssetRegistry(tmp_db)
    api.load_from_json(valid_json_file, registry=registry)
    result = list(
        registry.get_versions(db.Asset("hero", db.AssetType.CHARACTER), version=1)
    )
    assert result == [
        db.AssetVersion(
            db.AssetVersionKey(db.Asset("hero", db.AssetType.CHARACTER), "modeling", 1),
            db.AssetVersionState(db.AssetVersionStatus.INACTIVE),
        ),
        db.AssetVersion(
            db.AssetVersionKey(
                db.Asset("hero", db.AssetType.CHARACTER), "texturing", 1
            ),
            db.AssetVersionState(db.AssetVersionStatus.ACTIVE),
        ),
    ]


def test__get_versions__found__status(tmp_db, valid_json_file):
    """Test the get_versions with a status after adding data."""
    registry = db.AssetRegistry(tmp_db)
    api.load_from_json(valid_json_file, registry=registry)
    result = list(
        registry.get_versions(
            db.Asset("hero", db.AssetType.CHARACTER),
            status=db.AssetVersionStatus.ACTIVE,
        )
    )
    assert result == [
        db.AssetVersion(
            db.AssetVersionKey(db.Asset("hero", db.AssetType.CHARACTER), "modeling", 2),
            db.AssetVersionState(db.AssetVersionStatus.ACTIVE),
        ),
        db.AssetVersion(
            db.AssetVersionKey(
                db.Asset("hero", db.AssetType.CHARACTER), "texturing", 1
            ),
            db.AssetVersionState(db.AssetVersionStatus.ACTIVE),
        ),
    ]
