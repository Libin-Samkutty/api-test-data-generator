"""CSV exporter — uses pandas when available, falls back to csv stdlib."""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any

from api_test_data_generator.generator.exceptions import ExportError

logger = logging.getLogger(__name__)


def _flatten(record: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Recursively flatten a nested dict with dot-notation keys."""
    flat: dict[str, Any] = {}
    for key, value in record.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(_flatten(value, full_key))
        elif isinstance(value, list):
            flat[full_key] = json_safe_list(value)
        else:
            flat[full_key] = value
    return flat


def json_safe_list(value: list[Any]) -> str:
    import json
    return json.dumps(value, default=str)


def export_csv(
    records: list[dict[str, Any]],
    output_path: str | Path,
) -> Path:
    """Write records as a CSV file to *output_path*."""
    path = Path(output_path)
    if not records:
        raise ExportError("Cannot export an empty record list to CSV.")

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        flat_records = [_flatten(r) for r in records]

        # Attempt pandas first for performance
        try:
            import pandas as pd  # type: ignore
            df = pd.DataFrame(flat_records)
            df.to_csv(path, index=False)
            logger.info(f"Exported {len(records)} records to {path} (CSV via pandas)")
            return path
        except ImportError:
            pass

        # stdlib fallback — union of all keys to handle optional fields correctly
        seen: dict[str, None] = {}
        for rec in flat_records:
            seen.update(dict.fromkeys(rec.keys()))
        fieldnames = list(seen)
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(flat_records)
        logger.info(f"Exported {len(records)} records to {path} (CSV via stdlib)")
        return path
    except OSError as exc:
        raise ExportError(f"Failed to write CSV to '{path}': {exc}") from exc
