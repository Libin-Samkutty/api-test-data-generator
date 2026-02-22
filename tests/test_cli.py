"""Integration tests for the CLI using typer's test client."""
import json
import csv
import pytest
from pathlib import Path
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
