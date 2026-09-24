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

| Challenge                                       | Description                                                                                                                                                                                                                                                                                                                                    | Design Requirement                                                                                              |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| **Heterogeneous Tooling for Homogeneous Tasks** | Different experiments may evaluate the same logical problem. For example, both `vllm-bench` and `guide-llm` measure inference-serving performance, but the system has no way to know they can address the same benchmark.                                                                                                                      | The system must have a standardized way to recognize that disparate experiments can execute the same benchmark. |
| **Ambiguous and Domain-Specific Properties**    | Benchmarking domains are too diverse to share a fixed schema. A synthetic math benchmark has no "dataset" column; a quantum max-cut benchmark is characterized by `graph_type` and `node_count`.                                                                                                                                               | The system must support dynamic, per-benchmark, properties.                                                     |
| **Benchmark Instance Property Fragmentation**   | Defining a benchmark instance often involves a matrix of runtime properties. If results are differentiated by raw property values, results from minor variations (`concurrency=100` vs `concurrency=105`) can never be aggregated. Further, the properties required to run the same benchmark with different experiments may be very different | The design must allow related property combinations to be collapsed into a single canonical value.              |

<!-- markdownlint-enable line-length -->

---

## 2. Logical Benchmark Definition

### 2.1 Concept

A **logical benchmark** is an abstract, domain-specific definition of a
benchmark problem. It defines:

- a unique identifier
- the **instance** properties defining the benchmark problem instances and the valid values each property may take
- the canonical **metric names** that results should be reported under

### 2.2 Schema

**Top-level fields:**

<!-- markdownlint-disable line-length -->

| Field                 | Type             | Required | Description                                                                                                                                                                       |
| --------------------- | ---------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `benchmarkIdentifier` | string           | Yes      | The canonical identifier.                                                                                                                                                         |
| `title`               | string           | No       | Short human-readable display name for this benchmark.                                                                                                                             |
| `description`         | string           | Yes      | Human-readable description of the abstract problem being evaluated.                                                                                                               |
| `instance`            | list of Property | Yes      | The properties defining a benchmark instance. Each entry specifies the property name, an optional domain of valid values, and human-readable descriptions.                        |
| `metrics`             | list of strings  | No       | Canonical metric names for this benchmark.                                                                                                                                        |
| `ranking`             | Ranking          | No       | Defines how benchmark results are ordered on a leaderboard. See Ranking fields below.                                                                                             |
| `owner`               | string           | No       | Team or individual responsible for maintaining this definition.                                                                                                                   |

**Instance Property fields:**

| Field            | Type                               | Required | Description                                                                        |
| ---------------- | ---------------------------------- | -------- | ---------------------------------------------------------------------------------- |
| `identifier`     | string                             | Yes      | Canonical property identifier.                                                     |
| `is_artifact`    | boolean                            | No       | Uses artifact files rather than a scalar value. Default: `false`.                  |
| `metadata`       | map                                | No       | Metadata about what this property represents. Can include e.g. description         |
| `propertyDomain` | orchestrator.schema.PropertyDomain | No       | Valid values for this property. If omitted, an open categorical domain is assumed. |

**Ranking fields:**

| Field    | Type            | Required | Description                                                               |
| -------- | --------------- | -------- | ------------------------------------------------------------------------- |
| `metric` | string          | Yes      | Identifier of the metric used for ranking. Must be in the `metrics` list. |
| `order`  | "asc" or "desc" | Yes      | Sort order: "asc" for lower-is-better, "desc" for higher-is-better.       |

<!-- markdownlint-enable line-length -->

### 2.3 Example: Graph Coloring

The logical benchmark definition lives under the `logicalBenchmark` key inside
`benchmarks/<benchmark-id>/problem.yaml`. Bindings are placed in the sibling
`bindings` list in the same file (see [Section 3](#3-benchmark-binding)).

```yaml
logicalBenchmark:
    benchmarkIdentifier: graph_coloring
    title: Graph Coloring
    description: >
        Evaluates graph-coloring algorithms on their ability to produce valid
        k-colorings with a small chromatic number. Instances span random
        Erdős–Rényi graphs and structured benchmark graphs at varying densities.
    instance:
        - identifier: graph
          is_artifact: true
          metadata:
              description: Graph instance file artifact.
        - identifier: graph_family
          metadata:
              description: Graph family (erdos_renyi, planar, random_regular).
          propertyDomain:
              variableType: CATEGORICAL_VARIABLE_TYPE
              values: [erdos_renyi, planar, random_regular]
        - identifier: num_vertices
          metadata:
              description: Number of vertices in the graph.
          propertyDomain:
              variableType: DISCRETE_VARIABLE_TYPE
              values: [50, 100, 250, 500]
        - identifier: edge_density
          metadata:
              description: Edge probability / density parameter.
          propertyDomain:
              variableType: CONTINUOUS_VARIABLE_TYPE
    metrics:
        - num_colors_used
        - is_valid_coloring
        - elapsed_ms
    ranking:
        metric: num_colors_used
        order: asc

bindings:
    - ...
```

See
[the ado property domain documentation](https://ibm.github.io/ado/core-concepts/properties-and-domains/)
for more information about the types of domains that can be specified.

### 2.4 Logical Benchmark Instances and Artifacts

A logical benchmark can define concrete problem instances (e.g. specific graphs,
routing networks, or datasets). Each instance lives in its own folder under
`instances/<instance-name>/` with an `instance.yaml` file and an `artifacts/`
folder containing the actual instance files (which may include multiple file
formats of the same instance).

#### Instance Directory Layout

```text
benchmarks/<benchmark-id>/instances/<instance-name>/
├── instance.yaml
└── artifacts/
    ├── graph.dimacs
    └── graph.json
```

#### Instance Schema

Each `instance.yaml` defines a concrete problem instance. Instance properties match the property
identifiers defined under `instance:` in `problem.yaml`:

- **Scalar properties** (`is_artifact: false`, the default) are specified directly as scalar/primitive values.
- **Artifact properties** (`is_artifact: true`) are specified as a list of filenames or a map of format
  names to filenames located in the instance's `artifacts/` folder.

| Field          | Type                           | Required | Description                                                         |
| -------------- | ------------------------------ | -------- | ------------------------------------------------------------------- |
| `identifier`   | string                         | **Yes**  | Unique identifier for this benchmark instance.                      |
| `description`  | string                         | No       | Human-readable description of this specific instance.               |
| `<property_id>`| scalar / list / map of strings | No       | Values matching property identifiers defined in `problem.yaml`.     |

#### Example Instance (`benchmarks/graph-coloring/instances/erdos_renyi_50_02/instance.yaml`)

```yaml
identifier: erdos_renyi_50_02
description: 50-node Erdos-Renyi graph with edge density 0.2

# Scalar instance properties
graph_family: erdos_renyi
num_vertices: 50
edge_density: 0.2

# Artifact instance property (files in artifacts/ directory)
graph:
    - graph.dimacs
    - graph.json
```

## 3. Benchmark Binding

### 3.1 Concept

For an experiment to target a logical benchmark it must provide a mapping of its
property names and values to the logical benchmark's. This is called a
**benchmark binding**.

A benchmark binding serves two purposes:

1. **Declaration** — it defines the logical benchmark an experiment maps to

2. **Mapping** — it describes how the experiment's internal property names and
   metric names correspond to the canonical property and metric names defined by
   the logical benchmark. This allows the system to extract and consistently
   label results from this experiment without any domain-specific knowledge.

### 3.2 Schema

**Top-level fields:**

<!-- markdownlint-disable line-length -->

| Field             | Type                | Required | Description                                                                                                                                                                                       |
| ----------------- | ------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `experiment`      | ExperimentReference | **Yes**  | The `ado` ExperimentReference object.                                                                                                                                                             |
| `metricMapping`   | list                | No       | Translates per-experiment metric names to the canonical metric names defined by the logical benchmark. Required when metric names differ across experiments targeting the same logical benchmark. |
| `propertyMapping` | list                | No       | Remaps benchmark instance properties/parameters to experiment inputs.                                                                                                                             |
| `staticFilters`   | list                | No       | Sets static experiment properties to values implicit in the logical benchmark.                                                                                                                    |

<!-- markdownlint-enable line-length -->

#### Metric mapping

```yaml
metricMapping:
    - benchmark:
          identifier: <canonical-benchmark-metric-name>
      experiment:
          identifier: <experiment-metric-name>
```

Metrics not listed are passed through under their original names. For two
experiments to produce a merged metric column, both must map their respective
metric names to the same canonical name defined by the logical benchmark.

#### Property mapping

The `propertyMapping` list maps benchmark instance properties/parameters to
experiment inputs. The artifact mapping is implicit — the experiment property
being bound against determines which artifact is used. Two types of entry are
possible:

- _field mapping_: A 1-to-1 mapping for a benchmark instance property.
    - Allows translating "WHERE logical_dim = X" to "WHERE experiment_param = X"
- _categorical value mapping_: 1-to-many mapping for the values of a categorical
  benchmark instance property.
    - Allows translating "WHERE logical_dim = CategoryA" to e.g. "WHERE
      exp_param_1 > X and exp_param_2 = y"

**Field mapping** — maps an experiment property to a benchmark instance property.

```yaml
propertyMapping:
    - benchmark:
          identifier: "<benchmark-instance-property-name>"
      experiment:
          identifier: "<experiment-property-name>"
```

**Categorical value mapping** — maps one or more values of a categorical
benchmark instance property to a set of (experiment property:allowed value set)
pairs.

```yaml
propertyMapping:
    - categoricalValue:
          property:
              identifier: "<benchmark-instance-property-name>"
          value: "<categorical-value-from-benchmark-domain>"
      predicate:
          - identifier: "<experiment-property-name>"
            propertyDomain: <PropertyDomain>
          - ...
```

#### Static filters

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

**Full example:**

```yaml
propertyMapping:
    - benchmark:
          identifier: num_vertices
      experiment:
          identifier: n_nodes
    - benchmark:
          identifier: edge_density
      experiment:
          identifier: density
staticFilters:
    - property:
          identifier: graph_type
      value: erdos_renyi
```

### 3.3 Example: `guide_llm_runner`

Bindings are placed in the `bindings` list inside `problem.yaml`, alongside the
`logicalBenchmark` definition (see
[Section 2.3](#23-example-graph-coloring)):

```yaml
bindings:
    - experiment:
          actuatorIdentifier: vllm_performance
          experimentIdentifier: guide_llm_runner
          experimentVersion: 2.0.0 # The binding only uses the major version
      propertyMapping:
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
                  propertyDomain:
                      values: ["constant"]
                - identifier: concurrency
                  propertyDomain:
                      domainRange: [100, 1000]
                      variableType: CONTINUOUS_VARIABLE_TYPE
          - categoricalValue:
                property:
                    identifier: workload
                value: poisson_bursty
            predicate:
                - identifier: traffic_shape
                  propertyDomain:
                      values: ["poisson"]
                - identifier: concurrency
                  propertyDomain:
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
{benchmarkIdentifier}-{experimentIdentifier}-{property1=value}-{property2=value}
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
bindings:
    - experiment:
          actuatorIdentifier: vllm_performance
          experimentIdentifier: vllm_bench_runner
          experimentVersion: 1.0.0
      targetMapping: model_name
      propertyMapping:
          - benchmark:
                identifier: dataset
            experiment:
                identifier: dataset_path # vllm bench serve internal param name
          - categoricalValue:
                property:
                    identifier: workload
                value: steady_state_heavy
            predicate:
                - identifier: distribution
                  propertyDomain:
                      values: ["fixed"]
                - identifier: num_concurrent_requests
                  propertyDomain:
                      domainRange: [100, 99999]
                      variableType: CONTINUOUS_VARIABLE_TYPE
          - categoricalValue:
                property:
                    identifier: workload
                value: light_load
            predicate:
                - identifier: distribution
                  propertyDomain:
                      values: ["fixed"]
                - identifier: num_concurrent_requests
                  propertyDomain:
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

### 5.1 Logical Benchmark Location & Ownership

Logical benchmark definition files are stored under the `benchmarks/` directory
at the top level of the Algorithm Nexus repository. Each logical benchmark has
its own subdirectory named after its `benchmarkIdentifier`, containing a
`problem.yaml` file that holds both the `logicalBenchmark` definition and its
`bindings`:

```text
benchmarks/
└── <benchmark-id>/
    ├── problem.yaml        # logicalBenchmark definition + bindings
    └── instances/          # optional concrete problem instances
        └── <instance-name>/
            ├── instance.yaml
            └── artifacts/
```

A logical benchmark owner is given by the value of the "owner" field. If this is
ambiguous the author of the PR adding the benchmark will be treated as the
owner.

### 5.2 Benchmark Binding Location

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

### 7.1 Implicit Benchmark Target

The [`benchmark_integration_design.md`](./benchmark_integration_design.md)
establishes that the benchmark target is implicit from the enclosing model
definition for model-level benchmark submissions. The binding does not need to
name the target property explicitly — the target identity is determined by the
enclosing model or algorithm definition that owns the benchmark submission.

### 7.2 Benchmark Package Registration and Submissions

The existing `nexus.yaml` benchmark package registrations and
`benchmark_submissions/space.yaml` remain unchanged. The benchmark binding is an
additional artifact and does not alter the Nexus package structure.
