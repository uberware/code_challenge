"""The API for the asset_service commands"""

import json
from pathlib import Path
from typing import Union

from pydantic import ValidationError

from asset_service import db, logger, validation


def load_from_json(
    filename: Union[Path, str], *, registry: db.AssetRegistry | None = None
) -> bool:
    """Load asset version data from a JSON file.

    Args:
        filename: The filename to load the data from, expects to contain a list of asset version objects
        registry: The asset registry instance to use. None creates one on demand.

    Returns:
        True if the file was successfully loaded, False otherwise
        TODO: more error reporting for error/partial/complete results

    Raises:
        TypeError: if registry is not an instance of AssetRegistry or None
    """
    # Validate and load the JSON file
    if isinstance(filename, str):
        filename = Path(filename)
    elif not isinstance(filename, Path):
        logger.error(f"filename must be a string or Path. Got: {type(filename)}")
        return False
    if not filename.exists():
        logger.error(f"file does not exist: {filename}")
        return False
    data = json.loads(filename.read_text())

    # We only support JSON files with lists of objects
    if not isinstance(data, list):
        logger.error(f"file {filename} did not contain a list. Got: {type(data)}")
        return False

    good_versions = validation.find_good_versions(data)

    # Store the valid asset versions into the database
    # TODO: Optimize bulk database operation
    registry = registry or db.AssetRegistry()
    for asset in good_versions:
        registry.asset(asset.name, asset.asset_type)
        for version in good_versions[asset]:
            registry.version(
                asset, version.key.department, version.key.version, version.state.status
            )

    # only considered successful if some data was loaded
    return bool(good_versions)


def add_asset(
    asset_name: str,
    asset_type: str | db.AssetType,
    *,
    registry: db.AssetRegistry | None = None,
) -> db.Asset | None:
    """Add an asset to the registry.

    Args:
        asset_name: The name of the asset to add.
        asset_type: The type of the asset to add.
        registry: The asset registry to use. None creates one on demand.

    Returns:
        The added asset object or None on failure
    """
    # Validate the arguments
    try:
        if not isinstance(asset_type, db.AssetType):
            asset_type = db.AssetType(asset_type)
    except (ValueError, TypeError, ValidationError) as e:
        logger.error(f"Invalid asset data: {asset_name} {asset_type}\n{e}")
        return None
    registry = registry or db.AssetRegistry()
    return registry.asset(asset_name, asset_type)


def add_version(
    asset: db.Asset,
    department: str,
    version: int,
    status: str | db.AssetVersionStatus | None = None,
    *,
    registry: db.AssetRegistry | None = None,
) -> db.AssetVersionState | None:
    """Add an asset version to the registry.

    Does not add the Asset itself to the registry.

    Args:
        asset: The asset to add the version to.
        department: The department of the asset.
        version: The version of the asset.
        status: The status of the asset.
        registry: The asset registry to use. None creates one on demand.

    Returns:
        The asset version status or None on failure
    """
    # Validate the arguments
    try:
        if status is None:
            status = db.AssetVersionStatus.ACTIVE
        asset_version = db.AssetVersion(
            db.AssetVersionKey(asset, department, version),
            db.AssetVersionState(db.AssetVersionStatus(status)),
        )
    except (ValueError, TypeError, ValidationError) as e:
        logger.error(f"Invalid AssetVersion: {version} {department} {status}\n{e}")
        return None
    registry = registry or db.AssetRegistry()
    return registry.version(
        asset,
        asset_version.key.department,
        asset_version.key.version,
        asset_version.state.status,
    )
