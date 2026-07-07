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
    actuator_configurations: Annotated[
        list[str] | None,
        typer.Option(
            "--use-actuator-configuration",
            help=(
                "Map an actuatorIdentifier to an actuatorConfigurationId using the format "
                "'actuator-id=config-id'. Pass multiple mappings either by repeating the flag "
                "or as a comma-separated list: 'id1=cfg-1,id2=cfg-2'. "
                "Experiments whose actuatorIdentifier matches a key will have the "
                "corresponding actuatorConfigurationId added to the operation's "
                "actuatorConfigurationIdentifiers list."
            ),
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
    # Validate output format if specified
    if output_format:
        validate_output_format(output_format, allow_yaml=True, allow_csv=False)

    actuator_configuration_id_map: dict[str, str] = {}
    for entry in actuator_configurations or []:
        for pair in entry.split(","):
            if "=" not in pair:
                raise typer.BadParameter(
                    f"Invalid format '{pair}': expected 'actuator-id=config-id'",
                    param_hint="--use-actuator-configuration",
                )
            key, _, value = pair.partition("=")

            actuator_configuration_id_map[key] = value

    try:
        manager = BenchmarkManager(
            pr_url=pr,
            execute=not dry_run,
            remote_context_file=remote,
            context_file=context,
            actuator_configuration_id_map=actuator_configuration_id_map or None,
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
            write_results_to_file(results, output_file, fmt)
        elif fmt in ("json", "yaml"):
            print_structured_results(results, fmt)
        else:
            print_human_readable_results(results)

        if not dry_run and results.get("summary") and results["summary"]["failed"] > 0:
            raise typer.Exit(code=1)

    except KeyboardInterrupt:
        console_err.print("\n[yellow]Interrupted by user[/yellow]")
        raise typer.Exit(code=130)
    except Exception as e:
        console_err.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


# Made with Bob
