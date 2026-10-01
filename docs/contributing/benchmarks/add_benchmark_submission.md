<!--
Copyright IBM Corporation 2026
SPDX-License-Identifier: Apache-2.0
-->

# How to add a benchmark submission

This guide shows you how to register a benchmark submission in Algorithm Nexus.

A **benchmark submission** is one registered use of a benchmark experiment on a
benchmark instance for a specific target:

```text
Benchmark Submission = Benchmark Experiment + Benchmark Target + Benchmark Instance
```

Each submission is a folder under `experiments/<experiment-name>/submissions/`
containing a `space.yaml` file. That file is how you apply the experiment to the
instance.

The steps below apply the `rlx_coloring` experiment to the `erdos_renyi_50_02`
instance, with `rlx` as the target. After that walk-through,
[Alternatives](#alternatives) covers inspecting the experiment, running the
submission locally, and applying the same experiment to another instance.

## Prerequisites

Work from a local checkout of your Algorithm Nexus fork with the CLI extra
installed:

```bash
cd algorithm-nexus
uv sync --group dev --extra cli
git checkout -b add-rlx-coloring-submission
```

To add the `rlx_coloring` experiment, see
[How to add a benchmark experiment](./add_benchmark_experiment.md).

To add the `erdos_renyi_50_02` instance, see
[How to add a benchmark problem and instance](./add_benchmark_problem.md).
When that instance is already registered it lives at
`benchmarks/graph_coloring/instances/erdos_renyi_50_02/instance.yaml`.

To map this instance's property names onto the experiment's names, see
[How to bind an experiment to a problem](./add_instance_binding.md).

## 1. Create the submission from the instance

The instance file `benchmarks/graph_coloring/instances/erdos_renyi_50_02/instance.yaml` contains:

```yaml
identifier: erdos_renyi_50_02
description: 50-node Erdos-Renyi graph with edge density 0.2
graph_family: erdos_renyi
num_vertices: 50
edge_density: 0.2
```

Create a submission folder under `rlx_coloring` named after that instance:

```bash
mkdir -p experiments/rlx_coloring/submissions/erdos_renyi_50_02
```

Write `experiments/rlx_coloring/submissions/erdos_renyi_50_02/space.yaml`.
`space.yaml` is an `ado` discoveryspace that pins this instance and target for
the experiment. Property names in `entitySpace` are the experiment's names; the
instance file uses the problem's names.

```yaml
entitySpace:
    - identifier: solver
      propertyDomain:
          values: ["rlx"]
    - identifier: n_nodes
      propertyDomain:
          values: [50]
    - identifier: density
      propertyDomain:
          values: [0.2]
    - identifier: graph_type
      propertyDomain:
          values: ["erdos_renyi"]

experiments:
    - actuatorIdentifier: custom_experiments
      experimentIdentifier: rlx_coloring
```

Here `n_nodes`, `density`, and `graph_type` carry `num_vertices`,
`edge_density`, and `graph_family` from the instance, and `solver` is the
target.

See
[Using your custom experiment in a discoveryspace](https://ibm.github.io/ado/actuators/creating-custom-experiments/#using-your-custom-experiment-in-a-discoveryspace)
for the `space.yaml` syntax.

You now have:

```text
experiments/rlx_coloring/
├── experiment_package.yaml
└── submissions/
    └── erdos_renyi_50_02/
        └── space.yaml
```

## 2. Validate

```bash
uv run nexus validate experiments --experiment rlx_coloring
```

A successful run lists the submission with status `success`. The submission is
ready to commit.

## 3. Open a pull request

```bash
git add experiments/rlx_coloring/submissions/erdos_renyi_50_02
git commit -s -m "feat(benchmark): Add erdos_renyi_50_02 submission for rlx_coloring"
git push origin add-rlx-coloring-submission
```

Open a pull request from your fork to the Algorithm Nexus main branch.

---

## Alternatives

### Inspect the experiment inputs and outputs

To learn the experiment's input names when you are not following this example,
install its package and describe it with `ado`:

```bash
uv pip install rlx-coloring
ado describe experiment rlx_coloring
```

Use those property names in the submission `entitySpace`.

### Run the submission locally

To execute the submission on your machine, install the experiment package and
create an `ado` space and operation. Save this operation configuration as
`op.yaml`:

```yaml
metadata:
    name: randomwalk-all
spaces:
    - dynamically_inserted
operation:
    module:
        operatorName: random_walk
        operationType: search
    parameters:
        numberEntities: all
        samplerConfig:
            samplerType: generator
            mode: random
```

Then:

```bash
uv pip install rlx-coloring
ado create space -f experiments/rlx_coloring/submissions/erdos_renyi_50_02/space.yaml
ado create operation -f op.yaml --use-latest space
```

See [Benchmark Execution and Operations](../../design/benchmarking/benchmark_execution.md)
and the [ADO documentation](https://ibm.github.io/ado) for sweeps and remote
execution.

### Apply the same experiment to another instance

To apply this experiment to a different instance — or to a different target on
this instance — create another folder under `submissions/` and write a
`space.yaml` whose `experimentIdentifier` is still one of the ids in
`experiment_package.yaml`.

```bash
mkdir -p experiments/rlx_coloring/submissions/<submission-name>
```

Then validate as in [step 2](#2-validate).

### Validate every experiment

To validate all registered experiments and their submissions:

```bash
uv run nexus validate experiments
```

To validate one experiment folder, use the command in [step 2](#2-validate).

## See also

- [Benchmark Experiments and Submissions](../../design/benchmarking/benchmark_experiments_and_submissions.md)
  — schema and folder layout
- [How to add a benchmark experiment](./add_benchmark_experiment.md)
- [How to add a benchmark problem and instance](./add_benchmark_problem.md)
- [How to bind an experiment to a problem](./add_instance_binding.md)
- [Benchmark Execution and Operations](../../design/benchmarking/benchmark_execution.md)
- [`nexus validate experiments`](../../getting-started/cli-reference.md#nexus-validate-experiments)
