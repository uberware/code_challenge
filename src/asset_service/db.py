"""Asset data types and container."""

import sqlite3
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
    def __init__(self):
        logger.info(f"Starting up database: {DATABASE_PATH}")
        self.conn = sqlite3.connect(DATABASE_PATH)
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

    def asset(self, name: str, asset_type: AssetType) -> Asset:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT OR IGNORE INTO assets (name, asset_type) VALUES (?, ?)
            """,
            (name, asset_type),
        )
        self.conn.commit()
        return Asset(name, asset_type)

    def version(
        self,
        asset: Asset,
        department: str,
        version: int,
        status: AssetVersionStatus = AssetVersionStatus.ACTIVE,
    ) -> AssetVersionState:
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
