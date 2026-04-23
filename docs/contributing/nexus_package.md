<!--
Copyright IBM Corporation 2026
SPDX-License-Identifier: Apache-2.0
-->

# Nexus Package Structure Guide

This document defines the folder structure and configuration files for a Nexus
package based on the requirements outlined in
[`docs/requirements/nexus_package.md`](../requirements/nexus_package.md) and
[`docs/requirements/models_testing.md`](../requirements/models_testing.md).

## 1. Overview

A Nexus package is a **metadata and configuration package** that references an
external Python package (released on GitHub or PyPI) and defines the models it
supports. The Nexus package **does not contain the Python package source code
itself**, but rather provides standardized metadata for validation, testing,
benchmarking, and integration within the Algorithm Nexus ecosystem.

The Nexus package serves as a registry entry that:

- References a Python package with versioned releases on GitHub or PyPI
- Defines which models are supported by that Python package
- Provides testing and benchmarking configurations for each model
- Enables dependency resolution across all packages in the Algorithm Nexus

---

## 2. Folder Structure

Each Nexus package must be placed under the top-level `packages/` directory in
the repository. Within `packages/`, each package directory must contain the
following structure:

```text
packages/
└── <nexus-package-name>/
    ├── nexus.yaml         # Required package metadata
    ├── AGENTS.md          # Optional agent skills documentation
    └── models/
        ├── <model-1>/
        │   ├── model.yaml # Required model metadata
        │   ├── tests/     # Required test artifacts
        │   ├── benchmarks/# Optional benchmark artifacts
        │   └── usage.md   # Required usage documentation
        ├── <model-2>/
        │   └── ...
        └── ...
```

The required root file is `nexus.yaml`, which declares the Nexus package
metadata and the list of supported model folders. `AGENTS.md` is optional and
should only be included when the package provides embedded agent skills
documentation. The `models/` directory is required whenever the package declares
one or more supported models, and each model folder must contain a `model.yaml`
file describing the model metadata, testing requirements, optional vLLM
integration, and optional benchmarking configuration. Each model folder should
also include `usage.md` so users have model-specific usage guidance. The
`tests/` directory is required for every model because testing artifacts are
mandatory. The `benchmarks/` directory is only needed when the model provides
custom benchmarking artifacts, such as Python modules referenced by
`benchmarking.custom_experiments.python_module`, or other benchmark-specific
assets that are not covered by catalog experiments alone.

---

## 3. Configuration Files

### 3.1. Nexus Package Configuration (`nexus.yaml`)

The `nexus.yaml` file defines package-level metadata and references the external
Python package and its supported models.

#### 3.1.1. Field Summary

| Field                           | Type           | Required | Description                                                                                                                    |
| ------------------------------- | -------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `package.name`                  | `string`       | Yes      | Python package name used as the Nexus package identifier. The package must publish versioned releases on GitHub or PyPI.       |
| `package.version`               | `string`       | No       | Specific Python package version to use for dependency resolution. If omitted, the latest version is used.                      |
| `package.agent_skills.embedded` | `boolean`      | No       | Indicates that agent skills are embedded in this package. When present, include `AGENTS.md` at the package root.               |
| `package.agent_skills.external` | `string (URL)` | No       | URL to externally hosted agent skills documentation. Use this when skills are not embedded locally.                            |
| `package.distribution_variants` | `list[string]` | Yes      | List of distribution variants this package should be included into. Must only contain: `ecosystem`, `product`, or `candidate`. |
| `models`                        | `list[string]` | No       | List of supported model folder names under `models/`. Leave empty when the package does not declare any models.                |

#### 3.1.2. Example

```yaml
package:
  name: "terramind-geospatial"
  version: "1.2.0"
  agent_skills:
    embedded: true # Indicated embedded agents skill in AGENTS.md
  distribution_variants:
    - "ecosystem"
    - "product"

# List model folder names to include
# Leave empty if no models to include
models:
  - terramind-base-flood # Folder name in models/
  - terramind-base-fire # Folder name in models/
```

---

### 3.2. Model Configuration (`models/<model-name>/model.yaml`)

Each model has its own configuration file defining testing, benchmarking, and
integration requirements.

#### 3.2.1. Fields Summary

##### `model`

| Field   | Type     | Required | Description                                                             |
| ------- | -------- | -------- | ----------------------------------------------------------------------- |
| `id`    | `string` | Yes      | Hugging Face model repository identifier, for example `org/model-name`. |
| `owner` | `string` | No       | Model owner. If omitted, ownership defaults to the Nexus package owner. |

##### `model.vllm`

| Field                   | Type           | Required | Description                                                                                                                                                                                                                                                                                                                                                         |
| ----------------------- | -------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `enabled`               | `boolean`      | Yes      | Must be set to `True` when the `vllm` section is present. Indicates that the model can be served with vLLM. This also requires that at least one of `product` or `candidate` must be set in the parent Nexus package configuration in `package.distribution_variants`. The `vllm` section must be present even for models that support vLLM but require no plugins. |
| `plugins.general`       | `string`       | No       | General vLLM plugin that loads the model class required in the runtime environment.                                                                                                                                                                                                                                                                                 |
| `plugins.io_processors` | `list[string]` | No       | List of vLLM IO processor plugins supported by this model that should be in the runtime environment.                                                                                                                                                                                                                                                                |

##### `model.testing`

| Field          | Type           | Required      | Description                                                                               |
| -------------- | -------------- | ------------- | ----------------------------------------------------------------------------------------- |
| `hardware`     | `object`       | Yes           | Hardware requirements for running the model test suite.                                   |
| `dependencies` | `list[string]` | No            | Additional Python dependencies needed to run the model test suite.                        |
| `commands`     | `list[string]` | Yes           | Commands used to execute the required model tests.                                        |
| `vllm`         | `object`       | Conditionally | Required when `model.vllm.enabled` is `True`, to define vLLM-specific test configuration. |

##### `model.testing.hardware`

| Field              | Type      | Required      | Description                                                                           |
| ------------------ | --------- | ------------- | ------------------------------------------------------------------------------------- |
| `gpu.type`         | `string`  | No            | GPU type required for testing, such as `NVIDIA A100` or `any`.                        |
| `gpu.count`        | `integer` | Conditionally | Required when `gpu` is specified and a GPU count must be declared.                    |
| `gpu.cpu_fallback` | `boolean` | Conditionally | Required when `gpu` is specified to indicate whether CPU-only execution is supported. |
| `cpu.cores`        | `integer` | No            | Minimum CPU core count for testing.                                                   |
| `cpu.ram`          | `string`  | No            | Minimum RAM required for testing.                                                     |

##### `model.testing.vllm`

| Field      | Type           | Required      | Description                                                                             |
| ---------- | -------------- | ------------- | --------------------------------------------------------------------------------------- |
| `commands` | `list[string]` | Conditionally | Required when `model.testing.vllm` is present. Defines the vLLM-specific test commands. |

##### `model.benchmarking`

| Field                | Type           | Required | Description                                                                                                                |
| -------------------- | -------------- | -------- | -------------------------------------------------------------------------------------------------------------------------- |
| `dependencies`       | `list[string]` | No       | Additional Python dependencies needed for benchmarking.                                                                    |
| `experiments`        | `list[object]` | No       | List of benchmark experiments to run for the model. Each experiment name must be in the Algorithm Nexus benchmark catalog. |
| `custom_experiments` | `list[object]` | No       | List of custom benchmark definitions implemented by the package.                                                           |

##### `model.benchmarking.experiments[]`

| Field  | Type     | Required | Description                                                  |
| ------ | -------- | -------- | ------------------------------------------------------------ |
| `name` | `string` | Yes      | Name of the benchmark experiment from the benchmark catalog. |
| `args` | `string` | Yes      | Arguments passed to the benchmark experiment.                |

##### `model.benchmarking.custom_experiments[]`

| Field           | Type     | Required | Description                                                                          |
| --------------- | -------- | -------- | ------------------------------------------------------------------------------------ |
| `name`          | `string` | Yes      | Name of a custom benchmark function. Used when defining custom benchmark logic.      |
| `python_module` | `string` | Yes      | Python module path implementing the custom benchmark, typically under `benchmarks/`. |
| `args`          | `string` | Yes      | Arguments passed to the custom benchmark function.                                   |

Each model can optionally provide usage documentation in
`models/<model-name>/usage.md`. Usage documentation is not configured in
`model.yaml`.

#### 3.2.2. Example

```yaml
model:
  id: "ibm-esa-geospatial/TerraMind-base-Flood"
  owner: "ibm-esa-geospatial-team"

  vllm:
    enabled: true
    plugins:
      io_processors:
        - "terratorch-tm-segmentation"

  testing:
    hardware:
      gpu:
        type: "NVIDIA A100"
        count: 1
        cpu_fallback: false
      cpu:
        cores: 8
        ram: "32GB"

    dependencies:
      - "pytest>=8.0.0"
      - "torch>=2.4.0"
      - "terratorch>=0.99.0"

    commands:
      - "pytest tests/test_inference.py -v"

    vllm:
      commands:
        - "pytest tests/test_vllm.py -v"

  benchmarking:
    dependencies:
      - "torch>=2.4.0"
      - "evaluate>=0.4.0"

    experiments:
      - name: "flood-segmentation"
        args: "--dataset flood.jsonl"

    custom_experiments:
      - name: "regional-flood-benchmark"
        python_module: "benchmarks/regional_flood.py"
        args: "--region emea --resolution 10m"
```
