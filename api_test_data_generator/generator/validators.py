"""JSON Schema validation for generated records."""
from __future__ import annotations

import logging
from typing import Any

import jsonschema

from api_test_data_generator.generator.exceptions import ValidationError

logger = logging.getLogger(__name__)


def validate_record(record: dict[str, Any], schema: dict[str, Any]) -> None:
    """Validate a record against a JSON Schema. Raises ValidationError on failure."""
    try:
        jsonschema.validate(instance=record, schema=schema)
    except jsonschema.ValidationError as exc:
        logger.error(f"Validation failed: {exc.message}")
        raise ValidationError(f"Record failed schema validation: {exc.message}") from exc
    except jsonschema.SchemaError as exc:
        logger.error(f"Invalid schema: {exc.message}")
        raise ValidationError(f"Schema itself is invalid: {exc.message}") from exc


def validate_bulk(records: list[dict[str, Any]], schema: dict[str, Any]) -> None:
    """Validate a list of records. Raises ValidationError on the first failure."""
    for i, record in enumerate(records):
        try:
            validate_record(record, schema)
        except ValidationError as exc:
            raise ValidationError(f"Record {i} failed validation: {exc}") from exc
