# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

"""Pydantic models for Nexus package YAML validation."""

from __future__ import annotations

import re
import sys
from typing import Annotated, Literal

from pydantic import AfterValidator, computed_field, model_validator

try:
    from ado.schema.property import Property
    from ado.schema.property_value import PropertyValue
    from ado.schema.reference import ExperimentReference
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


def validate_remote_requirement_specifier(v: str) -> str:
    """Validate that a requirement specifier points to GitHub or PyPI, not a local path.

    Local paths (starting with '.', '/', or '~') are not allowed. The specifier
    must be either a PyPI package name (optionally with a version constraint) or
    a GitHub repository URL.
    """
    stripped = v.strip()
    if not stripped:
        msg = "requirement_specifier must not be empty"
        raise ValueError(msg)
    if stripped.startswith((".", "/", "~")):
        msg = (
            "requirement_specifier must be a PyPI package name or a GitHub URL. "
            "Local paths are not allowed."
        )
        raise ValueError(msg)
    return v


class ExperimentSpecifier(BaseModel):
    """Experiment specifier in an experiment_package.yaml file.

    Registers the package that provides experiments and lists the experiment
    identifiers it exposes. The package must be available on PyPI or GitHub;
    local paths are not permitted.
    """

    model_config = ConfigDict(extra="forbid")

    requirement_specifier: Annotated[
        str,
        AfterValidator(validate_remote_requirement_specifier),
        Field(
            min_length=1,
            description=(
                "Python package requirement specifier for the experiment package. "
                "Must be a PyPI package name (optionally with a version constraint) "
                "or a GitHub repository URL. Local paths are not allowed."
            ),
        ),
    ]
    experiments: Annotated[
        list[str],
        Field(
            min_length=1,
            description="Experiment identifiers exposed by the package.",
        ),
    ]


class ExperimentConfig(BaseModel):
    """Top-level schema for experiment_package.yaml files inside experiments/<name>/."""

    model_config = ConfigDict(extra="forbid")

    experiment_package: Annotated[
        ExperimentSpecifier,
        Field(description="Experiment package specifier and experiment list."),
    ]


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
    """Result of validating a benchmark submission."""

    success: Annotated[bool, Field(description="Whether validation succeeded")]
    submission_path: Annotated[
        str, Field(description="Path to the benchmark submission")
    ]
    errors: Annotated[list[str], Field(description="List of validation errors")]
    warnings: Annotated[list[str], Field(description="List of validation warnings")]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def status(self) -> str:
        """Computed status based on success field."""
        return "success" if self.success else "failed"


class BenchmarkExecutionResult(BaseModel):
    """Result of executing a benchmark submission."""

    submission_path: Annotated[
        str, Field(description="Path to the benchmark submission")
    ]
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


class BenchmarkInstanceProperty(Property):
    """A benchmark instance property definition, with optional artifact indicator."""

    is_artifact: Annotated[
        bool,
        Field(
            default=False,
            description="Whether this instance property is provided via artifact files rather than scalar values.",
        ),
    ] = False


class FieldMapping(BaseModel):
    """1-to-1 mapping of a benchmark property to an experiment property."""

    model_config = ConfigDict(extra="forbid")

    benchmark: Annotated[
        Property,
        Field(description="Canonical benchmark property."),
    ]
    experiment: Annotated[Property, Field(description="Experiment property.")]


class CategoricalValueMapping(BaseModel):
    """Maps a categorical benchmark property value to a set of experiment property predicates."""

    model_config = ConfigDict(extra="forbid")

    categoricalValue: Annotated[
        PropertyValue,
        Field(description="The benchmark categorical value being mapped."),
    ]
    predicate: Annotated[
        list[Property],
        Field(
            min_length=1,
            description="Experiment property constraints that identify this categorical value.",
        ),
    ]


class MetricIdentifier(BaseModel):
    """A reference to a canonical benchmark metric by its identifier string."""

    model_config = ConfigDict(extra="forbid")

    identifier: Annotated[
        str,
        Field(min_length=1, description="Metric identifier."),
    ]


class MetricMapping(BaseModel):
    """Maps a canonical benchmark metric name to an experiment metric name."""

    model_config = ConfigDict(extra="forbid")

    benchmark: Annotated[
        MetricIdentifier,
        Field(description="Canonical benchmark metric identifier."),
    ]

    experiment: Annotated[
        MetricIdentifier,
        Field(description="Experiment metric identifier."),
    ]


class BenchmarkRanking(BaseModel):
    """Defines how benchmark results are ranked."""

    model_config = ConfigDict(extra="forbid")

    metric: Annotated[
        str,
        Field(min_length=1, description="Identifier of the metric used for ranking."),
    ]
    order: Annotated[
        Literal["asc", "desc"],
        Field(
            description="Sort order: 'asc' for lower-is-better, 'desc' for higher-is-better."
        ),
    ]


class StaticFilters(BaseModel):
    """Static property filters for a benchmark binding.

    Two directions are supported:

    * ``experimentFilters`` — experiment properties whose values are implicit in
      the logical benchmark.  When querying this experiment's results the system
      adds ``WHERE <experiment-property> = <value>`` automatically.
    * ``benchmarkFilters`` — benchmark instance properties whose values are
      implicit in the experiment.  When building a leaderboard row the system
      injects ``<benchmark-property> = <value>`` without reading it from the
      experiment results.
    """

    model_config = ConfigDict(extra="forbid")

    experimentFilters: Annotated[
        list[PropertyValue] | None,
        Field(
            description=(
                "Experiment property values that are implicit in the logical benchmark. "
                "Each entry is added as a constant filter when querying the experiment."
            ),
        ),
    ] = None
    benchmarkFilters: Annotated[
        list[PropertyValue] | None,
        Field(
            description=(
                "Benchmark instance property values that are implicit in the experiment. "
                "Each entry is injected as a known constant into the leaderboard row "
                "without reading it from the experiment results."
            ),
        ),
    ] = None


class BenchmarkBinding(BaseModel):
    """Binding that maps an experiment's properties and metrics to a logical benchmark."""

    model_config = ConfigDict(extra="forbid")

    benchmarkIdentifier: Annotated[
        str,
        Field(
            min_length=1,
            description="Identifier of the logical benchmark this binding targets.",
        ),
    ]
    experiment: Annotated[
        ExperimentReference,
        Field(description="The ado ExperimentReference object."),
    ]
    targetMapping: Annotated[
        str | None,
        Field(
            min_length=1,
            description=(
                "Identifies the leaderboard target (row key) for this binding. "
                "Can be a custom label string, the name of an experiment property "
                "whose value will be resolved at query time, or omitted to default "
                "to the experiment identifier."
            ),
        ),
    ] = None
    metricMapping: Annotated[
        list[MetricMapping] | None,
        Field(
            description="Translates per-experiment metric names to canonical benchmark metric names."
        ),
    ] = None
    instanceMapping: Annotated[
        list[FieldMapping | CategoricalValueMapping] | None,
        Field(
            description="Remaps benchmark instance properties/parameters to experiment inputs.",
        ),
    ] = None
    staticFilters: Annotated[
        StaticFilters | None,
        Field(
            description=(
                "Static property filters for this binding. "
                "``experimentFilters`` pins experiment properties to values implicit in the benchmark; "
                "``benchmarkFilters`` pins benchmark properties to values implicit in the experiment."
            ),
        ),
    ] = None

    @model_validator(mode="after")
    def default_target_mapping(self) -> BenchmarkBinding:
        """Default targetMapping to the experiment identifier when omitted."""
        if self.targetMapping is None:
            self.targetMapping = self.experiment.experimentIdentifier
        return self


class BenchmarkInstance(BaseModel):
    """Benchmark instance configuration."""

    model_config = ConfigDict(extra="allow")

    identifier: Annotated[
        str,
        Field(min_length=1, description="Identifier for this benchmark instance."),
    ]
    description: Annotated[
        str | None,
        Field(description="Description of this specific instance."),
    ] = None


class LogicalBenchmarkDefinition(BaseModel):
    """Logical benchmark definition — the abstract problem description."""

    model_config = ConfigDict(extra="forbid")

    benchmarkIdentifier: Annotated[
        str,
        Field(
            min_length=1, description="Canonical identifier for this logical benchmark."
        ),
    ]
    title: Annotated[
        str | None,
        Field(
            min_length=1,
            description="Short human-readable display name for this benchmark.",
        ),
    ] = None
    description: Annotated[
        str,
        Field(
            min_length=1,
            description="Human-readable description of the abstract problem being evaluated.",
        ),
    ]
    instance: Annotated[
        list[BenchmarkInstanceProperty],
        Field(
            min_length=1,
            description="Properties defining a benchmark instance for this benchmark.",
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
    ranking: Annotated[
        BenchmarkRanking | None,
        Field(description="Optional ranking configuration for this benchmark."),
    ] = None


class LogicalBenchmarkConfig(BaseModel):
    """Root model for a logical benchmark YAML file (benchmark.yaml).

    Contains only the logical benchmark definition. Bindings live in
    experiments/<name>/bindings/*.yaml, not in benchmark.yaml.
    """

    model_config = ConfigDict(extra="forbid")

    logicalBenchmark: Annotated[
        LogicalBenchmarkDefinition,
        Field(description="The logical benchmark definition."),
    ]
