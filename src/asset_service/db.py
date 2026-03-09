"""
Asset data types and storage interface.
"""

import sqlite3
from collections.abc import Iterator
from enum import StrEnum, auto
from pathlib import Path

from pydantic import Field
from pydantic.dataclasses import dataclass

from asset_service import logger

DATABASE_PATH = Path.home() / "asset_library.db"
"""Hard-coded database path for simplicity."""


class AssetType(StrEnum):
    """Possible asset types."""

    CHARACTER = auto()
    PROP = auto()
    SET = auto()
    ENVIRONMENT = auto()
    VEHICLE = auto()
    DRESSING = auto()
    FX = auto()


class AssetVersionStatus(StrEnum):
    """Possible asset version states."""

    ACTIVE = auto()
    INACTIVE = auto()


@dataclass(frozen=True)
class Asset:
    """Representation of an asset."""

    name: str
    asset_type: AssetType


@dataclass(frozen=True)
class AssetVersionKey:
    """Representation of an asset version (without mutable state data)."""

    asset: Asset
    department: str
    version: int = Field(gt=0)


@dataclass
class AssetVersionState:
    """Mutable asset version state data."""

    status: AssetVersionStatus


@dataclass
class AssetVersion:
    """A combination of one key and one state."""

    key: AssetVersionKey
    state: AssetVersionState


def make_asset_version(
    asset: Asset,
    department: str,
    number: int = 1,
    active: AssetVersionStatus | str | bool = True,
) -> AssetVersion:
    """Helper to make AssetVersion objects"""
    if isinstance(active, bool):
        active = AssetVersionStatus.ACTIVE if active else AssetVersionStatus.INACTIVE
    return AssetVersion(
        AssetVersionKey(asset, department, number),
        AssetVersionState(AssetVersionStatus(active)),
    )


class AssetRegistry:
    def __init__(
        self,
        database_path: Path | str | None = None,
        *,
        connection: sqlite3.Connection | None = None,
    ):
        """Initialize the asset registry.

        Args:
            database_path: Supply a database path. None uses default
        """
        database_path = database_path or DATABASE_PATH
        logger.info(f"Database: {database_path}")
        self.conn = connection or sqlite3.connect(database_path)
        self._init_db()

    def _init_db(self):
        """Initialize the database."""
        logger.debug("Initializing database schema")
        cur = self.conn.cursor()
        # Create the asset table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS assets (
                name TEXT,
                asset_type TEXT,
                PRIMARY KEY (name, asset_type)
            )
            """
        )
        # Create the asset version table
        # TODO: optimize storage by using an asset ID key instead of the name and type
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS asset_versions (
                name TEXT,
                asset_type TEXT,
                department TEXT,
                version INTEGER,
                status TEXT,
                PRIMARY KEY (name, asset_type, department, version)
            )
            """
        )
        self.conn.commit()

    def register_asset(self, name: str, asset_type: AssetType) -> Asset:
        """Register an asset.

        Args:
            name: Asset name.
            asset_type: Asset type.

        Returns:
            Asset object with the name and asset type.
        """
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT OR IGNORE INTO assets (name, asset_type) VALUES (?, ?)
            """,
            (name, asset_type),
        )
        self.conn.commit()
        return Asset(name, asset_type)

    def register_version(
        self,
        asset: Asset,
        department: str,
        version: int,
        status: AssetVersionStatus = AssetVersionStatus.ACTIVE,
    ) -> AssetVersionState:
        """Register an asset version.

        Args:
            asset: Asset object this version belongs to
            department: Department name
            version: Version number
            status: Version status

        Returns:
            State object with the status provided
        """
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT OR IGNORE INTO asset_versions
            (name, asset_type, department, version, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (asset.name, asset.asset_type, department, version, status),
        )
        self.conn.commit()
        return AssetVersionState(status)

    # --------------------------------------------------
    # Queries
    # --------------------------------------------------

    def get_asset(self, name: str, asset_type: AssetType) -> Asset | None:
        """Retrieve an asset by name and asset type.

        Args:
            name: Asset name.
            asset_type: Asset type.

        Returns:
            Asset object if found, None if not found.
        """
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT * FROM assets WHERE name = ? AND asset_type = ?
            """,
            (name, asset_type),
        )
        row = cur.fetchone()
        if row:
            return Asset(name, asset_type)
        return None

    def get_assets(
        self, name: str | None = None, asset_type: AssetType | None = None
    ) -> Iterator[Asset]:
        """Generator to get all assets matching a name or asset type filter.

        Args:
            name: Asset name filter, None matches all assets.
            asset_type: Asset type filter, None matches all assets.

        Yields:
            Each Asset found.
        """
        # Build the query
        query = "SELECT name, asset_type FROM assets"
        conditions = []
        params = []
        if name:
            conditions.append("name = ?")
            params.append(name)
        if asset_type:
            conditions.append("asset_type = ?")
            params.append(asset_type)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        cur = self.conn.cursor()
        cur.execute(query, params)
        for name, status_type in cur.fetchall():
            yield Asset(name, status_type)

    def get_version(
        self, asset: Asset, department: str, version: int
    ) -> AssetVersion | None:
        """Get a specific version of an asset.

        Args:
            asset: Asset to find the version for.
            department: Department name to find the version for.
            version: Version number to retrieve.

        Returns:
            AssetVersion object if found, None if not found.
        """
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT status
            FROM asset_versions
            WHERE name = ? AND asset_type = ? AND department = ? AND version = ?
            """,
            (asset.name, asset.asset_type, department, version),
        )
        status = cur.fetchone()
        if status:
            return make_asset_version(asset, department, version, status[0])
        return None

    def get_versions(
        self,
        asset: Asset,
        department: str | None = None,
        version: int | None = None,
        status: AssetVersionStatus | None = None,
    ) -> Iterator[AssetVersion]:
        """List asset versions that match the given filters.

        Args:
            asset: Asset to find the version for.
            department: Optionally filter by department.
            version: Optionally filter by version.
            status: Optionally filter by status.

        Yields:
            Each AssetVersion found.
        """
        query = """SELECT name, asset_type, department, version, status 
        FROM asset_versions
        WHERE name = ? AND asset_type = ?"""
        conditions = []
        params = [asset.name, asset.asset_type]
        if department:
            conditions.append("department = ?")
            params.append(department)
        if version:
            conditions.append("version = ?")
            params.append(version)
        if status:
            conditions.append("status = ?")
            params.append(status)
        if conditions:
            query += " AND " + " AND ".join(conditions)
        cur = self.conn.cursor()
        cur.execute(query, params)
        for name, asset_type, department, version, status in cur.fetchall():
            yield make_asset_version(asset, department, version, status)

    def latest(
        self, asset: Asset, department: str, active_only: bool = True
    ) -> AssetVersion | None:
        """Get the latest version of an asset for a specific department.

        Args:
            asset: Asset to find the latest version for.
            department: The department to find the latest version for.
            active_only: If True, inactive versions are ignored.
        """
        query = "SELECT version, status FROM asset_versions WHERE name = ? AND asset_type = ? AND department = ?"
        if active_only:
            query += " AND status = 'active'"
        query += " ORDER BY version DESC LIMIT 1"
        cur = self.conn.cursor()
        cur.execute(query, (asset.name, asset.asset_type, department))
        row = cur.fetchone()
        if row:
            version, status = row
            return make_asset_version(asset, department, version, status)
        return None
