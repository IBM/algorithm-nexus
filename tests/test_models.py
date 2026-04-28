# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for Pydantic models."""

from textwrap import dedent

import pytest
import yaml
from pydantic import ValidationError

from algorithm_nexus.models import (
    ModelConfig,
    ModelYAML,
    NexusYAML,
    PackageConfig,
    VLLMConfig,
)


class TestPackageConfig:
    """Tests for PackageConfig model."""

    def test_valid_package_config(self) -> None:
        """Test valid package configuration."""
        data = {
            "name": "test-package",
        }
        config = PackageConfig(**data)
        assert config.name == "test-package"

    def test_missing_name(self) -> None:
        """Test that missing name is detected."""
        data = {}
        with pytest.raises(ValidationError) as exc_info:
            PackageConfig(**data)
        assert "name" in str(exc_info.value)


class TestVLLMConfig:
    """Tests for VLLMConfig model."""

    def test_vllm_with_plugins(self) -> None:
        """Test vLLM with plugins."""
        data = {
            "enabled": True,
            "plugins": {"io_processors": ["processor1", "processor2"]},
        }
        config = VLLMConfig(**data)
        assert config.enabled is True
        assert config.plugins is not None
        assert len(config.plugins.io_processors) == 2

    def test_vllm_with_general_plugin(self) -> None:
        """Test vLLM with general plugin."""
        data = {
            "enabled": True,
            "plugins": {"general": "my-vllm-plugin"},
        }
        config = VLLMConfig(**data)
        assert config.enabled is True
        assert config.plugins is not None
        assert config.plugins.general == "my-vllm-plugin"

    def test_vllm_disabled_fails(self) -> None:
        """Test that enabled=False is rejected."""
        data = {"enabled": False}
        with pytest.raises(ValidationError) as exc_info:
            VLLMConfig(**data)
        assert "enabled" in str(exc_info.value).lower()

    def test_vllm_missing_enabled_fails(self) -> None:
        """Test that missing enabled field is detected."""
        data = {"plugins": {"general": "my-plugin"}}
        with pytest.raises(ValidationError) as exc_info:
            VLLMConfig(**data)
        assert "enabled" in str(exc_info.value)


class TestModelConfig:
    """Tests for ModelConfig model."""

    def test_valid_model_config(self) -> None:
        """Test valid model configuration."""
        data = {
            "id": "org/model",
        }
        config = ModelConfig(**data)
        assert config.id == "org/model"

    def test_model_without_vllm(self) -> None:
        """Test that models without vLLM configuration are valid."""
        data = {
            "id": "org/model",
        }
        config = ModelConfig(**data)
        assert config.id == "org/model"
        assert config.vllm is None

    def test_missing_model_id(self) -> None:
        """Test that missing model.id is detected."""
        data = {}
        with pytest.raises(ValidationError) as exc_info:
            ModelConfig(**data)
        assert "id" in str(exc_info.value)

    def test_model_with_owner(self) -> None:
        """Test model configuration with owner."""
        data = {
            "id": "org/model",
            "owner": "github-username",
        }
        config = ModelConfig(**data)
        assert config.id == "org/model"
        assert config.owner == "github-username"

    def test_vllm_disabled_fails(self) -> None:
        """Test that vLLM enabled=False is rejected."""
        data = {
            "id": "org/model",
            "vllm": {
                "enabled": False,
            },
        }
        with pytest.raises(ValidationError) as exc_info:
            ModelConfig(**data)
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
        config = ModelConfig(**data)
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
        model_yaml = ModelYAML(**data)
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
        model_yaml = ModelYAML(**data)
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
        nexus_yaml = NexusYAML(**data)
        assert nexus_yaml.package.name == "test-package"

    def test_nexus_yaml_minimal(self) -> None:
        """Test minimal nexus.yaml structure."""
        yaml_content = dedent("""
            package:
              name: "minimal-package"
            """)
        data = yaml.safe_load(yaml_content)
        nexus_yaml = NexusYAML(**data)
        assert nexus_yaml.package.name == "minimal-package"
