<!--
Copyright IBM Corporation 2026
SPDX-License-Identifier: Apache-2.0
-->

# Requirements for a Nexus Package

**Status:** Proposed

## 1. Introduction

This document outlines the requirements for defining a Nexus package and the
models it contains. A Nexus package encapsulates a Python package together with
its associated models, providing standardized metadata for validation, testing,
benchmarking, and integration within the Algorithm Nexus ecosystem. When
mentioning model we always refer to a Hugging Face repository hosting the model
documentation and weights.

---

## 2. Core Requirements

### REQ-1: Python Packages Used in Nexus

A Python package **must** fulfill a set of requirements to guarantee it can be
properly integrated with Nexus.

- **REQ-1.1 (Release):** A Python package **must** must provide versioned
  releases, using any versioning scheme as long as it guarantees that increasing
  version numbers represent newer releases. The releases must be published on
  GitHub or PyPI.
- **REQ-1.2 (Owner):** Each Python package **must** define at least one
  maintainer. This will be considered as owner of the Nexus package.
- **REQ-1.3 (Metadata):** Each Python package **must** include a description and
  link to documentation in the released wheel.
- **REQ-1.4 (Dependencies):** Each Python package **must** define all
  dependencies required for use and testing.

### REQ-2: Nexus Package Definition

A Nexus package must allow for the following information to be recorded:

- **REQ-2.1 (Python Package):** A Nexus package **must** provide the PyPI
  package name or GitHub repository name, which serves as the identifier within
  Algorithm Nexus.

- **REQ-2.2 (Python Package Version):** A Nexus package **may** provide the
  version of the python package to be used for dependency resolution.

- **REQ-2.3 (Supported Models):** A Nexus package **must** have a mechanism to
  define the models it supports.

- **REQ-2.4 (Agent skills):** A Nexus package **may** specify agent skills for
  using the python package, either directly embedded in the Nexus package (e.g.
  AGENTS.md) or as a link to existing skills on an external repository.

### REQ-3: Model Definition

Each model contained in a Nexus package allows recording the operational
artifacts required for integration into Algorithm Nexus.

- **REQ-3.1 (Identifier):** The model Hugging Face repository name serves as the
  identifier (for example, `ibm-esa-geospatial/TerraMind-base-Flood`).

- **REQ-3.2 (Testing):** Each model **must** provide the artifacts required for
  testing the model, as defined in
  [Requirements for Model Testing](./models_testing.md).

- **REQ-3.3 (Benchmarking):** Each model **may** provide the artifacts required
  for benchmarking, such as scripts and any model-specific benchmarking
  requirements.

- **REQ-3.4 (Owner):** Each model **must** have a designated owner. By default,
  the owner of the Nexus package will be the the owner of each model unless a
  specific owner is given.

### REQ-4: Optional Requirements

A Nexus package or a model **may** provide additional artifacts that support
integration with agent frameworks, production systems, and serving runtimes.

- **REQ-4.1 (Model Usage):** A model **may** provide usage documentation that
  combines explanatory text and code snippets to help users get started. Unlike
  the documentation link included in model metadata, this material should be
  committed as part of the Nexus package for reuse in project documentation and
  agentic skills.

- **REQ-4.2 (Agent Integration):** A Nexus package **may** provide concrete
  integration artifacts for one or more supported agent frameworks, protocols,
  or model-tool interaction interfaces. If provided, the package **should**
  specify the supported target, setup requirements, and a minimal runnable
  example of agent-to-model interaction.

- **REQ-4.3 (vLLM Integration):** A model **may** provide information related to
  serving the model with `vllm`, including any `vllm`-specific plugins required
  in the Python environment used for serving.

## 3. Notes

- Benchmarking and testing requirements may be unified in the future, depending
  on the outcomes of issues `#8` and `#18`.
