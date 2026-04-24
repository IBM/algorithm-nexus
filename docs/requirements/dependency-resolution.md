# Dependency Resolution in Algorithm Nexus

**Status:** Draft

---

## 1. Introduction

This document describes the dependency declaration and dependency resolution
process for **Algorithm Nexus** in the context of the three distribution package
variants defined in
[Requirements for Package Variants and Dependency Management](docs/requirements/packaging_and_dependency_reqs.md#req-1-multiple-build-targets`).

It explains how distribution package variants are implemented using the
packaging system, how dependencies are added, and how correctness is enforced
via continuous integration (CI).

## 2. Packaging and Variant-Based Dependency Resolution

Algorithm Nexus uses **uv** as its packaging system and is published on PyPI as
the package **`algorithm-nexus`**.

Support for multiple distribution package variants is implemented using
**optional dependencies (extras)** as defined by uv:
<https://docs.astral.sh/uv/concepts/projects/dependencies/#optional-dependencies>

The mapping between **distribution package variants** and **optional
dependencies** is defined as follows:

- **Ecosystem Variant**

  - Installation target: `algorithm-nexus[ecosystem]`
  - The dependency graph **must not include** the `vllm` library.
  - Only Algorithm Stack packages associated with the _Ecosystem Algorithm
    Stack_ are included.

- **Candidate Variant**

  - Installation target: `algorithm-nexus[candidate]`
  - The dependency graph **must include** the `vllm` library.
  - A **specific version of `vllm` must always be required**.
  - Only Algorithm Stack packages associated with the _Candidate Algorithm
    Stack_ are included.

- **Product Variant**
  - Installation target: `algorithm-nexus[product]`
  - The dependency graph **must include** the `vllm` library.
  - A **specific, pinned version of `vllm` must always be required**.
  - Only Algorithm Stack packages associated with the _Product Algorithm Stack_
    are included.

Because different variants may result in mutually incompatible dependency
graphs, uv is relied upon to isolate and resolve dependencies per variant.
Conflicts between variants are permitted; **dependency conflicts within a single
variant are not**.

Dependency conflict handling follows uv’s documented behavior:
<https://docs.astral.sh/uv/concepts/projects/config/#conflicting-dependencies>

## 3. Adding Dependencies to Algorithm Nexus

All Algorithm Stack dependencies **must** be added to Algorithm Nexus using
**uv** and **must** be explicitly associated with one or more distribution
package variants.

Algorithm Nexus does **not** use a default dependency group for Algorithm Stack
packages. Every Algorithm Stack package is associated with variants exclusively
via optional dependencies (extras).

Manual editing of dependency declarations, lockfiles, or exported requirement
files is **strictly forbidden**. All dependency changes **must** be performed
using uv commands only.

Official instructions for adding dependencies are documented in the uv guide:
<https://docs.astral.sh/uv/concepts/projects/dependencies/#dependency-sources>

## 4. Variant Association Rules

Algorithm Stack packages are classified based on **how they declare `vllm` in
their dependency metadata**, distinguishing between default and optional
dependencies.

When adding an Algorithm Stack package, contributors **must** classify it using
exactly one of the following categories.

### 4.1 Ecosystem‑Only Packages

An **ecosystem‑only package** is a package that:

- does **not** declare `vllm` as a default dependency, and
- does **not** declare `vllm` as an optional dependency.

These packages can never introduce `vllm` into a dependency graph.

**Variant integration rules:**

- These packages **must** be added to the **Ecosystem Variant**.
- They **must not** be added to the Candidate or Product Variants.

### 4.2 vllm‑Dependent Packages

A **vllm‑dependent package** is a package that:

- declares `vllm` as a **default (mandatory) dependency**.

These packages always introduce `vllm` into the dependency graph.

**Variant integration rules:**

- These packages **must** be added to the **Candidate** and **Product**
  Variants.
- These packages **must not** be added to the Ecosystem Variant.

### 4.3 vllm‑Agnostic Packages

A **vllm‑agnostic package** is a package that:

- does **not** declare `vllm` as a default dependency, but
- declares `vllm` as an **optional dependency** (via one or more extras).

These packages can participate in dependency graphs **both with and without**
`vllm`, depending on how they are installed.

**Variant integration rules:**

- For the **Ecosystem Variant**: the package **must** be added **without
  enabling any extras** that introduce `vllm` into the dependency graph.

- For the **Candidate** and **Product Variants**: the package **must** be added
  **with extras enabled** such that `vllm` is included in the resolved
  dependency graph.

## 5. Adding Packages with uv

All Algorithm Stack packages are added using **uv**. The concrete commands are
determined by:

1. the package’s classification (see Section 4), and
2. the distribution package variant being targeted.

The **same package may be added differently for different variants**, depending
on whether `vllm` must or must not be present in the resulting dependency graph.

> [!CAUTION]
>
> No Algorithm Stack package may be added to a variant in a way that violates
> the dependency guarantees of that variant.

### 5.1 General Command Pattern

All packages are added using the following pattern:

```bash
uv add <package-spec> --optional <variant-extra>
```

Where `<variant-extra>` is one of:

- `ecosystem`
- `candidate`
- `product`

Packages **must only** be added to the extras required by their classification.
Do **not** assume that a package should be added to all extras unless explicitly
required by Section 4.

### 5.2 Ecosystem‑Only Packages

Ecosystem‑only packages never introduce `vllm` into the dependency graph.

Add the package **only** to the Ecosystem Variant:

```bash
uv add <package-name> --optional ecosystem
```

### 5.3 vllm‑Dependent Packages

vllm‑dependent packages declare `vllm` as a **default dependency** and therefore
always introduce `vllm` into the dependency graph.

Add the package to **both** vllm‑enabled variants:

```bash
uv add <package-name> --optional candidate
uv add <package-name> --optional product
```

These packages **must not** be added to the Ecosystem Variant.

### 5.4 vllm‑Agnostic Packages

vllm‑agnostic packages do **not** declare `vllm` as a default dependency, but
**do** declare `vllm` as an optional dependency via one or more extras.

These packages must be added **differently per variant**.

#### Ecosystem Variant (vllm excluded)

Add the package **without enabling any extras** that introduce `vllm`:

```bash
uv add <package-name> --optional ecosystem
```

or, if the package requires a specific non‑vllm extra:

```bash
uv add <package-name>[<non-vllm-extra>] --optional ecosystem
```

#### Candidate and Product Variants (vllm included)

Add the package **with extras enabled** such that `vllm` is included in the
dependency graph:

```bash
uv add <package-name>[<vllm-extra>] --optional candidate
uv add <package-name>[<vllm-extra>] --optional product
```

This ensures that:

- the Ecosystem Variant remains free of `vllm`, and
- the Candidate and Product Variants consistently include `vllm`.

### 5.5 Git‑Based Packages

> [!IMPORTANT]
>
> SSH-based cloning is not supported. All Git dependencies **must** be publicly
> accessible and clonable via HTTPS.

For packages hosted in a public Git repository, the same rules apply.

General form:

```bash
uv add git+https://<git-server-url>/<org>/<repository>[<extras>] --optional <variant-extra>
```

Repeat the command for each variant as required by Section 4, enabling or
disabling dependency‑introducing extras as appropriate.

## 6. Dependency Resolution Checks in CI

The Algorithm Nexus CI pipeline enforces dependency correctness on every pull
request.

The following checks **must** pass for all changes that modify dependencies or
their resolution.

### 6.1 Lockfile and Export Consistency

- The `uv.lock` file **must** be present and up to date.
- A `requirements.txt` file **must** be exported from `uv.lock` and kept in
  sync.
- All packages listed in `requirements.txt` **must**:
  - be available from the configured package index, and
  - not be yanked or otherwise invalid.

### 6.2 Variant Dependency Resolution Checks

Each distribution package variant **must** be validated independently in CI by
resolving its dependency graph using the corresponding extra.

#### Ecosystem Variant

Resolving the `ecosystem` extra **must not** produce a dependency graph that
contains `vllm`.

CI **must** fail if `vllm` appears anywhere in the resolved dependency graph,
including transitive dependencies.

Packages may declare optional support for `vllm`, but any extras that introduce
`vllm` **must not** be enabled for the Ecosystem Variant.

#### Candidate and Product Variants

Resolving the `candidate` and `product` extras **must** produce a dependency
graph that includes `vllm`.

CI **must** fail if:

- `vllm` is missing from the resolved dependency graph, or
- the resolved `vllm` version does not satisfy the variant’s constraints.
