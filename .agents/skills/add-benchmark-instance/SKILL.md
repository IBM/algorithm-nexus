---
name: add-benchmark-instance
description: >
  Step-by-step guidance for adding a new problem instance (benchmark instance)
  to an existing logical benchmark in Algorithm Nexus. Creates instance.yaml
  (and optional artifact files), validates the instance definition, and opens a
  pull request. Use when the user wants to add a new problem instance, benchmark
  instance, or concrete instance to Algorithm Nexus.
---

# Adding a Benchmark Instance to Algorithm Nexus

## Prerequisites

The following information is required before creating a benchmark instance:

- **Target logical benchmark (`benchmark_id`)**: The snake-case identifier of the existing problem class
  (e.g. `graph_coloring`, `portfolio_optimization`). The benchmark definition must already exist at
  `benchmarks/<benchmark_id>/benchmark.yaml`.
    > **Note**: If the target problem does not exist yet, use the skill in
    > `.agents/skills/add-logical-benchmark` to add the logical benchmark first before proceeding.
- `instance_id` (string, required): Unique identifier for this instance, e.g. `erdos_renyi_50_02` or
  `100nodes_random3regular`. This becomes the folder name under
  `benchmarks/<benchmark_id>/instances/<instance_id>/` and the `instanceIdentifier` field value.
- `description` (string, optional/recommended): Human-readable description of this concrete instance.
- `problem_property_values` (list of PropertyValue, required if `problemProperties` are defined in
  `benchmark.yaml`): Concrete values corresponding to the problem properties defined in
  `benchmarks/<benchmark_id>/benchmark.yaml`. Each entry specifies:
    - `property.identifier`: The identifier matching a `problemProperty` from `benchmark.yaml`.
    - `value`: The concrete value for this instance (e.g. integer, float, string).
- `instance_artifacts` (list of InstanceArtifact, optional): If the instance provides pre-generated
  input files (such as graphs, datasets, or mathematical models) that algorithms consume directly:
    - `property.identifier`: Identifier for the artifact slot (e.g. `graph`, `model`, `market_data`).
    - `artifactsLocation`: Subfolder name relative to the instance directory containing the files.

If the user has not provided enough information, ask for the missing details before creating files.

## Steps

1. **Gather information & verify problem existence** — verify the logical benchmark exists and confirm
   all instance property values and artifacts.
2. **Create the instance definition** — write
   `benchmarks/<benchmark_id>/instances/<instance_id>/instance.yaml` and create artifact files if applicable.
3. **Validate** — run `uv run nexus validate logical-benchmarks` and resolve any errors.
4. **Commit, push, and open a PR** — commit changes to a new branch and open a pull request.

---

## Step 1 — Gather Information & Verify Problem Existence

1. Verify that the parent logical benchmark exists at `benchmarks/<benchmark_id>/benchmark.yaml`.
   - If `benchmark.yaml` does not exist or the user has not specified a problem, stop and guide the
     user to create the benchmark problem first using the skill in `.agents/skills/add-logical-benchmark`.
2. Inspect `benchmarks/<benchmark_id>/benchmark.yaml` to retrieve the declared `problemProperties`.
3. Check whether an instance with the same `instance_id` already exists under
   `benchmarks/<benchmark_id>/instances/<instance_id>/`. If it already exists, stop and inform the user.
4. Distinguish between problem properties and instance artifacts:
   - **Problem property values** define the parameters of the problem (e.g. `num_vertices: 50`,
     `edge_density: 0.2`) and must match properties declared in `benchmark.yaml`.
   - **Instance artifacts** are concrete input files (e.g. `.dimacs`, `.mps`, `.json`, `.csv`) stored
     in a subfolder and referenced in `instanceArtifacts`. Artifact identifiers do not need to be
     listed in `problemProperties`.

---

## Step 2 — Create the Instance Definition

Create the instance folder:

```bash
mkdir -p benchmarks/<benchmark_id>/instances/<instance_id>
```

Write `benchmarks/<benchmark_id>/instances/<instance_id>/instance.yaml` following the schema below,
including the IBM copyright header:

```yaml
# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0

instanceIdentifier: <instance_id>
benchmarkIdentifier: <benchmark_id>
description: >
  <description>

problemPropertyValues:
  - property:
      identifier: <property_id_1>
    value: <value_1>
  - property:
      identifier: <property_id_2>
    value: <value_2>

# (Optional) Include instanceArtifacts if the instance ships with input files
instanceArtifacts:
  - property:
      identifier: <artifact_property_name>
    artifactsLocation: <artifacts_subfolder>
```

### Artifact Files (Optional)

If the instance includes artifact files:

1. Create the subfolder under the instance directory:

   ```bash
   mkdir -p benchmarks/<benchmark_id>/instances/<instance_id>/<artifacts_subfolder>
   ```

2. Place or generate the required artifact files in that subfolder.
3. Ensure `artifactsLocation` in `instance.yaml` matches the exact name of the subfolder.

---

## Step 3 — Validate

Run the validation command from the repository root:

```bash
uv run nexus validate logical-benchmarks
```

To validate only the specific benchmark and its instances:

```bash
uv run nexus validate logical-benchmarks --file benchmarks/<benchmark_id>
```

A successful validation prints `success` for the benchmark. If validation fails:

1. Read the error messages carefully (e.g. unknown problem property identifier, schema validation
   errors, missing `artifactsLocation` subfolder).
2. Fix `instance.yaml` or artifact files.
3. Re-run validation until all checks pass.

Do not proceed to the PR step until validation succeeds without errors.

---

## Step 4 — Commit, Push, and Open a PR

Create a feature branch, stage all instance files, commit, and push:

```bash
git checkout -b add-<instance_id>-instance
git add benchmarks/<benchmark_id>/instances/<instance_id>
git commit -s -m "feat(benchmark): Add <instance_id> instance to <benchmark_id>"
git push origin add-<instance_id>-instance
```

Then open a pull request from the new branch to the Algorithm Nexus `main` branch.
Use the `create_pr_workflow` if available to generate the PR description automatically.
