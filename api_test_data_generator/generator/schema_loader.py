"""Schema loading from JSON and YAML files."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from api_test_data_generator.generator.exceptions import SchemaLoadError

logger = logging.getLogger(__name__)


def load_schema(path: str | Path) -> dict[str, Any]:
    """Load a JSON or YAML schema file and return it as a dict."""
    file_path = Path(path)
    if not file_path.exists():
        raise SchemaLoadError(f"Schema file not found: {file_path}")

    suffix = file_path.suffix.lower()
    try:
        if suffix in (".yaml", ".yml"):
            import yaml  # type: ignore
            with file_path.open("r", encoding="utf-8") as f:
                schema = yaml.safe_load(f)
        elif suffix == ".json":
            with file_path.open("r", encoding="utf-8") as f:
                schema = json.load(f)
        else:
            raise SchemaLoadError(
                f"Unsupported schema format '{suffix}'. Use .json, .yaml, or .yml."
            )
    except (json.JSONDecodeError, Exception) as exc:
        raise SchemaLoadError(f"Failed to parse schema '{file_path}': {exc}") from exc

    if not isinstance(schema, dict):
        raise SchemaLoadError(f"Schema must be a JSON/YAML object (dict), got {type(schema)}.")

    logger.info(f"Schema loaded from {file_path}")
    return schema


def load_schema_from_dict(schema: dict[str, Any]) -> dict[str, Any]:
    """Validate and return an inline schema dict."""
    if not isinstance(schema, dict):
        raise SchemaLoadError("Inline schema must be a dict.")
    return schema
