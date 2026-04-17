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
benchmarking, and integration within the Algorithm Nexus ecosystem.

---

## 2. Core Requirements

### REQ-1: Nexus Package Definition

A Nexus package **must** define the package-level metadata and assets required
for cataloging and distribution.

- **REQ-1.1 (Identifier):** A Nexus package **must** define a unique package
  identifier using lowercase, hyphenated format (for example,
  `transformers-llm`).

- **REQ-1.2 (Metadata):** A Nexus package **must** provide package metadata,
  including its name, description, and a link to its documentation.

- **REQ-1.3 (Python Package):** A Nexus package **must** specify the Python
  package name or the URL from which the package can be obtained.

- **REQ-1.4 (Version):** A Nexus package **must** specify the version of the
  Python package.

- **REQ-1.5 (Supported Models):** A Nexus package **must** declare the list of
  models supported by the package.

### REQ-2: Model Definition

Each model contained in a Nexus package **must** define the model-level metadata
and operational artifacts required for integration into Algorithm Nexus.

- **REQ-2.1 (Identifier):** Each model **must** define a unique model identifier
  using lowercase, hyphenated format (for example, `terramind-flood`). No two
  models in Algorithm Nexus may share the same identifier.

- **REQ-2.2 (Metadata):** Each model **must** provide metadata including its
  name, version, description, and a link to its documentation.

- **REQ-2.3 (Model Weights):** Each model **must** specify the Hugging Face
  repository hosting the model weights together with the version of those
  weights.

- **REQ-2.4 (Testing):** Each model **must** provide the artifacts required for
  testing the model, as defined in
  [Requirements for Model Testing](./models_testing.md).

- **REQ-2.5 (Benchmarking):** Each model **must** provide the artifacts required
  for benchmarking, such as scripts and any model-specific benchmarking
  requirements.

- **REQ-2.6 (Model Owner):** Each model **must** specify the GitHub ID of the
  model owner.

### REQ-3: Optional Integration Requirements

A Nexus package **may** provide additional artifacts that support integration
with agent frameworks, production systems, and serving runtimes.

- **REQ-3.1 (Model Usage):** A model **may** provide usage documentation that
  combines explanatory text and code snippets to help users get started. Unlike
  the documentation link included in model metadata, this material should be
  committed as part of the Nexus package for reuse in project documentation and
  agentic skills.

- **REQ-3.2 (Agent Integration):** A model **may** provide documentation and
  examples for integration with agent frameworks such as LangChain, AutoGPT, MCP
  servers, or custom agents.

- **REQ-3.3 (Observability):** A model **may** provide documentation and
  examples for integration with observability frameworks or standards such as
  OpenTelemetry.

- **REQ-3.4 (vLLM Integration):** A model **may** provide information related to
  serving the model with `vllm`, including any `vllm`-specific plugins required
  in the Python environment used for serving.

## 3. Notes

- Benchmarking and testing requirements may be unified in the future, depending
  on the outcomes of issues #8 and #18.
- Requirements for `vllm` integration will be detailed in the future.
