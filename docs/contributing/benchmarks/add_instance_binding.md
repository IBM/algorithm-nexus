<!--
Copyright IBM Corporation 2026
SPDX-License-Identifier: Apache-2.0
-->

# How to bind an experiment to a problem instance

This guide shows you how to register a benchmark instance binding in Algorithm
Nexus.

A **benchmark instance binding** is used to identify the runs of an experiment
that are on that particular instance. See
[Routing Query](../../design/benchmarking/logical_benchmarks_and_instances.md#62-routing-query)
for the details. It also translates the experiment output property/metric names
to the canonical metric names defined by the logical benchmark.

The steps below bind `rlx_coloring` to the `erdos_renyi_50_02` instance of the
`graph_coloring` benchmark. After that walk-through,
[Alternatives](#alternatives) covers matching names, categorical mappings, and
static filters.

## Prerequisites

Work from a local checkout of your Algorithm Nexus fork with the CLI extra
installed:

```bash
cd algorithm-nexus
uv sync --group dev --extra cli
git checkout -b add-rlx-coloring-binding
```

The `graph_coloring` benchmark and its `erdos_renyi_50_02` instance are already
registered. To add them, see
[How to add a benchmark problem and instance](./add_benchmark_problem.md).

The `rlx_coloring` experiment is already registered. To add it, see
[How to add a benchmark experiment](./add_benchmark_experiment.md).

## 1. Create the binding

Create the bindings folder and write a YAML file that names the benchmark
instance, the experiment, and the field mappings.

```bash
mkdir -p experiments/rlx_coloring/bindings
```

Create `experiments/rlx_coloring/bindings/graph_coloring_binding.yaml`:

```yaml
instanceBindingIdentifier: coloring_rlx
instanceReference: erdos_renyi_50_02/graph_coloring
experiment:
    actuatorIdentifier: custom_experiments
    experimentIdentifier: rlx_coloring
    experimentVersion: 1.0.0
targetMapping:
    static: rlx # The target (algorithm) of this experiment is always "rlx".
problemPropertyMapping:
    - instance: # benchmark's num_vertices is experiment's n_nodes parameter
          identifier: num_vertices
      experiment:
          identifier: n_nodes
    - instance:
          identifier: edge_density
      experiment:
          identifier: density
    - instance:
          identifier: graph_family
      experiment:
          identifier: graph_type
metricMapping:
    - benchmark: # the benchmark's num_colors_used output is given by the experiment's colors output
          identifier: num_colors_used
      experiment:
          identifier: colors
    - benchmark:
          identifier: elapsed_ms
      experiment:
          identifier: runtime_ms
```

`problemPropertyMapping` pairs a benchmark instance problem property with a
corresponding experiment input property. `metricMapping` does the same for
result columns. `targetMapping` is a custom string label or the name of an
experiment property whose value is resolved at query time; it defaults to the
experiment identifier when omitted.

The full field list is in
[Logical Benchmarks and Instances](../../design/benchmarking/logical_benchmarks_and_instances.md#4-benchmark-instance-binding).

You now have:

```text
experiments/rlx_coloring/
├── experiment_package.yaml
└── bindings/
    └── graph_coloring_binding.yaml
```

## 2. Validate

```bash
uv run nexus validate experiments --experiment rlx_coloring
```

A successful run lists the experiment with status `success`. The binding is
ready to commit.

## 3. Open a pull request

```bash
git add experiments/rlx_coloring/bindings
git commit -s -m "feat(benchmark): Bind rlx_coloring to graph_coloring"
git push origin add-rlx-coloring-binding
```

Open a pull request from your fork to the Algorithm Nexus main branch.

To apply this experiment to an instance, continue with
[How to add a benchmark submission](./add_benchmark_submission.md).

---

## Alternatives

### Omit mappings when the experiment has no counterpart inputs

When the experiment takes no problem-property inputs (e.g. it always operates on
a fixed artifact and needs no per-dimension filtering), both
`problemPropertyMapping` and `metricMapping` can be omitted. Any problem
property from the instance that has no entry in `problemPropertyMapping` is
treated as having no counterpart experiment input and is not used for forming a
[routing query](../../design/benchmarking/logical_benchmarks_and_instances.md#62-routing-query).

```yaml
instanceMappingIdentifier: sorting_bubble
instanceReference: random_100k/sorting
experiment:
    actuatorIdentifier: custom_experiments
    experimentIdentifier: bubble_sort
    experimentVersion: 1.0.0
targetMapping:
    experimentProperty: model
```

`metricMapping` can still be omitted whenever the experiment already uses the
same metric names as the logical benchmark.

### Map a categorical instance value to experiment predicates

To collapse a range of experiment inputs onto one instance category, use a
categorical value mapping:

```yaml
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
                domainRange: [200, 500]
                variableType: CONTINUOUS_VARIABLE_TYPE
```

### Map experiment properties to instance artifacts

When the experiment takes instance artifact files as inputs, use
`instanceArtifactMapping`. A `fieldMapping` entry renames the instance artifact
property to the experiment input; a `staticMapping` entry pins an artifact
property to a constant value implicit in the experiment:

```yaml
# Field mapping: dynamic artifact property mapped to experiment input
instanceArtifactMapping:
    - instance:
          identifier: graph
      instance:
          identifier: input_graph
      validValues:
          - graph.json
```

### Pin a property with static filters

Static filters pin known-constant property values to a binding without recording
them in results or benchmark instances.

```yaml
staticFilters:
    - property:
          identifier: dataset
      value: random
```

See
[section 4 of Logical Benchmarks and Instances](../../design/benchmarking/logical_benchmarks_and_instances.md#4-benchmark-instance-binding)
for the mapping variants.

## See also

- [Logical Benchmarks and Instances](../../design/benchmarking/logical_benchmarks_and_instances.md)
  — binding schema and aggregation
- [How to add a benchmark problem and instance](./add_benchmark_problem.md)
- [How to add a benchmark experiment](./add_benchmark_experiment.md)
- [How to add a benchmark submission](./add_benchmark_submission.md)
- [`nexus validate experiments`](../../getting-started/cli-reference.md#nexus-validate-experiments)
