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


def run_in_venv(
    venv_path: Path,
    command: list[str],
    capture_output: bool = True,
) -> subprocess.CompletedProcess:
    """Execute a command in the virtual environment context.

    Args:
        venv_path: Path to the virtual environment
        command: Command to execute (without python prefix)
        capture_output: Whether to capture stdout/stderr

    Returns:
        CompletedProcess instance with execution results
    """
    python_path = venv_path / "bin" / "python"
    full_command = [str(python_path), *command]

    return subprocess.run(  # noqa: S603
        full_command,
        capture_output=capture_output,
        text=True,
        check=False,
    )


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
