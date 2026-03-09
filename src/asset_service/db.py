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
    # Mutation
    # --------------------------------------------------

    def set_status(
        self,
        asset: Asset,
        department: str,
        version: int,
        status: AssetVersionStatus,
    ):
        cur = self.conn.cursor()
        cur.execute(
            """
            UPDATE asset_versions
            SET status = ?
            WHERE name = ? AND asset_type = ?
            AND department = ? AND version = ?
            """,
            (status, asset.name, asset.asset_type, department, version),
        )
        self.conn.commit()

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
            List each object found.
        """
        cur = self.conn.cursor()
        if name and asset_type:
            where = "WHERE name = ? AND asset_type = ?"
            data = (name, asset_type)
        elif name:
            where = "WHERE name = ?"
            data = (name,)
        elif asset_type is not None:
            where = "WHERE asset_type = ?"
            data = (asset_type,)
        else:
            where = data = None
        if data is not None:
            cur.execute(f"SELECT name, asset_type FROM assets {where}", data)
        else:
            cur.execute("SELECT name, asset_type FROM assets")
        for name, status_type in cur.fetchall():
            yield Asset(name, status_type)

    def versions_for(self, asset: Asset, department: str | None = None):
        cur = self.conn.cursor()
        if department is None:
            cur.execute(
                """
                SELECT department, version, status
                FROM asset_versions
                WHERE name=? AND asset_type=?
                """,
                (asset.name, asset.asset_type),
            )
        else:
            cur.execute(
                """
                SELECT department, version, status
                FROM asset_versions
                WHERE name=? AND asset_type=? AND department=?
                """,
                (asset.name, asset.asset_type, department),
            )
        for dept, version, status in cur.fetchall():
            yield (
                AssetVersionKey(asset, dept, version),
                AssetVersionState(AssetVersionStatus(status)),
            )

    def latest(self, asset: Asset, department: str):
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT version, status
            FROM asset_versions
            WHERE name=? AND asset_type=? AND department=?
            ORDER BY version DESC
            LIMIT 1
            """,
            (asset.name, asset.asset_type, department),
        )
        row = cur.fetchone()
        if row:
            version, status = row
            return (
                AssetVersionKey(asset, department, version),
                AssetVersionState(AssetVersionStatus(status)),
            )
        return None


@dataclass
class AssetVersion:
    """A combination of one key and one state."""

    key: AssetVersionKey
    state: AssetVersionState
