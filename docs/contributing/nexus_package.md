<!--
Copyright IBM Corporation 2026
SPDX-License-Identifier: Apache-2.0
-->

# Nexus Package Structure Guide

This document defines the folder structure and configuration files for a Nexus
package based on the requirements outlined in the
[`Nexus Package`](../requirements/nexus_package.md) requirements document.

## 1. Overview

A Nexus package is a **metadata and configuration package** that references an
external Python package (released on GitHub or PyPI) and defines the models it
supports. The Nexus package **does not contain the Python package source code
itself**, but rather provides standardized metadata for validation and
integration within the Algorithm Nexus ecosystem.

The Nexus package serves as a registry entry that:

- References a Python package with versioned releases on GitHub or PyPI
- Defines which models are supported by that Python package
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
    ├── skills             # Optional agent skills resources
    └── models/
        ├── <model-1>/
        │   ├── model.yaml # Required model metadata
        │   └── usage.md   # Optional usage documentation
        ├── <model-2>/
        │   └── ...
        └── ...
```

The required root file is `nexus.yaml`, which declares the Nexus package
metadata and the list of supported model folders. `skills` is optional and
should only be included when the package provides embedded agent skills material
to assist users in using the package. The `models/` directory is required
whenever the package declares one or more supported models, and each model
folder must contain a `model.yaml` file describing the model metadata and
optional vLLM integration. Each model folder can optionally include a `usage.md`
file to provide users with model-specific usage guidance.

---

## 3. Configuration Files

### 3.1. Nexus Package Configuration (`nexus.yaml`)

The `nexus.yaml` file defines package-level metadata and references the external
Python package and its supported models.

#### 3.1.1. Fields Summary

| Field                           | Type           | Required | Description                                                                                                                          |
| ------------------------------- | -------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `package.name`                  | `string`       | Yes      | Python package name used as the Nexus package identifier. The package must publish versioned releases on GitHub or PyPI.             |
| `package.agent_skills.embedded` | `boolean`      | No       | Indicates that agent skills are embedded in this package. When present, include the `skills` folder at the package root.<sup>1</sup> |
| `package.agent_skills.external` | `string (URL)` | No       | URL to externally hosted agent skills resources.<sup>2</sup>                                                                         |
| `models`                        | `list[string]` | No       | List of supported model folder names under `models/`. Leave empty when the package does not declare any models.                      |

<sup>1</sup> One sub-folder for each skill must be created in the `skills`
folder. Agent skills should follow the
[agent skills specification](https://agentskills.io/specification) to guarantee
maximum interoperability across different agents.

<sup>2</sup> The URL must point to a `skills` folder on a remote server.

#### 3.1.2. Example

```yaml
package:
  name: "terramind-geospatial"
  agent_skills:
    embedded: true # Indicates embedded agent skills in skills/ folder

# List model folder names to include
# Leave empty if no models to include
models:
  - terramind-base-flood # Folder name in models/
  - terramind-base-fire # Folder name in models/
```

---

### 3.2. Model Configuration (`models/<model-name>/model.yaml`)

Each model has its own configuration file defining integration requirements.

#### 3.2.1. Fields Summary

##### `model`

| Field   | Type     | Required | Description                                                                                                                                            |
| ------- | -------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `id`    | `string` | Yes      | Hugging Face model repository identifier, for example `org/model-name`.                                                                                |
| `owner` | `string` | No       | Model owner GitHub identifier. If omitted, ownership defaults to the Nexus package owner.                                                              |
| `vllm`  | `object` | No       | Only required for models that need additional vLLM plugins and belong to a Nexus Package targeting the `product` or `candidate` distribution variants. |

##### `model.vllm`

| Field                   | Type           | Required | Description                                                                                          |
| ----------------------- | -------------- | -------- | ---------------------------------------------------------------------------------------------------- |
| `enabled`               | `boolean`      | Yes      | Must be `true` to enable vLLM serving for this model.                                                |
| `plugins.general`       | `string`       | No       | General vLLM plugin that loads the model class required in the runtime environment.                  |
| `plugins.io_processors` | `list[string]` | No       | List of vLLM IO processor plugins supported by this model that should be in the runtime environment. |

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
```
