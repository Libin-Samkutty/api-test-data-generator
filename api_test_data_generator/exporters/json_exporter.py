"""JSON exporter."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from api_test_data_generator.generator.exceptions import ExportError

logger = logging.getLogger(__name__)


def export_json(
    records: list[dict[str, Any]],
    output_path: str | Path,
    indent: int = 2,
) -> Path:
    """Write records as a JSON array to *output_path*."""
    path = Path(output_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(records, f, indent=indent, default=str, ensure_ascii=False)
        logger.info(f"Exported {len(records)} records to {path} (JSON)")
        return path
    except OSError as exc:
        raise ExportError(f"Failed to write JSON to '{path}': {exc}") from exc
