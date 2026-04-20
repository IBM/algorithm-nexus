# Requirements for Package Variants and Dependency Management

**Status:** Proposed

## 1. Introduction

This document outlines the requirements for generating and installing distinct
python distribution package variants tailored to diverse target environments. The
primary technical challenge is managing the package metadata and subsequent
dependency resolution graphs to support installations that either completely
exclude the 'vllm' library, or strictly require specific, pinned versions of it.

### 1.1. Terminology

- project - a python project. The overarching library, framework, or application
  you are building.
  - May be same as "source tree"
- distribution package - a python wheel
- distribution package variant - customized configuration originating from the
  same source tree, designed to trigger a distinct dependency resolution graph
  or provide tailored compiled artifacts at install time.
- packaging system - tooling which creates a package from a python project and
  then installs that package into a python environment
- build - creating a python distribution package
- install - resolving distribution package dependencies, installing them, then
  installing the distribution package

---

## 2. Core Requirements

### REQ-1: Multiple Build Targets

The project's build configuration **must** support the generation and successful
installation of distinct distribution package variants for "algorithm nexus,"
defined by the inclusion and version constraints of the `vllm` dependency.

- **REQ-1.1 (Core Distribution):** It **must** be possible to build and
  successfully install a base distribution package that declares only core
  dependencies. This variant's metadata **must** exclude `vllm`.

- **REQ-1.2 (Pinned vLLM Variant):** It **must** be possible to build a
  distribution package variant whose metadata strictly pins a specific,
  product-targeted version of the `vllm` library. The resulting dependency tree
  for this variant **must** be fully resolvable and successfully installable
  into the target environment without conflicts.

- **REQ-1.3 (Latest vLLM Variant):** It **must** be possible to build a
  distribution package variant whose metadata requires the latest stable release
  of the `vllm` library from the package index. The resulting dependency tree
  for this variant **must** be fully resolvable and successfully installable
  into the target environment.

### REQ-2: Dependency Declaration and Resolution

The packaging system must provide clear mechanisms for declaring dependency
relationships and resolving them correctly for each build target (from Req 1)

- **REQ-2.1 (vLLM-Exclusive Dependencies):** When adding a new dependency, it
  **must** be possible to specify that it is required _only_ one or both of the
  `vllm`-enabled variants.

- **REQ-2.2 (vLLM-Aware Optional Dependencies):** It **must** be possible for a
  declare a package to optionally require vLLM (vLLM aware)
  - **2.2.a:** A `vLLM-aware` package **must** be installable as part of the
    "core" variant (**REQ-1.1**).
  - **2.2.b:** A `vLLM-aware` package **must** be installable as part of a
    `vllm`-enabled variant (**REQ-1.2**, **REQ-1.3**)

- **REQ-2.3 (Contextual Dependency Resolution):** The dependency resolution
  process **must** operate within the context of the selected build target.
  - **2.3.a:** When installing a `vllm`-enabled variant, the full dependency
    graph for all included packages **must** be resolved against the specific
    version of `vllm` defined for that variant (e.g., the pineed version).
  - **2.3.b:** When installing the "core" variant, the dependency graph for all
    included packages **must** be resolved together _without_ `vllm` present.

### REQ-3: Continuous Integration (CI) Validation

The CI pipeline **must** validate the conformance of all defined distribution
package variants to the requirements of this document.

- **REQ-3.1 (Build Verification and Testing):** The CI pipeline **must**
  validate each generated distribution package variant by successfully
  installing the built artifact into an isolated target environment and
  executing a distinct test suite against that installation."
