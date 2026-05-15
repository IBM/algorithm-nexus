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
nexus validate /path/to/my-package
```

## Next Steps

- Learn about [Nexus Package Structure](../design/nexus_package.md)
- Read the [Contributing Guide](../contributing/index.md)
- Explore [package requirements](../requirements/nexus_package.md)
