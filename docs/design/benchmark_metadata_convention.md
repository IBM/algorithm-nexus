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
   benchmark problem: what properties it is evaluated on and what values those
   properties can take. This is the shared contract that all experiments
   targeting the same problem must conform to.

2. **Benchmark Binding** — metadata that maps an `ado` experiment's internal
   properties and metrics to the properties and metric names of a logical
   benchmark. This tells the system how to extract and label the relevant
   results from that experiment's data.

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

| Challenge                                       | Description                                                                                                                                                                                                                                                                                                                          | Design Requirement                                                                                              |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| **Heterogeneous Tooling for Homogeneous Tasks** | Different experiments may evaluate the same logical problem. For example, both `vllm-bench` and `guide-llm` measure inference-serving performance, but the system has no way to know they can address the same benchmark.                                                                                                            | The system must have a standardized way to recognize that disparate experiments can execute the same benchmark. |
| **Ambiguous and Domain-Specific Properties**    | Benchmarking domains are too diverse to share a fixed schema. A synthetic math benchmark has no "dataset" column; a quantum max-cut benchmark is characterized by `graph_type` and `node_count`.                                                                                                                                     | The system must support dynamic, per-benchmark, properties.                                                     |
| **Workload Property Fragmentation**             | Defining a workload often involves a matrix of runtime properties. If results are differentiated by raw property values, results from minor variations (`concurrency=100` vs `concurrency=105`) can never be aggregated. Further, the properties required to run the same benchmark with different experiments may be very different | The design must allow related property combinations to be collapsed into a single canonical value.              |

<!-- markdownlint-enable line-length -->

---

## 2. Logical Benchmark Definition

### 2.1 Concept

A **logical benchmark** is an abstract, domain-specific definition of a
benchmark problem. It defines:

- a unique identifier
- the **properties** on which the benchmark is evaluated (e.g. `dataset`,
  `workload`) and the valid values each property may take
- the canonical **metric names** that results should be reported under

### 2.2 Schema

**Top-level fields:**

<!-- markdownlint-disable line-length -->

| Field                 | Type            | Required | Description                                                                                                                                                                       |
| --------------------- | --------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `benchmarkIdentifier` | string          | Yes      | The canonical identifier.                                                                                                                                                         |
| `description`         | string          | Yes      | Human-readable description of the abstract problem being evaluated.                                                                                                               |
| `target`              | string          | Yes      | The property that identifiers the quantity being benchmarked                                                                                                                      |
| `properties`          | list            | Yes      | The properties on which this benchmark is evaluated. Each entry specifies the property name, an optional domain of valid values, and human-readable descriptions of those values. |
| `metrics`             | list of strings | No       | Canonical metric names for this benchmark.                                                                                                                                        |
| `owner`               | string          | No       | Team or individual responsible for maintaining this definition.                                                                                                                   |

**Property fields:**

| Field        | Type                               | Required | Description                                                                        |
| ------------ | ---------------------------------- | -------- | ---------------------------------------------------------------------------------- |
| `identifier` | string                             | Yes      | Canonical property identifier.                                                     |
| `metadata`   | string                             | No       | Metadata about what this property represents. Can include e.g. description         |
| `domain`     | orchestrator.schema.PropertyDomain | No       | Valid values for this property. If omitted, an open categorical domain is assumed. |

<!-- markdownlint-enable line-length -->

### 2.3 Example: Inference Serving

```yaml
benchmarkIdentifier: inference_serving
description: >
    Evaluation of AI model inference serving throughput and latency under
    controlled traffic conditions.
target:
    - identifier: model
      metadata:
          description: "The id of the AI model being benchmarked"
properties:
    - identifier: dataset
      metadata:
          description: "Dataset used for inference requests."
      # No domain: Will be OPEN_CATEGORICAL_DOMAIN by default
    - identifier: workload
      metadata:
          description: "Traffic pattern or workload profile."
      domain:
          values: ["steady_state_heavy", "poisson_bursty", "light_load"]
metrics:
    - throughput_tokens_per_second
    - time_to_first_token_ms
owner: "@vllm-team"
```

See
[the ado property domain documentation](https://ibm.github.io/ado/core-concepts/properties-and-domains/)
for more information about the types of domains that can be specified.

## 3. Benchmark Binding

### 3.1 Concept

For an experiment to target a logical benchmark it must provide a mapping of its
property names and values to the logical benchmark's. This is called a
**benchmark binding**. .

A benchmark binding serves two purposes:

1. **Declaration** — it defines the logical benchmark an experiment maps to

2. **Mapping** — it describes how the experiment's internal property names and
   metric names correspond to the canonical property and metric names defined by
   the logical benchmark. This allows the system to extract and consistently
   label results from this experiment without any domain-specific knowledge.

### 3.2 Schema

**Top-level fields:**

<!-- markdownlint-disable line-length -->

| Field                  | Type   | Required | Description                                                                                                                                                                                       |
| ---------------------- | ------ | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `experimentIdentifier` | string | **Yes**  | The `ado` experiment identifier.                                                                                                                                                                  |
| `benchmarkIdentifier`  | string | **Yes**  | The `id` of the logical benchmark this experiment targets.                                                                                                                                        |
| `targetMapping`        | string | **Yes**  | The name of the experiment property that carries the benchmark target (model or algorithm identifier).                                                                                            |
| `staticFilters`        | list   | No       | Sets values of experiment internal properties to those implicitly required by the logical benchmark                                                                                               |
| `propertyMapping`      | list   | No       | Maps the experiment's internal properties to the canonical properties defined by the logical benchmark.                                                                                           |
| `metricMapping`        | map    | No       | Translates per-experiment metric names to the canonical metric names defined by the logical benchmark. Required when metric names differ across experiments targeting the same logical benchmark. |

<!-- markdownlint-enable line-length -->

#### Property Mapping

Each entry in `propertyMapping` specifies how one or more experiment properties
map to canonical benchmark properties. Benchmark properties not listed
are assumed to have a 1:1 mapping with a experiment property of same name.

Two types of mapping are possible:

- _field mapping_: A 1-to-1 mapping for logical benchmark properties
    - Allows translating "WHERE logical_dim = X" to "WHERE experiment_param = X"
- _categorical value mapping_: 1-to-many mapping for the values of a categorical
  logical benchmark properties
    - Allows translating "WHERE logical_dim = CategoryA" to e.g. "WHERE
      exp_param_1 > X and exp_param_2 = y"

**Field mapping** — maps an experiment property to a benchmark property.

```yaml
propertyMapping:
    - benchmark:
          identifier: "<logical-benchmark-property-name>"
      experiment:
          identifier: "<experiment-property-name>"
```

**Categorical value mapping** — maps one or more values of a categorical
benchmark property to a set of (experiment property:allowed value set) pairs.

```yaml
propertyMapping:
    - categoricalValue:
          property:
              identifier: "<logical-benchmark-property-name>"
          value: "<categorical-value-from-logical-benchmark-domain>"
      predicate:
          - identifier: "<experiment-property-name>"
            domain: <PropertyDomain>
          - ...
```

**Static Filters:**

Static filters allow setting a property of the experiment to a value that's
implicit in the logical benchmark. For example, the benchmark experiment may
have two modes, "debug" and "production", and one should be used for a
particular logical benchmark, essentially adding "AND production == True" to all
queries.

```yaml
staticFilters:
    - property:
          identifier: "<experiment-property-name>"
      value: "<experiment-property-value>"
```

#### Metric mapping

```yaml
metricMapping:
   benchmark:
      identifier: <canonical-benchmark-property-name>
    experiment:
      identifier: <experiment-target-property-name>
```

Metrics not listed are passed through under their original names. For two
experiments to produce a merged metric column, both must map their respective
metric names to the same canonical name defined by the logical benchmark.

### 3.3 Example: `guide_llm_runner`

```yaml
benchmarkIdentifier: inference_serving
targetMapping: model_name
experiment:
    actuatorIdentifier: vllm_performance
    experimentIdentifier: guide_llm_runner
    experimentVersion: 2.0.0 # The binding only uses the major version

propertyMappings:
    - benchmark:
          identifier: dataset
      experiment:
          identifier: input_data_path # guide-llm's internal param name
    - categoricalValue:
          property:
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
          property:
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
metricMapping:
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

- The logical benchmark defines **what properties** exist and **what values**
  they can take.
- Each benchmark binding defines **how to query** one experiment's results for
  those properties and **how to label** them consistently.

A leaderboard is simply a query over a subset of the logical benchmark's
properties. Omitting a property aggregates across all its values; specifying one
filters to it.

### 4.2 Routing Key

A deterministic routing key can be constructed from a result and the benchmark
binding:

```text
{experimentIdentifier}-{experimentIdentifier}-{property1=value}-{property2=value}
```

Properties are sorted alphabetically. For example:

```text
inference_serving-guide_llm_runner-dataset=sharegpt-workload=steady_state_heavy
```

The routing key identifies a specific leaderboard slot. Leaderboard queries can
match on any prefix or subset of these components.

### 4.3 Dynamic Property Resolution

Property resolution — mapping from raw experiment properties to canonical
benchmark properties — is performed **at query time**. This means only one
database of raw results needs to be maintained.

The leaderboard population process for a given query:

1. Identify all experiments with a benchmark binding to the queried
   `logicalBenchmark`.
2. For each experiment, use its benchmark binding to construct a query against
   the result store (ado `samplestore`) (using the experiment's own internal
   property names as the filter criteria).
3. Rename result dataframe columns using `propertyMapping` and `metricMapping`
   (metric names).
4. Merge the resulting dataframes. All share the same canonical column names.

### 4.4 Cross-Experiment Aggregation Example

A second experiment, `vllm_bench_runner`, targets the same logical benchmark
with entirely different internal property and metric names:

```yaml
benchmarkIdentifier: inference_serving
experiment:
    actuatorIdentifier: vllm_performance
    experimentIdentifier: vllm_bench_runner
    experimentVersion: 1.0.0
targetMapping: model_name
propertyMappings:
    - benchmark:
          identifier: dataset
      experiment:
          identifier: dataset_path # guide-llm's internal param name
    - categoricalValue:
          property:
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
          property:
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
metricMapping:
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

### 5.2 Logical Benchmark Location & Ownership

Logical benchmark definition files are stored at the top level of the Algorithm
Nexus repository. Its suggested to create a top-level dir `benchmarks` which
contains one YAML file per logical benchmark.

A logical benchmark owner is given by the value of the "owner" field. If this is
ambiguous the author of the PR adding the benchmark will be treated as the
owner.

### 7.1 Benchmark Binding Location

Benchmark bindings are stored in the YAML file with the logical benchmarks they
target e.g. the structure of this file could be

```yaml
logicalBenchmark: ... #logical benchmark fields
bindings:
    -  #List of benchmark bindings
```

This simplifies validating the field ands values in the bindings, and
discovering bindings.

The benchmark binding is owned by the author of the PR that added it.

---

## 6. Benchmark Binding Versioning

A benchmark binding only can change if:

- The experiment property names or values used change
    - This should result in a new experiment major version and a new binding
    - The binding for the previous experiment major version can be kept
- The logical benchmark property names or values change
    - If the original logical benchmark parameters/values and mappings are now
      invalid, the existing logical benchmarks and bindings can be updated in
      place
    - If the original logical benchmark parameters/values and mappings are still
      valid, a new logical benchmark should be created
- Additional experiment properties are added that must be set to **non-default
  values** AND only experiment minor version changes
    - The binding must be changed - different sets of experiment data will be
      aggregated
    - Note: This applies to **non-default values** only - by ado versioning
      convention a minor version change means that the new parameters with
      default values measure output metrics the same way as previous experiment
      with same major version but without those parameters

---

## 7. Relationship to Existing Benchmark Design

### 7.2 `target_mapping` and the Implicit Benchmark Target

The [`benchmark_integration_design.md`](./benchmark_integration_design.md)
establishes that the benchmark target is implicit from the enclosing model
definition for model-level benchmark instances. The `target_mapping` field is
complementary, not conflicting:

- `target_mapping` in the benchmark binding names the **experiment property**
  that carries the target identifier (e.g. `model_name`).
- The **value** of that property for a specific benchmark instance is determined
  by the enclosing model definition.

For example, if the benchmark binding declares `target_mapping: model_name`, and
a model-level benchmark instance is defined for `ibm/granite-3b`, the
leaderboard system knows that `model_name=ibm/granite-3b` is the target for that
result.

### 7.3 Benchmark Package Registration and Instances

The existing `nexus.yaml` benchmark package registrations and
`benchmark_instances/space.yaml` remain unchanged. The benchmark binding is an
additional artifact and does not alter the Nexus package structure.
