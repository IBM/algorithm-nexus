# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Run commands for Algorithm Nexus CLI."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

from algorithm_nexus.commands.benchmark_manager import BenchmarkManager
from algorithm_nexus.commands.utils import (
    print_human_readable_results,
    print_structured_results,
    validate_output_format,
    write_results_to_file,
)

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

console = Console()
console_err = Console(stderr=True)


def run_benchmarks(
    pr: Annotated[
        str | None,
        typer.Option(
            "--pr",
            help="GitHub Pull Request URL (e.g., https://github.com/IBM/algorithm-nexus/pull/123). "
            "If not provided, runs benchmark instances from packages.",
        ),
    ] = None,
    packages_root: Annotated[
        Path,
        typer.Option(
            "--packages-root",
            help="Path to packages directory",
        ),
    ] = Path("./packages"),
    package: Annotated[
        str | None,
        typer.Option(
            "--package",
            help="Run only benchmark instances from a specific package",
        ),
    ] = None,
    remote: Annotated[
        Path | None,
        typer.Option(
            "--remote",
            help="Execute operations on remote Ray cluster using the specified context file",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    context: Annotated[
        Path | None,
        typer.Option(
            "--context",
            help="Path to ADO context YAML file (samplestore context)",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="List benchmarks without executing them (dry run)",
        ),
    ] = False,
    output_file: Annotated[
        Path | None,
        typer.Option(
            "--output-file",
            help="Output file path for execution results. If not specified, results are printed to screen.",
            dir_okay=False,
            writable=True,
        ),
    ] = None,
    output_format: Annotated[
        str | None,
        typer.Option(
            "-o",
            "--output-format",
            help="Output format: 'json' or 'yaml'. Only used with --output-file.",
        ),
    ] = None,
) -> None:
    """Execute benchmarks.

    This command supports three modes:
    1. PR mode: Execute instances modified in a PR (provide --pr)
    2. All mode: Execute all benchmark instances (no --pr)
    3. Package mode: Execute instances from a specific package (use --package)

    Identifies benchmark instances and optionally executes them using the ADO CLI.
    When executing with --remote flag, automatically installs required benchmark
    packages in the Ray environment.
    """
    # Validate output format if specified
    if output_format:
        validate_output_format(output_format, allow_yaml=True, allow_csv=False)

    # Warn if both package filter and PR URL are provided (package is ignored in PR mode)
    if package and pr:
        console.print(
            "[yellow]Warning:[/yellow] --package is ignored when --pr is specified. "
            "In PR mode, only instances changed in the PR are executed."
        )

    # Validate package exists if package filter is specified (non-PR mode only)
    if package and not pr:
        package_path = packages_root / package
        if not package_path.is_dir():
            console.print(
                f"[red]Error:[/red] Package '{package}' not found in {packages_root.resolve()}"
            )
            console.print(
                "\nTo see available packages, run: [cyan]nexus list packages[/cyan]"
            )
            raise typer.Exit(code=1)

    try:
        if pr:
            manager = BenchmarkManager(
                pr_url=pr,
                execute=not dry_run,
                remote_context_file=remote,
                context_file=context,
            )
            results = manager.run()
        else:
            manager = BenchmarkManager(
                pr_url=None,
                execute=not dry_run,
                remote_context_file=remote,
                context_file=context,
            )
            results = manager.run(
                packages_root=packages_root,
                package_filter=package,
            )

        # Output results
        # Determine output format
        if output_format:
            fmt = output_format
        elif output_file and (
            output_file.suffix == ".yaml" or output_file.suffix == ".yml"
        ):
            fmt = "yaml"
        elif output_file:
            fmt = "json"
        else:
            fmt = None  # Human-readable format for console

        # Output results
        if output_file:
            # fmt is guaranteed to be a string when output_file is provided
            # (either from output_format, file extension, or defaulted to "json")
            if fmt is None:
                fmt = "json"  # Default fallback (should never happen based on logic above)
            write_results_to_file(results, output_file, fmt)
        elif fmt in ("json", "yaml"):
            print_structured_results(results, fmt)
        else:
            print_human_readable_results(results)

        if not dry_run and results.get("summary") and results["summary"]["failed"] > 0:
            raise typer.Exit(code=1)

    except typer.Exit:
        raise
    except KeyboardInterrupt:
        console_err.print("\n[yellow]Interrupted by user[/yellow]")
        raise typer.Exit(code=130)
    except Exception as e:
        console_err.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


# Made with Bob
