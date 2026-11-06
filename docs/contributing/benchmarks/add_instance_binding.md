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
instanceReference: graph_coloring/erdos_renyi_50_02
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

### How the experiment version is used

`experimentVersion` is the first version the binding applies to. The binding
matches all runs of the experiment from that version up to, but not including,
the `experimentVersion` of the next higher binding for the same experiment and
instance. With no higher binding, `1.0.0` above covers runs of `1.0.1`, `1.1.0`
and all later versions.

If something needs to change for newer versions of the experiment, for example
an experiment property was renamed, add an additional binding with the new
`experimentVersion` and updated mappings rather than editing this one. For
example, adding a binding at `1.3.0` makes it cover `1.3.0` and later, while this
one keeps covering `1.0.0` up to (but not including) `1.3.0`. See
[Experiment version matching](../../design/benchmarking/logical_benchmarks_and_instances.md#experiment-version-matching).

Binding versions only select which runs are matched. Data exists for a version
only if that version has been run, and each version of the experiment that will
have data needs its own `requirement_specifier` in `experiment_package.yaml`
(see [Add a benchmark experiment](add_benchmark_experiment.md)).

## 2. Validate

```bash
uv run nexus validate experiments --experiment rlx_coloring
```

A successful run lists the binding file with status `success`. Besides the
experiment package, the command checks that:

- the binding matches the schema and its `instanceBindingIdentifier` is unique
- `experimentIdentifier` is listed in the experiment's `experiment_package.yaml`
- `instanceReference` points to an existing benchmark and instance
- every mapped metric and problem property exists in the benchmark
- every `instanceArtifactMapping` names an artifact declared by the instance,
  and each file in `validValues` exists in that artifact's `artifactsLocation`

The binding is ready to commit.

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
instanceBindingIdentifier: sorting_bubble
instanceReference: sorting/random_100k
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
`instanceArtifactMapping`. Each entry maps the instance artifact property to the
experiment input property and lists the valid file names:

```yaml
instanceArtifactMapping:
    - instance:
          identifier: graph
      experiment:
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
