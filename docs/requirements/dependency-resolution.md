# Dependency Resolution in Algorithm Nexus

**Status:** Draft

## Introduction

This document outlines the dependency resolution process for Algorithm Nexus in
the context of the three build targets defined in
[Requirements for Package Variants and Dependency Management](docs/requirements/packaging_and_dependency_reqs.md#req-1-multiple-build-targets).

## Algorithm Nexus Packaging and Dependency Resolution

Algorithm Nexus uses `uv` as its packaging system and is published on PyPI as
`algorithm-nexus`. The
[multiple build targets](docs/requirements/packaging_and_dependency_reqs.md#req-1-multiple-build-targets)
requirement is implemented via
[Optional Dependencies](https://docs.astral.sh/uv/concepts/projects/dependencies/#optional-dependencies).

- The "Core" variant is the default variant and requires no extras.
- The "vLLM-enabled" variant includes `vllm` as a dependency and requires the
  `vllm` extra (`algorithm-nexus[vllm]`). **A lower bound on the vLLM version is
  required at all times**.
- The "vLLM-product" variant includes `vllm` as a dependency and requires the
  `vllm-product` extra (`algorithm-nexus[vllm-product]`). **A specific version
  of vLLM is required at all times**.

When the "vLLM-enabled" and "vLLM-product" variants have conflicting
dependencies, the packaging system will automatically handle the conflict in
accordance with
[uv's conflicting dependencies documentation](https://docs.astral.sh/uv/concepts/projects/config/#conflicting-dependencies).
The only allowed dependency conflict among all variants is the vLLM version.

## Adding a Distribution Package to Algorithm Nexus

Per the specification above, **all packages must be added to Algorithm Nexus
using `uv`**.

Instructions for adding dependencies are documented in the uv guide:
https://docs.astral.sh/uv/concepts/projects/dependencies/#dependency-sources.

**Manually adding or editing dependencies by hand is strictly forbidden.** Any
dependency changes must go through `uv`.

Below are the commands for the most common scenarios.

### Packages Without vLLM Dependencies and vLLM-enabled Variants

These distribution packages should be added to Algorithm Nexus's default
dependencies.

#### Published packages

For packages published on PyPI, use the following command:

```
uv add <package-name>
```

If the package is published on a different (public) package index, use the
following command:

```
uv add <package-name> --index <package-index-url>
```

#### Git packages

Packages that are hosted on a Git repository can be added using the following
command:

```
uv add git+https://<git-server-url>/<your-org-name>/<your-package-name>
```

**NOTE**: SSH-cloning of packages is not supported. Packages must be publicly
available and clonable via HTTPS.

### Packages with vLLM Dependencies and vLLM-enabled Variants

These distribution packages should be added to Algorithm Nexus's optional
dependencies for both the `vllm` and the `vllm-product` variants.

#### Published packages

For packages published on PyPI, use the following commands:

```
uv add <package-name> --optional vllm
uv add <package-name> --optional vllm-product
```

If the package is published on a different (public) package index, use the
following commands:

```
uv add <package-name> --optional vllm --index <package-index-url>
uv add <package-name> --optional vllm-product --index <package-index-url>
```

#### Git packages

Packages that are hosted on a Git repository can be added using the following
commands:

```
uv add git+https://<git-server-url>/<your-org-name>/<your-package-name> --optional vllm
uv add git+https://<git-server-url>/<your-org-name>/<your-package-name> --optional vllm-product
```

**NOTE**: SSH-cloning of packages is not supported. Packages must be publicly
available and clonable via HTTPS.

## Dependency Resolution Checks

The Algorithm Nexus CI pipeline runs dependency resolution checks on every PR.
The following checks are performed:

- Check that the `uv.lock` file is present and up-to-date.
- Check that a `requirements.txt` file has been exported from the `uv.lock` file
  and is up-to-date.
- Check that the packages listed in `requirements.txt` are available in the
  package index and have not been yanked.
