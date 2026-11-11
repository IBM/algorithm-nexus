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

    def test_ssh_slash_shorthand_becomes_git_ssh_url(self):
        result = self.manager._resolve_benchmark_package_requirement(
            "git@github.ibm.com/Daniele-Lotito/lightsabre-custom-experiment.git@dl_cp_custom_exp_top_level"
        )
        assert (
            result
            == "git+ssh://git@github.ibm.com/Daniele-Lotito/lightsabre-custom-experiment.git@dl_cp_custom_exp_top_level"
        )

    def test_enterprise_github_https_url_gets_git_prefix(self):
        result = self.manager._resolve_benchmark_package_requirement(
            "https://github.ibm.com/org/repo.git"
        )
        assert result == "git+https://github.ibm.com/org/repo.git"

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
            "  - requirement_specifier: sorting-benchmarks\n"
            "    experiments:\n"
            "      - experimentIdentifier: bubble_sort\n"
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
            "  - requirement_specifier: https://github.com/org/repo.git\n"
            "    experiments:\n"
            "      - experimentIdentifier: my_exp\n"
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
            f"experiment_package:\n  - requirement_specifier: {requirement}\n"
            "    experiments:\n      - experimentIdentifier: my_exp\n"
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

    def test_missing_experiment_package_yaml_returns_empty(self, tmp_path):
        """Test that an experiment directory without experiment_package.yaml is skipped."""
        exp_dir = tmp_path / "experiments" / "missing_yaml"
        exp_dir.mkdir(parents=True)
        # No experiment_package.yaml, no submissions either

        result = self.manager.find_all_benchmark_submissions(tmp_path / "experiments")
        assert result == []

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


class TestValidateSeparateVenvs:
    """Each experiment package is installed in its own venv when validating."""

    PKG_YAML = (
        "experiment_package:\n"
        "  - requirement_specifier: pkg==1.0.0\n"
        "    experiments:\n"
        "      - experimentIdentifier: exp\n"
        "        experimentVersion: 1.0.0\n"
        "  - requirement_specifier: pkg==2.0.0\n"
        "    experiments:\n"
        "      - experimentIdentifier: exp\n"
        "        experimentVersion: 2.0.0\n"
    )

    def _setup(self, tmp_path, versions):
        exp = tmp_path / "experiments" / "my_exp"
        exp.mkdir(parents=True)
        (exp / "experiment_package.yaml").write_text(self.PKG_YAML)
        for name, version in versions.items():
            sub = exp / "submissions" / name
            sub.mkdir(parents=True)
            (sub / "space.yaml").write_text(
                "experiments:\n"
                "- actuatorIdentifier: custom_experiments\n"
                "  experimentIdentifier: exp\n"
                f"  experimentVersion: {version}\n"
            )
        return tmp_path / "experiments"

    def _run(self, tmp_path, monkeypatch, versions, install_ok=lambda req: True):
        from algorithm_nexus.commands import ado_validator, venv_manager
        from algorithm_nexus.commands.benchmark_manager import BenchmarkManager
        from algorithm_nexus.models import ValidationResult

        root = self._setup(tmp_path, versions)
        created, installed, cleaned, used = [], [], [], {}

        def fake_create(*a, **k):
            p = tmp_path / f"venv{len(created)}"
            created.append(p)
            return p

        def fake_install(venv, reqs, verbose=False):
            installed.append((venv, tuple(reqs)))
            return install_ok(reqs[0])

        def fake_validate(base_path, submission_path, venv_path):
            used[submission_path.split("/")[-1]] = venv_path
            return ValidationResult(
                success=True,
                submission_path=submission_path,
                errors=[],
                warnings=[],
            )

        monkeypatch.setattr(venv_manager, "create_temp_venv", fake_create)
        monkeypatch.setattr(venv_manager, "install_packages", fake_install)
        monkeypatch.setattr(
            venv_manager, "verify_experiments_installed", lambda *a, **k: (True, [])
        )
        monkeypatch.setattr(venv_manager, "cleanup_venv", cleaned.append)
        monkeypatch.setattr(ado_validator, "validate_with_ado", fake_validate)

        manager = BenchmarkManager(pr_url=None, execute=False)
        report = manager.validate(experiments_root=root)
        return report, created, installed, cleaned, used

    def test_each_package_gets_its_own_venv(self, tmp_path, monkeypatch):
        _, created, installed, cleaned, _ = self._run(
            tmp_path, monkeypatch, {"s1": "1.0.0"}
        )
        assert len(created) == 2
        assert len({venv for venv, _ in installed}) == 2
        assert [reqs for _, reqs in installed] == [("pkg==1.0.0",), ("pkg==2.0.0",)]
        assert set(cleaned) == set(created)

    def test_submission_validated_in_venv_of_matching_version(
        self, tmp_path, monkeypatch
    ):
        _, created, _, _, used = self._run(
            tmp_path, monkeypatch, {"old": "1.0.0", "new": "2.0.0"}
        )
        assert used["old"] == created[0]
        assert used["new"] == created[1]

    def test_failed_install_only_skips_its_own_submissions(self, tmp_path, monkeypatch):
        report, _, _, _, used = self._run(
            tmp_path,
            monkeypatch,
            {"old": "1.0.0", "new": "2.0.0"},
            install_ok=lambda req: req != "pkg==1.0.0",
        )
        assert "old" not in used
        assert "new" in used
        assert report.failed == 1


class TestValidateInvalidExperimentPackage:
    """An invalid experiment_package.yaml is reported, not hidden by ado errors."""

    # Pre-#350 schema: experiment_package is a mapping, not a list.
    LEGACY_YAML = (
        "experiment_package:\n"
        "  requirement_specifier: pkg==1.0.0\n"
        "  experiments:\n"
        "    - exp\n"
    )

    def test_reports_parse_error_and_skips_submissions(
        self, tmp_path, monkeypatch, capsys
    ):
        from algorithm_nexus.commands import ado_validator, venv_manager
        from algorithm_nexus.commands.benchmark_manager import BenchmarkManager

        exp = tmp_path / "experiments" / "my_exp"
        sub = exp / "submissions" / "s1"
        sub.mkdir(parents=True)
        (exp / "experiment_package.yaml").write_text(self.LEGACY_YAML)
        (sub / "space.yaml").write_text("experiments: []\n")

        def fail(*a, **k):
            raise AssertionError("must not be called for an invalid config")

        monkeypatch.setattr(venv_manager, "create_temp_venv", fail)
        monkeypatch.setattr(venv_manager, "install_packages", fail)
        monkeypatch.setattr(ado_validator, "validate_with_ado", fail)

        manager = BenchmarkManager(pr_url=None, execute=False)
        report = manager.validate(experiments_root=tmp_path / "experiments")

        assert report.failed == 1
        assert report.successful == 0
        assert report.total == 1
        (result,) = report.instances
        assert result["submission_path"] == "experiments/my_exp/experiment_package"
        assert "Invalid experiment_package.yaml" in result["errors"][0]
        assert "experiment_package: Input should be a valid list" in result["errors"][0]

        out = capsys.readouterr().out
        assert "Input should be a valid list" in out
        assert "Skipping 1 submission(s)" in out
        assert "ADO binary not found" not in out


class TestSelectPackageIndex:
    def _packages(self):
        from algorithm_nexus.models import ExperimentConfig

        return ExperimentConfig.model_validate(
            {
                "experiment_package": [
                    {
                        "requirement_specifier": "pkg==1.0.0",
                        "experiments": [
                            {"experimentIdentifier": "e", "experimentVersion": "1.0.0"}
                        ],
                    },
                    {
                        "requirement_specifier": "pkg==2.1.0",
                        "experiments": [
                            {"experimentIdentifier": "e", "experimentVersion": "2.1.0"}
                        ],
                    },
                ]
            }
        ).packages

    def test_exact_version(self):
        from algorithm_nexus.commands.benchmark_manager import select_package_index

        refs = [{"experimentIdentifier": "e", "experimentVersion": "2.1.0"}]
        assert select_package_index(refs, self._packages()) == (1, None)

    def test_same_major_version(self):
        from algorithm_nexus.commands.benchmark_manager import select_package_index

        refs = [{"experimentIdentifier": "e", "experimentVersion": "2.0.0"}]
        assert select_package_index(refs, self._packages()) == (1, None)

    def test_unknown_version_warns_and_falls_back(self):
        from algorithm_nexus.commands.benchmark_manager import select_package_index

        refs = [{"experimentIdentifier": "e", "experimentVersion": "9.0.0"}]
        idx, warning = select_package_index(refs, self._packages())
        assert idx == 0
        assert warning is not None
        assert "9.0.0" in warning

    def test_no_version_uses_first_declaring_package(self):
        from algorithm_nexus.commands.benchmark_manager import select_package_index

        refs = [{"experimentIdentifier": "e"}]
        assert select_package_index(refs, self._packages()) == (0, None)

    def test_unknown_experiment(self):
        from algorithm_nexus.commands.benchmark_manager import select_package_index

        refs = [{"experimentIdentifier": "other"}]
        assert select_package_index(refs, self._packages()) == (None, None)
