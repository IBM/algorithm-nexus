<!--
Copyright IBM Corporation 2026
SPDX-License-Identifier: Apache-2.0
-->

# Models Testing Requirements

This section defines the requirements for testing of models within Algorithm
Nexus. Model tests validate that models operate correctly, produce expected
outputs, and integrate properly with the platform. Contributors must provide
comprehensive test suites that cover model initialization, inference, and
integration scenarios.

## Test Infrastructure Requirements

The table below outlines the infrastructure and environment requirements for
testing models.

| Requirement                 | Description                                                                                                                                                                              |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Hardware Specifications** | Minimum and recommended hardware for running tests. Must specify: GPU requirements (type, memory, count), CPU requirements, RAM requirements, and whether CPU-only fallback is supported |
| **Test Dependencies**       | Python packages required for testing (e.g., pytest, unittest), version constraints, and any additional testing tools or frameworks                                                       |
| **Test Fixtures**           | Reusable test components, test configurations, and setup/teardown procedures                                                                                                             |

## Test Implementation Requirements

The table below specifies what must be included in the tests implementation.

| Requirement                  | Description                                                                                                                                                                                         |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Model loading tests**      | Tests validating the model can be properly loaded                                                                                                                                                   |
| **Inference tests**          | Tests at least one single inference (one input-one-output) and validates the value of the output is correct. Optionally other inference modes can be tested to (e.g., batch of inferences or ...) . |
| **vLLM Integration Testing** | Tests verifying model loading and inference with vLLM. This test is optional.                                                                                                                       |

Test implementations should follow pytest conventions and best practices, and
all tests must be reproducible and deterministic. Test data retrieval must be
part of the test itself. Also, tests should be designed to run in CI/CD
environments with limited resources (both compute and storage).

Notes:

- Implementation requirements do not have to be addressed one by one in
  dedicated tests, they can also be all fulfilled in a single test.
- The requirements for vLLM integration will be detailed in the future.

## Test Execution Requirements

The table below defines how tests should be executed and validated.

| Requirement       | Description                                                                                                                                                     |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Test Commands** | Specific commands to run tests (e.g., `pytest tests/models/model-id/`), commands for different test categories, and any required environment variables or flags |
| **Test Duration** | Expected execution time for full test suite, execution time for individual test categories, and timeout configurations                                          |

Notes:

- The duration of the test could be capped at the AlgorithmNexus level, with
  users requested to provide tests that run within a pre-defined amount of time.
