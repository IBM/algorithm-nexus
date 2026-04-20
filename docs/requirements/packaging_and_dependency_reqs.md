# Requirements for Package Variants and Dependency Management

**Status:** Proposed

## 1. Introduction

This document outlines the requirements for building and distributing package
"variants" that cater to different runtime environments. The primary challenge
is to manage dependencies for environments that may or may not include the
`vllm` library, and may require specific versions of it.

---

## 2. Core Requirements

### REQ-1: Multiple Build Targets

The packaging system **must** be capable of producing distinct, installable
distributions (variants) of the project based on the inclusion and versioning of
`vllm`.

- **REQ-1.1 (No vLLM):** It **must** be possible to build a "core" version of
  the package that includes all base dependencies _without_ including `vllm` or
  any code that strictly requires it.

- **REQ-1.2 (vLLM - Product Target Versioned):** It **must** be possible to build a
  variant of the package that bundles a specific, product targetted version of
  the `vllm` library.

- **REQ-1.3 (vLLM - Latest):** It **must** be possible to build a variant that
  bundles the latest stable version of the `vllm` library available from the
  package index.

### REQ-2: Dependency Declaration and Resolution

The system must provide clear mechanisms for declaring dependency relationships
and resolving them correctly for each build target.

- **REQ-2.1 (vLLM-Exclusive Dependencies):** When adding a new dependency, it
  **must** be possible to specify that it is required _only_ for the
  `vllm`-enabled variants.

- **REQ-2.2 (vLLM-Aware Optional Dependencies):** It **must** be possible for a
  package within our project to have optional features that depend on `vllm`.
  Such a package is "vLLM-aware."
  - **2.2.a:** A `vLLM-aware` package **must** be installable as part of the
    "core" variant (**REQ-1.1**), where its `vllm`-dependent features will be
    dormant.
  - **2.2.b:** When a `vLLM-aware` package is installed as part of a
    `vllm`-enabled variant (**REQ-1.2**, **REQ-1.3**), its `vllm`-dependent
    features should be activated.

- **REQ-2.3 (Contextual Dependency Resolution):** The dependency resolution
  process **must** operate within the context of the selected build target.
  - **2.3.a:** When building a `vllm`-enabled variant, the full dependency graph
    for all included packages **must** be resolved against the specific version
    of `vllm` defined for that variant (e.g., the RedHat version).
  - **2.3.b:** When building the "core" variant, the dependency graph for all
    included packages **must** be resolved together _without_ `vllm` present.

### REQ-3: Continuous Integration (CI) Validation

The CI pipeline **must** validate the integrity of all defined package variants.

- **REQ-3.1 (Build Verification):** Upon a pull request, the CI process **must**
  attempt to execute a full, contextual dependency resolution (**REQ-2.3**) and
  build for _all_ variants defined in **REQ-1**. A failure in any single variant
  build should fail the CI check.

- **REQ-3.2 (Testing):** The CI pipeline **must** run distinct test suites
  against each built variant.
  - **3.2.a:** Tests for the "core" variant must validate core functionality and
    confirm that `vllm`-dependent features fail gracefully or are inactive.
  - **3.2.b:** Tests for the `vllm`-enabled variants must validate that the
    `vllm`-aware features are active and functioning correctly.
