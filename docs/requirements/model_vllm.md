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

---

## 2. Requirements

### REQ-1: vLLM Usage Declaration

A model that is intended to be used with vLLM **must** explicitly declare in the
model definition that it uses vLLM.

### REQ-2: vLLM General Plugin Support

For models that require a vLLM general plugin follow the requirements below:

- **REQ-2.1 (Optional General Plugin):** A model definition **must** specify a
  vLLM general plugin required to load the model into vLLM.

- **REQ-2.2 (Package Responsibility):** The Python package that owns the model
  is responsible for installing that plugin.

### REQ-3: vLLM I/O Processor Plugin Support

For models using vLLM IO Processor plugins, follow the requirements below:

- **REQ-3.1 (Optional I/O Processor Plugins):** A model definition **must**
  specify one, or more vLLM IO Processor plugins.

- **REQ-3.3 (Package Responsibility):** The Python package that owns the model
  is responsible for installing those plugins.
