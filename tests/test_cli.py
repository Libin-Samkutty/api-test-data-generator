"""Integration tests for the CLI using typer's test client."""
import csv
import json
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch
from typer.testing import CliRunner

from api_test_data_generator.cli.main import app

runner = CliRunner()


@pytest.fixture
def schema_path(tmp_path, simple_schema) -> Path:
    p = tmp_path / "schema.json"
    p.write_text(json.dumps(simple_schema))
    return p


class TestGenerateCommand:
    def test_basic_generation(self, schema_path, tmp_path):
        out = tmp_path / "out.json"
        result = runner.invoke(app, [
            "generate",
            "--schema", str(schema_path),
            "--output", str(out),
            "--count", "5",
            "--seed", "42",
        ])
        assert result.exit_code == 0
        assert out.exists()
        data = json.loads(out.read_text())
        assert len(data) == 5

    def test_default_count_is_one(self, schema_path, tmp_path):
        out = tmp_path / "out.json"
        result = runner.invoke(app, [
            "generate",
            "--schema", str(schema_path),
            "--output", str(out),
        ])
        assert result.exit_code == 0
        data = json.loads(out.read_text())
        assert len(data) == 1

    def test_csv_format(self, schema_path, tmp_path):
        out = tmp_path / "out.csv"
        result = runner.invoke(app, [
            "generate",
            "--schema", str(schema_path),
            "--output", str(out),
            "--count", "3",
            "--format", "csv",
        ])
        assert result.exit_code == 0
        assert out.exists()
        with out.open(newline="") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 3

    def test_invalid_format_exits_with_error(self, schema_path, tmp_path):
        out = tmp_path / "out.xml"
        result = runner.invoke(app, [
            "generate",
            "--schema", str(schema_path),
            "--output", str(out),
            "--format", "xml",
        ])
        assert result.exit_code != 0

    def test_missing_schema_exits_with_error(self, tmp_path):
        out = tmp_path / "out.json"
        result = runner.invoke(app, [
            "generate",
            "--schema", str(tmp_path / "nonexistent.json"),
            "--output", str(out),
        ])
        assert result.exit_code != 0

    def test_seed_determinism(self, schema_path, tmp_path):
        from api_test_data_generator.utils.randomizer import reset_faker
        out1 = tmp_path / "out1.json"
        reset_faker()
        runner.invoke(app, [
            "generate", "--schema", str(schema_path),
            "--output", str(out1), "--count", "5", "--seed", "7",
        ])

        out2 = tmp_path / "out2.json"
        reset_faker()
        runner.invoke(app, [
            "generate", "--schema", str(schema_path),
            "--output", str(out2), "--count", "5", "--seed", "7",
        ])

        assert json.loads(out1.read_text()) == json.loads(out2.read_text())

    def test_verbose_flag_accepted(self, schema_path, tmp_path):
        out = tmp_path / "out.json"
        result = runner.invoke(app, [
            "generate", "--schema", str(schema_path),
            "--output", str(out), "--verbose",
        ])
        assert result.exit_code == 0

    def test_no_validate_flag(self, schema_path, tmp_path):
        out = tmp_path / "out.json"
        result = runner.invoke(app, [
            "generate", "--schema", str(schema_path),
            "--output", str(out), "--no-validate",
        ])
        assert result.exit_code == 0

    def test_ndjson_format(self, schema_path, tmp_path):
        out = tmp_path / "out.ndjson"
        result = runner.invoke(app, [
            "generate", "--schema", str(schema_path),
            "--count", "3", "--output", str(out), "--format", "ndjson",
        ])
        assert result.exit_code == 0, result.output
        assert out.exists()
        lines = [ln for ln in out.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert len(lines) == 3
        for line in lines:
            assert isinstance(json.loads(line), dict)

    def test_stdout_json_output(self, schema_path):
        result = runner.invoke(app, [
            "generate", "--schema", str(schema_path),
            "--count", "2", "--output", "-", "--format", "json",
        ])
        assert result.exit_code == 0, result.output
        parsed = json.loads(result.output)
        assert isinstance(parsed, list)
        assert len(parsed) == 2

    def test_stdout_ndjson_output(self, schema_path):
        result = runner.invoke(app, [
            "generate", "--schema", str(schema_path),
            "--count", "2", "--output", "-", "--format", "ndjson",
        ])
        assert result.exit_code == 0, result.output
        lines = [ln for ln in result.output.splitlines() if ln.strip()]
        assert len(lines) == 2
        for line in lines:
            assert isinstance(json.loads(line), dict)

    def test_stdout_csv_rejected(self, schema_path):
        result = runner.invoke(app, [
            "generate", "--schema", str(schema_path),
            "--output", "-", "--format", "csv",
        ])
        assert result.exit_code == 1

    def test_stdout_does_not_create_file(self, schema_path, tmp_path):
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            runner.invoke(app, [
                "generate", "--schema", str(schema_path),
                "--output", "-", "--format", "json",
            ])
        finally:
            os.chdir(old_cwd)
        assert not (tmp_path / "-").exists()


class TestPreviewCommand:
    @pytest.fixture()
    def schema_path(self, tmp_path):
        """Minimal valid schema for preview tests."""
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string", "format": "uuid"},
                "email": {"type": "string", "format": "email"},
            },
            "required": ["id", "email"],
        }
        p = tmp_path / "schema.json"
        p.write_text(json.dumps(schema), encoding="utf-8")
        return p

    def test_preview_basic(self, schema_path):
        """Happy-path: exit 0, non-empty output."""
        result = runner.invoke(app, ["preview", "--schema", str(schema_path)])
        assert result.exit_code == 0, result.output
        assert result.output.strip()

    def test_preview_default_count_is_three(self, schema_path):
        """Default count=3 must produce 3 records without --count flag."""
        rich_mocks = {k: None for k in list(sys.modules) if k == "rich" or k.startswith("rich.")}
        with patch.dict(sys.modules, rich_mocks):
            result = runner.invoke(app, [
                "preview", "--schema", str(schema_path), "--seed", "1",
            ])
        assert result.exit_code == 0
        # Plain fallback: "# Preview — 3 record(s)\n\n<json>\n"
        lines = result.output.split("\n", 1)
        parsed = json.loads(lines[1])
        assert isinstance(parsed, list)
        assert len(parsed) == 3

    def test_preview_count_respected(self, schema_path):
        """--count 5 should produce 5 records."""
        rich_mocks = {k: None for k in list(sys.modules) if k == "rich" or k.startswith("rich.")}
        with patch.dict(sys.modules, rich_mocks):
            result = runner.invoke(app, [
                "preview", "--schema", str(schema_path),
                "--count", "5", "--seed", "42",
            ])
        assert result.exit_code == 0
        lines = result.output.split("\n", 1)
        parsed = json.loads(lines[1])
        assert len(parsed) == 5

    def test_preview_count_max_allowed(self, schema_path):
        """--count 10 is the maximum, must succeed."""
        result = runner.invoke(app, [
            "preview", "--schema", str(schema_path), "--count", "10",
        ])
        assert result.exit_code == 0

    def test_preview_count_exceeds_max_rejected(self, schema_path):
        """--count 11 exceeds max=10; Typer must reject it."""
        result = runner.invoke(app, [
            "preview", "--schema", str(schema_path), "--count", "11",
        ])
        assert result.exit_code != 0

    def test_preview_invalid_schema_exits_2(self, tmp_path):
        """Non-existent schema path must exit with code 2."""
        result = runner.invoke(app, [
            "preview", "--schema", str(tmp_path / "missing.json"),
        ])
        assert result.exit_code == 2

    def test_preview_deterministic_with_seed(self, schema_path):
        """Same seed must produce identical output on two calls."""
        from api_test_data_generator.utils.randomizer import reset_faker
        reset_faker()
        r1 = runner.invoke(app, ["preview", "--schema", str(schema_path), "--seed", "99"])
        reset_faker()
        r2 = runner.invoke(app, ["preview", "--schema", str(schema_path), "--seed", "99"])
        assert r1.exit_code == 0
        assert r1.output == r2.output

    def test_preview_no_file_created(self, schema_path, tmp_path):
        """preview must never write a file to disk."""
        before = set(tmp_path.iterdir())
        runner.invoke(app, ["preview", "--schema", str(schema_path)])
        after = set(tmp_path.iterdir())
        new_files = after - before
        assert not new_files, f"Unexpected files created: {new_files}"

    def test_preview_fallback_without_rich(self, schema_path):
        """When rich is absent, plain JSON fallback must still work."""
        rich_mocks = {k: None for k in list(sys.modules) if k == "rich" or k.startswith("rich.")}
        with patch.dict(sys.modules, rich_mocks):
            result = runner.invoke(app, [
                "preview", "--schema", str(schema_path), "--count", "2",
            ])
        assert result.exit_code == 0
        assert result.output.strip()

    def test_preview_output_contains_required_fields(self, schema_path):
        """Output must include schema-required field keys."""
        result = runner.invoke(app, [
            "preview", "--schema", str(schema_path), "--count", "1", "--seed", "7",
        ])
        assert result.exit_code == 0
        assert "id" in result.output
        assert "email" in result.output
