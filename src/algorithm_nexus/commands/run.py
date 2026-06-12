# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Run commands for Algorithm Nexus CLI."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated, Any

from algorithm_nexus.commands.benchmark_manager import BenchmarkManager

try:
    import typer
    import yaml
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


def _format_results(results: dict[str, Any], fmt: str) -> str:
    """Format benchmark results as JSON or YAML string."""
    if fmt == "json":
        return json.dumps(results, indent=2)
    else:  # yaml
        return yaml.safe_dump(results, default_flow_style=False, sort_keys=False)


def _write_results_to_file(
    results: dict[str, Any], output_file: Path, fmt: str
) -> None:
    """Write benchmark results to a file in the specified format."""
    output_file.write_text(_format_results(results, fmt))
    console.print(f"\nResults written to: {output_file}")


def _print_structured_results(results: dict[str, Any], fmt: str) -> None:
    """Print benchmark results in structured format (JSON or YAML)."""
    console.print()  # Blank line before output
    console.print(_format_results(results, fmt))


def _get_status_display(status: str) -> str:
    """Get color-coded status display string."""
    status_colors = {
        "success": "green",
        "started": "cyan",
        "failed": "red",
    }
    color = status_colors.get(status, "yellow")
    return f"[{color}]{status}[/{color}]"


def _print_human_readable_results(results: dict[str, Any]) -> None:
    """Print benchmark results in human-readable format."""
    console.print("\n[bold]Benchmark Execution Results[/bold]\n")

    if not results.get("instances"):
        console.print("[yellow]No benchmark instances found[/yellow]")
        return

    for instance in results["instances"]:
        instance_path = instance.get("instance_path", "Unknown")
        status = instance.get("status", "unknown")
        message = instance.get("message", "")

        console.print(f"[bold]{instance_path}[/bold]")
        console.print(f"  Status: {_get_status_display(status)}")

        if message:
            console.print(f"  Message: {message}")

        if instance.get("space_id"):
            console.print(f"  Space ID: {instance['space_id']}")
        if instance.get("operation_id"):
            console.print(f"  Operation ID: {instance['operation_id']}")
        if instance.get("ray_job_id"):
            console.print(f"  Ray Job ID: {instance['ray_job_id']}")

        console.print()  # Empty line between instances


def run_benchmarks(
    pr: Annotated[
        str,
        typer.Option(
            "--pr",
            help="GitHub Pull Request URL (e.g., https://github.com/IBM/algorithm-nexus/pull/123)",
        ),
    ],
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
    """Execute benchmarks from a GitHub Pull Request.

    Identifies new or changed benchmark instances in a PR and optionally
    executes them using the ADO CLI. When executing with --remote flag,
    automatically installs required benchmark packages in the Ray environment.

    The command automatically checks if the local repository is on the same
    commit as the PR. If not, it will checkout the PR code in a temporary
    directory.
    """
    from algorithm_nexus.commands.utils import validate_output_format

    # Validate output format if specified
    if output_format:
        validate_output_format(output_format, allow_yaml=True, allow_csv=False)

    try:
        manager = BenchmarkManager(
            pr_url=pr,
            execute=not dry_run,
            remote_context_file=remote,
            context_file=context,
        )
        results = manager.run()

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
            _write_results_to_file(results, output_file, fmt)
        elif fmt in ("json", "yaml"):
            _print_structured_results(results, fmt)
        else:
            _print_human_readable_results(results)

        if not dry_run and results.get("summary") and results["summary"]["failed"] > 0:
            raise typer.Exit(code=1)

    except KeyboardInterrupt:
        console_err.print("\n[yellow]Interrupted by user[/yellow]")
        raise typer.Exit(code=130)
    except Exception as e:
        console_err.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


# Made with Bob
