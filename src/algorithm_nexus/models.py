# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Pydantic models for Nexus package YAML validation."""

from __future__ import annotations

import re
import sys
from typing import Annotated, Literal

try:
    from pydantic import BaseModel, ConfigDict, Field, field_validator
except ImportError:
    print(
        "Error: CLI dependencies are not installed.\n"
        "Please install them with: pip install algorithm-nexus[cli]",
        file=sys.stderr,
    )
    sys.exit(1)


class NexusPackageInfo(BaseModel):
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
            min_length=1,
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


class ModelInfo(BaseModel):
    """Model-level configuration."""

    model_config = ConfigDict(extra="forbid")

    id: Annotated[
        str,
        Field(
            min_length=1,
            description="Hugging Face model repository identifier",
        ),
    ]

    owner: Annotated[
        str | None,
        Field(
            # Validates the owner field against the GitHub username rules:
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

    @field_validator("id")
    @classmethod
    def validate_model_id(cls, v: str) -> str:
        """Validate HuggingFace model ID format and constraints.
        https://huggingface.co/docs/hub/en/security-sso-okta-scim#step-5-assign-users-or-groups

        Rules:
        - Only alphanumeric characters and dashes are accepted
        - Double dashes (--) are forbidden
        - Cannot start or end with a dash
        - Digit-only names are not accepted (must contain at least one letter)
        - Minimum length is 2 and maximum length is 42 per segment
        - Format: username/model-name where both follow the same rules
        """
        if "/" not in v:
            msg = "Model ID must be in format 'username/model-name'"
            raise ValueError(msg)

        parts = v.split("/")
        if len(parts) != 2:
            msg = "Model ID must contain exactly one slash"
            raise ValueError(msg)

        username, model_name = parts

        # Regex pattern for each segment:
        # - Length: 2-42 characters (first char + 0-40 middle + last char)
        # - Must start and end with alphanumeric
        # - Can contain alphanumeric and dashes in the middle
        # - No double dashes (negative lookahead (?!.*--))
        # - Must contain at least one letter (positive lookahead (?=.*[a-zA-Z]))
        segment_pattern = re.compile(
            r"^(?!.*--)(?=.*[a-zA-Z])[a-zA-Z0-9][a-zA-Z0-9-]{0,40}[a-zA-Z0-9]$"
        )

        # Validate each segment
        for part, name in [(username, "username"), (model_name, "model name")]:
            # Check all constraints via regex
            if not segment_pattern.match(part):
                msg = f"{name} must be 2-42 characters, start and end with alphanumeric, contain only alphanumeric and dashes, not have double dashes, and contain at least one letter"
                raise ValueError(msg)

        return v


class AlgorithmNexusModelConfig(BaseModel):
    """Root model.yaml structure."""

    model_config = ConfigDict(extra="forbid")

    model: Annotated[ModelInfo, Field(description="Model configuration")]


class AlgorithmNexusPackageConfig(BaseModel):
    """Root nexus.yaml structure."""

    model_config = ConfigDict(extra="forbid")

    package: Annotated[
        NexusPackageInfo, Field(description="Package-level configuration")
    ]
