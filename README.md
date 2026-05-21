# Algorithm Nexus

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Algorithm Nexus packages a diverse set of AI algorithm stacks — models,
frameworks, and related tooling — within a unified Python environment. Each
algorithm stack is described by a **Nexus package**: a small metadata directory
that records the package's dependencies, models, and validation requirements.
The `nexus` CLI validates Nexus packages and supports contributors in keeping
their packages well-formed.

## Roadmap

### Version 0.1 (Alpha, End of April 2026)

- **Project requirements for dependencies resolution, Nexus package definition,
  testing and benchmarking**
- **Protocol and tools for cross package dependency resolution in place**,
  supporting with/without vLLM with latest and pinned scenarios
- **Benchmarking and testing protocols defined**
- **Nexus package and model owner responsibilities defined**
- **Rules for contributing a new Nexus Package defined**
- **Initial CI in place**, supporting Nexus package structure validation
  (without vLLM validation), dependency resolution and models inference testing
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

## Installation

Choose the section that matches your goal:

- [I want to install algorithm nexus packages in my environment](#installing-algorithm-nexus-packages-in-your-environment)
- [I want to contribute my Python library to Algorithm Nexus](#contributing-your-python-library-to-algorithm-nexus)
- [I want to develop Algorithm Nexus itself](#developing-algorithm-nexus)

### Installing algorithm nexus packages in your environment

Algorithm Nexus is **not published to PyPI**. All installs reference a tagged
[GitHub Release](https://github.com/IBM/algorithm-nexus/releases).

Each release ships three mutually-exclusive dependency variants. Pick the one
that matches your environment:

| Variant     | vLLM included    | Intended use                          |
| ----------- | ---------------- | ------------------------------------- |
| `ecosystem` | No               | Research and exploration environments |
| `candidate` | Yes (latest)     | Pre-production evaluation             |
| `product`   | Yes (stable pin) | Production deployments                |

#### Install a variant

Each release tag includes a pinned, hash-verified requirements file for every
variant. Install using `uv`:

```bash
uv pip install -r https://raw.githubusercontent.com/IBM/algorithm-nexus/refs/tags/{version}/requirements-{variant}.txt
```

Replace `{version}` with the release tag (e.g. `v0.1.0`) and `{variant}` with
`ecosystem`, `candidate`, or `product`.

### Contributing your python library to algorithm nexus

> **Note:** This project is currently in closed beta. Contributions are open to
> IBM contributors only.

Contributing a package means adding your Python library as an Algorithm Nexus
dependency, creating a Nexus package metadata directory under `packages/`, and
opening a pull request from a fork of the nexus repository.

Before you begin you will need:

- Your algorithm package publicly available on GitHub
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) installed
- A
  [fork](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo)
  of this repository checked out locally

Set up your local environment:

```bash
cd algorithm-nexus
uv sync --group dev --extra cli
uv run pre-commit install
```

Then create a branch and follow one of the two paths below.

#### Option A — Coding Agent (Recommended)

An agent skill is available for adding Nexus packages. Open the algorithm nexus
repository in your coding agent and ask it to add your python package to the
nexus giving it your package repository URL e.g.

```commandline
Add the package at ${URL} to the nexus
```

replacing `${URL}` with your packages repo URL.

#### Option B — Manual

Follow the step-by-step guide in
[`docs/contributing/add_new_nexus_package.md`](docs/contributing/add_new_nexus_package.md),
which covers variant classification, `nexus.yaml` authoring, dependency
resolution with `uv add`, and opening a PR.

#### Before opening a pull request

Read [CONTRIBUTING.md](CONTRIBUTING.md) for DCO sign-off requirements, commit
message conventions (Conventional Commits / Angular style), and coding style
checks. All checks must pass before a PR can be merged.

### Developing Algorithm Nexus

For IBM contributors working on the CLI, validation logic, tests, or CI
infrastructure. This setup is a superset of the package contributor setup — it
adds the `test` dependency group.

```bash
git clone https://github.com/IBM/algorithm-nexus.git
cd algorithm-nexus
uv sync --extra cli --group dev --group test
uv run pre-commit install --install-hooks
uv run pre-commit install --hook-type commit-msg
```

Full details on coding standards, legal requirements (DCO), commit conventions,
and manual lint commands are in [CONTRIBUTING.md](CONTRIBUTING.md).

## CLI Reference

Algorithm Nexus provides the `nexus` CLI for working with Nexus packages.

### Validating nexus packages

To validate the structure and configuration of a Nexus package run:

```bash
nexus validate /path/to/package
```

This will examine the following:

- **Package structure**: Verifies required files (`nexus.yaml`, `model.yaml`)
  and directories exist
- **YAML syntax**: Ensures all configuration files are valid YAML
- **Schema validation**: Validates configuration against Pydantic models for
  correct field types and required fields
- **Cross-validation**: Checks dependencies between configurations
- **Model declarations**: Ensures all models have corresponding directories
- **Duplicate detection**: Checks for duplicate HuggingFace model IDs

In case of validation errors, a detailed report guides you to fix each issue.

### Discovering packages and benchmarks

Algorithm Nexus provides commands to discover and list packages, benchmark
packages, and experiments across your repository.

#### List all Nexus packages

```bash
nexus list packages [PACKAGES_ROOT]
```

Lists all valid Nexus packages found in the packages directory (default:
`./packages`). Supports JSON and CSV output formats with `-o json` or `-o csv`.
Use `--strict` to show warnings for packages that fail to load.

**Example:**

```bash
nexus list packages ./packages --strict
```

#### List benchmark packages

```bash
nexus list benchmark-packages [PACKAGES_ROOT]
```

Lists all benchmark packages registered across Nexus packages. Shows which Nexus
packages use each benchmark package. Filter by a specific Nexus package with
`--nexus-package`.

**Example:**

```bash
nexus list benchmark-packages ./packages --nexus-package terratorch
```

#### List benchmark experiments

```bash
nexus list benchmark-experiments [PACKAGES_ROOT]
```

Lists all benchmark experiments with their associated benchmark packages and
Nexus packages. Filter by a specific Nexus package with `--nexus-package`.

**Example:**

```bash
nexus list benchmark-experiments ./packages -o json
```

#### Get benchmark requirements

```bash
nexus get benchmark-requirements NEXUS_PACKAGE [PACKAGES_ROOT]
```

Retrieves the benchmark requirement specifiers for a specific Nexus package.
Output in requirements.txt format with `-o txt` for use with pip.

**Example:**

```bash
nexus get benchmark-requirements terratorch ./packages -o txt --output-file requirements.txt
```

### Output formats

Most list commands support multiple output formats:

- **Table** (default): Human-readable table output
- **JSON** (`-o json`): Machine-readable JSON format
- **CSV** (`-o csv`): Comma-separated values for spreadsheets
- **TXT** (`-o txt`): Requirements file format (get commands only)

Use `--output-file` to write output to a file instead of stdout.

## Contributing

This project is currently in closed beta. We are not accepting external
contributions at this time.

For IBM contributors:

- See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.
- See
  [`docs/contributing/add_new_nexus_package.md`](docs/contributing/add_new_nexus_package.md)
  for step-by-step instructions for contributing a Nexus package.

## License

This project is licensed under the Apache License 2.0 — see the
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
