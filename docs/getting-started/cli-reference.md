# CLI Reference

The `nexus` command-line interface provides tools for managing and validating
Nexus packages.

## Global Options

The `nexus` CLI provides the following global behavior:

- **Help**: Use `--help` with any command to see detailed usage information
- **Exit Codes**: Commands exit with code `0` on success and `1` on failure

## Getting Help

### Command Help

Get help for any command:

```bash
nexus --help
nexus validate --help
nexus list --help
nexus get --help
```

### Version Information

Check the installed version:

```bash
nexus --version
```

## nexus validate

Validate the structure and configuration of a Nexus package directory.

### Usage

```bash
nexus validate <package_path>
```

### Arguments

- `package_path` (required): Path to a Nexus package directory to validate

### Examples

Validate a package in the current directory:

```bash
nexus validate .
```

Validate a package at a specific path:

```bash
nexus validate packages/my-package
```

## nexus list

List various resources in Nexus packages.

### Subcommands

#### nexus list packages

List all Nexus packages discovered in the packages directory.

**Usage:**

```bash
nexus list packages
```

**Example:**

```bash
nexus list packages
```

#### nexus list benchmark-packages

List all benchmark packages discovered across all Nexus packages.

**Usage:**

```bash
nexus list benchmark-packages
```

**Example:**

```bash
nexus list benchmark-packages
```

#### nexus list benchmark-experiments

List all benchmark experiments discovered across all Nexus packages.

**Usage:**

```bash
nexus list benchmark-experiments
```

**Example:**

```bash
nexus list benchmark-experiments
```

## nexus get

Get specific information about Nexus packages.

### Subcommands

#### nexus get benchmark-requirements

Get the list of benchmark requirement specifiers for a specific Nexus package.

**Usage:**

```bash
nexus get benchmark-requirements <package_name>
```

**Arguments:**

- `package_name` (required): Name of the Nexus package

**Example:**

```bash
nexus get benchmark-requirements terratorch
```

## Common Workflows

### Validating a New Package

When creating a new Nexus package, validate its structure:

```bash
# Navigate to your package directory
cd packages/my-new-package

# Validate the package
nexus validate .
```

### Listing Available Resources

View all packages and their resources:

```bash
# List all packages
nexus list packages

# List all benchmark packages
nexus list benchmark-packages

# List all benchmark experiments
nexus list benchmark-experiments
```

### Getting Package Information

Retrieve specific information about a package:

```bash
# Get benchmark requirements for a package
nexus get benchmark-requirements my-package
```

## Exit Codes

All commands follow standard Unix exit code conventions:

- `0`: Success
- `1`: Error (validation failed, resource not found, etc.)

## Next Steps

- Learn about [Nexus Package Structure](../design/nexus_package.md)
- Read the [Contributing Guide](../contributing/index.md)
- Explore [package requirements](../requirements/nexus_package.md)
