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


MetadataKey = Annotated[
    str, Field(max_length=4096, description="Metadata dictionary key.")
]
MetadataValue = Annotated[
    str, Field(max_length=4096, description="Metadata dictionary value.")
]
MetadataDict = dict[MetadataKey, MetadataValue]


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
    metadata: Annotated[
        MetadataDict | None,
        Field(
            description="Arbitrary key-value annotations as a flat string-to-string dictionary."
        ),
    ] = None


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


class FieldMapping(BaseModel):
    """1-to-1 mapping of a benchmark instance problem property to an experiment property."""

    model_config = ConfigDict(extra="forbid")

    instance: Annotated[
        Property,
        Field(description="Benchmark instance problem property."),
    ]
    experiment: Annotated[Property, Field(description="Experiment input property.")]


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


class StaticTargetMapping(BaseModel):
    """Static string label for the leaderboard target."""

    model_config = ConfigDict(extra="forbid")

    static: Annotated[
        str,
        Field(
            min_length=1,
            description="Fixed label applied to every run of this binding.",
        ),
    ]


class ExperimentPropertyTargetMapping(BaseModel):
    """Resolves the leaderboard target from an experiment input property at query time."""

    model_config = ConfigDict(extra="forbid")

    experimentProperty: Annotated[
        str,
        Field(
            min_length=1,
            description=(
                "Identifier of the experiment input property whose value is used as "
                "the leaderboard target."
            ),
        ),
    ]


class InstanceArtifactMapping(BaseModel):
    """Maps a benchmark instance artifact property to an experiment input property."""

    model_config = ConfigDict(extra="forbid")

    instance: Annotated[
        Property,
        Field(description="The instance artifact property being mapped."),
    ]
    experiment: Annotated[
        Property,
        Field(description="The experiment input property receiving the artifact path."),
    ]
    validValues: Annotated[
        list[str],
        Field(
            min_length=1,
            description="List of valid file names for this artifact in the instance folder.",
        ),
    ]


class InstanceArtifact(BaseModel):
    """An artifact entry within a benchmark instance definition."""

    model_config = ConfigDict(extra="forbid")

    property: Annotated[
        Property,
        Field(description="Identifies this artifact slot within the instance."),
    ]
    artifactsLocation: Annotated[
        str,
        Field(
            min_length=1,
            description="Subfolder (relative to the instance folder) holding the artifact files.",
        ),
    ]


class BenchmarkInstance(BaseModel):
    """Benchmark instance configuration (instance.yaml)."""

    model_config = ConfigDict(extra="forbid")

    instanceIdentifier: Annotated[
        str,
        Field(
            min_length=1, description="Unique identifier for this benchmark instance."
        ),
    ]
    benchmarkIdentifier: Annotated[
        str,
        Field(
            min_length=1,
            description="The benchmarkIdentifier of the benchmark this instance maps to.",
        ),
    ]
    description: Annotated[
        str | None,
        Field(description="Human-readable description of this specific instance."),
    ] = None
    problemPropertyValues: Annotated[
        list[PropertyValue] | None,
        Field(
            description="Values for all problem properties defined in benchmark.yaml."
        ),
    ] = None
    instanceArtifacts: Annotated[
        list[InstanceArtifact] | None,
        Field(description="All artifacts available for this instance."),
    ] = None
    metadata: Annotated[
        MetadataDict | None,
        Field(
            description="Arbitrary key-value annotations as a flat string-to-string dictionary."
        ),
    ] = None


class InstanceBinding(BaseModel):
    """Binding that maps an experiment's properties and metrics to a benchmark instance."""

    model_config = ConfigDict(extra="forbid")

    instanceBindingIdentifier: Annotated[
        str,
        Field(
            min_length=1,
            description="Unique identifier for this instance binding.",
        ),
    ]
    instanceReference: Annotated[
        str,
        Field(
            min_length=1,
            description=(
                "Reference to the benchmark instance in the form "
                "'benchmarkIdentifier/instanceIdentifier'."
            ),
            pattern=r"^[^/]+/[^/]+$",
        ),
    ]
    experiment: Annotated[
        ExperimentReference,
        Field(description="The ado ExperimentReference object."),
    ]
    targetMapping: Annotated[
        StaticTargetMapping | ExperimentPropertyTargetMapping | None,
        Field(
            description=(
                "Identifies the leaderboard target (row key) for this binding. "
                "Use 'static' for a fixed label or 'experimentProperty' to resolve "
                "the target from an experiment input at query time. "
                "Defaults to the experiment identifier when omitted."
            ),
        ),
    ] = None
    metricMapping: Annotated[
        list[MetricMapping] | None,
        Field(
            description="Translates per-experiment metric names to canonical benchmark metric names."
        ),
    ] = None
    problemPropertyMapping: Annotated[
        list[FieldMapping | CategoricalValueMapping] | None,
        Field(
            description=(
                "Remaps benchmark instance problem properties to experiment input properties."
            ),
        ),
    ] = None
    instanceArtifactMapping: Annotated[
        list[InstanceArtifactMapping] | None,
        Field(
            description=(
                "Maps benchmark instance artifact properties to experiment input properties."
            ),
        ),
    ] = None
    staticFilters: Annotated[
        list[PropertyValue] | None,
        Field(
            description=(
                "Pins experiment property values that are implicit in the instance. "
                "Each entry adds a constant WHERE clause when querying the experiment."
            ),
        ),
    ] = None
    metadata: Annotated[
        MetadataDict | None,
        Field(
            description="Arbitrary key-value annotations as a flat string-to-string dictionary."
        ),
    ] = None

    @model_validator(mode="after")
    def default_target_mapping(self) -> InstanceBinding:
        """Default targetMapping to a static experiment identifier when omitted."""
        if self.targetMapping is None:
            self.targetMapping = StaticTargetMapping(
                static=self.experiment.experimentIdentifier
            )
        return self


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
    problemProperties: Annotated[
        list[Property],
        Field(
            min_length=1,
            description="The properties defining a benchmark problem instance.",
        ),
    ]
    metrics: Annotated[
        list[Property] | None,
        Field(description="Canonical metric names for this logical benchmark."),
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
    metadata: Annotated[
        MetadataDict | None,
        Field(
            description="Arbitrary key-value annotations as a flat string-to-string dictionary."
        ),
    ] = None


class BindingFileConfig(BaseModel):
    """Root model for a binding YAML file (experiments/<name>/bindings/*.yaml).

    Each file contains exactly one instance binding at the top level.
    """

    model_config = ConfigDict(extra="forbid")

    instanceBindingIdentifier: Annotated[
        str,
        Field(min_length=1, description="Unique identifier for this instance binding."),
    ]
    instanceReference: Annotated[
        str,
        Field(
            min_length=1,
            description="Reference in the form 'benchmarkIdentifier/instanceIdentifier'.",
            pattern=r"^[^/]+/[^/]+$",
        ),
    ]
    experiment: Annotated[
        ExperimentReference,
        Field(description="The ado ExperimentReference object."),
    ]
    targetMapping: Annotated[
        StaticTargetMapping | ExperimentPropertyTargetMapping | None,
        Field(description="Leaderboard target mapping."),
    ] = None
    metricMapping: Annotated[
        list[MetricMapping] | None,
        Field(description="Metric name translations."),
    ] = None
    problemPropertyMapping: Annotated[
        list[FieldMapping | CategoricalValueMapping] | None,
        Field(description="Problem property remappings."),
    ] = None
    instanceArtifactMapping: Annotated[
        list[InstanceArtifactMapping] | None,
        Field(description="Instance artifact remappings."),
    ] = None
    staticFilters: Annotated[
        list[PropertyValue] | None,
        Field(description="Static experiment property filters."),
    ] = None
    metadata: Annotated[
        MetadataDict | None,
        Field(
            description="Arbitrary key-value annotations as a flat string-to-string dictionary."
        ),
    ] = None
