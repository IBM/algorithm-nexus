# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Run commands for Algorithm Nexus CLI."""

from __future__ import annotations

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
    from orchestrator.core.discoveryspace.config import DiscoverySpaceConfiguration
    from orchestrator.core.operation.config import (
        ConfigurationMetadata,
        DiscoveryOperationConfiguration,
        DiscoveryOperationEnum,
        DiscoveryOperationResourceConfiguration,
        OperatorReference,
    )
    from orchestrator.core.remotecontext.config import (
        PackageConfiguration,
        RemoteExecutionContext,
    )
    from orchestrator.modules.operators.randomwalk import (
        BaseSamplerConfiguration,
        RandomWalkParameters,
    )
    from orchestrator.utilities.output import pydantic_model_as_yaml
    from rich.console import Console
except ImportError:
    print(
        "Error: CLI dependencies are not installed.\n"
        "Please install them with: pip install algorithm-nexus[cli]",
        file=sys.stderr,
    )
    sys.exit(1)

from algorithm_nexus.commands.utils import strip_ansi_codes
from algorithm_nexus.models import (
    AlgorithmNexusPackageConfig,
    BenchmarkExecutionResult,
)

console = Console()
console_err = Console(stderr=True)


# Random walk operation template using DiscoveryOperationResourceConfiguration
def create_random_walk_operation_config(
    space_id: str,
    metadata_name: str = "randomwalk-all",
    metadata_description: str = "Perform a random walk on all points in a space",
    custom_metadata: dict[str, Any] | None = None,
) -> DiscoveryOperationResourceConfiguration:
    """Create a random walk operation configuration.

    Args:
        space_id: The discovery space identifier
        metadata_name: Name for the operation metadata
        metadata_description: Description for the operation metadata
        custom_metadata: Additional custom metadata fields

    Returns:
        DiscoveryOperationResourceConfiguration object
    """
    # Build metadata with custom fields
    labels = {}
    if custom_metadata:
        labels.update(custom_metadata)
    metadata = ConfigurationMetadata(
        name=metadata_name,
        description=metadata_description,
        labels=labels or None,
    )

    operation = DiscoveryOperationConfiguration(
        module=OperatorReference(
            operatorName="random_walk",
            operationType=DiscoveryOperationEnum.SEARCH,
        ),
        parameters=RandomWalkParameters(
            numberEntities="all",
            singleMeasurement=True,
            samplerConfig=BaseSamplerConfiguration(
                samplerType="generator",
                mode="sequential",
            ),
        ),
    )

    return DiscoveryOperationResourceConfiguration(
        metadata=metadata,
        spaces=[space_id],
        operation=operation,
        actuatorConfigurationIdentifiers=[],
    )


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
            console_err.print(f"[red]Error:[/red] Failed to fetch PR diff: {e}")
            console_err.print("Make sure 'gh' is installed and authenticated")
            raise typer.Exit(code=1)
        except FileNotFoundError:
            console_err.print("[red]Error:[/red] GitHub CLI (gh) is not installed")
            console_err.print("Install it from: https://cli.github.com/")
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
        # Parse instance path using regex:
        # - Model-level: packages/<package>/models/<model>/benchmark_instances/<instance>
        # - Package-level: packages/<package>/benchmark_instances/<instance>
        import re

        path_str = str(instance_path)

        # Try model-level pattern first
        model_pattern = r"^packages/([^/]+)/models/([^/]+)/benchmark_instances/([^/]+)$"
        match = re.match(model_pattern, path_str)
        if match:
            package_name, model_name, instance_name = match.groups()
            return package_name, model_name, instance_name

        # Try package-level pattern
        package_pattern = r"^packages/([^/]+)/benchmark_instances/([^/]+)$"
        match = re.match(package_pattern, path_str)
        if match:
            package_name, instance_name = match.groups()
            model_name = "base"
            return package_name, model_name, instance_name

        # If neither pattern matches, raise an error
        raise ValueError(
            f"Invalid benchmark instance path format: {instance_path}. "
            "Expected: packages/<package>/benchmark_instances/<instance> or "
            "packages/<package>/models/<model>/benchmark_instances/<instance>"
        )

    def find_benchmark_instances(self, changed_files: list[str]) -> list[Path]:
        """Find benchmark instance directories from changed files.

        Args:
            changed_files: List of changed file paths

        Returns:
            List of unique benchmark instance directory paths
        """
        benchmark_dirs = set()

        for file_path in changed_files:
            path = Path(file_path)
            if "benchmark_instances" in path.parts:
                # Find the index of 'benchmark_instances' in the path parts
                bench_idx = path.parts.index("benchmark_instances")
                # Ensure there's at least one part after 'benchmark_instances'
                if bench_idx + 1 < len(path.parts):
                    # Reconstruct path up to and including the first directory after 'benchmark_instances'
                    instance_dir = Path(*path.parts[: bench_idx + 2])
                    benchmark_dirs.add(instance_dir)

        return sorted(benchmark_dirs)

    def checkout_pr_to_temp(self):
        """Clone the repository and checkout the PR code in a temporary directory."""
        try:
            self.temp_dir_obj = tempfile.TemporaryDirectory(prefix="pr_checkout_")
            temp_path = Path(self.temp_dir_obj.name)

            console.print(f"Creating temporary clone in {temp_path}")

            # Use gh CLI to clone the repo directly from the PR URL
            console.print("Cloning repository using gh CLI...")
            subprocess.run(  # noqa: S603
                ["gh", "repo", "clone", self.pr_url, str(temp_path)],  # noqa: S607
                capture_output=True,
                text=True,
                check=True,
            )

            # Use gh CLI to checkout the PR using the URL
            console.print("Checking out PR using gh CLI...")
            subprocess.run(  # noqa: S603
                ["gh", "pr", "checkout", self.pr_url],  # noqa: S607
                capture_output=True,
                text=True,
                check=True,
                cwd=temp_path,
            )

            self.repo_root = temp_path
            console.print("[green]✓[/green] Successfully checked out PR code")

        except subprocess.CalledProcessError as e:
            console_err.print(f"[red]Error:[/red] Failed to checkout PR: {e}")
            if e.stderr:
                console_err.print(f"  {e.stderr}")
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
                console_err.print(
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
            if not space_yaml_path.is_file():
                return set()

            # Load space configuration using DiscoverySpaceConfiguration
            space_config_dict = yaml.safe_load(space_yaml_path.read_text())
            space_config = DiscoverySpaceConfiguration.model_validate(space_config_dict)

            # Extract experiment identifiers
            # Convert experiments to reference list for easier processing
            space_config_with_refs = (
                space_config.convert_experiments_to_reference_list()
            )

            if not space_config_with_refs.experiments:
                return set()

            # After conversion, experiments is a list of ExperimentReference
            experiment_ids: set[str] = {
                exp_ref.experimentIdentifier  # type: ignore[union-attr]
                for exp_ref in space_config_with_refs.experiments  # type: ignore[union-attr]
            }

            current_path = repo_root / instance_path
            nexus_yaml_path = None

            # Find the deepest nexus.yaml file up to repo_root
            for parent in [current_path, *current_path.parents]:
                if parent == repo_root.parent:
                    break
                potential_nexus = parent / "nexus.yaml"
                if potential_nexus.is_file():
                    nexus_yaml_path = potential_nexus
                    break

            if not nexus_yaml_path:
                parts = instance_path.parts
                if len(parts) > 0 and parts[0] == "packages" and len(parts) > 1:
                    potential_nexus = repo_root / "packages" / parts[1] / "nexus.yaml"
                    if potential_nexus.exists():
                        nexus_yaml_path = potential_nexus

            if not nexus_yaml_path or not nexus_yaml_path.exists():
                return set()

            # Load nexus config using AlgorithmNexusPackageConfig
            nexus_config_dict = yaml.safe_load(nexus_yaml_path.read_text())
            nexus_config = AlgorithmNexusPackageConfig.model_validate(nexus_config_dict)

            if nexus_config.package.benchmark_packages:
                for bench_pkg in nexus_config.package.benchmark_packages:
                    pkg_experiments = set(bench_pkg.experiments)
                    if experiment_ids & pkg_experiments:
                        packages.add(bench_pkg.requirement_specifier)

        except Exception as e:
            console_err.print(
                f"[yellow]Warning:[/yellow] Could not determine benchmark packages for {instance_path}: {e}"
            )
            return set()

        return packages

    def execute_benchmark(self, instance_path: Path) -> BenchmarkExecutionResult:
        """Execute a benchmark instance using ADO CLI.

        Args:
            instance_path: Path to benchmark instance directory

        Returns:
            Execution result
        """
        result = BenchmarkExecutionResult(instance_path=str(instance_path))

        # Prepare remote config once for this benchmark instance
        remote_config_for_space = None
        remote_config_for_operation = None
        temp_remote_configs = []

        try:
            # Use repo_root which is set to either local or checked out directory
            space_yaml_path = self.repo_root / instance_path / "space.yaml"

            if not space_yaml_path.is_file():
                raise FileNotFoundError(f"space.yaml not found in {instance_path}")

            # If in remote mode, create remote configs with benchmark packages
            if self.remote_context_file:
                benchmark_packages = self.get_benchmark_packages_for_instance(
                    instance_path
                )

                if benchmark_packages:
                    console.print(
                        f"  Installing benchmark packages in Ray environment: {', '.join(benchmark_packages)}"
                    )
                    # Create base remote config with benchmark packages
                    base_remote_config = self._create_or_update_remote_config(
                        benchmark_packages, self.remote_context_file, self.repo_root
                    )
                    temp_remote_configs.append(base_remote_config)

                    # Load base config for space creation using RemoteExecutionContext
                    base_config_dict = (
                        yaml.safe_load(base_remote_config.read_text()) or {}
                    )
                    base_remote_context = RemoteExecutionContext.model_validate(
                        base_config_dict
                    )

                    # Use base config for operation (without wait: true override)
                    remote_config_for_operation = base_remote_config
                else:
                    # No benchmark packages, use original config
                    base_config_dict = (
                        yaml.safe_load(self.remote_context_file.read_text()) or {}
                    )
                    base_remote_context = RemoteExecutionContext.model_validate(
                        base_config_dict
                    )

                    # Use original config for operation
                    remote_config_for_operation = self.remote_context_file

                # Create temporary config for space creation with wait: true
                # Create a new RemoteExecutionContext with wait=True
                space_remote_context = RemoteExecutionContext(
                    executionType=base_remote_context.executionType,
                    packages=base_remote_context.packages,
                    wait=True,
                    envVars=base_remote_context.envVars,
                    additionalFiles=base_remote_context.additionalFiles,
                )

                with tempfile.NamedTemporaryFile(
                    mode="w",
                    suffix=".yaml",
                    delete=False,
                    prefix="remote_config_space_",
                ) as tmp_file:
                    remote_config_for_space = Path(tmp_file.name)
                    remote_config_for_space.write_text(
                        pydantic_model_as_yaml(space_remote_context)
                    )
                    temp_remote_configs.append(remote_config_for_space)

            console.print(f"  Creating ADO discoveryspace for: {instance_path}")
            space_id = self._create_discoveryspace(
                space_yaml_path, instance_path, remote_config_for_space
            )
            result.space_id = space_id
            console.print(f"  [green]✓[/green] Successfully created space: {space_id}")

            console.print(f"  Creating operation for space: {space_id}")
            operation_result = self._create_operation(
                space_id, instance_path, remote_config_for_operation
            )
            result.operation_id = operation_result["operation_id"]
            result.ray_job_id = operation_result.get("ray_job_id")

            # Set status to "started" if Ray job was successfully started, otherwise "success"
            if result.ray_job_id:
                result.status = "started"
                message_parts = [
                    f"Successfully started on Ray cluster with job ID: {result.ray_job_id}"
                ]
                if result.operation_id:
                    message_parts.append(f"Operation ID: {result.operation_id}")
                message_parts.append(f"Space ID: {space_id}")
            else:
                result.status = "success"
                message_parts = [
                    f"Successfully created space {space_id} and operation {operation_result['operation_id']}"
                ]
            result.message = strip_ansi_codes(" | ".join(message_parts))

            console.print(
                f"  [green]✓[/green] Successfully created operation: {operation_result['operation_id'] or 'pending'}"
            )
            if result.ray_job_id:
                console.print(f"  [green]✓[/green] Ray job ID: {result.ray_job_id}")

        except FileNotFoundError as e:
            result.status = "failed"
            result.message = f"File not found: {e}"
            console_err.print(f"  [red]✗[/red] Failed: {result.message}")

        except subprocess.CalledProcessError as e:
            result.status = "failed"
            result.message = f"ADO CLI error: {strip_ansi_codes(e.stderr or str(e))}"
            console_err.print(f"  [red]✗[/red] Failed: {result.message}")

        except Exception as e:
            result.status = "failed"
            result.message = f"Execution error: {strip_ansi_codes(str(e))}"
            console_err.print(f"  [red]✗[/red] Failed: {result.message}")

        finally:
            # Clean up temporary remote config files
            for temp_config in temp_remote_configs:
                temp_config.unlink(missing_ok=True)

        return result

    def _create_discoveryspace(
        self,
        space_yaml_path: Path,
        instance_path: Path,
        remote_config: Path | None = None,
    ) -> str:
        """Create a discoveryspace using ado CLI.

        Args:
            space_yaml_path: Path to space.yaml file
            instance_path: Path to benchmark instance directory
            remote_config: Optional path to remote configuration file (with wait: true for space creation)

        Returns:
            Created space identifier
        """

        # Load the space configuration from YAML
        space_config_dict = yaml.safe_load(space_yaml_path.read_text())

        # Parse the configuration using DiscoverySpaceConfiguration
        space_config = DiscoverySpaceConfiguration.model_validate(space_config_dict)

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

        # Build custom labels with algorithm-nexus fields
        labels = space_config.metadata.labels or {}
        labels["algorithm-nexus.pr_url"] = self.pr_url
        labels["algorithm-nexus.instance_path"] = str(instance_path)

        # Update metadata with descriptive name, description, and labels
        space_config.metadata = ConfigurationMetadata(
            name=space_name,
            description=space_description,
            labels=labels,
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=True
        ) as tmp_file:
            temp_space_path = tmp_file.name
            Path(temp_space_path).write_text(pydantic_model_as_yaml(space_config))

            cmd = ["ado"]

            # Add context file if provided
            if self.context_file:
                cmd.extend(["--context", str(self.context_file)])

            # Add remote flag if in remote mode
            if remote_config:
                cmd.extend(["--remote", str(remote_config)])

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

        # Load existing remote config (base_config_path existence is validated by CLI)
        if not base_config_path:
            raise ValueError(
                "base_config_path must be provided with a valid RemoteExecutionContext configuration"
            )

        remote_config_dict = yaml.safe_load(base_config_path.read_text()) or {}
        remote_config = RemoteExecutionContext.model_validate(remote_config_dict)

        # Get existing packages
        existing_pypi_packages = set(remote_config.packages.fromPyPI)
        existing_source_packages = set(remote_config.packages.fromSource)

        # Process benchmark packages
        new_pypi_packages = list(existing_pypi_packages)
        new_source_packages = list(existing_source_packages)

        for pkg in benchmark_packages:
            # Check if package is a GitHub URL
            if pkg.startswith(
                ("https://github.com/", "http://github.com/", "git@github.com:")
            ):
                # Add git+ prefix for GitHub URLs if not already present
                git_url = pkg if pkg.startswith("git+") else f"git+{pkg}"
                if git_url not in existing_pypi_packages:
                    new_pypi_packages.append(git_url)
            else:
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
                        new_source_packages.append(resolved_path)
                else:
                    # Treat as PyPI package
                    if pkg not in existing_pypi_packages:
                        new_pypi_packages.append(pkg)

        # Update packages configuration
        remote_config.packages = PackageConfiguration(
            fromPyPI=new_pypi_packages,
            fromSource=new_source_packages,
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, prefix="remote_config_"
        ) as tmp_file:
            temp_path = Path(tmp_file.name)
            temp_path.write_text(pydantic_model_as_yaml(remote_config))
            return temp_path

    def _create_operation(
        self,
        space_id: str,
        instance_path: Path | None = None,
        remote_config: Path | None = None,
    ) -> dict[str, str | None]:
        """Create and execute an operation using ado CLI.

        Args:
            space_id: Discovery space identifier
            instance_path: Optional path to benchmark instance (for package resolution)
            remote_config: Optional path to remote configuration file

        Returns:
            Dictionary with operation_id and ray_job_id (if remote execution)
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=True
        ) as tmp_file:
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
            else:
                operation_name = "randomwalk-all"
                operation_description = "Perform a random walk on all points in a space"

            # Create custom metadata with algorithm-nexus fields
            custom_metadata = {
                "algorithm-nexus.pr_url": self.pr_url,
                "algorithm-nexus.instance_path": str(instance_path)
                if instance_path
                else "",
            }

            # Create operation config using the factory function
            operation_config = create_random_walk_operation_config(
                space_id=space_id,
                metadata_name=operation_name,
                metadata_description=operation_description,
                custom_metadata=custom_metadata,
            )

            operation_config_path = tmp_file.name
            Path(operation_config_path).write_text(
                pydantic_model_as_yaml(operation_config)
            )

            cmd = ["ado"]

            # Add context file if provided
            if self.context_file:
                cmd.extend(["--context", str(self.context_file)])

            # The remote config goes right after the ado command (and context if present)
            if remote_config:
                cmd.extend(["--remote", str(remote_config)])

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
            if remote_config:
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
                    results["instances"].append(exec_result.model_dump())

                    if exec_result.status == "success":
                        successful += 1
                    else:
                        failed += 1

                console.print("\n" + "=" * 60)
                console.print("Execution Summary:")
                console.print(f"  Total: {len(benchmark_instances)}")
                console.print(f"  Successful: {successful}")
                console.print(f"  Failed: {failed}")
                console.print("=" * 60)
            else:
                for instance_path in benchmark_instances:
                    console.print(f"  {instance_path}")
                    results["instances"].append({"instance_path": str(instance_path)})

            return results
        finally:
            self.cleanup_temp_dir()


def _format_results(results: dict[str, Any], fmt: str) -> str:
    """Format benchmark results as JSON or YAML string."""
    if fmt == "json":
        return json.dumps(results, indent=2)
    else:  # yaml
        return yaml.safe_dump(results, default_flow_style=False, sort_keys=False)


def _write_results_to_file(
    results: dict[str, Any], output_file: Path, fmt: str
) -> None:
    """Write benchmark results to a file in the specified format."""
    output_file.write_text(_format_results(results, fmt))
    console.print(f"\nResults written to: {output_file}")


def _print_structured_results(results: dict[str, Any], fmt: str) -> None:
    """Print benchmark results in structured format (JSON or YAML)."""
    console.print()  # Blank line before output
    console.print(_format_results(results, fmt))


def _get_status_display(status: str) -> str:
    """Get color-coded status display string."""
    status_colors = {
        "success": "green",
        "started": "cyan",
        "failed": "red",
    }
    color = status_colors.get(status, "yellow")
    return f"[{color}]{status}[/{color}]"


def _print_human_readable_results(results: dict[str, Any]) -> None:
    """Print benchmark results in human-readable format."""
    console.print("\n[bold]Benchmark Execution Results[/bold]\n")

    if not results.get("instances"):
        console.print("[yellow]No benchmark instances found[/yellow]")
        return

    for instance in results["instances"]:
        instance_path = instance.get("instance_path", "Unknown")
        status = instance.get("status", "unknown")
        message = instance.get("message", "")

        console.print(f"[bold]{instance_path}[/bold]")
        console.print(f"  Status: {_get_status_display(status)}")

        if message:
            console.print(f"  Message: {message}")

        if instance.get("space_id"):
            console.print(f"  Space ID: {instance['space_id']}")
        if instance.get("operation_id"):
            console.print(f"  Operation ID: {instance['operation_id']}")
        if instance.get("ray_job_id"):
            console.print(f"  Ray Job ID: {instance['ray_job_id']}")

        console.print()  # Empty line between instances


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
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    context: Annotated[
        Path | None,
        typer.Option(
            "--context",
            help="Path to ADO context YAML file (samplestore context)",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="List benchmarks without executing them (dry run)",
        ),
    ] = False,
    output_file: Annotated[
        Path | None,
        typer.Option(
            "--output-file",
            help="Output file path for execution results. If not specified, results are printed to screen.",
            dir_okay=False,
            writable=True,
        ),
    ] = None,
    output_format: Annotated[
        str | None,
        typer.Option(
            "-o",
            "--output-format",
            help="Output format: 'json' or 'yaml'. Only used with --output-file.",
        ),
    ] = None,
) -> None:
    """Execute benchmarks from a GitHub Pull Request.

    Identifies new or changed benchmark instances in a PR and optionally
    executes them using the ADO CLI. When executing with --remote flag,
    automatically installs required benchmark packages in the Ray environment.

    The command automatically checks if the local repository is on the same
    commit as the PR. If not, it will checkout the PR code in a temporary
    directory.
    """
    from algorithm_nexus.commands.utils import validate_output_format

    # Validate output format if specified
    if output_format:
        validate_output_format(output_format, allow_yaml=True, allow_csv=False)

    try:
        manager = BenchmarkManager(
            pr_url=pr,
            execute=not dry_run,
            remote_context_file=remote,
            context_file=context,
        )
        results = manager.run()

        # Output results
        # Determine output format
        if output_format:
            fmt = output_format
        elif output_file and (
            output_file.suffix == ".yaml" or output_file.suffix == ".yml"
        ):
            fmt = "yaml"
        elif output_file:
            fmt = "json"
        else:
            fmt = None  # Human-readable format for console

        # Output results
        if output_file:
            # fmt is guaranteed to be a string when output_file is provided
            # (either from output_format, file extension, or defaulted to "json")
            if fmt is None:
                fmt = "json"  # Default fallback (should never happen based on logic above)
            _write_results_to_file(results, output_file, fmt)
        elif fmt in ("json", "yaml"):
            _print_structured_results(results, fmt)
        else:
            _print_human_readable_results(results)

        if not dry_run and results.get("summary") and results["summary"]["failed"] > 0:
            raise typer.Exit(code=1)

    except KeyboardInterrupt:
        console_err.print("\n[yellow]Interrupted by user[/yellow]")
        raise typer.Exit(code=130)
    except Exception as e:
        console_err.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


# Made with Bob
