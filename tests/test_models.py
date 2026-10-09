# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for Pydantic models."""

from textwrap import dedent

import pytest
import yaml
from ado.schema.reference import ExperimentReference
from pydantic import ValidationError

from algorithm_nexus.models import (
    AlgorithmNexusModelConfig,
    AlgorithmNexusPackageConfig,
    BenchmarkInstance,
    BindingFileConfig,
    ExperimentConfig,
    ExperimentSpecifier,
    InstanceBinding,
    LogicalBenchmarkDefinition,
    ModelInfo,
    NexusPackageInfo,
    ProblemProperty,
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


class TestLogicalBenchmarkProperties:
    def test_logical_benchmark_problem_properties(self) -> None:
        """Test LogicalBenchmarkDefinition problemProperties field."""
        from algorithm_nexus.models import LogicalBenchmarkDefinition

        data = {
            "benchmarkIdentifier": "test_bench",
            "description": "A test benchmark",
            "problemProperties": [
                {"identifier": "graph"},
                {"identifier": "num_nodes"},
                {"identifier": "density"},
            ],
        }
        config = LogicalBenchmarkDefinition.model_validate(data)
        props = config.problemProperties
        assert len(props) == 3
        assert props[0].identifier == "graph"
        assert props[1].identifier == "num_nodes"
        assert props[2].identifier == "density"

    def test_logical_benchmark_metadata_valid(self) -> None:
        """Test LogicalBenchmarkDefinition with valid metadata."""
        config = LogicalBenchmarkDefinition(
            benchmarkIdentifier="test_bench",
            description="A test benchmark",
            problemProperties=[ProblemProperty(identifier="num_nodes")],
            metadata={
                "data_source_version": "v2.1.0",
                "owning_team": "platform-perf",
            },
        )
        assert config.metadata == {
            "data_source_version": "v2.1.0",
            "owning_team": "platform-perf",
        }

    def test_logical_benchmark_metadata_max_length(self) -> None:
        """Test LogicalBenchmarkDefinition metadata allows 4096 character keys and values."""
        long_key = "k" * 4096
        long_val = "v" * 4096
        config = LogicalBenchmarkDefinition(
            benchmarkIdentifier="test_bench",
            description="A test benchmark",
            problemProperties=[ProblemProperty(identifier="num_nodes")],
            metadata={long_key: long_val},
        )
        assert config.metadata is not None
        assert config.metadata[long_key] == long_val

    def test_logical_benchmark_metadata_key_too_long(self) -> None:
        """Test LogicalBenchmarkDefinition rejects metadata key longer than 4096 characters."""
        with pytest.raises(ValidationError):
            LogicalBenchmarkDefinition(
                benchmarkIdentifier="test_bench",
                description="A test benchmark",
                problemProperties=[ProblemProperty(identifier="num_nodes")],
                metadata={"k" * 4097: "valid_value"},
            )

    def test_logical_benchmark_metadata_value_too_long(self) -> None:
        """Test LogicalBenchmarkDefinition rejects metadata value longer than 4096 characters."""
        with pytest.raises(ValidationError):
            LogicalBenchmarkDefinition(
                benchmarkIdentifier="test_bench",
                description="A test benchmark",
                problemProperties=[ProblemProperty(identifier="num_nodes")],
                metadata={"valid_key": "v" * 4097},
            )

    def test_logical_benchmark_metadata_non_string_value_rejected(self) -> None:
        """Test LogicalBenchmarkDefinition rejects non-string metadata values."""
        with pytest.raises(ValidationError):
            LogicalBenchmarkDefinition(
                benchmarkIdentifier="test_bench",
                description="A test benchmark",
                problemProperties=[ProblemProperty(identifier="num_nodes")],
                metadata={"nested": {"key": "val"}},  # type: ignore[dict-item]
            )


# Made with Bob


class TestExperimentConfig:
    """Tests for ExperimentConfig and ExperimentSpecifier models."""

    def test_valid_pypi_specifier(self) -> None:
        """Test valid experiment config with a PyPI package name."""
        data = {
            "experiment_package": {
                "requirement_specifier": "sorting-benchmarks>=1.0.0",
                "experiments": ["bubble_sort", "merge_sort"],
            }
        }
        config = ExperimentConfig.model_validate(data)
        assert (
            config.experiment_package.requirement_specifier
            == "sorting-benchmarks>=1.0.0"
        )
        assert config.experiment_package.experiments == ["bubble_sort", "merge_sort"]

    def test_valid_github_https_url(self) -> None:
        """Test valid experiment config with a GitHub HTTPS URL."""
        data = {
            "experiment_package": {
                "requirement_specifier": "https://github.com/org/repo.git",
                "experiments": ["exp_one"],
            }
        }
        config = ExperimentConfig.model_validate(data)
        assert (
            config.experiment_package.requirement_specifier
            == "https://github.com/org/repo.git"
        )

    def test_valid_git_plus_prefix(self) -> None:
        """Test valid experiment config with git+ prefixed URL."""
        data = {
            "experiment_package": {
                "requirement_specifier": "git+https://github.com/org/repo@main",
                "experiments": ["exp_one"],
            }
        }
        config = ExperimentConfig.model_validate(data)
        assert (
            config.experiment_package.requirement_specifier
            == "git+https://github.com/org/repo@main"
        )

    def test_local_path_dot_slash_rejected(self) -> None:
        """Test that local path starting with ./ is rejected."""
        data = {
            "experiment_package": {
                "requirement_specifier": "./packages/my-benchmark",
                "experiments": ["exp_one"],
            }
        }
        with pytest.raises(ValidationError) as exc_info:
            ExperimentConfig.model_validate(data)
        assert "local paths are not allowed" in str(exc_info.value).lower()

    def test_local_path_absolute_rejected(self) -> None:
        """Test that absolute local path is rejected."""
        data = {
            "experiment_package": {
                "requirement_specifier": "/usr/local/my-pkg",
                "experiments": ["exp_one"],
            }
        }
        with pytest.raises(ValidationError) as exc_info:
            ExperimentConfig.model_validate(data)
        assert "local paths are not allowed" in str(exc_info.value).lower()

    def test_local_path_tilde_rejected(self) -> None:
        """Test that tilde-prefixed path is rejected."""
        data = {
            "experiment_package": {
                "requirement_specifier": "~/my-pkg",
                "experiments": ["exp_one"],
            }
        }
        with pytest.raises(ValidationError) as exc_info:
            ExperimentConfig.model_validate(data)
        assert "local paths are not allowed" in str(exc_info.value).lower()

    def test_empty_experiments_list_rejected(self) -> None:
        """Test that an empty experiments list is rejected."""
        data = {
            "experiment_package": {
                "requirement_specifier": "my-package",
                "experiments": [],
            }
        }
        with pytest.raises(ValidationError) as exc_info:
            ExperimentConfig.model_validate(data)
        assert "experiments" in str(exc_info.value).lower()

    def test_missing_requirement_specifier_rejected(self) -> None:
        """Test that missing requirement_specifier is rejected."""
        data = {
            "experiment_package": {
                "experiments": ["exp_one"],
            }
        }
        with pytest.raises(ValidationError) as exc_info:
            ExperimentConfig.model_validate(data)
        assert "requirement_specifier" in str(exc_info.value)

    def test_extra_fields_forbidden(self) -> None:
        """Test that extra fields are rejected."""
        data = {
            "experiment_package": {
                "requirement_specifier": "my-package",
                "experiments": ["exp_one"],
                "extra_field": "not allowed",
            }
        }
        with pytest.raises(ValidationError) as exc_info:
            ExperimentConfig.model_validate(data)
        assert "extra_field" in str(exc_info.value).lower()

    def test_extra_top_level_fields_forbidden(self) -> None:
        """Test that extra top-level fields are rejected."""
        data = {
            "experiment_package": {
                "requirement_specifier": "my-package",
                "experiments": ["exp_one"],
            },
            "unexpected": "value",
        }
        with pytest.raises(ValidationError) as exc_info:
            ExperimentConfig.model_validate(data)
        assert "unexpected" in str(exc_info.value).lower()

    def test_valid_metadata(self) -> None:
        """Test valid experiment config with metadata."""
        config = ExperimentConfig(
            experiment_package=ExperimentSpecifier(
                requirement_specifier="my-package",
                experiments=["exp_one"],
            ),
            metadata={
                "author": "IBM",
                "tier": "production",
            },
        )
        assert config.metadata == {"author": "IBM", "tier": "production"}

    def test_metadata_value_too_long_rejected(self) -> None:
        """Test that metadata value exceeding 4096 chars is rejected."""
        with pytest.raises(ValidationError):
            ExperimentConfig(
                experiment_package=ExperimentSpecifier(
                    requirement_specifier="my-package",
                    experiments=["exp_one"],
                ),
                metadata={
                    "author": "a" * 4097,
                },
            )


class TestBenchmarkInstanceMetadata:
    """Tests for BenchmarkInstance metadata validation."""

    def test_valid_metadata(self) -> None:
        instance = BenchmarkInstance(
            instanceIdentifier="small_model_8b",
            benchmarkIdentifier="inference_serving",
            metadata={
                "region": "us-south",
                "endpoint-url": "http://ibm.com/my-endpoint/",
            },
        )
        assert instance.metadata == {
            "region": "us-south",
            "endpoint-url": "http://ibm.com/my-endpoint/",
        }

    def test_metadata_optional(self) -> None:
        instance = BenchmarkInstance(
            instanceIdentifier="small_model_8b",
            benchmarkIdentifier="inference_serving",
        )
        assert instance.metadata is None

    def test_metadata_non_string_value_rejected(self) -> None:
        with pytest.raises(ValidationError):
            BenchmarkInstance(
                instanceIdentifier="small_model_8b",
                benchmarkIdentifier="inference_serving",
                metadata={"tags": ["a", "b"]},  # type: ignore[dict-item]
            )


class TestInstanceBindingMetadata:
    """Tests for InstanceBinding and BindingFileConfig metadata validation."""

    def test_instance_binding_valid_metadata(self) -> None:
        binding = InstanceBinding(
            instanceBindingIdentifier="my_binding",
            instanceReference="inference_serving/small_model_8b",
            experiment=ExperimentReference(
                actuatorIdentifier="my_actuator", experimentIdentifier="exp1"
            ),
            metadata={"run_label": "nightly-2025-07-01"},
        )
        assert binding.metadata == {"run_label": "nightly-2025-07-01"}

    def test_binding_file_config_valid_metadata(self) -> None:
        config = BindingFileConfig(
            instanceBindingIdentifier="my_binding",
            instanceReference="inference_serving/small_model_8b",
            experiment=ExperimentReference(
                actuatorIdentifier="my_actuator",
                experimentIdentifier="exp1",
            ),
            metadata={"run_label": "nightly-2025-07-01"},
        )
        assert config.metadata == {"run_label": "nightly-2025-07-01"}

    def test_binding_metadata_key_too_long_rejected(self) -> None:
        with pytest.raises(ValidationError):
            BindingFileConfig(
                instanceBindingIdentifier="my_binding",
                instanceReference="inference_serving/small_model_8b",
                experiment=ExperimentReference(
                    actuatorIdentifier="my_actuator",
                    experimentIdentifier="exp1",
                ),
                metadata={"k" * 4097: "val"},
            )
