"""Tests for schema_loader module."""
import json
import pytest
from pathlib import Path

from api_test_data_generator.generator.schema_loader import load_schema, load_schema_from_dict
from api_test_data_generator.generator.exceptions import SchemaLoadError


class TestLoadSchema:
    def test_load_json(self, schema_file: Path):
        schema = load_schema(schema_file)
        assert isinstance(schema, dict)
        assert "properties" in schema

    def test_load_yaml(self, yaml_schema_file: Path):
        schema = load_schema(yaml_schema_file)
        assert isinstance(schema, dict)
        assert "properties" in schema

    def test_file_not_found(self, tmp_path: Path):
        with pytest.raises(SchemaLoadError, match="not found"):
            load_schema(tmp_path / "nonexistent.json")

    def test_invalid_json(self, tmp_path: Path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{ not valid json }")
        with pytest.raises(SchemaLoadError, match="Failed to parse"):
            load_schema(bad_file)

    def test_unsupported_extension(self, tmp_path: Path):
        p = tmp_path / "schema.toml"
        p.write_text("[schema]")
        with pytest.raises(SchemaLoadError, match="Unsupported schema format"):
            load_schema(p)

    def test_non_dict_schema_raises(self, tmp_path: Path):
        p = tmp_path / "list_schema.json"
        p.write_text(json.dumps([1, 2, 3]))
        with pytest.raises(SchemaLoadError, match="must be a JSON/YAML object"):
            load_schema(p)


class TestLoadSchemaFromDict:
    def test_valid_dict(self):
        schema = load_schema_from_dict({"type": "object"})
        assert schema == {"type": "object"}

    def test_non_dict_raises(self):
        with pytest.raises(SchemaLoadError):
            load_schema_from_dict([1, 2])  # type: ignore
