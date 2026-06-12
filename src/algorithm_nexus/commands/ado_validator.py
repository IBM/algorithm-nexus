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


def validate_space_yaml_syntax(space_yaml_path: Path) -> ValidationResult:
    """Validate space.yaml YAML syntax and basic structure using DiscoverySpaceConfiguration.

    Args:
        space_yaml_path: Path to space.yaml file

    Returns:
        ValidationResult with syntax validation results
    """
    errors = []
    warnings = []

    try:
        # Check if file exists
        if not space_yaml_path.exists():
            errors.append(f"File not found: {space_yaml_path}")
            return ValidationResult(
                success=False,
                instance_path=str(space_yaml_path.parent),
                errors=errors,
                warnings=warnings,
            )

        # Load and parse YAML
        space_config_dict = yaml.safe_load(space_yaml_path.read_text())

        # Validate using DiscoverySpaceConfiguration
        DiscoverySpaceConfiguration.model_validate(space_config_dict)

        # Check for optional but common sections
        if not space_config_dict.get("experiments"):
            warnings.append("No 'experiments' section found in space.yaml")
        elif len(space_config_dict.get("experiments", [])) == 0:
            warnings.append("'experiments' list is empty")

        if "entitySpace" not in space_config_dict:
            warnings.append("No 'entitySpace' section found in space.yaml")

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

    return ValidationResult(
        success=len(errors) == 0,
        instance_path=str(space_yaml_path.parent),
        errors=errors,
        warnings=warnings,
    )


def validate_with_ado(
    space_yaml_path: Path,
    venv_path: Path,
    dry_run: bool = True,
) -> ValidationResult:
    """Run ADO validation in isolated virtual environment.

    Args:
        space_yaml_path: Path to space.yaml file
        venv_path: Path to virtual environment with ADO installed
        dry_run: Whether to perform dry-run validation (default: True)

    Returns:
        ValidationResult with ADO validation results
    """
    errors = []
    warnings = []

    # First validate syntax
    syntax_result = validate_space_yaml_syntax(space_yaml_path)
    errors.extend(syntax_result.errors)
    warnings.extend(syntax_result.warnings)

    if syntax_result.errors:
        # Don't proceed with ADO validation if syntax is invalid
        return ValidationResult(
            success=False,
            instance_path=str(space_yaml_path.parent),
            errors=errors,
            warnings=warnings,
        )

    # Check if ADO binary is available in the venv
    ado_binary = venv_path / "bin" / "ado"
    if not ado_binary.is_file():
        errors.append(
            "ADO binary not found in the virtual environment. "
            "Make sure ado-core is installed."
        )
        return ValidationResult(
            success=False,
            instance_path=str(space_yaml_path.parent),
            errors=errors,
            warnings=warnings,
        )

    # Validate with ADO using dry-run mode
    try:
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
        instance_path=str(space_yaml_path.parent),
        errors=errors,
        warnings=warnings,
    )


# Made with Bob
