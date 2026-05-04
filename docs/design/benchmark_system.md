# Algorithm Nexus Benchmarking System

## Executive Summary

This document proposes a benchmarking system for the Algorithm Stack packages
within Algorithm Nexus based on
[the benchmarking requirements](../requirements/benchmark.md).

An analysis of the benchmarking requirements indicates that `ado` natively
fulfills the majority of the complex orchestration, data provenance, and
scalable execution needs for evaluating **benchmark targets** against defined
**workloads**. By combining `ado` and Ray with specific **Algorithm Nexus
Extensions**, integration definitions, and robust administrative processes, the
team can deliver a comprehensive, end-to-end benchmarking solution capable of
generating repeatable **benchmark results**.

To fully satisfy these requirements, the design of the Benchmarking System is
divided into three **Architectural Pillars**: System Architecture (The
Mechanisms), Operational Architecture (The Infrastructure), and Governance &
Conventions (The Standards).

---

## 1. System Architecture (The Mechanisms)

This pillar details the technical components, automated mechanisms, and
execution engines that make up the benchmarking system.

### 1.1 Two-Tiered Packaging Architecture

The system utilizes a two-tiered architecture to strictly separate the
definition of a benchmark experiment from its application to a specific AI
model.

<!-- markdownlint-disable line-length -->

| Tier                                        | Component       | Responsibility & Behavior                                                                                                                                                                                                                                                                              |
| ------------------------------------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Tier 1: Benchmark Experiment Definition** | `ado` core      | Serves as the core capability engine. It provides the framework to define, package, and execute a self-contained benchmark experiment. It enforces strict input/output interfaces, handles versioning of the experiment logic, and manages the execution provenance independently of the target model. |
| **Tier 2: Benchmark Integration**           | `nexus` Package | While `ado` knows _how_ to run an experiment, `nexus` dictates _when_ and _against what_. It provides the declarative metadata required to define a benchmark: bind a specific target (the model) to a specific `ado` benchmark experiment and a defined workload.                                     |

<!-- markdownlint-enable line-length -->

### 1.2 Event & Orchestration Broker

**GitHub** acts as the primary interface and event broker for the system. It
captures user intent and system state changes (e.g., deployments or releases),
routing these events to the underlying execution infrastructure. It acts as the
technical bridge between human operations and the execution engine.

### 1.3 Execution and Orchestration Engine

The execution architecture relies on **Ray** and **`ado`**. `ado` leverages
**Ray** to handle parameter sweeps and single benchmark instances mechanically.
Thanks to `ado`'s data recording capabilities, if one instance in a sweep fails
`ado` continues orchestration and commits successful results to the database.
Ray allows the underlying experiments to explicitly request hardware resources
(e.g., `@ray.remote(num_gpus=1)`) via task decorators. Ray can also create
per-task execution environments, allowing tests with incompatible requirements
to ado-core or other experiments to execute.

### 1.4 Centralized Data & Discovery

The architecture utilizes `ado` distributed projects capabilities to store data,
enforcing a uniform schema for results and custom metadata dictionaries.
Furthermore, `ado` automatically registers available experiments upon
environment installation, providing built-in commands to list and discover them.

#### System Architecture Requirements Matching

<!-- markdownlint-disable line-length -->

| Requirement | Name                           | Fulfillment Strategy | Component     | Proposed Solution                                                                                                         |
| ----------- | ------------------------------ | -------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **REQ 1.1** | Input/Output Specification     | Technology           | `ado` core    | `ado` defines a standard programmatic input/output schema for benchmark experiments.                                      |
| **REQ 1.2** | Python Package                 | Technology           | `ado` core    | `ado` experiments are written purely in Python and distributed as standard packages.                                      |
| **REQ 1.5** | Lifecycle Management           | Technology           | `ado` core    | `ado` natively provides a flag for experiments to mark deprecation.                                                       |
| **REQ 2.2** | Benchmark Experiment Discovery | Technology           | nexus         | The nexus CLI provides built-in commands to list all registered experiments.                                              |
| **REQ 2.4** | Benchmark Discovery            | Technology           | nexus         | The nexus CLI will enable listing all benchmarks defined in all packages (or a specific package or for a specific model). |
| **REQ 3.3** | Benchmark Experiment Reuse     | Technology           | `ado` + nexus | Once registered as described in REQ 2.1, experiments can be universally referenced across projects.                       |
| **REQ 4.1** | Single & Sweep Execution       | Technology           | Ray + `ado`   | `ado` provides the capability to execute single experiment instances and parameter sweeps.                                |
| **REQ 4.2** | Resource Specification         | Technology           | Ray           | Ray allows a benchmark experiment to make explicit hardware resource requests.                                            |
| **REQ 4.4** | Result Capture                 | Technology           | `ado` DB      | `ado` commits successful benchmark results even if parallel instances fail.                                               |
| **REQ 4.5** | Standardized Error Reporting   | Technology           | `ado` core    | Handled natively via standard Python error handling and custom `ado` return payloads.                                     |
| **REQ 4.8** | Local Execution                | Technology           | `ado` core    | `ado` supports local execution for rapid prototyping on local compute.                                                    |
| **REQ 5.1** | Centralized Results Storage    | Technology           | `ado` DB      | `ado` provides centralized remote results storage.                                                                        |
| **REQ 5.2** | Common Results Schema          | Technology           | `ado` core    | `ado` enforces a uniform, structured schema for all stored results.                                                       |
| **REQ 5.3** | Custom Metadata Support        | Technology           | `ado` DB      | `ado` supports returning custom metadata dicts alongside core results.                                                    |

<!-- markdownlint-enable line-length -->

---

## 2. Operational Architecture (Workflows & Infrastructure)

This pillar details how the system is deployed, maintained, triggered, and
scaled by the administrative team and CI/CD pipelines.

### 2.1 Infrastructure Configuration

Admins configure the **Ray cluster** on K8s via KubeRay, with hard namespace
limits to maintain resource quotas during massive sweeps. To optimize
performance, the underlying cluster mounts a shared persistent filesystem (via
PVC) for workload dataset caching. Ray dynamically isolates worker node
environments to prevent dependency version clashes between concurrent
evaluations.

### 2.2 Orchestration Triggers & Automation

The mechanism for triggering centralized administrative evaluations is fully
automated via **GitHub**. These are triggered mechanically via automated GitHub
events (such as code deployments or releases) or on-demand utilizing GitHub
ChatOps. They are executed with a combination of GitHub Actions (on Event or on
schedule) and polling Runners. Global orchestration across multiple packages
utilizes `ado`'s native search space semantics.

#### Operational Requirements Matching

<!-- markdownlint-disable line-length -->

| Requirement | Name                                 | Fulfillment Strategy | Component           | Proposed Solution                                                                                                                                                                                                                                                                                                                                    |
| ----------- | ------------------------------------ | -------------------- | ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **REQ 2.1** | Benchmark Experiment Registration    | Technology + Process | nexus               | Registering a benchmark experiments package involves adding metadata describing the package and the experiments it contains to a Nexus package, as well as validating that all referenced packages can be installed together. Packages provided via any mechanism outlined in REQ 3.2 can be registered. [PENDING: Nexus Test Dependencies Handling] |
| **REQ 2.3** | Benchmark Registration               | Technology + Process | nexus + `ado`       | Registering a benchmark (see REQ 3.1 for specification) involves adding the relevant files and metadata to a nexus package model directory AND those files passing ado+nexus validation. [PENDING: Nexus Model Benchmark Specification Decision].                                                                                                    |
| **REQ 4.3** | Resource Limits                      | Technology + Process | Ray Cluster         | Admins configure Ray clusters to set hard quotas per instance.                                                                                                                                                                                                                                                                                       |
| **REQ 4.6** | Logging                              | Technology + Process | Ray Cluster         | Admins configure infrastructure to persist logs without indefinite retention.                                                                                                                                                                                                                                                                        |
| **REQ 6.2** | Isolated Execution                   | Technology + Process | `ado` + Ray Runtime | Users can describe the benchmark experiment dependencies in the benchmark experiment package using `ado` + Ray semantics. Ray will dynamically create isolated virtual environments per worker.                                                                                                                                                      |
| **REQ 6.3** | Persistent Filesystem                | Technology + Process | Ray / K8s           | Admins configure the cluster to mount a shared PVC for dataset caching.                                                                                                                                                                                                                                                                              |
| **REQ 7.2** | Admin-Triggered Evaluation Execution | Technology + Process | GitHub              | Triggered via automated GitHub events or on-demand via GitHub ChatOps.                                                                                                                                                                                                                                                                               |

<!-- markdownlint-enable line-length -->

---

## 3. Governance & Conventions (Policies & Standards)

This pillar outlines the human-in-the-loop requirements, conventions, and
security policies that contributors must adhere to in order for the technical
and operational systems to function correctly.

### 3.1 Trust and Security Model

Nexus relies on an organizational trust model. Only authorized IBMers can submit
code. To enforce security, all packages undergo mandatory standard CI/CD CVE
scans before they are allowed into the execution environment.

### 3.2 Packaging and Versioning Conventions

While `ado` provides the mechanism for versioning and reproducibility,
contributors are bound by strict conventions to ensure uniqueness and
reliability.

- **Reproducibility Contract:** Contributors must adhere to the convention that
  an experiment name plus specific parameter values defines a unique, repeatable
  execution. Repeatable here means **the experiment instance use an identical
  process** not produces the same result, as experiments can be stochastic.
- **Versioning**: ado provides mechanisms for experiment versioning but does not
  prescribe any. The main convention w.r.t experiment versioning is that
  whatever mechanism is chosen ensures the **Reproducibility Contract**
- **Data Handling Guidelines:** Workload data must either be bundled directly
  inside the benchmark experiment package or programmed to download dynamically
  at execution time.

### 3.3 Governance of Sweeps

Because parameter sweeps are computationally expensive, they must undergo
particular scrutiny, with admins retaining manual and automated review
oversight. Sweep configurations must pass GitHub PR approvals prior to being
submitted to the Ray cluster for execution.

#### Governance Requirements Matching

<!-- markdownlint-disable line-length -->

| Requirement | Name                            | Fulfillment Strategy    | Component     | Proposed Solution                                                                                                                                                         |
| ----------- | ------------------------------- | ----------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **REQ 1.3** | Versioning                      | Technology + Convention | `ado` + nexus | Users leverage `ado` capabilities to specify versions while adhering to semantic naming standards. [PENDING: Versioning Semantics Decision]                               |
| **REQ 1.4** | Reproducible Execution          | Technology + Convention | `ado` + nexus | Users must adhere to ado`'s convention that a given experiment name encodes a unique, repeatable experiment.                                                              |
| **REQ 1.7** | Required Data                   | Technology + Convention | `ado`         | Developers bundle data with benchmark experiment packages or the experiment downloads it dynamically.                                                                     |
| **REQ 4.7** | Self-Contained Execution        | Technology + Convention | `ado`         | As REQ 1.7                                                                                                                                                                |
| **REQ 3.1** | Benchmark Specification         | Technology + Process    | `ado` config  | Users specify benchmarks by creating an `ado` config that binds an experiment to a workload.                                                                              |
| **REQ 3.2** | Providing Benchmark Experiments | Technology + Process    | `ado` + nexus | Benchmark experiment packages (following Standardized Benchmarking Packaging Protocol) can be provided in a Nexus package in the Algorithm Nexus repo, on PyPI or GitHub. |
| **REQ 6.1** | Admin Security                  | Process                 | CI            | Secured via trusted code submissions and mandatory CVE scans.                                                                                                             |
| **REQ 7.1** | Nexus-Level Benchmarks          | Technology + Process    | `ado` + nexus | These are benchmarks defined independently using `ado` configuration semantics and stored in the nexus repository. [PENDING: Nexus Repo Layout Decision]                  |
| **REQ 7.3** | Sweep Review and Approval       | Process                 | GitHub PRs    | Admins retain review oversight of sweep configurations via GitHub PR workflows.                                                                                           |

<!-- markdownlint-enable line-length -->

---

## Open Questions

The following questions/decisions are open and can be resolved in subsequent
issues.

- Versioning Semantics for REQ 1.3
  - Rules and conventions for versioning benchmark experiments
- Nexus Test Dependencies Handling for REQ 2.2
  - The process for validating that the benchmark packages referenced by a nexus
    package can be installed together
- Nexus Model Benchmark Specification Decision for REQ 2.3
  - Exact YAML metadata and directory structure used to add a Nexus Model
    benchmark specification
- Nexus Repo Layout for REQ 7.1
  - Exact YAML metadata and directory structure used to add a Nexus benchmark
    specification

## How Nexus package developers will use the system

### Contributing a benchmark experiment

Developers write and package the experiment according to the standardized
packaging protocol (REQ 3.2) i.e. as an ado custom experiment or
actuator+experiments. They put the package on GitHub, PyPI or in the algorithm
nexus repo (REQ 3.2).

### Defining the benchmark experiment packages used by a nexus package

Nexus package owners register the benchmark experiment packages, and the
experiments they want to use, by referencing them in their nexus package's
metadata (REQ 2.1) and validating that all the benchmark experiments the package
needs can be installed together.

### Defining a benchmark to use for a model

First developers can:

- use `nexus` CLI and `ado` CLI to discover existing benchmark experiments (REQ
  2.2)
- use `nexus` CLI to discover existing benchmark specifications (REQ 2.4)

They then define their benchmark using an ado configuration (REQ 3.1) adding
this to the model directory of the relevant nexus package (REQ 2.3). The
benchmark configuration can reference any benchmark experiment registered by the
Nexus package. If the benchmark experiment they need is not registered by the
nexus package [they can add it.](#defining-a-benchmark-to-use-for-a-model). The
benchmark configuration can also be based on one discovered via the Nexus CLI.
