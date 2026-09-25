# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Benchmark manager for discovering and managing benchmark submissions from GitHub PRs."""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    import typer
    import yaml
    from ado.core.discoveryspace.config import DiscoverySpaceConfiguration
    from ado.core.operation.config import (
        ConfigurationMetadata,
        DiscoveryOperationConfiguration,
        DiscoveryOperationEnum,
        DiscoveryOperationResourceConfiguration,
        OperatorReference,
    )
    from ado.core.remotecontext.config import (
        PackageConfiguration,
        RemoteExecutionContext,
    )
    from ado.modules.operators.randomwalk import (
        BaseSamplerConfiguration,
        RandomWalkParameters,
    )
    from ado.utilities.output import pydantic_model_as_yaml
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
    BenchmarkExecutionResult,
    ExperimentConfig,
    ValidationReport,
)

console = Console()
console_err = Console(stderr=True)


# Random walk operation template using DiscoveryOperationResourceConfiguration
def create_random_walk_operation_config(
    space_id: str,
    metadata_name: str = "randomwalk-all",
    metadata_description: str = "Perform a random walk on all points in a space",
    custom_metadata: dict[str, Any] | None = None,
    actuator_configuration_ids: list[str] | None = None,
) -> DiscoveryOperationResourceConfiguration:
    """Create a random walk operation configuration.

    Args:
        space_id: The discovery space identifier
        metadata_name: Name for the operation metadata
        metadata_description: Description for the operation metadata
        custom_metadata: Additional custom metadata fields
        actuator_configuration_ids: Optional list of actuator configuration identifiers

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
            operationType=DiscoveryOperationEnum.EXPLORE,
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
        actuatorConfigurationIdentifiers=actuator_configuration_ids or [],
    )


class BenchmarkManager:
    """Manages discovery and execution of benchmark submissions from a GitHub PR."""

    def __init__(
        self,
        pr_url: str | None,
        execute: bool = True,
        remote_context_file: Path | None = None,
        context_file: Path | None = None,
        actuator_configuration_id_map: dict[str, str] | None = None,
    ):
        """Initialize the benchmark manager.

        Args:
            pr_url: GitHub Pull Request URL, or None for non-PR mode
            execute: Whether to execute benchmarks with ADO CLI
            remote_context_file: Path to remote execution context YAML file
            context_file: Path to ADO context YAML file (samplestore context)
            actuator_configuration_id_map: Optional mapping of actuatorIdentifier to
                actuatorConfigurationId. When provided, experiments whose actuatorIdentifier
                matches a key will have the corresponding actuatorConfigurationId added to
                the operation's actuatorConfigurationIdentifiers list.
        """
        self.pr_url = pr_url
        self.execute = execute
        self.remote_context_file = remote_context_file
        self.context_file = context_file
        self.actuator_configuration_id_map: dict[str, str] = (
            actuator_configuration_id_map or {}
        )
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

    def _discover_instances(
        self,
        experiments_root: Path | None = None,
        experiment_filter: str | None = None,
    ) -> list[Path]:
        """Discover benchmark submissions based on mode (PR or all/experiment).

        Args:
            experiments_root: Path to experiments directory (for all/experiment mode)
            experiment_filter: Optional experiment name to filter by

        Returns:
            List of benchmark instance paths
        """
        if self.pr_url:
            # PR mode: Check out PR code if needed
            if not self.is_local_repo_on_pr_commit():
                console.print("[yellow]Local repository is not on PR commit[/yellow]")
                console.print("Checking out PR code to temporary directory...")
                self.checkout_pr_to_temp()
            else:
                console.print(
                    "[green]✓[/green] Using local repository (already on PR commit)"
                )

            changed_files = self.get_changed_files()
            return self.find_benchmark_submissions(changed_files)

        elif experiments_root:
            # All or experiment mode
            console.print("Discovering benchmark submissions...")
            return self.find_all_benchmark_submissions(
                experiments_root, experiment_filter
            )

        else:
            console.print(
                "[red]Error:[/red] Either pr_url or experiments_root must be provided"
            )
            raise typer.Exit(code=1)

    def _print_mode_header(
        self,
        experiments_root: Path | None = None,
        experiment_filter: str | None = None,
        mode_name: str = "execution",
    ) -> None:
        """Print mode header and configuration.

        Args:
            experiments_root: Path to experiments directory (for all/experiment mode)
            experiment_filter: Optional experiment name to filter by
            mode_name: Name of the mode (e.g., "Executing", "Validating")
        """
        if self.pr_url:
            console.print(f"\n[bold]Mode:[/bold] {mode_name} PR changes")
            console.print(f"PR URL: {self.pr_url}")
        elif experiment_filter:
            console.print(
                f"\n[bold]Mode:[/bold] {mode_name} experiment '{experiment_filter}'"
            )
        else:
            console.print(f"\n[bold]Mode:[/bold] {mode_name} all benchmark submissions")

        # Print experiments root when not in PR mode
        if not self.pr_url and experiments_root:
            console.print(f"Experiments root: {experiments_root.resolve()}")

        console.print("=" * 60)

    def _print_instances_found(
        self,
        benchmark_submissions: list[Path],
        experiment_filter: str | None = None,
        show_list: bool = True,
    ) -> None:
        """Print found instances or empty message.

        Args:
            benchmark_submissions: List of found benchmark submissions
            experiment_filter: Optional experiment name (for empty message)
            show_list: Whether to show the list of instances
        """
        if not benchmark_submissions:
            if self.pr_url:
                console.print(
                    "\n[yellow]No benchmark submissions found in this PR.[/yellow]"
                )
            elif experiment_filter:
                console.print(
                    f"\n[yellow]No benchmark submissions found in experiment '{experiment_filter}'.[/yellow]"
                )
            else:
                console.print("\n[yellow]No benchmark submissions found.[/yellow]")
            return

        console.print(
            f"\n[bold]Found {len(benchmark_submissions)} benchmark submission(s):[/bold]"
        )
        if show_list:
            for instance in benchmark_submissions:
                console.print(f"  • {instance}")

    def _resolve_all_dependencies(
        self, benchmark_submissions: list[Path], verbose: bool = False
    ) -> dict[Path, list[str]]:
        """Resolve dependencies for all benchmark submissions.

        Args:
            benchmark_submissions: List of benchmark instance paths
            verbose: Whether to show verbose output

        Returns:
            Dictionary mapping instance paths to their dependency lists
        """
        console.print("\n[bold]Resolving dependencies...[/bold]")
        instance_dependencies: dict[Path, list[str]] = {}

        for instance in benchmark_submissions:
            packages = self.get_benchmark_packages_for_submission(instance)
            if verbose:
                console.print(
                    f"  {instance}: {', '.join(packages) if packages else 'no dependencies'}"
                )

            instance_dependencies[instance] = list(packages)

        console.print(
            f"[green]✓[/green] Resolved dependencies for {len(benchmark_submissions)} instance(s)"
        )

        return instance_dependencies

    def _parse_submission_path(self, submission_path: Path) -> tuple[str, str, str]:
        """Parse benchmark instance path to extract experiment, model, and instance names.

        Args:
            submission_path: Path to benchmark instance directory

        Returns:
            Tuple of (experiment_name, model_name, instance_name)
            model_name is always "base" for experiment submissions.

        Raises:
            ValueError: If the instance path format is invalid
        """
        # Pattern: experiments/<experiment>/submissions/<submission>
        path_str = str(submission_path)
        pattern = r"^experiments/([^/]+)/submissions/([^/]+)$"
        match = re.match(pattern, path_str)
        if match:
            experiment_name, instance_name = match.groups()
            return experiment_name, "base", instance_name

        raise ValueError(
            f"Invalid benchmark submission path format: {submission_path}. "
            "Expected: experiments/<experiment>/submissions/<submission>"
        )

    def find_benchmark_submissions(self, changed_files: list[str]) -> list[Path]:
        """Find benchmark instance directories from changed files.

        Recognises paths under experiments/<name>/submissions/<submission>/.

        Args:
            changed_files: List of changed file paths

        Returns:
            List of unique benchmark instance directory paths
        """
        benchmark_dirs = set()

        for file_path in changed_files:
            path = Path(file_path)
            parts = path.parts
            # Pattern: experiments/<name>/submissions/<submission>/...
            if (
                len(parts) >= 4
                and parts[0] == "experiments"
                and parts[2] == "submissions"
            ):
                instance_dir = Path(*parts[:4])
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

    def _resolve_benchmark_package_requirement(self, requirement: str) -> str:
        """Resolve a benchmark package requirement specifier to its final form.

        Args:
            requirement: The requirement specifier from nexus.yaml

        Returns:
            Resolved requirement string (local path or package specifier)
        """
        # Check if it's a local path
        resolved_path = self.repo_root / requirement.lstrip("./")
        if resolved_path.exists():
            return str(resolved_path)

        # Already has git+ scheme (e.g. git+https://, git+ssh://, git+http://)
        if requirement.startswith("git+"):
            return requirement

        # SSH URL with ssh:// prefix (e.g. ssh://git@...) -> git+ssh://git@...
        if requirement.startswith("ssh://"):
            return f"git+{requirement}"

        # SSH scp-like or slash shorthand (e.g. git@github.com:org/repo or git@github.ibm.com/org/repo)
        if requirement.startswith("git@"):
            # If formatted like git@host:path -> git+ssh://git@host/path
            if ":" in requirement:
                host, path = requirement.split(":", 1)
                return f"git+ssh://{host}/{path}"
            # If formatted like git@host/path -> git+ssh://git@host/path
            return f"git+ssh://{requirement}"

        # HTTP/HTTPS URLs (e.g. https://github.com/..., https://github.ibm.com/...) -> git+https://...
        if requirement.startswith(("https://", "http://")):
            return f"git+{requirement}"

        return requirement

    def get_benchmark_packages_for_submission(self, submission_path: Path) -> set[str]:
        """Get the benchmark packages required for a specific benchmark instance.

        For submissions under experiments/<name>/submissions/<submission>/, the
        requirement specifier is read from experiments/<name>/experiment_package.yaml.

        Args:
            submission_path: Path to benchmark instance directory (relative to repo_root)

        Returns:
            Set of requirement specifiers for benchmark packages
        """
        try:
            repo_root = self.repo_root
            parts = submission_path.parts

            # Expect: experiments/<experiment_name>/submissions/<submission_name>/...
            if len(parts) >= 2 and parts[0] == "experiments":
                experiment_name = parts[1]
                experiment_yaml_path = (
                    repo_root
                    / "experiments"
                    / experiment_name
                    / "experiment_package.yaml"
                )
                if not experiment_yaml_path.is_file():
                    return set()

                experiment_config_dict = yaml.safe_load(
                    experiment_yaml_path.read_text()
                )
                experiment_config = ExperimentConfig.model_validate(
                    experiment_config_dict
                )
                resolved_req = self._resolve_benchmark_package_requirement(
                    experiment_config.experiment_package.requirement_specifier
                )
                return {resolved_req}

            return set()

        except Exception as e:
            console_err.print(
                f"[yellow]Warning:[/yellow] Could not determine benchmark packages for {submission_path}: {e}"
            )
            return set()

    def execute_benchmark(self, submission_path: Path) -> BenchmarkExecutionResult:
        """Execute a benchmark instance using ADO CLI.

        Args:
            submission_path: Path to benchmark instance directory

        Returns:
            Execution result
        """
        result = BenchmarkExecutionResult(submission_path=str(submission_path))

        # Prepare remote config once for this benchmark submission
        remote_config_for_space = None
        remote_config_for_operation = None
        temp_remote_configs = []

        try:
            # Use repo_root which is set to either local or checked out directory
            space_yaml_path = self.repo_root / submission_path / "space.yaml"

            if not space_yaml_path.is_file():
                raise FileNotFoundError(f"space.yaml not found in {submission_path}")

            # If in remote mode, create remote configs with benchmark packages
            if self.remote_context_file:
                benchmark_packages = self.get_benchmark_packages_for_submission(
                    submission_path
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
                    tmp_file.write(pydantic_model_as_yaml(space_remote_context))
                    tmp_file.flush()
                    temp_remote_configs.append(remote_config_for_space)

            console.print(f"  Creating ADO discoveryspace for: {submission_path}")
            space_id, actuator_configuration_ids = self._create_discoveryspace(
                space_yaml_path, submission_path, remote_config_for_space
            )
            result.space_id = space_id
            console.print(f"  [green]✓[/green] Successfully created space: {space_id}")

            console.print(f"  Creating operation for space: {space_id}")
            operation_result = self._create_operation(
                space_id,
                submission_path,
                remote_config_for_operation,
                actuator_configuration_ids,
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
        submission_path: Path,
        remote_config: Path | None = None,
    ) -> tuple[str, list[str]]:
        """Create a discoveryspace using ado CLI.

        Args:
            space_yaml_path: Path to space.yaml file
            submission_path: Path to benchmark instance directory
            remote_config: Optional path to remote configuration file (with wait: true for space creation)

        Returns:
            Tuple of (space identifier, resolved actuator configuration IDs)
        """

        # Load the space configuration from YAML
        space_config_dict = yaml.safe_load(space_yaml_path.read_text())

        # Resolve actuator configuration IDs while the space dict is available
        actuator_configuration_ids: list[str] = []
        if self.actuator_configuration_id_map:
            for experiment in (space_config_dict or {}).get("experiments", []):
                actuator_identifier = experiment.get("actuatorIdentifier")
                if (
                    actuator_identifier
                    and actuator_identifier in self.actuator_configuration_id_map
                ):
                    actuator_configuration_ids.append(
                        self.actuator_configuration_id_map[actuator_identifier]
                    )

        # Parse the configuration using DiscoverySpaceConfiguration
        space_config = DiscoverySpaceConfiguration.model_validate(space_config_dict)

        # Generate descriptive name and description from instance path
        # Extract PR number from URL (pr_url may be None in non-PR mode)
        pr_number = self.pr_url.rstrip("/").split("/")[-1] if self.pr_url else "unknown"

        # Parse submission path to get package, model, and submission names
        package_name, model_name, instance_name = self._parse_submission_path(
            submission_path
        )

        # Create descriptive name: space-pr123-package-model-submission
        space_name = f"space-pr{pr_number}-{package_name}-{model_name}-{instance_name}"
        space_description = f"Discovery space for benchmark submission from PR #{pr_number}: {package_name}/{model_name}/{instance_name}"

        # Build custom labels with algorithm-nexus fields
        labels = space_config.metadata.labels or {}
        labels["algorithm-nexus.pr_url"] = self.pr_url
        labels["algorithm-nexus.submission_path"] = str(submission_path)

        # Update metadata with descriptive name, description, and labels
        space_config.metadata = ConfigurationMetadata(
            name=space_name,
            description=space_description,
            labels=labels,
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=True
        ) as tmp_file:
            tmp_file.write(pydantic_model_as_yaml(space_config))
            tmp_file.flush()
            temp_space_path = tmp_file.name

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
                return strip_ansi_codes(match.group(1)), actuator_configuration_ids
            else:
                output_words = result.stdout.strip().split()
                if output_words:
                    return strip_ansi_codes(
                        output_words[-1]
                    ), actuator_configuration_ids
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

            if pkg in existing_pypi_packages or pkg in existing_source_packages:
                # The package is already present in the remote config, no need to add it again
                continue

            # Check if it is a local package path
            if Path(pkg).exists():
                # Check if package is a local path (relative or absolute)
                new_source_packages.append(pkg)
            else:
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
            tmp_file.write(pydantic_model_as_yaml(remote_config))
            tmp_file.flush()
            return temp_path

    def _create_operation(
        self,
        space_id: str,
        submission_path: Path | None = None,
        remote_config: Path | None = None,
        actuator_configuration_ids: list[str] | None = None,
    ) -> dict[str, str | None]:
        """Create and execute an operation using ado CLI.

        Args:
            space_id: Discovery space identifier
            submission_path: Optional path to benchmark submission (for package resolution)
            remote_config: Optional path to remote configuration file
            actuator_configuration_ids: Actuator configuration IDs resolved from space.yaml

        Returns:
            Dictionary with operation_id and ray_job_id (if remote execution)
        """
        # Generate descriptive name and description from submission path
        if submission_path:
            # Extract PR number from URL (pr_url may be None in non-PR mode)
            pr_number = (
                self.pr_url.rstrip("/").split("/")[-1] if self.pr_url else "unknown"
            )

            # Parse submission path to get package, model, and submission names
            package_name, model_name, instance_name = self._parse_submission_path(
                submission_path
            )

            # Create descriptive name: randomwalk-pr123-package-model-submission
            operation_name = (
                f"randomwalk-pr{pr_number}-{package_name}-{model_name}-{instance_name}"
            )
            operation_description = f"Random walk for benchmark submission from PR #{pr_number}: {package_name}/{model_name}/{instance_name}"
        else:
            operation_name = "randomwalk-all"
            operation_description = "Perform a random walk on all points in a space"

        # Create custom metadata with algorithm-nexus fields
        custom_metadata = {
            "algorithm-nexus.pr_url": self.pr_url or "",
            "algorithm-nexus.submission_path": str(submission_path)
            if submission_path
            else "",
        }

        # Create operation config using the factory function
        operation_config = create_random_walk_operation_config(
            space_id=space_id,
            metadata_name=operation_name,
            metadata_description=operation_description,
            custom_metadata=custom_metadata,
            actuator_configuration_ids=actuator_configuration_ids or None,
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=True
        ) as tmp_file:
            tmp_file.write(pydantic_model_as_yaml(operation_config))
            tmp_file.flush()
            operation_config_path = tmp_file.name

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
            words = result.stdout.strip().split()
            if words:
                operation_id = strip_ansi_codes(words[-1])

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
            console.print("Analyzing PR for new or changed benchmark submissions...")
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

            benchmark_submissions = self.find_benchmark_submissions(changed_files)

            if not benchmark_submissions:
                console.print(
                    "[yellow]No new or changed benchmark submissions found in this PR.[/yellow]"
                )
                return {"submissions": []}

            console.print(
                f"Found {len(benchmark_submissions)} benchmark submission(s):"
            )

            results: dict[str, Any] = {
                "submissions": [],
            }

            if self.execute:
                console.print("\nExecuting benchmarks with ADO CLI...")

                for submission_path in benchmark_submissions:
                    console.print(f"\nProcessing: {submission_path}")
                    exec_result = self.execute_benchmark(submission_path)
                    results["submissions"].append(exec_result.model_dump())

            else:
                for submission_path in benchmark_submissions:
                    console.print(f"  {submission_path}")
                    results["submissions"].append(
                        {"submission_path": str(submission_path)}
                    )

            return results
        finally:
            self.cleanup_temp_dir()

    def find_all_benchmark_submissions(
        self, experiments_root: Path, experiment_filter: str | None = None
    ) -> list[Path]:
        """Find all benchmark submissions in the experiments directory.

        Scans experiments/<name>/submissions/<submission>/ for space.yaml files.
        Experiments without experiment_package.yaml are skipped with a warning.

        Args:
            experiments_root: Path to experiments directory
            experiment_filter: Optional experiment name to filter by

        Returns:
            List of benchmark instance directory paths (relative to repo_root)
        """
        benchmark_submissions = []

        # Resolve experiments_root to absolute path
        experiments_root_abs = experiments_root.resolve()

        if not experiments_root_abs.exists():
            console.print(
                f"[red]Error:[/red] Experiments directory not found: {experiments_root_abs}"
            )
            raise typer.Exit(code=1)

        # Only update repo_root after confirming the path exists
        self.repo_root = experiments_root_abs.parent  # Parent of experiments directory

        # Walk through experiments directory
        for exp_dir in sorted(experiments_root_abs.iterdir()):
            if not exp_dir.is_dir() or exp_dir.name.startswith("."):
                continue

            # Filter by experiment name if specified
            if experiment_filter and exp_dir.name != experiment_filter:
                continue

            # Find submissions/<submission>/ directories that contain space.yaml
            submissions_dir = exp_dir / "submissions"
            if submissions_dir.exists() and submissions_dir.is_dir():
                benchmark_submissions.extend(
                    instance_dir.relative_to(self.repo_root)
                    for instance_dir in submissions_dir.iterdir()
                    if instance_dir.is_dir() and (instance_dir / "space.yaml").exists()
                )

        return sorted(benchmark_submissions)

    def _scan_experiments(
        self, experiments_root: Path, experiment_filter: str | None = None
    ) -> list[tuple[str, Path, ExperimentConfig | None, list[Path]]]:
        """Scan experiments directory and return structured per-experiment data.

        For each experiment directory returns a tuple of:
          (experiment_name, experiment_dir, experiment_config_or_None, submission_paths)

        experiment_config is None when experiment_package.yaml is absent or invalid.
        submission_paths are relative to self.repo_root.

        Args:
            experiments_root: Absolute path to the experiments directory
            experiment_filter: Optional experiment name to filter by

        Returns:
            List of (name, dir, config, submissions) tuples, sorted by name
        """
        results = []

        for exp_dir in sorted(experiments_root.iterdir()):
            if not exp_dir.is_dir() or exp_dir.name.startswith("."):
                continue

            if experiment_filter and exp_dir.name != experiment_filter:
                continue

            # Phase 1 — optional experiment_package.yaml
            experiment_config: ExperimentConfig | None = None
            experiment_yaml = exp_dir / "experiment_package.yaml"
            if experiment_yaml.is_file():
                try:
                    experiment_config = ExperimentConfig.model_validate(
                        yaml.safe_load(experiment_yaml.read_text())
                    )
                except Exception as e:
                    console.print(
                        f"[yellow]Warning:[/yellow] Could not parse "
                        f"{experiment_yaml}: {e}"
                    )

            # Phase 2 — optional submissions directory
            submissions: list[Path] = []
            submissions_dir = exp_dir / "submissions"
            if submissions_dir.is_dir():
                submissions = sorted(
                    instance_dir.relative_to(self.repo_root)
                    for instance_dir in submissions_dir.iterdir()
                    if instance_dir.is_dir() and (instance_dir / "space.yaml").exists()
                )

            results.append((exp_dir.name, exp_dir, experiment_config, submissions))

        return results

    def validate(
        self,
        experiments_root: Path | None = None,
        experiment_filter: str | None = None,
        verbose: bool = False,
        fail_fast: bool = False,
    ) -> ValidationReport:
        """Validate experiments in two phases per experiment, using one shared venv.

        Phase 1 (experiment_package): If experiment_package.yaml is present, install
        the package and verify the declared experiment IDs are discoverable.

        Phase 2 (submissions): If submissions/<name>/space.yaml files are present,
        validate each with ADO dry-run using the same venv.

        Both phases are optional and independent; an experiment may trigger either,
        neither, or both.

        Args:
            experiments_root: Path to experiments directory (for all/experiment mode)
            experiment_filter: Optional experiment name to filter by
            verbose: Show detailed validation output
            fail_fast: Stop validation on first error

        Returns:
            ValidationReport with all results
        """
        from algorithm_nexus.commands.ado_validator import validate_with_ado
        from algorithm_nexus.commands.venv_manager import (
            cleanup_venv,
            create_temp_venv,
            install_packages,
            verify_experiments_installed,
        )
        from algorithm_nexus.models import ValidationResult

        try:
            # Print mode header
            self._print_mode_header(experiments_root, experiment_filter, "Validating")

            if self.pr_url:
                # PR mode — original per-submission flow (no experiment_package phase)
                benchmark_submissions = self._discover_instances(
                    experiments_root, experiment_filter
                )
                self._print_instances_found(benchmark_submissions, experiment_filter)

                if not benchmark_submissions:
                    return ValidationReport(
                        instances=[], successful=0, failed=0, total=0
                    )

                instance_dependencies = self._resolve_all_dependencies(
                    benchmark_submissions, verbose
                )

                all_results: list[dict] = []
                total_success = 0
                total_failed = 0

                for instance in benchmark_submissions:
                    resolved_req_list = instance_dependencies[instance]
                    venv_path = None
                    try:
                        venv_path = create_temp_venv()
                        if resolved_req_list and not install_packages(
                            venv_path, resolved_req_list, verbose=verbose
                        ):
                            all_results.append(
                                ValidationResult(
                                    success=False,
                                    submission_path=str(instance),
                                    errors=["Failed to install dependencies"],
                                    warnings=[],
                                ).model_dump()
                            )
                            total_failed += 1
                            if fail_fast:
                                break
                            continue

                        result = validate_with_ado(
                            base_path=self.repo_root,
                            submission_path=str(instance),
                            venv_path=venv_path,
                        )
                        all_results.append(result.model_dump())
                        if result.success:
                            total_success += 1
                        else:
                            total_failed += 1
                    finally:
                        if venv_path:
                            cleanup_venv(venv_path)

                    if fail_fast and total_failed > 0:
                        break

                return ValidationReport(
                    instances=all_results,
                    successful=total_success,
                    failed=total_failed,
                    total=len(benchmark_submissions),
                )

            # All / experiment mode — two-phase validation per experiment
            if not experiments_root:
                console.print(
                    "[red]Error:[/red] Either pr_url or experiments_root must be provided"
                )
                raise typer.Exit(code=1)

            experiments_root_abs = experiments_root.resolve()
            if not experiments_root_abs.exists():
                console.print(
                    f"[red]Error:[/red] Experiments directory not found: {experiments_root_abs}"
                )
                raise typer.Exit(code=1)

            self.repo_root = experiments_root_abs.parent

            console.print("Discovering experiments...")
            experiments = self._scan_experiments(
                experiments_root_abs, experiment_filter
            )

            if not experiments:
                console.print("\n[yellow]No experiments found.[/yellow]")
                return ValidationReport(instances=[], successful=0, failed=0, total=0)

            console.print(f"\n[bold]Found {len(experiments)} experiment(s):[/bold]")
            for exp_name, _, exp_cfg, submissions in experiments:
                pkg_label = (
                    f"package: {exp_cfg.experiment_package.requirement_specifier}"
                    if exp_cfg
                    else "no package"
                )
                console.print(
                    f"  • {exp_name}  [{pkg_label}, {len(submissions)} submission(s)]"
                )

            all_results = []
            total_success = 0
            total_failed = 0
            total_items = 0

            console.print("\n[bold]Validating experiments...[/bold]")
            console.print("=" * 60)

            for exp_name, _exp_dir, exp_cfg, submissions in experiments:
                console.print(f"\n[bold cyan]Experiment:[/bold cyan] {exp_name}")

                # Skip entirely if there is nothing to validate
                if exp_cfg is None and not submissions:
                    console.print(
                        "  [yellow]Skipping:[/yellow] no experiment_package.yaml "
                        "and no submissions found"
                    )
                    continue

                venv_path = None
                package_install_ok = True
                try:
                    venv_path = create_temp_venv()

                    # ── Phase 1: experiment_package ──────────────────────────
                    if exp_cfg is not None:
                        req = self._resolve_benchmark_package_requirement(
                            exp_cfg.experiment_package.requirement_specifier
                        )
                        console.print(
                            f"  [cyan]Phase 1:[/cyan] Installing package {req!r}"
                        )
                        if not install_packages(venv_path, [req], verbose=verbose):
                            pkg_result = ValidationResult(
                                success=False,
                                submission_path=f"experiments/{exp_name}/experiment_package",
                                errors=[f"Failed to install package: {req}"],
                                warnings=[],
                            )
                            all_results.append(pkg_result.model_dump())
                            total_failed += 1
                            total_items += 1
                            package_install_ok = False
                            if fail_fast:
                                break
                        else:
                            # Verify declared experiments are discoverable
                            ok, errors = verify_experiments_installed(
                                venv_path,
                                exp_cfg.experiment_package.experiments,
                                verbose=verbose,
                            )
                            pkg_result = ValidationResult(
                                success=ok,
                                submission_path=f"experiments/{exp_name}/experiment_package",
                                errors=errors,
                                warnings=[],
                            )
                            all_results.append(pkg_result.model_dump())
                            total_items += 1
                            if ok:
                                console.print(
                                    "  [green]✓[/green] Package installed and all "
                                    "experiments verified"
                                )
                                total_success += 1
                            else:
                                console.print(
                                    "  [red]✗[/red] Experiment verification failed"
                                )
                                total_failed += 1
                                for err in errors:
                                    console.print(f"    [red]Error:[/red] {err}")
                                if fail_fast:
                                    break

                    # ── Phase 2: submissions ─────────────────────────────────
                    if submissions:
                        if not package_install_ok:
                            console.print(
                                "  [yellow]Skipping submissions:[/yellow] "
                                "package install failed"
                            )
                        else:
                            console.print(
                                f"  [cyan]Phase 2:[/cyan] Validating "
                                f"{len(submissions)} submission(s)"
                            )
                            for instance in submissions:
                                console.print(
                                    f"    [cyan]Validating:[/cyan] {instance}"
                                )
                                result = validate_with_ado(
                                    base_path=self.repo_root,
                                    submission_path=str(instance),
                                    venv_path=venv_path,
                                )
                                all_results.append(result.model_dump())
                                total_items += 1
                                if result.success:
                                    console.print(
                                        "    [green]✓[/green] Validation passed"
                                    )
                                    total_success += 1
                                else:
                                    console.print("    [red]✗[/red] Validation failed")
                                    total_failed += 1
                                    for err in result.errors:
                                        console.print(f"      [red]Error:[/red] {err}")
                                    for warn in result.warnings:
                                        console.print(
                                            f"      [yellow]Warning:[/yellow] {warn}"
                                        )
                                if fail_fast and total_failed > 0:
                                    break

                finally:
                    if venv_path:
                        cleanup_venv(venv_path)

                if fail_fast and total_failed > 0:
                    console.print(
                        "\n[yellow]Stopping validation (--fail-fast)[/yellow]"
                    )
                    break

            return ValidationReport(
                instances=all_results,
                successful=total_success,
                failed=total_failed,
                total=total_items,
            )

        finally:
            self.cleanup_temp_dir()


# Made with Bob
