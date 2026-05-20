# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Command-line interface for Algorithm Nexus package validation."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

try:
    import typer
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
except ImportError:
    print(
        "Error: CLI dependencies are not installed.\n"
        "Please install them with: pip install algorithm-nexus[cli]",
        file=sys.stderr,
    )
    sys.exit(1)

from algorithm_nexus.models import AlgorithmNexusPackageConfig
from algorithm_nexus.validation import (
    ValidationErrorCollector,
    load_yaml_file,
    validate_package_directory,
)

console = Console()

app = typer.Typer(
    help="Algorithm Nexus CLI - Tools for managing and validating Nexus packages.",
    add_completion=False,
    no_args_is_help=True,
)

# Create subcommand group for 'list'
list_app = typer.Typer(
    help="List various resources in Nexus packages.",
    no_args_is_help=True,
)
app.add_typer(list_app, name="list")


@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context) -> None:
    pass


def _print_experiments_table(pkg_name: str, experiments: list[tuple[str, str]]) -> None:
    """Print a table of experiments for a single package.

    Args:
        pkg_name: Name of the Nexus package
        experiments: List of (experiment_id, requirement_specifier) tuples
    """
    console.print(f"[bold]Nexus Package:[/bold] [cyan]{pkg_name}[/cyan]")
    table = Table(
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Experiment ID", style="white")
    table.add_column("Benchmark Package", style="yellow")

    for exp_id, requirement in experiments:
        table.add_row(exp_id, requirement)

    console.print(table)
    console.print()


@app.command(name="validate")
def validate(
    package_path: Annotated[
        Path,
        typer.Argument(
            help="Path to a Nexus package directory.",
            dir_okay=True,
            file_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ],
) -> None:
    """Validate Nexus package structure and YAML configuration files."""
    collector = ValidationErrorCollector()
    validate_package_directory(package_path, collector)

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


@list_app.command(name="experiments")
def list_experiments(
    packages_root: Annotated[
        Path,
        typer.Argument(
            help="Path to the packages root directory (default: ./packages).",
            dir_okay=True,
            file_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ] = Path("./packages"),
) -> None:
    """List all benchmark experiments discovered across all Nexus packages.

    Scans all packages in the packages directory and discovers experiments
    from model benchmark_instances directories by parsing space.yaml files.
    """
    if not packages_root.is_dir():
        console.print(f"[red]Error:[/red] {packages_root} is not a directory")
        raise typer.Exit(code=1)

    # Structure to hold discovered experiments grouped by package
    # package_name -> [(experiment_id, requirement_specifier), ...]
    experiments_by_package: dict[str, list[tuple[str, str]]] = {}
    total_experiments = 0

    # Scan all package directories
    for package_dir in packages_root.iterdir():
        if not package_dir.is_dir() or package_dir.name.startswith("."):
            continue

        # Load package name from nexus.yaml
        nexus_yaml_path = package_dir / "nexus.yaml"
        if not nexus_yaml_path.exists():
            continue

        collector = ValidationErrorCollector()
        nexus_data = load_yaml_file(nexus_yaml_path, collector)
        if nexus_data is None or collector.has_errors:
            continue

        try:
            package_config = AlgorithmNexusPackageConfig.model_validate(nexus_data)
            package_name = package_config.package.name

            # Extract experiments directly from nexus.yaml
            if package_config.package.benchmark_packages:
                package_experiments: list[tuple[str, str]] = []
                for bench_pkg in package_config.package.benchmark_packages:
                    for exp_id in bench_pkg.experiments:
                        package_experiments.append(
                            (exp_id, bench_pkg.requirement_specifier)
                        )
                        total_experiments += 1

                if package_experiments:
                    # Sort experiments by ID within each package
                    package_experiments.sort(key=lambda x: x[0])
                    experiments_by_package[package_name] = package_experiments
        except Exception:  # noqa: S112
            continue

    # Output results
    if not experiments_by_package:
        console.print(
            "\n[yellow]No benchmark experiments found in any packages[/yellow]\n"
        )
        return

    # Display a table for each package
    console.print("\n[bold]Discovered Benchmark Experiments[/bold]\n")

    for pkg_name in sorted(experiments_by_package.keys()):
        experiments = experiments_by_package[pkg_name]
        _print_experiments_table(pkg_name, experiments)

    console.print(
        f"[bold]Total:[/bold] {total_experiments} experiments across {len(experiments_by_package)} packages\n"
    )

    # Add instructions for getting more details
    console.print("[bold]For further details on each experiment:[/bold]")
    console.print("1. Install ado")
    console.print("   [cyan]uv pip install ado-core[/cyan]")
    console.print("2. Install the Benchmark package the experiment belongs to")
    console.print("   [cyan]uv pip install <benchmark_package>[/cyan]")
    console.print("3. Describe the experiment")
    console.print("   [cyan]ado describe experiment <experiment_id>[/cyan]\n")


def main() -> None:
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    main()
