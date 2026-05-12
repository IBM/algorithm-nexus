<!--
Copyright IBM Corporation 2026
SPDX-License-Identifier: Apache-2.0
-->

# Requirements for Models Using vLLM

## 1. Introduction

This set of requirements is targeting models requiring vLLM that belong to a
Nexus Package in the `candidate` or `product` variant. The information collected
via this set of requirements are meant to be used for:

1. Identifying which models should be included in product releases.
2. Building a documentation base to be released with the product.

Packages that are only in the `ecosystem` variant are not required to collect
this information.

---

## 2. Requirements

### REQ-1: vLLM Usage Declaration

A model that is intended to be used with `vllm` **may** explicitly declare in
the model definition that it uses `vllm`.

### REQ-2: vLLM General Plugin Support

A model using `vllm` **may** require a general plugin to enable loading the
model into `vllm`.

- **REQ-2.1 (Optional General Plugin):** A model definition **may** specify a
  `vllm` general plugin required to load the model into `vllm`.

- **REQ-2.2 (Single General Plugin):** A model **must not** specify more than
  one `vllm` general plugin.

- **REQ-2.4 (Package Responsibility):** When a model requires a `vllm` general
  plugin, the Python package that owns the model is responsible for installing
  that plugin.

### REQ-3: vLLM I/O Processor Plugin Support

A model using `vllm` **may** support one or more I/O processor plugins.

- **REQ-3.1 (Optional I/O Processor Plugins):** A model definition **may**
  specify zero, one, or more `vllm` I/O processor plugins.

- **REQ-3.3 (Package Responsibility):** When a model supports one or more I/O
  processor plugins, the Python package that owns the model is responsible for
  installing those plugins.
