"""Core DataGenerator engine."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from api_test_data_generator.generator.schema_loader import load_schema, load_schema_from_dict
from api_test_data_generator.generator.field_types import FieldGeneratorRegistry
from api_test_data_generator.generator.validators import validate_record, validate_bulk
from api_test_data_generator.generator.exceptions import ValidationError
from api_test_data_generator.utils.seed_manager import set_seed
from api_test_data_generator.utils.randomizer import reset_faker

logger = logging.getLogger(__name__)


class DataGenerator:
    """
    Main engine for generating schema-driven test data.

    Usage::

        gen = DataGenerator.from_file("user_schema.json", seed=42)
        record = gen.generate_record()
        records = gen.generate_bulk(1000)
    """

    def __init__(
        self,
        schema: dict[str, Any],
        seed: int | None = None,
        validate: bool = True,
    ) -> None:
        self._schema = load_schema_from_dict(schema)
        self._validate = validate
        self._registry = FieldGeneratorRegistry()

        if seed is not None:
            set_seed(seed)
            reset_faker()  # ensure Faker picks up new seed
            logger.debug(f"DataGenerator initialised with seed={seed}")

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_file(
        cls,
        path: str | Path,
        seed: int | None = None,
        validate: bool = True,
    ) -> "DataGenerator":
        schema = load_schema(path)
        return cls(schema=schema, seed=seed, validate=validate)

    @classmethod
    def from_dict(
        cls,
        schema: dict[str, Any],
        seed: int | None = None,
        validate: bool = True,
    ) -> "DataGenerator":
        return cls(schema=schema, seed=seed, validate=validate)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_record(self) -> dict[str, Any]:
        """Generate a single record conforming to the schema."""
        record = self._generate_object(self._schema)
        if self._validate:
            try:
                validate_record(record, self._schema)
            except ValidationError:
                logger.warning("Generated record failed validation — retrying once.")
                record = self._generate_object(self._schema)
                validate_record(record, self._schema)
        logger.debug("Record generated successfully.")
        return record

    def generate_bulk(self, count: int) -> list[dict[str, Any]]:
        """Generate *count* records."""
        if count < 1:
            raise ValueError(f"count must be >= 1, got {count}")
        records = [self._generate_object(self._schema) for _ in range(count)]
        if self._validate:
            validate_bulk(records, self._schema)
        logger.info(f"Bulk generation complete: {count} records.")
        return records

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _generate_object(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Generate a top-level or nested object from its schema."""
        properties: dict[str, Any] = schema.get("properties", {})
        required: list[str] = schema.get("required", [])
        record: dict[str, Any] = {}

        for field_name, field_schema in properties.items():
            # Always include required fields; include optional ones ~80% of the time
            import random
            if field_name in required or random.random() > 0.2:
                logger.debug(f"Generating field '{field_name}'")
                record[field_name] = self._registry.generate_field(field_schema)

        return record
