# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Command-line interface for Algorithm Nexus package validation."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import typer
    from rich.console import Console
    from rich.panel import Panel
except ImportError:
    print(
        "Error: CLI dependencies are not installed.\n"
        "Please install them with: pip install algorithm-nexus[cli]",
        file=sys.stderr,
    )
    sys.exit(1)

from algorithm_nexus.validation import (
    ValidationErrorCollector,
    validate_package_directory,
)

console = Console()

app = typer.Typer(
    help="Algorithm Nexus CLI - Tools for managing and validating Nexus packages.",
    add_completion=False,
)


@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context) -> None:
    """Algorithm Nexus CLI - Tools for managing and validating Nexus packages."""
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit()


@app.command(name="validate")
def validate(
    package_path: Path = typer.Argument(
        ...,
        help="Path to a Nexus package directory.",
    ),
) -> None:
    """Validate Nexus package structure and YAML configuration files."""
    collector = ValidationErrorCollector()

    resolved_path = package_path.resolve()

    if not resolved_path.exists():
        collector.add(f"Package path does not exist: {resolved_path}")
        console.print(
            Panel(
                str(collector),
                title="[bold red]Validation Failed[/bold red]",
                border_style="red",
            )
        )
        raise typer.Exit(code=1)

    validate_package_directory(resolved_path, collector)

    if collector.has_errors:
        console.print(
            Panel(
                collector.format_errors(),
                title="[bold red]Validation Failed[/bold red]",
                border_style="red",
            )
        )
        raise typer.Exit(code=1)

    # Build success message
    success_message = "[green]✓[/green] All validation checks passed"

    if collector.has_info:
        success_message += (
            "\n\n[bold]Optional files/directories:[/bold]\n" + collector.format_info()
        )

    console.print(
        Panel(
            success_message,
            title="[bold green]Validation Successful[/bold green]",
            border_style="green",
        )
    )


def main() -> None:
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    main()
