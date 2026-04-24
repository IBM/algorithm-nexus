# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for Pydantic models."""

from textwrap import dedent

import pytest
import yaml
from pydantic import ValidationError

from algorithm_nexus.models import (
    ModelConfig,
    ModelTestingConfig,
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

    def test_with_agent_skills(self) -> None:
        """Test package config with agent skills."""
        data = {
            "name": "test-package",
            "agent_skills": {
                "embedded": True,
            },
        }
        config = PackageConfig(**data)
        assert config.agent_skills is not None
        assert config.agent_skills.embedded is True

    def test_agent_skills_embedded_false_and_external(self) -> None:
        """Test that embedded=False and external can coexist."""
        data = {
            "name": "test-package",
            "agent_skills": {
                "embedded": False,
                "external": "https://example.com/skills",
            },
        }
        config = PackageConfig(**data)
        assert config.agent_skills is not None
        assert config.agent_skills.embedded is False
        assert config.agent_skills.external == "https://example.com/skills"

    def test_agent_skills_embedded_none_and_external(self) -> None:
        """Test that embedded=None and external can coexist."""
        data = {
            "name": "test-package",
            "agent_skills": {
                "external": "https://example.com/skills",
            },
        }
        config = PackageConfig(**data)
        assert config.agent_skills is not None
        assert config.agent_skills.embedded is None
        assert config.agent_skills.external == "https://example.com/skills"

    def test_agent_skills_embedded_true_and_external_fails(self) -> None:
        """Test that embedded=True and external cannot coexist."""
        data = {
            "name": "test-package",
            "agent_skills": {
                "embedded": True,
                "external": "https://example.com/skills",
            },
        }
        with pytest.raises(ValidationError) as exc_info:
            PackageConfig(**data)
        assert "embedded must be False or None when external is defined" in str(
            exc_info.value
        )


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


class TestTestingConfig:
    """Tests for TestingConfig model."""

    def test_valid_testing_config(self) -> None:
        """Test valid testing configuration."""
        data = {
            "hardware": {
                "cpu": {
                    "cores": 4,
                }
            },
            "commands": ["pytest tests/"],
        }
        config = ModelTestingConfig(**data)
        assert config.commands == ["pytest tests/"]
        assert config.hardware.cpu.cores == 4

    def test_missing_commands(self) -> None:
        """Test that missing commands is detected."""
        data = {
            "hardware": {
                "cpu": {
                    "cores": 4,
                }
            },
        }
        with pytest.raises(ValidationError) as exc_info:
            ModelTestingConfig(**data)
        assert "commands" in str(exc_info.value)

    def test_vllm_testing_required_when_vllm_enabled(self) -> None:
        """Test that vLLM testing is required when vLLM is enabled."""
        # This validation happens at the ModelConfig level


class TestModelConfig:
    """Tests for ModelConfig model."""

    def test_valid_model_config(self) -> None:
        """Test valid model configuration."""
        data = {
            "id": "org/model",
            "testing": {
                "hardware": {
                    "cpu": {
                        "cores": 4,
                    }
                },
                "commands": ["pytest tests/"],
            },
        }
        config = ModelConfig(**data)
        assert config.id == "org/model"
        assert config.testing.commands == ["pytest tests/"]

    def test_model_without_vllm(self) -> None:
        """Test that models without vLLM configuration are valid."""
        data = {
            "id": "org/model",
            "testing": {
                "hardware": {
                    "cpu": {
                        "cores": 4,
                    }
                },
                "commands": ["pytest tests/"],
            },
        }
        config = ModelConfig(**data)
        assert config.id == "org/model"
        assert config.vllm is None
        assert config.testing.vllm is None

    def test_missing_model_id(self) -> None:
        """Test that missing model.id is detected."""
        data = {
            "testing": {
                "hardware": {
                    "cpu": {
                        "cores": 4,
                    }
                },
                "commands": ["pytest tests/"],
            }
        }
        with pytest.raises(ValidationError) as exc_info:
            ModelConfig(**data)
        assert "id" in str(exc_info.value)

    def test_vllm_enabled_requires_vllm_testing(self) -> None:
        """Test that vLLM enabled requires vLLM testing."""
        data = {
            "id": "org/model",
            "vllm": {
                "enabled": True,
                "plugins": {"io_processors": ["processor1"]},
            },
            "testing": {
                "hardware": {
                    "cpu": {
                        "cores": 4,
                    }
                },
                "commands": ["pytest tests/"],
            },
        }
        with pytest.raises(ValidationError) as exc_info:
            ModelConfig(**data)
        assert "vllm" in str(exc_info.value).lower()
        assert "testing" in str(exc_info.value).lower()

    def test_vllm_disabled_fails(self) -> None:
        """Test that vLLM enabled=False is rejected."""
        data = {
            "id": "org/model",
            "vllm": {
                "enabled": False,
            },
            "testing": {
                "hardware": {
                    "cpu": {
                        "cores": 4,
                    }
                },
                "commands": ["pytest tests/"],
            },
        }
        with pytest.raises(ValidationError) as exc_info:
            ModelConfig(**data)
        assert "enabled" in str(exc_info.value).lower()

    def test_vllm_with_vllm_testing(self) -> None:
        """Test valid vLLM configuration with testing."""
        data = {
            "id": "org/model",
            "vllm": {
                "enabled": True,
                "plugins": {"io_processors": ["processor1"]},
            },
            "testing": {
                "hardware": {
                    "cpu": {
                        "cores": 4,
                    }
                },
                "commands": ["pytest tests/"],
                "vllm": {
                    "commands": ["pytest tests/test_vllm.py"],
                },
            },
        }
        config = ModelConfig(**data)
        assert config.vllm is not None
        assert config.testing.vllm is not None


class TestModelYAML:
    """Tests for ModelYAML model."""

    def test_valid_model_yaml(self) -> None:
        """Test valid model.yaml structure."""
        yaml_content = dedent("""
            model:
              id: "org/test-model"
              testing:
                hardware:
                  cpu:
                    cores: 4
                commands:
                  - "pytest tests/"
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
              testing:
                hardware:
                  cpu:
                    cores: 4
                commands:
                  - "pytest tests/"
                vllm:
                  commands:
                    - "pytest tests/test_vllm.py"
            """)
        data = yaml.safe_load(yaml_content)
        model_yaml = ModelYAML(**data)
        assert model_yaml.model.vllm is not None
        assert model_yaml.model.vllm.plugins is not None


class TestNexusYAML:
    """Tests for NexusYAML model."""

    def test_valid_nexus_yaml(self) -> None:
        """Test valid nexus.yaml structure."""
        yaml_content = dedent("""
            package:
              name: "test-package"

            models:
              - test-model
            """)
        data = yaml.safe_load(yaml_content)
        nexus_yaml = NexusYAML(**data)
        assert nexus_yaml.package.name == "test-package"
        assert nexus_yaml.models == ["test-model"]

    def test_nexus_yaml_with_multiple_models(self) -> None:
        """Test nexus.yaml with multiple models."""
        yaml_content = dedent("""
            package:
              name: "test-package"

            models:
              - model-1
              - model-2
              - model-3
            """)
        data = yaml.safe_load(yaml_content)
        nexus_yaml = NexusYAML(**data)
        assert nexus_yaml.models is not None
        assert len(nexus_yaml.models) == 3

    def test_nexus_yaml_without_models(self) -> None:
        """Test nexus.yaml without models list."""
        yaml_content = dedent("""
            package:
              name: "test-package"
            """)
        data = yaml.safe_load(yaml_content)
        nexus_yaml = NexusYAML(**data)
        assert nexus_yaml.models is None or nexus_yaml.models == []
