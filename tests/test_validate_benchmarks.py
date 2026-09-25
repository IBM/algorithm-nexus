# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Tests for validate benchmarks command."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from algorithm_nexus.commands.ado_validator import validate_space_yaml_syntax
from algorithm_nexus.commands.venv_manager import (
    cleanup_venv,
    create_temp_venv,
    install_packages,
)
from algorithm_nexus.models import ValidationResult


class TestVenvManager:
    """Tests for virtual environment manager."""

    def test_create_temp_venv(self):
        """Test creating venv with uv."""
        venv_path = create_temp_venv()
        try:
            assert venv_path.exists()
            assert (venv_path / "bin" / "python").exists()
        finally:
            cleanup_venv(venv_path)

    def test_cleanup_venv(self):
        """Test venv cleanup."""
        venv_path = create_temp_venv()
        assert venv_path.exists()
        cleanup_venv(venv_path)
        # Parent temp directory should be removed
        assert not venv_path.parent.exists()

    @patch("algorithm_nexus.commands.venv_manager.subprocess.run")
    def test_install_packages_passes_requirements_unchanged(self, mock_run):
        """Test that install_packages passes requirements to uv pip install unchanged."""
        # Create a temporary venv path (doesn't need to exist for this test)
        venv_path = Path(tempfile.mkdtemp()) / "venv"

        mock_run.return_value = MagicMock(stdout="", returncode=0)

        requirements = [
            "git+https://github.com/user/repo.git",
            "package-name==1.0.0",
            "./local/path",
        ]

        install_packages(venv_path, requirements, verbose=False)

        assert mock_run.called
        call_args = mock_run.call_args[0][0]

        assert "git+https://github.com/user/repo.git" in call_args
        assert "package-name==1.0.0" in call_args
        assert "./local/path" in call_args

        shutil.rmtree(venv_path.parent, ignore_errors=True)


class TestResolveBenchmarkPackageRequirement:
    """Tests for BenchmarkManager._resolve_benchmark_package_requirement."""

    def setup_method(self):
        from algorithm_nexus.commands.benchmark_manager import BenchmarkManager

        self.manager = BenchmarkManager(pr_url=None, execute=False)
        self.manager.repo_root = Path("/nonexistent")  # no local paths will resolve

    def test_https_github_url_gets_git_prefix(self):
        result = self.manager._resolve_benchmark_package_requirement(
            "https://github.com/org/repo"
        )
        assert result == "git+https://github.com/org/repo"

    def test_already_prefixed_https_url_unchanged(self):
        result = self.manager._resolve_benchmark_package_requirement(
            "git+https://github.com/org/repo.git"
        )
        assert result == "git+https://github.com/org/repo.git"

    def test_ssh_shorthand_becomes_git_ssh_url(self):
        result = self.manager._resolve_benchmark_package_requirement(
            "git@github.com:org/repo.git"
        )
        assert result == "git+ssh://git@github.com/org/repo.git"

    def test_pypi_package_unchanged(self):
        result = self.manager._resolve_benchmark_package_requirement("mypackage==1.2.3")
        assert result == "mypackage==1.2.3"


class TestFindBenchmarkSubmissions:
    """Tests for BenchmarkManager.find_benchmark_submissions (PR mode)."""

    def setup_method(self):
        from algorithm_nexus.commands.benchmark_manager import BenchmarkManager

        self.manager = BenchmarkManager(pr_url=None, execute=False)

    def test_finds_submission_in_experiments_path(self):
        changed_files = [
            "experiments/sorting_algorithms/submissions/bubble_sort/space.yaml"
        ]
        result = self.manager.find_benchmark_submissions(changed_files)
        assert result == [
            Path("experiments/sorting_algorithms/submissions/bubble_sort")
        ]

    def test_deduplicates_multiple_files_in_same_submission(self):
        changed_files = [
            "experiments/sorting_algorithms/submissions/bubble_sort/space.yaml",
            "experiments/sorting_algorithms/submissions/bubble_sort/operation.yaml",
        ]
        result = self.manager.find_benchmark_submissions(changed_files)
        assert len(result) == 1
        assert result[0] == Path(
            "experiments/sorting_algorithms/submissions/bubble_sort"
        )

    def test_finds_multiple_submissions(self):
        changed_files = [
            "experiments/sorting_algorithms/submissions/bubble_sort/space.yaml",
            "experiments/sorting_algorithms/submissions/merge_sort/space.yaml",
        ]
        result = self.manager.find_benchmark_submissions(changed_files)
        assert len(result) == 2

    def test_ignores_non_submission_paths(self):
        changed_files = [
            "packages/my-pkg/nexus.yaml",
            "benchmarks/sorting/benchmark.yaml",
            "experiments/sorting_algorithms/experiment_package.yaml",
            "experiments/sorting_algorithms/bindings/sorting_binding.yaml",
        ]
        result = self.manager.find_benchmark_submissions(changed_files)
        assert result == []

    def test_ignores_path_without_enough_parts(self):
        changed_files = [
            "experiments/sorting_algorithms/space.yaml",  # no 'submissions' segment
        ]
        result = self.manager.find_benchmark_submissions(changed_files)
        assert result == []


class TestGetBenchmarkPackagesForSubmission:
    """Tests for BenchmarkManager.get_benchmark_packages_for_submission."""

    def setup_method(self):
        from algorithm_nexus.commands.benchmark_manager import BenchmarkManager

        self.manager = BenchmarkManager(pr_url=None, execute=False)

    def test_reads_requirement_from_experiment_package_yaml(self, tmp_path):
        """Test that requirement_specifier is read from experiments/<name>/experiment_package.yaml."""
        exp_dir = tmp_path / "experiments" / "sorting_algorithms"
        exp_dir.mkdir(parents=True)
        (exp_dir / "experiment_package.yaml").write_text(
            "experiment_package:\n"
            "  requirement_specifier: sorting-benchmarks\n"
            "  experiments:\n"
            "    - bubble_sort\n"
        )

        self.manager.repo_root = tmp_path
        submission = Path("experiments/sorting_algorithms/submissions/bubble_sort")
        result = self.manager.get_benchmark_packages_for_submission(submission)
        assert result == {"sorting-benchmarks"}

    def test_github_url_gets_git_prefix(self, tmp_path):
        """Test that GitHub HTTPS URL gets git+ prefix."""
        exp_dir = tmp_path / "experiments" / "my_exp"
        exp_dir.mkdir(parents=True)
        (exp_dir / "experiment_package.yaml").write_text(
            "experiment_package:\n"
            "  requirement_specifier: https://github.com/org/repo.git\n"
            "  experiments:\n"
            "    - my_exp\n"
        )

        self.manager.repo_root = tmp_path
        submission = Path("experiments/my_exp/submissions/run1")
        result = self.manager.get_benchmark_packages_for_submission(submission)
        assert result == {"git+https://github.com/org/repo.git"}

    def test_returns_empty_when_no_experiment_package_yaml(self, tmp_path):
        """Test empty set returned when experiment_package.yaml does not exist."""
        (tmp_path / "experiments" / "my_exp").mkdir(parents=True)
        self.manager.repo_root = tmp_path
        submission = Path("experiments/my_exp/submissions/run1")
        result = self.manager.get_benchmark_packages_for_submission(submission)
        assert result == set()

    def test_returns_empty_for_non_experiment_path(self, tmp_path):
        """Test empty set for paths not under experiments/."""
        self.manager.repo_root = tmp_path
        submission = Path("packages/my-pkg/benchmark_submissions/run1")
        result = self.manager.get_benchmark_packages_for_submission(submission)
        assert result == set()


class TestFindAllBenchmarkSubmissions:
    """Tests for BenchmarkManager.find_all_benchmark_submissions."""

    def setup_method(self):
        from algorithm_nexus.commands.benchmark_manager import BenchmarkManager

        self.manager = BenchmarkManager(pr_url=None, execute=False)

    def _make_experiment(
        self, experiments_root: Path, name: str, requirement: str = "my-pkg"
    ) -> Path:
        """Helper: create a minimal experiment directory with experiment_package.yaml."""
        exp_dir = experiments_root / name
        exp_dir.mkdir(parents=True, exist_ok=True)
        (exp_dir / "experiment_package.yaml").write_text(
            f"experiment_package:\n  requirement_specifier: {requirement}\n"
        )
        return exp_dir

    def test_finds_submissions_with_space_yaml(self, tmp_path):
        """Test that submissions containing space.yaml are discovered."""
        exp_dir = self._make_experiment(tmp_path / "experiments", "sorting_algorithms")
        sub_dir = exp_dir / "submissions" / "bubble_sort"
        sub_dir.mkdir(parents=True)
        (sub_dir / "space.yaml").write_text("entitySpace: []\n")

        result = self.manager.find_all_benchmark_submissions(tmp_path / "experiments")
        assert Path("experiments/sorting_algorithms/submissions/bubble_sort") in result

    def test_ignores_submissions_without_space_yaml(self, tmp_path):
        """Test that submission directories without space.yaml are ignored."""
        exp_dir = self._make_experiment(tmp_path / "experiments", "sorting_algorithms")
        sub_dir = exp_dir / "submissions" / "incomplete"
        sub_dir.mkdir(parents=True)
        # No space.yaml

        result = self.manager.find_all_benchmark_submissions(tmp_path / "experiments")
        assert result == []

    def test_experiment_filter(self, tmp_path):
        """Test that experiment_filter limits results to one experiment."""
        experiments_root = tmp_path / "experiments"
        for exp_name in ["exp_a", "exp_b"]:
            exp_dir = self._make_experiment(experiments_root, exp_name)
            sub_dir = exp_dir / "submissions" / "run1"
            sub_dir.mkdir(parents=True)
            (sub_dir / "space.yaml").write_text("entitySpace: []\n")

        result = self.manager.find_all_benchmark_submissions(
            experiments_root, experiment_filter="exp_a"
        )
        assert len(result) == 1
        assert "exp_a" in str(result[0])

    def test_missing_experiment_package_yaml_exits(self, tmp_path):
        """Test that an experiment directory without experiment_package.yaml raises typer.Exit."""
        import typer

        exp_dir = tmp_path / "experiments" / "missing_yaml"
        exp_dir.mkdir(parents=True)
        # No experiment_package.yaml

        with pytest.raises(typer.Exit):
            self.manager.find_all_benchmark_submissions(tmp_path / "experiments")

    def test_nonexistent_experiments_root_exits(self, tmp_path):
        """Test that a nonexistent experiments root raises a typer.Exit."""
        import typer

        with pytest.raises(typer.Exit):
            self.manager.find_all_benchmark_submissions(
                tmp_path / "nonexistent_experiments"
            )


class TestAdoValidator:
    """Tests for ADO validator."""

    def test_validate_space_yaml_syntax_missing_file(self):
        """Test validation with missing file."""
        result = validate_space_yaml_syntax(
            base_path=Path("/nonexistent"), submission_path="benchmark_submissions/test"
        )
        assert not result.success
        assert len(result.errors) == 1
        assert "not found" in result.errors[0].lower()
        assert result.warnings == []

    def test_validate_space_yaml_syntax_valid(self, tmp_path):
        """Test validation with valid space.yaml."""
        instance_dir = tmp_path / "test_instance"
        instance_dir.mkdir()
        space_yaml = instance_dir / "space.yaml"
        space_yaml.write_text(
            """
entitySpace:
  - identifier: dataset
    propertyDomain:
      values: ["test"]

experiments:
  - actuatorIdentifier: custom_experiments
    experimentIdentifier: test-experiment
"""
        )

        result = validate_space_yaml_syntax(
            base_path=tmp_path, submission_path="test_instance"
        )
        assert result.success
        assert len(result.errors) == 0

    def test_validate_space_yaml_syntax_invalid_yaml(self, tmp_path):
        """Test validation with invalid YAML."""
        instance_dir = tmp_path / "test_instance"
        instance_dir.mkdir()
        space_yaml = instance_dir / "space.yaml"
        space_yaml.write_text("invalid: yaml: content:")

        result = validate_space_yaml_syntax(
            base_path=tmp_path, submission_path="test_instance"
        )
        assert not result.success
        assert len(result.errors) > 0

    def test_validate_space_yaml_syntax_missing_experiments(self, tmp_path):
        """Test validation with missing experiments section."""
        instance_dir = tmp_path / "test_instance"
        instance_dir.mkdir()
        space_yaml = instance_dir / "space.yaml"
        space_yaml.write_text(
            """
entitySpace:
  - identifier: dataset
"""
        )

        result = validate_space_yaml_syntax(
            base_path=tmp_path, submission_path="test_instance"
        )
        # Should succeed but have warnings
        assert result.success
        assert len(result.warnings) > 0
        assert "experiments" in result.warnings[0].lower()

    def test_validation_result_model(self):
        """Test ValidationResult Pydantic model."""
        result = ValidationResult(
            success=True,
            submission_path="/test/path",
            errors=[],
            warnings=["test warning"],
        )

        assert result.success
        assert result.submission_path == "/test/path"
        assert len(result.errors) == 0
        assert len(result.warnings) == 1
        assert result.status == "success"

        summary = result.model_dump()
        assert summary["submission_path"] == "/test/path"
        assert summary["status"] == "success"
        assert summary["errors"] == []
        assert summary["warnings"] == ["test warning"]


class TestValidateBenchmarksCommand:
    """Tests for validate benchmarks CLI command."""

    def test_validate_experiments_nonexistent_experiment(self, tmp_path, capsys):
        """Test validate benchmarks with nonexistent experiment."""
        import typer

        from algorithm_nexus.commands.validate import validate_experiments

        experiments_root = tmp_path / "experiments"
        experiments_root.mkdir()
        (experiments_root / "existing-experiment").mkdir()

        with pytest.raises(typer.Exit) as exc_info:
            validate_experiments(
                pr_url=None,
                experiments_root=experiments_root,
                experiment="nonexistent-experiment",
                verbose=False,
                fail_fast=False,
                output_format="table",
            )
        assert exc_info.value.exit_code == 1

        captured = capsys.readouterr()
        assert "nexus list experiments" in captured.out

    def test_validate_experiments_no_instances_in_experiment(self, tmp_path):
        """Test validate benchmarks finds no instances when experiment has no submissions."""
        import contextlib

        import typer

        from algorithm_nexus.commands.validate import validate_experiments

        experiments_root = tmp_path / "experiments"
        experiments_root.mkdir()
        (experiments_root / "test-experiment").mkdir()

        # No submissions directories exist, so validation exits cleanly with code 0
        with contextlib.suppress(typer.Exit):
            validate_experiments(
                pr_url=None,
                experiments_root=experiments_root,
                experiment="test-experiment",
                verbose=False,
                fail_fast=False,
                output_format="table",
            )

    def test_validate_experiments_both_experiment_and_pr_warns(self, tmp_path, capsys):
        """Test that specifying both --experiment and --pr prints a warning."""
        import contextlib

        import typer

        from algorithm_nexus.commands.validate import validate_experiments

        experiments_root = tmp_path / "experiments"
        experiments_root.mkdir()

        # Providing both experiment and pr_url should print a warning before proceeding
        # (it will then fail trying to reach GitHub, which we suppress)
        with contextlib.suppress(typer.Exit, Exception):
            validate_experiments(
                pr_url="https://github.com/test/repo/pull/1",
                experiments_root=experiments_root,
                experiment="some-experiment",
                verbose=False,
                fail_fast=False,
                output_format="table",
            )

        captured = capsys.readouterr()
        assert "--experiment is ignored" in captured.out


# Made with Bob
