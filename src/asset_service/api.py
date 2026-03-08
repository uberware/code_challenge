"""The API for the asset_service commands"""

import json
from pathlib import Path
from typing import Union

from asset_service import logger
from asset_service.db import AssetRegistry
from asset_service.validation import find_good_versions


def load_from_json(filename: Union[Path, str]) -> bool:
    """Load asset version data from a JSON file.

    Args:
        filename: The filename to load the data from, expects to contain a list of asset version objects

    Returns:
        True if the file was successfully loaded, False otherwise
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

    good_versions = find_good_versions(data)

    # Store the valid asset versions into the database
    # TODO: Optimize bulk database operation
    registry = AssetRegistry()
    for asset in good_versions:
        registry.asset(asset.name, asset.asset_type)
        for version in good_versions[asset]:
            registry.version(
                asset, version.key.department, version.key.version, version.state.status
            )

    # only considered successful if some data was loaded
    return bool(good_versions)
