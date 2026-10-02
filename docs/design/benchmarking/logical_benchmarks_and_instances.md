<!--
Copyright IBM Corporation 2026
SPDX-License-Identifier: Apache-2.0
-->

# Logical Benchmarks and Instances

## Executive Summary

This document specifies **logical benchmarks** and **benchmark instances**, and
how an experiment binds to a logical benchmark so results from diverse
experiments can be aggregated in a standardized, domain-agnostic way.

To register a problem and instance, see
[How to add a benchmark problem and instance](../../contributing/benchmarks/add_benchmark_problem.md).
To bind an experiment to a benchmark instance, see
[How to bind an experiment to a benchmark instance](../../contributing/benchmarks/add_instance_binding.md).

The design rests on three complementary abstractions:

1. **Logical Benchmark Definition** — a declarative description of an abstract
benchmark problem: what properties define it and what values those
properties can take. 

2. **Benchmark Instance Definition** — a concrete instantiation of a logical
   benchmark problem. Defines specific values for the problem properties and optionally provides instance specific files generated based on those property values. 

3. **Benchmark Instance Binding** — metadata that maps an `ado` experiment's
   internal properties and metrics to the properties and metric names of a
   benchmark instance. This tells the system how to extract and label the
   relevant results from that experiment's data.

Together, these abstractions allow the benchmarking system to remain agnostic to
domain-specific concepts. All domain knowledge is expressed by the logical
benchmark, benchmark instance and benchmark experiment authors; the system only
needs to read the metadata and apply it.

### Requirements to Design Mapping

| Requirement | Design interpretation                                                                                                     |
| ----------- | ------------------------------------------------------------------------------------------------------------------------- |
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

| Challenge                                       | Description                                                                                                                                                                                                                                                                                                                                     | Design Requirement                                                                                 |
| ----------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| **Heterogeneous Tooling for Homogeneous Tasks** | Different experiments may evaluate the same logical problem. For example, both `vllm-bench` and `guide-llm` measure inference-serving performance, but the system has no way to know they can address the same logical benchmark.                                                                                                               | The system must recognize that disparate experiments can address the same logical benchmark.       |
| **Ambiguous and Domain-Specific Properties**    | Benchmarking domains are too diverse to share a fixed schema. A synthetic math logical benchmark has no "dataset" column; a quantum max-cut logical benchmark is characterized by `graph_type` and `node_count`.                                                                                                                                | The system must support dynamic, per-logical-benchmark, properties.                                |
| **Benchmark Instance Property Fragmentation**   | Defining a benchmark instance often involves a matrix of runtime properties. If results are differentiated by raw property values, results from minor variations (`concurrency=100` vs `concurrency=105`) can never be aggregated. Further, the properties required to address the same logical benchmark with different experiments may differ | The design must allow related property combinations to be collapsed into a single canonical value. |

<!-- markdownlint-enable line-length -->

---

## 2. Logical Benchmark Definition

### 2.1 Concept

A **logical benchmark** is an abstract, reusable definition of a problem class
or evaluation task (the benchmark problem). It defines:

- a unique identifier
- the **problem properties** that are used for defining an instance of the
  problem. When creating a benchmark instance, these properties are used for
  defining the complexity or size of the problem to be benchmarked.
- the canonical **metric names** that results should be reported under

### 2.2 Schema

**Top-level fields:**

<!-- markdownlint-disable line-length -->

| Field               | Type             | Required | Description                                                                                                                     |
| ------------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `identifier`        | string           | Yes      | Unique identifier for this benchmark.                                                                                           |
| `title`             | string           | No       | Short human-readable display name for this logical benchmark.                                                                   |
| `description`       | string           | Yes      | Human-readable description of the abstract problem being evaluated.                                                             |
| `problemProperties` | list of Property | Yes      | The properties defining a benchmark problem. Each entry specifies the property name and an optional human-readable description. |
| `metrics`           | list of Property | No       | Canonical metric names for this logical. Each entry specifies the metric name and an optional human-readable description.       |
| `ranking`           | Ranking          | No       | Defines how benchmark results are ordered on a leaderboard. See Ranking fields below.                                           |
| `owner`             | string           | No       | Team or individual responsible for maintaining this definition.                                                                 |

**Ranking fields:**

| Field    | Type            | Required | Description                                                               |
| -------- | --------------- | -------- | ------------------------------------------------------------------------- |
| `metric` | string          | Yes      | Identifier of the metric used for ranking. Must be in the `metrics` list. |
| `order`  | "asc" or "desc" | Yes      | Sort order: "asc" for lower-is-better, "desc" for higher-is-better.       |

<!-- markdownlint-enable line-length -->

### 2.3 Example

The logical benchmark definition lives under the `logicalBenchmark` key inside
`benchmarks/<benchmark-id>/benchmark.yaml`. Bindings live separately in
`experiments/<experiment-name>/bindings/` (see
[Section 4](#4-benchmark-instance-binding)).

```yaml
identifier: graph_coloring
title: Graph Coloring
description: >
    Evaluates graph-coloring algorithms on their ability to produce valid
    k-colorings with a small chromatic number. Instances span random
    Erdős–Rényi graphs and structured benchmark graphs at varying densities.
problemProperties:
    - identifier: graph_family
        metadata:
            description: Graph family (erdos_renyi, planar, random_regular).
    - identifier: num_vertices
        metadata:
            description: Number of vertices in the graph.
    - identifier: edge_density
        metadata:
            description: Edge probability / density parameter.
metrics:
    - identifier: num_colors_used
    - identifier: is_valid_coloring
    - identifier: elapsed_ms
ranking:
    metric: num_colors_used
    order: asc
```

See
[the ado property domain documentation](https://ibm.github.io/ado/core-concepts/properties-and-domains/)
for more information about the types of domains that can be specified.

---

## 3. Benchmark Instance Definition

### 3.1 Concept

You can define concrete **benchmark instances**  for a logical benchmark (e.g. specific
circuit compilation problem, portfolio optimization problem, or genai inference workload). Each instance lives in its own folder
under `instances/<instance-name>/` with an `instance.yaml` file and one or more
subfolders containing the actual artifact files for that instance.

### 3.2 Instance Artifacts

An **instance artifact** is a file that is derived from the instance's problem
properties and can be fed directly to algorithms as input. Rather than having
each algorithm re-derive the same input representation from raw property values,
the artifact is pre-generated once and stored alongside the instance.

For example, for a graph-coloring instance the problem properties might describe
a graph in terms of its family, number of vertices, and edge density. A
pre-processing step can consume those properties, generate the actual graph
using a tool such as an MPS converter, and write the resulting graph file (e.g.
`graph.dimacs` or `graph.json`) to an artifact folder. Benchmark experiments can take one of these files as input rather than having to reconstruct the graph themselves.

### 3.3 Directory Layout

```text
benchmarks/<benchmark-id>/instances/<instance-name>/
├── instance.yaml
└── <artifacts-subfolder>/        # name matches artifactsLocation in instance.yaml
    ├── graph.dimacs
    └── graph.json
```

### 3.4 Schema

Each `instance.yaml` defines a concrete benchmark instance. Problem properties
match the problem property identifiers defined under `problemProperties:` in
`benchmark.yaml`, while `instanceArtifacts` identifies the artifacts that have been created for 
this instance. Artifacts are specified as a map with a mandatory
`artifactsLocation` key whose value is a subfolder name within the instance
directory that contains the valid files for that property. The folder must exist
inside the instance directory.

| Field                | Type                                         | Required | Description                                                    |
| -------------------- | -------------------------------------------- | -------- | -------------------------------------------------------------- |
| `identifier`         | string                                       | **Yes**  | Unique identifier for this benchmark instance.                 |
| `benchmarkReference` | string                                       | **Yes**  | The `identifier` of the benchmark this instance maps to.       |
| `description`        | string                                       | No       | Human-readable description of this specific instance.          |
| `problemProperties`  | list of PropertyValue                        | No       | Values for all problem properties defined in `benchmark.yaml`. |
| `instanceArtifacts`  | list of maps \{<artifact_name\>: <folder\>\} | No       | Locations of all artifacts available for this instance.        |

### 3.5 Example

The following is an example instance definition at
`benchmarks/graph-coloring/instances/erdos_renyi_50_02/instance.yaml`:

```yaml
identifier: erdos_renyi_50_02
benchmarkReference: graph_coloring
description: 50-node Erdos-Renyi graph with edge density 0.2

# Problem properties
problemProperties:
    - property:
            identifier: graph_family
        value: erdos_renyi
    - property:
            identifier: num_vertices
        value: 50
    - property:
            identifier: edge_density
        value: 0.2

# Artifact instance property
instanceArtifacts:
    - graph:
            artifactsLocation: my_graphs
```

---

## 4. Benchmark Instance Binding

### 4.1 Concept

A benchmark instance binding defines how a given experiment can execute a benchmark instance.
property names and values to one or more of the available benchmrk instances.
This is called an **instance binding**.

An instance binding serves two purposes:

1. **Declaration** — it defines the benchmark instance an experiment maps to

2. **Mapping** — it describes how 
     - the experiment's input property names map to the problemProperties and/or instanceArtifcats of the benchmark instance
      - the experiments output property names correspond to the metric names defined by
the logical benchmark. 

The purpose of this approach is provide flexibility in what information
 benchmark experiment need to execute a benchmark instance. 
As an example, one experiment
might have been designed solely for solving one specific instance problem, and
therefore it requires no input parameters. While others might have a more
generic implementation and require specific input data (an instance artefact, or the problem property values) to execute that specific instance.

### 4.2 Schema

Binding files live under `experiments/<experiment-name>/bindings/`. Each file
contains a `bindings` list, where each entry is one instance binding.

**Per-entry fields:**

<!-- markdownlint-disable line-length -->

| Field                     | Type                                  | Required | Description                                                                                                                                                                                                                                                                                                                                                        |
| ------------------------- | ------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `identifier`              | string                                | **Yes**  | The unique identifier of this binding.                                                                                                                                                                                                                                                                                                                             |
| `instanceReference`       | string                                | **Yes**  | It is formed as `benchmarkIdentifier/instanceIdentifier` for the instance it maps to.                                                                                                                                                                                                                                                                                      |
| `experiment`              | ExperimentReference                   | **Yes**  | The `ado` ExperimentReference object.                                                                                                                                                                                                                                                                                                                              |
| `targetMapping`           | string                                | No       | Identifies the leaderboard target (row key) for this binding. Can be a custom string label, or the name of an experiment property whose value is resolved at query time. Defaults to the experiment identifier when omitted.                                                                                                                                       |
| `metricMapping`           | list of **metric mapping**            | No       | Translates per-experiment metric names to the canonical metric names defined by the logical benchmark. Required when metric names differ across experiments targeting the same logical.benchmark.                                                                                                                                                                  |
| `problemPropertyMapping`  | list of **problem property mapping**  | No       | Remaps instance problem properties to experiment input properties.                                                                                                                                                                                                                                                                                                 |
| `instanceArtifactMapping` | list of **instance artifact mapping** | No       | Remaps benchmark instance artifact properties to experiment input properties. These mappings should be present even if the experiment and instance properties have the same name. Every property omitted here is considered not to be a property of the experiment and will not be used for resolving the mapping between experiment runs and benchmark instances. |
| `staticFilters`           | list of PropertyValue                 | No       | Sets static experiment properties to values implicit in the instance.                                                                                                                                                                                                                                                                                              |

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

#### Problem property mapping

The `problemPropertyMapping` list maps problem properties/parameters from the
benchmark instance to experiment inputs. 
types of entry are possible:

- _field mapping_: A 1-to-1 mapping for a benchmark instance property.
    - Allows translating "WHERE problem_property_Z = X" to "WHERE experiment_param = X"
- _categorical value mapping_: 1-to-many mapping for the values of a categorical
  benchmark instance property.
    - Allows translating "WHERE logical_dim = CategoryA" to e.g. "WHERE
      exp_param_1 > X and exp_param_2 = y"

Only benchmark instance problem property or instance artifacts that map to an experiment input need to be included here. The others can be ignored.  
used for creating a [routing key](#62-routing-key).

##### Field mapping

Maps an experiment property to a benchmark instance problem property.

```yaml
problemPropertyMapping:
    - instance:
          identifier: "<benchmark-instance-problem-property-name>"
      experiment:
          identifier: "<experiment-property-name>"
```

##### Categorical value mapping

Maps one or more values of a categorical benchmark instance problem property to
a set of (experiment property:allowed value set) pairs.

```yaml
problemPropertyMapping:
    - categoricalValue:
          property:
              identifier: "<benchmark-instance-problem-property-name>"
          value: "<categorical-value-from-benchmark-domain>"
      predicate:
          - identifier: "<experiment-property-name>"
            propertyDomain: <PropertyDomain>
          - ...
```

#### Instance artifact mapping

Maps an experiment property to an instance artifact. One type of entry is
possible:

- _field mapping_: A 1-to-1 mapping for a benchmark instance property.
    - Allows translating "WHERE logical_dim = X" to "WHERE experiment_param = X"
- _static value mapping_: An instance artifact property is fixed to a value that
  is implicit in the experiment. The static value used must be the name of one
  the files contained in the `artifact_location` folder for that specific
  artifact property.

```yaml
instanceArtifactMapping:
    - fieldMapping:
          instance:
              identifier: "<benchmark-instance-artifact-property-name>"
          experiment:
              identifier: "<experiment-property-name>"
    - staticMapping:
          property:
              identifier: "<benchmark-instance-artifact-property-name>"
          value: "value"
```

Every artifact from the instance with no mapping is considered not to have a
counterpart input property in the experiment, and will not be used for creating
a [routing key](#62-routing-key).

#### Static filters

Static filters pin known-constant property values to a binding without recording
them in experiment results or benchmark instances.

A property of the experiment is fixed to a value that is implicit in the
instance. Every query against this experiment automatically adds
`AND <experiment-property> = <value>`. For example, the experiment may expose a
`mode` property with values `"debug"` and `"production"`, and the instance
always requires `"production"`.

```yaml
staticFilters:
    - property:
          identifier: "<experiment-property-name>"
      value: "<experiment-property-value>"
```

### 4.3 Examples

#### Artifact-Only Binding Example

This experiment only takes the artifact as input and does not have input
parameters that match the problem properties.

```yaml
identifier: coloring_rlx
instanceReference: gaph_coloring/erdos_renyi_50_02
experiment:
    actuatorIdentifier: custom_experiments
    experimentIdentifier: rlx_coloring
    experimentVersion: 1.0.0

instanceArtifactMapping:
    - fieldMapping:
          instance:
              identifier: graph
          experiment:
              identifier: input_graph
```

#### Properties and Static Artifact Binding Example

This experiment instead requires all the problem properties to be specified as
inputs to the experiment, while it does not use any of the available artifacts.

```yaml
identifier: coloring_rlx
instanceReference: gaph_coloring/erdos_renyi_50_02
experiment:
    actuatorIdentifier: custom_experiments
    experimentIdentifier: rlx_coloring
    experimentVersion: 1.0.1
problemPropertyMapping:
    - instance:
        identifier: graph_family
    experiment:
        identifier: family
    - instance:
        identifier: num_vertices
    experiment:
        identifier: n_vertices
    - instance:
        identifier: edge_density
    experiment:
        identifier: density
instanceArtifactMapping:
    - staticMapping:
        property:
            identifier: graph
        value: graph.json
```

---

## 5. Full End-to-End Example

This section traces a complete example for the `llm_inference` benchmark,
showing how a logical benchmark, an instance, and an experiment binding fit
together for evaluating LLM inference performance with
`guidellm-bench-deployment`.

### 5.1 Logical benchmark definition

The logical benchmark definition lives under
`benchmarks/llm-inference/benchmark.yaml`:

```yaml
identifier: llm_inference
title: LLM Inference Performance
description: >
    Evaluates LLM serving systems on throughput and latency under different
    traffic workloads. Instances are characterised by the workload category
    (traffic intensity and concurrency regime).
problemProperties:
    - identifier: workload
        metadata:
            description: >
                Canonical workload category that captures traffic intensity
                and concurrency regime.
metrics:
    - identifier: throughput_tokens_per_second
        metadata:
            description: >
                Total output tokens generated per second across all concurrent
                requests.
    - identifier: time_to_first_token_ms
        metadata:
            description: >
                Time in milliseconds from request submission to the first
                output token being produced.
ranking:
    metric: throughput_tokens_per_second
    order: desc
```

### 5.2 Benchmark instance definition

A concrete instance lives under
`benchmarks/llm-inference/instances/steady_state_heavy/instance.yaml`:

```yaml
identifier: steady_state_heavy
benchmarkReference: llm_inference
description: >
    Steady-state heavy workload: requests sent as fast as possible at high
    concurrency.

problemProperties:
    - property:
            identifier: workload
        value: steady_state_heavy
```

### 5.3 Benchmark instance binding

The binding lives in `experiments/guidellm/bindings/llm_inference_binding.yaml`.
Each entry in the `bindings` list carries a `instanceIdentifier` and
`benchmarkIdentifier` to identify which instance of which logical benchmark:

```yaml
identifier: guidellm_steady_state_heavy
instanceReference: llm_inference/steady_state_heavy
experiment:
    actuatorIdentifier: vllm_performance
    experimentIdentifier: guidellm-bench-deployment
    experimentVersion: 1.1.0
problemPropertyMapping:
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
    # The experiment's 'dataset' param controls synthetic prompt generation;
    # pinned to 'random' because this binding does not vary the prompt dataset.
    - property:
        identifier: dataset
    value: random
```

---

## 6. Leaderboards and Routing

### 6.1 How the Artifacts Combine

With a logical benchmark definition, benchmark instances, and one or more
experiment instance bindings in place, the system can answer aggregation queries
without any domain-specific logic:

- The instance defines **what properties** exist and **what values** they can
  take.
- Each instance binding defines **how to query** one experiment's results for
  those properties and **how to label** them consistently.

A leaderboard is simply a query over a subset of the logical benchmark's
properties. Omitting a property aggregates across all its values; specifying one
filters to it.

### 6.2 Routing Key

A deterministic routing key can be constructed from a result and the instance
binding:

```text
{experimentIdentifier}-{property1=value}-{property2=value}
```

Properties are sorted alphabetically. For example:

```text
llm_inference-guidellm-bench-deployment-workload=steady_state_heavy
```

The routing key identifies a specific leaderboard slot. Leaderboard queries can
match on any prefix or subset of these components.

### 6.3 Dynamic Property Resolution

Property resolution — mapping from raw experiment properties to canonical
benchmark properties — is performed **at query time**. This means only one
database of raw results needs to be maintained.

The leaderboard population process for a given query:

1. Identify all experiments with a binding to an instance of the queried
   `logicalBenchmark`.
2. For each experiment, use its instance binding to construct a query against
   the result store (ado `samplestore`) (using the experiment's own internal
   property names as the filter criteria).
3. Rename result dataframe columns using `problemPropertyMapping`,
   `artifactMapping` and `metricMapping` (metric names).
4. Merge the resulting dataframes. All share the same canonical column names.

### 6.4 Cross-Experiment Aggregation Example

A second experiment, `vllm-bench-deployment`, targets the same logical benchmark
in [Section 5](#5-full-end-to-end-example). Both experiments share the same
parameter names, so no `metricMapping` is needed and the
`problemPropertyMapping` uses the same predicate identifiers — only the
concurrency ranges differ, reflecting each tool's calibration of what
constitutes "steady-state heavy":

```yaml
identifier: guidellm_steady_state_heavy
instanceReference: llm_inference/steady_state_heavy
experiment:
    actuatorIdentifier: vllm_performance
    experimentIdentifier: vllm-bench-deployment
    experimentVersion: 1.1.0
problemPropertyMapping:
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
staticFilters:
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

## 7. Instance Binding Versioning

An instance binding may only change if:

- The experiment property names or values used in `problemPropertyMapping`,
  `instanceArtifactMapping`, or `staticFilters` change
    - This should result in a new experiment major version and a new binding
    - The binding for the previous experiment major version can be kept
- The logical benchmark `problemProperties` or their values change
    - If the original logical benchmark parameters/values and mappings are now
      invalid, the existing logical benchmark and its bindings can be updated in
      place
    - If the original logical benchmark parameters/values and mappings are still
      valid, a new logical benchmark should be created
- Additional experiment properties are added that must be set to **non-default
  values** AND only the experiment minor version changes
    - The binding must be changed — different sets of experiment data will be
      aggregated under `problemPropertyMapping` or `staticFilters`
    - Note: This applies to **non-default values** only — by ado versioning
      convention a minor version change means that the new parameters with
      default values measure output metrics the same way as the previous
      experiment with the same major version but without those parameters

---

## 8. Relationship to Existing Benchmark Design

### 8.1 Implicit Benchmark Target

[Benchmark Experiments and Submissions](./benchmark_experiments_and_submissions.md)
establishes that the benchmark target is implicit from the enclosing model
definition for model-level benchmark submissions. The binding does not need to
name the target property explicitly — the target identity is determined by the
enclosing model or algorithm definition that owns the benchmark submission.

### 8.2 Benchmark Package Registration and Submissions

Benchmark experiment packages are registered in
`experiments/<name>/experiment_package.yaml`. Benchmark submissions live under
`experiments/<name>/submissions/<submission>/space.yaml`. Instance bindings live
under `experiments/<name>/bindings/` and do not alter the structure of
experiment packages or submissions. Each binding file contains one binding whose
entries reference the target logical benchmark and instance via
`instanceReference` field, and describe the mapping via
`problemPropertyMapping`, `metricMapping`, `instanceArtifactMapping`, and
`staticFilters` as defined in [Section 4.2](#42-schema).
