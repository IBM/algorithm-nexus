# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Pydantic models for Nexus package YAML validation."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class AgentSkills(BaseModel):
    """Agent skills configuration."""

    embedded: bool | None = Field(
        None, description="Whether agent skills are embedded in the package"
    )
    external: str | None = Field(
        None, description="External agent skills reference or URL"
    )

    @model_validator(mode="after")
    def validate_mutually_exclusive(self) -> AgentSkills:
        """Validate that if both embedded and external are defined, embedded must be False or None."""
        if self.external is not None and self.embedded is True:
            raise ValueError(
                "embedded must be False or None when external is defined. "
                "Agent skills cannot be both embedded and external."
            )
        return self


class PackageConfig(BaseModel):
    """Package-level configuration."""

    name: str = Field(..., min_length=1, description="Python package name")
    agent_skills: AgentSkills | None = Field(
        None, description="Agent skills configuration for this package"
    )


class VLLMPlugins(BaseModel):
    """vLLM plugins configuration."""

    general: str | None = Field(None, description="General vLLM plugin configuration")
    io_processors: list[str] | None = Field(
        None, description="List of I/O processor plugins for vLLM"
    )


class VLLMConfig(BaseModel):
    """vLLM serving configuration.

    Should only be defined for models that require additional vLLM plugins
    and belong to a Nexus Package targeting the product or candidate distribution variants.
    """

    enabled: Literal[True] = Field(
        ..., description="Whether vLLM serving is enabled for this model"
    )
    plugins: VLLMPlugins | None = Field(None, description="vLLM plugins configuration")


class GPUConfig(BaseModel):
    """GPU hardware configuration."""

    type: str | None = Field(
        None, description="GPU type (e.g., 'NVIDIA A100', 'NVIDIA H100')"
    )
    count: int | None = Field(None, description="Number of GPUs required")
    cpu_fallback: bool | None = Field(
        None, description="Whether CPU fallback is allowed if GPU is unavailable"
    )


class CPUConfig(BaseModel):
    """CPU hardware configuration."""

    cores: int | None = Field(None, description="Number of CPU cores required")
    ram: str | None = Field(None, description="RAM requirement (e.g., '32GB', '64GB')")


class HardwareConfig(BaseModel):
    """Hardware requirements configuration."""

    gpu: GPUConfig | None = Field(None, description="GPU hardware requirements")
    cpu: CPUConfig | None = Field(None, description="CPU hardware requirements")


class VLLMTestingConfig(BaseModel):
    """vLLM-specific testing configuration."""

    commands: list[str] = Field(
        ..., min_length=1, description="Shell commands to run vLLM-specific tests"
    )


class ModelTestingConfig(BaseModel):
    """Model testing configuration."""

    hardware: HardwareConfig = Field(
        ..., description="Hardware requirements for testing"
    )
    commands: list[str] = Field(
        ..., min_length=1, description="Shell commands to run tests"
    )
    vllm: VLLMTestingConfig | None = Field(
        None,
        description="vLLM-specific testing configuration. Should only be defined for models that should be tested with vLLM and belong to a Nexus Package targeting the product or candidate distribution variants.",
    )


class BenchmarkExperiment(BaseModel):
    """Benchmark experiment from catalog."""

    name: str = Field(
        ..., description="Name of the benchmark experiment from the catalog"
    )
    args: str = Field(..., description="Arguments to pass to the benchmark experiment")


class CustomBenchmarkExperiment(BaseModel):
    """Custom benchmark experiment."""

    name: str = Field(..., description="Name of the custom benchmark experiment")
    python_module: str = Field(
        ..., description="Python module path for the custom benchmark"
    )
    args: str = Field(..., description="Arguments to pass to the custom benchmark")


class BenchmarkingConfig(BaseModel):
    """Model benchmarking configuration."""

    experiments: list[BenchmarkExperiment] | None = Field(
        None, description="List of benchmark experiments from the catalog"
    )
    custom_experiments: list[CustomBenchmarkExperiment] | None = Field(
        None, description="List of custom benchmark experiments"
    )


class ModelConfig(BaseModel):
    """Model-level configuration."""

    id: str = Field(..., min_length=1, description="Hugging Face model repository ID")
    owner: str | None = Field(None, description="Owner or maintainer of the model")
    vllm: VLLMConfig | None = Field(
        None,
        description="vLLM serving configuration. Only required for models that need additional vLLM plugins and belong to a Nexus Package targeting the product or candidate distribution variants.",
    )
    testing: ModelTestingConfig = Field(
        ..., description="Testing configuration for the model"
    )
    benchmarking: BenchmarkingConfig | None = Field(
        None, description="Benchmarking configuration for the model"
    )

    @model_validator(mode="after")
    def validate_vllm_testing(self) -> ModelConfig:
        """Validate that vllm testing is present when vllm is enabled."""
        if self.vllm is not None and self.vllm.enabled and self.testing.vllm is None:
            raise ValueError(
                "model.testing.vllm is required when model.vllm.enabled is true"
            )
        return self


class ModelYAML(BaseModel):
    """Root model.yaml structure."""

    model: ModelConfig = Field(..., description="Model configuration")


class NexusYAML(BaseModel):
    """Root nexus.yaml structure."""

    package: PackageConfig = Field(..., description="Package-level configuration")
    models: list[str] | None = Field(
        default_factory=list, description="List of model directory names under models/"
    )
