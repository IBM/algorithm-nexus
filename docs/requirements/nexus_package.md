<!--
Copyright IBM Corporation 2026
SPDX-License-Identifier: Apache-2.0
-->

# Requirements for a Nexus package

A Nexus package encapsulates a Python package and its associated models,
providing standardized metadata for validation, testing, and integration.
Contributors must provide both package-level information and model-specific
details to ensure proper cataloging and operational readiness within the
Algorithm Nexus ecosystem.

## Nexus Package Requirements

| Requirement        | Description                                                                              |
| ------------------ | ---------------------------------------------------------------------------------------- |
| **Identifier**     | Unique Nexus package identifier (lowercase, hyphenated format, e.g., "transformers-llm") |
| **Metadata**       | Package name, description and link to documentation                                      |
| **Python package** | Name or URL of the python package                                                        |
| **Version**        | Version of the python package                                                            |
| **Models**         | List of the models supported by this package                                             |

## Model Requirements

The table below summarises the requirements for each model in the Nexus Package

| Requirement       | Description                                                                                                                              |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **Identifier**    | Unique model identifier (lowercase, hyphenated format, e.g., "terramind-flood"). No two models can have the same name in Algorithm Nexus |
| **Metadata**      | Model name, version, description, and link to documentation                                                                              |
| **Model weights** | Name of the Hugging Face repository hosting the model weights, and version of the weights                                                |
| **Testing**       | Artifacts for testing the model (see the [testing requirements](./models_testing.md))                                                    |
| **Benchmarking**  | Artifacts for benchmarking the model (e.g., script, and specific benchmarking requirements)                                              |
| **Model Owner**   | GitHub ID of the model owner                                                                                                             |

Notes:

- The benchmarking and testing might endup being unified depending on the
  outcomes of #8 and #18

### Optional requirements

The table below summarizes optional requirements for integrating models with
agent frameworks and production systems.

| Requirement           | Description                                                                                                                                                                                                                                                                                                                         |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Model usage**       | Documentation on how to use the model. This includes a combination of text and code snippets to help model users in getting started with a specific model. Differently to the documentation info in the metadata, this should be committed as part of the Nexus package for further use in project documentation and agentic skills |
| **Agent Integration** | Information on integration with agent frameworks (LangChain, AutoGPT, MCP servers, custom agents). This includes a combination of text and code snippets demonstrating integration with agent frameworks.                                                                                                                           |
| **Observability**     | Information on integration with observability frameworks/standards (e.g., OpenTelemetry). This includes a combination of text and code snippets demonstrating integration with observability frameworks.                                                                                                                            |
| **vLLM integration**  | Information related to serving the model with vLLM, including any vLLM specific plugins required to be installed in the python environment used for serving.                                                                                                                                                                        |

Notes:

- The requirements for vLLM integration will be detailed in the future.
