# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""List commands for Algorithm Nexus CLI."""

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
    collect_benchmark_data,
    output_data,
    try_load_package_config,
    validate_output_format,
)

console = Console()


def list_packages(
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
            help="Output format: 'csv' or 'json'. Default is table output.",
        ),
    ] = None,
    output_file: Annotated[
        Path | None,
        typer.Option(
            "--output-file",
            help="File path to write output to. Only used with -o csv or json.",
        ),
    ] = None,
    strict: Annotated[
        bool,
        typer.Option(
            "--strict",
            help="Warn on stderr when packages fail to load due to invalid YAML or schema errors.",
        ),
    ] = False,
) -> None:
    """List all Nexus packages discovered in the packages directory."""
    validate_output_format(output_format)

    if not packages_root.is_dir():
        console.print(f"[red]Error:[/red] {packages_root} is not a directory")
        raise typer.Exit(code=1)

    # Collect all nexus packages
    nexus_packages: list[str] = []

    for package_dir in packages_root.iterdir():
        if not package_dir.is_dir() or package_dir.name.startswith("."):
            continue

        package_config = try_load_package_config(package_dir, warn_on_error=strict)
        if package_config:
            nexus_packages.append(package_config.package.name)

    if not nexus_packages:
        console.print("\n[yellow]No Nexus packages found[/yellow]\n")
        return

    # Prepare data for output
    data = [{"Nexus Package": pkg} for pkg in sorted(nexus_packages)]
    headers = ["Nexus Package"]

    output_data(
        data=data,
        headers=headers,
        output_format=output_format,
        output_file=output_file,
        table_title="Discovered Nexus Packages",
    )

    if not output_format:
        console.print(f"\n[bold]Total:[/bold] {len(nexus_packages)} packages\n")


def list_benchmark_packages(
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
    nexus_package: Annotated[
        str | None,
        typer.Option(
            "--nexus-package",
            help="Filter results to show only benchmark packages used by the specified nexus package",
        ),
    ] = None,
    output_format: Annotated[
        str | None,
        typer.Option(
            "-o",
            "--output-format",
            help="Output format: 'csv' or 'json'. Default is table output.",
        ),
    ] = None,
    output_file: Annotated[
        Path | None,
        typer.Option(
            "--output-file",
            help="File path to write output to. Only used with -o csv or json.",
        ),
    ] = None,
    strict: Annotated[
        bool,
        typer.Option(
            "--strict",
            help="Warn on stderr when packages fail to load due to invalid YAML or schema errors.",
        ),
    ] = False,
) -> None:
    """List all benchmark packages discovered across all Nexus packages.

    By default, shows a deduplicated table of benchmark packages with the nexus
    packages that use them. Use --nexus-package to filter results for a specific
    nexus package.
    """
    validate_output_format(output_format)

    if not packages_root.is_dir():
        console.print(f"[red]Error:[/red] {packages_root} is not a directory")
        raise typer.Exit(code=1)

    # Collect all benchmark data
    benchmark_data = collect_benchmark_data(packages_root, warn_on_error=strict)

    if not benchmark_data:
        console.print(
            "\n[yellow]No benchmark packages found in any packages[/yellow]\n"
        )
        return

    # Filter by nexus package if specified
    title = "Discovered Benchmark Packages"
    if nexus_package:
        filtered_data: dict[str, dict[str, list[str]]] = {}
        for bench_pkg, experiments in benchmark_data.items():
            for exp_id, pkg_list in experiments.items():
                if nexus_package in pkg_list:
                    if bench_pkg not in filtered_data:
                        filtered_data[bench_pkg] = {}
                    filtered_data[bench_pkg][exp_id] = [nexus_package]

        if not filtered_data:
            console.print(
                f"\n[yellow]No benchmark packages found for nexus package '{nexus_package}'[/yellow]\n"
            )
            return

        benchmark_data = filtered_data
        title = f"Benchmark Packages for Nexus Package: {nexus_package}"

    # Prepare data for output
    if nexus_package:
        headers = ["Benchmark Package"]
        data = [
            {"Benchmark Package": bench_pkg}
            for bench_pkg in sorted(benchmark_data.keys())
        ]
    else:
        headers = ["Benchmark Package", "Registered By"]
        data = []
        for bench_pkg in sorted(benchmark_data.keys()):
            all_packages = set()
            for exp_packages in benchmark_data[bench_pkg].values():
                all_packages.update(exp_packages)
            data.append(
                {
                    "Benchmark Package": bench_pkg,
                    "Registered By": ", ".join(sorted(all_packages)),
                }
            )

    output_data(
        data=data,
        headers=headers,
        output_format=output_format,
        output_file=output_file,
        table_title=title,
    )

    if not output_format:
        console.print(
            f"\n[bold]Total:[/bold] {len(benchmark_data)} benchmark packages\n"
        )


def list_benchmark_experiments(
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
    nexus_package: Annotated[
        str | None,
        typer.Option(
            "--nexus-package",
            help="Filter results to show only experiments used by the specified nexus package",
        ),
    ] = None,
    output_format: Annotated[
        str | None,
        typer.Option(
            "-o",
            "--output-format",
            help="Output format: 'csv' or 'json'. Default is table output.",
        ),
    ] = None,
    output_file: Annotated[
        Path | None,
        typer.Option(
            "--output-file",
            help="File path to write output to. Only used with -o csv or json.",
        ),
    ] = None,
    strict: Annotated[
        bool,
        typer.Option(
            "--strict",
            help="Warn on stderr when packages fail to load due to invalid YAML or schema errors.",
        ),
    ] = False,
) -> None:
    """List all benchmark experiments discovered across all Nexus packages.

    By default, shows a unified table with experiments and their nexus packages.
    Use --nexus-package to filter results for a specific nexus package.
    """
    validate_output_format(output_format)

    if not packages_root.is_dir():
        console.print(f"[red]Error:[/red] {packages_root} is not a directory")
        raise typer.Exit(code=1)

    # Collect all benchmark data
    benchmark_data = collect_benchmark_data(packages_root, warn_on_error=strict)

    if not benchmark_data:
        console.print(
            "\n[yellow]No benchmark experiments found in any packages[/yellow]\n"
        )
        return

    # Filter by nexus package if specified
    if nexus_package:
        filtered_data: dict[str, dict[str, list[str]]] = {}
        for bench_pkg, experiments in benchmark_data.items():
            for exp_id, pkg_list in experiments.items():
                if nexus_package in pkg_list:
                    if bench_pkg not in filtered_data:
                        filtered_data[bench_pkg] = {}
                    filtered_data[bench_pkg][exp_id] = [nexus_package]

        if not filtered_data:
            console.print(
                f"\n[yellow]No benchmark experiments found for nexus package '{nexus_package}'[/yellow]\n"
            )
            return

        benchmark_data = filtered_data

    # Prepare data for output
    if nexus_package:
        headers = ["Experiment ID", "Benchmark Package"]
        title = f"Benchmark Experiments for Nexus Package: {nexus_package}"
        data = [
            {
                "Experiment ID": exp_id,
                "Benchmark Package": bench_pkg,
            }
            for bench_pkg in sorted(benchmark_data.keys())
            for exp_id in sorted(benchmark_data[bench_pkg].keys())
        ]
    else:
        headers = ["Experiment ID", "Benchmark Package", "Used By"]
        title = "Discovered Benchmark Experiments"
        data = []
        for bench_pkg in sorted(benchmark_data.keys()):
            for exp_id in sorted(benchmark_data[bench_pkg].keys()):
                nexus_packages = sorted(benchmark_data[bench_pkg][exp_id])
                data.append(
                    {
                        "Experiment ID": exp_id,
                        "Benchmark Package": bench_pkg,
                        "Used By": ", ".join(nexus_packages),
                    }
                )

    output_data(
        data=data,
        headers=headers,
        output_format=output_format,
        output_file=output_file,
        table_title=title,
    )

    if not output_format:
        console.print(
            f"\n[bold]Total:[/bold] {len(data)} experiments across {len(benchmark_data)} benchmark packages\n"
        )

        # Add instructions for getting more details
        console.print("[bold]For further details on each experiment:[/bold]")
        console.print("1. Install ado")
        console.print("   [cyan]uv pip install ado-core[/cyan]")
        console.print("2. Install the Benchmark package the experiment belongs to")
        console.print("   [cyan]uv pip install <benchmark_package>[/cyan]")
        console.print("3. Describe the experiment")
        console.print("   [cyan]ado describe experiment <experiment_id>[/cyan]\n")


# Made with Bob
