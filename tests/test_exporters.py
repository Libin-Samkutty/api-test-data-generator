"""Tests for JSON and CSV exporters."""
import json
import csv
import pytest
from pathlib import Path

from api_test_data_generator.exporters.json_exporter import export_json
from api_test_data_generator.exporters.csv_exporter import export_csv, _flatten
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
