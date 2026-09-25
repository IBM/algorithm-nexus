<!--
Copyright IBM Corporation 2026
SPDX-License-Identifier: Apache-2.0
-->

# Logical Benchmarks and Instances

## Executive Summary

This document specifies how to add **logical benchmarks** and **benchmark
instances**. It also defines how an experiment binds to a logical benchmark so
results from diverse experiments can be aggregated in a standardized,
domain-agnostic way.

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
to domain-specific concepts. All domain knowledge is expressed by the logical
benchmark, benchmark instance and benchmark experiment authors; the system only
needs to read the metadata and apply it.

### Requirements to Design Mapping

| Requirement | Design interpretation                                                                                                     |
| ------------| --------------------------------------------------------------------------------------------------------------------------|
| REQ 2.1     | A logical benchmark is registered as `benchmarks/<id>/benchmark.yaml`                                                     |
| REQ 2.2     | A benchmark instance is registered as `benchmarks/<id>/instances/<name>/instance.yaml`                                    |
| REQ 2.5     | Logical benchmarks and instances are listed by scanning `benchmarks/`                                                     |
| REQ 3.3     | A logical benchmark or instance can be referenced by any experiment or submission                                         |
| REQ 5.2     | Bindings map experiment outputs onto the logical benchmark's properties and metric names so stored results share a schema |
| REQ 5.3     | Bindings and instance metadata carry the domain-specific context stored alongside results                                 |
| REQ 7.1     | Logical benchmarks and instances live under top-level `benchmarks/`, independent of any Nexus package                     |

---

## 1. Motivation

### 1.1 Challenges

Three challenges arise when aggregating results from diverse benchmark
experiments:

<!-- markdownlint-disable line-length -->

| Challenge                                       | Description                                                                                                                                                                                                                                                                                                                                    | Design Requirement                                                                                              |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| **Heterogeneous Tooling for Homogeneous Tasks** | Different experiments may evaluate the same logical problem. For example, both `vllm-bench` and `guide-llm` measure inference-serving performance, but the system has no way to know they can address the same logical benchmark.                                                                                                              | The system must recognize that disparate experiments can address the same logical benchmark.                    |
| **Ambiguous and Domain-Specific Properties**    | Benchmarking domains are too diverse to share a fixed schema. A synthetic math logical benchmark has no "dataset" column; a quantum max-cut logical benchmark is characterized by `graph_type` and `node_count`.                                                                                                                               | The system must support dynamic, per-logical-benchmark, properties.                                             |
| **Benchmark Instance Property Fragmentation**   | Defining a benchmark instance often involves a matrix of runtime properties. If results are differentiated by raw property values, results from minor variations (`concurrency=100` vs `concurrency=105`) can never be aggregated. Further, the properties required to address the same logical benchmark with different experiments may differ| The design must allow related property combinations to be collapsed into a single canonical value.              |

<!-- markdownlint-enable line-length -->

---

## 2. Logical Benchmark Definition

### 2.1 Concept

A **logical benchmark** is an abstract, reusable definition of a problem class
or evaluation task (the benchmark problem). It defines:

- a unique identifier
- the **instance** properties defining the benchmark problem instances and the
  valid values each property may take
- the canonical **metric names** that results should be reported under

### 2.2 Schema

**Top-level fields:**

<!-- markdownlint-disable line-length -->

| Field                 | Type                              | Required | Description                                                                                                                                                                  |
| --------------------- | --------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `benchmarkIdentifier` | string                            | Yes      | The canonical identifier.                                                                                                                                                    |
| `title`               | string                            | No       | Short human-readable display name for this logical benchmark.                                                                                                                |
| `description`         | string                            | Yes      | Human-readable description of the abstract problem being evaluated.                                                                                                          |
| `instance`            | list of BenchmarkInstanceProperty | Yes      | The properties defining a benchmark instance. Each entry specifies the property name, an optional domain of valid values, and human-readable descriptions. See fields below. |
| `metrics`             | list of strings                   | No       | Canonical metric names for this logical benchmark.                                                                                                                           |
| `ranking`             | Ranking                           | No       | Defines how benchmark results are ordered on a leaderboard. See Ranking fields below.                                                                                        |
| `owner`               | string                            | No       | Team or individual responsible for maintaining this definition.                                                                                                              |

**BenchmarkInstanceProperty fields:**

| Field            | Type                             | Required | Description                                                                        |
| ---------------- | -------------------------------- | -------- | ---------------------------------------------------------------------------------- |
| `identifier`     | string                           | Yes      | Canonical property identifier.                                                     |
| `is_artifact`    | boolean                          | No       | Uses artifact files rather than a scalar value. Default: `false`.                  |
| `metadata`       | map                              | No       | Metadata about what this property represents. Can include e.g. description         |
| `propertyDomain` | ado.schema.domain.PropertyDomain | No       | Valid values for this property. If omitted, an open categorical domain is assumed. |

**Ranking fields:**

| Field    | Type            | Required | Description                                                               |
| -------- | --------------- | -------- | ------------------------------------------------------------------------- |
| `metric` | string          | Yes      | Identifier of the metric used for ranking. Must be in the `metrics` list. |
| `order`  | "asc" or "desc" | Yes      | Sort order: "asc" for lower-is-better, "desc" for higher-is-better.       |

<!-- markdownlint-enable line-length -->

### 2.3 Example: Graph Coloring

The logical benchmark definition lives under the `logicalBenchmark` key inside
`benchmarks/<benchmark-id>/benchmark.yaml`. Bindings live separately in
`experiments/<experiment-name>/bindings/` (see
[Section 3](#3-benchmark-binding)).

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
```

See
[the ado property domain documentation](https://ibm.github.io/ado/core-concepts/properties-and-domains/)
for more information about the types of domains that can be specified.

### 2.4 Benchmark Instances and Artifacts

A logical benchmark can define concrete benchmark instances (e.g. specific graphs,
routing networks, or datasets). Each instance lives in its own folder under
`instances/<instance-name>/` with an `instance.yaml` file and one or more
subfolders containing the actual artifact files for that instance.

#### Instance Directory Layout

```text
benchmarks/<benchmark-id>/instances/<instance-name>/
├── instance.yaml
└── <artifacts-subfolder>/        # name matches artifacts_location in instance.yaml
    ├── graph.dimacs
    └── graph.json
```

#### Instance Schema

Each `instance.yaml` defines a concrete benchmark instance. Instance properties
match the property identifiers defined under `instance:` in `benchmark.yaml`:

- **Scalar properties** (`is_artifact: false`, the default) are specified
  directly as scalar/primitive values.
- **Artifact properties** (`is_artifact: true`) are specified as a map with a
  mandatory `artifacts_location` key whose value is a subfolder name within the
  instance directory that contains the valid files for that property. The folder
  must exist inside the instance directory.

| Field           | Type                                                                                    | Required | Description                                                                                                                                                           |
| --------------- | --------------------------------------------------------------------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `identifier`    | string                                                                                  | **Yes**  | Unique identifier for this benchmark instance.                                                                                                                        |
| `description`   | string                                                                                  | No       | Human-readable description of this specific instance.                                                                                                                 |
| `<property_id>` | scalar (for scalar properties) or `{artifacts_location: str}` (for artifact properties) | No       | Value for a property defined in `benchmark.yaml`. Artifact properties must use the `{artifacts_location: <folder>}` map; folder must exist in the instance directory. |

#### Example Instance (`benchmarks/graph-coloring/instances/erdos_renyi_50_02/instance.yaml`)

```yaml
identifier: erdos_renyi_50_02
description: 50-node Erdos-Renyi graph with edge density 0.2

# Scalar instance properties
graph_family: erdos_renyi
num_vertices: 50
edge_density: 0.2

# Artifact instance property
graph:
    artifacts_location: my_graphs
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

Binding files live under `experiments/<experiment-name>/bindings/`. Each file
contains a top-level `bindings:` list; every entry in that list carries its own
`benchmarkIdentifier` field so a single file can bind one experiment to multiple
logical benchmarks.

**Per-entry fields:**

<!-- markdownlint-disable line-length -->

| Field                 | Type                | Required | Description                                                                                                                                                                                                                  |
| --------------------- | ------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `benchmarkIdentifier` | string              | **Yes**  | The `benchmarkIdentifier` of the logical benchmark this entry maps to.                                                                                                                                                       |
| `experiment`          | ExperimentReference | **Yes**  | The `ado` ExperimentReference object.                                                                                                                                                                                        |
| `targetMapping`       | string              | No       | Identifies the leaderboard target (row key) for this binding. Can be a custom string label, or the name of an experiment property whose value is resolved at query time. Defaults to the experiment identifier when omitted. |
| `metricMapping`       | list                | No       | Translates per-experiment metric names to the canonical metric names defined by the logical benchmark. Required when metric names differ across experiments targeting the same logical benchmark.                            |
| `instanceMapping`     | list                | No       | Remaps benchmark instance properties/parameters to experiment inputs.                                                                                                                                                        |
| `staticFilters`       | list                | No       | Sets static experiment properties to values implicit in the logical benchmark.                                                                                                                                               |

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

#### Instance mapping

The `instanceMapping` list maps benchmark instance properties/parameters to
experiment inputs. The artifact mapping is implicit — the experiment property
being bound against determines which artifact is used. Two types of entry are
possible:

- _field mapping_: A 1-to-1 mapping for a benchmark instance property.
    - Allows translating "WHERE logical_dim = X" to "WHERE experiment_param = X"
- _categorical value mapping_: 1-to-many mapping for the values of a categorical
  benchmark instance property.
    - Allows translating "WHERE logical_dim = CategoryA" to e.g. "WHERE
      exp_param_1 > X and exp_param_2 = y"

**Field mapping** — maps an experiment property to a benchmark instance
property.

```yaml
instanceMapping:
    - benchmark:
          identifier: "<benchmark-instance-property-name>"
      experiment:
          identifier: "<experiment-property-name>"
```

**Categorical value mapping** — maps one or more values of a categorical
benchmark instance property to a set of (experiment property:allowed value set)
pairs.

```yaml
instanceMapping:
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

Static filters pin known-constant property values to a binding without recording
them in experiment results or benchmark instances. Two directions are supported:

- **`experimentFilters`** _(benchmark → experiment)_: A property of the
  experiment is fixed to a value that is implicit in the logical benchmark.
  Every query against this experiment automatically adds
  `AND <experiment-property> = <value>`. For example, the experiment may expose
  a `mode` property with values `"debug"` and `"production"`, and the logical
  benchmark always requires `"production"`.

- **`benchmarkFilters`** _(experiment → benchmark)_: A benchmark instance
  property is fixed to a value that is implicit in the experiment. When building
  a leaderboard row the system injects `<benchmark-property> = <value>` without
  reading it from the experiment results. For example, a benchmark instance
  property `framework` is always `"pytorch"` for a particular experiment, so the
  binding asserts that rather than expecting a `framework` column in the
  results. Only benchmark instance properties that are **not** already covered
  by an `instanceMapping` entry may appear here — a property that is mapped from
  the experiment cannot also be statically asserted.

```yaml
staticFilters:
    experimentFilters:
        - property:
              identifier: "<experiment-property-name>"
          value: "<experiment-property-value>"
    benchmarkFilters:
        - property:
              identifier: "<benchmark-instance-property-name>"
          value: "<benchmark-property-value>"
```

Either sub-key may be omitted when only one direction is needed.

**Full example:**

```yaml
instanceMapping:
    - benchmark:
          identifier: num_vertices
      experiment:
          identifier: n_nodes
    - benchmark:
          identifier: edge_density
      experiment:
          identifier: density
staticFilters:
    experimentFilters:
        - property:
              identifier: graph_type
          value: erdos_renyi
    benchmarkFilters:
        - property:
              identifier: graph_family
          value: random_regular
```

### 3.3 Example: `guidellm-bench-deployment`

#### `benchmark.yaml`

The logical benchmark definition lives under
`benchmarks/llm-inference/benchmark.yaml`:

```yaml
logicalBenchmark:
    benchmarkIdentifier: llm_inference
    title: LLM Inference Performance
    description: >
        Evaluates LLM serving systems on throughput and latency under different
        traffic workloads. Instances are characterised by the workload category
        (traffic intensity and concurrency regime).
    instance:
        - identifier: workload
          metadata:
              description: >
                  Canonical workload category that captures traffic intensity
                  and concurrency regime.
          propertyDomain:
              variableType: CATEGORICAL_VARIABLE_TYPE
              values: [steady_state_heavy, poisson_bursty]
    metrics:
        - throughput_tokens_per_second
        - time_to_first_token_ms
    ranking:
        metric: throughput_tokens_per_second
        order: desc
```

#### `instance.yaml`

A concrete instance lives under
`benchmarks/llm-inference/instances/steady_state_heavy/instance.yaml`:

```yaml
identifier: steady_state_heavy
description: >
    Steady-state heavy workload: requests sent as fast as possible at high
    concurrency.

workload: steady_state_heavy
```

#### Binding

The binding lives in `experiments/guidellm/bindings/llm_inference_binding.yaml`.
Each entry in the `bindings` list carries a `benchmarkIdentifier` to identify
which logical benchmark it maps to:

```yaml
bindings:
    - benchmarkIdentifier: llm_inference
      experiment:
          actuatorIdentifier: vllm_performance
          experimentIdentifier: guidellm-bench-deployment
          experimentVersion: 1.1.0
      instanceMapping:
          - categoricalValue:
                property:
                    identifier: workload
                value: steady_state_heavy
            predicate:
                - identifier: request_rate # -1 = send as fast as possible
                  propertyDomain:
                      values: [-1]
                - identifier: max_concurrency
                  propertyDomain:
                      domainRange: [200, 500]
                      variableType: CONTINUOUS_VARIABLE_TYPE
          - categoricalValue:
                property:
                    identifier: workload
                value: poisson_bursty
            predicate:
                - identifier: request_rate
                  propertyDomain:
                      domainRange: [1, 20]
                      variableType: CONTINUOUS_VARIABLE_TYPE
                - identifier: max_concurrency
                  propertyDomain:
                      domainRange: [1, 50]
                      variableType: CONTINUOUS_VARIABLE_TYPE
      metricMapping:
          - benchmark:
                identifier: throughput_tokens_per_second
            experiment:
                identifier: output_throughput
          - benchmark:
                identifier: time_to_first_token_ms
            experiment:
                identifier: mean_ttft_ms
      staticFilters:
          experimentFilters:
              # The experiment's 'dataset' param controls synthetic prompt generation;
              # pinned to 'random' because this binding does not vary the prompt dataset.
              - property:
                    identifier: dataset
                value: random
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
llm_inference-guidellm-bench-deployment-workload=steady_state_heavy
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
3. Rename result dataframe columns using `instanceMapping` and `metricMapping`
   (metric names).
4. Merge the resulting dataframes. All share the same canonical column names.

### 4.4 Cross-Experiment Aggregation Example

A second experiment, `vllm-bench-deployment`, targets the same logical benchmark
in [Section 3.3](#33-example-guidellm-bench-deployment). Both experiments share
the same parameter names, so no `metricMapping` is needed and the
`instanceMapping` uses the same predicate identifiers — only the concurrency
ranges differ, reflecting each tool's calibration of what constitutes
"steady-state heavy":

```yaml
bindings:
    - experiment:
          actuatorIdentifier: vllm_performance
          experimentIdentifier: vllm-bench-deployment
          experimentVersion: 1.1.0
      instanceMapping:
          - categoricalValue:
                property:
                    identifier: workload
                value: steady_state_heavy
            predicate:
                - identifier: request_rate
                  propertyDomain:
                      values: [-1]
                - identifier: max_concurrency
                  propertyDomain:
                      domainRange: [100, 500]
                      variableType: CONTINUOUS_VARIABLE_TYPE
          - categoricalValue:
                property:
                    identifier: workload
                value: poisson_bursty
            predicate:
                - identifier: request_rate
                  propertyDomain:
                      domainRange: [1, 20]
                      variableType: CONTINUOUS_VARIABLE_TYPE
                - identifier: max_concurrency
                  propertyDomain:
                      domainRange: [1, 50]
                      variableType: CONTINUOUS_VARIABLE_TYPE
      staticFilters:
          experimentFilters:
              - property:
                    identifier: dataset
                value: random
```

A leaderboard query for
`logical_benchmark=llm_inference, workload=steady_state_heavy` will:

1. Fetch the bindings for `guidellm-bench-deployment` and
   `vllm-bench-deployment` (all experiments with a binding to `llm_inference`).
2. Query `guidellm-bench-deployment` results where `dataset=random` AND
   `request_rate=-1` AND `max_concurrency` between 200 and 500. The
   `output_throughput` and `mean_ttft_ms` columns are renamed to
   `throughput_tokens_per_second` and `time_to_first_token_ms`.
3. Query `vllm-bench-deployment` results where `dataset=random` AND
   `request_rate=-1` AND `max_concurrency` between 100 and 500. No metric
   renaming is needed (output column names are identical).
4. Merge both dataframes. Both now share the same canonical column names and can
   be displayed in a single leaderboard table keyed by model.

---

## 5. Governance

### 5.1 Logical Benchmark Location & Ownership

Logical benchmark definition files are stored under the `benchmarks/` directory
at the top level of the Algorithm Nexus repository. Each logical benchmark has
its own subdirectory named after its `benchmarkIdentifier`, containing a
`benchmark.yaml` file that holds the `logicalBenchmark` definition:

```text
benchmarks/
└── <benchmark-id>/
    ├── benchmark.yaml      # logicalBenchmark definition
    ├── README.md           # optional: full problem statement and context
    └── instances/          # optional concrete problem instances
        └── <instance-name>/
            ├── instance.yaml
            └── artifacts/
```

A `README.md` alongside `benchmark.yaml` is encouraged to provide a full
description of the problem. For example to give the mathematical formulation,
cite references, or explain the instance structure beyond what the `description`
field in `benchmark.yaml` allows.

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

[Benchmark Experiments and Submissions](./benchmark_experiments_and_submissions.md)
establishes that the benchmark target is implicit from the enclosing model
definition for model-level benchmark submissions. The binding does not need to
name the target property explicitly — the target identity is determined by the
enclosing model or algorithm definition that owns the benchmark submission.

### 7.2 Benchmark Package Registration and Submissions

Benchmark experiment packages are registered in
`experiments/<name>/experiment_package.yaml` (not in `nexus.yaml`). Benchmark
submissions live under `experiments/<name>/submissions/<submission>/space.yaml`.
The benchmark binding is an additional artifact that sits alongside these files
in `experiments/<name>/bindings/` and does not alter their structure.
