"""Tests for the DataGenerator core engine."""
import time
import pytest
from pathlib import Path

from api_test_data_generator.generator.core import DataGenerator
from api_test_data_generator.generator.exceptions import ValidationError, SchemaLoadError


class TestDataGeneratorInit:
    def test_from_dict(self, simple_schema):
        gen = DataGenerator.from_dict(simple_schema)
        assert gen is not None

    def test_from_file(self, schema_file):
        gen = DataGenerator.from_file(schema_file)
        assert gen is not None

    def test_from_file_yaml(self, yaml_schema_file):
        gen = DataGenerator.from_file(yaml_schema_file)
        assert gen is not None

    def test_invalid_file_raises(self, tmp_path):
        with pytest.raises(SchemaLoadError):
            DataGenerator.from_file(tmp_path / "missing.json")


class TestGenerateRecord:
    def test_returns_dict(self, simple_schema):
        gen = DataGenerator.from_dict(simple_schema, seed=42)
        record = gen.generate_record()
        assert isinstance(record, dict)

    def test_required_fields_present(self, simple_schema):
        gen = DataGenerator.from_dict(simple_schema, seed=42)
        record = gen.generate_record()
        assert "user_id" in record
        assert "email" in record

    def test_user_id_is_uuid(self, simple_schema):
        import uuid
        gen = DataGenerator.from_dict(simple_schema, seed=42)
        record = gen.generate_record()
        uuid.UUID(record["user_id"])  # raises if not valid UUID

    def test_email_contains_at(self, simple_schema):
        gen = DataGenerator.from_dict(simple_schema, seed=42)
        record = gen.generate_record()
        assert "@" in record["email"]

    def test_age_within_bounds(self, simple_schema):
        gen = DataGenerator.from_dict(simple_schema, seed=42)
        for _ in range(20):
            record = gen.generate_record()
            if "age" in record:
                assert 18 <= record["age"] <= 60

    def test_is_active_is_bool(self, simple_schema):
        gen = DataGenerator.from_dict(simple_schema, seed=42)
        for _ in range(20):
            record = gen.generate_record()
            if "is_active" in record:
                assert isinstance(record["is_active"], bool)


class TestDeterministicOutput:
    def test_same_seed_same_output(self, simple_schema):
        from api_test_data_generator.utils.randomizer import reset_faker
        reset_faker()
        gen1 = DataGenerator.from_dict(simple_schema, seed=99)
        records1 = gen1.generate_bulk(5)

        reset_faker()
        gen2 = DataGenerator.from_dict(simple_schema, seed=99)
        records2 = gen2.generate_bulk(5)

        assert records1 == records2

    def test_different_seeds_different_output(self, simple_schema):
        from api_test_data_generator.utils.randomizer import reset_faker
        reset_faker()
        gen1 = DataGenerator.from_dict(simple_schema, seed=1)
        records1 = gen1.generate_bulk(10)

        reset_faker()
        gen2 = DataGenerator.from_dict(simple_schema, seed=2)
        records2 = gen2.generate_bulk(10)

        assert records1 != records2


class TestGenerateBulk:
    def test_returns_correct_count(self, simple_schema):
        gen = DataGenerator.from_dict(simple_schema, seed=42)
        records = gen.generate_bulk(10)
        assert len(records) == 10

    def test_all_records_are_dicts(self, simple_schema):
        gen = DataGenerator.from_dict(simple_schema, seed=42)
        records = gen.generate_bulk(5)
        assert all(isinstance(r, dict) for r in records)

    def test_count_less_than_one_raises(self, simple_schema):
        gen = DataGenerator.from_dict(simple_schema, seed=42)
        with pytest.raises(ValueError):
            gen.generate_bulk(0)

    def test_bulk_performance_10k(self, simple_schema):
        """CLI should generate 10k records in < 2 seconds."""
        gen = DataGenerator.from_dict(simple_schema, seed=42, validate=False)
        start = time.perf_counter()
        records = gen.generate_bulk(10_000)
        elapsed = time.perf_counter() - start
        assert len(records) == 10_000
        assert elapsed < 5.0, f"Bulk generation took {elapsed:.2f}s (limit 5s)"


class TestValidation:
    def test_validation_passes_for_valid_schema(self, simple_schema):
        gen = DataGenerator.from_dict(simple_schema, seed=42, validate=True)
        record = gen.generate_record()
        assert isinstance(record, dict)

    def test_validation_disabled(self, simple_schema):
        gen = DataGenerator.from_dict(simple_schema, seed=42, validate=False)
        records = gen.generate_bulk(5)
        assert len(records) == 5


class TestEdgeCases:
    def test_empty_schema(self):
        gen = DataGenerator.from_dict({}, seed=1, validate=False)
        record = gen.generate_record()
        assert record == {}

    def test_deeply_nested_schema(self):
        schema = {
            "type": "object",
            "properties": {
                "level1": {
                    "type": "object",
                    "properties": {
                        "level2": {
                            "type": "object",
                            "properties": {
                                "value": {"type": "integer"}
                            },
                            "required": ["value"],
                        }
                    },
                    "required": ["level2"],
                }
            },
            "required": ["level1"],
        }
        gen = DataGenerator.from_dict(schema, seed=1, validate=False)
        record = gen.generate_record()
        assert "level1" in record
        assert "level2" in record["level1"]
        assert "value" in record["level1"]["level2"]

    def test_schema_with_array_field(self):
        schema = {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 2,
                    "maxItems": 4,
                }
            },
            "required": ["tags"],
        }
        gen = DataGenerator.from_dict(schema, seed=1, validate=False)
        record = gen.generate_record()
        assert isinstance(record["tags"], list)
        assert 2 <= len(record["tags"]) <= 4

    def test_enum_schema(self):
        schema = {
            "type": "object",
            "properties": {
                "status": {"enum": ["active", "inactive", "pending"]}
            },
            "required": ["status"],
        }
        gen = DataGenerator.from_dict(schema, seed=1, validate=False)
        for _ in range(10):
            record = gen.generate_record()
            assert record["status"] in ["active", "inactive", "pending"]
