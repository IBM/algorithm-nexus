<!--
Copyright IBM Corporation 2026
SPDX-License-Identifier: Apache-2.0
-->

# How to add a benchmark experiment

This guide shows you how to register a benchmark experiment in Algorithm Nexus.

A **benchmark experiment** is an `ado` custom experiment, distributed as a Python
package, that evaluates a target (an algorithm or model) and collects
measurements. Registering the python package in Algorithm Nexus
makes all the experiments it contains available to submissions.

The steps below register a graph-coloring experiment whose package is already
on PyPI. After that walk-through, [Alternatives](#alternatives) covers GitHub
URLs, packages that expose several experiments, and authoring a new package.

To register the problem this experiment relates to, see
[How to add a benchmark problem and instance](./add_benchmark_problem.md).

## Prerequisites

Work from a local checkout of your Algorithm Nexus fork with the CLI extra
installed:

```bash
cd algorithm-nexus
uv sync --group dev --extra cli
git checkout -b add-rlx-coloring-experiment
```

The following assumes a python package containing the experiment
is published on PyPI (or GitHub; see
[Point the specifier at a GitHub URL](#point-the-specifier-at-a-github-url)).

## 1. Create the experiment folder

Create the experiment folder and write `experiment_package.yaml`. This file
names the Python package and the experiment identifiers it exposes.

```bash
mkdir -p experiments/rlx_coloring
```

Create `experiments/rlx_coloring/experiment_package.yaml`:

```yaml
experiment_package:
    requirement_specifier: "rlx-coloring"
    experiments:
        - rlx_coloring
```

`requirement_specifier` is a PyPI package name (optionally with a version
constraint) or a GitHub URL. The `experiments` list is the set of experiment
ids submissions will reference.

The full field list is in
[Benchmark Experiments and Submissions](../../design/benchmarking/benchmark_experiments_and_submissions.md#31-experiment-package-registration-in-experiment_packageyaml).

You now have:

```text
experiments/rlx_coloring/
└── experiment_package.yaml
```

## 2. Validate

```bash
uv run nexus validate experiments --experiment rlx_coloring
```

A successful run lists the experiment with status `success`. The registration is
ready to commit.

## 3. Open a pull request

```bash
git add experiments/rlx_coloring
git commit -s -m "feat(benchmark): Add rlx_coloring experiment"
git push origin add-rlx-coloring-experiment
```

Open a pull request from your fork to the Algorithm Nexus main branch.

To map this experiment to a benchmark instance, continue with
[How to bind an experiment to a benchmark instance](./add_instance_binding.md).
To apply this experiment to a target and instance, continue with
[How to add a benchmark submission](./add_benchmark_submission.md).

---

## Alternatives

### Point the specifier at a GitHub URL

To register a package hosted on GitHub, set `requirement_specifier` to the
repository URL:

```yaml
experiment_package:
    requirement_specifier: "https://github.com/<org>/<experiment-package-repo>"
    experiments:
        - rlx_coloring
```

Then validate as in [step 2](#2-validate).

### Declare several experiment ids from one package

To expose more than one experiment from the same package, list each identifier:

```yaml
experiment_package:
    requirement_specifier: "sorting-benchmarks>=1.0.0"
    experiments:
        - bubble_sort
        - merge_sort
        - quick_sort
```

Each id in the list is available to submissions under this experiment folder.

### Author a new experiment package

To create the Python package itself, follow the
[ado custom experiment template](https://ibm.github.io/ado/actuators/creating-custom-experiments/),
publish the package on PyPI or GitHub, then continue from
[step 1](#1-create-the-experiment-folder).

### List registered experiments

To see which experiments Algorithm Nexus already registers:

```bash
uv run nexus list benchmark-experiments
```

## See also

- [Benchmark Experiments and Submissions](../../design/benchmarking/benchmark_experiments_and_submissions.md)
  — schema and folder layout
- [How to bind an experiment to a benchmark instance](./add_instance_binding.md)
- [How to add a benchmark submission](./add_benchmark_submission.md)
- [How to add a benchmark problem and instance](./add_benchmark_problem.md)
- [`nexus validate experiments`](../../getting-started/cli-reference.md#nexus-validate-experiments)
- [`nexus list benchmark-experiments`](../../getting-started/cli-reference.md#nexus-list-benchmark-experiments)
