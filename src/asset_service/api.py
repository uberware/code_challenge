"""The API for the asset_service commands"""

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Union

from pydantic import ValidationError

from asset_service import logger
from asset_service.db import (
    Asset,
    AssetRegistry,
    AssetType,
    AssetVersion,
    AssetVersionKey,
    AssetVersionState,
    AssetVersionStatus,
)


def load_from_json(filename: Union[Path, str]):
    """Load asset version data from a JSON file.

    Args:
        filename: The filename to load the data from, expects to contain a list of asset version objects

    Raises:
        TypeError: The argument is not a file or Path
        OSError: The filename does not point a file that actually exists
        ValueError: The JSON file did not contain a list
    """
    # Validate and load the JSON file
    if isinstance(filename, str):
        filename = Path(filename)
    elif not isinstance(filename, Path):
        raise TypeError(f"filename must be a string or Path. Got: {type(filename)}")
    if not filename.exists():
        raise OSError(f"file does not exist: {filename}")
    data = json.loads(filename.read_text())

    # We only support JSON files with lists of objects
    if not isinstance(data, list):
        raise ValueError(f"file {filename} did not contain a list. Got: {type(data)}")

    good_versions = _find_good_versions(data)

    # Store the valid asset versions into the database
    # TODO: Optimize bulk database operation
    registry = AssetRegistry()
    for asset, versions in good_versions.items():
        for version in versions:
            registry.asset(asset.name, asset.asset_type)
            registry.version(
                asset, version.key.department, version.key.version, version.state.status
            )


def _validate_asset_version(item: Any) -> tuple[Asset | None, AssetVersion | None]:
    """Validate that the item is a dictionary and contains the required elements.

    Args:
        item: One item from the list in the JSON file

    Returns:
        tuple of Asset, AssetVersionKey, AssetVersionState or None, None on failure
    """
    failures = []
    warnings = []
    # validate dictionary with required keys
    if not isinstance(item, dict):
        failures.append("Item is not a dictionary")
    else:
        asset_data = item.get("asset")
        if not isinstance(asset_data, dict):
            failures.append("Item missing asset information")
        else:
            if "name" not in asset_data:
                failures.append("Unable to determine asset name")
            if "type" not in asset_data:
                failures.append("Unable to determine asset type")
        if "department" not in item:
            failures.append("Unable to determine department")
        if "version" not in item:
            failures.append("Unable to determine version")
        if "status" not in item:
            failures.append("Unable to determine status")
        warnings.extend(
            [
                f"Ignoring unknown key: {key}"
                for key in item
                if key not in ["name", "type", "department", "version", "status"]
            ]
        )

    if failures:
        failures = "\n- ".join(failures)
        logger.error(f"Invalid item:\n{item}\n- {failures}")
        return None, None

    # valdate item data
    try:
        asset = Asset(asset_data["name"], AssetType(asset_data["type"]))
        version = AssetVersion(
            key=AssetVersionKey(asset, item["department"], item["version"]),
            state=AssetVersionState(AssetVersionStatus(item["status"])),
        )
    except (TypeError, ValidationError) as e:
        logger.error(f"Invalid item:\n{item}\n{e}")
        return None, None

    if warnings:
        warnings = "\n- ".join(warnings)
        logger.warning(f"Item generated warnings:\n{item}\n- {warnings}")
    return asset, version


def _validate_version_list(version_list: list[AssetVersion]) -> dict[str, list[str]]:
    """Validates that the version list starts at 1 and increments without gaps.

    Assumes version list is not empty.

    Returns:
        dict with a list of failures for each department
    """
    failures = defaultdict(list)
    # sort by department
    ver_by_dept = defaultdict(list)
    for version in version_list:
        ver_by_dept[version.department].append(version.version)
    # validate each department has versions starting at 1 and incrementing without gaps
    for department, dept_versions in ver_by_dept.items():
        min_ver = min(dept_versions)
        if min_ver != 1:
            failures[department].append(f"Versions do not start at 1: {min_ver})")
        expected_count = max(dept_versions)
        if len(dept_versions) < expected_count:
            failures[department].append(f"Has version gaps: {dept_versions}")
        elif len(dept_versions) > expected_count:
            failures[department].append(f"Has duplicate versions: {dept_versions}")
    return failures


def _find_good_versions(data: list) -> dict[Asset, list[AssetVersion]]:
    """Parses the raw data into valid asset version data ready to store.

    The required criteria are that the version starts at 1 and goes up by 1 without holes.

    Args:
        data: input list from the decoded JSON

    Returns:
        a dictionary mapping Assets to a list of AssetVersions
    """
    # build a table of asset versions
    check_versions: dict[Asset, list[AssetVersion]] = defaultdict(list)
    for item in data:
        asset, version = _validate_asset_version(item)
        if asset and version:
            check_versions[asset].append(version)
    # check each one to build the good final list of asset versions
    good_versions: dict[Asset, list[AssetVersion]] = defaultdict(list)
    for asset, version_list in check_versions.items():
        if not version_list:
            logger.error(f"No versions supplied for: {asset}")
            continue
        bad_depts = _validate_version_list(version_list)
        clean_versions = [
            ver for ver in version_list if ver.department not in bad_depts
        ]
        if not clean_versions:
            logger.error(f"No good versions supplied for: {asset}")
        else:
            good_versions[asset] = clean_versions
        for dept, failures in bad_depts:
            for failure in failures:
                logger.error(f"{asset} {dept}: {failure}")
    return good_versions
