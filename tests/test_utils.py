# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Tests for utility functions in algorithm_nexus.commands.utils."""

from __future__ import annotations

from pathlib import Path

import pytest

from algorithm_nexus.commands.utils import (
    find_package_config,
    output_requirements_txt,
    try_load_package_config,
)


class TestTryLoadPackageConfig:
    """Tests for try_load_package_config function."""

    def test_load_valid_package(self, tmp_path: Path) -> None:
        """Test loading a valid package configuration."""
        # Create a valid nexus.yaml
        package_dir = tmp_path / "test-package"
        package_dir.mkdir()
        nexus_yaml = package_dir / "nexus.yaml"
        nexus_yaml.write_text(
            """
package:
  name: "test-package"
"""
        )

        config = try_load_package_config(package_dir)
        assert config is not None
        assert config.package.name == "test-package"

    def test_load_package_missing_nexus_yaml(self, tmp_path: Path) -> None:
        """Test loading package without nexus.yaml returns None."""
        package_dir = tmp_path / "test-package"
        package_dir.mkdir()

        config = try_load_package_config(package_dir)
        assert config is None

    def test_load_package_invalid_yaml(self, tmp_path: Path) -> None:
        """Test loading package with invalid YAML returns None."""
        package_dir = tmp_path / "test-package"
        package_dir.mkdir()
        nexus_yaml = package_dir / "nexus.yaml"
        nexus_yaml.write_text("invalid: yaml: content:")

        config = try_load_package_config(package_dir)
        assert config is None

    def test_load_package_invalid_schema(self, tmp_path: Path) -> None:
        """Test loading package with invalid schema returns None."""
        package_dir = tmp_path / "test-package"
        package_dir.mkdir()
        nexus_yaml = package_dir / "nexus.yaml"
        nexus_yaml.write_text(
            """
package:
  invalid_field: "value"
"""
        )

        config = try_load_package_config(package_dir)
        assert config is None


class TestFindPackageConfig:
    """Tests for find_package_config function."""

    def test_find_existing_package(self, tmp_path: Path) -> None:
        """Test finding an existing package by name."""
        # Create multiple packages
        for name in ["package-a", "package-b", "package-c"]:
            package_dir = tmp_path / name
            package_dir.mkdir()
            nexus_yaml = package_dir / "nexus.yaml"
            nexus_yaml.write_text(
                f"""
package:
  name: "{name}"
"""
            )

        result = find_package_config("package-b", tmp_path)
        assert result is not None
        pkg_dir, config = result
        assert pkg_dir.name == "package-b"
        assert config.package.name == "package-b"

    def test_find_nonexistent_package(self, tmp_path: Path) -> None:
        """Test finding a package that doesn't exist returns None."""
        # Create a package
        package_dir = tmp_path / "package-a"
        package_dir.mkdir()
        nexus_yaml = package_dir / "nexus.yaml"
        nexus_yaml.write_text(
            """
package:
  name: "package-a"
"""
        )

        result = find_package_config("nonexistent", tmp_path)
        assert result is None

    def test_find_package_skips_hidden_dirs(self, tmp_path: Path) -> None:
        """Test that hidden directories are skipped."""
        # Create a hidden directory with a package
        hidden_dir = tmp_path / ".hidden"
        hidden_dir.mkdir()
        nexus_yaml = hidden_dir / "nexus.yaml"
        nexus_yaml.write_text(
            """
package:
  name: "hidden-package"
"""
        )

        result = find_package_config("hidden-package", tmp_path)
        assert result is None

    def test_find_package_skips_files(self, tmp_path: Path) -> None:
        """Test that files are skipped during search."""
        # Create a file (not a directory)
        (tmp_path / "not-a-dir.txt").write_text("content")

        # Create a valid package
        package_dir = tmp_path / "valid-package"
        package_dir.mkdir()
        nexus_yaml = package_dir / "nexus.yaml"
        nexus_yaml.write_text(
            """
package:
  name: "valid-package"
"""
        )

        result = find_package_config("valid-package", tmp_path)
        assert result is not None
        assert result[1].package.name == "valid-package"


class TestOutputRequirementsTxt:
    """Tests for output_requirements_txt function."""

    def test_output_to_console(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test outputting requirements to console."""
        import re

        requirements = ["package-a>=1.0.0", "package-b==2.0.0", "package-c"]

        output_requirements_txt(requirements, None)

        captured = capsys.readouterr()
        # Rich console adds ANSI color codes, so we strip them for testing
        # ANSI escape codes pattern: \x1b\[[0-9;]*m
        output_clean = re.sub(r"\x1b\[[0-9;]*m", "", captured.out)

        assert "package-a>=1.0.0" in output_clean
        assert "package-b==2.0.0" in output_clean
        assert "package-c" in output_clean

    def test_output_to_file(self, tmp_path: Path) -> None:
        """Test outputting requirements to a file."""
        requirements = ["package-a>=1.0.0", "package-b==2.0.0", "package-c"]
        output_file = tmp_path / "requirements.txt"

        output_requirements_txt(requirements, output_file)

        assert output_file.exists()
        content = output_file.read_text()
        assert content == "package-a>=1.0.0\npackage-b==2.0.0\npackage-c\n"

    def test_output_empty_requirements(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test outputting empty requirements list."""
        requirements: list[str] = []

        output_requirements_txt(requirements, None)

        captured = capsys.readouterr()
        assert captured.out == "\n"


# Made with Bob
