# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for Pydantic models."""

from textwrap import dedent

import pytest
import yaml
from pydantic import ValidationError

from algorithm_nexus.models import (
    AlgorithmNexusModelConfig,
    AlgorithmNexusPackageConfig,
    ModelInfo,
    NexusPackageInfo,
    VLLMConfig,
)


class TestPackageConfig:
    """Tests for PackageConfig model."""

    def test_valid_package_config(self) -> None:
        """Test valid package configuration."""
        data = {
            "name": "test-package",
        }
        config = NexusPackageInfo.model_validate(data)
        assert config.name == "test-package"

    def test_missing_name(self) -> None:
        """Test that missing name is detected."""
        data = {}
        with pytest.raises(ValidationError) as exc_info:
            NexusPackageInfo.model_validate(data)
        assert "name" in str(exc_info.value)


class TestVLLMConfig:
    """Tests for VLLMConfig model."""

    def test_vllm_with_plugins(self) -> None:
        """Test vLLM with plugins."""
        data = {
            "enabled": True,
            "plugins": {"io_processors": ["processor1", "processor2"]},
        }
        config = VLLMConfig.model_validate(data)

        assert config.enabled is True
        assert config.plugins is not None
        assert len(config.plugins.io_processors) == 2

    def test_vllm_with_general_plugin(self) -> None:
        """Test vLLM with general plugin."""
        data = {
            "enabled": True,
            "plugins": {"general": "my-vllm-plugin"},
        }
        config = VLLMConfig.model_validate(data)

        assert config.enabled is True
        assert config.plugins is not None
        assert config.plugins.general == "my-vllm-plugin"

    def test_vllm_disabled_fails(self) -> None:
        """Test that enabled=False is rejected."""
        data = {"enabled": False}
        with pytest.raises(ValidationError) as exc_info:
            VLLMConfig.model_validate(data)

        assert "enabled" in str(exc_info.value).lower()

    def test_vllm_missing_enabled_fails(self) -> None:
        """Test that missing enabled field is detected."""
        data = {"plugins": {"general": "my-plugin"}}
        with pytest.raises(ValidationError) as exc_info:
            VLLMConfig.model_validate(data)

        assert "enabled" in str(exc_info.value)


class TestModelConfig:
    """Tests for ModelConfig model."""

    def test_valid_model_config(self) -> None:
        """Test valid model configuration."""
        data = {
            "id": "org/model",
        }
        config = ModelInfo.model_validate(data)

        assert config.id == "org/model"

    def test_model_without_vllm(self) -> None:
        """Test that models without vLLM configuration are valid."""
        data = {
            "id": "org/model",
        }
        config = ModelInfo.model_validate(data)

        assert config.id == "org/model"
        assert config.vllm is None

    def test_missing_model_id(self) -> None:
        """Test that missing model.id is detected."""
        data = {}
        with pytest.raises(ValidationError) as exc_info:
            ModelInfo.model_validate(data)

        assert "id" in str(exc_info.value)

    def test_valid_model_ids(self) -> None:
        """Test valid HuggingFace model IDs."""
        valid_ids = [
            "org/model",
            "my-org/my-model",
            "org123/model456",
            "a1/b2",  # minimum length (2 chars each)
            "a" * 42 + "/" + "b" * 42,  # maximum length for org (42 chars)
            "a" * 42 + "/" + "b" * 96,  # maximum length for model (96 chars)
            "user-name/model-name",
            "org1-2/model3-4",
            "org/model-1.0",  # model with version number
            "org/model-2.0.1",  # model with semantic version
            "ibm-nasa-geospatial/Prithvi-EO-2.0-300M-TL",  # real-world example
            "org.name/model.name",  # dots in both parts
            "org/model.1.2.3-beta",  # complex version with dots and dash
            "org/model_name",  # underscore in model name
            "org_name/model_name",  # underscores in both parts
            "org/model_v1.0",  # underscore and dot in model
            "org/my_model-2.0",  # combination of underscore, dash, and dot in model
            "org_name/model",  # underscore in org name
            "org.name/model",  # dot in org name
            "my_org.v2/model",  # underscore and dot in org name
            "org.v1_test/model-name",  # dots and underscores in org
        ]
        for model_id in valid_ids:
            data = {"id": model_id}
            config = ModelInfo.model_validate(data)

            assert config.id == model_id

    def test_invalid_model_ids(self) -> None:
        """Test invalid HuggingFace model IDs."""
        invalid_ids = [
            "org",  # missing slash and model name
            "/model",  # missing org name
            "org/",  # missing model name
            "-org/model",  # starts with dash
            "org-/model",  # ends with dash
            "org/-model",  # model starts with dash
            "org/model-",  # model ends with dash
            "org--name/model",  # double dash in org
            "org/model--name",  # double dash in model
            "123/456",  # digit-only names
            "123/model",  # digit-only org
            "org/456",  # digit-only model
            "o/model",  # org too short (1 char)
            "org/m",  # model too short (1 char)
            "a" * 43 + "/model",  # org too long (43 chars)
            "org/" + "b" * 97,  # model too long (97 chars)
            "org@name/model",  # illegal character in org
            "org/model@name",  # illegal character in model
            "org name/model",  # space in org
            "org/model name",  # space in model
            "org/model/extra",  # too many slashes
        ]
        for model_id in invalid_ids:
            data = {"id": model_id}
            with pytest.raises(ValidationError) as exc_info:
                ModelInfo.model_validate(data)

            assert "id" in str(exc_info.value).lower()

    def test_model_with_owner(self) -> None:
        """Test model configuration with owner."""
        data = {
            "id": "org/model",
            "owner": "github-username",
        }
        config = ModelInfo.model_validate(data)

        assert config.id == "org/model"
        assert config.owner == "github-username"

    def test_model_with_invalid_owner_id(self) -> None:
        """Test model configuration with owner."""
        data = {
            "id": "org/model",
        }

        # starts with a dash
        data["owner"] = "-github-username"
        with pytest.raises(ValidationError):
            ModelInfo.model_validate(data)

        # ends with a dash
        data["owner"] = "github-username-"
        with pytest.raises(ValidationError):
            ModelInfo.model_validate(data)

        # scontaines consecutive dashes
        data["owner"] = "github--username"
        with pytest.raises(ValidationError):
            ModelInfo.model_validate(data)

        # contains an illegal character
        data["owner"] = "github-usern@me"
        with pytest.raises(ValidationError):
            ModelInfo.model_validate(data)

        # longer than 39 characters
        data["owner"] = "ThisGitHubUsernameIsDefinitelyTooLongToBeValid"
        with pytest.raises(ValidationError):
            ModelInfo.model_validate(data)

    def test_vllm_disabled_fails(self) -> None:
        """Test that vLLM enabled=False is rejected."""
        data = {
            "id": "org/model",
            "vllm": {
                "enabled": False,
            },
        }
        with pytest.raises(ValidationError) as exc_info:
            ModelInfo.model_validate(data)

        assert "enabled" in str(exc_info.value).lower()

    def test_vllm_with_plugins(self) -> None:
        """Test valid vLLM configuration with plugins."""
        data = {
            "id": "org/model",
            "vllm": {
                "enabled": True,
                "plugins": {"io_processors": ["processor1"]},
            },
        }
        config = ModelInfo.model_validate(data)

        assert config.vllm is not None
        assert config.vllm.plugins is not None
        assert config.vllm.plugins.io_processors == ["processor1"]


class TestModelYAML:
    """Tests for ModelYAML model."""

    def test_valid_model_yaml(self) -> None:
        """Test valid model.yaml structure."""
        yaml_content = dedent("""
            model:
              id: "org/test-model"
            """)
        data = yaml.safe_load(yaml_content)
        model_yaml = AlgorithmNexusModelConfig.model_validate(data)

        assert model_yaml.model.id == "org/test-model"

    def test_model_yaml_with_vllm(self) -> None:
        """Test model.yaml with vLLM configuration."""
        yaml_content = dedent("""
            model:
              id: "org/test-model"
              vllm:
                enabled: true
                plugins:
                  io_processors:
                    - "processor1"
            """)
        data = yaml.safe_load(yaml_content)
        model_yaml = AlgorithmNexusModelConfig.model_validate(data)

        assert model_yaml.model.vllm is not None
        assert model_yaml.model.vllm.plugins is not None
        assert model_yaml.model.vllm.plugins.io_processors == ["processor1"]


class TestNexusYAML:
    """Tests for NexusYAML model."""

    def test_valid_nexus_yaml(self) -> None:
        """Test valid nexus.yaml structure."""
        yaml_content = dedent("""
            package:
              name: "test-package"
            """)
        data = yaml.safe_load(yaml_content)
        nexus_yaml = AlgorithmNexusPackageConfig.model_validate(data)

        assert nexus_yaml.package.name == "test-package"

    def test_nexus_yaml_minimal(self) -> None:
        """Test minimal nexus.yaml structure."""
        yaml_content = dedent("""
            package:
              name: "minimal-package"
            """)
        data = yaml.safe_load(yaml_content)
        nexus_yaml = AlgorithmNexusPackageConfig.model_validate(data)

        assert nexus_yaml.package.name == "minimal-package"


class TestBenchmarkPackage:
    """Tests for BenchmarkPackage model."""

    def test_valid_benchmark_package(self) -> None:
        """Test valid benchmark package configuration."""
        data = {
            "requirement_specifier": "my-benchmark-package>=1.0.0",
            "experiments": ["exp-1", "exp-2"],
        }
        bench_pkg = AlgorithmNexusPackageConfig.model_validate(
            {"package": {"name": "test", "benchmark_packages": [data]}}
        )

        assert bench_pkg.package.benchmark_packages is not None
        assert len(bench_pkg.package.benchmark_packages) == 1
        assert (
            bench_pkg.package.benchmark_packages[0].requirement_specifier
            == "my-benchmark-package>=1.0.0"
        )
        assert bench_pkg.package.benchmark_packages[0].experiments == ["exp-1", "exp-2"]

    def test_benchmark_package_with_url(self) -> None:
        """Test benchmark package with URL requirement specifier."""
        data = {
            "requirement_specifier": "git+https://github.com/org/repo.git",
            "experiments": ["exp-1"],
        }
        bench_pkg = AlgorithmNexusPackageConfig.model_validate(
            {"package": {"name": "test", "benchmark_packages": [data]}}
        )

        assert bench_pkg.package.benchmark_packages is not None
        assert (
            bench_pkg.package.benchmark_packages[0].requirement_specifier
            == "git+https://github.com/org/repo.git"
        )

    def test_benchmark_package_with_local_path(self) -> None:
        """Test benchmark package with local path requirement specifier."""
        data = {
            "requirement_specifier": "./packages/my-benchmark",
            "experiments": ["exp-1"],
        }
        bench_pkg = AlgorithmNexusPackageConfig.model_validate(
            {"package": {"name": "test", "benchmark_packages": [data]}}
        )

        assert bench_pkg.package.benchmark_packages is not None
        assert (
            bench_pkg.package.benchmark_packages[0].requirement_specifier
            == "./packages/my-benchmark"
        )

    def test_benchmark_package_empty_experiments_fails(self) -> None:
        """Test that empty experiments list is rejected."""
        data = {
            "requirement_specifier": "my-benchmark-package",
            "experiments": [],
        }
        with pytest.raises(ValidationError) as exc_info:
            AlgorithmNexusPackageConfig.model_validate(
                {"package": {"name": "test", "benchmark_packages": [data]}}
            )

        assert "experiments" in str(exc_info.value).lower()

    def test_benchmark_package_missing_requirement_specifier_fails(self) -> None:
        """Test that missing requirement_specifier is rejected."""
        data = {
            "experiments": ["exp-1"],
        }
        with pytest.raises(ValidationError) as exc_info:
            AlgorithmNexusPackageConfig.model_validate(
                {"package": {"name": "test", "benchmark_packages": [data]}}
            )

        assert "requirement_specifier" in str(exc_info.value)

    def test_benchmark_package_missing_experiments_fails(self) -> None:
        """Test that missing experiments is rejected."""
        data = {
            "requirement_specifier": "my-benchmark-package",
        }
        with pytest.raises(ValidationError) as exc_info:
            AlgorithmNexusPackageConfig.model_validate(
                {"package": {"name": "test", "benchmark_packages": [data]}}
            )

        assert "experiments" in str(exc_info.value)

    def test_benchmark_package_empty_requirement_specifier_fails(self) -> None:
        """Test that empty requirement_specifier is rejected."""
        data = {
            "requirement_specifier": "",
            "experiments": ["exp-1"],
        }
        with pytest.raises(ValidationError) as exc_info:
            AlgorithmNexusPackageConfig.model_validate(
                {"package": {"name": "test", "benchmark_packages": [data]}}
            )

        assert "requirement_specifier" in str(exc_info.value).lower()

    def test_benchmark_package_extra_fields_forbidden(self) -> None:
        """Test that extra fields are forbidden (extra='forbid')."""
        data = {
            "requirement_specifier": "my-benchmark-package",
            "experiments": ["exp-1"],
            "extra_field": "not allowed",
        }
        with pytest.raises(ValidationError) as exc_info:
            AlgorithmNexusPackageConfig.model_validate(
                {"package": {"name": "test", "benchmark_packages": [data]}}
            )

        assert "extra_field" in str(exc_info.value).lower()

    def test_benchmark_package_invalid_experiments_type(self) -> None:
        """Test that invalid experiments type is rejected."""
        data = {
            "requirement_specifier": "my-benchmark-package",
            "experiments": "not-a-list",
        }
        with pytest.raises(ValidationError) as exc_info:
            AlgorithmNexusPackageConfig.model_validate(
                {"package": {"name": "test", "benchmark_packages": [data]}}
            )

        assert "experiments" in str(exc_info.value).lower()

    def test_multiple_benchmark_packages(self) -> None:
        """Test multiple benchmark packages in a single nexus package."""
        data = [
            {
                "requirement_specifier": "benchmark-pkg-1",
                "experiments": ["exp-1"],
            },
            {
                "requirement_specifier": "benchmark-pkg-2",
                "experiments": ["exp-2", "exp-3"],
            },
        ]
        bench_pkg = AlgorithmNexusPackageConfig.model_validate(
            {"package": {"name": "test", "benchmark_packages": data}}
        )

        assert bench_pkg.package.benchmark_packages is not None
        assert len(bench_pkg.package.benchmark_packages) == 2
        assert (
            bench_pkg.package.benchmark_packages[0].requirement_specifier
            == "benchmark-pkg-1"
        )
        assert (
            bench_pkg.package.benchmark_packages[1].requirement_specifier
            == "benchmark-pkg-2"
        )

    def test_nexus_package_without_benchmark_packages(self) -> None:
        """Test that benchmark_packages is optional."""
        data = {"package": {"name": "test"}}
        nexus_pkg = AlgorithmNexusPackageConfig.model_validate(data)

        assert nexus_pkg.package.benchmark_packages is None

    def test_nexus_package_with_null_benchmark_packages(self) -> None:
        """Test that benchmark_packages can be explicitly null."""
        data = {"package": {"name": "test", "benchmark_packages": None}}
        nexus_pkg = AlgorithmNexusPackageConfig.model_validate(data)

        assert nexus_pkg.package.benchmark_packages is None


# Made with Bob
