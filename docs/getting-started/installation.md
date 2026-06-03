# Installation

Algorithm Nexus provides the `nexus` CLI tool for managing Nexus packages. This
tool allows the validation of the structure of a Nexus Package.

## Install from a Release

You can install Algorithm Nexus directly from a published release, depending on
how you plan to use it.

### Install the CLI

```bash
uv pip install algorithm-nexus[cli]
```

### Install a Dependency Variant

Install a dependency variant such as `product`, with dependencies resolved at
runtime:

```bash
uv pip install algorithm-nexus[product]
```

### Install a Pre-resolved Dependency Set

Install a pre-resolved dependency set for a specific release and variant:

```bash
uv pip install -r https://raw.githubusercontent.com/IBM/algorithm-nexus/refs/tags/{version}/requirements-{variant}.txt
```

Replace `{version}` with the release tag and `{variant}` with the dependency
group you want to install, such as `product`, `candidate`, or `ecosystems`.

## Install from Source for Development

To develop locally with the CLI, test dependencies, and development tooling,
clone the repository and install with uv:

```bash
git clone https://github.com/IBM/algorithm-nexus.git
cd algorithm-nexus
uv sync --extra cli --group dev --group test
```

## Verify Installation

After installation, verify that the `nexus` CLI is available:

```bash
nexus --help
```

## Next Steps

- Learn about [Nexus Package Structure](../design/nexus_package.md)
- Read the [Contributing Guide](../contributing/index.md) to start contributing
- Explore the [Getting Started Guide](index.md) for more information
