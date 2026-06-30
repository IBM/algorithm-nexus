# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Pydantic models for Nexus package YAML validation."""

from __future__ import annotations

import re
import sys
from typing import Annotated, Literal

from pydantic import AfterValidator, computed_field

try:
    from orchestrator.schema.property import Property
    from orchestrator.schema.reference import ExperimentReference
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


class BenchmarkPackage(BaseModel):
    """Benchmark package registration in nexus.yaml.

    Registers a benchmark package and the experiments it exposes.
    Each package must follow the ADO custom experiment format.
    """

    model_config = ConfigDict(extra="forbid")

    requirement_specifier: Annotated[
        str,
        Field(
            min_length=1,
            description="Python package requirement target for the benchmark package. May be a Python package name, a URL to a Python package or source repository, or a local path to a Python package within ./packages in the Nexus repository root.",
        ),
    ]
    experiments: Annotated[
        list[str],
        Field(
            min_length=1,
            description="Experiment identifiers exposed by that benchmark package and made available to models in the Nexus package.",
        ),
    ]


class NexusPackageInfo(BaseModel):
    """Package-level configuration."""

    model_config = ConfigDict(extra="forbid")

    name: Annotated[str, Field(min_length=1, description="Python package name")]
    benchmark_packages: Annotated[
        list[BenchmarkPackage] | None,
        Field(
            description="List of benchmark packages available to models in this package",
        ),
    ] = None


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


class ValidationResult(BaseModel):
    """Result of validating a benchmark instance."""

    success: Annotated[bool, Field(description="Whether validation succeeded")]
    instance_path: Annotated[str, Field(description="Path to the benchmark instance")]
    errors: Annotated[list[str], Field(description="List of validation errors")]
    warnings: Annotated[list[str], Field(description="List of validation warnings")]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def status(self) -> str:
        """Computed status based on success field."""
        return "success" if self.success else "failed"


class BenchmarkExecutionResult(BaseModel):
    """Result of executing a benchmark instance."""

    instance_path: Annotated[str, Field(description="Path to the benchmark instance")]
    status: Annotated[
        Literal["success", "failed", "started", "unknown"],
        Field(description="Execution status"),
    ] = "unknown"
    message: Annotated[
        str, Field(description="Status message or error description")
    ] = ""
    space_id: Annotated[str | None, Field(description="Created discovery space ID")] = (
        None
    )
    operation_id: Annotated[str | None, Field(description="Created operation ID")] = (
        None
    )
    ray_job_id: Annotated[
        str | None, Field(description="Ray job ID for remote execution")
    ] = None


class ValidationReport(BaseModel):
    """Aggregated result of validating all benchmark instances."""

    instances: Annotated[
        list[dict], Field(description="Per-instance validation result dicts")
    ]
    successful: Annotated[int, Field(description="Number of instances that passed")]
    failed: Annotated[int, Field(description="Number of instances that failed")]
    total: Annotated[
        int,
        Field(
            description="Total number of instances discovered (may exceed successful + failed under --fail-fast)"
        ),
    ]


# ---------------------------------------------------------------------------
# Logical Benchmark models
# ---------------------------------------------------------------------------


class FieldMapping(BaseModel):
    """1-to-1 mapping of a benchmark property to an experiment property."""

    model_config = ConfigDict(extra="forbid")

    benchmark: Annotated[
        Property,
        Field(description="Canonical benchmark property (propertyIdentifier)."),
    ]
    experiment: Annotated[
        Property, Field(description="Experiment property (propertyIdentifier).")
    ]


class CategoricalValueRef(BaseModel):
    """A reference to a specific value of a categorical benchmark property."""

    model_config = ConfigDict(extra="forbid")

    property: Annotated[
        Property,
        Field(description="The categorical benchmark property (propertyIdentifier)."),
    ]
    value: Annotated[
        str,
        Field(
            min_length=1, description="The categorical value from the benchmark domain."
        ),
    ]


class CategoricalValueMapping(BaseModel):
    """Maps a categorical benchmark property value to a set of experiment property predicates."""

    model_config = ConfigDict(extra="forbid")

    categoricalValue: Annotated[
        CategoricalValueRef,
        Field(description="The benchmark categorical value being mapped."),
    ]
    predicate: Annotated[
        list[Property],
        Field(
            min_length=1,
            description="Experiment property constraints that identify this categorical value.",
        ),
    ]


class StaticFilter(BaseModel):
    """Pins an experiment property to a fixed value implicit in the logical benchmark."""

    model_config = ConfigDict(extra="forbid")

    property: Annotated[
        Property,
        Field(description="The experiment property to filter on."),
    ]
    value: Annotated[
        str,
        Field(
            min_length=1, description="The fixed value for this experiment property."
        ),
    ]


class MetricMapping(BaseModel):
    """Maps a canonical benchmark metric name to an experiment metric name."""

    model_config = ConfigDict(extra="forbid")

    benchmark: Annotated[
        Property,
        Field(description="Canonical benchmark metric identifier."),
    ]

    experiment: Annotated[Property, Field(description="Experiment metric identifier.")]


class LogicalBenchmarkDefinition(BaseModel):
    """Logical benchmark definition — the abstract problem description."""

    model_config = ConfigDict(extra="forbid")

    benchmarkIdentifier: Annotated[
        str,
        Field(
            min_length=1, description="Canonical identifier for this logical benchmark."
        ),
    ]
    description: Annotated[
        str,
        Field(
            min_length=1,
            description="Human-readable description of the abstract problem being evaluated.",
        ),
    ]
    target: Annotated[
        Property,
        Field(
            description="The property that identifies the quantity being benchmarked."
        ),
    ]
    properties: Annotated[
        list[Property],
        Field(
            min_length=1,
            description="The properties on which this benchmark is evaluated.",
        ),
    ]
    metrics: Annotated[
        list[str] | None,
        Field(description="Canonical metric names for this benchmark."),
    ] = None
    owner: Annotated[
        str | None,
        Field(
            description="Team or individual responsible for maintaining this definition."
        ),
    ] = None


class BenchmarkBinding(BaseModel):
    """Binding that maps an experiment's properties and metrics to a logical benchmark."""

    model_config = ConfigDict(extra="forbid")

    benchmarkIdentifier: Annotated[
        str,
        Field(
            min_length=1,
            description="The id of the logical benchmark this experiment targets.",
        ),
    ]
    experiment: Annotated[
        ExperimentReference,
        Field(description="The ado ExperimentReference object."),
    ]
    targetMapping: Annotated[
        str,
        Field(
            min_length=1,
            description="The experiment property name that carries the benchmark target.",
        ),
    ]
    staticFilters: Annotated[
        list[StaticFilter] | None,
        Field(
            description="Static experiment property filters implicit in this logical benchmark."
        ),
    ] = None
    propertyMapping: Annotated[
        list[FieldMapping | CategoricalValueMapping] | None,
        Field(
            description="Maps experiment internal properties to canonical benchmark properties."
        ),
    ] = None
    metricMapping: Annotated[
        list[MetricMapping] | None,
        Field(
            description="Translates per-experiment metric names to canonical benchmark metric names."
        ),
    ] = None


class LogicalBenchmarkConfig(BaseModel):
    """Root model for a logical benchmark YAML file (logicalBenchmark + optional bindings)."""

    model_config = ConfigDict(extra="forbid")

    logicalBenchmark: Annotated[
        LogicalBenchmarkDefinition,
        Field(description="The logical benchmark definition."),
    ]
    bindings: Annotated[
        list[BenchmarkBinding] | None,
        Field(description="Benchmark bindings declared in this file."),
    ] = None
