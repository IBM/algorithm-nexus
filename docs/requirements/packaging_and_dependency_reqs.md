# Requirements for Package Variants and Dependency Management

**Status:** Approved

---

## 1. Introduction

This document defines the requirements for building and installing multiple,
distinct Python distribution package variants of **Algorithm Nexus**, tailored
to different target environments.

The primary technical challenge addressed by this document is the management of
package metadata and dependency resolution graphs in order to support
installations that:

- completely exclude the `vllm` library, or
- strictly require specific versions of the `vllm` library.

All requirements in this document are normative unless explicitly stated
otherwise.

---

## 1.1 Terminology

The following terminology is used consistently throughout this document:

- **Building**: The process of creating a Python distribution package from a
  source tree.

- **Distribution package**: A Python wheel (`.whl`) produced from a Python
  project.

- **Distribution package variant** (or **variant**): A distinct build and
  install configuration of a distribution package, derived from the same source
  tree but resulting in a different dependency graph and/or install-time
  behavior. Variants are typically produced by selecting different sets of
  optional dependencies.

- **Installing**: The process of resolving dependencies for a distribution
  package and installing both the package and its resolved dependencies into a
  Python environment.

- **Packaging system**: Tooling capable of building distribution packages and
  installing them into Python environments (e.g., build backends, dependency
  resolvers, and installers).

- **Project**: A Python project and its associated source tree.

- **Algorithm Stack**: A defined collection of Python package dependencies used
  by Algorithm Nexus that provide AI models and algorithms.

- **Algorithm Stack package**: An individual Python package that is a member of
  the Algorithm Stack.

- **`vllm`**: The Python package published under the name `vllm` in the package
  index. This document uses the lowercase form consistently to match the package
  name.

---

## 2. Core Requirements

### REQ‑1: Multiple Build Targets

Algorithm Nexus **must** support building and installing multiple, mutually
distinct distribution package variants from the same source tree.

Each variant **must** define a different dependency graph by controlling:

- whether and how the `vllm` library is included, and
- which subset of the Algorithm Stack is selected.

The following **distribution package variants** are formally defined and
referenced throughout this document:

- **Ecosystem Variant**
- **Product Variant**
- **Candidate Variant**

#### REQ‑1.1: Ecosystem Variant

It **must** be possible to build and successfully install the **Ecosystem
Variant**, whose dependencies **do not include** the `vllm` library.

Only Algorithm Stack packages belonging to the _Ecosystem Algorithm Stack_
**must** be included in this variant.

#### REQ‑1.2: Product Variant

It **must** be possible to build and successfully install the **Product
Variant**, whose dependencies **require a specific, pinned version** of the
`vllm` library.

Only Algorithm Stack packages belonging to the _Product Algorithm Stack_
**must** be included in this variant.

#### REQ‑1.3: Candidate Variant

It **must** be possible to build and successfully install the **Candidate
Variant**, whose dependencies **require the latest stable release** of the
`vllm` library available from the package index.

Only Algorithm Stack packages belonging to the _Candidate Algorithm Stack_
**must** be included in this variant.

#### REQ‑1.4: Algorithm Stack Partitioning

When installing a given distribution package variant, **only** the Algorithm
Stack packages associated with that variant **must** be installed.

An individual Algorithm Stack package **may be** associated with more than one
variant.

---

### REQ‑2: Dependency Declaration and Resolution

The packaging system **must** provide clear and explicit mechanisms for
declaring dependency relationships and resolving them correctly for each
distribution package variant defined in REQ‑1.

#### REQ‑2.1: Ecosystem‑Only Dependencies

When adding a new dependency (e.g., an Algorithm Stack package), it **must** be
possible to specify that the dependency is required **only** for the **Ecosystem
Variant**.

#### REQ‑2.2: Product‑ and Candidate‑Only Dependencies

When adding a new dependency (e.g., an Algorithm Stack package), it **must** be
possible to specify that the dependency is required **only** for:

- the **Product Variant**,
- the **Candidate Variant**, or
- both the Product and Candidate Variants.

#### REQ‑2.3: Dependencies Common to All Variants

It **must** be possible to specify that a dependency is required for **all**
distribution package variants.

Such dependencies are defined as **vllm‑aware**, meaning that they are
compatible with both:

- environments where `vllm` is present, and
- environments where `vllm` is absent.

#### REQ‑2.4: Explicit Variant Association

Every Algorithm Stack package **must** be explicitly associated with at least
one defined distribution package variant.

Algorithm Stack packages **must not** belong exclusively to an implicit or
default dependency group.

Non‑Algorithm‑Stack dependencies that are generic and used by all variants
**may** be placed in a default dependency group.

#### REQ‑2.5: Contextual Dependency Resolution

The dependency resolution process **must** operate within the context of the
selected distribution package variant.

##### REQ‑2.5.a: Product and Candidate Resolution

When installing the **Product Variant** or **Candidate Variant**, the complete
dependency graph for all included packages **must** be resolved against the
specific version of `vllm` defined for that variant (e.g., the pinned product
version).

##### REQ‑2.5.b: Ecosystem Resolution

When installing the **Ecosystem Variant**, the complete dependency graph for all
included packages **must** be resolved together **without** `vllm` present.

---

### REQ‑3: Continuous Integration (CI) Validation

The continuous integration (CI) pipeline **must** validate conformance of all
defined distribution package variants to the requirements in this document.

#### REQ‑3.1: Build Verification and Testing

The CI pipeline **must** validate each distribution package variant by:

1. building the corresponding distribution package,
2. installing the built artifact into an isolated target environment, and
3. executing a variant‑specific test suite against that installation.
