# Algorithm Nexus Benchmarking System

## Executive Summary

This document proposes the adoption of the open-source **Accelerated Discovery
Orchestrator (`ado`)** framework, powered by the **Ray** distributed computing
engine, as the foundational architecture for the Algorithm Nexus benchmarking
system.

An analysis of the benchmarking requirements indicates that `ado` natively
fulfills the majority of the complex orchestration, data provenance, and
scalable execution needs for evaluating **benchmark targets** against defined
**workloads**. By combining `ado` and Ray with specific **Algorithm Nexus
Extensions** (treating all **benchmark experiments** as standardized Python
packages) and robust **Admin Processes** (CI/CD integration, trust models, and
cluster management), the team can deliver a comprehensive, end-to-end
benchmarking solution capable of generating repeatable **benchmark results**
across various **benchmark instances**.

## High-Level Architecture Overview

The proposed system consists of five main pillars:

1. **User/Admin Interface Tier (`ado` Client):** The `ado` CLI and Python API
    serve as the primary entry point for package owners to discover **benchmark
    experiments**, configure **benchmarks**, and view **benchmark results**.
2. **Orchestration & Provenance Tier (`ado` Core):** The `ado` internal
    protocols handle parameter tracking for **workloads**, automatically track
    the provenance of data and operations, and manage the structured storage of
    results across all **benchmark instances**.
3. **Execution Tier (Ray Engine):** `ado` delegates the actual execution of
    benchmark instances to a Ray cluster, which handles distributed execution,
    resource allocation, and worker isolation.
4. **Nexus Extensions (Packaging Strategy):** All benchmark experiments are
    integrated as standard Python packages within the Nexus repository.
    Installing the packages for a specific Nexus version allows users to
    seamlessly browse and execute available evaluations locally or on the
    cluster.
5. **Admin Processes (Governance & Infrastructure):** Defines the operational
    trust model (e.g., executing trusted code via IBMer submissions and CVE
    scans), manual sweep oversight, CI automation, and Ray cluster configuration
    (PVCs and log persistence).

---

## Architecture Details

### Standardized Benchmark Packaging Protocol

The `ado` extension framework dictates the architecture for defining **benchmark
experiments**. `ado` enforces strict input/output interfaces for all tools and
experiments. Because `ado` is purely Python-based, wrapping external frameworks
simply involves writing a Python class adapter distributed as a standard
package. Versioning and reproducibility are natively handled by `ado`'s
data-reuse protocols, which track the exact combination of an experiment name
and its parameters to define a unique execution. Data dependencies are managed
either via standard Python package data inclusion or by the experiment's
internal logic downloading the required workload files at runtime.

<!-- markdownlint-disable-next-line MD024 -->
#### Requirements Matching

<!-- markdownlint-disable line-length -->

| Requirement | Name                       | Proposed Solution                                                                                                                                            |
| :---------- | :------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **REQ 1.1** | Input/Output Specification | `ado` enforces a standard programmatic input/output schema. Experiments natively accept the benchmark target alongside parameterizable kwargs.               |
| **REQ 1.2** | Python Package             | `ado` and all wrappers are written purely in Python and distributed as standard packages with explicitly defined dependencies loaded by Ray.                 |
| **REQ 1.3** | Versioning                 | `ado` allows arbitrary parameters (e.g., version strings) to be passed and tracked, satisfying varying versioning approaches.                                |
| **REQ 1.4** | Reproducible Execution     | `ado`'s provenance tracking guarantees that an experiment name plus specific parameter values defines a unique, repeatable execution.                        |
| **REQ 1.5** | Lifecycle Management       | `ado` natively provides a flag for experiments to mark deprecation, visible to users to prevent technical debt.                                              |
| **REQ 1.7** | Required Data              | Workload data is either bundled directly inside the Nexus Python package or the `ado` experiment is programmed to download it dynamically at execution time. |

<!-- markdownlint-enable line-length -->

### Benchmark Registration and Discoverability

In this area, the architecture leverages standard Python packaging combined with
`ado`'s native CLI. Benchmark experiments are committed as Python packages
directly within the Nexus repository. When a user installs a Nexus version,
`ado` automatically registers the available experiments. Users can use the `ado`
CLI or database to list registered experiments, defined **benchmarks** (fixed or
parameterized), and the targets utilizing them.

<!-- markdownlint-disable-next-line MD024 -->
#### Requirements Matching

<!-- markdownlint-disable line-length -->

| Requirement | Name                              | Proposed Solution                                                                                                                                                         |
| :---------- | :-------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **REQ 2.1** | Benchmark Experiment Registration | Registration is achieved by committing the benchmark experiment Python package to Nexus. Installing the package registers it with the local `ado` instance.               |
| **REQ 2.2** | Benchmark Experiment Discovery    | `ado` CLI & Python API provides built-in commands to list and discover all registered benchmark experiments, including deprecated ones.                                   |
| **REQ 2.3** | Benchmark Registration            | A benchmark is formally registered by saving an `ado` configuration (YAML or Python) that binds a benchmark experiment (fixed or parameterizable) to a specific workload. |
| **REQ 2.4** | Benchmark Discovery               | By querying the centralized `ado` database, users can discover defined benchmarks and trace which benchmark targets have executed them.                                   |

<!-- markdownlint-enable line-length -->

### Using the Benchmarking System

Contributors interact with the architecture through Python code and `ado`
configuration semantics. They are responsible for specifying which benchmark
they want to use, or if a new one is needed, encapsulating their custom logic
into a standard Python package that conforms to the `ado` interface.

<!-- markdownlint-disable-next-line MD024 -->
#### Requirements Matching

<!-- markdownlint-disable line-length -->

| Requirement | Name                            | Proposed Solution                                                                                                                                     |
| :---------- | :------------------------------ | :---------------------------------------------------------------------------------------------------------------------------------------------------- |
| **REQ 3.1** | Benchmark Specification         | Package owners use the `ado` CLI or API to specify the registered benchmark configuration they wish to execute against their target.                  |
| **REQ 3.2** | Providing Benchmark Experiments | Package owners provide custom benchmark experiment scripts as new `ado` extensions, packaged in compliance with Nexus standards.                      |
| **REQ 3.3** | Benchmark Experiment Reuse      | Once an experiment is registered in the `ado` environment via a Nexus package, it can be universally referenced and reused across different projects. |

<!-- markdownlint-enable line-length -->

### Execution and Orchestration

Execution architecture relies on Ray. `ado` leverages `raytune` to handle
parameter sweeps and single **benchmark instances**. Ray allows experiments to
explicitly request hardware resources (like GPUs) via task decorators, while
admins maintain control by setting hard namespace limits. Ray isolates
individual tasks, meaning if one instance in a sweep fails, the others continue.

<!-- markdownlint-disable-next-line MD024 -->
#### Requirements Matching

<!-- markdownlint-disable line-length -->

| Requirement | Name                         | Proposed Solution                                                                                                                                                           |
| :---------- | :--------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **REQ 4.1** | Single and Sweep Execution   | `ado` uses Ray's built-in samplers and optimizers out-of-the-box for both single benchmark instances and parameter sweeps.                                                  |
| **REQ 4.2** | Resource Specification       | Ray allows explicit hardware resource requests (e.g., `@ray.remote(num_gpus=1)`) within the benchmark experiment code.                                                      |
| **REQ 4.3** | Resource Limits              | A configured Ray cluster allows admins to set hard quotas and resource limits per instance or set of instances.                                                             |
| **REQ 4.4** | Result Capture               | Ray isolates instances; `ado` independently commits successful benchmark results to the database even if parallel instances fail.                                           |
| **REQ 4.5** | Standardized Error Reporting | Handled natively via standard Python error handling and custom return payloads within the `ado` interface.                                                                  |
| **REQ 4.6** | Logging                      | Admins will configure the Ray cluster infrastructure to capture and persist Ray logs (including tracebacks), making them accessible without requiring indefinite retention. |
| **REQ 4.7** | Self-Contained Execution     | Ray spins up isolated, stateless worker processes, ensuring experiments cannot rely on unmanaged pre-existing data on the filesystem.                                       |
| **REQ 4.8** | Local Execution              | `ado` + Ray natively supports local, single-node execution for rapid prototyping by users with sufficient local compute.                                                    |

<!-- markdownlint-enable line-length -->

### Data Storage and Analysis

For centralized data tracking, the architecture utilizes `ado` "Distributed
Projects." This connects the execution engine to a remote database, ensuring all
**benchmark results** are logged centrally. `ado`'s automatic data-tracking
enforces a uniform schema across all benchmark instances and allows custom
metadata dictionaries to be attached to preserve context.

<!-- markdownlint-disable-next-line MD024 -->
#### Requirements Matching

<!-- markdownlint-disable line-length -->

| Requirement | Name                        | Proposed Solution                                                                                                                                     |
| :---------- | :-------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------- |
| **REQ 5.1** | Centralized Results Storage | `ado` Distributed Projects uses a remote database connection to store and centralize results for cross-model comparison and package owner inspection. |
| **REQ 5.2** | Common Results Schema       | `ado`'s automatic data-tracking enforces a uniform, structured schema and metadata standard for all stored benchmark results.                         |
| **REQ 5.3** | Custom Metadata Support     | `ado` result interfaces support returning and storing custom metadata dicts alongside core quantitative execution results.                            |

<!-- markdownlint-enable line-length -->

### Admin Execution Environment

The administrative architecture focuses on a trust-based model combined with Ray
cluster configurations. Nexus will rely on organizational trust—only IBMers can
submit code, and all packages undergo standard CI/CD CVE scans. Ray runtime
environments dynamically handle isolated execution for dependencies, and the
underlying cluster will mount a shared Persistent Filesystem (PVC) to optimize
performance via data caching.

<!-- markdownlint-disable-next-line MD024 -->
#### Requirements Matching

<!-- markdownlint-disable line-length -->

| Requirement | Name                  | Proposed Solution                                                                                                                           |
| :---------- | :-------------------- | :------------------------------------------------------------------------------------------------------------------------------------------ |
| **REQ 6.1** | Admin Execution       | Admin execution is supported securely via trusted IBMer code submissions, CVE scans, and Ray cluster deployment.                            |
| **REQ 6.2** | Isolated Execution    | Ray dynamically manages and loads package dependencies into isolated worker node environments at execution time to prevent version clashes. |
| **REQ 6.3** | Persistent Filesystem | Admins will configure the Ray cluster to mount a shared persistent filesystem (PVC) between executions to allow workload dataset caching.   |

<!-- markdownlint-enable line-length -->

### Nexus-Level Orchestration & Review

Global orchestration across multiple packages will utilize `ado`'s native search
space semantics to define benchmarks independently of individual packages.
Governance over expensive parameter sweeps is handled manually by admins,
supplemented by automated CI checks. The mechanism for actually triggering these
centralized administrative evaluations is pending definition.

<!-- markdownlint-disable-next-line MD024 -->
#### Requirements Matching

<!-- markdownlint-disable line-length -->

| Requirement | Name                                 | Proposed Solution                                                                                                                 |
| :---------- | :----------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------- |
| **REQ 7.1** | Nexus-Level Benchmarks Definition    | Nexus-level benchmarks can be defined independently using `ado` configuration semantics (search spaces and wrapper extensions).   |
| **REQ 7.2** | Admin-Triggered Evaluation Execution | TBD                                                                                                                               |
| **REQ 7.3** | Sweep Review and Approval            | Admins retain manual/automated review oversight of sweep configurations (e.g., via PR approvals) prior to Ray cluster submission. |

<!-- markdownlint-enable line-length -->

---

## Requirements Summary

<!-- markdownlint-disable line-length -->

| Requirement | Requirement Area                           | Name                                 | Proposed Solution                                                                                                                                                           |
| :---------- | :----------------------------------------- | :----------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **REQ 1.1** | Standardized Benchmark Packaging Protocol  | Input/Output Specification           | `ado` enforces a standard programmatic input/output schema. Experiments natively accept the benchmark target alongside parameterizable kwargs.                              |
| **REQ 1.2** | Standardized Benchmark Packaging Protocol  | Python Package                       | `ado` and all wrappers are written purely in Python and distributed as standard packages with explicitly defined dependencies loaded by Ray.                                |
| **REQ 1.3** | Standardized Benchmark Packaging Protocol  | Versioning                           | `ado` allows arbitrary parameters (e.g., version strings) to be passed and tracked, satisfying varying versioning approaches.                                               |
| **REQ 1.4** | Standardized Benchmark Packaging Protocol  | Reproducible Execution               | `ado`'s provenance tracking guarantees that an experiment name plus specific parameter values defines a unique, repeatable execution.                                       |
| **REQ 1.5** | Standardized Benchmark Packaging Protocol  | Lifecycle Management                 | `ado` natively provides a flag for experiments to mark deprecation, visible to users to prevent technical debt.                                                             |
| **REQ 1.7** | Standardized Benchmark Packaging Protocol  | Required Data                        | Workload data is either bundled directly inside the Nexus Python package or the `ado` experiment is programmed to download it dynamically at execution time.                |
| **REQ 2.1** | Benchmark Registration and Discoverability | Benchmark Experiment Registration    | Registration is achieved by committing the benchmark experiment Python package to Nexus. Installing the package registers it with the local `ado` instance.                 |
| **REQ 2.2** | Benchmark Registration and Discoverability | Benchmark Experiment Discovery       | `ado` CLI & Python API provides built-in commands to list and discover all registered benchmark experiments, including deprecated ones.                                     |
| **REQ 2.3** | Benchmark Registration and Discoverability | Benchmark Registration               | A benchmark is formally registered by saving an `ado` configuration (YAML or Python) that binds a benchmark experiment (fixed or parameterizable) to a specific workload.   |
| **REQ 2.4** | Benchmark Registration and Discoverability | Benchmark Discovery                  | By querying the centralized `ado` database, users can discover defined benchmarks and trace which benchmark targets have executed them.                                     |
| **REQ 3.1** | Using the Benchmarking System              | Benchmark Specification              | Package owners use the `ado` CLI or API to specify the registered benchmark configuration they wish to execute against their target.                                        |
| **REQ 3.2** | Using the Benchmarking System              | Providing Benchmark Experiments      | Package owners provide custom benchmark experiment scripts as new `ado` extensions, packaged in compliance with Nexus standards.                                            |
| **REQ 3.3** | Using the Benchmarking System              | Benchmark Experiment Reuse           | Once an experiment is registered in the `ado` environment via a Nexus package, it can be universally referenced and reused across different projects.                       |
| **REQ 4.1** | Execution and Orchestration                | Single and Sweep Execution           | `ado` uses Ray's built-in samplers and optimizers out-of-the-box for both single benchmark instances and parameter sweeps.                                                  |
| **REQ 4.2** | Execution and Orchestration                | Resource Specification               | Ray allows explicit hardware resource requests (e.g., `@ray.remote(num_gpus=1)`) within the benchmark experiment code.                                                      |
| **REQ 4.3** | Execution and Orchestration                | Resource Limits                      | A configured Ray cluster allows admins to set hard quotas and resource limits per instance or set of instances.                                                             |
| **REQ 4.4** | Execution and Orchestration                | Result Capture                       | Ray isolates instances; `ado` independently commits successful benchmark results to the database even if parallel instances fail.                                           |
| **REQ 4.5** | Execution and Orchestration                | Standardized Error Reporting         | Handled natively via standard Python error handling and custom return payloads within the `ado` interface.                                                                  |
| **REQ 4.6** | Execution and Orchestration                | Logging                              | Admins will configure the Ray cluster infrastructure to capture and persist Ray logs (including tracebacks), making them accessible without requiring indefinite retention. |
| **REQ 4.7** | Execution and Orchestration                | Self-Contained Execution             | Ray spins up isolated, stateless worker processes, ensuring experiments cannot rely on unmanaged pre-existing data on the filesystem.                                       |
| **REQ 4.8** | Execution and Orchestration                | Local Execution                      | `ado` + Ray natively supports local, single-node execution for rapid prototyping by users with sufficient local compute.                                                    |
| **REQ 5.1** | Data Storage and Analysis                  | Centralized Results Storage          | `ado` Distributed Projects uses a remote database connection to store and centralize results for cross-model comparison and package owner inspection.                       |
| **REQ 5.2** | Data Storage and Analysis                  | Common Results Schema                | `ado`'s automatic data-tracking enforces a uniform, structured schema and metadata standard for all stored benchmark results.                                               |
| **REQ 5.3** | Data Storage and Analysis                  | Custom Metadata Support              | `ado` result interfaces support returning and storing custom metadata dicts alongside core quantitative execution results.                                                  |
| **REQ 6.1** | Admin Execution Environment                | Admin Execution                      | Admin execution is supported securely via trusted IBMer code submissions, CVE scans, and Ray cluster deployment.                                                            |
| **REQ 6.2** | Admin Execution Environment                | Isolated Execution                   | Ray dynamically manages and loads package dependencies into isolated worker node environments at execution time to prevent version clashes.                                 |
| **REQ 6.3** | Admin Execution Environment                | Persistent Filesystem                | Admins will configure the Ray cluster to mount a shared persistent filesystem (PVC) between executions to allow workload dataset caching.                                   |
| **REQ 7.1** | Nexus-Level Orchestration & Review         | Nexus-Level Benchmarks Definition    | Nexus-level benchmarks can be defined independently using `ado` configuration semantics (search spaces and wrapper extensions).                                             |
| **REQ 7.2** | Nexus-Level Orchestration & Review         | Admin-Triggered Evaluation Execution | TBD                                                                                                                                                                         |
| **REQ 7.3** | Nexus-Level Orchestration & Review         | Sweep Review and Approval            | Admins retain manual/automated review oversight of sweep configurations (e.g., via PR approvals) prior to Ray cluster submission.                                           |

<!-- markdownlint-enable line-length -->
