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

## nexus run

Execute benchmark instances.

### Subcommands

#### nexus run benchmarks

Execute benchmarks from a GitHub Pull Request. This command identifies new or
changed benchmark instances in a PR and optionally executes them using the `ado`
CLI.

!!! warning

    This command requires [`ado` to be installed](https://ibm.github.io/ado/getting-started/install/)
    in the local python environment.

**Usage:**

```bash
nexus run benchmarks --pr <pr_url> [OPTIONS]
```

**Required Options:**

- `--pr <pr_url>`: GitHub Pull Request URL (e.g.,
  `https://github.com/IBM/algorithm-nexus/pull/123`)

**Optional Flags:**

- `--remote <path>`: Execute operations on a remote Ray cluster using the
  specified configuration file. When provided, the command automatically
  installs the required benchmark packages in the Ray environment. Read
  [`Running ado on remote Ray clusters`](https://ibm.github.io/ado/getting-started/remote_run/)
  to discover the remote context configuration format.
- `--context <path>`: Path to ADO context YAML file (samplestore context). Read
  [`Working with Contexts`](https://ibm.github.io/ado/resources/metastore/#working-with-contexts)
  to discover how to manage contexts.
- `--list-only`: List benchmark instances without executing them
- `--output <path>`: Output file path for execution results (default:
  `output.json`)

**Behavior:**

The command automatically:

1. Checks if the local repository is on the same commit as the PR
2. If not, checks out the PR code to a temporary directory
3. Analyzes the PR to find new or changed benchmark instances
4. Executes the benchmarks (unless `--list-only` is specified)
5. Writes results to the output file

**Benchmark Instance Detection:**

A benchmark instance is detected as changed if any file within its directory is
modified in the PR. This includes:

- Changes to `space.yaml` files
- Changes to any other files in the `benchmark_instances/<instance-name>/`
  directory
- New benchmark instance directories (any new folder under
  `benchmark_instances/`)

The detection works for both:

- **Model-level instances**:
  `packages/<package>/models/<model>/benchmark_instances/<instance>/`
- **Package-level instances**:
  `packages/<package>/benchmark_instances/<instance>/`

!!! note

    When not running in remote mode (`--remote` not set), the benchmark instances will be executed with
    `ado` in the local environment. It is the user responsibility to ensure that the required
    benchmark packages are installed in the local python environment. Benchmark packages are listed for
    each nexus package in the `nexus.yaml` configuration.

**Examples:**

List benchmarks in a PR without executing:

```bash
nexus run benchmarks --pr https://github.com/IBM/algorithm-nexus/pull/123 --list-only
```

Execute benchmarks locally:

```bash
nexus run benchmarks --pr https://github.com/IBM/algorithm-nexus/pull/123
```

Execute benchmarks on a remote Ray cluster:

```bash
nexus run benchmarks \
  --pr https://github.com/IBM/algorithm-nexus/pull/123 \
  --remote path/to/remote-context.yaml \
  --context path/to/ado-context.yaml
```

Execute benchmarks and save results to a custom file:

```bash
nexus run benchmarks \
  --pr https://github.com/IBM/algorithm-nexus/pull/123 \
  --output benchmark_results.json
```

**Output Format:**

The command outputs a JSON file with the following structure:

```json
{
    "instances": [
        {
            "instance_path": "packages/<package>/models/<model>/benchmark_instances/test_benchmark",
            "status": "success",
            "message": "Successfully created space space-a009d7-default and operation None | Ray job ID: raysubmit_snRVd4ZqTTKcaR3W",
            "space_id": "space-a009d7-default",
            "operation_id": "randomwalk-123456-default",
            "ray_job_id": "raysubmit_snRVd4ZqTTKcaR3W"
        }
    ],
    "summary": {
        "successful": 1,
        "failed": 0
    }
}
```

When running in local mode (`--remote` **not** set in the cli), the `ray_job_id`
field will be `null`, while the `operation_id` field will contain the`ado`
operation ID. When running in remote mode (`--remote` set in the cli), the
`ray_job_id` field will contain the Ray job ID, while `operation_id` will be
`null`. In the latter case, users will have to inspect the Ray job logs to
extract the `ado` operation ID. In case of failure of one or more of the
benchmark instances, the message fields will contain the reason for the failure.

**Exit Codes:**

- `0`: All benchmarks executed successfully
- `1`: One or more benchmarks failed or an error occurred
- `130`: Interrupted by user (Ctrl+C)

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

### Running Benchmarks from a Pull Request

Execute benchmarks from a GitHub PR to validate changes:

```bash
# First, check what benchmarks would be executed (dry-run)
nexus run benchmarks \
  --pr https://github.com/IBM/algorithm-nexus/pull/123 \
  --list-only

# Execute benchmarks locally
nexus run benchmarks \
  --pr https://github.com/IBM/algorithm-nexus/pull/123

# Execute benchmarks on a remote Ray cluster
nexus run benchmarks \
  --pr https://github.com/IBM/algorithm-nexus/pull/123 \
  --remote config/remote-context.yaml \
  --context config/ado-context.yaml \
  --output pr123_results.json
```

The command will:

1. Automatically detect if your local repo is on the PR commit
2. Checkout the PR code if needed (to a temporary directory)
3. Find all new or changed benchmark instances
4. Execute them and report results

## Exit Codes

All commands follow standard Unix exit code conventions:

- `0`: Success
- `1`: Error (validation failed, resource not found, etc.)

## Next Steps

- Learn about [Nexus Package Structure](../design/nexus_package.md)
- Read the [Contributing Guide](../contributing/index.md)
- Explore [package requirements](../requirements/nexus_package.md)
