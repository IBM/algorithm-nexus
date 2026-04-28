# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Pydantic models for Nexus package YAML validation."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field


class PackageConfig(BaseModel):
    """Package-level configuration."""

    model_config = {"extra": "forbid"}

    name: Annotated[str, Field(min_length=1, description="Python package name")]


class VLLMPlugins(BaseModel):
    """vLLM plugins configuration."""

    model_config = {"extra": "forbid"}

    general: Annotated[
        str | None,
        Field(None, description="General vLLM plugin that loads the model class"),
    ] = None
    io_processors: Annotated[
        list[str] | None,
        Field(
            None,
            description="List of vLLM IO processor plugins supported by this model",
        ),
    ] = None


class VLLMConfig(BaseModel):
    """vLLM serving configuration.

    Should only be defined for models that require additional vLLM plugins
    and belong to a Nexus Package targeting the product or candidate distribution variants.
    """

    model_config = {"extra": "forbid"}

    enabled: Annotated[
        Literal[True],
        Field(description="Whether vLLM serving is enabled for this model"),
    ]
    plugins: Annotated[
        VLLMPlugins | None,
        Field(None, description="vLLM plugins configuration"),
    ] = None


class ModelConfig(BaseModel):
    """Model-level configuration."""

    model_config = {"extra": "forbid"}

    id: Annotated[
        str,
        Field(min_length=1, description="Hugging Face model repository identifier"),
    ]
    owner: Annotated[
        str | None,
        Field(
            None,
            description="Model owner GitHub identifier. If omitted, ownership defaults to the Nexus package owner.",
        ),
    ] = None
    vllm: Annotated[
        VLLMConfig | None,
        Field(
            None,
            description="vLLM serving configuration. Only required for models that need additional vLLM plugins and belong to a Nexus Package targeting the product or candidate distribution variants.",
        ),
    ] = None


class ModelYAML(BaseModel):
    """Root model.yaml structure."""

    model_config = {"extra": "forbid"}

    model: Annotated[ModelConfig, Field(description="Model configuration")]


class NexusYAML(BaseModel):
    """Root nexus.yaml structure."""

    model_config = {"extra": "forbid"}

    package: Annotated[PackageConfig, Field(description="Package-level configuration")]
