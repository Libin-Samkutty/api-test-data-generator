"""Shared pytest fixtures."""
import json
import pytest
from pathlib import Path


SIMPLE_SCHEMA = {
    "type": "object",
    "properties": {
        "user_id": {"type": "string", "format": "uuid"},
        "name": {"type": "string", "faker": "name"},
        "email": {"type": "string", "format": "email"},
        "age": {"type": "integer", "minimum": 18, "maximum": 60},
        "is_active": {"type": "boolean"},
    },
    "required": ["user_id", "email"],
}


@pytest.fixture
def simple_schema() -> dict:
    return SIMPLE_SCHEMA


@pytest.fixture
def schema_file(tmp_path: Path, simple_schema: dict) -> Path:
    p = tmp_path / "schema.json"
    p.write_text(json.dumps(simple_schema))
    return p


@pytest.fixture
def yaml_schema_file(tmp_path: Path) -> Path:
    yaml_content = """
type: object
properties:
  id:
    type: string
    format: uuid
  score:
    type: number
    minimum: 0.0
    maximum: 100.0
required:
  - id
"""
    p = tmp_path / "schema.yaml"
    p.write_text(yaml_content)
    return p
