# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Integration tests for CLI validation command."""

from pathlib import Path
from textwrap import dedent

import pytest
from typer.testing import CliRunner

from algorithm_nexus.cli import app

runner = CliRunner()


@pytest.fixture
def temp_package_dir(tmp_path: Path) -> Path:
    """Create a temporary package directory structure."""
    package_dir = tmp_path / "packages" / "test-package"
    package_dir.mkdir(parents=True)
    return package_dir


def create_valid_nexus_yaml(package_dir: Path) -> None:
    """Create a valid nexus.yaml file."""
    nexus_yaml = package_dir / "nexus.yaml"
    nexus_yaml.write_text(
        dedent("""
            package:
              name: "test-package"
            """)
    )


def create_valid_model_structure(
    package_dir: Path, model_name: str = "test-model"
) -> None:
    """Create a valid model directory structure."""
    model_dir = package_dir / "models" / model_name
    model_dir.mkdir(parents=True)

    # Create model.yaml
    model_yaml = model_dir / "model.yaml"
    model_yaml.write_text(
        dedent("""
            model:
              id: "org/test-model"
              owner: "test-team"

              vllm:
                enabled: true
                plugins:
                  io_processors:
                    - "test-processor"
            """)
    )

    # Create optional usage.md
    (model_dir / "usage.md").write_text("# Usage\n\nTest model usage.")


class TestValidPackageStructure:
    """Tests for fully correct package structure."""

    def test_valid_package_passes_validation(self, temp_package_dir: Path) -> None:
        """Test that a fully valid package passes validation."""
        create_valid_nexus_yaml(temp_package_dir)
        create_valid_model_structure(temp_package_dir)

        result = runner.invoke(app, ["validate", str(temp_package_dir)])

        assert result.exit_code == 0
        assert "Validation Successful" in result.stdout

    def test_valid_package_with_multiple_models(self, temp_package_dir: Path) -> None:
        """Test validation with multiple models."""
        create_valid_nexus_yaml(temp_package_dir)

        # Create model structures
        for model_name in ["model-1", "model-2"]:
            model_dir = temp_package_dir / "models" / model_name
            model_dir.mkdir(parents=True)

            model_yaml = model_dir / "model.yaml"
            model_yaml.write_text(
                dedent("""
                    model:
                      id: "org/model"
                    """)
            )

            (model_dir / "usage.md").write_text("# Usage")

        result = runner.invoke(app, ["validate", str(temp_package_dir)])

        assert result.exit_code == 0
        assert "Validation Successful" in result.stdout


class TestMissingModelConfig:
    """Tests for missing model configuration files."""

    def test_missing_model_yaml(self, temp_package_dir: Path) -> None:
        """Test that missing model.yaml is detected."""
        create_valid_nexus_yaml(temp_package_dir)

        model_dir = temp_package_dir / "models" / "test-model"
        model_dir.mkdir(parents=True)
        (model_dir / "usage.md").write_text("# Usage")

        result = runner.invoke(app, ["validate", str(temp_package_dir)])

        assert result.exit_code == 1
        assert "Missing YAML file" in result.stdout


class TestMissingPackageConfig:
    """Tests for missing package configuration."""

    def test_missing_nexus_yaml(self, temp_package_dir: Path) -> None:
        """Test that missing nexus.yaml is detected."""
        result = runner.invoke(app, ["validate", str(temp_package_dir)])

        assert result.exit_code == 1
        assert "nexus.yaml" in result.stdout

    def test_empty_nexus_yaml(self, temp_package_dir: Path) -> None:
        """Test that empty nexus.yaml is detected."""
        nexus_yaml = temp_package_dir / "nexus.yaml"
        nexus_yaml.write_text("")

        result = runner.invoke(app, ["validate", str(temp_package_dir)])

        assert result.exit_code == 1
        assert "empty" in result.stdout.lower()


class TestMalformedPackageConfig:
    """Tests for malformed package configuration."""

    def test_invalid_yaml_syntax_in_nexus(self, temp_package_dir: Path) -> None:
        """Test that invalid YAML syntax in nexus.yaml is detected."""
        nexus_yaml = temp_package_dir / "nexus.yaml"
        nexus_yaml.write_text("package:\n  name: [invalid yaml")

        result = runner.invoke(app, ["validate", str(temp_package_dir)])

        assert result.exit_code == 1

    def test_yaml_list_instead_of_dict(self, temp_package_dir: Path) -> None:
        """Test that YAML containing a list instead of dict is rejected."""
        nexus_yaml = temp_package_dir / "nexus.yaml"
        nexus_yaml.write_text("- item1\n- item2\n")

        result = runner.invoke(app, ["validate", str(temp_package_dir)])

        assert result.exit_code == 1
        assert "must contain a YAML mapping at the top level" in result.stdout

    def test_yaml_string_instead_of_dict(self, temp_package_dir: Path) -> None:
        """Test that YAML containing a string instead of dict is rejected."""
        nexus_yaml = temp_package_dir / "nexus.yaml"
        nexus_yaml.write_text("just a string\n")

        result = runner.invoke(app, ["validate", str(temp_package_dir)])

        assert result.exit_code == 1
        assert "must contain a YAML mapping at the top level" in result.stdout
        assert "yaml" in result.stdout.lower()
