"""CLI entry point for api-test-data-generator."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

import typer

from api_test_data_generator.generator.core import DataGenerator
from api_test_data_generator.exporters.json_exporter import export_json
from api_test_data_generator.exporters.csv_exporter import export_csv
from api_test_data_generator.exporters.ndjson_exporter import export_ndjson
from api_test_data_generator.generator.exceptions import (
    SchemaLoadError,
    ValidationError,
    ExportError,
)

app = typer.Typer(
    name="api-gen",
    help="Generate structured test data for API testing.",
    add_completion=False,
)

_FORMAT_CHOICES = ["json", "csv", "ndjson"]


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        format="%(levelname)s | %(name)s | %(message)s",
        level=level,
    )


@app.command("generate")
def generate(
    schema: Path = typer.Option(
        ...,
        "--schema",
        "-s",
        help="Path to JSON or YAML schema file.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    count: int = typer.Option(
        1,
        "--count",
        "-n",
        min=1,
        help="Number of records to generate.",
    ),
    output: str = typer.Option(
        ...,
        "--output",
        "-o",
        help="Output file path, or '-' to write to stdout.",
    ),
    fmt: str = typer.Option(
        "json",
        "--format",
        "-f",
        help="Output format: json, csv, or ndjson.",
    ),
    seed: Optional[int] = typer.Option(
        None,
        "--seed",
        help="Random seed for deterministic output.",
    ),
    validate: bool = typer.Option(
        True,
        "--validate/--no-validate",
        help="Validate generated records against the schema.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose/debug logging.",
    ),
) -> None:
    """Generate test data records from a schema file."""
    _setup_logging(verbose)

    if fmt not in _FORMAT_CHOICES:
        typer.echo(f"[ERROR] Unsupported format '{fmt}'. Choose from: {_FORMAT_CHOICES}", err=True)
        raise typer.Exit(code=1)

    write_to_stdout = output == "-"
    if not write_to_stdout:
        output_path = Path(output)

    if write_to_stdout and fmt == "csv":
        typer.echo(
            "[ERROR] CSV format does not support stdout output. Use --output <file> for CSV.",
            err=True,
        )
        raise typer.Exit(code=1)

    try:
        generator = DataGenerator.from_file(schema, seed=seed, validate=validate)

        if count == 1:
            records = [generator.generate_record()]
        else:
            records = generator.generate_bulk(count)

        if write_to_stdout:
            if fmt == "ndjson":
                for record in records:
                    typer.echo(json.dumps(record, default=str, ensure_ascii=False))
            else:
                typer.echo(json.dumps(records, indent=2, default=str, ensure_ascii=False))
        else:
            if fmt == "csv":
                export_csv(records, output_path)
            elif fmt == "ndjson":
                export_ndjson(records, output_path)
            else:
                export_json(records, output_path)
            _print_success(count, output_path, fmt)

    except SchemaLoadError as exc:
        typer.echo(f"[ERROR] Schema error: {exc}", err=True)
        raise typer.Exit(code=2)
    except ValidationError as exc:
        typer.echo(f"[ERROR] Validation error: {exc}", err=True)
        raise typer.Exit(code=3)
    except ExportError as exc:
        typer.echo(f"[ERROR] Export error: {exc}", err=True)
        raise typer.Exit(code=4)
    except Exception as exc:
        typer.echo(f"[ERROR] Unexpected error: {exc}", err=True)
        raise typer.Exit(code=99)


@app.command("preview")
def preview(
    schema: Path = typer.Option(
        ...,
        "--schema",
        "-s",
        help="Path to JSON or YAML schema file.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    count: int = typer.Option(
        3,
        "--count",
        "-n",
        min=1,
        max=10,
        help="Number of records to preview (1-10).",
    ),
    seed: Optional[int] = typer.Option(
        None,
        "--seed",
        help="Random seed for deterministic preview.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose/debug logging.",
    ),
) -> None:
    """Preview generated records in the terminal without saving a file."""
    _setup_logging(verbose)

    try:
        generator = DataGenerator.from_file(schema, seed=seed, validate=False)
        records = generator.generate_bulk(count)

        try:
            from rich.console import Console
            from rich import print_json as rich_print_json

            console = Console()
            console.print(
                f"[bold cyan]Preview[/bold cyan] — {count} record(s) "
                f"from [dim]{schema}[/dim]\n"
            )
            for i, record in enumerate(records, 1):
                console.print(f"[bold]Record {i}[/bold]")
                rich_print_json(json.dumps(record, default=str, ensure_ascii=False))
                console.print()
        except ImportError:
            typer.echo(f"# Preview — {count} record(s)\n")
            typer.echo(json.dumps(records, indent=2, default=str, ensure_ascii=False))

    except SchemaLoadError as exc:
        typer.echo(f"[ERROR] Schema error: {exc}", err=True)
        raise typer.Exit(code=2)
    except Exception as exc:
        typer.echo(f"[ERROR] Unexpected error: {exc}", err=True)
        raise typer.Exit(code=99)


def _print_success(count: int, output: Path, fmt: str) -> None:
    """Print a rich-formatted or plain success message."""
    try:
        from rich.console import Console
        from rich.panel import Panel

        console = Console()
        console.print(
            Panel(
                f"[green]✓[/green] Generated [bold]{count}[/bold] record(s)\n"
                f"  Format : [cyan]{fmt.upper()}[/cyan]\n"
                f"  Output : [cyan]{output}[/cyan]",
                title="api-gen",
                expand=False,
            )
        )
    except ImportError:
        typer.echo(f"✓ Generated {count} record(s) → {output} ({fmt.upper()})")


@app.callback(invoke_without_command=True)
def _root_callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
