<!--
Copyright IBM Corporation 2026
SPDX-License-Identifier: Apache-2.0
-->

# Contributing a Benchmark

This guide walks you through adding a benchmark to Algorithm Nexus. If you have
not yet registered your algorithm, start with
[Contributing a Python Algorithm Package to Algorithm Nexus](./add_new_nexus_package.md).

There are four steps to add a benchmark submission:

1. **Find or create a benchmark experiment package**
2. **Create an experiment folder and register the package**
3. **Define a benchmark submission**
4. **Run the benchmark submission**

## Prerequisites

Before you begin, ensure:

- `uv` is [installed](https://docs.astral.sh/uv/getting-started/installation/)
  on your system.
- You have a
  [fork](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo)
  of the Algorithm Nexus repository checked out locally and your development
  environment is set up:

```bash
cd algorithm-nexus
uv sync --group dev --extra cli
```

## Step 1: Find or create a benchmark experiment package

A benchmark experiment is a Python package that defines how to evaluate a
benchmark target. First check whether a suitable experiment already exists in
Algorithm Nexus before creating a new one.

### Find an existing experiment

List all benchmark experiments registered across Algorithm Nexus:

```bash
uv run nexus list benchmark-experiments
```

If an experiment covers the evaluation you need, note its experiment ID and the
experiment folder that declares it — you will reference both in the next step.
Skip ahead to [Step 2](#step-2-create-an-experiment-folder-and-register-the-package).

To inspect the inputs, outputs, and parameters of a specific experiment, install
the benchmark package it belongs to and use the `ado` CLI:

```bash
uv pip install <benchmark-package>
ado describe experiment <experiment-id>
```

### Create a new experiment package

If no existing experiment fits your needs, create one following the
[ADO custom experiment template](https://ibm.github.io/ado/actuators/creating-custom-experiments/).
A benchmark experiment is a standard `ado` custom experiment packaged as a
Python package. The package must be published on PyPI or hosted on GitHub —
local packages stored only inside the repository are not supported.

## Step 2: Create an experiment folder and register the package

Create a new directory under `experiments/` for your experiment:

```bash
mkdir -p experiments/<experiment-name>/submissions
mkdir -p experiments/<experiment-name>/bindings
```

Create `experiments/<experiment-name>/experiment_package.yaml` to declare the experiment
package and the experiment identifiers it exposes:

```yaml
experiment_package:
    # PyPI package (optionally with version constraint)
    requirement_specifier: "<experiment-package-name>"
    experiments:
        - "<experiment-id>"
```

Or for a package hosted on GitHub:

```yaml
experiment_package:
    requirement_specifier: "https://github.com/<org>/<experiment-package-repo>"
    experiments:
        - "<experiment-id>"
```

The `requirement_specifier` must be a PyPI package name or a GitHub URL.
Local paths are not allowed.

Validate the new experiment folder:

```bash
uv run nexus validate experiments --experiment <experiment-name>
```

Fix any validation errors before proceeding.

## Step 3: Define a benchmark submission

A benchmark submission is one registered use of a benchmark experiment on a
benchmark instance for a specific benchmark target. Each submission is a folder
under `experiments/<experiment-name>/submissions/` containing a `space.yaml`
file.

Create the directory:

```bash
mkdir -p experiments/<experiment-name>/submissions/<submission-name>
```

Create `experiments/<experiment-name>/submissions/<submission-name>/space.yaml`:

```yaml
entitySpace:
    - identifier: dataset
      propertyDomain:
          values: ["<dataset-name>"]
    - identifier: split
      propertyDomain:
          values: ["test"]

experiments:
    - actuatorIdentifier: custom_experiments
      experimentIdentifier: <experiment-id>
```

The `entitySpace` defines the benchmark instance and any other parameters for
this submission. The `experimentIdentifier` must match one of the experiment IDs
you declared in `experiment_package.yaml` in the previous step.

For full details on `space.yaml` syntax, see the
[ADO discoveryspace documentation](https://ibm.github.io/ado/actuators/creating-custom-experiments/#using-your-custom-experiment-in-a-discoveryspace).

Validate the experiment folder again to confirm the submission is well-formed:

```bash
uv run nexus validate experiments --experiment <experiment-name>
```

## Step 4: Run the benchmark submission

Install the experiment package and run the benchmark submission locally using the
`ado` CLI. First save the following operation configuration to a file `op.yaml`.
It will execute the experiment on all points in your space.

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
uv pip install <experiment-package-name>
ado create space -f experiments/<experiment-name>/submissions/<submission-name>/space.yaml
ado create operation -f op.yaml --use-latest space
```

See the [ADO documentation](https://ibm.github.io/ado) for the full set of
execution options including parameter sweeps and remote execution.

## Step 5: Commit Changes and Open a Pull Request

Add and commit your changes:

```bash
git add experiments/<experiment-name>
git commit -s -m "feat(benchmark): Add <submission-name> submission for <experiment-name>"
git push origin <your-branch>
```

Open a pull request from your fork to the Algorithm Nexus main branch.

---

## Optional: Mapping to logical benchmarks

Once your submission is running, you can connect it to a logical benchmark so the
results can be compared with results from other experiments targeting the same
type of problem. This requires creating a _benchmark biding_ that maps the
experiments internal parameters and metrics to a shared, canonical vocabulary.

This is done in two parts:

1. Creating the logical benchmark definition (if it does not exist)
2. Adding the benchmark binding for your experiment to the logical benchmark

### Check for an existing logical benchmark definition

Logical benchmark definitions live in the `benchmarks/` directory at the root of
the Algorithm Nexus repository. Browse that directory to see whether a
definition already exists for your domain (e.g.
`benchmarks/llm-inference/benchmark.yaml`, `benchmarks/max-cut/benchmark.yaml`).

- **If a definition exists** — you add a binding for experiment to it. Continue
  to
  [Add a benchmark binding for your experiment](#add-a-benchmark-binding-for-your-experiment).
- **If no definition exists** — you will create one first. Continue to
  [Create a logical benchmark definition](#create-a-logical-benchmark-definition).

### Create a logical benchmark definition

If no definition exists, create a directory in
`benchmarks/<logical-benchmark-id>/` with a `benchmark.yaml` file. This file
establishes the canonical vocabulary for your benchmark — property names, valid
values, and metric names.

A minimal example:

```yaml
logicalBenchmark:
    benchmarkIdentifier: graph_coloring
    title: Graph Coloring
    description: >
        Evaluates graph-coloring algorithms on their ability to produce valid
        k-colorings with a small chromatic number. Instances span random
        Erdős–Rényi graphs and structured benchmark graphs at varying densities.
    instance:
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
        - identifier: graph
          is_artifact: true
          metadata:
              description: Graph input files in various formats.
    metrics:
        - num_colors_used
        - is_valid_coloring
        - elapsed_ms
    ranking:
        metric: num_colors_used
        order: asc
    owner: "@graph-team"
```

For the full schema and a complete worked example, see
[Section 2 of Logical Benchmarks and Instances](../design/benchmarking/logical_benchmarks_and_instances.md#2-logical-benchmark-definition).

### Add logical benchmark instances

To define specific benchmark problem instances (e.g., individual graphs, routing
problem instances, or datasets), add a subfolder per instance in
`benchmarks/<logical-benchmark-id>/instances/<instance-name>/` containing an
`instance.yaml` file and any subfolders holding artifact files referenced by the
instance.

Example instance YAML
(`benchmarks/<logical-benchmark-id>/instances/graph_01/instance.yaml`):

```yaml
identifier: graph_01
description: 50-node random graph
graph_family: random_regular
num_vertices: 50
edge_density: 0.2
graph:
    artifacts_location: graph_files # subfolder that exists inside instances/graph_01/
```

### Add a benchmark binding for your experiment

Create a binding file under `experiments/<experiment-name>/bindings/`. Each
entry in the `bindings` list must include a `benchmarkIdentifier` field that
names the logical benchmark it maps to.

```yaml
bindings:
    - benchmarkIdentifier: <logical-benchmark-id>
      experiment:
          experimentIdentifier: myexperiment
          experimentVersion: 1.2
          actuatorIdentifier: customexperiments
      targetMapping: ...
    - # next binding (may target a different benchmarkIdentifier)
```

A binding contains the following mapping sections:

- `targetMapping`: Names the experiment property that carries the benchmark
  target (e.g. the algorithm or model identifier)
- `instanceMapping`: Maps benchmark instance properties to experiment inputs
- `staticFilters`: Sets static property values implicit in either the logical
  benchmark or the experiment. Contains two optional sub-keys:
    - `experimentFilters`: pins experiment properties to values that are
      implicit in the logical benchmark (adds a constant `WHERE` clause to every
      query)
    - `benchmarkFilters`: pins benchmark instance properties to values that are
      implicit in the experiment (injects a constant value into leaderboard rows
      without reading it from the experiment results)
- `metricMapping`: Maps outputs of the logical benchmark to the outputs of the
  experiment

An example binding file (`experiments/rlx_coloring/bindings/graph_coloring_binding.yaml`):

```yaml
bindings:
    - benchmarkIdentifier: graph_coloring
      experiment:
          actuatorIdentifier: custom_experiments
          experimentIdentifier: rlx_coloring
          experimentVersion: 1.0.0 # The binding only uses the major version
      targetMapping: solver # The experiment property that carries the benchmark target identifier
      instanceMapping:
          - benchmark:
                identifier: num_vertices
            experiment:
                identifier: n_nodes # rlx_coloring's internal param name
          - benchmark:
                identifier: edge_density
            experiment:
                identifier: density # rlx_coloring's internal param name
      metricMapping:
          - benchmark:
                identifier: num_colors_used
            experiment:
                identifier: colors # rlx_coloring's internal metric name
          - benchmark:
                identifier: elapsed_ms
            experiment:
                identifier: runtime_ms # rlx_coloring's internal metric name
```

For the full benchmark binding schema and worked examples, see the
[Logical Benchmarks and Instances](../design/benchmarking/logical_benchmarks_and_instances.md).

---

## `benchmarks/` Directory Convention

The top-level `benchmarks/` directory is the single source of truth for all
logical benchmark definitions and their bindings.

### Structure

Each logical benchmark has its own directory containing `benchmark.yaml` and an
`instances/` directory with per-instance subfolders:

```text
benchmarks/
├── <benchmark-id>/
│   ├── benchmark.yaml
│   ├── README.md              # optional: full problem statement and context
│   └── instances/
│       ├── <instance-1-id>/
│       │   ├── instance.yaml
│       │   └── <artifacts-subfolder>/   # named by artifacts_location in instance.yaml
│       │       ├── graph.dimacs
│       │       └── graph.json
│       └── ...
└── ...
```

A `README.md` alongside `benchmark.yaml` is encouraged to provide a full
description of the problem. For example to explain the mathematical formulation,
provide references, or describe the instance structure in more detail than the
`description` field in `benchmark.yaml` allows.

Benchmark bindings for any experiment targeting this logical benchmark live in
`experiments/<experiment-name>/bindings/` (see
[Section 3 of Logical Benchmarks and Instances](../design/benchmarking/logical_benchmarks_and_instances.md#3-benchmark-binding)).

### Ownership

- The **logical benchmark owner** is given by the `owner` field in the
  `logicalBenchmark` block. If omitted, the author of the PR that introduced the
  file is treated as the owner.
- Each **benchmark binding** is owned by the author of the PR that added it.
- Ownership implies responsibility for keeping the definition and bindings
  consistent with the experiments that reference them.

### Versioning and When a Binding May Change

A benchmark binding may only be updated when:

- **Experiment property names or values change** — this should accompany a new
  experiment major version. The binding for the previous major version can be
  retained alongside the new one.
- **Logical benchmark property names or values change** — if the existing
  mappings become invalid, update the definition and all affected bindings in
  place. If the original mappings are still valid, create a new logical
  benchmark instead.
- **New non-default experiment properties are added in a minor version bump** —
  if those properties must be set to non-default values to reproduce the same
  measurement, the binding must be updated because a different subset of
  experiment data would be aggregated.

### Validation

Validate all logical benchmark files before opening a pull request:

```bash
uv run nexus validate logical-benchmarks
```

To validate a single file or benchmark folder:

```bash
uv run nexus validate logical-benchmarks --file benchmarks/<logical-benchmark-id>
```

---

## Getting Help

If you encounter issues:

1. Check the
   [Benchmark Experiments and Submissions](../design/benchmarking/benchmark_experiments_and_submissions.md)
2. Check
   [Logical Benchmarks and Instances](../design/benchmarking/logical_benchmarks_and_instances.md)
3. Refer to the [ADO documentation](https://ibm.github.io/ado)
4. Search existing issues on GitHub
5. Open a new issue with details about your problem
