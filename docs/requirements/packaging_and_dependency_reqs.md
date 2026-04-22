# Requirements for Package Variants and Dependency Management

**Status:** Approved

## 1. Introduction

This document outlines the requirements for building and installing distinct
Python distribution package variants of Algorithm Nexus, tailored to diverse
target environments. The primary technical challenge is managing the package
metadata and subsequent dependency resolution graphs to support installations
that either completely exclude the 'vllm' library, or strictly require specific,
pinned versions of it.

### 1.1. Terminology

- **Building**: creating a Python distribution package.
- **Distribution package**: a Python wheel.
- **Distribution package variant**: a variant of the project's distribution
  package, derived from the same source tree but configured to yield a distinct
  dependency graph and/or install-time behavior. Typically the result of
  selecting additional optional dependencies.
- **Installing**: resolving distribution package dependencies and installing
  them along with the distribution package.
- **Packaging system**: tooling which can create a distribution package from a
  Python project and install it into a Python environment.
- **Project**: a Python project and its source tree.

---

## 2. Core Requirements

### REQ-1: Multiple Build Targets

Algorithm Nexus's build configuration **must** support building and installing
distinct distribution package variants, as defined by inclusion and version
constraints of the `vllm` dependency.

- **REQ-1.1 (Core Variant):** It **must** be possible to build and successfully
  install a distribution variant package whose dependencies **must** exclude
  `vllm`. We define this as the "Core" variant.

- **REQ-1.2 (Pinned vLLM Variant):** It **must** be possible to build and
  successfully install a distribution package variant whose metadata strictly
  pins a specific, product-targeted version of the `vllm` library.

- **REQ-1.3 (Latest vLLM Variant):** It **must** be possible to build and
  successfully install a distribution package variant whose metadata requires
  the latest stable release of the `vllm` library from the package index.

### REQ-2: Dependency Declaration and Resolution

The packaging system must provide clear mechanisms for declaring dependency
relationships and resolving them correctly for each build target (from Req 1).

- **REQ-2.1 Dependencies that can only be in the Core variant:** When adding a
  new dependency, it **must** be possible to specify that it is required for
  _only_ the "Core" variant.

- **REQ-2.2 Dependencies that can only be in a vLLM variant:** When adding a new
  dependency, it **must** be possible to specify that it is required for _only_
  one or both of the `vllm`-enabled variants.

- **REQ-2.3 Dependencies that can be in all variants:** It **must** be possible
  for a package to specify that is required in all variants. We define such a
  dependency "vLLM-aware".

- **REQ-2.4 (Contextual Dependency Resolution):** The dependency resolution
  process **must** operate within the context of the selected variant.
  - **2.4.a:** When installing a `vllm`-enabled variant, the full dependency
    graph for all included packages **must** be resolved against the specific
    version of `vllm` defined for that variant (e.g., the pinned version).
  - **2.4.b:** When installing the "core" variant, the dependency graph for all
    included packages **must** be resolved together _without_ `vllm` present.

### REQ-3: Continuous Integration (CI) Validation

The CI pipeline **must** validate the conformance of all defined distribution
package variants to the requirements of this document.

- **REQ-3.1 (Build Verification and Testing):** The CI pipeline **must**
  validate each distribution package variant by successfully installing the
  built artifact into an isolated target environment and executing a distinct
  test suite against that installation.
