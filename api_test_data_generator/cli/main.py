"""CLI entry point for api-test-data-generator."""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

import typer

from api_test_data_generator.generator.core import DataGenerator
from api_test_data_generator.exporters.json_exporter import export_json
from api_test_data_generator.exporters.csv_exporter import export_csv
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

_FORMAT_CHOICES = ["json", "csv"]


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
    output: Path = typer.Option(
        ...,
        "--output",
        "-o",
        help="Output file path.",
    ),
    fmt: str = typer.Option(
        "json",
        "--format",
        "-f",
        help="Output format: json or csv.",
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

    try:
        generator = DataGenerator.from_file(schema, seed=seed, validate=validate)

        if count == 1:
            records = [generator.generate_record()]
        else:
            records = generator.generate_bulk(count)

        if fmt == "csv":
            export_csv(records, output)
        else:
            export_json(records, output)

        _print_success(count, output, fmt)

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
