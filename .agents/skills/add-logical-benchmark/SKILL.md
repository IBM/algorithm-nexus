---
name: add-logical-benchmark
description: >
  Step-by-step guidance for adding a new problem class (logical benchmark) to
  Algorithm Nexus. Creates benchmark.yaml, validates it, and opens a pull
  request. Use when the user wants to add a new benchmark problem, problem
  class, or logical-benchmark to Algorithm Nexus.
---

# Adding a Logical Benchmark (Problem Class) to Algorithm Nexus

## Prerequisites

The following information is required before starting. If any required item is
missing, ask the user before proceeding.

- `benchmark_id` (string, required): Snake-case unique identifier for the
  problem, e.g. `graph_coloring`. This becomes both the folder name and the
  `benchmarkIdentifier` value.
- `title` (string, optional): Short human-readable display name.
- `description` (string, required): What the benchmark evaluates — algorithm
  class, inputs, goal.
- `problem_properties` (list, required): The properties that characterise the
  *abstract* problem — complexity parameters, size dimensions, structural
  settings. Each property needs an `identifier` and an optional human-readable
  `description`. A `propertyDomain` is optional (see Step 2).
- `metrics` (list, optional): Canonical output metric names that every
  experiment binding will report under. Each metric has an `identifier` and an
  optional `metadata.description` — use it to explain what the metric measures
  and its unit, rather than leaving that detail to the README.
- `ranking_metric` and `ranking_order` (`asc` or `desc`, optional): Which
  metric drives the leaderboard and in which direction.
- `owner` (string, optional): GitHub team or username, e.g. `@my-team`.

If the user has not provided enough information to fill in all required fields,
ask for it before creating any files.

## Steps

1. **Gather information** — confirm all required prerequisite information.
2. **Create the problem definition** — write `benchmarks/<benchmark_id>/benchmark.yaml`.
3. **Write the README** — write `benchmarks/<benchmark_id>/README.md`.
4. **Validate** — run `uv run nexus validate logical-benchmarks` and fix any errors.
5. **Commit, push, and open a PR** — commit all changes to a new branch and open a pull request.

---

## Step 1 — Gather Information

Before writing any file, confirm all prerequisite information is available.
Inspect the workspace to check whether a benchmark with the same identifier
already exists under `benchmarks/`. If it does, stop and inform the user.

### Distinguish problem properties from instance artifacts

Before finalising `problemProperties`, review each proposed property with the
following question:

> **Does this property describe the abstract problem (its size, structure, or
> parameters), or does it represent a pre-generated input file that an
> algorithm will consume directly?**

- **Scalar/categorical parameters** that characterise problem complexity (e.g.
  number of nodes, graph family, budget, risk-aversion weight) → declare as
  `problemProperties` in `benchmark.yaml`.
- **Files or datasets** that are derived from those parameters and fed directly
  to algorithms (e.g. a graph in DIMACS format, an MPS model file, a JSON
  representation) → these are **instance artifacts**, not problem properties.
  They belong in `instanceArtifacts` on the instance, not in `problemProperties`
  on the benchmark. Do not add them to `problemProperties`.

If the user describes a property that is clearly a file input, flag it and
explain that it should be an instance artifact instead. Only proceed with
writing `benchmark.yaml` once this distinction has been applied.

---

## Step 2 — Create the Problem Definition

Create the benchmark folder and `benchmark.yaml`:

```bash
mkdir -p benchmarks/<benchmark_id>
```

Write `benchmarks/<benchmark_id>/benchmark.yaml` with the following structure,
including the IBM copyright header:

```yaml
# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

benchmarkIdentifier: <benchmark_id>
title: <title>
description: >
  <description>
problemProperties:
  - identifier: <property_id>
    metadata:
      description: <property description>
    # propertyDomain is optional — omit it when the property is open-ended
    propertyDomain:
      variableType: <DOMAIN_TYPE>
      values: [...]          # for CATEGORICAL_VARIABLE_TYPE or DISCRETE_VARIABLE_TYPE
metrics:
  - identifier: <metric_id>
    metadata:
      description: <what this metric measures and its unit>
ranking:
  metric: <metric_id>
  order: asc   # or desc
owner: "<owner>"
```

Only include `title`, `metrics`, `ranking`, and `owner` if the information is
available. Only include `propertyDomain` when it adds meaningful constraint or
documentation value; omit it for open-ended properties.

**Property domain types** — choose the right `variableType` when a domain is
declared:

| User intent | `variableType` | Extra fields |
| --- | --- | --- |
| A fixed set of named categories | `CATEGORICAL_VARIABLE_TYPE` | `values: [a, b, c]` |
| A fixed set of integer counts | `DISCRETE_VARIABLE_TYPE` | `values: [10, 50, 100]` |
| Any real number | `CONTINUOUS_VARIABLE_TYPE` | *(none, or `domainRange: [lo, hi]`)* |
| No constraint / open-ended | omit `propertyDomain` entirely | — |

---

## Step 3 — Write the README

Create `benchmarks/<benchmark_id>/README.md` alongside `benchmark.yaml`. The
README gives a human-readable problem statement that is not constrained by YAML
syntax. It should cover:

- **Problem formulation** — what is being optimised or evaluated, objective,
  constraints.
- **Instance structure** — what the problem properties represent and how they
  combine to define a concrete instance.
- **References** — papers, datasets, or external benchmark suites the problem
  is drawn from (if any).

Write the README from the information gathered in Step 1. If the user has not
provided enough detail to write a meaningful formulation, ask before proceeding.

---

## Step 4 — Validate

Run the validation command from the repository root:

```bash
uv run nexus validate logical-benchmarks
```

To validate only the new benchmark:

```bash
uv run nexus validate logical-benchmarks --file benchmarks/<benchmark_id>
```

A successful run prints `success` for the benchmark folder. If validation fails:

1. Read the error messages carefully — they are usually Pydantic schema errors
   or missing required fields.
2. Fix `benchmark.yaml`.
3. Re-run validation until all errors are resolved.

Do not proceed to the PR step until validation passes with no errors.

---

## Step 5 — Commit, Push, and Open a PR

Stage and commit everything:

```bash
git checkout -b add-<benchmark_id>-benchmark
git add benchmarks/<benchmark_id>
git commit -s -m "feat(benchmark): Add <benchmark_id> problem class"
git push origin add-<benchmark_id>-benchmark
```

Then open a pull request from the new branch to the Algorithm Nexus main branch.
Use the `create_pr_workflow` if available to generate the PR description
automatically.
