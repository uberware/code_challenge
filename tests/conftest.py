"""Common test fixtures."""

import json
import sqlite3
from pathlib import Path

import pytest


@pytest.fixture
def valid_data():
    original = Path(__file__).parent / "sample_data" / "small.json"
    return json.loads(original.read_text())


@pytest.fixture
def valid_json_file(valid_data, tmp_path):
    """A fixture that creates a valid json file on disk."""
    original = Path(__file__).parent / "sample_data" / "small.json"
    filename = tmp_path / "valid_data.json"
    filename.write_text(original.read_text())
    return filename


@pytest.fixture
def bad_json_file(valid_data, tmp_path):
    """A fixture that creates a json file on disk with gap in versions."""
    original = Path(__file__).parent / "sample_data" / "bad.json"
    filename = tmp_path / "invalid_data.json"
    filename.write_text(original.read_text())
    return filename


@pytest.fixture
def memory_db():
    """A fixture that creates a sqlite memory database."""
    return sqlite3.connect(":memory:")


@pytest.fixture
def tmp_db(tmp_path):
    """Fixture to create a temporary database file path."""
    return tmp_path / "test.db"


@pytest.fixture
def partial_json_file(valid_data, tmp_path):
    """A fixture that creates a json file on disk with gap in versions."""
    original = Path(__file__).parent / "sample_data" / "partial.json"
    filename = tmp_path / "partial_data.json"
    filename.write_text(original.read_text())
    return filename
