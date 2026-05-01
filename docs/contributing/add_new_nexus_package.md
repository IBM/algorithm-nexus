<!--
Copyright IBM Corporation 2026
SPDX-License-Identifier: Apache-2.0
-->

# Contributing a python algorithm package to Algorithm Nexus

This guide walks you through the process of contributing a algorithm python
package, containing, for example, AI models, to Algorithm Nexus.

There are four steps to contribute your algorithm package

1. \*Setup a local copy of the Algorithm Nexus repository\*\*
2. **Add your algorithm package to the Algorithm Nexus dependencies**
3. \*_Create a Nexus package for your algorithm_
4. **Commit your changes, push them, and then open a PR with Algorithm Nexus**

## Prerequisites

Before you begin, ensure

- Your algorithm package is publicly available GitHub at `<Python-Package-URL>`.
- `uv` is [installed](https://docs.astral.sh/uv/getting-started/installation/)
  on your system.
- You have a
  [fork](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo)
  of the Algorithm Nexus repository checked out locally

## Step 1: Setup the Algorithm Nexus repository

Run the commands below from the folder where you have checked out your Algorithm
Nexus fork.

```bash
cd algorithm-nexus
uv sync --group dev --extra cli
uv run pre-commit install
```

Then, create a new branch to host your changes.

```bash
git checkout -b add-<package-name>-package
```

## Step 2: Add your algorithm package to the Algorithm Nexus dependencies

First, determine which variants your package should be added to, by reading
[`Identify The Algorithm Nexus variant for your Package`](#identify-the-algorithm-nexus-variant-for-your-package).
Then add it to each of this variants using `uv`.

For example, if your package should be added to the `ecosystem` variant run,

```bash
uv add <Python-Package-URL> --optional ecosystem
```

If the `uv add` step fails, and you are unable to troubleshoot the error, record
the error you get and continue on to step 3 and 4.

## Step 3: Create a Nexus package for your algorithm

A Nexus package is a directory with some files that contains metadata about your
algorithm package. Under `packages/` in the root of the Algorithm Nexus
repository you checked out, create a folder with your package name

```bash
mkdir packages/<package-name>
```

Then, create the Nexus package configuration file in
`packages/<package-name>/nexus.yaml` with the following content:

```yaml
package:
  name: <package-name>
```

Finally, validate the package structure with

```bash
uv run nexus validate packages/<package-name>
```

In case of validation errors, the nexus validate tool will list all the errors.
Fix them before moving to the next step.

## Step 4: Commit Changes and Open a Pull Request

Add the files to be committed

```bash
git add packages/<package-name> pyproject.toml uv.lock
```

Commit your changes and push to your remote fork

```bash
git commit -s -m "feat(package): Add <package-name> Nexus Package"
git push origin add-<package-name>-package
```

Finally, navigate to your fork on GitHub and open a Pull request for the newly
pushed branch to be merged with the Algorithm Nexus main branch. Use the
`New Nexus Package` pull request template and fill all the required fields. In
case of failures in _Step 2_, the PR template contains a dedicated section
(`I Need Help`) where you can log the errors recorded while adding your python
package to the Algorithm Nexus dependencies.

## Next Steps

After completing above you can flesh out your contribution with more
information:

1. [Describe the models your algorithm package contains](#describe-the-models-in-your-algorithm-package)
   - This is required to access testing and benchmarking of your model in future
2. [Add documentation on how to use your models](#model-usage-documentation) for
   inference and fine-tuning
3. [Add agent skills for your package](#agent-skills-for-nexus-packages)

## Additional Material

### Identify The Algorithm Nexus Variant for your Package

If your Python package:

- does **not** declare `vllm` as a default dependency
- does **not** declare `vllm` as an optional dependency

It belongs to the `ecosystem` variant only.

If your Python package:

- declares `vllm` as a **default (mandatory) dependency**

It belongs to the `candidate` variant only.

If your Python package:

- declares `vllm` as an **optional dependency**

It belongs both to the `ecosystem` and `candidate` variant only. In this case,
when adding to the `candidate` variant, users must ensure their package is added
with the optional `vllm` dependency (`package-name[vllm-dependency]`).

### Describe the Models in Your Algorithm Package

If your algorithm package contains one or more models, you can add their
description to the Nexus package metadata by following the steps below.

For each model (`<model-name>`) that your package supports:

1. Create a directory under `packages/<package-name>/models/<model-name>/`
2. Create a `model.yaml` file with the model configuration:

   ```yaml
   model:
     id: organization/model-name # Hugging Face model repository identifier
     owner: github-username # Optional: defaults to package owner if omitted
   ```

Full details on the model configuration file are available in the
[Nexus Package Structure Guide](../design/nexus_package.md).

### Model Usage Documentation

Optionally, each model in a Nexus package can provide usage documentation in a
`usage.md` file in the model subfolder. This should be populated with usage
examples, description of useful parameters, and any other relevant information.

### Agent Skills for Nexus Packages

Optionally, each Nexus package can provide agent skills for helping the user
with using the package and its models. Example agent skills would aid the users
with models deployment on different target infrastructure (e.g., bare metal,
Kubernetes, etc.) and with building scripts for evaluating the models.

## Getting Help

If you encounter issues:

1. Check the [Nexus Package Structure Guide](nexus_package.md)
2. Review the
   [Dependency Resolution Design Document](../design/dependency-resolution.md)
3. Search existing issues on GitHub
4. Open a new issue with details about your problem

## References

- [Nexus Package Structure Guide](../design/nexus_package.md)
- [Nexus Package Requirements](../requirements/nexus_package.md)
- [Packaging and Dependency Requirements](../requirements/packaging_and_dependency_reqs.md)
- [Contributing Guidelines](../../CONTRIBUTING.md)
- [Maintainers](../../MAINTAINERS.md)
