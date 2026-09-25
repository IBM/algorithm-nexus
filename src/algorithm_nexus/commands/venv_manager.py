# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Virtual environment management for benchmark validation."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from rich.console import Console
except ImportError:
    print(
        "Error: CLI dependencies are not installed.\n"
        "Please install them with: pip install algorithm-nexus[cli]",
        file=sys.stderr,
    )
    sys.exit(1)

console = Console()


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


def verify_experiments_installed(
    venv_path: Path,
    experiment_ids: list[str],
    verbose: bool = False,
) -> tuple[bool, list[str]]:
    """Verify that the declared experiment IDs are discoverable after package install.

    Runs `ado describe experiments` in the venv and checks that each declared
    experiment ID appears in the output.

    Args:
        venv_path: Path to the virtual environment
        experiment_ids: List of experiment identifiers to verify
        verbose: Whether to show command output

    Returns:
        Tuple of (success, list_of_error_strings)
    """
    ado_binary = venv_path / "bin" / "ado"
    if not ado_binary.is_file():
        return False, [
            "ADO binary not found in the virtual environment. Make sure ado-core is installed."
        ]

    try:
        result = subprocess.run(  # noqa: S603
            [str(ado_binary), "get", "experiments"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return False, ["Timed out waiting for `ado get experiments`"]
    except Exception as e:
        return False, [f"Failed to run `ado get experiments`: {e}"]

    if verbose:
        console.print(f"  [dim]ado get experiments stdout:[/dim]\n{result.stdout}")
        if result.stderr:
            console.print(f"  [dim]stderr:[/dim]\n{result.stderr}")

    output = result.stdout + result.stderr
    errors = [
        f"Experiment '{exp_id}' not found after installing package "
        f"(not listed by `ado get experiments`)"
        for exp_id in experiment_ids
        if exp_id not in output
    ]

    return len(errors) == 0, errors


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
