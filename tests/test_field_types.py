"""Unit tests for field type generators."""
import logging
import pytest
import re
from api_test_data_generator.generator.field_types import (
    StringGenerator,
    IntegerGenerator,
    FloatGenerator,
    BooleanGenerator,
    UUIDGenerator,
    EmailGenerator,
    PhoneGenerator,
    AddressGenerator,
    DateGenerator,
    DateTimeGenerator,
    EnumGenerator,
    ArrayGenerator,
    ObjectGenerator,
    RegexGenerator,
    FakerFieldGenerator,
    FieldGeneratorRegistry,
)
from api_test_data_generator.generator.exceptions import UnsupportedFieldTypeError
from api_test_data_generator.utils.seed_manager import set_seed
from api_test_data_generator.utils.randomizer import reset_faker


@pytest.fixture(autouse=True)
def reset_seed_before_each():
    """Ensure clean seed state for each test."""
    set_seed(42)
    reset_faker()
    yield
    reset_faker()


class TestStringGenerator:
    def test_returns_string(self):
        result = StringGenerator().generate({})
        assert isinstance(result, str)

    def test_respects_min_max_length(self):
        result = StringGenerator().generate({"minLength": 10, "maxLength": 10})
        assert len(result) == 10

    def test_default_range(self):
        result = StringGenerator().generate({})
        assert 5 <= len(result) <= 20


class TestIntegerGenerator:
    def test_returns_integer(self):
        assert isinstance(IntegerGenerator().generate({}), int)

    def test_respects_bounds(self):
        for _ in range(20):
            val = IntegerGenerator().generate({"minimum": 5, "maximum": 10})
            assert 5 <= val <= 10

    def test_default_range(self):
        val = IntegerGenerator().generate({})
        assert 0 <= val <= 1_000_000


class TestFloatGenerator:
    def test_returns_float(self):
        result = FloatGenerator().generate({})
        assert isinstance(result, float)

    def test_respects_bounds(self):
        for _ in range(20):
            val = FloatGenerator().generate({"minimum": 1.0, "maximum": 2.0})
            assert 1.0 <= val <= 2.0

    def test_precision(self):
        val = FloatGenerator().generate({"minimum": 0, "maximum": 100, "precision": 3})
        assert len(str(val).split(".")[-1]) <= 3


class TestBooleanGenerator:
    def test_returns_bool(self):
        assert isinstance(BooleanGenerator().generate({}), bool)

    def test_generates_both_values(self):
        results = {BooleanGenerator().generate({}) for _ in range(50)}
        assert True in results
        assert False in results


class TestUUIDGenerator:
    def test_returns_uuid_string(self):
        import uuid
        val = UUIDGenerator().generate({})
        uuid.UUID(val)  # raises if invalid

    def test_returns_string(self):
        assert isinstance(UUIDGenerator().generate({}), str)


class TestEmailGenerator:
    def test_contains_at(self):
        assert "@" in EmailGenerator().generate({})

    def test_returns_string(self):
        assert isinstance(EmailGenerator().generate({}), str)


class TestPhoneGenerator:
    def test_returns_string(self):
        assert isinstance(PhoneGenerator().generate({}), str)


class TestAddressGenerator:
    def test_returns_dict_with_keys(self):
        result = AddressGenerator().generate({})
        assert isinstance(result, dict)
        for key in ("street", "city", "state", "country", "postal_code"):
            assert key in result


class TestDateGenerator:
    def test_returns_iso_date_string(self):
        from datetime import date
        val = DateGenerator().generate({})
        date.fromisoformat(val)  # raises if invalid

    def test_returns_string(self):
        assert isinstance(DateGenerator().generate({}), str)


class TestDateTimeGenerator:
    def test_returns_iso_datetime(self):
        from datetime import datetime
        val = DateTimeGenerator().generate({})
        datetime.fromisoformat(val)

    def test_returns_string(self):
        assert isinstance(DateTimeGenerator().generate({}), str)


class TestEnumGenerator:
    def test_returns_one_of_values(self):
        config = {"enum": ["a", "b", "c"]}
        for _ in range(20):
            assert EnumGenerator().generate(config) in ["a", "b", "c"]

    def test_raises_on_empty_enum(self):
        with pytest.raises(UnsupportedFieldTypeError):
            EnumGenerator().generate({"enum": []})

    def test_single_item_enum(self):
        assert EnumGenerator().generate({"enum": ["only"]}) == "only"


class TestArrayGenerator:
    def test_returns_list(self):
        assert isinstance(ArrayGenerator().generate({}), list)

    def test_respects_min_max_items(self):
        config = {"minItems": 3, "maxItems": 3, "items": {"type": "integer"}}
        result = ArrayGenerator().generate(config)
        assert len(result) == 3

    def test_nested_types(self):
        config = {"minItems": 2, "maxItems": 2, "items": {"type": "boolean"}}
        result = ArrayGenerator().generate(config)
        assert all(isinstance(x, bool) for x in result)

    def test_inverted_min_max_does_not_raise(self):
        """minItems > maxItems must not crash — clamps to minItems length."""
        result = ArrayGenerator().generate(
            {"minItems": 5, "maxItems": 2, "items": {"type": "string"}}
        )
        assert isinstance(result, list)
        assert len(result) == 5

    def test_inverted_min_max_logs_warning(self, caplog):
        """minItems > maxItems must emit a WARNING."""
        with caplog.at_level(
            logging.WARNING, logger="api_test_data_generator.generator.field_types"
        ):
            ArrayGenerator().generate({"minItems": 5, "maxItems": 2, "items": {"type": "string"}})
        assert "minItems" in caplog.text
        assert "maxItems" in caplog.text
        assert any(r.levelno == logging.WARNING for r in caplog.records)

    def test_equal_min_max_returns_exact_count(self):
        """minItems == maxItems is a valid boundary case."""
        result = ArrayGenerator().generate(
            {"minItems": 3, "maxItems": 3, "items": {"type": "integer"}}
        )
        assert isinstance(result, list)
        assert len(result) == 3


class TestObjectGenerator:
    def test_returns_dict(self):
        config = {
            "properties": {
                "x": {"type": "integer"},
                "y": {"type": "string"},
            },
            "required": ["x", "y"],
        }
        result = ObjectGenerator().generate(config)
        assert isinstance(result, dict)
        assert "x" in result
        assert "y" in result

    def test_required_fields_always_present(self):
        config = {
            "properties": {"req": {"type": "boolean"}},
            "required": ["req"],
        }
        for _ in range(20):
            result = ObjectGenerator().generate(config)
            assert "req" in result

    def test_empty_properties(self):
        result = ObjectGenerator().generate({})
        assert result == {}


class TestRegexGenerator:
    def test_returns_string(self):
        assert isinstance(RegexGenerator().generate({"pattern": r"\d{5}"}), str)

    def test_simple_digit_pattern(self):
        result = RegexGenerator().generate({"pattern": r"\d{4}"})
        # Should contain only digits (may have extra chars from fallback)
        assert isinstance(result, str)


class TestFakerFieldGenerator:
    def test_known_method(self):
        result = FakerFieldGenerator().generate({"faker": "name"})
        assert isinstance(result, str)
        assert len(result) > 0

    def test_unknown_method_falls_back(self):
        result = FakerFieldGenerator().generate({"faker": "nonexistent_method_xyz"})
        assert isinstance(result, str)

    def test_unknown_method_logs_warning(self, caplog):
        """Invalid faker key must emit a WARNING visible at default log level."""
        with caplog.at_level(
            logging.WARNING, logger="api_test_data_generator.generator.field_types"
        ):
            result = FakerFieldGenerator().generate({"faker": "nonexistent_xyz_method"})
        assert isinstance(result, str)
        assert "nonexistent_xyz_method" in caplog.text
        warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert warning_records, "Expected at least one WARNING log record"


class TestFieldGeneratorRegistry:
    def setup_method(self):
        self.registry = FieldGeneratorRegistry()

    def test_string_type(self):
        assert isinstance(self.registry.generate_field({"type": "string"}), str)

    def test_integer_type(self):
        assert isinstance(self.registry.generate_field({"type": "integer"}), int)

    def test_number_type(self):
        assert isinstance(self.registry.generate_field({"type": "number"}), float)

    def test_boolean_type(self):
        assert isinstance(self.registry.generate_field({"type": "boolean"}), bool)

    def test_uuid_format(self):
        import uuid
        val = self.registry.generate_field({"type": "string", "format": "uuid"})
        uuid.UUID(val)

    def test_email_format(self):
        val = self.registry.generate_field({"type": "string", "format": "email"})
        assert "@" in val

    def test_enum_field(self):
        val = self.registry.generate_field({"enum": ["x", "y"]})
        assert val in ["x", "y"]

    def test_pattern_field(self):
        val = self.registry.generate_field({"type": "string", "pattern": r"\d{3}"})
        assert isinstance(val, str)

    def test_faker_field(self):
        val = self.registry.generate_field({"type": "string", "faker": "first_name"})
        assert isinstance(val, str)

    def test_array_field(self):
        val = self.registry.generate_field({"type": "array", "items": {"type": "integer"}})
        assert isinstance(val, list)

    def test_object_field(self):
        val = self.registry.generate_field({
            "type": "object",
            "properties": {"a": {"type": "string"}},
            "required": ["a"],
        })
        assert isinstance(val, dict)
        assert "a" in val

    def test_union_type_skips_null(self):
        val = self.registry.generate_field({"type": ["null", "string"]})
        assert isinstance(val, str)

    def test_unsupported_type_raises(self):
        with pytest.raises(UnsupportedFieldTypeError):
            self.registry.generate_field({"type": "unsupported_xyz"})

    def test_date_format(self):
        from datetime import date
        val = self.registry.generate_field({"type": "string", "format": "date"})
        date.fromisoformat(val)

    def test_datetime_format(self):
        from datetime import datetime
        val = self.registry.generate_field({"type": "string", "format": "date-time"})
        datetime.fromisoformat(val)
