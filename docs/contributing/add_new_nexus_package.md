<!--
Copyright IBM Corporation 2026
SPDX-License-Identifier: Apache-2.0
-->

# Contributing a Nexus Package to Algorithm Nexus

This guide walks you through the complete process of contributing a Nexus
package to Algorithm Nexus, from creating your package to opening a pull
request.

## Prerequisites

Before you begin, ensure you have:

- A Python package published on GitHub or PyPI
- Models that your package supports
- `uv` installed on your system
- A
  [fork](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo)
  of the Algorithm Nexus repository checked out locally

## Step 1: Create Your Nexus Package

A Nexus package is a metadata and configuration package that references your
Python package and defines the models it supports.

### 1.1 Use the Template

Start by copying the Nexus package template:

```bash
cp -r templates/nexus-package-template packages/<your-package-name>
```

Replace `<your-package-name>` with your actual package name (e.g.,
`terratorch`).

### 1.2 Configure `nexus.yaml`

Edit `packages/<your-package-name>/nexus.yaml` to declare your package metadata:

```yaml
package:
  name: your-package-name # Must match your Python package name
```

See the
[Nexus Package Configuration](nexus_package.md#31-nexus-package-configuration-nexusyaml)
for detailed configuration options.

### 1.3 Configure Model Metadata

For each model your package supports:

1. Create a directory under `packages/<your-package-name>/models/<model-name>/`
1. Create a `model.yaml` file with the model configuration:

   ```yaml
   model:
     id: organization/model-name # Hugging Face model repository identifier
     owner: github-username # Optional: defaults to package owner
     vllm: # Optional: required only if the model is served with vLLM
       enabled: true
       plugins: # Optional: vLLM plugins required for serving your model
         general: your_package.vllm_plugin # Optional: vLLM general plugin required for loading your model in vLLM
         io_processors: # Optional: list of IO Processor plugins that can be used with your model
           - my_io_processor
   ```

1. Optionally add a `usage.md` file with usage documentation

See the
[Model Configuration](nexus_package.md#32-model-configuration-modelsmodel-namemodelyaml)
for complete model configuration options.

## Step 2: Validate Your Nexus Package

Before submitting, validate your package structure and configuration:

```bash
# From the repository root
uv run an validate packages/<your-package-name>
```

This command checks:

- Required files exist (`nexus.yaml`, `model.yaml` for each model)
- YAML syntax is valid
- Configuration follows the required schema
- All declared models have corresponding directories

Fix any validation errors before proceeding.

## Step 3: Add Your Package to Algorithm Nexus

Your Python package must be added to Algorithm Nexus as a dependency using `uv`.
The exact command depends on your package's relationship with `vllm`.

Follow the instructions in the sections below to make sure your Python package
is added properly to the Algorithm Nexus dependencies. Read the
[Algorithm Nexus Dependency Resolution Process documentation](../design/dependency-resolution.md)
for full details.

### 3.1 Classify Your Package

Determine which category your package falls into:

#### Ecosystem-Only Packages

Your package is **ecosystem-only** if it:

- Does **not** declare `vllm` as a default dependency
- Does **not** declare `vllm` as an optional dependency

**Add to ecosystem variant only:**

```bash
uv add <your-package-name> --optional ecosystem
```

#### vLLM-Dependent Packages

Your package is **vllm-dependent** if it:

- Declares `vllm` as a **default (mandatory) dependency**

**Add to candidate variant:**

```bash
uv add <your-package-name> --optional candidate
```

> [!NOTE] Do not add packages to the `product` variant. Algorithm Nexus
> maintainers will handle this once product requirements are met.

#### vLLM-Agnostic Packages

Your package is **vllm-agnostic** if it:

- Does **not** declare `vllm` as a default dependency
- Declares `vllm` as an **optional dependency** (via extras)

**Add to ecosystem variant (without vllm):**

```bash
uv add <your-package-name> --optional ecosystem
```

**Add to candidate variant (with vllm):**

```bash
uv add <your-package-name>[<vllm-extra>] --optional candidate
```

Replace `<vllm-extra>` with the extra name that enables vllm in your package.

### 3.2 Git-Based Packages

If your package is not yet published on PyPI, you can add it from a Git
repository:

```bash
uv add git+https://github.com/<org>/<repository> --optional <variant>
```

> [!IMPORTANT] SSH-based cloning is not supported. All Git dependencies must be
> publicly accessible via HTTPS.

### 3.3 Verify Dependency Resolution

After adding your package, verify the lockfile is updated:

```bash
uv lock --check
```

For detailed information about dependency resolution, see the
[Dependency Resolution Design Document](../design/dependency-resolution.md).

## Step 4: Commit Your Changes

Commit your changes with a descriptive message:

```bash
git add packages/<your-package-name>/
git add pyproject.toml uv.lock requirements-*.txt
git commit -s -m "feat(package): Add <your-package-name> Nexus package

- Add Nexus package metadata and model configurations
- Add <your-package-name> dependency to <variant> variant(s)
- Update lockfile and requirements exports"
```

> [!IMPORTANT] The `-s` flag adds a Signed-off-by line, which is required for
> all contributions. This indicates you accept the
> [Developer's Certificate of Origin](../../CONTRIBUTING.md#legal). Also, make
> sure you have installed the pre-commit hooks before committing your changes.
> This will reduce the likelihood for your contribution to fail the CI workflow.

## Step 5: Open a Pull Request

1. Push your changes to your fork:

   ```bash
   git push origin <your-branch-name>
   ```

2. Open a pull request on GitHub using the `New Nexus Package` template, and
   fill all the required information.

3. Wait for CI checks to complete:
   - Lockfile consistency checks
   - Requirements export validation
   - Package availability verification
   - Variant-specific dependency resolution checks

## Step 6: Address Review Feedback

Maintainers will review your PR and may request changes:

- Respond to comments and questions
- Push updates to your branch (the PR will update automatically)
- Re-request review once changes are complete

## Common Issues and Solutions

### Validation Errors

**Issue**: `an validate` reports errors

**Solution**: Carefully read the error messages and fix the issues in your YAML
files. Common problems include:

- Missing required fields
- Invalid YAML syntax
- Incorrect file paths
- Model directories without `model.yaml`

### Dependency Conflicts

**Issue**: `uv lock` fails with dependency conflicts

**Solution**: Check if your package has conflicting dependencies with existing
packages. You may need to:

- Update your package's dependency constraints
- Coordinate with maintainers about resolving conflicts

If you are unable to resolve the dependency conflicts when adding your package,
you can still create the PR in draft state, and explicitly state that the
package cannot be added due to dependency conflicts. The maintainers will help
you to solve the conflicts, which might require also coordinating with other
Nexus package owners.

### CI Failures

**Issue**: CI checks fail after opening PR

**Solution**: Carefully read the logs and try to identify the root cause. If
unable to solve the issue, send a message in the PR to request the maintainers
help.

## Getting Help

If you encounter issues:

1. Check the [Nexus Package Structure Guide](nexus_package.md)
2. Review the
   [Dependency Resolution Design Document](../design/dependency-resolution.md)
3. Search existing issues on GitHub
4. Open a new issue with details about your problem

## Additional Resources

- [Nexus Package Requirements](../requirements/nexus_package.md)
- [Packaging and Dependency Requirements](../requirements/packaging_and_dependency_reqs.md)
- [Contributing Guidelines](../../CONTRIBUTING.md)
- [Maintainers](../../MAINTAINERS.md)
