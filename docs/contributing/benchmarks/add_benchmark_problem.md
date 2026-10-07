<!--
Copyright IBM Corporation 2026
SPDX-License-Identifier: Apache-2.0
-->

# How to add a benchmark problem and instance

This guide shows you how to register a benchmark problem in Algorithm Nexus and
add a concrete instance of that problem.

A **benchmark problem** (also called a _logical benchmark_) is the abstract task
you want algorithms or models compared on. A **benchmark instance** is one
concrete realisation of that task — a specific graph, dataset, workload, or
other input.

The steps below add a graph-coloring problem and one instance of it. After that
walk-through, [Alternatives](#alternatives) covers artifact files, extra
instances, and other property domains.

## Prerequisites

Work from a local checkout of your Algorithm Nexus fork with the CLI extra
installed:

```bash
cd algorithm-nexus
uv sync --group dev --extra cli
git checkout -b add-graph-coloring-benchmark
```

## 1. Create the problem definition

Create the problem folder and write `benchmark.yaml`. This file names the
problem and declares the instance properties and metrics that every instance —
and later experiment binding — will share.

```bash
mkdir -p benchmarks/graph_coloring
```

Create `benchmarks/graph_coloring/benchmark.yaml`:

```yaml
benchmarkIdentifier: graph_coloring
title: Graph Coloring
description: >
    Evaluates graph-coloring algorithms on their ability to produce valid
    k-colorings with a small chromatic number. Instances span random
    Erdős–Rényi graphs and structured benchmark graphs at varying densities.
problemProperties:
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
    - identifier: num_colors_used
    - identifier: is_valid_coloring
    - identifier: elapsed_ms
ranking:
    metric: num_colors_used
    order: asc
owner: "@graph-team"
```

The `problemProperties` list is the vocabulary for every instance of this problem.
`metrics` and `ranking` are the vocabulary for results and leaderboard order.

The full field list is in
[Logical Benchmarks and Instances](../../design/benchmarking/logical_benchmarks_and_instances.md#2-logical-benchmark-definition).

## 2. Add an instance

Create one instance folder and write `instance.yaml`. Use the property
identifiers from the problem definition, and give each a concrete value.

```bash
mkdir -p benchmarks/graph_coloring/instances/erdos_renyi_50_02
```

Create `benchmarks/graph_coloring/instances/erdos_renyi_50_02/instance.yaml`:

```yaml
instanceIdentifier: erdos_renyi_50_02
benchmarkIdentifier: graph_coloring
description: 50-node Erdos-Renyi graph with edge density 0.2
problemPropertyValues:
    - property:
          identifier: graph_family
      value: erdos_renyi
    - property:
          identifier: num_vertices
      value: 50
    - property:
          identifier: edge_density
      value: 0.2
```

The full field list is in
[Logical Benchmarks and Instances](../../design/benchmarking/logical_benchmarks_and_instances.md#3-benchmark-instance-definition).

You now have:

```text
benchmarks/graph_coloring/
├── benchmark.yaml
└── instances/
    └── erdos_renyi_50_02/
        └── instance.yaml
```

## 3. Validate

```bash
uv run nexus validate logical-benchmarks
```

A successful run lists the problem folder with status `success`. The problem and
instance are ready to commit.

## 4. Open a pull request

```bash
git add benchmarks/graph_coloring
git commit -s -m "feat(benchmark): Add graph_coloring problem and instance"
git push origin add-graph-coloring-benchmark
```

Open a pull request from your fork to the Algorithm Nexus main branch.

To register an experiment that evaluates this problem, continue with
[How to add a benchmark experiment](./add_benchmark_experiment.md). To bind that
experiment to this problem, continue with
[How to bind an experiment to a benchmark instance](./add_instance_binding.md). To apply an
experiment to this instance, continue with
[How to add a benchmark submission](./add_benchmark_submission.md).

---

## Alternatives

### Add an instance that includes artifact files

To ship input files with an instance (graphs, datasets, prompts), create a
subfolder inside the instance directory that holds those files, then declare
`instanceArtifacts` in `instance.yaml` pointing to that subfolder. Artifacts
are defined on the instance itself and do not need to be listed in the
benchmark's `problemProperties`.

In the instance directory, create the subfolder and the files, then reference it
from `instance.yaml`:

```bash
mkdir -p benchmarks/graph_coloring/instances/erdos_renyi_50_02/graph_files
```

```yaml
instanceIdentifier: erdos_renyi_50_02
benchmarkIdentifier: graph_coloring
description: 50-node Erdos-Renyi graph with edge density 0.2
problemPropertyValues:
    - property:
          identifier: graph_family
      value: erdos_renyi
    - property:
          identifier: num_vertices
      value: 50
    - property:
          identifier: edge_density
      value: 0.2
instanceArtifacts:
    - property:
          identifier: graph
      artifactsLocation: graph_files
```

The instance directory then looks like this:

```text
benchmarks/graph_coloring/instances/erdos_renyi_50_02/
├── instance.yaml
└── graph_files/
    ├── graph.dimacs
    └── graph.json
```

### Add an instance to an existing problem

To add another instance of a problem that is already registered, create a new
folder under that problem's `instances/` directory and write an `instance.yaml`
that uses the same property identifiers.

```bash
mkdir -p benchmarks/<problem-id>/instances/<instance-name>
```

Then validate as in [step 3](#3-validate).

### Describe the problem in a README

To give a fuller problem statement — formulation, references, or instance
structure — add `benchmarks/<problem-id>/README.md` next to `benchmark.yaml`.

### Use other property domains

The walk-through uses a mix of categorical, discrete, and continuous properties.
To constrain a continuous property to a range, set `domainRange`:

```yaml
propertyDomain:
    variableType: CONTINUOUS_VARIABLE_TYPE
    domainRange: [0, 1]
```

To leave a categorical property open, omit `propertyDomain`. See the
[ado property domain documentation](https://ibm.github.io/ado/core-concepts/properties-and-domains/)
and
[section 2 of Logical Benchmarks and Instances](../../design/benchmarking/logical_benchmarks_and_instances.md#2-logical-benchmark-definition).

### Start from the repository templates

To begin from placeholders instead of the graph-coloring example, copy the
templates and replace every `<...>` marker:

```bash
mkdir -p benchmarks/<problem-id>
cp templates/logical-benchmark/benchmark.yaml \
    benchmarks/<problem-id>/benchmark.yaml
cp -R templates/logical-benchmark/instances \
    benchmarks/<problem-id>/instances
```

Rename `instances/instance-name/` to your instance id, then continue from
[step 3](#3-validate).

### Validate a single problem folder

To validate one problem:

```bash
uv run nexus validate logical-benchmarks --file benchmarks/graph_coloring
```

## See also

- [Logical Benchmarks and Instances](../../design/benchmarking/logical_benchmarks_and_instances.md)
  — schema, bindings, and how results are aggregated
- [How to add a benchmark experiment](./add_benchmark_experiment.md)
- [How to bind an experiment to a benchmark instance](./add_instance_binding.md)
- [How to add a benchmark submission](./add_benchmark_submission.md)
- [`nexus validate logical-benchmarks`](../../getting-started/cli-reference.md#nexus-validate-logical-benchmarks)
