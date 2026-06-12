# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Tests for validate benchmarks command."""

from __future__ import annotations

import contextlib
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from algorithm_nexus.commands.ado_validator import validate_space_yaml_syntax
from algorithm_nexus.commands.venv_manager import (
    cleanup_venv,
    create_temp_venv,
    has_uv,
    install_packages,
)
from algorithm_nexus.models import ValidationResult


class TestVenvManager:
    """Tests for virtual environment manager."""

    def test_has_uv(self):
        """Test uv detection."""
        # This will return True or False depending on system
        result = has_uv()
        assert isinstance(result, bool)

    @pytest.mark.skipif(not has_uv(), reason="uv not available")
    def test_create_temp_venv(self):
        """Test creating venv with uv."""
        venv_path = create_temp_venv()
        try:
            assert venv_path.exists()
            assert (venv_path / "bin" / "python").exists()
        finally:
            cleanup_venv(venv_path)

    @pytest.mark.skipif(not has_uv(), reason="uv not available")
    def test_cleanup_venv(self):
        """Test venv cleanup."""
        venv_path = create_temp_venv()
        assert venv_path.exists()
        cleanup_venv(venv_path)
        # Parent temp directory should be removed
        assert not venv_path.parent.exists()

    @patch("algorithm_nexus.commands.venv_manager.subprocess.run")
    def test_install_packages_passes_requirements_unchanged(self, mock_run):
        """Test that install_packages passes requirements to uv pip install unchanged.

        Note: git+ prefix addition is now handled by BenchmarkManager._resolve_benchmark_package_requirement
        before calling install_packages.
        """
        # Create a temporary venv path (doesn't need to exist for this test)
        venv_path = Path(tempfile.mkdtemp()) / "venv"

        # Mock successful subprocess run
        mock_run.return_value = MagicMock(stdout="", returncode=0)

        # Test with various package types (already processed with git+ prefix where needed)
        requirements = [
            "git+https://github.com/user/repo.git",
            "git+http://github.com/user/repo2.git",
            "git+https://github.com/user/repo3.git",
            "package-name==1.0.0",  # Regular package
            "./local/path",  # Local path
        ]

        # Call install_packages (now always uses uv)
        install_packages(venv_path, requirements, verbose=False)

        # Verify subprocess.run was called
        assert mock_run.called

        # Get the actual command that was passed
        call_args = mock_run.call_args[0][0]

        # Verify requirements are passed unchanged
        assert "git+https://github.com/user/repo.git" in call_args
        assert "git+http://github.com/user/repo2.git" in call_args
        assert "git+https://github.com/user/repo3.git" in call_args
        assert "package-name==1.0.0" in call_args
        assert "./local/path" in call_args

        # Cleanup
        import shutil

        shutil.rmtree(venv_path.parent, ignore_errors=True)


class TestAdoValidator:
    """Tests for ADO validator."""

    def test_validate_space_yaml_syntax_missing_file(self):
        """Test validation with missing file."""
        result = validate_space_yaml_syntax(Path("/nonexistent/space.yaml"))
        assert not result.success
        assert len(result.errors) > 0
        assert "not found" in result.errors[0].lower()

    def test_validate_space_yaml_syntax_valid(self, tmp_path):
        """Test validation with valid space.yaml."""
        space_yaml = tmp_path / "space.yaml"
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

        result = validate_space_yaml_syntax(space_yaml)
        assert result.success
        assert len(result.errors) == 0

    def test_validate_space_yaml_syntax_invalid_yaml(self, tmp_path):
        """Test validation with invalid YAML."""
        space_yaml = tmp_path / "space.yaml"
        space_yaml.write_text("invalid: yaml: content:")

        result = validate_space_yaml_syntax(space_yaml)
        assert not result.success
        assert len(result.errors) > 0

    def test_validate_space_yaml_syntax_missing_experiments(self, tmp_path):
        """Test validation with missing experiments section."""
        space_yaml = tmp_path / "space.yaml"
        space_yaml.write_text(
            """
entitySpace:
  - identifier: dataset
"""
        )

        result = validate_space_yaml_syntax(space_yaml)
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

        # Test to_summary_dict
        summary = result.to_summary_dict()
        assert summary["instance"] == "/test/path"
        assert summary["status"] == "success"
        assert summary["errors"] == []
        assert summary["warnings"] == ["test warning"]


class TestValidateBenchmarksCommand:
    """Tests for validate benchmarks CLI command."""

    @patch("algorithm_nexus.commands.benchmark_manager.BenchmarkManager")
    def test_validate_benchmarks_no_instances(self, mock_manager_class):
        """Test validate benchmarks with no instances found."""
        # Mock BenchmarkManager
        mock_manager = MagicMock()

        # Mock the validate method to return empty results
        mock_manager.validate.return_value = {
            "instances": [],
            "summary": {
                "total": 0,
                "successful": 0,
                "failed": 0,
            },
        }
        mock_manager_class.return_value = mock_manager

        # Import here to avoid issues with mocking
        from algorithm_nexus.commands.validate import validate_benchmarks

        # Should not raise an error when no instances found
        with contextlib.suppress(SystemExit):
            validate_benchmarks(
                pr_url="https://github.com/test/repo/pull/1",
                packages_root=Path("./packages"),
                verbose=False,
                fail_fast=False,
                output_format="table",
            )

    @patch("algorithm_nexus.commands.benchmark_manager.BenchmarkManager")
    def test_validate_benchmarks_with_instances(
        self,
        mock_manager_class,
        tmp_path,
    ):
        """Test validate benchmarks with instances."""
        # Setup mocks
        mock_manager = MagicMock()

        # Mock the validate method to return successful results
        mock_manager.validate.return_value = {
            "instances": [
                {
                    "instance": "test1",
                    "status": "success",
                    "errors": [],
                    "warnings": [],
                }
            ],
            "summary": {
                "total": 1,
                "successful": 1,
                "failed": 0,
            },
        }
        mock_manager_class.return_value = mock_manager

        from algorithm_nexus.commands.validate import validate_benchmarks

        # Should complete successfully
        with pytest.raises(SystemExit) as exc_info:
            validate_benchmarks(
                pr_url="https://github.com/test/repo/pull/1",
                packages_root=Path("./packages"),
                verbose=False,
                fail_fast=False,
                output_format="table",
            )
        # Exit code 0 or None means success
        assert exc_info.value.code in (0, None)


# Made with Bob
