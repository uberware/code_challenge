"""Tests the cli module."""

from click.testing import CliRunner

from asset_service import cli


def test__load__no_arguments():
    """Test load command with no arguments."""
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["load"])
    assert result.exit_code == 2
    assert "Error: Missing argument 'FILE_PATH'" in result.output


def test__load__bad_file(tmp_path):
    """Test load command with bad file."""
    filename = tmp_path / "bad.json"
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["load", str(filename)])
    assert result.exit_code == 2
    assert f"Path '{filename}' does not exist" in result.output


def test__load__valid_file(valid_json_file, caplog):
    """Test load command with valid file."""
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["load", str(valid_json_file)])
    assert result.exit_code == 0
    assert f"Loading assets from: {valid_json_file}" in result.output
    assert f"Failed to load assets from: {valid_json_file}" not in result.output
    assert "ERROR" not in caplog.text


def test__load__invalid_file(bad_json_file):
    """Test load command with invalid file."""
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["load", str(bad_json_file)])
    assert result.exit_code == 1
    assert f"Loading assets from: {bad_json_file}" in result.output
    assert f"Failed to load assets from: {bad_json_file}" in result.output


def test__load__partial_data(partial_json_file, caplog):
    """Test load command with partial data."""
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["load", str(partial_json_file)])
    assert result.exit_code == 0
    assert f"Loading assets from: {partial_json_file}" in result.output
    assert f"Failed to load assets from: {partial_json_file}" not in result.output
    assert "Has version gaps: [1, 3]" in caplog.text


def test__add_asset__valid():
    """Test add asset with valid data."""
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["add", "name", "fx"])
    assert result.exit_code == 0
    assert "Adding asset: name/fx" in result.output
    assert "Failed to add asset: name/fx" not in result.output


def test__add_asset__invalid():
    """Test add asset with invalid data."""
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["add", "name", "bad type"])
    assert result.exit_code == 1
    assert "Adding asset: name/bad type" in result.output
    assert "Failed to add asset: name/bad type" in result.output
