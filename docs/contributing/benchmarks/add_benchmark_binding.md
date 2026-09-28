<!--
Copyright IBM Corporation 2026
SPDX-License-Identifier: Apache-2.0
-->

# How to bind an experiment to a problem

This guide shows you how to register a benchmark binding in Algorithm Nexus.

A **benchmark binding** maps an experiment's property and metric names onto a
problem's instance properties and metrics. A submission's `space.yaml` uses the
experiment's names; the binding is how those names correspond to the instance.

The steps below bind `rlx_coloring` to the `graph_coloring` problem. After that
walk-through, [Alternatives](#alternatives) covers matching names, several
experiments in one file, categorical mappings, and static filters.

## Prerequisites

Work from a local checkout of your Algorithm Nexus fork with the CLI extra
installed:

```bash
cd algorithm-nexus
uv sync --group dev --extra cli
git checkout -b add-rlx-coloring-binding
```

The `graph_coloring` problem is already registered. To add it, see
[How to add a benchmark problem and instance](./add_benchmark_problem.md).

The `rlx_coloring` experiment is already registered. To add it, see
[How to add a benchmark experiment](./add_benchmark_experiment.md).

## 1. Create the binding

Create the bindings folder and write a YAML file that names the problem, the
experiment, and the field mappings.

```bash
mkdir -p experiments/rlx_coloring/bindings
```

Create `experiments/rlx_coloring/bindings/graph_coloring_binding.yaml`:

```yaml
bindings:
    - benchmarkIdentifier: graph_coloring
      experiment:
          actuatorIdentifier: custom_experiments
          experimentIdentifier: rlx_coloring
          experimentVersion: 1.0.0
      targetMapping: rlx # The target (algorithm) of this experiment is always "rlx".
      instanceMapping:
          - benchmark: # benchmarks num_vertices is experiments n_nodes parameter
                identifier: num_vertices
            experiment:
                identifier: n_nodes
          - benchmark:
                identifier: edge_density
            experiment:
                identifier: density
          - benchmark:
                identifier: graph_family
            experiment:
                identifier: graph_type
      metricMapping:
          - benchmark: #the benchmarks num_colors_used output is given by the experiment colors output
                identifier: num_colors_used
            experiment:
                identifier: colors
          - benchmark:
                identifier: elapsed_ms
            experiment:
                identifier: runtime_ms
```

`instanceMapping` pairs each instance property with the experiment input that
carries it. `metricMapping` does the same for result columns. `targetMapping`
names the experiment property that identifies the target.

In the above example, the experiment only implements a single "benchmark target".
Hence, the mapping it static.
An experiment that allows choosing an algorithms via a parameter, would have a mapping
here as in the `instanceMapping` and `metricMapping` sections.

The full field list is in
[Logical Benchmarks and Instances](../../design/benchmarking/logical_benchmarks_and_instances.md#3-benchmark-binding).

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

### Bind when names already match

When the experiment already uses the problem's property and metric names, the
binding names the problem, the experiment, and the target:

```yaml
bindings:
    - benchmarkIdentifier: sorting
      experiment:
          actuatorIdentifier: custom_experiments
          experimentIdentifier: bubble_sort
          experimentVersion: 1.0.0
      targetMapping: algorithm
```

### Bind several experiments in one file

To bind more than one experiment from the same package, add an entry per
experiment under `bindings:`:

```yaml
bindings:
    - benchmarkIdentifier: sorting
      experiment:
          actuatorIdentifier: custom_experiments
          experimentIdentifier: bubble_sort
          experimentVersion: 1.0.0
      targetMapping: algorithm
    - benchmarkIdentifier: sorting
      experiment:
          actuatorIdentifier: custom_experiments
          experimentIdentifier: merge_sort
          experimentVersion: 1.0.0
      targetMapping: algorithm
```

### Map a categorical instance value to experiment predicates

To collapse a range of experiment inputs onto one instance category, use a
categorical value mapping:

```yaml
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
                domainRange: [200, 500]
                variableType: CONTINUOUS_VARIABLE_TYPE
```

### Pin a property that is implicit in the problem or the experiment

To assert a constant without reading it from results or the instance, add
`staticFilters`:

```yaml
staticFilters:
    experimentFilters:
        - property:
              identifier: dataset
          value: random
    benchmarkFilters:
        - property:
              identifier: graph_family
          value: random_regular
```

See
[section 3 of Logical Benchmarks and Instances](../../design/benchmarking/logical_benchmarks_and_instances.md#3-benchmark-binding)
for the mapping variants.

## See also

- [Logical Benchmarks and Instances](../../design/benchmarking/logical_benchmarks_and_instances.md)
  — binding schema and aggregation
- [How to add a benchmark problem and instance](./add_benchmark_problem.md)
- [How to add a benchmark experiment](./add_benchmark_experiment.md)
- [How to add a benchmark submission](./add_benchmark_submission.md)
- [`nexus validate experiments`](../../getting-started/cli-reference.md#nexus-validate-experiments)
