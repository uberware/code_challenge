"""
Utilities for validating data.
"""

from collections import defaultdict
from typing import Any

from pydantic import ValidationError

from asset_service import logger
from asset_service.db import (
    Asset,
    AssetVersion,
    AssetType,
    AssetVersionKey,
    AssetVersionState,
    AssetVersionStatus,
)


def validate_asset_version(item: Any) -> tuple[Asset | None, AssetVersion | None]:
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
                if key
                not in ["asset", "name", "type", "department", "version", "status"]
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
    except (TypeError, ValueError, ValidationError) as e:
        logger.error(f"Invalid item:\n{item}\n{e}")
        return None, None

    if warnings:
        warnings = "\n- ".join(warnings)
        logger.warning(f"Item generated warnings:\n{item}\n- {warnings}")
    return asset, version


def validate_version_list(version_list: list[AssetVersion]) -> dict[str, list[str]]:
    """Validates that the version list starts at 1 and increments without gaps.

    Assumes version list is not empty.

    Returns:
        dict with a list of failures for each department
    """
    failures = defaultdict(list)
    # sort by department
    ver_by_dept = defaultdict(list)
    for version in version_list:
        ver_by_dept[version.key.department].append(version.key.version)
    # validate each department has versions starting at 1 and incrementing without gaps
    for department, dept_versions in ver_by_dept.items():
        min_ver = min(dept_versions)
        if min_ver != 1:
            failures[department].append(f"Versions do not start at 1: {min_ver}")
        expected_count = max(dept_versions) - min_ver + 1
        if len(dept_versions) < expected_count:
            failures[department].append(f"Has version gaps: {dept_versions}")
        elif len(dept_versions) > expected_count:
            failures[department].append(f"Has duplicate versions: {dept_versions}")
    return dict(failures)


def find_good_versions(data: list) -> dict[Asset, list[AssetVersion]]:
    """Parses the raw data into valid asset version data ready to store.

    The required criteria are that the version starts at 1 and goes up by 1 without holes.
    TODO: it's all or nothing. Possible improvement is to save versions 1 through last good one

    Args:
        data: input list from the decoded JSON

    Returns:
        a dictionary mapping Assets to a list of AssetVersions
    """
    # build a table of asset versions
    check_versions: dict[Asset, list[AssetVersion]] = defaultdict(list)
    for item in data:
        asset, version = validate_asset_version(item)
        if asset and version:
            check_versions[asset].append(version)
    # check each one to build the good final list of asset versions
    good_versions: dict[Asset, list[AssetVersion]] = defaultdict(list)
    for asset, version_list in check_versions.items():
        # the list is not empty because the asset value would not exist
        # if there was not at least 1 valid version
        bad_depts = validate_version_list(version_list)
        clean_versions = [
            ver for ver in version_list if ver.key.department not in bad_depts
        ]
        if not clean_versions:
            logger.error(f"No good versions supplied for: {asset}")
        else:
            good_versions[asset] = clean_versions
        for dept, failures in bad_depts.items():
            for failure in failures:
                logger.error(f"{asset} {dept}: {failure}")
    return dict(good_versions)
