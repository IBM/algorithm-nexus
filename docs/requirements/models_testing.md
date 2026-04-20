<!--
Copyright IBM Corporation 2026
SPDX-License-Identifier: Apache-2.0
-->

# Requirements for Model Testing

**Status:** Proposed

## 1. Introduction

This document outlines the requirements for testing models within Algorithm
Nexus. Model tests validate that models operate correctly, produce expected
outputs, and integrate properly with the platform. Contributors must provide a
test that covers inference on the model in a way that is reproducible and
suitable for CI/CD.

---

## 2. Core Requirements

### REQ-1: Test Infrastructure

The testing setup **must** define the infrastructure and environment required to
run model tests consistently.

- **REQ-1.1 (Hardware Specifications):** Testing requirements **must** specify
  the minimum and recommended hardware needed to run the tests, including GPU
  requirements (type, memory, and count), CPU requirements, RAM requirements,
  and whether CPU-only fallback is supported.

### REQ-2: Test Coverage Requirements

Model tests **must** validate the required loading and inference behaviour for a
model.

- **REQ-2.1 (Inference Tests):** Tests **must** execute at least one inference
  scenario using a single input and validate that the produced output is
  correct. Additional inference modes, such as batched inference, may also be
  tested.

- **REQ-2.2 (vLLM Integration Testing):** Tests **must** verify model loading
  and inference with `vllm`. **This requirement is optional**.

### REQ-3: Test Implementation Conventions

Model test implementations **must** follow conventions that make them reliable,
reproducible, and suitable for automated execution.

- **REQ-3.1 (Test Fixtures):** Users **must** define reusable test components,
  test configurations, and any setup or teardown procedures. Test fixtures must
  be delivered in the form of a python module.

- **REQ-3.2 (Test Data Retrieval):** Data for the test is distributed with the
  test.

### REQ-4: Test Execution

The testing specification **must** define how tests are executed and what
runtime expectations apply.

- **REQ-4.1 (Test Commands):** The testing specification **must** provide the
  commands used to run tests.

## 3. Notes

- Test Coverage requirements (REQ-2) do not need to be addressed one by one in
  dedicated tests; they may also be fulfilled within a single test.
- Requirements for `vllm` integration will be detailed in the future.
- Test duration may eventually be capped at the Algorithm Nexus level, with
  contributors expected to provide tests that run within a predefined time
  limit.
- It is desirable that tests can be executeted in a CI/CD environment with
  potentially limited resources (compute and storage).
