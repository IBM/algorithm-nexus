# Benchmark Integration Design for Algorithm Nexus

## Executive Summary

This document defines how benchmarking metadata is integrated into Algorithm
Nexus packages. The design keeps benchmark experiment registration at the Nexus
package level and benchmark specification in `benchmark_instances/` folders that
may exist either at package level for baselines or at model level for
model-specific benchmarks.

**Key Design Decisions:**

1. `nexus.yaml` registers benchmark packages and the benchmark experiments they
   expose to the package
2. `model.yaml` remains focused on model metadata
3. model-level `benchmark_instances/` specifies benchmark instances tied to a
   model
4. package-level `benchmark_instances/` specifies benchmark instances for
   baseline experiments that live at the top level of the Nexus package
5. The package-level `benchmark_packages/` folder stores local benchmark
   packages, and each such package follows the ADO custom experiment template
6. Benchmark package registrations in `nexus.yaml` use a `requirement_specifier`
   plus an `experiments` list
7. Every registration must resolve to an ADO custom experiment that follows the
   standardized benchmark packaging protocol
8. The benchmark target is implicit from the enclosing model definition for
   model-specific benchmark instances
9. Markdown documentation is updated before any schema, template, or validation
   implementation work

---

## 1. Requirements Analysis and Mapping

### 1.1 Benchmark System Components

Based on the [benchmark requirements](../requirements/benchmark.md), the system
has five core concepts that must be linked together by package metadata:

- **Benchmark experiment**
  - a script, harness, or workflow that executes a benchmark target on a
    workload and collects measurements
  - in this design, benchmark experiments are registered at package level in
    `nexus.yaml`
  - All benchmark experiments follow the
    [ADO custom experiment template](https://ibm.github.io/ado/actuators/creating-custom-experiments/)

- **Workload**
  - the inputs, data, and execution pattern exercised by a benchmark driver
  - in this design, workload or experiment parameter values are specified in
    per-instance `space.yaml` files under model-level or package-level
    `benchmark_instances/`

- **Benchmark target**
  - the model or algorithm being evaluated
  - in this design, the benchmark target is implicit from the enclosing model
    definition in `model.yaml` for model-level benchmark instances
  - for package-level baseline benchmark instances, the benchmark target is
    defined directly by the benchmark instance itself

- **Benchmark**
  - either a fixed benchmark experiment or a workload plus a parameterizable
    benchmark experiment
  - in this design, a benchmark instance references a registered benchmark
    experiment and provides parameter values where needed

- **Benchmark instance**
  - a concrete benchmark definition for a specific use case
  - in this design, each benchmark instance is represented by one folder under a
    model-level or package-level `benchmark_instances/` directory, containing a
    `space.yaml` file with the full ADO discoveryspace definition
  - for model-level benchmark instances, the benchmark target is the enclosing
    model
  - package-level benchmark instances support baseline experiments that live at
    the top level of the Nexus package
  - the benchmark instance binds together the selected experiment and the
    workload-specific parameter values used for execution

This follows the requirements terminology that a benchmark instance is formed
from a benchmark target together with a benchmark, where the benchmark is
represented as either a fixed benchmark experiment or a workload plus a
parameterizable benchmark experiment. For model-level benchmark instances, the
benchmark target comes from the enclosing model. For package-level baseline
benchmark instances, the benchmark target is defined directly by the benchmark
instance itself.

### 1.2 Responsibilities by File and Directory

| Location                                                                 | Responsibility                                                                                                                                  |
| ------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| [`nexus.yaml`](../../packages/terratorch/nexus.yaml)                     | Declares benchmark packages available to the package and the experiments exposed by each package                                                |
| package-level [`benchmark_packages/`](../../packages/terratorch/) folder | Stores one or more local benchmark packages, each following the ADO custom experiment template                                                  |
| package-level `benchmark_instances/` folder                              | Stores one folder per baseline benchmark instance at the top level of the Nexus package, each with a `space.yaml` ADO discoveryspace definition |
| `model.yaml`                                                             | Declares model metadata                                                                                                                         |
| model-level `benchmark_instances/` folder                                | Stores one folder per model-specific benchmark instance, each with a `space.yaml` ADO discoveryspace definition                                 |

### 1.3 Requirements to Design Mapping

| Requirement | Design interpretation                                                                                                                                                                                                                              |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| REQ 1.2     | Benchmark experiments are distributed as Python packages, including local benchmark packages under the package-level [`benchmark_packages/`](../../packages/terratorch/) directory and remote repositories addressed by URL                        |
| REQ 2.1     | Benchmark package registration happens in `nexus.yaml`, including the benchmark package `requirement_specifier` and the experiment identifiers it exposes                                                                                          |
| REQ 2.3     | Benchmark registration happens in `benchmark_instances/` folders, either at package level for baseline experiments or at model level for model-specific benchmarks, where each instance is represented by a `space.yaml` discoveryspace definition |
| REQ 3.1     | A benchmark entry specifies the benchmark to use through a dedicated discoveryspace definition in the relevant `benchmark_instances/` folder                                                                                                       |
| REQ 3.2     | New package-provided benchmark experiments are normally added as benchmark packages under the package-level [`benchmark_packages/`](packages/terratorch/) directory and then registered in `nexus.yaml` with their experiment identifiers          |
| REQ 3.3     | Models may reuse any experiment registered by the package, whether the experiment is provided by a local benchmark package or by remote repositories                                                                                               |

---

## 2. Folder Structure Design

### 2.1 Complete Nexus Package Structure

```text
packages/
└── <nexus-package-name>/
    ├── nexus.yaml
    ├── skills/
    ├── benchmark_packages/            # Local benchmark packages
    │   ├── <benchmark-package-a>/
    │   │   ├── pyproject.toml
    │   │   ├── src/
    │   └── <benchmark-package-b>/
    ├── benchmark_instances/           # Package-level baseline benchmark instances
    │   ├── <benchmark-instance-a>/
    │   │   └── space.yaml
    │   └── <benchmark-instance-b>/
    │       └── space.yaml
    └── models/
        └── <model-name>/
            ├── model.yaml
            ├── benchmark_instances/
            │   ├── <benchmark-instance-a>/
            │   │   └── space.yaml
            │   └── <benchmark-instance-b>/
            │       └── space.yaml
            └── usage.md
```

### 2.2 Ownership Model

The canonical benchmark metadata is split across three locations:

- [`nexus.yaml`](../../packages/terratorch/nexus.yaml)
  - registers the benchmark packages a package makes available
  - records the `requirement_specifier` for each registered benchmark package
  - records the experiment identifiers exposed by each registered benchmark
    package
- package-level `benchmark_instances/`
  - records which baseline benchmark instances the package makes available
  - stores one folder per package-level benchmark instance
  - carries a `space.yaml` ADO discoveryspace definition for each instance
- model-level `benchmark_instances/`
  - records which benchmark instances a model should use
  - stores one folder per model-specific benchmark instance
  - carries a `space.yaml` ADO discoveryspace definition for each instance

The package-level [`benchmark_packages/`](../../packages/terratorch/) directory
stores local benchmark packages that live with the Nexus package. Each local
benchmark package must follow the ADO custom experiment template and may expose
one or more ADO custom benchmark experiments.

### 2.3 Benchmark Package Registrations

A package-level benchmark package registration uses:

- a `requirement_specifier` to identify how the benchmark package should be
  resolved
- an `experiments` list to declare which experiment identifiers from that
  package are made available to the Nexus package

The `requirement_specifier` may be any valid Python package requirement target,
including:

1. a Python package name
2. a URL pointing to a Python package or source repository
3. a local path pointing to a Python package within [`./packages`](packages/)

In all cases, the referenced material must resolve to a Python package that
follows the ADO custom experiment format and the standardized benchmark
packaging protocol.

---

## 3. Schema Design

### 3.1 Package-Level Benchmark Package Registration in `nexus.yaml`

```yaml
package:
  name: "terratorch"

  benchmark_packages:
    - requirement_specifier: "./packages/terratorch/benchmark_packages/segmentation-benchmarks"
      experiments:
        - "local-segmentation-eval"
        - "local-boundary-eval"

    - requirement_specifier: "https://github.com/example-org/example-benchmarks"
      experiments:
        - "leaderboard-baseline"

    - requirement_specifier: "example-benchmark-package"
      experiments:
        - "packaged-baseline"
```

**Fields:**

- `package.benchmark_packages` is optional
- each entry in `benchmark_packages` identifies one benchmark package source
- `requirement_specifier` is a valid Python package requirement specifier string
  to be used for installing the benchmark experiments. It may be a Python
  package name, a URL to a Python package or source repository, or a local path
  to a Python package within the `./packages` folder in the Nexus project root.
- `experiments` lists the experiment identifiers exposed from that package and
  made available to models in the Nexus package

### 3.2 Package-Level Benchmark Instances in `benchmark_instances/`

A Nexus package may define a top-level `benchmark_instances/` folder. That
folder contains one subfolder per package-level benchmark instance. Each
benchmark instance folder must contain a file named `space.yaml`.

These package-level benchmark instances are intended for baseline experiments
that live at the top level of the Nexus package rather than under a specific
model.

Example structure:

```text
benchmark_instances/
└── flood-baseline-test/
    └── space.yaml
```

### 3.3 Model-Level Benchmark Instances in `models/<model-name>/benchmark_instances/`

Each model may also define a `benchmark_instances/` folder. That folder contains
one subfolder per benchmark instance. Each benchmark instance folder must
contain a file named `space.yaml`.

The `space.yaml` file must contain a full ADO discoveryspace definition for the
specific experiment the benchmark instance wants to use.

Example structure:

```text
models/<model-name>/
└── benchmark_instances/
    └── flood-segmentation-test/
        └── space.yaml
```

Example `space.yaml`:

```yaml
entitySpace:
  - identifier: dataset
    propertyDomain:
      values: ["sen1floods11"]
  - identifier: split
    propertyDomain:
      values: ["test"]

experiments:
  - actuatorIdentifier: custom_experiments
    experimentIdentifier: local-segmentation-eval
```

**Fields and expectations:**

- package-level `benchmark_instances/` is optional
- model-level `benchmark_instances/` is optional
- each subfolder name identifies one benchmark instance in its enclosing scope
- each benchmark instance subfolder must contain `space.yaml`
- each `space.yaml` must define a complete ADO discoveryspace for the benchmark
  instance
- model-level benchmark instances implicitly target the enclosing model
- package-level benchmark instances are used for baseline experiments defined at
  the top level of the Nexus package
- the experiment referenced in `space.yaml` must be one of the experiment
  identifiers registered through `package.benchmark_packages`

For reference on the expected discoveryspace structure, see
[Using your custom experiment in a discoveryspace](https://ibm.github.io/ado/actuators/creating-custom-experiments/#using-your-custom-experiment-in-a-discoveryspace).

This structure supports the requirement language in which a benchmark is either
a fixed benchmark experiment or a workload plus a parameterizable benchmark
experiment. Also, we assume that any dataset to be used for the benchmark is
fetched or provided with the experiment itself.

---

## 4. Validation Considerations

### 4.1 Package-Level Validation

Validation should eventually check that:

1. each benchmark package registration provides a `requirement_specifier`
2. each benchmark package registration provides an `experiments` list
3. experiment identifiers are unique within the package
4. each local `requirement_specifier` resolves to exactly one Python package
   within [`./packages`](packages/)
5. each referenced local benchmark package follows the ADO custom experiment
   template
6. each URL-valued `requirement_specifier` points to a valid Python package or
   repository location
7. each package-name-valued `requirement_specifier` is a valid Python package
   requirement target
8. all referenced requirement specifiers resolve to valid benchmark experiments
   that follow the ADO custom experiment format

### 4.2 Benchmark Instance Validation

Validation should eventually check that:

1. every package-level and model-level benchmark instance folder contains a
   `space.yaml` file
2. each `space.yaml` contains a valid ADO discoveryspace definition
3. each `space.yaml` references an experiment identifier registered in the same
   package
4. package-level benchmark instances define their benchmark target explicitly
   where needed, since they are not enclosed by a model
5. duplicate benchmark instance names are rejected if uniqueness is desired
6. each `space.yaml` contains a valid ADO discoveryspace definition
7. each `space.yaml` references an experiment identifier registered in the same
   package
8. package-level benchmark instances define their benchmark target explicitly
   where needed, since they are not enclosed by a model
9. duplicate benchmark instance names are rejected if uniqueness is desired

---

## 5. Benchmarks discovery

### 5.1 Experiments discovery

The medatata available in each Nexus package (`nexus.yaml`) can be used to list
all the experiment available in the package, without installing the benchmark
packages into the current environment. Also, this enables listing experiments
that are distributed via a remote repository, that would not be discoverable by
just installing the benchmark. package and the nexus package itself.

### 5.2 Benchmarks discovery

Similarly to experiments, benchmarks can be discovered from the top folder of a
Nexus package by scanning the package-level `benchmark_instances/` folder for
baseline experiments and scanning the
[`models/`](../../packages/terratorch/models/) tree for model-level
`benchmark_instances/` folders. This supports listing both package-level
baseline benchmark instances and model-specific benchmark instances without
requiring a separate benchmark index.

### 5.2 Fetching details about an experiment or a benchmark

Fetching details on experiments and benchmarks, such as the expected input,
metrics exported, etc. can be obtained with a combination of the `nexus` cli,
used for listing, and the `ado` cli that after installing the relevant benchmark
packages can be used for getting full details on the experiment or benchmark.
