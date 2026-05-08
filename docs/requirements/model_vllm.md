<!--
Copyright IBM Corporation 2026
SPDX-License-Identifier: Apache-2.0
-->

# Requirements for Models Using vLLM

## 1. Introduction

This document defines the requirements for a model to declare and support usage
with `vllm` in Algorithm Nexus. These requirements ensure that models intended
to run with `vllm` explicitly declare that support and specify any required
plugins that must be present in the Python environment where the model is
executed.

The scope of this document is limited to the metadata and plugin requirements
needed for `vllm` integration. Requirements for testing models with `vllm` are
defined separately in [Requirements for Model Testing](./models_testing.md).

---

## 2. Core Requirements

### REQ-1: vLLM Usage Declaration

A model that is intended to be used with `vllm` **must** explicitly declare that
it uses `vllm`.

- **REQ-1.1 (Explicit Declaration):** The model definition **must** include a
  field or mechanism that indicates whether the model is intended to run with
  `vllm`.

### REQ-2: vLLM General Plugin Support

A model using `vllm` **may** require a general plugin to enable loading the
model into `vllm`.

- **REQ-2.1 (Optional General Plugin):** A model definition **may** specify a
  `vllm` general plugin required to load the model into `vllm`.

- **REQ-2.2 (Single General Plugin):** A model **must not** specify more than
  one `vllm` general plugin.

- **REQ-2.3 (Plugin Availability):** If a model specifies a `vllm` general
  plugin, that plugin **must** be available through Python entry points in the
  `vllm.general_plugins` group in the environment where the model is executed

- **REQ-2.4 (Package Responsibility):** When a model requires a `vllm` general
  plugin, the Python package that owns the model **must** be responsible for
  installing that plugin.

### REQ-3: vLLM I/O Processor Plugin Support

A model using `vllm` **may** require one or more I/O processor plugins.

- **REQ-3.1 (Optional I/O Processor Plugins):** A model definition **may**
  specify zero, one, or more `vllm` I/O processor plugins.

- **REQ-3.2 (Plugin Availability):** Each I/O processor plugin specified by the
  model **must** be available through Python entry points in the
  `vllm.io_processor_plugins` group in the environment where the model is
  executed.

- **REQ-3.3 (Package Responsibility):** When a model requires one or more I/O
  processor plugins, the Python package that owns the model **must** be
  responsible for installing those plugins.
