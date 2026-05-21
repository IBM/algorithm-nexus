# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Command-line interface for Algorithm Nexus package validation."""

from __future__ import annotations

import sys

try:
    import typer
    from rich.console import Console
except ImportError:
    print(
        "Error: CLI dependencies are not installed.\n"
        "Please install them with: pip install algorithm-nexus[cli]",
        file=sys.stderr,
    )
    sys.exit(1)

from algorithm_nexus.commands.get import get_benchmark_requirements
from algorithm_nexus.commands.list import (
    list_benchmark_experiments,
    list_benchmark_packages,
    list_packages,
)
from algorithm_nexus.commands.validate import validate

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

# Create subcommand group for 'get'
get_app = typer.Typer(
    help="Get specific information about Nexus packages.",
    no_args_is_help=True,
)
app.add_typer(get_app, name="get")


@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context) -> None:
    pass


# Register validate command
app.command(name="validate")(validate)

# Register list commands
list_app.command(name="packages")(list_packages)
list_app.command(name="benchmark-packages")(list_benchmark_packages)
list_app.command(name="benchmark-experiments")(list_benchmark_experiments)

# Register get commands
get_app.command(name="benchmark-requirements")(get_benchmark_requirements)


def main() -> None:
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    main()

# Made with Bob
