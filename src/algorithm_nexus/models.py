# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Pydantic models for Nexus package YAML validation."""

from __future__ import annotations

import re
import sys
from typing import Annotated, Literal

from pydantic import AfterValidator

try:
    from pydantic import BaseModel, ConfigDict, Field
except ImportError:
    print(
        "Error: CLI dependencies are not installed.\n"
        "Please install them with: pip install algorithm-nexus[cli]",
        file=sys.stderr,
    )
    sys.exit(1)


def validate_hf_model_id(v: str) -> str:
    """Validate HuggingFace model ID format and constraints.
    https://huggingface.co/docs/hub/en/security-sso-okta-scim#step-5-assign-users-or-groups

    Rules:
    - Only alphanumeric characters, dashes, dots, and underscores are accepted
    - Double dashes (--) are forbidden
    - Cannot start or end with a dash
    - Digit-only names are not accepted (must contain at least one letter)
    - Format: org-name/model-name where both follow the same rules except length
      - Maximum length is 42 for org-name and 96 for model-name, minimum length is 2 for both
    """
    # Combined regex pattern that validates the entire model ID:
    # - org-name: 2-42 chars, alphanumeric + dashes + dots + underscores, no double dashes, must have letter
    # - model-name: 2-96 chars, same rules as org-name
    # - Separated by exactly one slash
    # Split validation into org and model parts to ensure each has at least one letter
    pattern = re.compile(
        r"^"
        r"(?=(?:[a-zA-Z0-9._-]*[a-zA-Z][a-zA-Z0-9._-]*)/)"  # org must contain at least one letter
        r"(?!.*--)"  # no double dashes in org
        r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,40}[a-zA-Z0-9]"  # org-name: 2-42 chars
        r"/"  # separator
        r"(?=(?:[a-zA-Z0-9._-]*[a-zA-Z][a-zA-Z0-9._-]*)$)"  # model must contain at least one letter
        r"(?!.*--)"  # no double dashes in model
        r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,94}[a-zA-Z0-9]"  # model-name: 2-96 chars
        r"$"
    )

    if not pattern.match(v):
        msg = "Model ID must be in format 'org-name/model-name' where org-name is 2-42 characters and model-name is 2-96 characters. Both must start and end with alphanumeric, contain only alphanumeric, dashes, dots, and underscores, not have double dashes, and contain at least one letter"
        raise ValueError(msg)

    return v


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
            min_length=5,
            max_length=139,
            description="Hugging Face model repository identifier",
        ),
        AfterValidator(validate_hf_model_id),
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
