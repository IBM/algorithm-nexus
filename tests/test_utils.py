# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Tests for utility functions in algorithm_nexus.commands.utils."""

from __future__ import annotations

from pathlib import Path

import pytest

from algorithm_nexus.commands.utils import (
    PackageLoadError,
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
        """Test loading package with invalid YAML raises PackageLoadError."""
        package_dir = tmp_path / "test-package"
        package_dir.mkdir()
        nexus_yaml = package_dir / "nexus.yaml"
        nexus_yaml.write_text("invalid: yaml: content:")

        with pytest.raises(PackageLoadError):
            try_load_package_config(package_dir)

    def test_load_package_invalid_schema(self, tmp_path: Path) -> None:
        """Test loading package with invalid schema raises PackageLoadError."""
        package_dir = tmp_path / "test-package"
        package_dir.mkdir()
        nexus_yaml = package_dir / "nexus.yaml"
        nexus_yaml.write_text(
            """
package:
  invalid_field: "value"
"""
        )

        with pytest.raises(PackageLoadError):
            try_load_package_config(package_dir)


# Made with Bob
