# Algorithm Nexus

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

> **Note:** This project is in the very early stages of planning and
> development. There is currently no functional code.

This library aims to robustly package a diverse set of AI models and frameworks
within a unified Python environment, enabling seamless deployment and management
of multiple models with different dependencies.

## Roadmap

### Version 0.1 (Enf od April 26, Alpha)

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

## Contributing

This project is currently in closed beta. We are not accepting external
contributions at this time. For IBM contributors, please see our
[Contributing Guide](CONTRIBUTING.md) for development setup and guidelines.

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
