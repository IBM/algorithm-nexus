# Algorithm Nexus

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Algorithm Nexus is a comprehensive framework for delivering and managing
multiple AI models within a unified Python environment. It enables seamless
integration of models built with different libraries and frameworks, providing
robust dependency management, testing, and benchmarking capabilities to ensure
reliable model deployment and operation.

## Features

- **Multi-Model Support**: Deploy and manage multiple AI models using different
  libraries (PyTorch, TensorFlow, scikit-learn, etc.) within the same Python
  environment
- **Dependency Management**: Intelligent dependency resolution and conflict
  detection across different model requirements
- **Testing Framework**: Comprehensive testing infrastructure for model
  validation and integration testing
- **Benchmarking**: Performance benchmarking tools to compare and optimize model
  performance

## Quick Start

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) for dependency management

### Installation

```bash
# Clone the repository
git clone https://github.com/IBM/algorithm-nexus.git
cd algorithm-nexus

# Install dependencies using uv
uv sync
```

### Development Setup

```bash
# Install development dependencies (includes pre-commit and linting tools)
uv sync --group dev

# Install pre-commit hooks (recommended)
pre-commit install --install-hooks
pre-commit install --hook-type commit-msg
```

For detailed development setup instructions, see our
[Contributing Guide](CONTRIBUTING.md).

## Documentation

For more information, see our [Contributing Guide](CONTRIBUTING.md).

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md)
for details on:

- Code of conduct
- Development setup
- Coding standards

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
