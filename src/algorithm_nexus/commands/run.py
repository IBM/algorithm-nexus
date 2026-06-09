# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Run commands for Algorithm Nexus CLI."""

from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Annotated, Any

try:
    import typer
    import yaml
    from rich.console import Console
except ImportError:
    print(
        "Error: CLI dependencies are not installed.\n"
        "Please install them with: pip install algorithm-nexus[cli]",
        file=sys.stderr,
    )
    sys.exit(1)

from algorithm_nexus.commands.utils import strip_ansi_codes

console = Console()

# Random walk operation template as a dictionary constant
RANDOM_WALK_OPERATION_TEMPLATE = {
    "metadata": {
        "name": "randomwalk-all",
        "description": "Perform a random walk on all points in a space",
    },
    "spaces": ["<will be set by ado>"],
    "operation": {
        "module": {
            "operatorName": "random_walk",
            "operationType": "search",
        },
        "parameters": {
            "numberEntities": "all",
            "singleMeasurement": True,
            "samplerConfig": {
                "mode": "sequential",
                "samplerType": "generator",
            },
        },
    },
}


class BenchmarkManager:
    """Manages discovery and execution of benchmark instances from a GitHub PR."""

    def __init__(
        self,
        pr_url: str,
        execute: bool = True,
        remote_context_file: Path | None = None,
        context_file: Path | None = None,
    ):
        """Initialize the benchmark manager.

        Args:
            pr_url: GitHub Pull Request URL
            execute: Whether to execute benchmarks with ADO CLI
            remote_context_file: Path to remote execution context YAML file
            context_file: Path to ADO context YAML file (samplestore context)
        """
        self.pr_url = pr_url
        self.execute = execute
        self.remote_context_file = remote_context_file
        self.context_file = context_file
        self.repo_root = Path.cwd()
        self.temp_dir_obj = None

        if execute:
            # Check if ado CLI is available
            try:
                result = subprocess.run(  # noqa: S603
                    ["ado", "-h"],  # noqa: S607
                    capture_output=True,
                    check=False,
                )
                if not result.stdout and not result.stderr:
                    raise FileNotFoundError("ado command produced no output")
            except FileNotFoundError:
                console.print(
                    "[red]Error:[/red] ADO CLI is not installed or not in PATH.\n"
                    "Install it from: https://github.com/IBM/ado"
                )
                raise typer.Exit(code=1)

        if remote_context_file and not remote_context_file.exists():
            console.print(
                f"[red]Error:[/red] Remote context file not found: {remote_context_file}"
            )
            raise typer.Exit(code=1)

    def get_changed_files(self) -> list[str]:
        """Get list of changed files from the PR using gh CLI.

        Returns:
            List of changed file paths
        """
        try:
            result = subprocess.run(  # noqa: S603
                ["gh", "pr", "diff", self.pr_url, "--name-only"],  # noqa: S607
                capture_output=True,
                text=True,
                check=True,
            )
            return [line.strip() for line in result.stdout.split("\n") if line.strip()]
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error:[/red] Failed to fetch PR diff: {e}")
            console.print("Make sure 'gh' is installed and authenticated")
            raise typer.Exit(code=1)
        except FileNotFoundError:
            console.print("[red]Error:[/red] GitHub CLI (gh) is not installed")
            console.print("Install it from: https://cli.github.com/")
            raise typer.Exit(code=1)

    def _parse_instance_path(self, instance_path: Path) -> tuple[str, str, str]:
        """Parse benchmark instance path to extract package, model, and instance names.

        Args:
            instance_path: Path to benchmark instance directory

        Returns:
            Tuple of (package_name, model_name, instance_name)
            For package-level instances, model_name will be "base"

        Raises:
            ValueError: If the instance path format is invalid
        """
        # Parse instance path:
        # - Model-level: packages/<package>/models/<model>/benchmark_instances/<instance>
        # - Package-level: packages/<package>/benchmark_instances/<instance>
        parts = str(instance_path).split("/")

        if len(parts) < 2:
            raise ValueError(
                f"Invalid benchmark instance path format: {instance_path}. "
                "Expected: packages/<package>/benchmark_instances/<instance> or "
                "packages/<package>/models/<model>/benchmark_instances/<instance>"
            )

        package_name = parts[1]

        # Check if this is a package-level or model-level benchmark instance
        if len(parts) > 2 and parts[2] == "benchmark_instances":
            # Package-level: packages/<package>/benchmark_instances/<instance>
            if len(parts) < 4:
                raise ValueError(
                    f"Invalid package-level benchmark instance path: {instance_path}. "
                    "Expected: packages/<package>/benchmark_instances/<instance>"
                )
            model_name = "base"
            instance_name = parts[3]
        else:
            # Model-level: packages/<package>/models/<model>/benchmark_instances/<instance>
            if len(parts) < 6:
                raise ValueError(
                    f"Invalid model-level benchmark instance path: {instance_path}. "
                    "Expected: packages/<package>/models/<model>/benchmark_instances/<instance>"
                )
            model_name = parts[3]
            instance_name = parts[5]

        return package_name, model_name, instance_name

    def find_benchmark_instances(self, changed_files: list[str]) -> list[Path]:
        """Find benchmark instance directories from changed files.

        Args:
            changed_files: List of changed file paths

        Returns:
            List of unique benchmark instance directory paths
        """
        benchmark_dirs = set()

        for file_path in changed_files:
            if "benchmark_instances/" in file_path:
                parts = file_path.split("benchmark_instances/")
                if len(parts) >= 2:
                    instance_parts = parts[1].split("/")
                    if instance_parts:
                        instance_dir = (
                            f"{parts[0]}benchmark_instances/{instance_parts[0]}"
                        )
                        benchmark_dirs.add(Path(instance_dir))

        return sorted(benchmark_dirs)

    def checkout_pr_to_temp(self):
        """Clone the repository and checkout the PR code in a temporary directory."""
        try:
            self.temp_dir_obj = tempfile.TemporaryDirectory(prefix="pr_checkout_")
            temp_path = Path(self.temp_dir_obj.name)

            console.print(f"Creating temporary clone in {temp_path}")

            result = subprocess.run(  # noqa: S603
                ["git", "remote", "get-url", "origin"],  # noqa: S607
                capture_output=True,
                text=True,
                check=True,
                cwd=self.repo_root,
            )
            repo_url = result.stdout.strip()

            pr_number = self.pr_url.rstrip("/").split("/")[-1]

            console.print("Cloning repository...")
            subprocess.run(  # noqa: S603
                [  # noqa: S607
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    "--no-single-branch",
                    repo_url,
                    str(temp_path),
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            # Use gh CLI to checkout the PR - it handles fetching the PR ref
            console.print(f"Checking out PR #{pr_number} using gh CLI...")
            subprocess.run(  # noqa: S603
                ["gh", "pr", "checkout", pr_number],  # noqa: S607
                capture_output=True,
                text=True,
                check=True,
                cwd=temp_path,
            )

            self.repo_root = temp_path
            console.print("[green]✓[/green] Successfully checked out PR code")

        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error:[/red] Failed to checkout PR: {e}")
            if e.stderr:
                console.print(f"  {e.stderr}")
            self.cleanup_temp_dir()
            raise typer.Exit(code=1)

    def cleanup_temp_dir(self):
        """Clean up the temporary directory if it was created."""
        if self.temp_dir_obj:
            try:
                console.print("\nCleaning up temporary directory")
                self.temp_dir_obj.cleanup()
                self.temp_dir_obj = None
                console.print("[green]✓[/green] Temporary directory cleaned up")
            except Exception as e:
                console.print(
                    f"[yellow]Warning:[/yellow] Failed to clean up temporary directory: {e}"
                )

    def is_local_repo_on_pr_commit(self) -> bool:
        """Check if the local repository is on the same commit as the PR head.

        Returns:
            True if local repo is on PR commit, False otherwise
        """
        try:
            # Get PR head commit SHA
            pr_number = self.pr_url.rstrip("/").split("/")[-1]
            result = subprocess.run(  # noqa: S603
                [  # noqa: S607
                    "gh",
                    "pr",
                    "view",
                    pr_number,
                    "--json",
                    "headRefOid",
                    "--jq",
                    ".headRefOid",
                ],
                capture_output=True,
                text=True,
                check=True,
                cwd=self.repo_root,
            )
            pr_commit = result.stdout.strip()

            # Get current local commit SHA
            result = subprocess.run(  # noqa: S603
                ["git", "rev-parse", "HEAD"],  # noqa: S607
                capture_output=True,
                text=True,
                check=True,
                cwd=self.repo_root,
            )
            local_commit = result.stdout.strip()

            return pr_commit == local_commit
        except (subprocess.CalledProcessError, FileNotFoundError):
            # If we can't determine, assume they're different to be safe
            return False

    def get_benchmark_packages_for_instance(self, instance_path: Path) -> set[str]:
        """Get the benchmark packages required for a specific benchmark instance.

        Args:
            instance_path: Path to benchmark instance directory

        Returns:
            Set of requirement specifiers for benchmark packages
        """
        packages = set()

        try:
            repo_root = self.repo_root

            space_yaml_path = repo_root / instance_path / "space.yaml"
            if not space_yaml_path.exists():
                return packages

            with open(space_yaml_path) as f:
                space_config = yaml.safe_load(f)

            experiment_ids = set()
            if "experiments" in space_config:
                for exp in space_config["experiments"]:
                    if isinstance(exp, dict) and "experimentIdentifier" in exp:
                        experiment_ids.add(exp["experimentIdentifier"])

            if not experiment_ids:
                return packages

            current_path = repo_root / instance_path
            nexus_yaml_path = None

            while current_path != repo_root and current_path.parent != current_path:
                potential_nexus = current_path / "nexus.yaml"
                if potential_nexus.exists():
                    nexus_yaml_path = potential_nexus
                    break
                current_path = current_path.parent

            if not nexus_yaml_path:
                parts = instance_path.parts
                if len(parts) > 0 and parts[0] == "packages" and len(parts) > 1:
                    potential_nexus = repo_root / "packages" / parts[1] / "nexus.yaml"
                    if potential_nexus.exists():
                        nexus_yaml_path = potential_nexus

            if not nexus_yaml_path or not nexus_yaml_path.exists():
                return packages

            with open(nexus_yaml_path) as f:
                nexus_config = yaml.safe_load(f)

            if (
                "package" in nexus_config
                and "benchmark_packages" in nexus_config["package"]
            ):
                for bench_pkg in nexus_config["package"]["benchmark_packages"]:
                    if (
                        "experiments" in bench_pkg
                        and "requirement_specifier" in bench_pkg
                    ):
                        pkg_experiments = set(bench_pkg["experiments"])
                        if experiment_ids & pkg_experiments:
                            packages.add(bench_pkg["requirement_specifier"])

        except Exception as e:
            console.print(
                f"[yellow]Warning:[/yellow] Could not determine benchmark packages for {instance_path}: {e}"
            )

        return packages

    def execute_benchmark(self, instance_path: Path) -> dict[str, Any]:
        """Execute a benchmark instance using ADO CLI.

        Args:
            instance_path: Path to benchmark instance directory

        Returns:
            Execution result dictionary
        """
        result = {
            "instance_path": str(instance_path),
            "status": "unknown",
            "message": "",
            "space_id": None,
            "operation_id": None,
            "ray_job_id": None,
        }

        try:
            # Use repo_root which is set to either local or checked out directory
            space_yaml_path = self.repo_root / instance_path / "space.yaml"

            if not space_yaml_path.exists():
                raise FileNotFoundError(f"space.yaml not found in {instance_path}")

            console.print(f"  Creating ADO discoveryspace for: {instance_path}")
            space_id = self._create_discoveryspace(space_yaml_path, instance_path)
            result["space_id"] = space_id
            console.print(f"  [green]✓[/green] Successfully created space: {space_id}")

            console.print(f"  Creating operation for space: {space_id}")
            operation_result = self._create_operation(space_id, instance_path)
            result["operation_id"] = operation_result["operation_id"]
            result["ray_job_id"] = operation_result.get("ray_job_id")

            result["status"] = "success"
            message_parts = [
                f"Successfully created space {space_id} and operation {operation_result['operation_id']}"
            ]
            if result["ray_job_id"]:
                message_parts.append(f"Ray job ID: {result['ray_job_id']}")
            result["message"] = strip_ansi_codes(" | ".join(message_parts))

            console.print(
                f"  [green]✓[/green] Successfully created operation: {operation_result['operation_id'] or 'pending'}"
            )
            if result["ray_job_id"]:
                console.print(f"  [green]✓[/green] Ray job ID: {result['ray_job_id']}")

        except FileNotFoundError as e:
            result["status"] = "failed"
            result["message"] = f"File not found: {e}"
            console.print(f"  [red]✗[/red] Failed: {result['message']}")

        except subprocess.CalledProcessError as e:
            result["status"] = "failed"
            result["message"] = f"ADO CLI error: {e.stderr or str(e)}"
            console.print(f"  [red]✗[/red] Failed: {result['message']}")

        except Exception as e:
            result["status"] = "failed"
            result["message"] = f"Execution error: {e}"
            console.print(f"  [red]✗[/red] Failed: {result['message']}")

        return result

    def _create_discoveryspace(self, space_yaml_path: Path, instance_path: Path) -> str:
        """Create a discoveryspace using ado CLI.

        Args:
            space_yaml_path: Path to space.yaml file
            instance_path: Path to benchmark instance directory

        Returns:
            Created space identifier
        """
        with open(space_yaml_path) as f:
            space_config = yaml.safe_load(f)

        # Ensure metadata section exists
        if "metadata" not in space_config:
            space_config["metadata"] = {}

        # Generate descriptive name and description from instance path
        # Extract PR number from URL
        pr_number = self.pr_url.rstrip("/").split("/")[-1]

        # Parse instance path to get package, model, and instance names
        package_name, model_name, instance_name = self._parse_instance_path(
            instance_path
        )

        # Create descriptive name: space-pr123-package-model-instance
        space_name = f"space-pr{pr_number}-{package_name}-{model_name}-{instance_name}"
        space_description = f"Discovery space for benchmark instance from PR #{pr_number}: {package_name}/{model_name}/{instance_name}"

        # Update metadata with descriptive name and description
        space_config["metadata"]["name"] = space_name
        space_config["metadata"]["description"] = space_description

        # Add custom algorithm-nexus fields to metadata
        if "algorithm-nexus" not in space_config["metadata"]:
            space_config["metadata"]["algorithm-nexus"] = {}

        space_config["metadata"]["algorithm-nexus"].update(
            {
                "pr_url": self.pr_url,
                "instance_path": str(instance_path),
            }
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as tmp_file:
            yaml.dump(space_config, tmp_file)
            temp_space_path = tmp_file.name

        try:
            cmd = ["ado"]

            # Add context file if provided
            if self.context_file:
                cmd.extend(["--context", str(self.context_file)])

            cmd.extend(["create", "discoveryspace", "-f", temp_space_path])

            result = subprocess.run(  # noqa: S603
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                raise subprocess.CalledProcessError(
                    result.returncode, cmd, output=result.stdout, stderr=error_msg
                )

            combined_output = result.stdout + "\n" + result.stderr
            match = re.search(r"identifier[:\s]+(\S+)", combined_output)
            if match:
                return strip_ansi_codes(match.group(1))
            else:
                output_words = result.stdout.strip().split()
                if output_words:
                    return strip_ansi_codes(output_words[-1])
                else:
                    raise ValueError(
                        f"Could not extract space identifier from ADO output.\n"
                        f"Return code: {result.returncode}\n"
                        f"Stdout: {result.stdout[:300]}\n"
                        f"Stderr: {result.stderr[:300]}"
                    )
        finally:
            Path(temp_space_path).unlink(missing_ok=True)

    def _create_or_update_remote_config(
        self,
        benchmark_packages: set[str],
        base_config_path: Path | None = None,
        repo_root: Path | None = None,
    ) -> Path:
        """Create or update a remote configuration file with benchmark package dependencies.

        Args:
            benchmark_packages: Set of requirement specifiers for benchmark packages
            base_config_path: Optional base remote config to extend
            repo_root: Repository root to resolve relative paths (defaults to self.repo_root)

        Returns:
            Path to the created/updated remote config file
        """
        if repo_root is None:
            repo_root = self.repo_root
        if base_config_path and base_config_path.exists():
            with open(base_config_path) as f:
                remote_config = yaml.safe_load(f) or {}
        else:
            remote_config = {}

        if "packages" not in remote_config:
            remote_config["packages"] = {}

        if "fromPyPI" not in remote_config["packages"]:
            remote_config["packages"]["fromPyPI"] = []

        if "fromSource" not in remote_config["packages"]:
            remote_config["packages"]["fromSource"] = []

        existing_pypi_packages = set(remote_config["packages"]["fromPyPI"])
        existing_source_packages = set(remote_config["packages"]["fromSource"])

        for pkg in benchmark_packages:
            # Check if package is a local path (relative or absolute)
            pkg_path = Path(pkg)

            # Try to resolve relative to repo_root first
            if not pkg_path.is_absolute():
                pkg_path = repo_root / pkg_path

            # Check if the resolved path exists and is a valid package source
            if pkg_path.exists() and (
                pkg_path.is_dir() or pkg_path.suffix in [".whl", ".tar.gz", ".zip"]
            ):
                # Resolve to absolute path for local packages
                resolved_path = str(pkg_path.resolve())
                if resolved_path not in existing_source_packages:
                    remote_config["packages"]["fromSource"].append(resolved_path)
            else:
                # Treat as PyPI package
                if pkg not in existing_pypi_packages:
                    remote_config["packages"]["fromPyPI"].append(pkg)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, prefix="remote_config_"
        ) as tmp_file:
            yaml.dump(remote_config, tmp_file, default_flow_style=False)
            return Path(tmp_file.name)

    def _create_operation(
        self, space_id: str, instance_path: Path | None = None
    ) -> dict[str, str | None]:
        """Create and execute an operation using ado CLI.

        Args:
            space_id: Discovery space identifier
            instance_path: Optional path to benchmark instance (for package resolution)

        Returns:
            Dictionary with operation_id and ray_job_id (if remote execution)
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as tmp_file:
            # Use the template constant and make a deep copy to avoid modifying the original
            operation_config = copy.deepcopy(RANDOM_WALK_OPERATION_TEMPLATE)

            operation_config["spaces"] = [space_id]

            # Ensure metadata section exists
            if "metadata" not in operation_config:
                operation_config["metadata"] = {}

            # Generate descriptive name and description from instance path
            if instance_path:
                # Extract PR number from URL
                pr_number = self.pr_url.rstrip("/").split("/")[-1]

                # Parse instance path to get package, model, and instance names
                package_name, model_name, instance_name = self._parse_instance_path(
                    instance_path
                )

                # Create descriptive name: randomwalk-pr123-package-model-instance
                operation_name = f"randomwalk-pr{pr_number}-{package_name}-{model_name}-{instance_name}"
                operation_description = f"Random walk for benchmark instance from PR #{pr_number}: {package_name}/{model_name}/{instance_name}"

                # Update metadata with descriptive name and description
                operation_config["metadata"]["name"] = operation_name
                operation_config["metadata"]["description"] = operation_description

            # Add custom algorithm-nexus fields to metadata
            if "algorithm-nexus" not in operation_config["metadata"]:
                operation_config["metadata"]["algorithm-nexus"] = {}

            operation_config["metadata"]["algorithm-nexus"].update(
                {
                    "pr_url": self.pr_url,
                    "instance_path": str(instance_path) if instance_path else None,
                }
            )

            yaml.dump(operation_config, tmp_file)
            operation_config_path = tmp_file.name

        remote_config_to_use = self.remote_context_file
        temp_remote_config = None

        try:
            if self.remote_context_file and instance_path:
                benchmark_packages = self.get_benchmark_packages_for_instance(
                    instance_path
                )
                if benchmark_packages:
                    console.print(
                        f"  Installing benchmark packages in Ray environment: {', '.join(benchmark_packages)}"
                    )
                    temp_remote_config = self._create_or_update_remote_config(
                        benchmark_packages, self.remote_context_file, self.repo_root
                    )
                    remote_config_to_use = temp_remote_config

            cmd = ["ado"]

            # Add context file if provided
            if self.context_file:
                cmd.extend(["--context", str(self.context_file)])

            # The remote config goes right after the ado command (and context if present)
            if remote_config_to_use:
                cmd.extend(["--remote", str(remote_config_to_use)])

            cmd.extend(
                [
                    "create",
                    "operation",
                    "-f",
                    operation_config_path,
                ]
            )

            result = subprocess.run(  # noqa: S603
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            # Extract Ray job ID and operation identifier
            # For remote execution: Ray job ID (raysubmit_*) is available immediately
            # Operation ID is only available after execution completes

            combined_output = result.stdout + "\n" + result.stderr

            # Extract Ray job ID (starts with raysubmit_) for remote execution
            ray_job_id = None
            if remote_config_to_use:
                ray_match = re.search(r"(raysubmit_\w+)", combined_output)
                if ray_match:
                    ray_job_id = strip_ansi_codes(ray_match.group(1))

            # For local execution or completed remote execution, extract operation ID
            # Operation ID is available after "identifier" keyword
            operation_id = None
            op_match = re.search(r"identifier\s+(\S+)", combined_output)
            if op_match:
                candidate = strip_ansi_codes(op_match.group(1))
                # Only use as operation_id if it's not a raysubmit ID
                if not candidate.startswith("raysubmit_"):
                    operation_id = candidate

            # Fallback for local execution: use last word if no operation_id found
            if not operation_id and not ray_job_id:
                operation_id = strip_ansi_codes(result.stdout.strip().split()[-1])

            return {
                "operation_id": operation_id,
                "ray_job_id": ray_job_id,
            }

        finally:
            Path(operation_config_path).unlink(missing_ok=True)
            if temp_remote_config:
                temp_remote_config.unlink(missing_ok=True)

    def run(self) -> dict[str, Any]:
        """Main execution method.

        Returns:
            Dictionary with execution results
        """
        try:
            console.print("Analyzing PR for new or changed benchmark instances...")
            console.print(f"PR URL: {self.pr_url}")

            # Always check if we need to checkout PR code at the beginning
            if not self.is_local_repo_on_pr_commit():
                console.print("[yellow]Local repository is not on PR commit[/yellow]")
                console.print("Checking out PR code to temporary directory...")
                self.checkout_pr_to_temp()
            else:
                console.print(
                    "[green]✓[/green] Using local repository (already on PR commit)"
                )

            changed_files = self.get_changed_files()

            benchmark_instances = self.find_benchmark_instances(changed_files)

            if not benchmark_instances:
                console.print(
                    "[yellow]No new or changed benchmark instances found in this PR.[/yellow]"
                )
                return {"instances": []}

            console.print(f"Found {len(benchmark_instances)} benchmark instance(s):")

            results: dict[str, Any] = {
                "instances": [],
            }

            if self.execute:
                console.print("\nExecuting benchmarks with ADO CLI...")
                successful = 0
                failed = 0

                for instance_path in benchmark_instances:
                    console.print(f"\nProcessing: {instance_path}")
                    exec_result = self.execute_benchmark(instance_path)
                    results["instances"].append(exec_result)

                    if exec_result["status"] == "success":
                        successful += 1
                    else:
                        failed += 1

                console.print("\n" + "=" * 60)
                console.print("Execution Summary:")
                console.print(f"  Total: {len(benchmark_instances)}")
                console.print(f"  Successful: {successful}")
                console.print(f"  Failed: {failed}")
                console.print("=" * 60)

                results["summary"] = {"successful": successful, "failed": failed}
            else:
                for instance_path in benchmark_instances:
                    console.print(f"  {instance_path}")
                    results["instances"].append({"instance_path": str(instance_path)})

            return results
        finally:
            self.cleanup_temp_dir()


def run_benchmarks(
    pr: Annotated[
        str,
        typer.Option(
            "--pr",
            help="GitHub Pull Request URL (e.g., https://github.com/IBM/algorithm-nexus/pull/123)",
        ),
    ],
    remote: Annotated[
        Path | None,
        typer.Option(
            "--remote",
            help="Execute operations on remote Ray cluster using the specified context file",
        ),
    ] = None,
    context: Annotated[
        Path | None,
        typer.Option(
            "--context",
            help="Path to ADO context YAML file (samplestore context)",
        ),
    ] = None,
    list_only: Annotated[
        bool,
        typer.Option(
            "--list-only",
            help="List benchmarks without executing them",
        ),
    ] = False,
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            help="Output results to JSON file",
        ),
    ] = Path("output.json"),
) -> None:
    """Execute benchmarks from a GitHub Pull Request.

    Identifies new or changed benchmark instances in a PR and optionally
    executes them using the ADO CLI. When executing with --remote flag,
    automatically installs required benchmark packages in the Ray environment.

    The command automatically checks if the local repository is on the same
    commit as the PR. If not, it will checkout the PR code in a temporary
    directory.
    """
    try:
        manager = BenchmarkManager(
            pr_url=pr,
            execute=not list_only,
            remote_context_file=remote,
            context_file=context,
        )
        results = manager.run()

        with open(output, "w") as f:
            json.dump(results, f, indent=2)
        console.print(f"\nResults written to: {output}")

        if (
            not list_only
            and results.get("summary")
            and results["summary"]["failed"] > 0
        ):
            raise typer.Exit(code=1)

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise typer.Exit(code=130)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


# Made with Bob
