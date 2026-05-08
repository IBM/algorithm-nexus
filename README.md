# Algorithm Nexus

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

> **Note:** This project is in the very early stages of planning and
> development. There is currently no functional code.

This library aims to robustly package a diverse set of AI models and frameworks
within a unified Python environment, enabling seamless deployment and management
of multiple models with different dependencies.

## Roadmap

### Version 0.1 (Alpha, End of April 26)

- **Project requirements for dependencies resolution, Nexus package definition,
  testing and benchmarking**
- **Protocol and tools for cross package dependency resolution in place**,
  supporting with/without vLLM with latest and pinned scenarios
- **Benchmarking and testing protocols defined**
- **Nexus package and model owner responsibilities defined**
- **Rules for contributing a new Nexus Package defined**
- **Initial CI in place**, supporting Nexus package structure validation
  (without vLLM validation), dependency resolution and models inference testing.
- **Nexus package for TerraTorch integrated**

### Version 0.2 (Beta, End of May 2026)

- **Requirements for models integration with vLLM defined**
- **CI workflows extended** with validation of vLLM integration requirements and
  benchmarking tasks
- **Agentic skills implemented** for generation of a Nexus package and PR
- **Agentic functionalities implemented** for supporting the implementation of
  the vLLM plugins required for a model
- **Integration of
  [Tokamind](https://github.com/UKAEA-IBM-STFC-Fusion-FMs/tokamind) Fusion
  models**

### Version 0.3 (First Release, End of June 2026)

- **Agentic functionalities extended** to supporting the deployment of the
  integrated models
- **Integration of additional algorithm packages from beta-test phase**
- **Models scoreboard implemented** to track the performance of the integrated
  models

## Algorithm Nexus CLI

Algorithm Nexus provides the `nexus` CLI tool for managing Nexus packages. This
tool allows the validation of the structure of a Nexus Package.

### Installation

#### Install from a release

You can install Algorithm Nexus directly from a published release, depending on
how you plan to use it.

Install the CLI:

```bash
uv pip install algorithm-nexus[cli]
```

Install a dependency variant such as `product`, with dependencies resolved at
runtime:

`uv pip install algorithm-nexus[product]`

Install a pre-resolved dependency set for a specific release and variant:

```bash
uv pip install -r https://raw.githubusercontent.com/IBM/algorithm-nexus/refs/tags/{version}/requirements-{variant}.txt
```

Replace `{version}` with the release tag and `{variant}` with the dependency
group you want to install, such as `product`, `candidate`, or `ecosystems`.

#### Install from source for development

To develop locally with the CLI, test dependencies, and development tooling,
clone the repository and install with uv:

```bash
git clone https://github.com/IBM/algorithm-nexus.git
cd algorithm-nexus
uv sync --extra cli --group dev --group test
```

### Available Tools

#### Nexus Package Validation

The validation tool checks:

- **Package structure**: Verifies required files (`nexus.yaml`, `model.yaml`)
  and directories (`tests/`) exist
- **YAML syntax**: Ensures all configuration files are valid YAML
- **Schema validation**: Validates configuration against Pydantic models for
  correct field types and required fields
- **Cross-validation**: Checks dependencies between configurations (e.g., vLLM
  enabled requires vLLM testing)
- **Model declarations**: Ensures all models in `nexus.yaml` have corresponding
  directories

Example usage:

```bash
nexus validate /path/to/package
```

In case of validation errors a detailed report guides the user to fix the
issues.

## Getting Started

## Contributing

This project is currently in closed beta. We are not accepting external
contributions at this time.

For IBM contributors:

- Please, see our [Contributing Guide](CONTRIBUTING.md) for development setup
  and guidelines.
- Read the [guide](./docs/contributing/add_new_nexus_package.md) for
  step-by-step instructions for contributing a Nexus Package.

## License

This project is licensed under the Apache License 2.0 - see the
[LICENSE](LICENSE) file for details.

## Maintainers

See [MAINTAINERS.md](MAINTAINERS.md) for the list of project maintainers.

## Support

- **Issues**: [GitHub Issues](https://github.com/IBM/algorithm-nexus/issues)
- **Discussions**:
  [GitHub Discussions](https://github.com/IBM/algorithm-nexus/discussions)

## Acknowledgments

This project is part of IBM's commitment to open-source AI infrastructure and
collaboration with Red Hat.
