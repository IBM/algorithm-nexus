# Benchmark Integration Design for Algorithm Nexus

## Executive Summary

This document defines how benchmarking metadata is integrated into Algorithm
Nexus packages. The design keeps benchmark experiment registration at the Nexus
package level and benchmark specification in a separate per-model
[`benchmarks.yaml`](../../packages/terratorch/models/prithvi/) file.

**Key Design Decisions:**

1. [`nexus.yaml`](../../packages/terratorch/nexus.yaml) registers the benchmark
   experiments available to the package
2. [`model.yaml`](../../packages/terratorch/models/prithvi/model.yaml) remains
   focused on model metadata
3. [`benchmarks.yaml`](../../packages/terratorch/models/prithvi/) specifies the
   benchmarks a model should use
4. The package-level [`benchmarks/`](../../packages/terratorch/) folder is the
   standard local benchmark Python package and follows the ADO custom experiment
   pattern
5. Benchmark experiment registrations in
   [`nexus.yaml`](../../packages/terratorch/nexus.yaml) use
   `distribution: package`, `local`, or `url`
6. Every registration must resolve to an ADO custom experiment that follows the
   standardized benchmark packaging protocol
7. The benchmark target is implicit from the enclosing model definition
8. Markdown documentation is updated before any schema, template, or validation
   implementation work

---

## 1. Requirements Analysis and Mapping

### 1.1 Benchmark System Components

Based on the [benchmark requirements](../requirements/benchmark.md), the system
has four core concepts that must be linked together by package metadata:

- **Benchmark experiment**
  - a script, harness, or workflow that executes a benchmark target on a
    workload and collects measurements
  - in this design, benchmark experiments are registered at package level in
    [`nexus.yaml`](../../packages/terratorch/nexus.yaml)
  - All benchmark experiments follow the
    [ADO custom experiment template](https://ibm.github.io/ado/actuators/creating-custom-experiments/)

- **Workload**
  - the inputs, data, and execution pattern exercised by a benchmark driver
  - in this design, workload or experiment parameter values are specified in
    [`benchmarks.yaml`](../../packages/terratorch/models/prithvi/)

- **Benchmark target**
  - the model or algorithm being evaluated
  - in this design, the benchmark target is implicit from the enclosing model
    definition in
    [`model.yaml`](../../packages/terratorch/models/prithvi/model.yaml)

- **Benchmark**
  - either a fixed benchmark experiment or a workload plus a parameterizable
    benchmark experiment
  - in this design, a model benchmark entry references a registered benchmark
    experiment and provides parameter values where needed

This follows the requirements terminology that a benchmark instance is formed
from a benchmark target together with a benchmark, where the benchmark is
represented as either a fixed benchmark experiment or a workload plus a
parameterizable benchmark experiment.

### 1.2 Responsibilities by File and Directory

| Location                                                                   | Responsibility                                                                                                  |
| -------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| [`nexus.yaml`](../../packages/terratorch/nexus.yaml)                       | Declares named benchmark experiments available to models in the package                                         |
| package-level [`benchmarks/`](../../packages/terratorch/) folder           | Local benchmark Python package following the ADO custom experiment pattern and exposing one or more experiments |
| [`model.yaml`](../../packages/terratorch/models/prithvi/model.yaml)        | Declares model metadata                                                                                         |
| model-level [`benchmarks.yaml`](../../packages/terratorch/models/prithvi/) | Declares the benchmark specification for a model by referencing a registered experiment and parameter data      |

### 1.3 Requirements to Design Mapping

| Requirement | Design interpretation                                                                                                                                                                                                |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| REQ 1.2     | Benchmark experiments are distributed as Python packages, including the local package-level [`benchmarks/`](../../packages/terratorch/) Python package and remote repositories addressed by URL                      |
| REQ 2.1     | Benchmark experiment registration happens in [`nexus.yaml`](../../packages/terratorch/nexus.yaml)                                                                                                                    |
| REQ 2.3     | Benchmark registration for a model happens in [`benchmarks.yaml`](../../packages/terratorch/models/prithvi/), where a benchmark is specified as a registered experiment plus parameter values when needed            |
| REQ 3.1     | A model benchmark entry specifies the benchmark to use for the model in the manner defined by REQ 2.3                                                                                                                |
| REQ 3.2     | New package-provided benchmark experiments are normally added under the package-level [`benchmarks/`](../../packages/terratorch/) folder and then registered in [`nexus.yaml`](../../packages/terratorch/nexus.yaml) |
| REQ 3.3     | Models may reuse any experiment registered by the package, whether the experiment is provided through installed package code, the local benchmark package, or remote repositories                                    |

---

## 2. Folder Structure Design

### 2.1 Complete Nexus Package Structure

```text
packages/
└── <nexus-package-name>/
    ├── nexus.yaml
    ├── skills/
    ├── benchmarks/                     # Local benchmark Python package
    │   ├── pyproject.toml
    │   ├── src/
    └── models/
        └── <model-name>/
            ├── model.yaml
            ├── benchmarks.yaml
            └── usage.md
```

### 2.2 Ownership Model

The canonical benchmark metadata is split across two files:

- [`nexus.yaml`](../../packages/terratorch/nexus.yaml)
  - registers the benchmark experiments a package makes available
  - records how each registered benchmark experiment is distributed
  - identifies which ADO custom experiment the registration refers to
- [`benchmarks.yaml`](../../packages/terratorch/models/prithvi/)
  - records which benchmarks a model should use
  - carries the parameter details for each model benchmark entry

The package-level [`benchmarks/`](../../packages/terratorch/) directory is the
local benchmark Python package that lives with the Nexus package. It follows the
ADO custom experiment pattern and may expose multiple ADO custom benchmark
experiments.

### 2.3 Benchmark Experiment Distribution Modes

A package-level benchmark experiment registration uses exactly one distribution
mode:

1. **`distribution: package`**
   - the Nexus algorithm package itself installs and exposes one or more ADO
     custom benchmark experiments
   - no additional location field is required

2. **`distribution: local`**
   - the experiment comes from the local package-level
     [`benchmarks/`](../../packages/terratorch/) Python package
   - that package must follow the ADO custom experiment format
   - developers may add as many benchmark experiments as needed inside that
     package
   - no additional location field is required

3. **`distribution: url`**
   - the registration points to a remote repository URL
   - that repository must follow the ADO custom experiment format
   - `url` is required

In all three distribution modes, the experiment name identifies the ADO custom
experiment installed through the relevant distribution mode.

---

## 3. Schema Design

### 3.1 Package-Level Benchmark Experiment Registration in [`nexus.yaml`](../../packages/terratorch/nexus.yaml)

```yaml
package:
  name: "terratorch"

  benchmark_experiments:
    - name: "native-flood-eval"
      distribution: "package"

    - name: "local-segmentation-eval"
      distribution: "local"

    - name: "leaderboard-baseline"
      distribution: "url"
      url: "https://github.com/example-org/ado-leaderboard-benchmarks"
```

**Fields:**

- `package.benchmark_experiments` is optional
- `name` identifies the ADO custom experiment exposed through that distribution
- `distribution` is one of `package`, `local`, or `url`
- `url` is required only when `distribution` is `url`

For distribution `local`, the source location is the package-level
[`benchmarks/`](../../packages/terratorch/) Python package. That package must
follow the ADO custom experiment format and may expose multiple experiments. For
both `local` and `url`, the referenced material must follow the ADO custom
experiment format and the standardized benchmark packaging protocol. For
`package`, the referenced experiment must be exposed by the installed Algorithm
Stack Python package itself.

### 3.2 Model-Level Benchmark Specification in [`benchmarks.yaml`](../../packages/terratorch/models/prithvi/)

```yaml
benchmarks:
  - name: "flood-segmentation-test"
    experiment: "local-segmentation-eval"
    parameters:
      dataset: "sen1floods11"
      split: "test"
      metrics:
        - "iou"
        - "f1_score"
```

**Fields:**

- `benchmarks` is optional
- `name` identifies the benchmark entry for the model
- `experiment` references one package-registered benchmark experiment by name
- `parameters` provides the experiment parameter values for that benchmark use

This structure supports the requirement language in which a benchmark is either
a fixed benchmark experiment or a workload plus a parameterizable benchmark
experiment. Also, we assume that any dataset to be used for the benchmark is
fetched or provided with the experiment itself.

### 3.3 Benchmark Target Handling

The benchmark target should be implicit from the enclosing model definition in
[`model.yaml`](../../packages/terratorch/models/prithvi/model.yaml).

This keeps the benchmark entry concise and avoids duplicating target metadata
that is already available from model metadata. By default we assume the target
model is identified by its unique Hugging Face model ID.

---

## 4. Validation Considerations

### 4.1 Package-Level Validation

Validation should eventually check that:

1. each benchmark experiment registration has a unique name
2. each registration uses exactly one supported `distribution`
3. `experiment` is always present
4. `url` is present only when `distribution` is `url`
5. `distribution: local` resolves through package-local benchmark content
6. `distribution: package` refers to an experiment exposed by the installed
   package
7. all referenced distributions resolve to a valid benchmark experiment that
   follows the ADO custom experiment format

### 4.2 Model-Level Validation

Validation should eventually check that:

1. every benchmark entry in
   [`benchmarks.yaml`](../../packages/terratorch/models/prithvi/) references an
   experiment registered in the same package
2. `parameters` content is a valid mapping
3. duplicate benchmark names are rejected if uniqueness is desired

---

## 5. Benchmarks discovery

### 5.1 Experiments discovery

The medatata available in each Nexus package (`nexus.yaml`) can be used to list
all the experiment available in the package, without installing the benchmark
packages into the current environment. Also, this enables listing experiments
that are distributed via a remote repository, that would not be discoverable by
just installing the benchmark. package and the nexus package itself.

### 5.2 Benchmarks discovery

Similarly to experiments, benchmarks can be discovered using the metadata in the
`benchmarks.yaml` file available for each model.

### 5.2 Fetching details about an experiment or a benchmark

Fetching details on experiments and benchmarks, such as the expected input,
metrics exported, etc. can be obtained with a combination of the `nexus` cli,
used for listing, and the `ado` cli that after installing the relevant benchmark
packages can be used for getting full details on the experiment or benchmark.
