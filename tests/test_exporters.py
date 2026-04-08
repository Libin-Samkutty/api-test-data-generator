"""Tests for JSON, CSV, and NDJSON exporters."""
import csv
import json
import sys
import pytest
from pathlib import Path
from unittest.mock import patch

from api_test_data_generator.exporters.json_exporter import export_json
from api_test_data_generator.exporters.csv_exporter import export_csv, _flatten
from api_test_data_generator.exporters.ndjson_exporter import export_ndjson
from api_test_data_generator.generator.exceptions import ExportError


SAMPLE_RECORDS = [
    {"id": "abc-123", "name": "Alice", "age": 30},
    {"id": "def-456", "name": "Bob", "age": 25},
]

NESTED_RECORDS = [
    {"id": "1", "address": {"city": "Nairobi", "country": "Kenya"}},
    {"id": "2", "address": {"city": "Lagos", "country": "Nigeria"}},
]


class TestJsonExporter:
    def test_creates_file(self, tmp_path):
        out = tmp_path / "output.json"
        export_json(SAMPLE_RECORDS, out)
        assert out.exists()

    def test_valid_json_output(self, tmp_path):
        out = tmp_path / "output.json"
        export_json(SAMPLE_RECORDS, out)
        with out.open() as f:
            data = json.load(f)
        assert data == SAMPLE_RECORDS

    def test_creates_parent_dirs(self, tmp_path):
        out = tmp_path / "subdir" / "deep" / "output.json"
        export_json(SAMPLE_RECORDS, out)
        assert out.exists()

    def test_returns_path(self, tmp_path):
        out = tmp_path / "output.json"
        result = export_json(SAMPLE_RECORDS, out)
        assert isinstance(result, Path)
        assert result == out

    def test_empty_list(self, tmp_path):
        out = tmp_path / "empty.json"
        export_json([], out)
        with out.open() as f:
            data = json.load(f)
        assert data == []

    def test_datetime_objects_serialised(self, tmp_path):
        from datetime import datetime
        out = tmp_path / "dates.json"
        records = [{"ts": datetime(2024, 1, 1, 12, 0, 0)}]
        export_json(records, out)
        data = json.load(out.open())
        assert isinstance(data[0]["ts"], str)


class TestCsvExporter:
    def test_creates_file(self, tmp_path):
        out = tmp_path / "output.csv"
        export_csv(SAMPLE_RECORDS, out)
        assert out.exists()

    def test_correct_row_count(self, tmp_path):
        out = tmp_path / "output.csv"
        export_csv(SAMPLE_RECORDS, out)
        with out.open(newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 2

    def test_column_headers(self, tmp_path):
        out = tmp_path / "output.csv"
        export_csv(SAMPLE_RECORDS, out)
        with out.open(newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
        assert "id" in fieldnames
        assert "name" in fieldnames
        assert "age" in fieldnames

    def test_nested_records_flattened(self, tmp_path):
        out = tmp_path / "nested.csv"
        export_csv(NESTED_RECORDS, out)
        with out.open(newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
        assert "address.city" in fieldnames or "address" in fieldnames

    def test_empty_records_raises(self, tmp_path):
        out = tmp_path / "empty.csv"
        with pytest.raises(ExportError):
            export_csv([], out)

    def test_returns_path(self, tmp_path):
        out = tmp_path / "output.csv"
        result = export_csv(SAMPLE_RECORDS, out)
        assert isinstance(result, Path)


    def test_stdlib_column_alignment_with_optional_fields(self, tmp_path):
        """Record[0] lacks 'notes' — stdlib path must still include it as a column."""
        records = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob", "notes": "VIP"},
            {"id": 3, "name": "Carol", "notes": "new"},
        ]
        out = tmp_path / "out.csv"
        with patch.dict(sys.modules, {"pandas": None}):
            export_csv(records, out)
        with out.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            rows = list(reader)
        assert "notes" in fieldnames
        assert rows[0]["notes"] == ""
        assert rows[1]["notes"] == "VIP"

    def test_stdlib_all_records_have_same_column_count(self, tmp_path):
        """Every CSV row must have the same number of cells."""
        records = [
            {"id": 1},
            {"id": 2, "extra": "x"},
            {"id": 3, "extra": "y", "more": "z"},
        ]
        out = tmp_path / "out.csv"
        with patch.dict(sys.modules, {"pandas": None}):
            export_csv(records, out)
        lines = out.read_text(encoding="utf-8").splitlines()
        col_counts = [len(line.split(",")) for line in lines if line]
        assert len(set(col_counts)) == 1, f"Rows have different column counts: {col_counts}"


class TestNdjsonExporter:
    _SAMPLE = [
        {"id": 1, "name": "Alice", "active": True},
        {"id": 2, "name": "Bob", "active": False},
        {"id": 3, "name": "Carol", "active": True},
    ]

    def test_creates_file(self, tmp_path):
        out = tmp_path / "out.ndjson"
        export_ndjson(self._SAMPLE, out)
        assert out.exists()

    def test_correct_line_count(self, tmp_path):
        out = tmp_path / "out.ndjson"
        export_ndjson(self._SAMPLE, out)
        lines = [ln for ln in out.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert len(lines) == len(self._SAMPLE)

    def test_each_line_is_valid_json(self, tmp_path):
        out = tmp_path / "out.ndjson"
        export_ndjson(self._SAMPLE, out)
        for line in out.read_text(encoding="utf-8").splitlines():
            if line.strip():
                assert isinstance(json.loads(line), dict)

    def test_record_contents_preserved(self, tmp_path):
        out = tmp_path / "out.ndjson"
        export_ndjson(self._SAMPLE, out)
        parsed = [
            json.loads(ln)
            for ln in out.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
        assert parsed == self._SAMPLE

    def test_empty_list_creates_empty_file(self, tmp_path):
        out = tmp_path / "empty.ndjson"
        export_ndjson([], out)
        assert out.exists()
        assert out.read_text(encoding="utf-8").strip() == ""

    def test_returns_path_object(self, tmp_path):
        out = tmp_path / "out.ndjson"
        result = export_ndjson(self._SAMPLE, out)
        assert isinstance(result, Path)
        assert result == out

    def test_export_error_on_os_error(self, tmp_path):
        out = tmp_path / "out.ndjson"
        with patch("pathlib.Path.open", side_effect=OSError("disk full")):
            with pytest.raises(ExportError, match="disk full"):
                export_ndjson(self._SAMPLE, out)

    def test_creates_parent_dirs(self, tmp_path):
        out = tmp_path / "nested" / "sub" / "out.ndjson"
        export_ndjson(self._SAMPLE, out)
        assert out.exists()

    def test_accepts_string_path(self, tmp_path):
        out = str(tmp_path / "out.ndjson")
        result = export_ndjson(self._SAMPLE, out)
        assert Path(result).exists()

    def test_non_ascii_characters_preserved(self, tmp_path):
        records = [{"name": "José", "city": "München"}]
        out = tmp_path / "unicode.ndjson"
        export_ndjson(records, out)
        parsed = json.loads(out.read_text(encoding="utf-8").strip())
        assert parsed["name"] == "José"
        assert parsed["city"] == "München"


class TestFlattenHelper:
    def test_flat_dict_unchanged(self):
        record = {"a": 1, "b": "hello"}
        assert _flatten(record) == record

    def test_nested_dict_flattened(self):
        record = {"a": {"b": {"c": 42}}}
        flat = _flatten(record)
        assert flat == {"a.b.c": 42}

    def test_list_values_serialised(self):
        record = {"tags": ["x", "y"]}
        flat = _flatten(record)
        assert "tags" in flat
        assert isinstance(flat["tags"], str)
