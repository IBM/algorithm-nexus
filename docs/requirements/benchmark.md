# Requirements for Benchmarking

The primary objective of this document is to establish the core requirements for
a flexible, robust, and user-friendly benchmarking system for the Algorithm
Nexus project. This system evaluates registered targets (models, algorithms, or
experiments), supports internal and external benchmarks, and allows users to
easily discover available testing options.

To ensure clarity, these requirements are divided into two categories: Generic
System Requirements (applying to the framework, interfaces, and general
execution) and Administrator Environment & Process Requirements (applying
specifically to the central execution infrastructure managed by the project
admins).

## Terminology

- **Logical Benchmark (Benchmark Problem)** An abstract, reusable definition of
  a problem class or evaluation task, independent of any specific dataset,
  model, or execution context. It defines _what_ is being measured (e.g.,
  Travelling Salesman Problem, Graph Colouring, Bin Packing, Maximum Cut)
  without prescribing _how_ it is instantiated or executed.

- **Benchmark Instance** The concrete realisation of a Logical Benchmark: the
  problem or task an AI model or algorithm is intended to solve, including the
  associated inputs, data, and execution pattern exercised by the benchmark
  driver.

- **Benchmark Target** The model, algorithm, or experiment being evaluated. For
  a given benchmark instance, this is the primary element that is varied.

- **Benchmark Experiment** A script, harness, or workflow that executes the
  benchmark target on the benchmark instance, controlling execution conditions,
  and collects measurements. The experiment might take the benchmark target and
  instance as input (**parameterizable**) or may hard-code one or both of them
  (**fixed**). A typical example is the experiment is an implementation of a
  single algorithm (benchmark target). Often an experiment can address one or
  more logical benchmarks.

- **Benchmark Result** The quantitative measurements produced by executing a
  benchmark submission (e.g., accuracy, runtime, throughput, resource
  utilization). Results are used to compare benchmark targets on a given
  benchmark instance.

- **Benchmark Submission** One registered use of a benchmark experiment on a
  benchmark instance for a specific benchmark target. A submission can be
  executed to produce benchmark results. It is not the experiment definition.

The relationship between core components can be summarized as:

```text
Benchmark Submission = Benchmark Experiment + Benchmark Target + Benchmark Instance.
```

where the Benchmark Experiment may imply the Benchmark Target.

---

## Part I: Generic Benchmarking System Requirements

### REQ-1: Standardized Benchmark Packaging Protocol

This section sets requirements for how benchmark experiments are constructed,
formatted, standardized, and versioned to ensure reproducibility.

- **REQ 1.1: Input/Output Specification** A benchmark experiment must define its
  inputs and outputs using a standardized system schema. Experiments must accept
  the benchmark target (model, algorithm, or experiment) as a primary
  programmatic input, and may support additional optional parameters.
  _Rationale_: Ensures the system can uniformly interact with diverse benchmark
  implementations.

- **REQ 1.2: Python Package** All benchmark experiments, including wrappers for
  external frameworks, must be implemented in Python and distributed as standard
  Python packages. Each package must define all its runtime dependencies.
  _Rationale_: Provides a predictable, unified installation mechanism for
  automated pipelines.

- **REQ 1.3: Versioning** Benchmark experiments are responsible for their own
  versioning. The system’s specification method must be flexible enough to
  satisfy differing versioning approaches across packages.

- **REQ 1.4: Reproducible Execution** Benchmark experiments must ensure that the
  combination of their name, version and the specific names and values of all
  their parameters defines a unique, repeatable execution.

- **REQ 1.5: Lifecycle Management** It must be possible to mark a benchmark
  experiment as deprecated. _Rationale_: Prevents technical debt and signals to
  users which benchmark experiments are no longer actively maintained or
  relevant.

- **REQ 1.7: Required Data** If a benchmark experiment requires specific data
  files to execute a benchmark instance these must be either (a) contained in
  the python package providing the experiment; (b) downloaded by the experiment.
  _Rationale_: Guarantees that automated execution does not fail due to missing
  local filesystem dependencies.

---

### REQ-2: Registration and Discoverability

This section outlines requirements for managing and discovering logical
benchmarks, instances, experiments, and submissions.

- **REQ 2.1: Logical Benchmark Registration** The system must provide a method
  for users to define and register a logical benchmark (a problem class).

- **REQ 2.2: Benchmark Instance Registration** The system must provide a method
  for users to define and register a concrete benchmark instance of a registered
  logical benchmark.

- **REQ 2.3: Benchmark Experiment Registration** The system must provide a
  method for users to upload and register a benchmark experiment definition,
  implemented according to the Standardized Benchmark Packaging Protocol, and to
  declare that the experiment can address one or more registered logical
  benchmarks.

- **REQ 2.4: Benchmark Submission Registration** The system must provide a
  method for users to define and register a benchmark submission that applies a
  registered benchmark experiment to a benchmark instance and a benchmark
  target. One experiment may have many submissions, across instances and
  targets.

- **REQ 2.5: Discoverability** The system must provide a method for users to
  list all registered artifacts: logical benchmarks, benchmark instances,
  benchmark experiments (including deprecated experiments and which logical
  benchmarks each can address), benchmark submissions, and associated targets.
  _Rationale_: Encourages reuse, prevents duplicated effort, and allows users to
  compare targets against established historical baselines.

---

### REQ-3: Using the Benchmarking System

This section details requirements for users to use the benchmarking system.

- **REQ 3.1: Benchmark Submission Specification** To use the system to evaluate
  a benchmark target, the user must specify a benchmark submission in the manner
  defined by the system, see REQ 2.4.

- **REQ 3.2: Providing Benchmark Experiments** If a target requires a benchmark
  experiment not in the registry, the contributor must provide one, in
  compliance with the Standardized Packaging Protocol (REQ-1) and register it as
  described in REQ 2.3. _Rationale_: Empowers contributors to expand the
  system's capabilities.

- **REQ 3.3: Artifact Reuse** The system must allow referencing and utilizing an
  existing benchmark experiment, logical benchmark, or benchmark instance across
  Nexus packages.

---

### REQ-4: Execution and Orchestration

This section covers operational requirements for execution, resource handling,
and failure management.

- **REQ 4.1: Single and Sweep Execution** The system must support both executing
  single benchmark submissions and parameter sweeps. _Rationale_: Sweeps are
  essential for performance profiling and evaluating models across a spectrum of
  benchmark instances.

- **REQ 4.2: Resource Specification** The system must allow benchmark
  experiments to define the compute resources they require. _Rationale_: Ensures
  the system schedules tasks on capable hardware, preventing Out-Of-Memory (OOM)
  errors and execution bottlenecks.

- **REQ 4.3: Resource Limits** The system must support setting hard limits on
  maximum resource usage (time, compute, memory) per benchmark submission or set
  of submissions. _Rationale_: Prevents processes from hogging shared
  infrastructure in the admin environment.

- **REQ 4.4: Result Capture** The system must ensure results from any successful
  benchmark submission are saved.

- **REQ 4.5: Standardized Error Reporting** The system must provide a
  standardized mechanism for reporting known, handled execution errors.

- **REQ 4.6: Logging** The system must capture unexpected execution failures,
  including the underlying Python exception and traceback. Execution logs must
  be captured and made accessible to the user executing the benchmark
  submission. The system is not required to retain these logs indefinitely.

- **REQ 4.7: Self-Contained Execution** Benchmark experiments must be
  self-contained and must not rely on pre-existing filesystem data. _Rationale_:
  Ensures seamless portability between local developer machines and remote
  orchestration environments.

- **REQ 4.8: Local Execution** The system must enable benchmark experiments to
  be executed locally by a user with sufficient compute resources. _Rationale_:
  Allows developers to rapidly prototype, test, and debug benchmark experiments
  and to confirm results of automated benchmarking runs.

---

### REQ-5: Data Storage and Analysis

This section outlines how results and supporting context are persisted.

- **REQ 5.1: Centralized Results Storage** Results of all benchmark submissions
  must be stored in a centralized location accessible by the users who submitted
  them. _Rationale_: Facilitates cross-model comparison, historical tracking,
  and platform-wide reporting.

- **REQ 5.2: Common Results Schema** The system must enforce a common schema and
  metadata standards for all stored benchmark results. _Rationale_: Enables
  automated data analysis, programmatic querying, and integration with
  visualization dashboards.

- **REQ 5.3: Custom Metadata Support** The system must allow benchmark
  experiments to store custom metadata alongside execution results. _Rationale_:
  Ensures nuanced, model/algorithm-specific context is not lost during
  standardized data capture.

---

## Part II: Administrator Environment & Process Requirements

### REQ-6: Admin Execution Environment

This section defines the infrastructure requirements for the centralized
benchmarking environment managed by project administrators.

- **REQ 6.1: Admin Execution** The system must be capable of executing benchmark
  submissions on administrator infrastructure.

- **REQ 6.2: Isolated Execution** The system must support isolated execution of
  benchmark experiments for dependency management. _Rationale_: Prevents
  dependency cross-contamination and version clashes (especially critical for
  low-level libraries like CUDA and vLLM) between different concurrently running
  models.

- **REQ 6.3: Persistent Filesystem** The admin environment must provide a
  persistent filesystem between executions. _Rationale_: Optimizes performance
  by allowing large datasets to be cached and reused across multiple benchmark
  runs.

---

### REQ-7: Nexus-Level Orchestration & Review

This section defines requirements for cross-package evaluations and
administrative oversight.

- **REQ 7.1: Nexus-Level Logical Benchmarks and Instances** The system must
  support defining logical benchmarks and benchmark instances independently of
  individual Nexus packages.

- **REQ 7.2: Admin-Triggered Evaluation Execution** The system must provide a
  dedicated mechanism for administrators to trigger and execute benchmark
  submissions.

- **REQ 7.3: Sweep Review and Approval** The administrative process must include
  a manual or automated review step for submitted sweep configurations prior to
  execution. _Rationale_: Acts as a safeguard against accidental misuse of
  expensive compute resources due to misconfigured parameter sweeps.
