"""Unit tests for the db module."""

import pytest

from asset_service import api


def make_asset_version(
    asset: api.Asset, department: str | None = None, number: int = 1
) -> api.AssetVersion:
    """Helper to make AssetVersion objects"""
    department = department or "department"
    return api.AssetVersion(
        api.AssetVersionKey(asset, department, number),
        api.AssetVersionState(api.AssetVersionStatus.ACTIVE),
    )


def test__validate_version_list__empty():
    """Test validate_version_list works as expectedwith empty version list."""
    asset = api.Asset("asset_name", api.AssetType.FX)
    versions = [make_asset_version(asset, number=it) for it in range(1, 6)]
    assert api._validate_version_list(versions)
