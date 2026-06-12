<!--
Copyright IBM Corporation 2026
SPDX-License-Identifier: Apache-2.0
-->

# Benchmark Metadata

## Executive Summary

This document defines the **Benchmark Metadata Convention** — the metadata
design that enables benchmark results from diverse experiments to be aggregated
in a standardized, domain-agnostic way.

The design rests on two complementary artifacts:

1. **Logical Benchmark Definition** — a declarative description of an abstract
   benchmark problem: what dimensions it is evaluated on and what values those
   dimensions can take. This is the shared contract that all experiments
   targeting the same problem must conform to.

2. **Experiment Manifest** — metadata declared inside an `ado` experiment that
   maps the experiment's internal parameters and metrics to the dimensions and
   metric names of a logical benchmark. This tells the system how to extract and
   label the relevant results from that experiment's data.

Together, these two artifacts allow the benchmarking system to remain agnostic
to domain-specific concepts. All domain knowledge is expressed by the benchmark
and experiment authors; the system only needs to read the metadata and apply it.

This convention builds on the [Benchmarking System](./benchmark_system.md) and
[Benchmark Integration Design](./benchmark_integration_design.md) documents,
which define how experiments are packaged and registered.

---

## 1. Motivation

### 1.1 Challenges

Three challenges arise when aggregating results from diverse benchmark
experiments:

<!-- markdownlint-disable line-length -->

| Challenge                                       | Description                                                                                                                                                                                                                                                                                                               | Design Requirement                                                                                              |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| **Heterogeneous Tooling for Homogeneous Tasks** | Different experiments may evaluate the same logical problem. For example, both `vllm-bench` and `guide-llm` measure inference-serving performance, but the system has no way to know they can address the same benchmark.                                                                                                 | The system must have a standardized way to recognize that disparate experiments can execute the same benchmark. |
| **Ambiguous and Domain-Specific Parameters**    | Benchmarking domains are too diverse to share a fixed schema. A synthetic math benchmark has no "dataset" column; a quantum max-cut benchmark is characterized by `graph_type` and `node_count`.                                                                                                                          | The system must support dynamic, per-benchmark, dimensions.                                                     |
| **Workload Parameter Fragmentation**            | Defining a workload often involves a matrix of runtime parameters. If results are differentiated by raw parameter values, results from minor variations (`concurrency=100` vs `concurrency=105`) can never be aggregated. Further, the parameters required to run the same benchmark with different may be very different | The design must allow related parameter combinations to be collapsed into a single canonical value.             |

<!-- markdownlint-enable line-length -->

---

## 2. Logical Benchmark Definition

### 2.1 Concept

A **logical benchmark** is an abstract, domain-specific definition of a
benchmark problem. It defines:

- a unique identifier
- the **dimensions** on which the benchmark is evaluated (e.g. `dataset`,
  `workload`) and the valid values each dimension may take
- the canonical **metric names** that results should be reported under

The logical benchmark definition is the shared contract. Any experiment that
claims to target a logical benchmark must conform to its dimension names and
values. This is what allows the benchmarking system to aggregate results from
different experiments without any domain-specific logic of its own.

Logical benchmark definitions are stored at the top level of the Algorithm Nexus
repository, above individual packages, so they are available as a project-wide
reference.

### 2.2 Schema

**Top-level fields:**

<!-- markdownlint-disable line-length -->

| Field         | Type            | Required | Description                                                                                                                                                                                                    |
| ------------- | --------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`          | string          | Yes      | The canonical identifier referenced in experiment manifests.                                                                                                                                                   |
| `description` | string          | Yes      | Human-readable description of the abstract problem being evaluated.                                                                                                                                            |
| `dimensions`  | list            | Yes      | The dimensions on which this benchmark is evaluated. Each entry specifies the dimension name, an optional domain of valid values, and human-readable descriptions of those values. See dimension fields below. |
| `metrics`     | list of strings | No       | Canonical metric names for this benchmark. Experiment manifests use these names as the targets of their `metric_mapping`.                                                                                      |
| `owner`       | string          | No       | Team or individual responsible for maintaining this definition.                                                                                                                                                |

**Dimension fields:**

| Field               | Type           | Required | Description                                                                                 |
| ------------------- | -------------- | -------- | ------------------------------------------------------------------------------------------- |
| `name`              | string         | Yes      | Canonical dimension name.                                                                   |
| `description`       | string         | No       | Human-readable description of what this dimension represents.                               |
| `domain`            | PropertyDomain | No       | Valid values for this dimension. If omitted, an open categorical domain is assumed.         |
| `valueDescriptions` | map            | No       | For categorical domains a human-readable description of each category, keyed by value name. |

<!-- markdownlint-enable line-length -->

### 2.3 Example: Inference Serving

```yaml
id: inference_serving
description: >
    Evaluation of AI model inference serving throughput and latency under
    controlled traffic conditions.
dimensions:
    - identifier: dataset
      description: "Dataset used for inference requests."
      # No domain: Will be OPEN_CATEGORICAL_DOMAIN by default

    - identifier: workload
      description: "Traffic pattern or workload profile."
      domain:
          values: ["steady_state_heavy", "poisson_bursty", "light_load"]
      valueDescriptions:
          steady_state_heavy: >
              Sustained high-concurrency load with a constant request arrival
              rate. Represents a production serving scenario under heavy
              continuous traffic. Experiments must use a fixed/constant traffic
              shape with concurrency >= 100.
          poisson_bursty: >
              Variable load with Poisson-distributed request arrivals.
              Represents bursty traffic with unpredictable inter-arrival times.
              Experiments must use a Poisson traffic distribution.
          light_load: >
              Low-concurrency baseline load. Establishes minimum performance
              characteristics under light traffic. Experiments must use
              concurrency < 100.
metrics:
    - throughput_tokens_per_second
    - time_to_first_token_ms
owner: "@vllm-team"
```

---

## 3. Benchmark Binding

### 3.1 Concept

An experiment declares its participation in a logical benchmark through a
**benchark binding** — a block of metadata stored in the `metadata` field of the
`ado` experiment schema. Any expeirment can define multiple benchmark bindings.

A benchmark binding serves two purposes:

1. **Declaration** — it defines a logical benchmark this experiment maps to

2. **Mapping** — it describes how the experiment's internal parameter names and
   metric names correspond to the canonical dimensions and metric names defined
   by the logical benchmark. This allows the system to extract and consistently
   label results from this experiment without any domain-specific knowledge.

### 3.2 Schema

**Top-level fields:**

<!-- markdownlint-disable line-length -->

| Field              | Type   | Required | Description                                                                                                                                                                                                             |
| ------------------ | ------ | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `logicalBenchmark` | string | **Yes**  | The `id` of the logical benchmark this experiment targets.                                                                                                                                                              |
| `targetNapping`    | string | **Yes**  | The name of the experiment parameter that carries the benchmark target (model or algorithm identifier).                                                                                                                 |
| `experimentid`     | string | No       | The `ado` experiment identifier.                                                                                                                                                                                        |
| `staticFilters`    | list   | No       | Sets experiment internal parameters to set values implicitly required by the logical benchmark                                                                                                                          |
| `dimensionMapping` | list   | No       | Maps the experiment's internal parameters to the canonical dimensions defined by the logical benchmark. A manifest with no `dimensions` is valid — results are associated with the `logical_benchmark` and target only. |
| `metricNapping`    | map    | No       | Translates per-experiment metric names to the canonical metric names defined by the logical benchmark. Required when metric names differ across experiments targeting the same logical benchmark.                       |

<!-- markdownlint-enable line-length -->

**Dimension Mapping:**

Each entry in `dimensionMapping` specifies how one or more experiment parameters
map to canonical benchmark dimensions. Two types of mapping are possible:

- _field mapping_: A 1-to-1 mapping for logical benchmark dimensionsx
    - Allows translating "WHERE logical_dim = X" to "WHERE experiment_param = X"
- _categorical value mapping_: 1-to-many mapping for the values of a categorical
  logical benchmark dimensions
    - Allows translating "WHERE logical_dim = CategoryA" to e.g. "WHERE
      exp_param_1 > X and exp_param_2 = y"

**Field mapping** — maps an experiment parameter to a benchmark dimension.

```yaml
dimensionMapping:
    - dimension:
          identifier: "<logical-benchmark-dimension-name>"
      experimentParameter:
          identifier: "<experiment-parameter-name>"
```

**Categorical value mapping** — maps one or more values of a categorical
benchmark dimension to a set of (experiment parameter:allowed value set) pairs.

```yaml
dimensionMapping:
    - categoricalValue:
          dimension:
              identifier: "<logical-benchmark-dimension-name>"
          value: "<categorical-value-from-logical-benchmark-domain>"
      predicate:
          - identifier: "<experiment-parameter-name>"
            domain: <PropertyDomain>
          - ...
```

**Static Filters:**

Static filters allow setting a parameter of the experiment to a value that's
implicit in the logical benchmark. For example, the benchmark experiment may
have two modes, "debug" and "production", and one should be used for a
particular logical benchmark, essentially adding "AND production == True" to all
queries.

```yaml
staticFilters:
    - property:
          identifier: "<experiment-parameter-name>"
      value: "<categorical-value-from-logical-benchmark-domain>"
```

**Metric mapping:**

```yaml
metricMapping:
   benchmark:
      identifier: <canonical benchmark name>
    experiment:
      identifier: <experiment target property name>
```

Metrics not listed are passed through under their original names. For two
experiments to produce a merged metric column, both must map their respective
metric names to the same canonical name defined by the logical benchmark.

### 3.3 Example: `guide_llm_runner`

```yaml
logicalBenchmark: inference_serving
targetMapping: model_name
experimentid: guide_llm_runner

dimensionMappings:
    - dimension:
          identifier: dataset
      experimentParameter:
          identifier: input_data_path # guide-llm's internal param name
    - categoricalValue:
          dimension:
              identifier: workload
          value: steady_state_heavy
      predicate:
          - identifier: traffic_shape
            domain:
                values: ["constant"]
          - identifier: concurrency
            domain:
                domainRange: [100, 1000]
                variableType: CONTINUOUS_VARIABLE_TYPE
    - categoricalValue:
          dimension:
              identifier: workload
          value: steady_state_heavy
      predicate:
          - identifier: traffic_shape
            domain:
                values: ["poisson"]
          - identifier: concurrency
            domain:
                domainRange: [1, 100]
                variableType: CONTINUOUS_VARIABLE_TYPE
metric_mapping:
    - benchmark:
          identifier: throughput_tokens_per_second
      experiment:
          identifier: throughput_rps # guide-llm's internal param name
    - benchmark:
          identifier: time_to_first_token_ms
      experiment:
          identifier: ttft_ms
```

---

## 4. Leaderboards and Routing

### 4.1 How the Two Artifacts Combine

With a logical benchmark definition and one or more experiment benchmark
bindings in place, the system can answer aggregation queries without any
domain-specific logic:

- The logical benchmark defines **what dimensions** exist and **what values**
  they can take.
- Each benchmark binding defines **how to query** one experiment's results for
  those dimensions and **how to label** them consistently.

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

The routing key identifies a specific leaderboard slot. Leaderboard queries can
match on any prefix or subset of these components.

### 4.3 Dynamic Dimension Resolution

Dimension resolution — mapping from raw experiment parameters to canonical
benchmark values — is performed **at query time**. This means only one database
of raw results needs to be maintained.

The leaderboard population process for a given query:

1. Identify all experiments whose manifest declares the queried
   `logicalBenchmark`.
2. For each experiment, use the benchmark binding for the logical benchmark to
   construct a query against the result store (using the experiment's own
   internal parameter names as the filter criteria).
3. Rename result dataframe columns using `dimensions` (dimension names) and
   `metricMapping` (metric names).
4. Merge the resulting dataframes. All share the same canonical column names.

### 4.4 Cross-Experiment Aggregation Example

A second experiment, `vllm_bench_runner`, targets the same logical benchmark
with entirely different internal parameter and metric names:

```yaml
logicalBenchmark: inference_serving
targetMapping: model_name
experimentid: vllm_bench_runner

dimensionMappings:
    - dimension:
          identifier: dataset
      experimentParameter:
          identifier: dataset_path # guide-llm's internal param name
    - categoricalValue:
          dimension:
              identifier: workload
          value: steady_state_heavy
      predicate:
          - identifier: distribution
            domain:
                values: ["fixed"]
          - identifier: num_concurrent_requests
            domain:
                domainRange: [100, 99999]
                variableType: CONTINUOUS_VARIABLE_TYPE
    - categoricalValue:
          dimension:
              identifier: workload
          value: light_load
      predicate:
          - identifier: distribution
            domain:
                values: ["fixed"]
          - identifier: num_concurrent_requests
            domain:
                domainRange: [1, 100]
                variableType: CONTINUOUS_VARIABLE_TYPE
metric_mapping:
    - benchmark:
          identifier: throughput_tokens_per_second
      experiment:
          identifier: req_per_sec
    - benchmark:
          identifier: time_to_first_token_ms
      experiment:
          identifier: time_to_first_token
```

A leaderboard query for
`logical_benchmark=inference_serving, dataset=sharegpt, workload=steady_state_heavy`
will:

1. Fetch the manifest for `guide_llm_runner` and `vllm_bench_runner` (all
   experiments declaring `logical_benchmark: inference_serving`).
2. Query `guide_llm_runner` results where `input_data_path=sharegpt` AND
   `traffic_shape=constant` AND `concurrency >= 100`. Rename `throughput_rps` →
   `throughput_tokens_per_second` and `ttft_ms` → `time_to_first_token_ms`.
3. Query `vllm_bench_runner` results where `dataset_path=sharegpt` AND
   `distribution=fixed` AND `num_concurrent_requests >= 100`. Rename
   `req_per_sec` → `throughput_tokens_per_second` and `time_to_first_token` →
   `time_to_first_token_ms`.
4. Merge both dataframes. Both now share identical column names and can be
   displayed in a single table keyed by model.

---

## 5. Governance

### 5.2 Formal Registry

Logical benchmark definition files are stored at the top level of the Algorithm
Nexus repository, enabling CI to validate that any manifest declaring a
`logical_benchmark` references a known definition, and that its dimension names
and profile `logical_name` values conform to that definition's schema.

### 5.3 Benchmark Binding Ownership

The benchmark binding is owned by the experiment author. Because metadata lives
at experiment level rather than benchmark instance level, updating the dimension
mappings for all instances of an experiment requires only updating the
experiment's manifest. No per-instance updates are needed.

---

## 6. Benchmark Binding Versioning

When a benchmark binding changes, the system has two sources of routing
information:

- **Stored run metadata** — the manifest captured in the `ado` discoveryspace
  result record at execution time.
- **Current experiment metadata** — the manifest in the latest version of the
  experiment in the `ado` actuator registry.

These two sources together cover the main change scenarios:

<!-- markdownlint-disable line-length -->

| Change type                                           | Handling                                                                                                                              |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Experiment renames an internal parameter              | Stored run metadata retains the original mapping; old results continue to route correctly.                                            |
| New `dimension_name` (benchmark dimension is renamed) | Effectively a new dimension. The experiment author can add a legacy entry in the new manifest to re-route old results if needed.      |
| New dimension added with updated mapping              | Can be addressed by adding a legacy profile entry in the new manifest, or by updating metadata on historical results in the database. |
| New benchmark metadata, no parameter changes          | The current experiment manifest can be applied to historical results to route them under the new metadata.                            |

<!-- markdownlint-enable line-length -->

---

## 7. Relationship to Existing Benchmark Design

### 7.1 Benchmark Binding Location

Benchmark bindings are stored in the `metadata` field of the `ado` `Experiment`
schema. This field is currently an untyped `dict`; a Pydantic model for the
manifest schema can be contributed to the `ado` library to add validation.

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
unchanged. The benchmark binding is an additional artifact inside the experiment
package and does not alter the Nexus package structure.
