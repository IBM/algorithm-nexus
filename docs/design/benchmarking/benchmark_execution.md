# Benchmark Execution and Operations

## Executive Summary

This document specifies how benchmark experiments are executed and operated:
`ado` and Ray, GitHub triggers, the admin cluster, and versioning conventions.

An analysis of the benchmarking requirements indicates that `ado` natively
fulfills the majority of the complex orchestration, data provenance, and
scalable execution needs for evaluating **benchmark targets** against defined
**benchmark instances**. By combining `ado` and Ray with specific **Algorithm
Nexus Extensions**, integration definitions, and robust administrative
processes, the team can deliver a comprehensive, end-to-end benchmarking
solution capable of generating repeatable **benchmark results**.

This document organizes that execution design into three pillars: System
Architecture (the mechanisms), Operational Architecture (the infrastructure),
and Governance & Conventions (the standards).

---

## 1. System Architecture (The Mechanisms)

This pillar details the technical components, automated mechanisms, and
execution engines that make up the benchmarking system.

### 1.1 Layered Architecture

Benchmarking has three layers. This document covers execution. The other two
layers are specified in their own documents, listed from the
[Benchmarking Architecture](./index.md) overview:

| Layer                                | Document                                                                            | Responsibility                                                                                     |
| ------------------------------------ | ----------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| **Execution**                        | This document                                                                       | `ado` experiment packages, Ray, the result store, GitHub and admin triggers, and sweep governance. |
| **Experiments and submissions**      | [Benchmark Experiments and Submissions](./benchmark_experiments_and_submissions.md) | Which experiments a package exposes, and the submissions that apply them to a target and instance. |
| **Logical benchmarks and instances** | [Logical Benchmarks and Instances](./logical_benchmarks_and_instances.md)           | The shared problem definition, concrete instances, and how results are aggregated.                 |

`ado` defines, packages, and executes a self-contained benchmark experiment. It
enforces input and output interfaces, versions the experiment logic, and records
provenance independently of the benchmark target. Nexus metadata says which
experiment is used, and against which benchmark target and instance. That metadata
is specified in
[Benchmark Experiments and Submissions](./benchmark_experiments_and_submissions.md).

### 1.2 Event & Orchestration Broker

**GitHub** acts as the primary interface and event broker for the system. It
captures user intent and system state changes (e.g., deployments or releases),
routing these events to the underlying execution infrastructure. It acts as the
technical bridge between human operations and the execution engine.

### 1.3 Execution and Orchestration Engine

The execution architecture relies on **Ray** and **`ado`**. `ado` leverages
**Ray** to handle parameter sweeps and single benchmark submissions
mechanically. Thanks to `ado`'s data recording capabilities, if one submission
in a sweep fails `ado` continues orchestration and commits successful results to
the database. Ray allows the underlying experiments to explicitly request
hardware resources (e.g., `@ray.remote(num_gpus=1)`) via task decorators. Ray
can also create per-task execution environments, allowing tests with
incompatible requirements to ado-core or other experiments to execute.

### 1.4 Centralized Data & Discovery

The architecture utilizes `ado` distributed projects capabilities to store data,
enforcing a uniform schema for results and custom metadata dictionaries.
Furthermore, `ado` automatically registers available experiments upon
environment installation, providing built-in commands to list and discover them.

#### System Architecture Requirements Matching

<!-- markdownlint-disable line-length -->

| Requirement | Name                           | Fulfillment Strategy | Component     | Proposed Solution                                                                                                         |
| ------------| -------------------------------| ---------------------| --------------| --------------------------------------------------------------------------------------------------------------------------|
| **REQ 1.1** | Input/Output Specification     | Technology           | `ado` core    | `ado` defines a standard programmatic input/output schema for benchmark experiments.                                      |
| **REQ 1.2** | Python Package                 | Technology           | `ado` core    | `ado` experiments are written purely in Python and distributed as standard packages.                                      |
| **REQ 1.5** | Lifecycle Management           | Technology           | `ado` core    | `ado` natively provides a flag for experiments to mark deprecation.                                                       |
| **REQ 4.1** | Single & Sweep Execution       | Technology           | Ray + `ado`   | `ado` provides the capability to execute single benchmark submissions and parameter sweeps.                               |
| **REQ 4.2** | Resource Specification         | Technology           | Ray           | Ray allows a benchmark experiment to make explicit hardware resource requests.                                            |
| **REQ 4.4** | Result Capture                 | Technology           | `ado` DB      | `ado` commits successful benchmark results even if parallel submissions fail.                                             |
| **REQ 4.5** | Standardized Error Reporting   | Technology           | `ado` core    | Handled natively via standard Python error handling and custom `ado` return payloads.                                     |
| **REQ 4.8** | Local Execution                | Technology           | `ado` core    | `ado` supports local execution for rapid prototyping on local compute.                                                    |
| **REQ 5.1** | Centralized Results Storage    | Technology           | `ado` DB      | `ado` provides centralized remote results storage.                                                                        |

<!-- markdownlint-enable line-length -->

---

## 2. Operational Architecture (Workflows & Infrastructure)

This pillar details how the system is deployed, maintained, triggered, and
scaled by the administrative team and CI/CD pipelines.

### 2.1 Infrastructure Configuration

Admins configure the **Ray cluster** on K8s via KubeRay, with hard namespace
limits to maintain resource quotas during massive sweeps. To optimize
performance, the underlying cluster mounts a shared persistent filesystem (via
PVC) for benchmark instance dataset caching. Ray dynamically isolates worker
node environments to prevent dependency version clashes between concurrent
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

| Requirement | Name                                      | Fulfillment Strategy | Component           | Proposed Solution                                                                                                                                                                                                                                                                                                                                      |
| ------------| ------------------------------------------| ---------------------| --------------------| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **REQ 4.3** | Resource Limits                           | Technology + Process | Ray Cluster         | Admins configure Ray clusters to set hard quotas per instance.                                                                                                                                                                                                                                                                                         |
| **REQ 4.6** | Logging                                   | Technology + Process | Ray Cluster         | Admins configure infrastructure to persist logs without indefinite retention.                                                                                                                                                                                                                                                                          |
| **REQ 6.2** | Isolated Execution                        | Technology + Process | `ado` + Ray Runtime | Users can describe the benchmark experiment dependencies in the benchmark experiment package using `ado` + Ray semantics. Ray will dynamically create isolated virtual environments per worker.                                                                                                                                                        |
| **REQ 6.3** | Persistent Filesystem                     | Technology + Process | Ray / K8s           | Admins configure the cluster to mount a shared PVC for dataset caching.                                                                                                                                                                                                                                                                                |
| **REQ 7.2** | Admin-Triggered Evaluation Execution      | Technology + Process | GitHub              | Triggered via automated GitHub events or on-demand via GitHub ChatOps.                                                                                                                                                                                                                                                                                 |

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
  execution. Repeatable here means **the benchmark submission uses an identical
  process** not produces the same result, as experiments can be stochastic.
- **Versioning**: ado provides mechanisms for experiment versioning but does not
  prescribe any. The main convention w.r.t experiment versioning is that
  whatever mechanism is chosen ensures the **Reproducibility Contract**
- **Data Handling Guidelines:** Benchmark instance data must either be bundled
  directly inside the benchmark experiment package or programmed to download
  dynamically at execution time.

### 3.3 Governance of Sweeps

Because parameter sweeps are computationally expensive, they must undergo
particular scrutiny, with admins retaining manual and automated review
oversight. Sweep configurations must pass GitHub PR approvals prior to being
submitted to the Ray cluster for execution.

#### Governance Requirements Matching

<!-- markdownlint-disable line-length -->

| Requirement | Name                            | Fulfillment Strategy    | Component     | Proposed Solution                                                                                                                                                         |
| ------------| --------------------------------| ------------------------| --------------| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **REQ 1.3** | Versioning                      | Technology + Convention | `ado` + nexus | Users leverage `ado` capabilities to specify versions while adhering to semantic naming standards. \[PENDING: Versioning Semantics Decision\]                             |
| **REQ 1.4** | Reproducible Execution          | Technology + Convention | `ado` + nexus | Users must adhere to ado`'s convention that a given experiment name encodes a unique, repeatable experiment.                                                              |
| **REQ 1.7** | Required Data                   | Technology + Convention | `ado`         | Developers bundle data with benchmark experiment packages or the experiment downloads it dynamically.                                                                     |
| **REQ 4.7** | Self-Contained Execution        | Technology + Convention | `ado`         | As REQ 1.7                                                                                                                                                                |
| **REQ 6.1** | Admin Execution                 | Process                 | CI            | Admin infrastructure can execute submissions. Access is limited to trusted code and mandatory CVE scans.                                                                  |
| **REQ 7.3** | Sweep Review and Approval       | Process                 | GitHub PRs    | Admins retain review oversight of sweep configurations via GitHub PR workflows.                                                                                           |

<!-- markdownlint-enable line-length -->

---

## Open Questions

The following questions/decisions are open and can be resolved in subsequent
issues.

- Versioning Semantics for REQ 1.3
    - Rules and conventions for versioning benchmark experiments
- Nexus Test Dependencies Handling for REQ 2.3
    - The process for validating that the benchmark experiment packages
      referenced by an experiment registration can be installed together

## How Nexus package developers will use the system

### Contributing a benchmark experiment

Developers write and package the experiment according to the standardized
packaging protocol (REQ 3.2) i.e. as an ado custom experiment or
actuator+experiments. They put the package on GitHub or PyPI (REQ 3.2).

### Registering a benchmark experiment

Experiment packages, and the experiment identifiers they expose, are registered
in `experiments/<name>/experiment_package.yaml` (REQ 2.3). See
[Benchmark Experiments and Submissions](./benchmark_experiments_and_submissions.md).

### Defining a benchmark submission

First developers can:

- use `nexus` CLI and `ado` CLI to discover existing benchmark experiments (REQ
  2.5)
- use `nexus` CLI to discover existing benchmark submissions (REQ 2.5)

They then register a benchmark submission using an ado configuration (REQ 3.1,
REQ 2.4). Where that submission is registered is specified in
[Benchmark Experiments and Submissions](./benchmark_experiments_and_submissions.md):
a folder under `experiments/<name>/submissions/`. The submission can reference
any registered benchmark experiment. If the experiment they need is not
registered
[they can add it.](#registering-a-benchmark-experiment).
The submission can also be based on one discovered via the Nexus CLI.
