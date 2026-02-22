"""Tests for JSON Schema validators."""
import pytest
from api_test_data_generator.generator.validators import validate_record, validate_bulk
from api_test_data_generator.generator.exceptions import ValidationError

SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer", "minimum": 0},
    },
    "required": ["name"],
}


class TestValidateRecord:
    def test_valid_record_passes(self):
        validate_record({"name": "Alice", "age": 30}, SCHEMA)

    def test_missing_required_raises(self):
        with pytest.raises(ValidationError, match="validation"):
            validate_record({"age": 30}, SCHEMA)

    def test_wrong_type_raises(self):
        with pytest.raises(ValidationError):
            validate_record({"name": 123}, SCHEMA)

    def test_minimum_violation_raises(self):
        with pytest.raises(ValidationError):
            validate_record({"name": "Bob", "age": -1}, SCHEMA)


class TestValidateBulk:
    def test_all_valid(self):
        records = [{"name": "A"}, {"name": "B", "age": 5}]
        validate_bulk(records, SCHEMA)

    def test_one_invalid_raises(self):
        records = [{"name": "A"}, {"age": 10}]  # second missing required
        with pytest.raises(ValidationError, match="Record 1"):
            validate_bulk(records, SCHEMA)
