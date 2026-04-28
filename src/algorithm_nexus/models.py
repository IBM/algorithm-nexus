# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Pydantic models for Nexus package YAML validation."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class PackageConfig(BaseModel):
    """Package-level configuration."""

    model_config = {"extra": "forbid"}

    name: str = Field(..., min_length=1, description="Python package name")


class VLLMPlugins(BaseModel):
    """vLLM plugins configuration."""

    model_config = {"extra": "forbid"}

    general: str | None = Field(
        None, description="General vLLM plugin that loads the model class"
    )
    io_processors: list[str] | None = Field(
        None, description="List of vLLM IO processor plugins supported by this model"
    )


class VLLMConfig(BaseModel):
    """vLLM serving configuration.

    Should only be defined for models that require additional vLLM plugins
    and belong to a Nexus Package targeting the product or candidate distribution variants.
    """

    model_config = {"extra": "forbid"}

    enabled: Literal[True] = Field(
        ..., description="Whether vLLM serving is enabled for this model"
    )
    plugins: VLLMPlugins | None = Field(None, description="vLLM plugins configuration")


class ModelConfig(BaseModel):
    """Model-level configuration."""

    model_config = {"extra": "forbid"}

    id: str = Field(
        ..., min_length=1, description="Hugging Face model repository identifier"
    )
    owner: str | None = Field(
        None,
        description="Model owner GitHub identifier. If omitted, ownership defaults to the Nexus package owner.",
    )
    vllm: VLLMConfig | None = Field(
        None,
        description="vLLM serving configuration. Only required for models that need additional vLLM plugins and belong to a Nexus Package targeting the product or candidate distribution variants.",
    )


class ModelYAML(BaseModel):
    """Root model.yaml structure."""

    model_config = {"extra": "forbid"}

    model: ModelConfig = Field(..., description="Model configuration")


class NexusYAML(BaseModel):
    """Root nexus.yaml structure."""

    model_config = {"extra": "forbid"}

    package: PackageConfig = Field(..., description="Package-level configuration")
