# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""List commands for Algorithm Nexus CLI."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Any

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
    _LOAD_ERROR,
    output_data,
    try_load_package_config,
    validate_output_format,
)

console = Console()
error_console = Console(stderr=True)


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
            help="Exit with an error if any package fails to load.",
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
    had_errors = False

    for package_dir in packages_root.iterdir():
        if not package_dir.is_dir() or package_dir.name.startswith("."):
            continue

        package_config = try_load_package_config(package_dir)
        if package_config is _LOAD_ERROR:
            had_errors = True
        elif package_config is not None:
            nexus_packages.append(package_config.package.name)

    if had_errors and strict:
        raise typer.Exit(code=1)

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


def list_experiment_packages(
    experiments_root: Annotated[
        Path,
        typer.Argument(
            help="Path to the experiments root directory (default: ./experiments).",
            dir_okay=True,
            file_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ] = Path("./experiments"),
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
            help="Exit with an error if any experiment package fails to load.",
        ),
    ] = False,
) -> None:
    """List all experiment packages discovered under experiments/.

    Shows a table of experiment packages with their folder, requirement
    specifier, experiment IDs, and logical benchmark bindings.
    """
    import yaml

    from algorithm_nexus.models import BindingFileConfig, ExperimentConfig

    validate_output_format(output_format)

    if not experiments_root.is_dir():
        console.print(f"[red]Error:[/red] {experiments_root} is not a directory")
        raise typer.Exit(code=1)

    data: list[dict[str, Any]] = []
    had_errors = False

    for exp_dir in sorted(experiments_root.iterdir()):
        if not exp_dir.is_dir() or exp_dir.name.startswith("."):
            continue

        exp_yaml = exp_dir / "experiment_package.yaml"
        if not exp_yaml.exists():
            error_console.print(
                f"[yellow]Warning:[/yellow] Skipping {exp_dir.name}: "
                f"no experiment_package.yaml found"
            )
            had_errors = True
            continue

        try:
            config_dict = yaml.safe_load(exp_yaml.read_text(encoding="utf-8"))
            if not config_dict or "experiment_package" not in config_dict:
                raise ValueError("Missing 'experiment_package' key")
            config = ExperimentConfig.model_validate(config_dict)
            exp_package = config.experiment_package
        except Exception as e:
            error_console.print(
                f"[yellow]Warning:[/yellow] Skipping {exp_dir.name}: "
                f"Failed to load or validate experiment_package.yaml: {e}"
            )
            had_errors = True
            continue

        # Collect all benchmark identifiers referenced in bindings/
        all_benchmarks: set[str] = set()
        bindings_dir = exp_dir / "bindings"
        if bindings_dir.is_dir():
            for binding_file in sorted(bindings_dir.iterdir()):
                if (
                    not binding_file.is_file()
                    or binding_file.name.startswith(".")
                    or binding_file.suffix not in (".yaml", ".yml")
                ):
                    continue
                try:
                    binding_data = yaml.safe_load(
                        binding_file.read_text(encoding="utf-8")
                    )
                    if binding_data:
                        for binding in BindingFileConfig.model_validate(
                            binding_data
                        ).bindings:
                            all_benchmarks.add(binding.benchmarkIdentifier)
                except Exception as e:
                    error_console.print(
                        f"[yellow]Warning:[/yellow] Failed to load binding file "
                        f"{binding_file.name}: {e}"
                    )
                    had_errors = True

        data.append(
            {
                "Experiment Folder": exp_dir.name,
                "Requirement Specifier": exp_package.requirement_specifier,
                "Experiments": ", ".join(sorted(exp_package.experiments)),
                "Bindings": ", ".join(sorted(all_benchmarks))
                if all_benchmarks
                else "None",
            }
        )

    if had_errors and strict:
        raise typer.Exit(code=1)

    if not data:
        console.print(
            "\n[yellow]No experiment packages found under experiments/[/yellow]\n"
        )
        return

    headers = ["Experiment Folder", "Requirement Specifier", "Experiments", "Bindings"]

    output_data(
        data=data,
        headers=headers,
        output_format=output_format,
        output_file=output_file,
        table_title="Discovered Experiment Packages",
    )

    if not output_format:
        console.print(f"\n[bold]Total:[/bold] {len(data)} experiment packages\n")


def list_benchmark_experiments(
    experiments_root: Annotated[
        Path,
        typer.Argument(
            help="Path to the experiments root directory (default: ./experiments).",
            dir_okay=True,
            file_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ] = Path("./experiments"),
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
            help="Exit with an error if any experiment package fails to load.",
        ),
    ] = False,
) -> None:
    """List all benchmark experiments discovered under experiments/."""
    import yaml

    from algorithm_nexus.models import BindingFileConfig, ExperimentConfig

    validate_output_format(output_format)

    if not experiments_root.is_dir():
        console.print(f"[red]Error:[/red] {experiments_root} is not a directory")
        raise typer.Exit(code=1)

    data: list[dict[str, Any]] = []
    had_errors = False

    # Traverse experiments_root
    for exp_dir in sorted(experiments_root.iterdir()):
        if not exp_dir.is_dir() or exp_dir.name.startswith("."):
            continue

        exp_yaml = exp_dir / "experiment_package.yaml"
        if not exp_yaml.exists():
            error_console.print(
                f"[yellow]Warning:[/yellow] Skipping {exp_dir.name}: "
                f"no experiment_package.yaml found"
            )
            had_errors = True
            continue

        try:
            config_dict = yaml.safe_load(exp_yaml.read_text(encoding="utf-8"))
            if not config_dict or "experiment_package" not in config_dict:
                raise ValueError("Missing 'experiment_package' key")

            config = ExperimentConfig.model_validate(config_dict)
            exp_package = config.experiment_package
        except Exception as e:
            error_console.print(
                f"[yellow]Warning:[/yellow] Skipping {exp_dir.name}: "
                f"Failed to load or validate experiment_package.yaml: {e}"
            )
            had_errors = True
            continue

        # Load bindings in experiments/<name>/bindings/
        bindings_dir = exp_dir / "bindings"
        exp_id_to_benchmarks: dict[str, set[str]] = {
            exp_id: set() for exp_id in exp_package.experiments
        }

        if bindings_dir.is_dir():
            for binding_file in sorted(bindings_dir.iterdir()):
                if (
                    not binding_file.is_file()
                    or binding_file.name.startswith(".")
                    or binding_file.suffix not in (".yaml", ".yml")
                ):
                    continue

                try:
                    binding_data = yaml.safe_load(
                        binding_file.read_text(encoding="utf-8")
                    )
                    if binding_data:
                        for binding in BindingFileConfig.model_validate(
                            binding_data
                        ).bindings:
                            exp_id = binding.experiment.experimentIdentifier
                            if exp_id in exp_id_to_benchmarks:
                                exp_id_to_benchmarks[exp_id].add(
                                    binding.benchmarkIdentifier
                                )
                except Exception as e:
                    error_console.print(
                        f"[yellow]Warning:[/yellow] Failed to load binding file {binding_file.name}: {e}"
                    )
                    had_errors = True

        # For each experiment ID, create an entry
        for exp_id in sorted(exp_package.experiments):
            associated_benchmarks = sorted(list(exp_id_to_benchmarks[exp_id]))
            data.append(
                {
                    "Experiment ID": exp_id,
                    "Experiment Folder": exp_dir.name,
                    "Requirement Specifier": exp_package.requirement_specifier,
                    "Associated Bindings": ", ".join(associated_benchmarks)
                    if associated_benchmarks
                    else "None",
                }
            )

    if had_errors and strict:
        raise typer.Exit(code=1)

    if not data:
        console.print(
            "\n[yellow]No benchmark experiments found under experiments/[/yellow]\n"
        )
        return

    headers = [
        "Experiment ID",
        "Experiment Folder",
        "Requirement Specifier",
        "Associated Bindings",
    ]

    output_data(
        data=data,
        headers=headers,
        output_format=output_format,
        output_file=output_file,
        table_title="Discovered Benchmark Experiments",
    )

    if not output_format:
        console.print(f"\n[bold]Total:[/bold] {len(data)} experiments discovered\n")

        # Add instructions for getting more details
        console.print("[bold]For further details on each experiment:[/bold]")
        console.print("1. Install the experiment package containing the experiment")
        console.print("   [cyan]uv pip install <requirement_specifier>[/cyan]")
        console.print("2. Describe the experiment")
        console.print("   [cyan]ado describe experiment <experiment_id>[/cyan]\n")


# Made with Bob
