# Introduction

The primary objective of this document is to establish the core requirements for
a flexible, robust, and user-friendly benchmarking system for the Algorithm
Nexus project. This system evaluates registered models, supports internal and
external benchmarks, and allows users to easily discover available testing
options.

To ensure clarity, these requirements are divided into two categories: Generic
System Requirements (applying to the framework, interfaces, and general
execution) and Administrator Environment & Process Requirements (applying
specifically to the central execution infrastructure managed by the project
admins).

## Terminology

To establish a clear mental model, the relationship between core components can
be summarized as: Benchmark Instance = Benchmark Target + Benchmark (Workload +
Benchmark Experiment)

- **Workload**
  The problem or task an AI model or algorithm is intended to solve, including
  the associated inputs, data, and execution pattern exercised by the benchmark
  driver.

- **Benchmark Target**
  The AI model or algorithm being evaluated. This is the element that varies
  across benchmark experiments while the benchmark definition and workload
  specification are held constant.

- **Benchmark Experiment**
  A script, harness, or workflow that executes the benchmark target on the
  workload, controlling execution conditions, and collects measurements. The
  experiment will take benchmark target as input. The benchmark experiment may
  hard-code the workload (**fixed**) OR the workload is specified by passing
  certain values for the benchmark experiments parameters (**parameterizable**)

- **Benchmark**
  A standardized, repeatable evaluation used to compare the behavior of a
  benchmark target (versions AI models or algorithms) on a problem of interest
  (workload) under controlled conditions. Emodied as either a **fixed benchmark
  experiment** or a **workload** plus **parameterized benchmark experiment**.

- **Benchmark Result**
  The quantitative measurements produced by executing a benchmark experiment
  (e.g., accuracy, runtime, throughput, resource utilization), with the
  **workload** - used to compare benchmark targets.

- **Benchmark Instance**
  A concrete execution of a benchmark, in which a benchmark driver runs a
  workload against a specific benchmark target and records measurements.

---

## Part I: Generic Benchmarking System Requirements

### REQ-1: Standardized Benchmark Packaging Protocol

This section sets requirements for how benchmark experiments are constructed,
formatted, standardized, and versioned to ensure reproducibility.

- **REQ 1.1: Input/Output Specification** A benchmark experiment must define its
  inputs and outputs using a standardized system schema. Experiments must accept
  the benchmark target (model or algorithm) as a primary programmatic input, and
  may support additional optional parameters. _Rationale_: Ensures the system
  can uniformly interact with diverse benchmark implementations.

- **REQ 1.2: Python Package**
   All benchmark experiments, including wrappers for external frameworks, must
  be implemented in Python and distributed as standard Python packages. Each
  package must define all its runtime dependencies _Rationale_: Provides a
  predictable, unified installation mechanism for automated pipelines.

- **REQ 1.3: Versioning**
  Benchmark experiments are responsible for their own versioning. The system’s
  specification method must be flexible enough to satisfy differing versioning
  approaches across packages.

- **REQ 1.4: Reproducible Execution**
  Benchmark experiments must ensure that the combination of their name and the
  specific names and values of all their parameters defines a unique, repeatable
  execution.

- **REQ 1.5: Lifecycle Management**
  It must be possible to mark a benchmark experiment as deprecated. _Rationale_:
  Prevents technical debt and signals to users which benchmarks are no longer
  actively maintained or relevant.

- **REQ 1.7: Required Data**
   If a benchmark experiment requires specific data files to execute a workload
  these must be either (a) contained in the python package providing the
  experiment; (b) downloaded by the experiment _Rationale_: Guarantees that
  automated execution does not fail due to missing local filesystem
  dependencies.

---

### REQ-2: Benchmark Registration and Discoverability

This section outlines requirements for managing and discovering available
benchmarks and benchmark experiments.

- **REQ 2.1: Benchmark Experiment Registration**
  The system must provide a method for users to add benchmark experiments,
  implemented according to the Standardized Benchmark Packaging Protocol

- **REQ 2.2: Benchmark Experiment Discovery**
  The system must provide a method for users to list the registered benchmark
  experiments (including deprecated experiments) _Rationale_: Encourages reuse
  and prevents duplicated effort across different research teams.

- **REQ 2.3: Benchmark Registration**
  The system must provide a method to define and register a **benchmark**:
- either as
  1. a combination a parameterizable benchmark experiment and a benchmark
     workload
  2. a fixed benchmark experiment

- **REQ 2.4: Benchmark Discovery**
  The system must provide a method for user to list the registered benchmarks
  and the models/algorithms using them. _Rationale_: Allows package owners to
  easily compare their models against established historical baselines.

---

### REQ-3: Using the Benchmarking System

This section details requirement for package owners to use the benchmarking
system

- **REQ 3.1: Benchmark Specification**
  To use the system to benchmark a model/algorithm, the nexus package owner must
  specify the benchmark to use, in the manner defined by the system c.f. REQ
  2-1.

- **REQ 3.2: Providing Benchmark Experiments**
  If a model/algorithm requires a benchmark experiment not in the registry, the
  contributor must provide one, in compliance with the Standardized Packaging
  Protocol c.f. REQ-1.
  _Rationale_: Empowers contributors to expand the system's capabilities

- **REQ 3.3: Benchmark Experiment Reuse**
  The system must allow referencing and utilizing an existing benchmark
  experiment or benchmark definition across different projects.

---

### REQ-4: Execution and Orchestration

This section covers operational requirements for execution, resource handling,
and failure management.

- **REQ 4.1: Single and Sweep Execution**
   The system must support both executing single benchmark instances and
  parameter sweeps. _Rationale_: Sweeps are essential for hyperparameter tuning,
  performance profiling, and evaluating models across a spectrum of workloads.

- **REQ 4.2: Resource Specification**
   The system must allow benchmark experiments to define the compute resources
  they require, _Rationale_: Ensures the system schedules tasks on capable
  hardware, preventing Out-Of-Memory (OOM) errors and execution bottlenecks

- **REQ 4.3: Resource Limits**
   The system must support setting hard limits on maximum resource usage (time,
  compute, memory) per benchmark instance or set of instances. _Rationale_:
  Prevents processes from hogging shared infrastructure in the admin
  environment.

- **REQ 4.4: Result Capture**
  The system must ensure results from any successful benchmark instance are
  saved.

- **REQ 4.5: Standardized Error Reporting**
  The system must provide a standardized mechanism for reporting known, handled
  execution errors.

- **REQ 4.6: Logging**
  The system must capture unexpected execution failures, including the
  underlying Python exception and traceback. Eecution logs must be captured and
  made accessible the user executing the benchmark. The system is not required
  to retain these logs indefinitely.

- **REQ 4.7: Self-Contained Execution**
  Benchmark experiments must be self-contained and must not rely on pre-existing
  filesystem data. _Rationale_: Ensures seamless portability between local
  developer machines and remote orchestration environments.

- **REQ 4.8: Local Execution**
  The system must enable benchmark experiments to be executed locally by a user
  with sufficient compute resources. _Rationale_: Allows developers to rapidly
  prototype, test, and debug benchmarks and to confirm results of automated
  benchmarkming runs.

---

### REQ-5: Data Storage and Analysis

This section outlines how results and supporting context are persisted.

- **REQ 5.1: Centralized Results Storage**
  Results of all benchmark instances must be stored in a centralized location
  accessible by the respective package owners. _Rationale_: Facilitates
  cross-model comparison, historical tracking, and platform-wide reporting.

- **REQ 5.2: Common Results Schema**
  The system must enforce a common schema and metadata standards for all stored
  benchmark results. _Rationale_: Enables automated data analysis, programmatic
  querying, and integration with visualization dashboards.

- **REQ 5.3: Custom Metadata Support**
  The system must allow benchmark experiments to store custom metadata alongside
  execution results. _Rationale_: Ensures nuanced, model/algorithm-specific
  context is not lost during standardized data capture.

---

## Part II: Administrator Environment & Process Requirements

### REQ-6: Admin Execution Environment

This section defines the infrastructure requirements for the centralized
benchmarking environment managed by project administrators.

- **REQ 6.1: Admin Execution**
  The system must be capable of executing benchmarks on administrator
  infrastructure.

- **REQ 6.2: Isolated Execution**
  The system must support isolated execution of benchmark experiments for
  dependency management. _Rationale_: Prevents dependency cross-contamination
  and version clashes (especially critical for low-level libraries like CUDA and
  vLLM) between different concurrently running models.

- **REQ 6.3: Persistent Filesystem**
  The admin environment must provide a persistent filesystem between executions.
  _Rationale_: Optimizes performance by allowing large datasets to be cached and
  reused across multiple benchmark runs.

---

### REQ-7: Nexus-Level Orchestration & Review

This section defines requirements for cross-package evaluations and
administrative oversight.

- **REQ 7.1: Nexus-Level Benchmarks Definition**
  The system must support defining benchmarks independently of individual
  packages.

- **REQ 7.2: Admin-Triggered Evaluation Execution**
  The system must provide a dedicated mechanism for administrators to trigger
  and execute benchmarks.

- **REQ 7.3: Sweep Review and Approval**
  The administrative process must include a manual or automated review step for
  submitted sweep configurations prior to execution. _Rationale_: Acts as a
  safeguard against accidental misuse of expensive compute resources due to
  misconfigured parameter sweeps.
