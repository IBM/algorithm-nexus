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
) -> None:
    """Validate nexus.yaml."""
    nexus_yaml_path = package_dir / "nexus.yaml"
    data = load_yaml_file(nexus_yaml_path, collector)
    if data is None:
        return

    try:
        NexusYAML.model_validate(data)
    except ValidationError as exc:
        for error in exc.errors():
            collector.add(format_pydantic_error(error, nexus_yaml_path))


def validate_model_yaml(model_dir: Path, collector: ValidationErrorCollector) -> None:
    """Validate a model's model.yaml file."""
    model_yaml_path = model_dir / "model.yaml"
    data = load_yaml_file(model_yaml_path, collector)
    if data is None:
        return

    try:
        ModelYAML.model_validate(data)
    except ValidationError as exc:
        for error in exc.errors():
            collector.add(format_pydantic_error(error, model_yaml_path))


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
) -> None:
    """Validate a single model directory structure and contents."""
    if not model_dir.is_dir():
        collector.add(f"Model path is not a directory: {model_dir}")
        return

    # Validate optional usage.md
    usage_md = model_dir / "usage.md"
    validate_optional_file(
        usage_md,
        collector,
        f"Optional model file missing for '{model_dir.name}': usage.md",
    )

    # Validate model.yaml
    validate_model_yaml(model_dir, collector)


def validate_package_directory(
    package_dir: Path, collector: ValidationErrorCollector
) -> None:
    """Validate the structure and contents of a Nexus package directory."""
    if not package_dir.is_dir():
        collector.add(f"Package path is not a directory: {package_dir}")
        return

    validate_nexus_yaml(package_dir, collector)

    # Validate optional skills directory
    skills_dir = package_dir / "skills"
    validate_optional_dir(
        skills_dir, collector, "Optional package directory missing: skills"
    )

    # Check if models directory exists
    models_dir = package_dir / "models"
    if not validate_optional_dir(
        models_dir, collector, "Optional package directory missing: models"
    ):
        return

    # Only validate model directories if models_dir exists
    for model_dir in models_dir.iterdir():
        validate_model_directory(model_dir, collector)
