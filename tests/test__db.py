"""Test the db module."""

from asset_service import db


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


def test__get_asset(tmp_db):
    """Test the get_asset function."""
    registry = db.AssetRegistry(tmp_db)
    assert registry.get_asset("test", db.AssetType.FX) is None
    registry.register_asset("test", db.AssetType.FX)
    assert registry.get_asset("test", db.AssetType.FX) == db.Asset(
        "test", db.AssetType.FX
    )
