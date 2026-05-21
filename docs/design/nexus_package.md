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
- Can optionally register benchmark packages, package-level baseline benchmark
  instances, and model-specific benchmark instances for benchmarking workflows

---

## 2. Folder Structure

Each Nexus package must be placed under the top-level `packages/` directory in
the repository. Within `packages/`, each package directory must contain the
following structure:

```text
packages/
└── <nexus-package-name>/
    ├── nexus.yaml               # Required package metadata
    ├── skills                   # Optional agent skills resources
    ├── benchmark_packages/      # Optional local benchmark packages
    ├── benchmark_instances/     # Optional package-level baseline benchmark instances
    │   └── <benchmark-instance-name>/
    │       └── space.yaml       # Required ADO discoveryspace for that benchmark instance
    └── models/
        ├── <model-1>/
        │   ├── model.yaml       # Required model metadata
        │   ├── benchmark_instances/ # Optional per-model benchmark instances
        │   │   └── <benchmark-instance-name>/
        │   │       └── space.yaml   # Required ADO discoveryspace for that benchmark instance
        │   └── usage.md         # Optional usage documentation
        ├── <model-2>/
        │   └── ...
        └── ...
```

The required root file is `nexus.yaml`, which declares the Nexus package
metadata. `skills` is optional and should only be included when the package
provides agent skills to assist users in using the package. The optional
`benchmark_packages/` folder stores local benchmark packages, and each such
package should follow the
[ADO custom experiment](https://ibm.github.io/ado/actuators/creating-custom-experiments/)
template. A Nexus package can also optionally define a top-level
`benchmark_instances/` folder for baseline experiments that live at package
scope rather than under a specific model. Each benchmark instance in that folder
must have its own sub-folder containing a `space.yaml` file. The `models/`
folder is required whenever a Nexus package wants to advertise one or more
models, with one sub-folder for each model. Each model folder must contain a
`model.yaml` file describing the model metadata and optional vLLM integration.
Each model folder can optionally include a sibling `benchmark_instances/`
folder. Inside `benchmark_instances/`, each benchmark instance must have its own
sub-folder, and that sub-folder must contain a `space.yaml` file defining the
full ADO discoveryspace for that specific benchmark instance. A `usage.md` file
can also be included to provide users with model-specific usage guidance.

---

## 3. Configuration Files

### 3.1. Nexus Package Configuration (`nexus.yaml`)

The `nexus.yaml` file defines package-level metadata and references the external
Python package and its supported models.

#### 3.1.1. Fields Summary

`package`

| Field                | Type     | Required | Description                                                                                                              |
| -------------------- | -------- | -------- | ------------------------------------------------------------------------------------------------------------------------ |
| `name`               | `string` | Yes      | Python package name used as the Nexus package identifier. The package must publish versioned releases on GitHub or PyPI. |
| `benchmark_packages` | `list`   | No       | Package-level benchmark package registrations available to models in this Nexus package.                                 |

`package.benchmark_packages[]`

| Field                   | Type           | Required | Description                                                                                                                                                                                                                         |
| ----------------------- | -------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `requirement_specifier` | `string`       | Yes      | Python package requirement target for the benchmark package. It may be a Python package name, a URL to a Python package or source repository, or a local path to a Python package within `./packages` in the Nexus repository root. |
| `experiments`           | `list[string]` | Yes      | Experiment identifiers exposed by that benchmark package and made available to models in the Nexus package.                                                                                                                         |

#### 3.1.2. Example

```yaml
package:
  name: "terratorch"

  benchmark_packages:
    - requirement_specifier: "./packages/terratorch/benchmark_packages/segmentation-benchmarks"
      experiments:
        - "local-segmentation-eval"
        - "local-boundary-eval"

    - requirement_specifier: "https://github.com/example-org/example-benchmarks"
      experiments:
        - "leaderboard-baseline"

    - requirement_specifier: "example-benchmark-package"
      experiments:
        - "packaged-baseline"
```

Benchmark packages are registered only at package level. Each registration uses
a `requirement_specifier` to identify how the benchmark package is resolved and
an `experiments` list to declare which experiment identifiers from that package
are made available to the Nexus package. The `requirement_specifier` may be a
Python package name, a URL to a Python package or source repository, or a local
path to a Python package within `./packages` in the Nexus repository root. In
all cases, the referenced package is expected to follow the ADO custom
experiment template.

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

#### 3.2.3. Benchmarks

Benchmark configuration should remain separate from
`models/<model-name>/model.yaml`. When a Nexus package defines baseline
benchmarks, they should be described in a top-level `benchmark_instances/`
folder in the package root. When a model defines model-specific benchmarks, they
should be described in a sibling `benchmark_instances/` folder. In either
location, each benchmark instance must have its own sub-folder that provides a
[`space.yaml`](https://ibm.github.io/ado/actuators/creating-custom-experiments/#using-your-custom-experiment-in-a-discoveryspace)
file with the full ADO discoveryspace definition for that benchmark run. The
experiment referenced in `space.yaml` must be one of the experiment identifiers
registered through `package.benchmark_packages`.
