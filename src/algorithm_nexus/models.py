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
    from ado.utilities.pydantic import StrictSemVerStr
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


# PEP 508 package name, optional extras and optional version specifiers, e.g.
# "pkg", "pkg[ado]", "pkg>=1.0,<2", "pkg[a,b] == 1.2.3". Direct references
# ("pkg @ url"), environment markers and anything path-like are rejected.
_PYPI_REQUIREMENT_PATTERN = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?"  # name
    r"(?:\[\s*[A-Za-z0-9][A-Za-z0-9._-]*(?:\s*,\s*[A-Za-z0-9][A-Za-z0-9._-]*)*\s*\])?"  # extras
    r"(?:\s*(?:~=|===|==|!=|<=|>=|<|>)\s*[A-Za-z0-9.*+!_-]+"  # first specifier
    r"(?:\s*,\s*(?:~=|===|==|!=|<=|>=|<|>)\s*[A-Za-z0-9.*+!_-]+)*)?$"  # further specifiers
)

# Git hosts that experiment packages may be installed from. Hosts are matched
# exactly (case-insensitive): subdomains, ports and user info are not allowed.
ALLOWED_GIT_HOSTS: tuple[str, ...] = (
    "github.com",
    "github.ibm.com",
    "research.github.ibm.com",
)

# Remote git URLs on an allowed host, over HTTPS or SSH:
#   https://<host>/<path>          git+https://<host>/<path>
#   ssh://git@<host>/<path>        git+ssh://git@<host>/<path>
#   git@<host>:<path>              git@<host>/<path>
# The host must be immediately followed by "/" (or ":" in the scp-like form), so
# look-alikes such as "github.com.evil.com" or "github.com@evil.com" are rejected.
# HTTPS URLs must not carry credentials, and the SSH user must be "git". Plain
# http://, file:// and whitespace anywhere in the URL are not accepted.
_HOST = "(?i:" + "|".join(re.escape(h) for h in ALLOWED_GIT_HOSTS) + ")"
_PATH = r"[A-Za-z0-9][A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]*"
_REMOTE_URL_PATTERN = re.compile(
    rf"^(?:(?:git\+)?https://{_HOST}/{_PATH}"
    rf"|(?:git\+)?ssh://git@{_HOST}/{_PATH}"
    rf"|git@{_HOST}[:/]{_PATH})$"
)


def validate_remote_requirement_specifier(v: str) -> str:
    """Validate that a requirement specifier points to PyPI or an allowed git host.

    The specifier must match a strict allowlist:

    - a PyPI package name, optionally with extras and version specifiers
      (e.g. ``pkg``, ``pkg[ado]>=1.0,<2``)
    - a git URL on one of ``ALLOWED_GIT_HOSTS`` over HTTPS (``https://``,
      ``git+https://``) or SSH (``ssh://git@``, ``git+ssh://git@``, or the
      scp-like ``git@host:org/repo``)

    Anything else is rejected, including other git hosts, local paths in any
    form (``./pkg``, ``/abs/pkg``, ``~/pkg``, ``sub/dir``, ``../pkg``),
    ``file://`` URLs, ``pkg @ url`` direct references, plain ``http://`` URLs,
    credentials or ports in URLs, and values starting with ``-`` that would be
    interpreted as installer options. These values end up as arguments to
    ``uv pip install``, which executes the build backend of the referenced
    project, so local paths must never be accepted.
    """
    stripped = v.strip()
    if not stripped:
        msg = "requirement_specifier must not be empty"
        raise ValueError(msg)
    if _PYPI_REQUIREMENT_PATTERN.match(stripped) or _REMOTE_URL_PATTERN.match(stripped):
        return stripped
    msg = (
        f"Invalid requirement_specifier {stripped!r}: must be a PyPI package name "
        "(optionally with extras and version specifiers) or a git URL over HTTPS "
        "or SSH on one of: " + ", ".join(ALLOWED_GIT_HOSTS) + ". "
        "Local paths, other hosts, file:// URLs, direct references, credentials "
        "in URLs and installer options are not allowed."
    )
    raise ValueError(msg)


class ExperimentEntry(BaseModel):
    """An experiment exposed by an experiment package, with an optional version."""

    model_config = ConfigDict(extra="forbid")

    experimentIdentifier: Annotated[
        str,
        Field(min_length=1, description="Experiment identifier."),
    ]
    experimentVersion: Annotated[
        StrictSemVerStr | None,
        Field(
            description=(
                "Version of the experiment provided by this package "
                "(strict SemVer MAJOR.MINOR.PATCH)."
            ),
        ),
    ] = None

    @model_validator(mode="after")
    def _identifier_has_no_version_suffix(self) -> ExperimentEntry:
        if "@" in self.experimentIdentifier:
            msg = (
                "experimentIdentifier must not contain '@'. "
                "Use experimentVersion to supply version information."
            )
            raise ValueError(msg)
        return self


class ExperimentSpecifier(BaseModel):
    """Experiment specifier in an experiment_package.yaml file.

    Registers the package that provides experiments and lists the experiment
    identifiers it exposes. The package must be available on PyPI or GitHub;
    local paths are not permitted.

    Each experiment is a mapping with an ``experimentIdentifier`` and an optional
    ``experimentVersion``.
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
        list[ExperimentEntry],
        Field(
            min_length=1,
            description=(
                "Experiments exposed by the package, as "
                "{experimentIdentifier, experimentVersion} mappings."
            ),
        ),
    ]

    @property
    def experiment_entries(self) -> list[ExperimentEntry]:
        """The experiments of this package."""
        return self.experiments

    @property
    def experiment_ids(self) -> list[str]:
        """Identifiers of the experiments exposed by this package."""
        return [e.experimentIdentifier for e in self.experiments]


class ExperimentConfig(BaseModel):
    """Top-level schema for experiment_package.yaml files inside experiments/<name>/.

    ``experiment_package`` is a list of packages (e.g. to pin different package
    revisions providing different experiment versions).
    """

    model_config = ConfigDict(extra="forbid")

    experiment_package: Annotated[
        list[ExperimentSpecifier],
        Field(
            min_length=1,
            description="Experiment package specifiers, with their experiments.",
        ),
    ]
    metadata: Annotated[
        MetadataDict | None,
        Field(
            description="Arbitrary key-value annotations as a flat string-to-string dictionary."
        ),
    ] = None

    @model_validator(mode="after")
    def _experiment_unique_per_requirement_specifier(self) -> ExperimentConfig:
        """An experiment may appear only once per requirement_specifier."""
        seen: set[tuple[str, str]] = set()
        for pkg in self.packages:
            for exp_id in pkg.experiment_ids:
                key = (pkg.requirement_specifier.strip(), exp_id)
                if key in seen:
                    msg = (
                        f"experiment '{exp_id}' is declared more than once for "
                        f"requirement_specifier '{pkg.requirement_specifier}'. "
                        "A package exposes a single version of an experiment; use a "
                        "different requirement_specifier for each version."
                    )
                    raise ValueError(msg)
                seen.add(key)
        return self

    @property
    def packages(self) -> list[ExperimentSpecifier]:
        """All declared experiment packages."""
        return self.experiment_package

    @property
    def experiment_ids(self) -> set[str]:
        """Identifiers of all experiments declared across all packages."""
        return {eid for pkg in self.packages for eid in pkg.experiment_ids}


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


class InstanceVariantArtifactValues(BaseModel):
    """The files of an instance artifact that belong to a given instance variant."""

    model_config = ConfigDict(extra="forbid")

    property: Annotated[
        Property,
        Field(description="The instance artifact property these files belong to."),
    ]
    values: Annotated[
        list[str],
        Field(
            min_length=1,
            description="Files in the artifact's artifactsLocation for this variant.",
        ),
    ]


class InstanceVariant(BaseModel):
    """A combination of problem property values that falls under a single instance."""

    model_config = ConfigDict(extra="forbid")

    problemPropertyValues: Annotated[
        list[PropertyValue],
        Field(
            min_length=1,
            description="Values of the problem properties that vary across variants.",
        ),
    ]
    instanceArtifactValues: Annotated[
        list[InstanceVariantArtifactValues] | None,
        Field(description="Artifact files that are specific to this variant."),
    ] = None


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
    instancePropertyValues: Annotated[
        list[PropertyValue] | None,
        Field(
            description=(
                "Optional generative properties used to produce this instance "
                "(e.g. random seed, generator parameters). Not declared in benchmark.yaml."
            )
        ),
    ] = None
    variants: Annotated[
        list[InstanceVariant] | None,
        Field(
            description=(
                "Different combinations of problem property values that fall under "
                "this instance. Problem properties not given a value in "
                "problemPropertyValues must be given one in every variant."
            )
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
