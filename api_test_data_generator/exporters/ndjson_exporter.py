"""NDJSON (Newline-Delimited JSON) exporter."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from api_test_data_generator.generator.exceptions import ExportError

logger = logging.getLogger(__name__)


def export_ndjson(
    records: list[dict[str, Any]],
    output_path: str | Path,
) -> Path:
    """Write records as NDJSON to output_path (one JSON object per line)."""
    path = Path(output_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, default=str, ensure_ascii=False))
                f.write("\n")
        logger.info("Exported %d records to %s (NDJSON)", len(records), path)
        return path
    except OSError as exc:
        raise ExportError(f"Failed to write NDJSON to '{path}': {exc}") from exc
