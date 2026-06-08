<!--
Copyright IBM Corporation 2026
SPDX-License-Identifier: Apache-2.0
-->

# Benchmark Metadata

## Executive Summary

This document defines the **Benchmark Metadata Convention** — the metadata
design that enables benchmark results from diverse experiments to be aggregated
into leaderboards in a standardized, domain-agnostic way.

The design rests on two complementary artifacts:

1. **Logical Benchmark Definition** — a declarative description of an abstract
   benchmark problem: what dimensions it is evaluated on and what values those
   dimensions can take. This is the shared contract that all experiments
   targeting the same problem must conform to.

2. **Experiment Manifest** — metadata declared inside an `ado` experiment that
   maps the experiment's internal parameters and metrics to the canonical
   dimensions and metric names of a logical benchmark. This tells the system
   how to extract and label the relevant results from that experiment's data.

Together, these two artifacts allow the leaderboard system to remain entirely
agnostic to domain-specific concepts. All domain knowledge is expressed by the
benchmark and experiment authors; the system only needs to read the metadata
and apply it.

This convention builds on the
[Benchmarking System](./benchmark_system.md) and
[Benchmark Integration Design](./benchmark_integration_design.md) documents,
which define how experiments are packaged and registered. The present document
defines the metadata required for **leaderboard routing**.

---

## 1. Motivation

### 1.1 Challenges

Three challenges arise when aggregating results from diverse benchmark
experiments into a unified leaderboard:

<!-- markdownlint-disable line-length -->

| Challenge | Description | Design Requirement |
| --------- | ----------- | ------------------ |
| **Heterogeneous Tooling for Homogeneous Tasks** | Different experiments may evaluate the same logical problem. For example, both `vllm-bench` and `guide-llm` measure inference-serving performance, but the system has no way to know they belong to the same leaderboard. | The system must have a standardized way to recognize that disparate experiments populate the same leaderboard. |
| **Ambiguous and Domain-Specific Parameters** | Benchmarking domains are too diverse to share a fixed schema. A synthetic math benchmark has no "dataset" column; a quantum max-cut benchmark is characterized by `graph_type` and `node_count`. | The system must support dynamic, per-domain dimensions rather than hardcoded global columns. |
| **Workload Parameter Fragmentation** | Defining a workload often involves a matrix of runtime parameters. If results are differentiated by raw parameter values, minor variations (`concurrency=100` vs `concurrency=105`) produce entirely separate leaderboard entries, making comparison impossible. | The design must allow related parameter combinations to be collapsed into a single canonical value. |

<!-- markdownlint-enable line-length -->

---

## 2. Logical Benchmark Definition

### 2.1 Concept

A **logical benchmark** is an abstract, domain-specific definition of a
benchmark problem. It defines:

- a unique identifier that experiments use to declare participation
- the **dimensions** on which the benchmark is evaluated (e.g. `dataset`,
  `workload`) and the valid values each dimension may take
- the canonical **metric names** that results should be reported under

The logical benchmark definition is the shared contract. Any experiment that
claims to target a logical benchmark must conform to its dimension names and
values. This is what allows the benchmarking system to aggregate results from
different experiments without any domain-specific logic of its own.

Logical benchmark definitions are stored at the top level of the Algorithm
Nexus repository, above individual packages, so they are available as a
project-wide reference.

### 2.2 Schema

**Top-level fields:**

<!-- markdownlint-disable line-length -->

| Field | Type | Required | Description |
| ----- | ---- | -------- | ----------- |
| `id` | string | Yes | The canonical identifier referenced in experiment manifests. |
| `description` | string | Yes | Human-readable description of the abstract problem being evaluated. |
| `dimensions` | list | Yes | The canonical dimensions on which this benchmark is evaluated. Each entry specifies the dimension name, an optional domain of valid values, and human-readable descriptions of those values. See dimension fields below. |
| `metrics` | list of strings | No | Canonical metric names for this benchmark. |
| `owner` | string | No | Team or individual responsible for maintaining this definition. |

**Dimension fields:**

| Field | Type | Required | Description |
| ----- | ---- | -------- | ----------- |
| `name` | string | Yes | Canonical dimension name. |
| `description` | string | No | Human-readable description of what this dimension represents. |
| `domain` | PropertyDomain | No | Valid values for this dimension. If omitted, any value is accepted.  |
| `value_descriptions` | map | No | Human-readable description of each named value in `domain.values`, keyed by value name. This is the canonical definition of what each value means — experiment authors use this to understand the intended semantics when implementing their `profile_mapping`. Only applicable when `domain` uses a fixed `values` list. |

<!-- markdownlint-enable line-length -->

**Domain types in practice:**

The `domain` field uses `PropertyDomain` from the `ado` library. The forms
most relevant for logical benchmark dimensions are:

- **No `domain`** — any value is accepted. Appropriate for dimensions like
  `dataset` where the set of valid values is open-ended.
- **`values: [...]`** (`CATEGORICAL_VARIABLE_TYPE`) — only the listed canonical
  values are valid. Appropriate for dimensions like `workload` where experiments
  must map their parameters to one of a fixed set of named profiles to ensure
  comparability.
- **`domainRange` with `DISCRETE_VARIABLE_TYPE`** — for numeric dimensions like
  `node_count` where valid values are drawn from a range.

### 2.3 Example: Inference Serving

```yaml
id: inference_serving
description: >
  Evaluation of AI model inference serving throughput and latency under
  controlled traffic conditions.
dimensions:
  - name: dataset
    description: "Dataset used for inference requests."
    # No domain: any dataset name is accepted.

  - name: workload
    description: "Traffic pattern or workload profile."
    domain:
      values: ["steady_state_heavy", "poisson_bursty", "light_load"]
    value_descriptions:
      steady_state_heavy: >
        Sustained high-concurrency load with a constant request arrival rate.
        Represents a production serving scenario under heavy continuous traffic.
        Experiments must use a fixed/constant traffic shape with concurrency >= 100.
      poisson_bursty: >
        Variable load with Poisson-distributed request arrivals.
        Represents bursty traffic with unpredictable inter-arrival times.
        Experiments must use a Poisson traffic distribution.
      light_load: >
        Low-concurrency baseline load.
        Establishes minimum performance characteristics under light traffic.
        Experiments must use concurrency < 100.

metrics:
  - throughput_tokens_per_second
  - time_to_first_token_ms
owner: "@vllm-team"
```

---

## 3. Experiment Manifest

### 3.1 Concept

An experiment declares its participation in a logical benchmark through a
**manifest** — a block of metadata stored in the `metadata` field of the `ado`
experiment schema. A Pydantic model for the manifest schema can be contributed
to `ado` to provide schema validation.

The manifest serves two purposes:

1. **Declaration** — it states which logical benchmark this experiment
   contributes to and which experiment parameter carries the benchmark target.

2. **Mapping** — it describes how the experiment's internal parameter names
   and metric names correspond to the canonical dimensions and metric names
   defined by the logical benchmark. This allows the system to extract and
   consistently label results from this experiment without any domain-specific
   knowledge.

Because the manifest lives inside the experiment definition, the experiment
identifier is already known and does not need to be declared in the manifest
itself. It may be included explicitly when writing a standalone concretized
record.

An experiment can have at most one manifest (one `logical_benchmark`
declaration). If an experiment is used by multiple logical benchmarks, a
separate wrapper experiment should be defined for each.

### 3.2 Schema

**Top-level fields:**

<!-- markdownlint-disable line-length -->

| Field | Type | Required | Description |
| ----- | ---- | -------- | ----------- |
| `logical_benchmark` | string | **Yes** | The `id` of the logical benchmark this experiment targets. |
| `target_mapping` | string | **Yes** | The name of the experiment parameter that carries the benchmark target (model or algorithm identifier). Names the *parameter key*; the *value* for a specific run is supplied by the benchmark instance (e.g. the enclosing model definition). |
| `experiment_id` | string | No | The `ado` experiment identifier.  |
| `dimensions` | list | No | Maps the experiment's internal parameters to the canonical dimensions defined by the logical benchmark. A manifest with no `dimensions` is valid — results are associated with the `logical_benchmark` and target only. |
| `metric_mapping` | map | No | Translates per-experiment metric names to the canonical metric names defined by the logical benchmark. Required when metric names differ across experiments targeting the same logical benchmark. |

<!-- markdownlint-enable line-length -->

**Dimension fields:**

Each entry in `dimensions` maps an experiment parameter to a canonical
benchmark dimension. An entry takes one of two forms:

**Direct mapping** — the dimension value is taken directly from the named
experiment parameter:

```yaml
dimensions:
  - dimension_name: "<canonical-dimension-name>"
    mapped_from_arg: "<internal-experiment-parameter-name>"
```

**Profile mapping** — the dimension value is resolved by matching a combination
of experiment parameters against a set of named profiles. The first matching
profile is used. If no profile matches, the dimension has no value for that run.

```yaml
dimensions:
  - dimension_name: "<canonical-dimension-name>"
    profile_mapping:
      - logical_name: "<canonical-value-from-logical-benchmark-domain>"
        requires_params:
          <param_name>: <PropertyDomain>
          ...
```

<!-- markdownlint-disable line-length -->

| Field | Type | Required | Description |
| ----- | ---- | -------- | ----------- |
| `dimension_name` | string | Yes | Canonical dimension name. Must match a dimension defined in the logical benchmark. |
| `mapped_from_arg` | string | Conditional | Internal experiment parameter mapped to this dimension. Required if `profile_mapping` is absent. |
| `profile_mapping` | list | Conditional | Ordered list of profiles. Required if `mapped_from_arg` is absent. First match wins. |
| `profile_mapping[].logical_name` | string | Yes | Must be a value in the logical benchmark dimension domain. |
| `profile_mapping[].requires_params` | map | Yes | Each key is an experiment parameter name; each value is a `PropertyDomain` condition that must be satisfied. All conditions are ANDed. |

<!-- markdownlint-enable line-length -->

**Profile condition grammar:**

Each condition in `requires_params` is a `PropertyDomain`
(from `orchestrator/schema/domain.py`). The two forms relevant in practice:

```yaml
# Value membership — parameter must equal one of the listed values
param_name:
  values: ["constant"]          # categorical exact match
  values: [100, 200, 500]       # discrete numeric membership

# Numeric range — parameter must fall in [lower, upper)
param_name:
  domainRange: [100, 99999]
  variableType: CONTINUOUS_VARIABLE_TYPE
```

For open-ended upper bounds, use a practically large upper value.

**Metric mapping:**

```yaml
metric_mapping:
  <experiment_metric_name>: <canonical_metric_name>
```

Metrics not listed are passed through under their original names. For two
experiments to produce a merged metric column, both must map their respective
metric names to the same canonical name defined by the logical benchmark.

### 3.3 Example: `guide_llm_runner`

```yaml
logical_benchmark: inference_serving
target_mapping: model_name
experiment_id: guide_llm_runner

dimensions:
  - dimension_name: dataset
    mapped_from_arg: input_data_path      # guide-llm's internal param name

  - dimension_name: workload
    profile_mapping:
      - logical_name: steady_state_heavy  # must be in inference_serving domain
        requires_params:
          traffic_shape:
            values: ["constant"]
          concurrency:
            domainRange: [100, 99999]
            variableType: CONTINUOUS_VARIABLE_TYPE
      - logical_name: poisson_bursty
        requires_params:
          traffic_shape:
            values: ["poisson"]
          concurrency:
            domainRange: [1, 100]
            variableType: CONTINUOUS_VARIABLE_TYPE

metric_mapping:
  throughput_rps: throughput_tokens_per_second   # guide-llm name → canonical
  ttft_ms: time_to_first_token_ms
```

The manifest says: "any run of this experiment where `input_data_path` has a
value and where `traffic_shape` and `concurrency` together match one of the
named profiles contributes data for the `inference_serving` benchmark."

---

## 4. Leaderboards and Routing

### 4.1 How the Two Artifacts Combine

With a logical benchmark definition and one or more experiment manifests in
place, the system can answer any leaderboard query without any domain-specific
logic:

- The logical benchmark defines **what dimensions** exist and **what values**
  they can take.
- Each manifest defines **how to query** one experiment's results for those
  dimensions and **how to label** them consistently.

A leaderboard is simply a query over a subset of the logical benchmark's
dimensions. Omitting a dimension aggregates across all its values; specifying
one filters to it.

### 4.2 Routing Key

A deterministic routing key can be constructed from a result and its
experiment's manifest:

```text
{logical_benchmark}-{experiment_id}-{dimension1=value}-{dimension2=value}
```

Dimensions are sorted alphabetically. For example:

```text
inference_serving-guide_llm_runner-dataset=sharegpt-workload=steady_state_heavy
```

The routing key identifies a specific leaderboard slot. Leaderboard queries
can match on any prefix or subset of these components.

### 4.3 Dynamic Dimension Resolution

Dimension resolution — mapping from raw experiment parameters to canonical
benchmark values — is performed **at query time**, not at result-capture
time. This means only one database of raw results needs to be maintained.

The leaderboard population process for a given query:

1. Identify all experiments whose manifest declares the queried
   `logical_benchmark`.
2. For each experiment, use the manifest's `dimensions` to construct a query
   against the result store (using the experiment's own internal parameter
   names as the filter criteria).
3. Rename result dataframe columns using `dimensions` (dimension names) and
   `metric_mapping` (metric names).
4. Merge the resulting dataframes. All share the same canonical column names.

### 4.4 Cross-Experiment Aggregation Example

A second experiment, `vllm_bench_runner`, targets the same logical benchmark
with entirely different internal parameter and metric names:

```yaml
logical_benchmark: inference_serving
target_mapping: model_id
experiment_id: vllm_bench_runner

dimensions:
  - dimension_name: dataset
    mapped_from_arg: dataset_path         # vllm-bench's internal param name

  - dimension_name: workload
    profile_mapping:
      - logical_name: steady_state_heavy
        requires_params:
          distribution:
            values: ["fixed"]
          num_concurrent_requests:
            domainRange: [100, 99999]
            variableType: CONTINUOUS_VARIABLE_TYPE
      - logical_name: light_load
        requires_params:
          distribution:
            values: ["fixed"]
          num_concurrent_requests:
            domainRange: [1, 100]
            variableType: CONTINUOUS_VARIABLE_TYPE

metric_mapping:
  req_per_sec: throughput_tokens_per_second   # vllm-bench name → canonical
  time_to_first_token: time_to_first_token_ms
```

A leaderboard query for
`logical_benchmark=inference_serving, dataset=sharegpt, workload=steady_state_heavy`
will:

1. Fetch the manifest for `guide_llm_runner` and `vllm_bench_runner` (all
   experiments declaring `logical_benchmark: inference_serving`).
2. Query `guide_llm_runner` results where `input_data_path=sharegpt` AND
   `traffic_shape=constant` AND `concurrency >= 100`. Rename
   `throughput_rps` → `throughput_tokens_per_second` and
   `ttft_ms` → `time_to_first_token_ms`.
3. Query `vllm_bench_runner` results where `dataset_path=sharegpt` AND
   `distribution=fixed` AND `num_concurrent_requests >= 100`. Rename
   `req_per_sec` → `throughput_tokens_per_second` and
   `time_to_first_token` → `time_to_first_token_ms`.
4. Merge both dataframes. Both now share identical column names and can be
   displayed in a single table keyed by model.

---

## 5. Governance

### 5.1 Self-Organising Convention

In the initial phase, logical benchmark definitions are established by
convention rather than enforced by a central registry:

- The first developer to submit a benchmark experiment in a domain defines the
  logical benchmark definition for that domain, establishing the canonical
  identifier, dimensions, and valid dimension values.
- Subsequent experiments in the same domain adopt the same identifiers and
  dimension names, or propose refinements via the standard PR process.
- If an experiment uses an incorrect `logical_benchmark` identifier or an
  inconsistent dimension name, its results will not appear in the expected
  leaderboard. Teams expecting their results in a leaderboard will check their
  experiment manifest when data is missing.

### 5.2 Formal Registry

As the number of logical benchmarks grows, a formal registry can be introduced.
Logical benchmark definition files are stored at the top level of the
Algorithm Nexus repository, enabling CI to validate that any manifest declaring
a `logical_benchmark` references a known definition, and that its dimension
names and profile `logical_name` values conform to that definition's schema.

### 5.3 Manifest Ownership

The manifest is owned by the experiment author. Because metadata lives at
experiment level rather than benchmark instance level, updating the dimension
mappings for all instances of an experiment requires only updating the
experiment's manifest. No per-instance updates are needed.

---

## 6. Manifest Versioning

When a manifest changes, the system has two sources of routing information:

- **Stored run metadata** — the manifest captured in the `ado` discoveryspace
  result record at execution time.
- **Current experiment metadata** — the manifest in the latest version of the
  experiment in the `ado` actuator registry.

These two sources together cover the main change scenarios:

<!-- markdownlint-disable line-length -->

| Change type | Handling |
| ----------- | -------- |
| New `mapped_from_arg` (experiment renames an internal parameter) | Stored run metadata retains the original mapping; old results continue to route correctly. |
| New `dimension_name` (benchmark dimension is renamed) | Effectively a new dimension. The experiment author can add a legacy entry in the new manifest to re-route old results if needed. |
| New dimension added with updated mapping | Can be addressed by adding a legacy profile entry in the new manifest, or by updating metadata on historical results in the database. |
| New benchmark metadata, no parameter changes | The current experiment manifest can be applied to historical results to route them under the new metadata. |

<!-- markdownlint-enable line-length -->

---

## 7. Relationship to Existing Benchmark Design

### 7.1 Manifest Location

The manifest is stored in the `metadata` field of the `ado` `Experiment` schema
(`orchestrator/schema/experiment.py`). This field is currently an untyped
`dict`; a Pydantic model for the manifest schema can be contributed to the `ado`
library to add validation.

### 7.2 `target_mapping` and the Implicit Benchmark Target

The [`benchmark_integration_design.md`](./benchmark_integration_design.md)
establishes that the benchmark target is implicit from the enclosing model
definition for model-level benchmark instances. The `target_mapping` field is
complementary, not conflicting:

- `target_mapping` in the manifest names the **experiment parameter key** that
  carries the target identifier (e.g. `model_name`).
- The **value** of that parameter for a specific benchmark instance is
  determined by the enclosing model definition.

For example, if the manifest declares `target_mapping: model_name`, and a
model-level benchmark instance is defined for `ibm/granite-3b`, the leaderboard
system knows that `model_name=ibm/granite-3b` is the target for that result.

### 7.3 Benchmark Package Registration and Instances

The existing `nexus.yaml` benchmark package registrations and
`benchmark_instances/space.yaml` `ado` discoveryspace definitions remain
unchanged. The manifest is an additional artifact inside the experiment
package and does not alter the Nexus package structure.
