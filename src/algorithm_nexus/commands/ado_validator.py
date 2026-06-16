# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""ADO validation for benchmark instances."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

try:
    from orchestrator.core.discoveryspace.config import DiscoverySpaceConfiguration
    from pydantic import ValidationError
    from rich.console import Console
except ImportError:
    print(
        "Error: CLI dependencies are not installed.\n"
        "Please install them with: pip install algorithm-nexus[cli]",
        file=sys.stderr,
    )
    sys.exit(1)

from algorithm_nexus.models import ValidationResult

console = Console()


def validate_space_yaml_syntax(base_path: Path, instance_path: str) -> ValidationResult:
    """Validate space.yaml YAML syntax and basic structure using DiscoverySpaceConfiguration.

    Args:
        base_path: Base path (e.g., repo root or temp directory)
        instance_path: Relative path to the benchmark instance from base_path

    Returns:
        ValidationResult with syntax validation results
    """
    errors = []
    warnings = []

    # Construct full path to space.yaml
    space_yaml_path = base_path / instance_path / "space.yaml"

    # Check if file exists
    if not space_yaml_path.is_file():
        errors.append(f"File not found: {space_yaml_path}")
        return ValidationResult(
            success=False,
            instance_path=instance_path,
            errors=errors,
            warnings=warnings,
        )

    space_config = None
    try:
        # Load and parse YAML
        space_config_dict = yaml.safe_load(space_yaml_path.read_text())

        # Validate using DiscoverySpaceConfiguration
        space_config = DiscoverySpaceConfiguration.model_validate(space_config_dict)

    except yaml.YAMLError as e:
        errors.append(f"Invalid YAML syntax: {e}")
    except ValidationError as e:
        # Extract validation errors from Pydantic
        for error in e.errors():
            loc = " -> ".join(str(x) for x in error["loc"])
            msg = error["msg"]
            errors.append(f"Validation error at {loc}: {msg}")
    except Exception as e:
        errors.append(f"Unexpected error reading space.yaml: {e}")

    # Check for optional but common sections using the validated model
    if space_config:
        space_config = space_config.convert_experiments_to_reference_list()
        if not space_config.experiments or len(space_config.experiments) == 0:
            warnings.append("No 'experiments' section found in space.yaml")

        if not space_config.entitySpace:
            warnings.append("No 'entitySpace' section found in space.yaml")

    return ValidationResult(
        success=len(errors) == 0,
        instance_path=instance_path,
        errors=errors,
        warnings=warnings,
    )


def validate_with_ado(
    base_path: Path,
    instance_path: str,
    venv_path: Path,
) -> ValidationResult:
    """Run ADO validation in isolated virtual environment.

    Args:
        base_path: Base path (e.g., repo root or temp directory)
        instance_path: Relative path to the benchmark instance from base_path
        venv_path: Path to virtual environment with ADO installed

    Returns:
        ValidationResult with ADO validation results
    """
    # First validate syntax
    syntax_result = validate_space_yaml_syntax(base_path, instance_path)

    if syntax_result.errors:
        # Don't proceed with ADO validation if syntax is invalid
        return syntax_result

    # Start with syntax warnings for ADO validation
    errors = []
    warnings = syntax_result.warnings.copy()

    # Check if ADO binary is available in the venv
    ado_binary = venv_path / "bin" / "ado"
    if not ado_binary.is_file():
        errors.append(
            "ADO binary not found in the virtual environment. "
            "Make sure ado-core is installed."
        )
        return ValidationResult(
            success=False,
            instance_path=instance_path,
            errors=errors,
            warnings=warnings,
        )

    # Validate with ADO using dry-run mode
    try:
        # Construct full path to space.yaml
        space_yaml_path = base_path / instance_path / "space.yaml"

        # Use ado create space with --dry-run flag
        # Run from the benchmark instance directory to support relative paths in space.yaml
        result = subprocess.run(  # noqa: S603
            [
                str(ado_binary),
                "create",
                "space",
                "-f",
                str(space_yaml_path),
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,  # 30 second timeout
            cwd=space_yaml_path.parent,  # Run from benchmark instance directory
        )

        if result.returncode != 0:
            # Parse error message for more details
            error_msg = (
                result.stderr.strip() if result.stderr else result.stdout.strip()
            )
            errors.append(f"ADO validation failed: {error_msg}")

    except subprocess.TimeoutExpired:
        errors.append("ADO validation timed out after 30 seconds")
    except Exception as e:
        errors.append(f"Failed to run ADO validation: {e}")

    return ValidationResult(
        success=len(errors) == 0,
        instance_path=instance_path,
        errors=errors,
        warnings=warnings,
    )


# Made with Bob
