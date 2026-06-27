# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Utility functions for Algorithm Nexus CLI commands."""

from __future__ import annotations

import csv
import io
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

try:
    import typer
    from rich.console import Console
    from rich.table import Table
except ImportError:
    print(
        "Error: CLI dependencies are not installed.\n"
        "Please install them with: pip install algorithm-nexus[cli]",
        file=sys.stderr,
    )
    sys.exit(1)

from algorithm_nexus.models import AlgorithmNexusPackageConfig

console = Console()


def strip_ansi_codes(text: str) -> str:
    """Remove ANSI escape sequences from text.

    Args:
        text: Text potentially containing ANSI codes

    Returns:
        Text with ANSI codes removed
    """
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


class ValidationErrorCollector:
    """Collects validation errors and info messages during package validation."""

    def __init__(self) -> None:
        """Initialize the error collector."""
        self.errors: list[str] = []
        self.info: list[str] = []

    def add(self, message: str) -> None:
        """Add a single error message."""
        self.errors.append(message)

    def add_info(self, message: str) -> None:
        """Add a single info message."""
        self.info.append(message)

    def extend(self, messages: list[str]) -> None:
        """Add multiple error messages."""
        self.errors.extend(messages)

    @property
    def has_errors(self) -> bool:
        """Check if any errors have been collected."""
        return bool(self.errors)

    @property
    def has_info(self) -> bool:
        """Check if any info messages have been collected."""
        return bool(self.info)

    def format_errors(self) -> str:
        """Format errors as a bulleted list."""
        return "\n".join(f"[red]✗[/red] {error}" for error in self.errors)

    def format_info(self) -> str:
        """Format info messages as a bulleted list."""
        return "\n".join(f"[yellow]i[/yellow] {msg}" for msg in self.info)

    def __str__(self) -> str:
        """Format errors as a bulleted list."""
        return self.format_errors()


def load_yaml_file(
    path: Path, collector: ValidationErrorCollector
) -> dict[str, Any] | None:
    """Load and parse a YAML file, collecting any errors.

    Returns a dict if successful, None otherwise.
    Validates that the YAML contains a mapping (dict) at the top level.
    """
    if not path.is_file():
        collector.add(f"Missing YAML file: {path}")
        return None

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        collector.add(f"Invalid YAML syntax in {path}: {exc}")
        return None

    if data is None:
        collector.add(f"YAML file is empty: {path}")
        return None

    if not isinstance(data, dict):
        collector.add(
            f"{path} must contain a YAML mapping at the top level, got {type(data).__name__}"
        )
        return None

    return data


def validate_output_format(
    output_format: str | None,
    allow_txt: bool = False,
    allow_yaml: bool = False,
    allow_csv: bool = True,
    allow_table: bool = False,
) -> None:
    """Validate the output format parameter.

    Args:
        output_format: The output format to validate
        allow_txt: Whether to allow 'txt' format (for requirements files)
        allow_yaml: Whether to allow 'yaml' format
        allow_csv: Whether to allow 'csv' format (default: True)
        allow_table: Whether to allow 'table' format (for human-readable tables)

    Raises:
        typer.Exit: If the format is invalid
    """
    valid_formats = ["json"]
    if allow_csv:
        valid_formats.append("csv")
    if allow_txt:
        valid_formats.append("txt")
    if allow_yaml:
        valid_formats.append("yaml")
    if allow_table:
        valid_formats.append("table")

    if output_format is not None and output_format not in valid_formats:
        formats_str = "', '".join(valid_formats)
        console.print(
            f"[red]Error:[/red] Invalid output format '{output_format}'. "
            f"Must be '{formats_str}'."
        )
        raise typer.Exit(code=1)


def validate_txt_only_format(output_format: str | None) -> None:
    """Validate that output format is 'txt' if specified.

    Args:
        output_format: The output format to validate

    Raises:
        typer.Exit: If the format is not 'txt'
    """
    if output_format is not None and output_format != "txt":
        console.print(
            f"[red]Error:[/red] Invalid output format '{output_format}'. Must be 'txt'."
        )
        raise typer.Exit(code=1)


def output_data(
    data: list[dict[str, Any]],
    headers: list[str],
    output_format: str | None,
    output_file: Path | None,
    table_title: str,
) -> None:
    """Output data in the specified format.

    Args:
        data: List of dictionaries containing the data rows
        headers: List of column headers
        output_format: Output format ('csv', 'json', 'yaml', or None for table)
        output_file: Optional file path to write output to
        table_title: Title for the table output
    """
    if output_format == "json":
        json_output = json.dumps(data, indent=2)
        if output_file:
            output_file.write_text(json_output)
            console.print(f"[green]Output written to {output_file}[/green]")
        else:
            console.print(json_output)
    elif output_format == "yaml":
        yaml_output = yaml.dump(data, default_flow_style=False, sort_keys=False)
        if output_file:
            output_file.write_text(yaml_output)
            console.print(f"[green]Output written to {output_file}[/green]")
        else:
            console.print(yaml_output)
    elif output_format == "csv":
        # Write CSV to string first
        csv_buffer = io.StringIO()
        writer = csv.DictWriter(csv_buffer, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)
        csv_output = csv_buffer.getvalue()

        if output_file:
            output_file.write_text(csv_output)
            console.print(f"[green]Output written to {output_file}[/green]")
        else:
            console.print(csv_output)
    else:
        # Default table output
        if output_file:
            console.print(
                "[yellow]Warning: --output-file is ignored for table output[/yellow]"
            )

        console.print(f"\n[bold]{table_title}[/bold]\n")
        table = Table(show_header=True, header_style="bold cyan")

        # Add columns with appropriate styling
        for header in headers:
            if "package" in header.lower() and "nexus" in header.lower():
                table.add_column(header, style="cyan")
            elif "package" in header.lower():
                table.add_column(header, style="yellow")
            elif "experiment" in header.lower():
                table.add_column(header, style="white")
            else:
                table.add_column(header)

        # Add rows
        for row in data:
            table.add_row(*[str(row[h]) for h in headers])

        console.print(table)


def collect_benchmark_data(
    packages_root: Path,
    warn_on_error: bool = False,
) -> dict[str, dict[str, list[str]]]:
    """Collect benchmark package data from all nexus packages.

    Args:
        packages_root: Root directory containing package directories
        warn_on_error: If True, print warnings to stderr for failed loads

    Returns:
        Dictionary mapping benchmark_package -> experiment_id -> [nexus_package_names]
    """
    # Structure: benchmark_package -> experiment_id -> list of nexus packages
    benchmark_data: dict[str, dict[str, list[str]]] = {}

    for package_dir in packages_root.iterdir():
        if not package_dir.is_dir() or package_dir.name.startswith("."):
            continue

        nexus_yaml_path = package_dir / "nexus.yaml"
        if not nexus_yaml_path.exists():
            continue

        collector = ValidationErrorCollector()
        nexus_data = load_yaml_file(nexus_yaml_path, collector)
        if nexus_data is None or collector.has_errors:
            if warn_on_error:
                error_console = Console(stderr=True)
                error_console.print(
                    f"[yellow]Warning:[/yellow] Skipping {package_dir.name}: "
                    f"Failed to load nexus.yaml"
                )
            continue

        try:
            package_config = AlgorithmNexusPackageConfig.model_validate(nexus_data)
            package_name = package_config.package.name

            if package_config.package.benchmark_packages:
                for bench_pkg in package_config.package.benchmark_packages:
                    req_spec = bench_pkg.requirement_specifier
                    if req_spec not in benchmark_data:
                        benchmark_data[req_spec] = {}

                    for exp_id in bench_pkg.experiments:
                        if exp_id not in benchmark_data[req_spec]:
                            benchmark_data[req_spec][exp_id] = []
                        benchmark_data[req_spec][exp_id].append(package_name)
        except Exception as e:  # noqa: S112
            if warn_on_error:
                error_console = Console(stderr=True)
                error_console.print(
                    f"[yellow]Warning:[/yellow] Skipping {package_dir.name}: "
                    f"Invalid package configuration ({type(e).__name__})"
                )
            continue

    return benchmark_data


def try_load_package_config(
    package_dir: Path,
    warn_on_error: bool = False,
) -> AlgorithmNexusPackageConfig | None:
    """Attempt to load and validate a package configuration.

    Args:
        package_dir: Directory containing the nexus.yaml file
        warn_on_error: If True, print warnings to stderr for failed loads

    Returns:
        Validated AlgorithmNexusPackageConfig if successful, None otherwise
    """
    nexus_yaml_path = package_dir / "nexus.yaml"
    if not nexus_yaml_path.exists():
        return None

    collector = ValidationErrorCollector()
    nexus_data = load_yaml_file(nexus_yaml_path, collector)
    if nexus_data is None or collector.has_errors:
        if warn_on_error:
            error_console = Console(stderr=True)
            error_console.print(
                f"[yellow]Warning:[/yellow] Skipping {package_dir.name}: "
                f"Failed to load nexus.yaml"
            )
        return None

    try:
        return AlgorithmNexusPackageConfig.model_validate(nexus_data)
    except Exception as e:  # noqa: S112
        if warn_on_error:
            error_console = Console(stderr=True)
            error_console.print(
                f"[yellow]Warning:[/yellow] Skipping {package_dir.name}: "
                f"Invalid package configuration ({type(e).__name__})"
            )
        return None


def find_package_config(
    nexus_package: str,
    packages_root: Path,
) -> tuple[Path, AlgorithmNexusPackageConfig] | None:
    """Find and load a package configuration by name.

    Args:
        nexus_package: Name of the Nexus package to find
        packages_root: Root directory containing package directories

    Returns:
        Tuple of (package_dir, package_config) if found, None otherwise
    """
    for pkg_dir in packages_root.iterdir():
        if not pkg_dir.is_dir() or pkg_dir.name.startswith("."):
            continue

        package_config = try_load_package_config(pkg_dir)
        if package_config and package_config.package.name == nexus_package:
            return (pkg_dir, package_config)

    return None


def output_requirements_txt(
    requirements: list[str],
    output_file: Path | None,
) -> None:
    """Output requirements in txt format.

    Args:
        requirements: List of requirement specifiers
        output_file: Optional file path to write output to
    """
    txt_output = "\n".join(requirements) + "\n"

    if output_file:
        output_file.write_text(txt_output)
        console.print(f"[green]Requirements written to {output_file}[/green]")
    else:
        console.print(txt_output, end="")


def output_benchmark_requirements_table(
    benchmark_packages: list[Any],
    nexus_package: str,
    output_format: str | None,
    output_file: Path | None,
) -> None:
    """Output benchmark requirements in table format.

    Args:
        benchmark_packages: List of BenchmarkPackage objects
        nexus_package: Name of the Nexus package
        output_format: Output format (csv, json, or None for table)
        output_file: Optional file path to write output to
    """
    headers = ["Requirement Specifier"]

    data = [
        {"Requirement Specifier": bench_pkg.requirement_specifier}
        for bench_pkg in benchmark_packages
    ]

    output_data(
        data=data,
        headers=headers,
        output_format=output_format,
        output_file=output_file,
        table_title=f"Benchmark Requirements for Nexus Package: {nexus_package}",
    )


def format_results(results: dict[str, Any], fmt: str) -> str:
    """Format benchmark results as JSON or YAML string.

    Args:
        results: Dictionary containing results to format
        fmt: Output format ('json' or 'yaml')

    Returns:
        Formatted string representation of results
    """
    if fmt == "json":
        return json.dumps(results, indent=2)
    else:  # yaml
        return yaml.safe_dump(results, default_flow_style=False, sort_keys=False)


def get_status_color(status: str) -> str:
    """Get the color name for a given status.

    Args:
        status: Status string (e.g., 'success', 'failed', 'started')

    Returns:
        Color name for Rich console formatting
    """
    status_colors = {
        "success": "green",
        "started": "cyan",
        "failed": "red",
    }
    return status_colors.get(status, "yellow")


def get_status_display(status: str) -> str:
    """Get color-coded status display string.

    Args:
        status: Status string (e.g., 'success', 'failed', 'started')

    Returns:
        Rich-formatted status string with color
    """
    color = get_status_color(status)
    return f"[{color}]{status}[/{color}]"


def write_results_to_file(results: dict[str, Any], output_file: Path, fmt: str) -> None:
    """Write benchmark results to a file in the specified format.

    Args:
        results: Dictionary containing results to write
        output_file: Path to the output file
        fmt: Output format ('json' or 'yaml')
    """
    output_file.write_text(format_results(results, fmt))
    console.print(f"\nResults written to: {output_file}")


def print_structured_results(results: dict[str, Any], fmt: str) -> None:
    """Print benchmark results in structured format (JSON or YAML).

    Args:
        results: Dictionary containing results to print
        fmt: Output format ('json' or 'yaml')
    """
    console.print()  # Blank line before output
    console.print(format_results(results, fmt))


def print_human_readable_results(results: dict[str, Any]) -> None:
    """Print benchmark results in human-readable format.

    Args:
        results: Dictionary containing results with 'instances' key
    """
    console.print("\n[bold]Benchmark Execution Results[/bold]\n")

    if not results.get("instances"):
        console.print("[yellow]No benchmark instances found[/yellow]")
        return

    for instance in results["instances"]:
        instance_path = instance.get("instance_path", "Unknown")
        status = instance.get("status", "unknown")
        message = instance.get("message", "")

        console.print(f"[bold]{instance_path}[/bold]")
        console.print(f"  Status: {get_status_display(status)}")

        if message:
            console.print(f"  Message: {message}")

        if instance.get("space_id"):
            console.print(f"  Space ID: {instance['space_id']}")
        if instance.get("operation_id"):
            console.print(f"  Operation ID: {instance['operation_id']}")
        if instance.get("ray_job_id"):
            console.print(f"  Ray Job ID: {instance['ray_job_id']}")

        console.print()  # Empty line between instances


# Made with Bob
