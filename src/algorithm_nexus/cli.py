# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Command-line interface for Algorithm Nexus package validation."""

from __future__ import annotations

import sys

try:
    import typer
except ImportError:
    print(
        "Error: CLI dependencies are not installed.\n"
        "Please install them with: pip install algorithm-nexus[cli]",
        file=sys.stderr,
    )
    sys.exit(1)

from algorithm_nexus.commands.list import (
    list_benchmark_experiments,
    list_experiment_packages,
    list_packages,
)
from algorithm_nexus.commands.run import run_benchmarks
from algorithm_nexus.commands.validate import (
    validate_experiments,
    validate_logical_benchmarks,
    validate_package,
)

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

# Create subcommand group for 'run'
run_app = typer.Typer(
    help="Execute benchmarks and operations.",
    no_args_is_help=True,
)
app.add_typer(run_app, name="run")

# Create subcommand group for 'validate'
validate_app = typer.Typer(
    help="Validate various aspects of Nexus packages.",
    no_args_is_help=True,
)
app.add_typer(validate_app, name="validate")


# Register list commands
list_app.command(name="packages")(list_packages)
list_app.command(name="experiment-packages")(list_experiment_packages)
list_app.command(name="experiments")(list_benchmark_experiments)

# Register run commands
run_app.command(name="benchmarks")(run_benchmarks)

# Register validate commands
validate_app.command(name="package")(validate_package)
validate_app.command(name="experiments")(validate_experiments)
validate_app.command(name="logical-benchmarks")(validate_logical_benchmarks)


def main() -> None:
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    main()

# Made with Bob
