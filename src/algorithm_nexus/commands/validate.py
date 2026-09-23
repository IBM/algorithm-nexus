# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Validate command for Algorithm Nexus CLI."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Any, Literal

try:
    import typer
    from pydantic import ValidationError
    from rich.console import Console
    from rich.panel import Panel
except ImportError:
    print(
        "Error: CLI dependencies are not installed.\n"
        "Please install them with: pip install algorithm-nexus[cli]",
        file=sys.stderr,
    )
    sys.exit(1)

from algorithm_nexus.commands.utils import (
    ValidationErrorCollector,
    determine_output_format,
    load_yaml_file,
    print_results_table,
    print_structured_results,
    validate_output_format,
    write_results_to_file,
)
from algorithm_nexus.models import (
    AlgorithmNexusModelConfig,
    AlgorithmNexusPackageConfig,
    BenchmarkBinding,
    BenchmarkInstance,
    CategoricalValueMapping,
    FieldMapping,
    LogicalBenchmarkConfig,
)

console = Console()


def format_pydantic_error(error: dict[str, Any], file_path: Path) -> str:
    """Format a Pydantic validation error into a readable message."""
    loc = ".".join(str(x) for x in error["loc"])
    msg = error["msg"]

    # Extract more context from the error if available
    error_type = error.get("type", "")

    # For value_error types, the message usually contains the full explanation
    if error_type.startswith("value_error"):
        # The message already contains the full context
        return f"[bold]{file_path}[/bold]\n  Field: [cyan]{loc}[/cyan]\n  Error: {msg}"

    # For missing field errors
    if error_type == "missing":
        return f"[bold]{file_path}[/bold]\n  Field: [cyan]{loc}[/cyan]\n  Error: This required field is missing"

    # Default format for other errors
    return f"[bold]{file_path}[/bold]\n  Field: [cyan]{loc}[/cyan]\n  Error: {msg}"


def validate_nexus_yaml(
    package_dir: Path,
    collector: ValidationErrorCollector,
) -> AlgorithmNexusPackageConfig | None:
    """Validate nexus.yaml.

    Returns the validated package config if successful, None otherwise.
    """
    nexus_yaml_path = package_dir / "nexus.yaml"
    data = load_yaml_file(nexus_yaml_path, collector)
    if data is None:
        return None

    try:
        return AlgorithmNexusPackageConfig.model_validate(data)
    except ValidationError as exc:
        for error in exc.errors():
            collector.add(format_pydantic_error(error, nexus_yaml_path))
        return None


def validate_model_yaml(
    model_dir: Path, collector: ValidationErrorCollector
) -> AlgorithmNexusModelConfig | None:
    """Validate a model's model.yaml file.

    Returns the validated model config if successful, None otherwise.
    """
    model_yaml_path = model_dir / "model.yaml"
    data = load_yaml_file(model_yaml_path, collector)
    if data is None:
        return None

    try:
        return AlgorithmNexusModelConfig.model_validate(data)
    except ValidationError as exc:
        for error in exc.errors():
            collector.add(format_pydantic_error(error, model_yaml_path))
        return None


def validate_benchmark_submissions(
    model_dir: Path,
    collector: ValidationErrorCollector,
    registered_experiments: set[str],
) -> None:
    """Validate a model's benchmark_submissions/ folder.

    Validates that each benchmark instance has a space.yaml file.
    Does not validate the contents of space.yaml as that is ADO's responsibility.
    """
    benchmark_submissions_dir = model_dir / "benchmark_submissions"

    # benchmark_submissions/ is optional
    if not benchmark_submissions_dir.exists():
        return

    if not benchmark_submissions_dir.is_dir():
        collector.add(
            f"benchmark_submissions must be a directory when present: {benchmark_submissions_dir}"
        )
        return

    # Validate each benchmark instance folder
    for instance_dir in benchmark_submissions_dir.iterdir():
        if not instance_dir.is_dir():
            continue

        space_yaml_path = instance_dir / "space.yaml"

        # Each benchmark instance must have a space.yaml
        if not space_yaml_path.exists():
            collector.add(
                f"[bold]{instance_dir}[/bold]\n"
                f"  Error: Missing required space.yaml file for benchmark instance '{instance_dir.name}'"
            )


def validate_optional_file(
    path: Path, collector: ValidationErrorCollector, context: str
) -> bool:
    """Validate optional file and add info if missing. Returns True if valid or doesn't exist."""
    if not path.exists():
        collector.add_info(f"{context}")
        return False
    elif not path.is_file():
        collector.add(f"{context} must be a file when present: {path}")
        return False

    return True


def validate_optional_dir(
    path: Path, collector: ValidationErrorCollector, context: str
) -> bool:
    """Validate optional directory and add info if missing. Returns True if valid or doesn't exist."""
    if not path.exists():
        collector.add_info(f"{context}")
        return False
    elif not path.is_dir():
        collector.add(f"{context} must be a directory when present: {path}")
        return False

    return True


def validate_model_directory(
    model_dir: Path,
    collector: ValidationErrorCollector,
    registered_experiments: set[str],
) -> AlgorithmNexusModelConfig | None:
    """Validate a single model directory structure and contents.

    Returns the validated model config if successful, None otherwise.
    """
    if not model_dir.is_dir():
        collector.add(f"Model path is not a directory: {model_dir}")
        return None

    # Validate optional usage.md
    usage_md = model_dir / "usage.md"
    validate_optional_file(
        usage_md,
        collector,
        f"Optional model file missing for '{model_dir.name}': usage.md",
    )

    # Validate model.yaml
    model_config = validate_model_yaml(model_dir, collector)

    # Validate optional benchmark_submissions/
    validate_benchmark_submissions(model_dir, collector, registered_experiments)

    return model_config


def validate_package_directory(
    package_dir: Path, collector: ValidationErrorCollector
) -> None:
    """Validate the structure and contents of a Nexus package directory."""
    if not package_dir.is_dir():
        collector.add(f"Package path is not a directory: {package_dir}")
        return

    # Validate nexus.yaml and extract registered experiments
    package_config = validate_nexus_yaml(package_dir, collector)
    registered_experiments: set[str] = set()
    if package_config and package_config.package.benchmark_packages:
        # Collect all experiment identifiers from all benchmark packages
        for pkg in package_config.package.benchmark_packages:
            registered_experiments.update(pkg.experiments)

        # Validate unique experiment identifiers across all packages
        all_experiments = []
        for pkg in package_config.package.benchmark_packages:
            all_experiments.extend(pkg.experiments)
        duplicates = {exp for exp in all_experiments if all_experiments.count(exp) > 1}
        if duplicates:
            collector.add(
                f"Duplicate experiment identifiers across benchmark packages in nexus.yaml: {', '.join(sorted(duplicates))}"
            )

    # Validate optional skills directory
    skills_dir = package_dir / "skills"
    validate_optional_dir(
        skills_dir, collector, "Optional package directory missing: skills"
    )

    # Validate optional benchmark_packages directory
    benchmark_packages_dir = package_dir / "benchmark_packages"
    if validate_optional_dir(
        benchmark_packages_dir,
        collector,
        "Optional package directory missing: benchmark_packages",
    ):
        # Check that each subdirectory is a valid Python package
        for pkg_dir in benchmark_packages_dir.iterdir():
            if not pkg_dir.is_dir():
                continue
            pyproject_toml = pkg_dir / "pyproject.toml"
            if not pyproject_toml.exists():
                collector.add_info(
                    f"Optional file missing in benchmark_packages/{pkg_dir.name}/: pyproject.toml (required for local benchmark Python package)"
                )

    # Validate optional package-level benchmark_submissions directory
    # The validate_benchmark_submissions function expects a directory that contains benchmark_submissions/
    # So we pass package_dir and it will look for package_dir/benchmark_submissions/
    validate_benchmark_submissions(package_dir, collector, registered_experiments)

    # Check if models directory exists
    models_dir = package_dir / "models"
    if not validate_optional_dir(
        models_dir, collector, "Optional package directory missing: models"
    ):
        return

    # Track HuggingFace model IDs to detect duplicates
    hf_id_to_models: dict[str, list[str]] = {}

    # Only validate model directories if models_dir exists
    for model_dir in models_dir.iterdir():
        model_config = validate_model_directory(
            model_dir, collector, registered_experiments
        )

        # Extract HF ID from validated model config for duplicate checking
        if model_config is not None:
            hf_id = model_config.model.id
            if hf_id not in hf_id_to_models:
                hf_id_to_models[hf_id] = []
            hf_id_to_models[hf_id].append(model_dir.name)

    # Check for duplicate HuggingFace model IDs
    for hf_id, model_names in hf_id_to_models.items():
        if len(model_names) > 1:
            models_list = ", ".join(f"'{name}'" for name in sorted(model_names))
            collector.add(
                f"Duplicate HuggingFace model ID '{hf_id}' found in models: {models_list}"
            )


def validate_package(
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


def _print_validation_table(all_results: list[dict[str, Any]]) -> None:
    rows = []
    for result in all_results:
        issues = []
        if result.get("errors"):
            issues.extend([f"E: {e}" for e in result["errors"]])
        if result.get("warnings"):
            issues.extend([f"W: {w}" for w in result["warnings"]])
        rows.append(
            {
                "submission_path": result["submission_path"],
                "status": result["status"],
                "details": "\n".join(issues) if issues else "-",
            }
        )
    print_results_table(rows, title="Validation Results", details_column="Issues")


def validate_benchmarks(
    pr_url: Annotated[
        str | None,
        typer.Option(
            "--pr",
            help="GitHub Pull Request URL (e.g., https://github.com/IBM/algorithm-nexus/pull/123). "
            "If not provided, validates all benchmark instances.",
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
            help="Validate only benchmark instances from a specific package",
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            help="Show detailed validation output",
        ),
    ] = False,
    fail_fast: Annotated[
        bool,
        typer.Option(
            "--fail-fast",
            help="Stop validation on first error",
        ),
    ] = False,
    output_format: Annotated[
        Literal["json", "yaml", "table"] | None,
        typer.Option(
            "-o",
            "--output-format",
            help="Output format: 'json', 'yaml', or 'table' (default: table)",
        ),
    ] = None,
) -> None:
    """Validate benchmark instances.

    This command supports three modes:
    1. PR mode: Validate instances modified in a PR (provide pr_url)
    2. All mode: Validate all benchmark instances (no pr_url)
    3. Package mode: Validate instances from a specific package (use --package)

    The command:
    - Installs required benchmark packages in isolated virtual environments
    - Validates each instance with ADO dry-run
    - Reports validation results
    """
    from algorithm_nexus.commands.benchmark_manager import BenchmarkManager

    # Validate output format if specified
    if output_format:
        validate_output_format(
            output_format, allow_yaml=True, allow_csv=False, allow_table=True
        )

    # Warn if both package filter and PR URL are provided (package is ignored in PR mode)
    if package and pr_url:
        console.print(
            "[yellow]Warning:[/yellow] --package is ignored when --pr is specified. "
            "In PR mode, only instances changed in the PR are validated."
        )

    # Validate package exists if package filter is specified (non-PR mode only)
    if package and not pr_url:
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
        # Create BenchmarkManager based on mode
        if pr_url:
            # PR mode
            manager = BenchmarkManager(pr_url=pr_url, execute=False)
            results = manager.validate(
                packages_root=None,
                package_filter=None,
                verbose=verbose,
                fail_fast=fail_fast,
            )
        else:
            # All or package mode
            manager = BenchmarkManager(pr_url=None, execute=False)
            results = manager.validate(
                packages_root=packages_root,
                package_filter=package,
                verbose=verbose,
                fail_fast=fail_fast,
            )

        # Extract results
        all_results = results.instances
        total_failed = results.failed

        # Determine output format (default to table for human-readable)
        fmt = output_format or "table"

        # Format output based on requested format
        if fmt in ("json", "yaml"):
            # Structured output (JSON or YAML)
            output_data = {
                "pr_url": pr_url,
                "instances": all_results,
            }
            print_structured_results(output_data, fmt)
        else:
            # Human-readable table output (default)
            _print_validation_table(all_results)

        # Exit with error if any validation failed
        if total_failed > 0:
            raise typer.Exit(code=1)

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise typer.Exit(code=130)
    except typer.Exit:
        # Re-raise typer.Exit to preserve exit codes
        raise
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        if verbose:
            import traceback

            console.print(traceback.format_exc())
        raise typer.Exit(code=1)


def _check_binding_integrity(
    binding: BenchmarkBinding,
    property_ids: set[str],
    metric_ids: set[str] | None,
    instance_ids: set[str] | None,
    collector: ValidationErrorCollector,
    file_path: Path,
    binding_index: int,
) -> None:
    """Check referential integrity between a binding and its parent definition."""
    prefix = f"[bold]{file_path}[/bold]\n  Binding[{binding_index}]"

    # 1. Metric identifiers in metricMapping must exist in the definition
    if binding.metricMapping and metric_ids is not None:
        for entry in binding.metricMapping:
            mid = entry.benchmark.identifier
            if mid not in metric_ids:
                collector.add(
                    f"{prefix}: metricMapping references unknown benchmark metric '{mid}'"
                )

    # 2. Property identifiers in instanceMapping.propertyMapping must exist in the definition
    if binding.instanceMapping and binding.instanceMapping.propertyMapping:
        for pm_entry in binding.instanceMapping.propertyMapping:
            if isinstance(pm_entry, FieldMapping):
                pid = pm_entry.benchmark.identifier
                if pid not in property_ids:
                    collector.add(
                        f"{prefix}: instanceMapping propertyMapping references unknown benchmark property '{pid}'"
                    )
            elif isinstance(pm_entry, CategoricalValueMapping):
                pid = pm_entry.categoricalValue.property.identifier
                if pid not in property_ids:
                    collector.add(
                        f"{prefix}: instanceMapping propertyMapping references unknown benchmark property '{pid}'"
                    )


def validate_instance(
    instance_target: Path,
    instance_props: dict[str, bool],
    collector: ValidationErrorCollector,
) -> BenchmarkInstance | None:
    """Validate a benchmark instance (either an instance directory containing instance.yaml or a standalone instance YAML)."""
    if instance_target.is_dir():
        instance_file = instance_target / "instance.yaml"
        if not instance_file.is_file():
            # Fall back to single yaml file in folder if instance.yaml not explicitly named
            cand_yamls = [
                p
                for p in instance_target.iterdir()
                if p.suffix in (".yaml", ".yml") and p.is_file()
            ]
            if len(cand_yamls) == 1:
                instance_file = cand_yamls[0]
            else:
                collector.add(
                    f"{instance_target}: missing required 'instance.yaml' file"
                )
                return None
        artifacts_dir = instance_target / "artifacts"
    else:
        instance_file = instance_target
        artifacts_dir = instance_target.parent / "artifacts"

    data = load_yaml_file(instance_file, collector)
    if data is None:
        return None

    try:
        instance = BenchmarkInstance.model_validate(data)
    except ValidationError as exc:
        for error in exc.errors():
            collector.add(format_pydantic_error(error, instance_file))
        return None

    # Validate top-level instance properties against benchmark instance definitions
    standard_fields = {"identifier", "description"}
    extra_fields = instance.model_extra if instance.model_extra is not None else {}

    for field_name, field_val in extra_fields.items():
        if field_name in standard_fields:
            continue
        if field_name not in instance_props:
            collector.add(
                f"{instance_file}: property '{field_name}' is not declared as an instance property in the logical benchmark"
            )
            continue

        is_artifact_prop = instance_props[field_name]
        if is_artifact_prop and field_val is not None:
            # Check artifact files exist
            artifact_files: list[str] = []
            if isinstance(field_val, list):
                artifact_files = [str(x) for x in field_val]
            elif isinstance(field_val, dict):
                artifact_files = [str(x) for x in field_val.values()]
            elif isinstance(field_val, str):
                artifact_files = [field_val]

            for art in artifact_files:
                art_path = artifacts_dir / art
                if not art_path.is_file():
                    collector.add(
                        f"{instance_file}: artifact file '{art}' for property '{field_name}' does not exist in {artifacts_dir}"
                    )

    return instance


def validate_logical_benchmark_file(
    file: Path,
    collector: ValidationErrorCollector,
    instance_ids: set[str] | None = None,
) -> LogicalBenchmarkConfig | None:
    """Validate a logical benchmark YAML file against the schema and referential integrity rules.

    Returns the parsed LogicalBenchmarkConfig if schema validation passes, None otherwise.
    Integrity errors are collected but do not prevent returning the parsed object.
    """
    data = load_yaml_file(file, collector)
    if data is None:
        return None

    try:
        parsed = LogicalBenchmarkConfig.model_validate(data)
    except ValidationError as exc:
        for error in exc.errors():
            collector.add(format_pydantic_error(error, file))
        return None

    # Referential integrity checks
    defn = parsed.logicalBenchmark
    property_ids = {p.identifier for p in defn.instance}
    metric_ids = set(defn.metrics) if defn.metrics is not None else None

    # Ranking integrity: ranking.metric must exist in the defined metrics
    if (
        defn.ranking is not None
        and metric_ids is not None
        and defn.ranking.metric not in metric_ids
    ):
        collector.add(
            f"[bold]{file}[/bold]\n  ranking.metric '{defn.ranking.metric}' "
            f"is not defined in metrics"
        )

    if parsed.bindings:
        for i, binding in enumerate(parsed.bindings):
            _check_binding_integrity(
                binding,
                property_ids,
                metric_ids,
                instance_ids,
                collector,
                file,
                i,
            )

    return parsed


def validate_logical_benchmark_directory(
    benchmark_dir: Path,
    collector: ValidationErrorCollector,
) -> LogicalBenchmarkConfig | None:
    """Validate a benchmark directory (problem.yaml, instances/, artifacts/)."""
    problem_file = benchmark_dir / "problem.yaml"
    if not problem_file.is_file():
        # Fall back to single-file named after folder or any yaml if problem.yaml not found
        candidate_yamls = list(benchmark_dir.glob("*.yaml"))
        if len(candidate_yamls) == 1:
            problem_file = candidate_yamls[0]
        else:
            collector.add(f"{benchmark_dir}: missing required 'problem.yaml' file")
            return None

    # First pass: parse problem.yaml data to get property IDs
    data = load_yaml_file(problem_file, collector)
    if data is None:
        return None

    try:
        config = LogicalBenchmarkConfig.model_validate(data)
    except ValidationError as exc:
        for error in exc.errors():
            collector.add(format_pydantic_error(error, problem_file))
        return None

    instance_props = {
        p.identifier: p.is_artifact for p in config.logicalBenchmark.instance
    }

    # Validate instances folder if present and collect instance identifiers
    instances_dir = benchmark_dir / "instances"
    discovered_instance_ids: set[str] = set()
    if instances_dir.exists():
        if not instances_dir.is_dir():
            collector.add(f"{instances_dir}: 'instances' must be a directory")
        else:
            # Each instance can be a subdirectory (instances/<instance-id>/instance.yaml)
            # or a standalone YAML (instances/<instance-id>.yaml)
            for item in sorted(instances_dir.iterdir()):
                if item.name.startswith("."):
                    continue
                if item.is_dir() or (
                    item.is_file() and item.suffix in (".yaml", ".yml")
                ):
                    inst = validate_instance(item, instance_props, collector)
                    if inst is not None:
                        discovered_instance_ids.add(inst.identifier)

    # Validate logical benchmark file with collected instance_ids
    return validate_logical_benchmark_file(
        problem_file,
        collector,
        instance_ids=discovered_instance_ids or None,
    )


def validate_logical_benchmarks(
    benchmarks_root: Annotated[
        Path,
        typer.Option(
            "--benchmarks-root",
            help="Path to the directory containing logical benchmark folders or YAML files.",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = Path("./benchmarks"),
    file: Annotated[
        Path | None,
        typer.Option(
            "--file",
            help="Validate a single logical benchmark YAML file or benchmark folder instead of the whole root directory.",
            exists=True,
            file_okay=True,
            dir_okay=True,
            readable=True,
            resolve_path=True,
        ),
    ] = None,
    output_format: Annotated[
        Literal["json", "yaml", "table"] | None,
        typer.Option(
            "-o",
            "--output-format",
            help="Output format: 'json', 'yaml', or 'table' (default: table)",
        ),
    ] = None,
    output_file: Annotated[
        Path | None,
        typer.Option(
            "--output-file",
            help="Write results to a file. Format is inferred from the file extension (.json/.yaml) unless --output-format is also set.",
            dir_okay=False,
            writable=True,
        ),
    ] = None,
) -> None:
    """Validate logical benchmark definitions and instances.

    This command supports two modes:
    1. Directory mode: validate all benchmark folders / *.yaml files under --benchmarks-root (default: ./benchmarks)
    2. Single target mode: validate one file or directory via --file

    Checks performed:
    - Schema correctness for problem.yaml (required fields, valid structure)
    - Referential integrity (binding identifiers match the definition, property/metric
      references exist in the definition)
    - Instance YAML validation (schema correctness, parameter validity, artifact existence)

    Exit code is 0 on success, 1 if any target fails validation.
    """
    # NOTE: no verbose mode — errors are always shown in the table's Issues column
    if output_format:
        validate_output_format(
            output_format, allow_yaml=True, allow_csv=False, allow_table=True
        )

    # Collect targets to validate (can be benchmark directories or YAML files)
    targets: list[Path] = []
    if file is not None:
        targets = [file]
    else:
        # Look for benchmark directories first (directories with problem.yaml or instances)
        for item in sorted(benchmarks_root.iterdir()):
            if (item.is_dir() and not item.name.startswith(".")) or (
                item.is_file() and item.suffix in (".yaml", ".yml")
            ):
                targets.append(item)

        if not targets:
            console.print(
                f"[yellow]No benchmarks found in {benchmarks_root.resolve()}[/yellow]"
            )
            raise typer.Exit(code=0)

    all_results: list[dict[str, Any]] = []
    total_failed = 0

    for target in targets:
        collector = ValidationErrorCollector()
        if target.is_dir():
            validate_logical_benchmark_directory(target, collector)
        else:
            validate_logical_benchmark_file(target, collector)

        success = not collector.has_errors
        if not success:
            total_failed += 1

        result: dict[str, Any] = {
            "submission_path": str(target),
            "status": "success" if success else "failed",
            "errors": collector.errors,
            "warnings": [],
        }
        all_results.append(result)

    output_data = {"files": all_results}

    fmt = determine_output_format(output_format, output_file, default="table")

    if output_file:
        write_results_to_file(output_data, output_file, fmt)
    elif fmt in ("json", "yaml"):
        print_structured_results(output_data, fmt)
    else:
        _print_validation_table(all_results)

    if total_failed > 0:
        raise typer.Exit(code=1)
