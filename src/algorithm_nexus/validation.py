# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Validation utilities for Nexus packages."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from algorithm_nexus.models import ModelYAML, NexusYAML


class ValidationErrorCollector:
    """Collects validation errors during package validation."""

    def __init__(self) -> None:
        """Initialize the error collector."""
        self.errors: list[str] = []

    def add(self, message: str) -> None:
        """Add a single error message."""
        self.errors.append(message)

    def extend(self, messages: list[str]) -> None:
        """Add multiple error messages."""
        self.errors.extend(messages)

    @property
    def has_errors(self) -> bool:
        """Check if any errors have been collected."""
        return bool(self.errors)

    def __str__(self) -> str:
        """Format errors as a bulleted list."""
        return "\n".join(f"[red]✗[/red] {error}" for error in self.errors)


def load_yaml_file(
    path: Path, collector: ValidationErrorCollector
) -> dict[str, Any] | list[Any] | None:
    """Load and parse a YAML file, collecting any errors."""
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except FileNotFoundError:
        collector.add(f"Missing YAML file: {path}")
        return None
    except yaml.YAMLError as exc:
        collector.add(f"Invalid YAML syntax in {path}: {exc}")
        return None

    if data is None:
        collector.add(f"YAML file is empty: {path}")
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
) -> tuple[NexusYAML | None, list[str]]:
    """Validate nexus.yaml and return the config and model names."""
    nexus_yaml_path = package_dir / "nexus.yaml"
    data = load_yaml_file(nexus_yaml_path, collector)
    if data is None:
        return None, []

    if not isinstance(data, dict):
        collector.add(
            f"{nexus_yaml_path} must contain a YAML mapping at the top level."
        )
        return None, []

    try:
        nexus_config = NexusYAML.model_validate(data)
        model_names = nexus_config.models or []
        return nexus_config, model_names
    except ValidationError as exc:
        for error in exc.errors():
            collector.add(format_pydantic_error(error, nexus_yaml_path))
        return None, []


def validate_model_yaml(
    model_dir: Path, collector: ValidationErrorCollector, nexus_config: NexusYAML | None
) -> None:
    """Validate a model's model.yaml file."""
    model_yaml_path = model_dir / "model.yaml"
    data = load_yaml_file(model_yaml_path, collector)
    if data is None:
        return

    if not isinstance(data, dict):
        collector.add(
            f"{model_yaml_path} must contain a YAML mapping at the top level."
        )
        return

    try:
        ModelYAML.model_validate(data)
    except ValidationError as exc:
        for error in exc.errors():
            collector.add(format_pydantic_error(error, model_yaml_path))


def validate_path_is_file(
    path: Path, collector: ValidationErrorCollector, context: str
) -> bool:
    """Validate that path is a file when it exists. Returns True if valid or doesn't exist."""
    if path.exists() and not path.is_file():
        collector.add(f"{context} must be a file when present: {path}")
        return False
    return True


def validate_path_is_dir(
    path: Path, collector: ValidationErrorCollector, context: str
) -> bool:
    """Validate that path is a directory when it exists. Returns True if valid or doesn't exist."""
    if path.exists() and not path.is_dir():
        collector.add(f"{context} must be a directory when present: {path}")
        return False
    return True


def validate_model_directory(
    model_dir: Path,
    collector: ValidationErrorCollector,
    nexus_config: NexusYAML | None,
) -> None:
    """Validate a single model directory structure and contents."""
    if not model_dir.is_dir():
        collector.add(f"Declared model directory is missing: {model_dir}")
        return

    # Validate required tests directory
    tests_dir = model_dir / "tests"
    if not tests_dir.is_dir():
        collector.add(f"Missing required tests directory: {tests_dir}")

    # Validate optional files/directories
    usage_md = model_dir / "usage.md"
    validate_path_is_file(usage_md, collector, "usage.md")

    benchmarks_dir = model_dir / "benchmarks"
    validate_path_is_dir(benchmarks_dir, collector, "benchmarks")

    # Validate model.yaml
    validate_model_yaml(model_dir, collector, nexus_config)


def check_undeclared_models(
    models_dir: Path,
    declared_model_names: list[str],
    collector: ValidationErrorCollector,
) -> None:
    """Check for model directories that aren't declared in nexus.yaml."""
    for child in models_dir.iterdir():
        if child.is_dir() and child.name not in declared_model_names:
            collector.add(f"Undeclared model directory found under models/: {child}")


def validate_package_directory(
    package_dir: Path, collector: ValidationErrorCollector
) -> None:
    """Validate the structure and contents of a Nexus package directory."""
    if not package_dir.is_dir():
        collector.add(f"Package path is not a directory: {package_dir}")
        return

    nexus_config, model_names = validate_nexus_yaml(package_dir, collector)

    # Validate optional AGENTS.md
    agents_md = package_dir / "AGENTS.md"
    validate_path_is_file(agents_md, collector, "AGENTS.md")

    # Handle case where no models are declared
    # Only validate models directory if there are models declared
    if not model_names:
        return

    models_dir = package_dir / "models"
    if not models_dir.is_dir():
        collector.add(f"Missing required models directory: {models_dir}")
        return

    # Validate each declared model
    for model_name in model_names:
        model_dir = models_dir / model_name
        validate_model_directory(model_dir, collector, nexus_config)

    # Check for undeclared models
    check_undeclared_models(models_dir, model_names, collector)
