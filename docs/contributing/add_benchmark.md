<!--
Copyright IBM Corporation 2026
SPDX-License-Identifier: Apache-2.0
-->

# Contributing a Benchmark for a Model

This guide walks you through adding a benchmark for an algorithm that you have
already registered in Algorithm Nexus. If you have not yet registered your
algorithm, start with
[Contributing a Python Algorithm Package to Algorithm Nexus](./add_new_nexus_package.md).

There are four steps to add a benchmark for your algorithm:

1. **Find or create a benchmark experiment**
2. **Register the experiment with your Nexus package**
3. **Define a benchmark instance for your algorithm**
4. **Run the benchmark**

## Prerequisites

Before you begin, ensure:

- Your algorithm is registered in a Nexus package under
  `packages/<package-name>/models/<model-name>/model.yaml`. See
  [Contributing a Python Algorithm Package](./add_new_nexus_package.md) if not.
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

## Step 1: Find or create a benchmark experiment

A benchmark experiment is a Python package that defines how to evaluate an algorithm.
First check whether a suitable experiment already exists in Algorithm Nexus
before creating a new one.

### Find an existing experiment

List all benchmark experiments registered across Algorithm Nexus:

```bash
uv run nexus list benchmark-experiments
```

If an experiment covers the evaluation you need, note its experiment ID and
the benchmark package that provides it — you will reference both in the next
step. Skip ahead to [Step 2](#step-2-register-the-experiment-with-your-nexus-package).

To inspect the inputs, outputs, and parameters of a specific experiment,
install the benchmark package it belongs to and use the `ado` CLI:

```bash
uv pip install <benchmark-package>
ado describe experiment <experiment-id>
```

### Create a new experiment

If no existing experiment fits your needs, create one following the
[ADO custom experiment template](https://ibm.github.io/ado/actuators/creating-custom-experiments/).
A benchmark experiment is a standard `ado` custom experiment packaged as a
Python package.

Place the package under your Nexus package directory:

```text
packages/<package-name>/
└── benchmark_packages/
    └── <experiment-package-name>/
        ├── pyproject.toml
        └── src/
```

## Step 2: Register the experiment with your Nexus package

Edit `packages/<package-name>/nexus.yaml` to declare that it
uses a the experiment from the given package

```yaml
package:
    name: <package-name>

    benchmark_packages:
        # Local package stored in this repository
        - requirement_specifier: "./packages/<package-name>/benchmark_packages/<experiment-package-name>"
          experiments:
              - "<experiment-id>"

        # Remote package hosted on GitHub
        - requirement_specifier: "https://github.com/<org>/<experiment-package-repo>"
          experiments:
              - "<experiment-id>"

        # Package published on PyPI
        - requirement_specifier: "<experiment-package-name>"
          experiments:
              - "<experiment-id>"
```

Each `requirement_specifier` must resolve to a Python package that contains an `ado` experiment.

Validate the updated package configuration:

```bash
uv run nexus validate packages/<package-name>
```

Fix any validation errors before proceeding.

## Step 3: Define a benchmark instance for your model

A benchmark instance specifies executing a registered experiment on your model/algorithm
with a specific set of parameter values (workload). Each benchmark instance is a folder under
your model's `benchmark_instances/` directory, that contains a `ado` `space.yaml`

Create the directory,

```bash
mkdir -p packages/<package-name>/models/<model-name>/benchmark_instances/<instance-name>
```

Create `packages/<package-name>/models/<model-name>/benchmark_instances/<instance-name>/space.yaml`:

Example:

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

The `entitySpace` defines the workload parameters for this instance. The
`experimentIdentifier` must match one of the experiment IDs you registered in
`nexus.yaml` in the previous step.

For full details on `space.yaml` syntax, see the
[ADO discoveryspace documentation](https://ibm.github.io/ado/actuators/creating-custom-experiments/#using-your-custom-experiment-in-a-discoveryspace).

Validate the package again to confirm the instance is well-formed:

```bash
uv run nexus validate packages/<package-name>
```

## Step 4: Run the benchmark

Install the benchmark package and run the benchmark instance locally using
the `ado` CLI. First save the following operation configuration to a file `op.yaml`.
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

Then,

```bash
uv pip install packages/<package-name>/benchmark_packages/<experiment-package-name>
ado create space -f <space-yaml-path>
ado create operation -f op.yaml --use-latest space
```

See the
[ADO documentation](https://ibm.github.io/ado) for the full set of execution
options including parameter sweeps and remote execution.

## Step 5: Commit Changes and Open a Pull Request

Add and commit your changes:

```bash
git add packages/<package-name>
git commit -s -m "feat(benchmark): Add <instance-name> benchmark for <model-name>"
git push origin <your-branch>
```

Open a pull request from your fork to the Algorithm Nexus main branch.

---

## Optional: Mapping to logical benchmarks

Once your benchmark is running, you can connect it to a logical benchmark
so the results can be compared with results from other experiments targeting the same
type of problem. This requires adding metadata to your experiment that maps its
internal parameters and metrics to a shared, canonical vocabulary.

This is done in two parts: adding a manifest to your experiment, and (if no
definition exists for your domain yet) creating a logical benchmark definition.

### Check for an existing logical benchmark definition

Logical benchmark definitions live in the `logical_benchmarks/` directory at
the root of the Algorithm Nexus repository. Browse that directory to see
whether a definition already exists for your domain (e.g.
`inference_serving.yaml`, `max_cut_solver.yaml`).

- **If a definition exists** — your experiment just needs a manifest that
  maps to it. Continue to
  [Add a manifest to your experiment](#add-a-manifest-to-your-experiment).
- **If no definition exists** — you will create one first. Continue to
  [Create a logical benchmark definition](#create-a-logical-benchmark-definition).

### Add a manifest to your experiment

The manifest is added to the `metadata` field of your `ado` experiment
definition. See the
[ADO custom experiment documentation](https://ibm.github.io/ado/actuators/creating-custom-experiments/)
for where this field lives in the experiment schema.

A minimal manifest declares the logical benchmark your experiment targets,
the parameter that identifies the benchmark target, and how the experiment's
internal parameters map to the canonical dimensions:

```yaml
logical_benchmark: <logical-benchmark-id>
target_mapping: <experiment-parameter-that-holds-the-model-id>

dimensions:
    - dimension_name: dataset
      mapped_from_arg: <your-internal-dataset-parameter-name>

    - dimension_name: workload
      profile_mapping:
          - logical_name: steady_state_heavy
            requires_params:
                traffic_shape:
                    values: ["constant"]
                concurrency:
                    domainRange: [100, 99999]
                    variableType: CONTINUOUS_VARIABLE_TYPE

metric_mapping:
    <your-metric-name>: <canonical-metric-name>
```

The `dimension_name` values and any `logical_name` values in `profile_mapping`
must match exactly the dimension names and domain values defined in the logical
benchmark definition. The `metric_mapping` translates your experiment's output
metric names to the canonical names defined by the logical benchmark.

For the full manifest schema and worked examples, see the
[Benchmark Metadata Convention](../design/benchmark_metadata_convention.md).

### Create a logical benchmark definition

If no definition exists for your domain, create a YAML file in
`logical_benchmarks/<logical-benchmark-id>.yaml`. This file establishes the
canonical vocabulary for your benchmark domain — dimension names, valid values,
and metric names — that all future experiments in this domain will follow.

A minimal definition:

```yaml
id: <logical-benchmark-id>
description: >
    <Human-readable description of the abstract problem being evaluated.>

dimensions:
    - name: dataset
      description: "Dataset used for evaluation."
      # No domain: any dataset name is accepted.

    - name: workload
      description: "Workload profile."
      domain:
          values: ["<profile-name-1>", "<profile-name-2>"]
      value_descriptions:
          <profile-name-1>: >
              <Description of what this profile means and what experiment
              parameter values it corresponds to.>
          <profile-name-2>: >
              <Description of what this profile means.>

metrics:
    - <canonical-metric-name-1>
    - <canonical-metric-name-2>

owner: "@<your-github-username>"
```

The dimension names and workload profile names you define here become the
shared vocabulary for your domain. Other teams adding experiments for the same
problem will adopt these names and map their own internal parameter names to
them.

For the full schema and a complete worked example, see
[Section 2 of the Benchmark Metadata Convention](../design/benchmark_metadata_convention.md#2-logical-benchmark-definition).

---

## Getting Help

If you encounter issues:

1. Check the [Benchmark Integration Design](../design/benchmark_integration_design.md)
2. Check the [Benchmark Metadata Convention](../design/benchmark_metadata_convention.md)
3. Refer to the [ADO documentation](https://ibm.github.io/ado)
4. Search existing issues on GitHub
5. Open a new issue with details about your problem
