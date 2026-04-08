"""Field type handlers using the Strategy pattern."""
from __future__ import annotations

import random
import logging
from abc import ABC, abstractmethod
from typing import Any

from api_test_data_generator.utils.randomizer import get_faker, random_string, random_from_regex
from api_test_data_generator.generator.exceptions import UnsupportedFieldTypeError

logger = logging.getLogger(__name__)


class BaseFieldGenerator(ABC):
    """Abstract base for all field generators."""

    @abstractmethod
    def generate(self, config: dict[str, Any]) -> Any:
        """Generate a value from the given field config."""


class StringGenerator(BaseFieldGenerator):
    """Generates plain string values, with optional minLength/maxLength."""

    def generate(self, config: dict[str, Any]) -> Any:
        min_len = config.get("minLength", 5)
        max_len = config.get("maxLength", 20)
        return random_string(min_len, max_len)


class IntegerGenerator(BaseFieldGenerator):
    def generate(self, config: dict[str, Any]) -> Any:
        minimum = config.get("minimum", 0)
        maximum = config.get("maximum", 1_000_000)
        return random.randint(int(minimum), int(maximum))


class FloatGenerator(BaseFieldGenerator):
    def generate(self, config: dict[str, Any]) -> Any:
        minimum = config.get("minimum", 0.0)
        maximum = config.get("maximum", 1_000_000.0)
        precision = config.get("precision", 2)
        value = random.uniform(float(minimum), float(maximum))
        return round(value, precision)


class BooleanGenerator(BaseFieldGenerator):
    def generate(self, config: dict[str, Any]) -> Any:
        return random.choice([True, False])


class UUIDGenerator(BaseFieldGenerator):
    def generate(self, config: dict[str, Any]) -> Any:
        return str(get_faker().uuid4())


class EmailGenerator(BaseFieldGenerator):
    def generate(self, config: dict[str, Any]) -> Any:
        return get_faker().email()


class PhoneGenerator(BaseFieldGenerator):
    def generate(self, config: dict[str, Any]) -> Any:
        return get_faker().phone_number()


class AddressGenerator(BaseFieldGenerator):
    def generate(self, config: dict[str, Any]) -> Any:
        faker = get_faker()
        return {
            "street": faker.street_address(),
            "city": faker.city(),
            "state": faker.state(),
            "country": faker.country(),
            "postal_code": faker.postcode(),
        }


class DateGenerator(BaseFieldGenerator):
    def generate(self, config: dict[str, Any]) -> Any:
        faker = get_faker()
        start_date = config.get("start_date", "-30y")
        end_date = config.get("end_date", "today")
        d = faker.date_between(start_date=start_date, end_date=end_date)
        return d.isoformat()


class DateTimeGenerator(BaseFieldGenerator):
    def generate(self, config: dict[str, Any]) -> Any:
        faker = get_faker()
        dt = faker.date_time_between(start_date="-30y", end_date="now")
        return dt.isoformat()


class EnumGenerator(BaseFieldGenerator):
    def generate(self, config: dict[str, Any]) -> Any:
        values = config.get("enum", [])
        if not values:
            raise UnsupportedFieldTypeError("Enum field must have at least one value in 'enum'.")
        return random.choice(values)


class ArrayGenerator(BaseFieldGenerator):
    def generate(self, config: dict[str, Any]) -> Any:
        from api_test_data_generator.generator.field_types import FieldGeneratorRegistry
        min_items = int(config.get("minItems", 1))
        max_items = int(config.get("maxItems", 5))
        if min_items > max_items:
            logger.warning(
                "ArrayGenerator: minItems (%d) > maxItems (%d); clamping maxItems to minItems.",
                min_items,
                max_items,
            )
            max_items = min_items
        count = random.randint(min_items, max_items)
        items_schema = config.get("items", {"type": "string"})
        registry = FieldGeneratorRegistry()
        return [registry.generate_field(items_schema) for _ in range(count)]


class ObjectGenerator(BaseFieldGenerator):
    def generate(self, config: dict[str, Any]) -> Any:
        from api_test_data_generator.generator.field_types import FieldGeneratorRegistry
        properties = config.get("properties", {})
        required = config.get("required", [])
        registry = FieldGeneratorRegistry()
        result: dict[str, Any] = {}
        for field_name, field_schema in properties.items():
            if field_name in required or random.random() > 0.2:
                logger.debug(f"Generating nested field: {field_name}")
                result[field_name] = registry.generate_field(field_schema)
        return result


class RegexGenerator(BaseFieldGenerator):
    def generate(self, config: dict[str, Any]) -> Any:
        pattern = config.get("pattern", r"\w+")
        return random_from_regex(pattern)


class FakerFieldGenerator(BaseFieldGenerator):
    """Delegates generation to a named Faker provider method."""

    def generate(self, config: dict[str, Any]) -> Any:
        faker_method = config.get("faker", "")
        faker = get_faker()
        method = getattr(faker, faker_method, None)
        if method is None:
            logger.warning(
                "Unknown Faker method %r — falling back to random string. "
                "Check the 'faker' key in your schema.",
                faker_method,
            )
            return StringGenerator().generate(config)
        return str(method())


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class FieldGeneratorRegistry:
    """Maps field configs to the appropriate generator and invokes it."""

    # Format-level overrides (JSON Schema `format` keyword)
    _FORMAT_MAP: dict[str, BaseFieldGenerator] = {
        "uuid": UUIDGenerator(),
        "email": EmailGenerator(),
        "date": DateGenerator(),
        "date-time": DateTimeGenerator(),
        "phone": PhoneGenerator(),
        "address": AddressGenerator(),
    }

    # Type-level defaults
    _TYPE_MAP: dict[str, BaseFieldGenerator] = {
        "string": StringGenerator(),
        "integer": IntegerGenerator(),
        "number": FloatGenerator(),
        "boolean": BooleanGenerator(),
        "array": ArrayGenerator(),
        "object": ObjectGenerator(),
    }

    def generate_field(self, config: dict[str, Any]) -> Any:
        # Enum shortcut
        if "enum" in config:
            return EnumGenerator().generate(config)

        # Regex shortcut
        if "pattern" in config:
            return RegexGenerator().generate(config)

        # Faker override
        if "faker" in config:
            return FakerFieldGenerator().generate(config)

        # Format override
        fmt = config.get("format")
        if fmt and fmt in self._FORMAT_MAP:
            return self._FORMAT_MAP[fmt].generate(config)

        # Type-based dispatch
        field_type = config.get("type", "string")
        if isinstance(field_type, list):
            # Union type — pick first non-null
            field_type = next((t for t in field_type if t != "null"), "string")

        generator = self._TYPE_MAP.get(field_type)
        if generator is None:
            raise UnsupportedFieldTypeError(
                f"No generator registered for type '{field_type}'. "
                f"Supported types: {list(self._TYPE_MAP.keys())}"
            )
        logger.debug(f"Generating field type='{field_type}' with config={config}")
        return generator.generate(config)
