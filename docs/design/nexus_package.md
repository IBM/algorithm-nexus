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
supports. Its purpose is validation and integration of Algorithm Stack Packages
into the Algorithm Nexus ecosystem.

The Nexus package serves as a registry entry that:

- References a Python package with versioned releases on GitHub or PyPI
- Defines which models are supported by that Python package
- Enables dependency resolution across all packages in the Algorithm Nexus
- Can optionally register benchmark experiments and model-specific benchmark
  definitions for benchmarking workflows

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
    ├── benchmarks/        # Optional local benchmark experiment package
    └── models/
        ├── <model-1>/
        │   ├── model.yaml # Required model metadata
        │   ├── benchmarks.yaml # Optional per-model benchmark definitions
        │   └── usage.md   # Optional usage documentation
        ├── <model-2>/
        │   └── ...
        └── ...
```

The required root file is `nexus.yaml`, which declares the Nexus package
metadata. `skills` is optional and should only be included when the package
provides agent skills to assist users in using the package. The optional
`benchmarks/` folder is the standard place for local benchmark experiment code
and should contain a Python package that follows the
[ADO custom experiment](https://ibm.github.io/ado/actuators/creating-custom-experiments/)
pattern. The `models/` folder is required whenever a Nexus package wants to
advertise one or more models, with one sub-folder for each model. Each model
folder must contain a `model.yaml` file describing the model metadata and
optional vLLM integration. Each model folder can optionally include a sibling
`benchmarks.yaml` file to define model-specific benchmark configurations and a
`usage.md` file to provide users with model-specific usage guidance.

---

## 3. Configuration Files

### 3.1. Nexus Package Configuration (`nexus.yaml`)

The `nexus.yaml` file defines package-level metadata and references the external
Python package and its supported models.

#### 3.1.1. Fields Summary

`package`

| Field                   | Type     | Required | Description                                                                                                              |
| ----------------------- | -------- | -------- | ------------------------------------------------------------------------------------------------------------------------ |
| `name`                  | `string` | Yes      | Python package name used as the Nexus package identifier. The package must publish versioned releases on GitHub or PyPI. |
| `benchmark_experiments` | `list`   | No       | Package-level benchmark experiment registrations available to models in this Nexus package.                              |

`package.benchmark_experiments[]`

| Field          | Type     | Required | Description                                                                                                       |
| -------------- | -------- | -------- | ----------------------------------------------------------------------------------------------------------------- |
| `name`         | `string` | Yes      | Benchmark experiment identifier. The identifier is expected to resolve to an ADO custom experiment.               |
| `distribution` | `string` | Yes      | Source of the benchmark experiment. Must be one of `package`, `local`, or `url`.                                  |
| `url`          | `string` | No       | Required only when `distribution` is `url`; points to a repository that follows the ADO custom experiment format. |

#### 3.1.2. Example

```yaml
package:
  name: "terratorch"

  benchmark_experiments:
    - name: "native-flood-eval"
      distribution: "package"

    - name: "local-segmentation-eval"
      distribution: "local"

    - name: "leaderboard-baseline"
      distribution: "url"
      url: "https://github.com/example-org/ado-leaderboard-benchmarks"
```

Benchmark experiments are registered only at package level. The `distribution`
field indicates whether the experiment is exposed directly by the installed
package, by the package-local [`benchmarks/`](../../packages/terratorch/) Python
package, or by a remote repository referenced through `url`.

#### 3.1.3. Agent Skills

Nexus packages can optionally include agent skills to assist users in working
with the package. Agent skills must be placed in the `skills` folder in the
package root, with one sub-folder for each skill. Agent skills should follow the
[agent skills specification](https://agentskills.io/specification) to guarantee
maximum interoperability across different agents.

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
`models/<model-name>/usage.md`.

Benchmark configuration should remain separate from
`models/<model-name>/model.yaml`. When a model defines benchmarks, they should
be described in a sibling
[`benchmarks.yaml`](../../packages/terratorch/models/prithvi/) file that
references one of the package-level registered benchmark experiments and
provides the parameter mapping to pass to that experiment.

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
