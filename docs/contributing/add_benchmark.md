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

A benchmark experiment is a Python package that defines how to evaluate an
algorithm. First check whether a suitable experiment already exists in Algorithm
Nexus before creating a new one.

### Find an existing experiment

List all benchmark experiments registered across Algorithm Nexus:

```bash
uv run nexus list benchmark-experiments
```

If an experiment covers the evaluation you need, note its experiment ID and the
benchmark package that provides it — you will reference both in the next step.
Skip ahead to [Step 2](#step-2-register-the-experiment-with-your-nexus-package).

To inspect the inputs, outputs, and parameters of a specific experiment, install
the benchmark package it belongs to and use the `ado` CLI:

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
    └── <benchmark-package-name>/
        ├── pyproject.toml
        └── src/
```

## Step 2: Register the experiment with your Nexus package

Edit `packages/<package-name>/nexus.yaml` to declare that it uses a the
experiment from the given package

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

Each `requirement_specifier` must resolve to a Python package that contains an
`ado` custom experiment.

Validate the updated package configuration:

```bash
uv run nexus validate package packages/<package-name>
```

Fix any validation errors before proceeding.

## Step 3: Define a benchmark instance for your model

A benchmark instance specifies executing a registered experiment on your
model/algorithm with a specific set of parameter values (workload). Each
benchmark instance is a folder under your model's `benchmark_instances/`
directory, that contains a `ado` `space.yaml`

Create the directory,

```bash
mkdir -p packages/<package-name>/models/<model-name>/benchmark_instances/<instance-name>
```

Create
`packages/<package-name>/models/<model-name>/benchmark_instances/<instance-name>/space.yaml`:

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
uv run nexus validate package packages/<package-name>
```

## Step 4: Run the benchmark

Install the benchmark package and run the benchmark instance locally using the
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

Then,

```bash
uv pip install packages/<package-name>/benchmark_packages/<experiment-package-name>
ado create space -f <space-yaml-path>
ado create operation -f op.yaml --use-latest space
```

See the [ADO documentation](https://ibm.github.io/ado) for the full set of
execution options including parameter sweeps and remote execution.

## Step 5: Commit Changes and Open a Pull Request

Add and commit your changes:

```bash
git add packages/<package-name>
git add benchmark_packages #required when also adding a benchmark package during Step 1
git commit -s -m "feat(benchmark): Add <instance-name> benchmark for <model-name>"
git push origin <your-branch>
```

Open a pull request from your fork to the Algorithm Nexus main branch.

---

## Optional: Mapping to logical benchmarks

Once your benchmark is running, you can connect it to a logical benchmark so the
results can be compared with results from other experiments targeting the same
type of problem. This requires creating a _benchmark biding_ that maps the
experiments internal parameters and metrics to a shared, canonical vocabulary.

This is done in two parts:

1. Creating the logical benchmark definition (if it does not exist)
2. Adding the benchmark binding for your experiment to the logical benchmark

### Check for an existing logical benchmark definition

Logical benchmark definitions live in the `benchmarks/` directory at the root of
the Algorithm Nexus repository. Browse that directory to see whether a
definition already exists for your domain (e.g. `inference_serving.yaml`,
`max_cut_solver.yaml`).

- **If a definition exists** — you add a binding for experiment to it. Continue
  to
  [Add a benchmark binding for your experiment](#add-a-benchmark-binding-for-your-experiment).
- **If no definition exists** — you will create one first. Continue to
  [Create a logical benchmark definition](#create-a-logical-benchmark-definition).

### Create a logical benchmark definition

If no definition exists, create a YAML file in
`benchmarks/<logical-benchmark-id>.yaml`. This file establishes the canonical
vocabulary for your benchmark — property names, valid values, and metric names.

A minimal example:

```yaml
logicalBenchmark:
  benchmarkIdentifier: inference_serving
  description: >
      Evaluation of AI model inference serving throughput and latency under
      controlled traffic conditions.
  target:
      - identifier: model
        metadata:
            description: "The id of the AI model being benchmarked"
  properties:
      - identifier: dataset
        metadata:
            description: "Dataset used for inference requests."
            # No propertyDomain: Will be OPEN_CATEGORICAL_DOMAIN by default
      - identifier: workload
        metadata:
            description: "Traffic pattern or workload profile."
        propertyDomain:
            values: ["steady_state_heavy", "poisson_bursty", "light_load"]
  metrics:
      - throughput_tokens_per_second
      - time_to_first_token_ms
  owner: "@vllm-team"
bindings: [] # List of bindings to this benchmark
```

For the full schema and a complete worked example, see
[Section 2 of the Benchmark Metadata Convention](../design/benchmark_metadata_convention.md#2-logical-benchmark-definition).

### Add a benchmark binding for your experiment

The binding is added to the list of bindings in the logical benchmark yaml.

```yaml
logicalBenchmark: ... #logical benchmark fields
bindings:
    - experiment:
          experimentIdentifer: myexperiment
          experimentVersion: 1.2
          actuatorIdentifier: customexperiments
      targetMapping: ...
    -  #next binding
```

A binding contains the following mapping sections: `

- `targetMapping`: Maps the target property of the benchmark to an experiment input property
- `propertyMapping`: Maps the other inputs of the logical benchmark to inputs of the
  experiment
- `metricMappings`: Maps outputs of the logical benchmark to the outputs of the
  experiment

An example binding is

```yaml
benchmarkIdentifier: inference_serving
experiment:
    actuatorIdentifier: vllm_performance
    experimentIdentifier: guide_llm_runner
    experimentVersion: 2.0.0 # The binding only uses the major version
targetMapping: model_name #The property model_name maps to the target property defined in the benchmark
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
          value: steady_state_heavy
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

For the full benchmark binding schema and worked examples, see the
[Benchmark Metadata Convention](../design/benchmark_metadata_convention.md).

---

## `benchmarks/` Directory Convention

The top-level `benchmarks/` directory is the single source of truth for all
logical benchmark definitions and their bindings.

### Structure

One YAML file per logical benchmark, named after the `benchmarkIdentifier`:

```text
benchmarks/
├── inference_serving.yaml
├── max_cut_solver.yaml
└── ...
```

Each file uses the following top-level structure:

```yaml
logicalBenchmark:
    # Definition fields (see Section 2 of the Benchmark Metadata Convention)
bindings:
    # List of benchmark bindings (see Section 3 of the Benchmark Metadata Convention)
```

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
  place. If the original mappings are still valid, create a new logical benchmark
  instead.
- **New non-default experiment properties are added in a minor version bump** —
  if those properties must be set to non-default values to reproduce the same
  measurement, the binding must be updated because a different subset of
  experiment data would be aggregated.

### Validation

Validate all logical benchmark files before opening a pull request:

```bash
uv run nexus validate logical-benchmarks
```

To validate a single file:

```bash
uv run nexus validate logical-benchmarks --file benchmarks/<logical-benchmark-id>.yaml
```

---

## Getting Help

If you encounter issues:

1. Check the
   [Benchmark Integration Design](../design/benchmark_integration_design.md)
2. Check the
   [Benchmark Metadata Convention](../design/benchmark_metadata_convention.md)
3. Refer to the [ADO documentation](https://ibm.github.io/ado)
4. Search existing issues on GitHub
5. Open a new issue with details about your problem
