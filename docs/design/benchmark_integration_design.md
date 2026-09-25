# Benchmark Integration Design for Algorithm Nexus

## Executive Summary

This document defines how benchmarking metadata is integrated into Algorithm
Nexus. Benchmark experiment registration and benchmark submissions live under
the top-level `experiments/` directory, entirely separate from `packages/`.

**Key Design Decisions:**

1. `experiments/<name>/experiment_package.yaml` registers a single benchmark
   experiment package and lists the experiment identifiers it exposes
2. `experiments/<name>/submissions/<submission>/space.yaml` is the
   per-submission ADO discoveryspace definition
3. `model.yaml` remains focused on model metadata — it carries no benchmark
   references
4. `nexus.yaml` carries only Nexus package identity (`name`) — benchmark package
   registrations have been removed from it
5. Experiment package `requirement_specifier` values must be a PyPI package name
   or a GitHub URL — local paths are not allowed
6. Every experiment package must follow the standardized ADO custom experiment
   packaging protocol
7. The benchmark target is the experiment property that represents the algorithm
   or model being evaluated
8. Markdown documentation is updated before any schema, template, or validation
   implementation work

---

## 1. Requirements Analysis and Mapping

### 1.1 Benchmark System Components

Based on the [benchmark requirements](../requirements/benchmark.md), the system
has five core concepts that must be linked together by the experiment metadata:

- **Benchmark experiment**
    - a script, harness, or workflow that executes a benchmark target on a
      benchmark instance and collects measurements
    - in this design, experiments are declared in
      `experiments/<name>/experiment_package.yaml`
    - All benchmark experiments follow the
      [ADO custom experiment template](https://ibm.github.io/ado/actuators/creating-custom-experiments/)

- **Benchmark instance**
    - the inputs, data, and execution pattern exercised by a benchmark driver
    - in this design, benchmark instance parameter values are specified in
      per-submission `space.yaml` files under
      `experiments/<name>/submissions/<submission>/`

- **Benchmark target**
    - the model or algorithm being evaluated
    - the benchmark target is the experiment property that identifies which
      algorithm or model is under evaluation

- **Benchmark**
    - either a fixed benchmark experiment or a benchmark instance plus a
      parameterizable benchmark experiment
    - in this design, a benchmark submission references a declared benchmark
      experiment and provides parameter values where needed

- **Benchmark submission**
    - a concrete benchmark definition for a specific use case
    - in this design, each benchmark submission is one folder under
      `experiments/<name>/submissions/`, containing a `space.yaml` file with the
      full ADO discoveryspace definition
    - the benchmark submission binds together the selected experiment and the
      benchmark-instance-specific parameter values used for execution

### 1.2 Responsibilities by File and Directory

| Location                                                 | Responsibility                                                                                 |
| -------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `experiments/<name>/experiment_package.yaml`             | Declares the experiment package (PyPI or GitHub) and the experiment identifiers it exposes     |
| `experiments/<name>/bindings/`                           | Optional benchmark binding YAML files that map experiment outputs to logical benchmark metrics |
| `experiments/<name>/submissions/<submission>/space.yaml` | Full ADO discoveryspace definition for one benchmark submission                                |
| `packages/<pkg>/nexus.yaml`                              | Declares Nexus package identity (`name`) only — no benchmark package references                |
| `packages/<pkg>/models/<model>/model.yaml`               | Declares model metadata — no benchmark references                                              |

### 1.3 Requirements to Design Mapping

| Requirement | Design interpretation                                                                                                                                                   |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| REQ 1.2     | Benchmark experiments are distributed as Python packages published on PyPI or GitHub — local packages are not supported                                                 |
| REQ 2.1     | Benchmark package registration happens in `experiments/<name>/experiment_package.yaml`, including the `requirement_specifier` and the experiment identifiers it exposes |
| REQ 2.3     | Benchmark submissions live in `experiments/<name>/submissions/`, where each submission folder contains a `space.yaml` discoveryspace definition                         |
| REQ 3.1     | A benchmark entry specifies the benchmark to use through a dedicated discoveryspace definition in the relevant `experiments/<name>/submissions/<submission>/` folder    |
| REQ 3.2     | New benchmark experiments are added as published Python packages (PyPI or GitHub) and declared in a new `experiments/<name>/experiment_package.yaml`                    |
| REQ 3.3     | Multiple submissions under the same experiment can reference any experiment identifier declared in `experiment_package.yaml`                                            |

---

## 2. Folder Structure Design

### 2.1 Complete Experiments Structure

```text
experiments/
└── <experiment-name>/
    ├── experiment_package.yaml       # Required: experiment package specifier + experiment IDs
    ├── bindings/                     # Optional: benchmark binding YAML files
    │   └── <binding-name>.yaml
    └── submissions/                  # Optional: benchmark submissions
        ├── <submission-a>/
        │   └── space.yaml            # Required per submission
        └── <submission-b>/
            └── space.yaml
```

### 2.2 Ownership Model

The canonical benchmark metadata is split across two locations within each
experiment folder:

- `experiments/<name>/experiment_package.yaml`
    - registers the package that provides benchmark experiments
    - records a single `requirement_specifier` (PyPI name or GitHub URL)
    - records the experiment identifiers exposed by that package

- `experiments/<name>/submissions/`
    - records which benchmark submissions belong to this experiment
    - stores one folder per benchmark submission
    - carries a `space.yaml` ADO discoveryspace definition for each submission

- `experiments/<name>/bindings/`
    - optional; contains benchmark binding YAML files mapping experiment outputs
      to logical benchmark metrics

### 2.3 Experiment Package Specifiers

An experiment package specifier uses:

- a `requirement_specifier` to identify how the experiment package should be
  resolved
- an `experiments` list to declare which experiment identifiers from that
  package are made available

The `requirement_specifier` must be one of:

1. a Python package name published on PyPI (optionally with a version
   constraint)
2. a GitHub repository URL (HTTPS or `git+` prefixed)

Local paths are explicitly **not** allowed. The package must be publicly
accessible from either PyPI or a GitHub repository.

In all cases, the referenced package must follow the ADO custom experiment
format and the standardized benchmark packaging protocol.

---

## 3. Schema Design

### 3.1 Experiment Package Registration in `experiment_package.yaml`

```yaml
experiment_package:
    requirement_specifier: "sorting-benchmarks>=1.0.0" # PyPI package name
    experiments:
        - bubble_sort
        - merge_sort
        - quick_sort
```

GitHub URL example:

```yaml
experiment_package:
    requirement_specifier: "https://github.com/example-org/example-benchmarks"
    experiments:
        - leaderboard-baseline
```

**Fields:**

- `experiment_package.requirement_specifier` — required; PyPI package name or
  GitHub URL (local paths are rejected by schema validation)
- `experiment_package.experiments` — required; non-empty list of experiment
  identifiers exposed by the package

### 3.2 Benchmark Submissions in `submissions/`

An experiment folder may define a `submissions/` directory. That folder contains
one subfolder per benchmark submission. Each benchmark submission folder must
contain a file named `space.yaml`.

Example structure:

```text
submissions/
└── flood-baseline-test/
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

- `submissions/` is optional
- each subfolder name identifies one benchmark submission
- each benchmark submission subfolder must contain `space.yaml`
- each `space.yaml` must define a complete ADO discoveryspace for the benchmark
  submission
- the experiment referenced in `space.yaml` must be one of the experiment
  identifiers declared in the sibling `experiment_package.yaml`

For reference on the expected discoveryspace structure, see
[Using your custom experiment in a discoveryspace](https://ibm.github.io/ado/actuators/creating-custom-experiments/#using-your-custom-experiment-in-a-discoveryspace).

---

## 4. Validation Considerations

### 4.1 Experiment-Level Validation

Validation checks that:

1. `experiment_package.yaml` is present in the experiment folder
2. `requirement_specifier` is a valid PyPI name or GitHub URL (local paths are
   rejected)
3. `experiments` list is non-empty
4. extra fields are forbidden (`extra="forbid"`)

### 4.2 Benchmark Submission Validation

Validation checks that:

1. every benchmark submission folder under `submissions/` contains a
   `space.yaml`
2. each `space.yaml` contains a valid ADO discoveryspace definition
3. each `space.yaml` references experiment identifiers declared in
   `experiment_package.yaml`

---

## 5. Benchmarks Discovery

### 5.1 Experiments Discovery

The metadata available in each experiment folder (`experiment_package.yaml`) can
be used to list all experiments available without installing the experiment
package into the current environment. This also enables listing experiments
distributed via a remote repository that would not be discoverable by just
installing the package.

### 5.2 Benchmarks Discovery

Benchmarks can be discovered by scanning the top-level `experiments/` directory.
Each `experiments/<name>/submissions/` folder lists the benchmark submissions
for that experiment. This supports listing all benchmark submissions without
requiring a separate benchmark index.

### 5.3 Fetching Details About an Experiment or a Benchmark

Fetching details on experiments and benchmarks — such as expected input, metrics
exported, etc. — can be obtained with a combination of the `nexus` CLI for
listing and the `ado` CLI for full experiment details after installing the
relevant experiment package.
