<!--
Copyright IBM Corporation 2026
SPDX-License-Identifier: Apache-2.0
-->

# Benchmark Metadata

## Executive Summary

This document defines the **Benchmark Metadata Convention** — a declarative
contract that enables aggregating the results of benchmark experiments in Algorithm Nexus
in a standardized, domain-agnostic way.
The motiviating use-case is for aggregating the data to show in a leaderboard:
we call this here "leaderboard routing".

The core requirement is that the benchmarking system itself should not contain any
domain knowledge. Instead, each experiment author declares one or more **benchmark
metadata manifests** within their `ado` experiment definition. Each manifest
describes how the experiment's and its parameters maps to a logical benchmark.
The system can then use this manifest to aggregate the data required for a leaderboard
without any particular domain's vocabulary.

This convention builds on the
[Benchmarking System](./benchmark_system.md) and
[Benchmark Integration Design](./benchmark_integration_design.md) documents,
which define how experiments are packaged and registered. The present document
defines the metadata required for **leaderboard routing**.

---

## 1. Motivation

### 1.1 Challenges

Three challenges arise when routing results from diverse benchmark experiments
to a unified leaderboard:

<!-- markdownlint-disable line-length -->

| Challenge | Description | Design Requirement |
| --------- | ----------- | ------------------ |
| **Heterogeneous Tooling for Homogeneous Tasks** | Different experiments may evaluate the same logical problem. For example, both `vllm-bench` and `guide-llm` measure inference-serving performance, but the system has no way to know they belong to the same leaderboard. | The system must have a standardized way to recognize that disparate experiments populate the same leaderboard. |
| **Ambiguous and Domain-Specific Parameters** | Benchmarking domains are too diverse to share a fixed schema. A synthetic math benchmark has no "dataset" column; a quantum max-cut benchmark routes on `graph_type` and `node_count`. | The system must support dynamic, per-domain routing dimensions rather than hardcoded global columns. |
| **Workload Parameter Fragmentation** | Defining a workload often involves a matrix of runtime parameters. If results are routed by raw parameter values, minor variations (`concurrency=100` vs `concurrency=105`) produce entirely separate leaderboard entries, making comparison impossible. | The design must allow related parameter combinations to be collapsed into a single canonical routing value. |

<!-- markdownlint-enable line-length -->

## 2. Core Concepts

- **Logical Benchmark** — An abstract, universally-agreed-upon identifier for
  the problem category being evaluated (e.g., `inference_serving`,
  `max_cut_solver`). Multiple experiments from different tools may target the
  same logical benchmark, which is how the system knows to aggregate their
  results together.
- **Routing Axis** — A mapping from an internal experiment parameter name
  to a canonical name (e.g., `dataset`,
  `workload`). The canonical name will be the name of a column in a leaderboard.
- **Logical Profile** — A named grouping that collapses a combination of raw
  execution parameter values into a single canonical string. For example,
  grouping various concurrency and traffic-shape settings under the name
  `steady_state_heavy`. Logical profiles prevent leaderboard fragmentation
  caused by minor parameter variations.
- **Benchmark Metadata Manifest** — The benchmark routing metadata declared
  within an `ado` experiment's `metadata` field.

---

## 3. Benchmark Metadata Manifest Schema

The manifest is stored in the `metadata` field of the `ado` experiment schema.
A Pydantic model for this field can be contributed to the `ado` library to
provide schema validation.

Because the manifest lives inside the experiment definition, the
`experiment_id` is already known from the enclosing experiment and does not
need to be declared in the manifest itself. When the manifest is extracted or
exported from an experiment (for example, to populate a leaderboard query), a
consumer can concretize a full routing record by injecting the experiment
identifier at that point.

### 3.1 Top-Level Fields

<!-- markdownlint-disable line-length -->

| Field | Type | Required | Description | Example |
| ------- | ---- | -------- | ------------- | ------- |
| `logical_benchmark` | string | **Yes** | An agreed-upon identifier for the abstract problem this experiment evaluates. Without this field the system cannot route to any leaderboard. | `inference_serving`, `max_cut_solver` |
| `target_mapping` | string | **Yes** | The name of the experiment parameter that carries the benchmark target (model or algorithm identifier). Names the *parameter key*; the *value* for a specific run is supplied by the benchmark instance (e.g., the enclosing model definition). | `model_name`, `model_id` |
| `experiment_id` | string | No | The `ado` experiment identifier. Derived automatically from the enclosing experiment definition and does not need to be declared in the manifest. May be included explicitly for documentation clarity or to produce a self-contained concretized record. | `guide_llm_runner` |
| `routing_axes` | list | No | Leaderboard dimensions beyond the target. A manifest with no `routing_axes` is valid — results will be aggregated for the `logical_benchmark` filtered only by target. Most experiments will define at least one axis. | See Section 3.2. |
| `metric_mapping` | map | No | Translates per-experiment metric names to canonical benchmark-level names. Only required when metric names need to be harmonized across experiments targeting the same logical benchmark. | See Section 3.4. |

<!-- markdownlint-enable line-length -->

### 3.2 Tier 2: Domain-Specific Routing Axes

The `routing_axes` field is a list of axis definitions. Each axis maps an
internal experiment parameter to a canonical benchmark parameter (leaderboard column).
An axis definition takes one of two forms:

**Direct mapping** — the axis value is taken directly from the named experiment
argument:

```yaml
routing_axes:
  - axis_name: "<canonical-leaderboard-dimension>"
    mapped_from_arg: "<internal-experiment-parameter-name>"
```

**Profile mapping** — the axis value is resolved by matching a combination of
raw execution parameters against a set of named profiles. The first profile
whose `requires_params` conditions are all satisfied is used. If no profile
matches, the axis has no value for that run and the result will not appear in
leaderboard views that filter on this axis.

```yaml
routing_axes:
  - axis_name: "<canonical-leaderboard-dimension>"
    profile_mapping:
      - logical_name: "<canonical-profile-name>"
        requires_params:
          <param_name>: "<value-or-condition>"
          ...
```

**Fields summary:**

<!-- markdownlint-disable line-length -->

| Field | Type | Required | Description |
| ----- | ---- | -------- | ----------- |
| `axis_name` | string | Yes | Canonical name of this leaderboard dimension. |
| `mapped_from_arg` | string | Conditional | The internal experiment parameter mapped to this axis. Required if `profile_mapping` is absent. |
| `profile_mapping` | list | Conditional | Ordered list of logical profiles for this axis. Required if `mapped_from_arg` is absent. Profiles are evaluated in declaration order; the first match wins. |
| `profile_mapping[].logical_name` | string | Yes | Canonical string this profile resolves to on the leaderboard. |
| `profile_mapping[].requires_params` | map | Yes | Conditions on experiment parameter values that must all be satisfied for this profile to match. See Section 3.3 for the condition grammar. |

<!-- markdownlint-enable line-length -->

### 3.3 Profile Condition Grammar

Each value in a `requires_params` map is a condition expressed as a
`PropertyDomain` (from the ADO orchestrator schema), evaluated against the
actual experiment parameter of the same name. Reusing `PropertyDomain` means
no new condition language needs to be defined or implemented, and the manifest
Pydantic model can reference the existing ADO type directly.

The two `PropertyDomain` forms relevant for profile conditions are:

**Value membership** — the parameter must be one of the listed values:

```yaml
requires_params:
  traffic_shape:
    values: ["constant"]         # categorical: exact match
  concurrency:
    values: [100, 200, 500]      # discrete: one of these specific numbers
```

**Numeric range** — the parameter must fall within a half-open interval
`[lower, upper)`:

```yaml
requires_params:
  concurrency:
    domainRange: [100, 99999]    # continuous: 100 <= concurrency < 99999
    variableType: CONTINUOUS_VARIABLE_TYPE
```

For open-ended upper bounds (e.g. "concurrency > 100"), use a practically
unbounded upper value. The full `PropertyDomain` field set and its validation
semantics are defined in `orchestrator/schema/domain.py` in the ADO library.

All conditions in a single `requires_params` block must be satisfied for the
profile to match (logical AND). Profiles are evaluated in declaration order;
the first matching profile wins. If no profile matches, the axis has no value
for that run and the result will not appear in leaderboard views that filter
on this axis.

### 3.4 Metric Name Mapping

When multiple experiments target the same logical benchmark but name their
output metrics differently, a `metric_mapping` field allows their results to be
merged into a unified leaderboard view. The mapping translates per-experiment
metric names to canonical benchmark-level metric names.

```yaml
metric_mapping:
  <experiment_metric_name>: <canonical_metric_name>
```

Metrics not listed in the mapping are passed through under their original names.

For two experiments to produce a single merged metric column on the leaderboard,
**both** manifests must map their respective metric names to the same canonical
name. If only one experiment provides a mapping, the other experiment's metric
will appear as a separate column under its original name, resulting in two
distinct columns rather than a merged one. Experiment authors must therefore
coordinate on canonical metric names within a logical benchmark domain.

---

## 4. Complete Examples

### 4.1 AI Inference Serving

This example shows both direct axis mapping and logical profile mapping.

```yaml
# Tier 1: Universal Core
logical_benchmark: inference_serving
target_mapping: model_name
experiment_id: guide_llm_runner

# Tier 2: Domain-Specific Routing Axes
routing_axes:
  - axis_name: "dataset"
    mapped_from_arg: "input_data_path"

  - axis_name: "workload"
    profile_mapping:
      - logical_name: "steady_state_heavy"
        requires_params:
          traffic_shape:
            values: ["constant"]
          concurrency:
            domainRange: [100, 99999]
            variableType: CONTINUOUS_VARIABLE_TYPE
      - logical_name: "poisson_heavy"
        requires_params:
          traffic_shape:
            values: ["poisson"]
          request_rate:
            values: ["100"]
```

Example routing key (after concretization with `experiment_id`):
`inference_serving-guide_llm_runner-dataset=sharegpt-workload=poisson_heavy`

This will

- find all results for the guide_llm_runner experiment
- filter by those whose dataset is `sharegpt`
- filter by those whose traffic-shape is "poisson" and whose rate is 100.

### 4.2 Quantum Max-Cut Solver

This example shows a different domain with entirely different routing axes and
no profile mapping.

```yaml
# Tier 1: Universal Core
logical_benchmark: max_cut_solver
target_mapping: algorithm_id
experiment_id: qaoa_maxcut_runner

# Tier 2: Domain-Specific Routing Axes
routing_axes:
  - axis_name: "graph_type"
    mapped_from_arg: "topology_generator"
  - axis_name: "node_count"
    mapped_from_arg: "num_nodes"
```

Example routing key:
`max_cut_solver-qaoa_maxcut_runner_qiskit-graph_type=regular-node_count=200`

---

## 5. Routing Mechanism

### 5.1 Deterministic Routing Key

After concretizing the manifest with the experiment identifier, a deterministic
routing key can be constructed from a given benchmark result:

```text
{logical_benchmark}-{experiment_id}-{axis1=value}-{axis2=value}
```

Axes are sorted alphabetically. This key uniquely identifies a specific
leaderboard slot for a given result.

### 5.2 Flexible Leaderboard Queries

A leaderboard is not required to filter on the full routing key. Instead, a
leaderboard is associated with a **query on a subset of keys**, enabling
flexible aggregation:

- Omitting `experiment_id` aggregates results across all experiments for a
  given `logical_benchmark`.
- Filtering on `dataset` while omitting `workload` shows all workload profiles
  for a fixed dataset.
- Any subset of keys can be combined to form a leaderboard view.

### 5.3 Dynamic Axis Resolution

Axis resolution — mapping from raw experiment parameters to canonical leaderboard
values — is performed **at query time**, not at result-capture time. This
avoids maintaining a second database of pre-resolved results.

The leaderboard population process is:

1. Fetch the manifest for each benchmark experiment required by the leaderboard
   query.
2. For each experiment, query the result store for all results matching the
   leaderboard's routing axis criteria, using the experiment's `routing_axes`
   definitions as the query template.
3. Rename result dataframe columns according to the manifest's `routing_axes`
   and `metric_mapping`.
4. Merge the resulting dataframes.

---

## 6. Governance of Logical Benchmarks

### 6.1 Self-Organising Convention

Logical benchmark identifiers are established by convention rather than a
central registry:

- The first developer to submit a benchmark experiment in a domain defines the
  first manifest for that domain, establishing the `logical_benchmark`
  identifier and the canonical routing axis names.
- Subsequent experiments in the same domain adopt the same identifiers and axis
  names, or propose refinements via the standard PR process.
- If an experiment uses an incorrect `logical_benchmark` identifier or an
  inconsistent axis name, its results will not appear in the expected
  leaderboard. This provides a natural correction incentive: teams expecting
  their results to appear in a leaderboard will check their experiment
  definition when data is missing.

A formal `logical_benchmark` registry can be introduced as an extension if
identifier drift becomes a problem in practice.

### 6.2 Manifest Ownership

The manifest is owned by the experiment author. Because metadata lives at
experiment level rather than benchmark instance level, updating routing for all
instances of an experiment requires only updating the experiment's manifest.
No per-instance updates are needed.

---

## 7. Manifest Versioning

When a manifest changes, the system has two sources of routing information
available:

- **Stored run metadata** — the metadata associated with a completed benchmark
  run in the ADO discoveryspace result record. This preserves the manifest as
  it was at execution time.
- **Current experiment metadata** — the manifest in the latest version of the
  experiment in the ADO actuator registry.

These two sources together cover the main manifest change scenarios:

| Change type | Handling |
| ----------- | -------- |
| New `mapped_from_arg` (experiment renames an internal parameter) | The stored run metadata retains the original mapping; old results continue to route correctly via the stored manifest. |
| New `axis_name` (leaderboard dimension is renamed) | Effectively a new leaderboard dimension; old and new results route to separate axes. The experiment author can add a legacy entry in the new manifest to re-route old results if needed. |
| New axis added with updated mapping | Can be addressed by adding a legacy profile entry in the new manifest, or by updating the metadata on historical results in the database. |
| New benchmark metadata, no parameter changes | The current experiment manifest can be applied to historical results to route them under the new metadata. |

---

## 8. Relationship to Existing Benchmark Design

### 8.1 Manifest Location

The benchmark metadata manifest is stored in the `metadata` field of the `ado`
experiment schema, placing it inside the experiment definition. This is
consistent with the principle that the experiment owns its routing metadata, as
established by the
[Benchmarking System design](./benchmark_system.md). A Pydantic model for the
manifest schema can be contributed to the ADO library.

### 8.2 `target_mapping` and the Implicit Benchmark Target

The [`benchmark_integration_design.md`](./benchmark_integration_design.md)
establishes that the benchmark target is implicit from the enclosing model
definition for model-level benchmark instances. The `target_mapping` field in
this convention is complementary, not conflicting:

- `target_mapping` in the manifest names the **experiment parameter key** that
  carries the target identifier (e.g., `model_name`).
- The **value** of that parameter for a specific benchmark instance is
  determined by the enclosing model definition, as described in
  `benchmark_integration_design.md`.

For example, if the manifest declares `target_mapping: model_name`, and a
model-level benchmark instance is defined for `ibm/granite-3b`, the leaderboard
system knows that `model_name=ibm/granite-3b` is the target dimension for that
result.

### 8.3 Benchmark Package Registration and Instances

The existing `nexus.yaml` benchmark package registrations and
`benchmark_instances/space.yaml` ADO discoveryspace definitions remain
unchanged. The benchmark metadata manifest is an additional artifact inside the
experiment package; it does not alter the Nexus package structure.
