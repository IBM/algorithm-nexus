# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Virtual environment management for benchmark validation."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

try:
    from rich.console import Console
except ImportError:
    print(
        "Error: CLI dependencies are not installed.\n"
        "Please install them with: pip install algorithm-nexus[cli]",
        file=sys.stderr,
    )
    sys.exit(1)

if TYPE_CHECKING:
    from algorithm_nexus.models import ExperimentEntry

console = Console()

# Number of trailing stderr lines to include when `ado` fails.
_ADO_STDERR_TAIL_LINES = 20


def create_temp_venv(system_site_packages: bool = True) -> Path:
    """Create a temporary virtual environment using uv.

    Args:
        system_site_packages: Whether to give access to system site packages (default: True)

    Returns:
        Path to the created virtual environment

    Raises:
        subprocess.CalledProcessError: If venv creation fails
        RuntimeError: If uv is not available
    """

    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="nexus-validate-")
    venv_path = Path(temp_dir) / "venv"

    try:
        console.print(f"  Creating virtual environment with uv: {venv_path}")
        cmd = ["uv", "venv", str(venv_path)]
        if system_site_packages:
            cmd.append("--system-site-packages")
        subprocess.run(  # noqa: S603
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )

        return venv_path

    except subprocess.CalledProcessError as e:
        # Clean up on failure
        shutil.rmtree(temp_dir, ignore_errors=True)
        console.print(f"[red]Error creating venv:[/red] {e.stderr}")
        raise


def install_packages(
    venv_path: Path,
    requirements: list[str],
    verbose: bool = False,
) -> bool:
    """Install packages in the virtual environment using uv.

    Args:
        venv_path: Path to the virtual environment
        requirements: List of package requirement specifiers
        verbose: Whether to show installation output

    Returns:
        True if installation succeeded, False otherwise

    Raises:
        RuntimeError: If uv is not available
    """
    if not requirements:
        return True

    python_path = venv_path / "bin" / "python"

    try:
        console.print(f"  Installing packages with uv: {', '.join(requirements)}")
        subprocess.run(  # noqa: S603
            # Forcing installing ado-core for extra safety. However,
            # ado-core is most probably already in the requirements of the benchmark
            # package.
            [  # noqa: S607
                "uv",
                "pip",
                "install",
                "--python",
                str(python_path),
                "ado-core",
                *requirements,
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        return True

    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error installing packages:[/red] {e.stderr}")
        return False


# Run with the venv's Python to dump every experiment in ado's actuator registry as
# JSON on the last line of stdout. Registry initialisation may print to stdout, so
# only the last line is parsed.
_LIST_EXPERIMENTS_SCRIPT = """
import json
from ado.modules.actuators.registry import ActuatorRegistry

registry = ActuatorRegistry.globalRegistry()
experiments = [
    {
        "actuatorIdentifier": actuator_id,
        "experimentIdentifier": experiment.identifier,
        "version": experiment.version,
        "targetProperties": [t.identifier for t in experiment.targetProperties],
    }
    for actuator_id in sorted(registry.actuatorIdentifierMap)
    for experiment in registry.catalogForActuatorIdentifier(actuator_id).experiments
]
print()
print(json.dumps(experiments))
"""


@dataclass(frozen=True)
class InstalledExperiment:
    """An experiment found in ado's actuator registry of a validation venv."""

    actuatorIdentifier: str
    experimentIdentifier: str
    version: str | None
    targetProperties: tuple[str, ...]


def list_installed_experiments(
    venv_path: Path,
    verbose: bool = False,
) -> tuple[list[InstalledExperiment] | None, list[str]]:
    """List the experiments, with their target properties, installed in a venv.

    Queries ado's actuator registry with the venv's Python interpreter.

    Returns:
        Tuple of (experiments or None on failure, list_of_error_strings)
    """
    python = venv_path / "bin" / "python"
    if not python.is_file():
        return None, ["Python interpreter not found in the virtual environment."]

    try:
        result = subprocess.run(  # noqa: S603
            [str(python), "-c", _LIST_EXPERIMENTS_SCRIPT],
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return None, ["Timed out waiting for ado's actuator registry"]
    except Exception as e:
        return None, [f"Failed to query ado's actuator registry: {e}"]

    if verbose:
        console.print(f"  [dim]ado registry stdout:[/dim]\n{result.stdout}")
        if result.stderr:
            console.print(f"  [dim]stderr:[/dim]\n{result.stderr}")

    if result.returncode != 0:
        # ado itself failed: report that rather than claiming every experiment is
        # missing, which would point at the wrong culprit (the benchmark package).
        details = (result.stderr.strip() or result.stdout.strip()).splitlines()
        tail = "\n".join(details[-_ADO_STDERR_TAIL_LINES:])
        message = (
            f"Querying ado's actuator registry failed with exit code "
            f"{result.returncode}; could not verify experiments. This usually "
            "indicates a problem with ado-core or its dependencies in the "
            "validation environment, not with the experiment package."
        )
        if tail:
            message += f"\n{tail}"
        return None, [message]

    lines = result.stdout.strip().splitlines()
    try:
        raw = json.loads(lines[-1]) if lines else None
        if not isinstance(raw, list):
            raise ValueError("expected a JSON list")
        experiments = [
            InstalledExperiment(
                actuatorIdentifier=e["actuatorIdentifier"],
                experimentIdentifier=e["experimentIdentifier"],
                version=e.get("version"),
                targetProperties=tuple(e.get("targetProperties") or ()),
            )
            for e in raw
        ]
    except (ValueError, KeyError, TypeError) as e:
        return None, [f"Could not parse ado's actuator registry output: {e}"]
    return experiments, []


def verify_experiments_installed(
    venv_path: Path,
    experiments: list[ExperimentEntry],
    verbose: bool = False,
) -> tuple[bool, list[str], list[InstalledExperiment] | None]:
    """Verify that the declared experiment IDs are discoverable after package install.

    Queries ado's actuator registry in the venv and checks that each declared
    experiment ID is registered. Only identifiers are checked, not versions.

    Args:
        venv_path: Path to the virtual environment
        experiments: Experiments (ExperimentEntry objects) to verify.
        verbose: Whether to show command output

    Returns:
        Tuple of (success, list_of_error_strings, installed experiments or None
        when the registry could not be queried)
    """
    installed, errors = list_installed_experiments(venv_path, verbose=verbose)
    if installed is None:
        return False, errors, None

    installed_ids = {e.experimentIdentifier for e in installed}
    errors = [
        f"Experiment '{e.experimentIdentifier}' not found after installing package "
        "(not registered with ado)"
        for e in experiments
        if e.experimentIdentifier not in installed_ids
    ]
    return not errors, errors, installed


def cleanup_venv(venv_path: Path) -> None:
    """Remove the temporary virtual environment.

    Args:
        venv_path: Path to the virtual environment to remove
    """
    try:
        # Remove the parent temp directory (which contains the venv)
        temp_dir = venv_path.parent
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception as e:
        console.print(
            f"[yellow]Warning:[/yellow] Failed to clean up venv at {venv_path}: {e}"
        )


# Made with Bob
