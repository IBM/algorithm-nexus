# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Pydantic models for Nexus package YAML validation."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class PackageConfig(BaseModel):
    """Package-level configuration."""

    model_config = ConfigDict(extra="forbid")

    name: Annotated[str, Field(min_length=1, description="Python package name")]


class VLLMPlugins(BaseModel):
    """vLLM plugins configuration."""

    model_config = ConfigDict(extra="forbid")

    general: Annotated[
        str | None,
        Field(description="General vLLM plugin that loads the model class"),
    ] = None
    io_processors: Annotated[
        list[str] | None,
        Field(
            description="List of vLLM IO processor plugins supported by this model",
        ),
    ] = None


class VLLMConfig(BaseModel):
    """vLLM serving configuration.

    Should only be defined for models that require additional vLLM plugins
    and belong to a Nexus Package targeting the product or candidate distribution variants.
    """

    model_config = ConfigDict(extra="forbid")

    enabled: Annotated[
        Literal[True],
        Field(description="Whether vLLM serving is enabled for this model"),
    ]
    plugins: Annotated[
        VLLMPlugins | None,
        Field(description="vLLM plugins configuration"),
    ] = None


class ModelConfig(BaseModel):
    """Model-level configuration."""

    model_config = ConfigDict(extra="forbid")

    id: Annotated[
        str,
        Field(min_length=1, description="Hugging Face model repository identifier"),
    ]
    owner: Annotated[
        str | None,
        Field(
            # Validats the owner field against the GitHub username rules:
            # https://docs.github.com/en/enterprise-cloud@latest/admin/managing-iam/iam-configuration-reference/username-considerations-for-external-authentication
            # - Only contains dashes and alphanumeric characters
            # - Does not start or end with a dash
            # - Does not contain consecutive dashes
            # - Has a maximum length of 39 characters
            pattern=r"^[a-zA-Z0-9]([a-zA-Z0-9]|-[a-zA-Z0-9]){0,38}$",
            description="Model owner GitHub identifier. If omitted, ownership defaults to the Nexus package owner.",
        ),
    ] = None

    vllm: Annotated[
        VLLMConfig | None,
        Field(
            description="vLLM serving configuration. Only required for models that need additional vLLM plugins and belong to a Nexus Package targeting the product or candidate distribution variants.",
        ),
    ] = None


class ModelYAML(BaseModel):
    """Root model.yaml structure."""

    model_config = ConfigDict(extra="forbid")

    model: Annotated[ModelConfig, Field(description="Model configuration")]


class NexusYAML(BaseModel):
    """Root nexus.yaml structure."""

    model_config = ConfigDict(extra="forbid")

    package: Annotated[PackageConfig, Field(description="Package-level configuration")]
