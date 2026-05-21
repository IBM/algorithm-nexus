# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Get commands for Algorithm Nexus CLI."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

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

from algorithm_nexus.commands.utils import (
    find_package_config,
    output_benchmark_requirements_table,
    output_requirements_txt,
    validate_txt_only_format,
)

console = Console()


def get_benchmark_requirements(
    nexus_package: Annotated[
        str,
        typer.Argument(
            help="Name of the Nexus package to get benchmark requirements for",
        ),
    ],
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
    output_format: Annotated[
        str | None,
        typer.Option(
            "-o",
            "--output-format",
            help="Output format: 'txt' (requirements file format). Default is table output.",
        ),
    ] = None,
    output_file: Annotated[
        Path | None,
        typer.Option(
            "--output-file",
            help="File path to write output to. Only used with -o txt.",
        ),
    ] = None,
) -> None:
    """Get the list of benchmark requirement specifiers for a specific Nexus package.

    This command retrieves all benchmark packages registered in the specified
    Nexus package's nexus.yaml file and displays their requirement specifiers.

    Use -o txt to output in requirements.txt format (one requirement per line),
    suitable for use with pip install -r.
    """
    validate_txt_only_format(output_format)

    if not packages_root.is_dir():
        console.print(f"[red]Error:[/red] {packages_root} is not a directory")
        raise typer.Exit(code=1)

    # Find and load the package configuration
    result = find_package_config(nexus_package, packages_root)
    if result is None:
        console.print(
            f"[red]Error:[/red] Nexus package '{nexus_package}' not found in {packages_root}"
        )
        raise typer.Exit(code=1)

    package_dir, package_config = result

    # Check if package has benchmark packages
    if not package_config.package.benchmark_packages:
        console.print(
            f"\n[yellow]No benchmark packages found for Nexus package '{nexus_package}'[/yellow]\n"
        )
        return

    # Handle txt format (requirements.txt style)
    if output_format == "txt":
        requirements = [
            bench_pkg.requirement_specifier
            for bench_pkg in package_config.package.benchmark_packages
        ]
        output_requirements_txt(requirements, output_file)
        return

    # Handle table output (default) and other formats
    output_benchmark_requirements_table(
        package_config.package.benchmark_packages,
        nexus_package,
        output_format,
        output_file,
    )

    if not output_format:
        console.print(
            f"\n[bold]Total:[/bold] {len(package_config.package.benchmark_packages)} benchmark requirement(s)\n"
        )


# Made with Bob
