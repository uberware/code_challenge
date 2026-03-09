"""
Test the cli module.
"""

import pytest
from click.testing import CliRunner

from asset_service import api, cli, db


# Load


def test__load__no_arguments(tmp_db):
    """Test load command with no arguments."""
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["--registry", tmp_db, "load"])
    assert result.exit_code == 2
    assert "Error: Missing argument 'FILE_PATH'" in result.output


def test__load__bad_file(tmp_db, tmp_path):
    """Test load command with bad file."""
    filename = tmp_path / "bad.json"
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["--registry", tmp_db, "load", str(filename)])
    assert result.exit_code == 2
    assert f"Path '{filename}' does not exist" in result.output


def test__load__valid_file(valid_json_file, tmp_db, caplog):
    """Test load command with valid file."""
    runner = CliRunner()
    result = runner.invoke(
        cli.cli, ["--registry", tmp_db, "load", str(valid_json_file)]
    )
    assert result.exit_code == 0
    assert f"Loading assets from: {valid_json_file}" in result.output
    assert f"Failed to load assets from: {valid_json_file}" not in result.output
    assert "ERROR" not in caplog.text


def test__load__invalid_file(bad_json_file, tmp_db, tmp_path):
    """Test load command with invalid file."""
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["--registry", tmp_db, "load", str(bad_json_file)])
    assert result.exit_code == 1
    assert f"Loading assets from: {bad_json_file}" in result.output
    assert f"Failed to load assets from: {bad_json_file}" in result.output


def test__load__partial_data(partial_json_file, tmp_db, caplog):
    """Test load command with partial data."""
    runner = CliRunner()
    result = runner.invoke(
        cli.cli, ["--registry", tmp_db, "load", str(partial_json_file)]
    )
    assert result.exit_code == 0
    assert f"Loading assets from: {partial_json_file}" in result.output
    assert f"Failed to load assets from: {partial_json_file}" not in result.output
    assert "Has version gaps: [1, 3]" in caplog.text


# Add asset


def test__add_asset__valid(tmp_db):
    """Test add asset with valid data."""
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["--registry", tmp_db, "add", "name", "fx"])
    assert result.exit_code == 0
    assert "Adding asset: name/fx" in result.output
    assert "Failed to add asset: name/fx" not in result.output


def test__add_asset__invalid(tmp_db):
    """Test add asset with invalid data."""
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["--registry", tmp_db, "add", "name", "bad type"])
    assert result.exit_code == 1
    assert "Adding asset: name/bad type" in result.output
    assert "Failed to add asset: name/bad type" in result.output


# Add version


def test__add_version__valid(tmp_db):
    """Test add version with valid data."""
    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        ["--registry", tmp_db, "versions", "add", "name", "set", "dep", "1", "active"],
    )
    assert result.exit_code == 0
    assert "Adding asset: name/set" in result.output
    assert "Failed to add asset: name/set" not in result.output
    assert "Adding version: dep/1 - active" in result.output
    assert "Failed to add version: dep/1 active" not in result.output


def test__add_version__invalid_asset(tmp_db):
    """Test add version with invalid asset data."""
    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        [
            "--registry",
            tmp_db,
            "versions",
            "add",
            "name",
            "bad type",
            "dep",
            "1",
            "active",
        ],
    )
    assert result.exit_code == 1
    assert "Adding asset: name/bad type" in result.output
    assert "Failed to add asset: name/bad type" in result.output
    assert "Adding version: dep/1 - active" not in result.output
    assert "Failed to add version: dep/1 active" not in result.output


def test__add_version__invalid_version(tmp_db):
    """Test add version with invalid version data."""
    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        ["--registry", tmp_db, "versions", "add", "name", "set", "dep", "1", "bad"],
    )
    assert result.exit_code == 1
    assert "Adding asset: name/set" in result.output
    assert "Failed to add asset: name/set" not in result.output
    assert "Adding version: dep/1 - bad" in result.output
    assert "Failed to add version: dep/1 - bad" in result.output


# get_asset


def test__get_asset__missing(tmp_db):
    """Test get_asset with an empty database (missing value)."""
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["--registry", tmp_db, "get", "name", "fx"])
    assert result.exit_code == 1
    assert "Asset not found: name/fx" in result.output


def test__get_asset__valid(tmp_db):
    """Test get_asset with valid data."""
    db.AssetRegistry(tmp_db).register_asset("name", db.AssetType.FX)
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["--registry", tmp_db, "get", "name", "fx"])
    assert result.exit_code == 0
    assert "Found Asset: name/fx" in result.output


# list


@pytest.mark.parametrize(
    "name, asset_type, expected",
    [
        (None, None, [("hero", "character"), ("hero", "fx"), ("spoon", "prop")]),
        ("hero", None, [("hero", "character"), ("hero", "fx")]),
        (None, "fx", [("hero", "fx")]),
        ("spoon", "prop", [("spoon", "prop")]),
        ("spoon", "fx", []),
    ],
)
def test__list(name, asset_type, expected, tmp_db, valid_json_file):
    """Test list."""
    api.load_from_json(valid_json_file, registry=db.AssetRegistry(tmp_db))
    runner = CliRunner()
    command = ["--registry", tmp_db, "list"]
    if name:
        command += ["--asset-name", name]
    if asset_type:
        command += ["--asset-type", asset_type]
    result = runner.invoke(cli.cli, command)
    assert result.exit_code == 0 if expected else 1
    for names in expected:
        assert f"Found Asset: {names[0]}/{names[1]}" in result.output


# versions get


def test__versions__get__missing(tmp_db):
    """Test get_versions with an empty database (missing value)."""
    runner = CliRunner()
    result = runner.invoke(
        cli.cli, ["--registry", tmp_db, "versions", "get", "name", "fx", "dept", "1"]
    )
    assert result.exit_code == 1
    assert "Version not found: name/fx - dept:1" in result.output


def test__versions__get__valid(tmp_db, valid_json_file):
    """Test get_versions with valid data."""
    api.load_from_json(valid_json_file, registry=db.AssetRegistry(tmp_db))
    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        ["--registry", tmp_db, "versions", "get", "hero", "fx", "texturing", "1"],
    )
    assert result.exit_code == 0
    assert "Found Version: hero/fx - texturing:1 = active" in result.output


# versions list


def test__versions__list__missing(tmp_db):
    """Test get_versions with invalid data."""
    runner = CliRunner()
    result = runner.invoke(
        cli.cli, ["--registry", tmp_db, "versions", "list", "hero", "fx"]
    )
    assert result.exit_code == 1
    assert "Found Version: hero/fx - texturing:1 = active" not in result.output


def test__versions__list__valid(tmp_db, valid_json_file):
    """Test listing versions with valid data."""
    api.load_from_json(valid_json_file, registry=db.AssetRegistry(tmp_db))
    runner = CliRunner()
    result = runner.invoke(
        cli.cli, ["--registry", tmp_db, "versions", "list", "hero", "fx"]
    )
    assert result.exit_code == 0
    assert "Found Version: hero/fx - texturing:1 = active" in result.output


# Latest


def test__versions__latest__missing(tmp_db):
    """Test get_versions with invalid data."""
    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        ["--registry", tmp_db, "versions", "latest", "hero", "character", "modeling"],
    )
    assert result.exit_code == 1
    assert "No versions found: hero/character - modeling" in result.output


def test__versions__latest__valid(tmp_db, valid_json_file):
    """Test get_versions with valid data."""
    api.load_from_json(valid_json_file, registry=db.AssetRegistry(tmp_db))
    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        ["--registry", tmp_db, "versions", "latest", "hero", "character", "modeling"],
    )
    assert result.exit_code == 0
    assert "Latest version: hero/character - modeling:2" in result.output
