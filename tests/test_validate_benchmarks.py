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


class TestAdoValidator:
    """Tests for ADO validator."""

    def test_validate_space_yaml_syntax_missing_file(self):
        """Test validation with missing file."""
        result = validate_space_yaml_syntax(
            base_path=Path("/nonexistent"), instance_path="benchmark_instances/test"
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
            base_path=tmp_path, instance_path="test_instance"
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
            base_path=tmp_path, instance_path="test_instance"
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
            base_path=tmp_path, instance_path="test_instance"
        )
        # Should succeed but have warnings
        assert result.success
        assert len(result.warnings) > 0
        assert "experiments" in result.warnings[0].lower()

    def test_validation_result_model(self):
        """Test ValidationResult Pydantic model."""
        result = ValidationResult(
            success=True,
            instance_path="/test/path",
            errors=[],
            warnings=["test warning"],
        )

        assert result.success
        assert result.instance_path == "/test/path"
        assert len(result.errors) == 0
        assert len(result.warnings) == 1
        assert result.status == "success"

        summary = result.model_dump()
        assert summary["instance_path"] == "/test/path"
        assert summary["status"] == "success"
        assert summary["errors"] == []
        assert summary["warnings"] == ["test warning"]


class TestValidateBenchmarksCommand:
    """Tests for validate benchmarks CLI command."""

    def test_validate_benchmarks_nonexistent_package(self, tmp_path, capsys):
        """Test validate benchmarks with nonexistent package."""
        import typer

        from algorithm_nexus.commands.validate import validate_benchmarks

        packages_root = tmp_path / "packages"
        packages_root.mkdir()
        (packages_root / "existing-package").mkdir()

        with pytest.raises(typer.Exit) as exc_info:
            validate_benchmarks(
                pr_url=None,
                packages_root=packages_root,
                package="nonexistent-package",
                verbose=False,
                fail_fast=False,
                output_format="table",
            )
        assert exc_info.value.exit_code == 1

        captured = capsys.readouterr()
        assert "nexus list packages" in captured.out

    def test_validate_benchmarks_no_instances_in_package(self, tmp_path):
        """Test validate benchmarks finds no instances when package has no benchmark_instances."""
        import contextlib

        import typer

        from algorithm_nexus.commands.validate import validate_benchmarks

        packages_root = tmp_path / "packages"
        packages_root.mkdir()
        (packages_root / "test-package").mkdir()

        # No benchmark_instances directories exist, so validation exits cleanly with code 0
        with contextlib.suppress(typer.Exit):
            validate_benchmarks(
                pr_url=None,
                packages_root=packages_root,
                package="test-package",
                verbose=False,
                fail_fast=False,
                output_format="table",
            )

    def test_validate_benchmarks_both_package_and_pr_warns(self, tmp_path, capsys):
        """Test that specifying both --package and --pr prints a warning."""
        import contextlib

        import typer

        from algorithm_nexus.commands.validate import validate_benchmarks

        packages_root = tmp_path / "packages"
        packages_root.mkdir()

        # Providing both package and pr_url should print a warning before proceeding
        # (it will then fail trying to reach GitHub, which we suppress)
        with contextlib.suppress(typer.Exit, Exception):
            validate_benchmarks(
                pr_url="https://github.com/test/repo/pull/1",
                packages_root=packages_root,
                package="some-package",
                verbose=False,
                fail_fast=False,
                output_format="table",
            )

        captured = capsys.readouterr()
        assert "--package is ignored" in captured.out


# Made with Bob
