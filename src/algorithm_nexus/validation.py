# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Validation utilities for Nexus packages."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

try:
    from pydantic import ValidationError
except ImportError:
    print(
        "Error: CLI dependencies are not installed.\n"
        "Please install them with: pip install algorithm-nexus[cli]",
        file=sys.stderr,
    )
    sys.exit(1)

from algorithm_nexus.models import (
    AlgorithmNexusModelConfig,
    AlgorithmNexusPackageConfig,
)


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


def validate_benchmark_instances(
    model_dir: Path,
    collector: ValidationErrorCollector,
    registered_experiments: set[str],
) -> None:
    """Validate a model's benchmark_instances/ folder.

    Validates that each benchmark instance has a space.yaml file.
    Does not validate the contents of space.yaml as that is ADO's responsibility.
    """
    benchmark_instances_dir = model_dir / "benchmark_instances"

    # benchmark_instances/ is optional
    if not benchmark_instances_dir.exists():
        return

    if not benchmark_instances_dir.is_dir():
        collector.add(
            f"benchmark_instances must be a directory when present: {benchmark_instances_dir}"
        )
        return

    # Validate each benchmark instance folder
    for instance_dir in benchmark_instances_dir.iterdir():
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

    # Validate optional benchmark_instances/
    validate_benchmark_instances(model_dir, collector, registered_experiments)

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
