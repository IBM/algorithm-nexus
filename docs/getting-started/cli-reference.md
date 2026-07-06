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

Validate various aspects of Nexus packages.

### Subcommands

#### nexus validate package

Validate the structure and configuration of a Nexus package directory.

**Usage:**

```bash
nexus validate package <package_path>
```

**Arguments:**

- `package_path` (required): Path to a Nexus package directory to validate

**Examples:**

Validate a package in the current directory:

```bash
nexus validate package .
```

Validate a package at a specific path:

```bash
nexus validate package packages/my-package
```

#### nexus validate benchmarks

Validate benchmark instances in three modes: PR changes, all instances, or
specific package.

**Usage:**

```bash
# Validate PR changes
nexus validate benchmarks --pr <pr_url> [OPTIONS]

# Validate all benchmark instances
nexus validate benchmarks [OPTIONS]

# Validate specific package
nexus validate benchmarks --package <package_name> [OPTIONS]
```

**Options:**

- `--pr URL`: GitHub Pull Request URL (e.g.,
  `https://github.com/IBM/algorithm-nexus/pull/123`). If not provided, validates
  all benchmark instances.
- `--packages-root PATH`: Path to packages directory (default: `./packages`)
- `--package NAME`: Validate only benchmark instances from a specific package
- `--verbose`: Show detailed validation output
- `--fail-fast`: Stop validation on first error
- `-o, --output-format [table|json|yaml]`: Output format (default: `table`)

**Examples:**

Validate benchmarks in a PR:

```bash
nexus validate benchmarks --pr https://github.com/IBM/algorithm-nexus/pull/123
```

Validate all benchmark instances:

```bash
nexus validate benchmarks
```

Validate only instances from a specific package:

```bash
nexus validate benchmarks --package terratorch
```

Validate with verbose output:

```bash
nexus validate benchmarks --pr https://github.com/IBM/algorithm-nexus/pull/123 --verbose
```

Validate and stop on first error:

```bash
nexus validate benchmarks --fail-fast
```

Get results in JSON format:

```bash
nexus validate benchmarks --output-format json
# or using the short form
nexus validate benchmarks -o json
```

Get results in YAML format:

```bash
nexus validate benchmarks --output-format yaml
# or using the short form
nexus validate benchmarks -o yaml
```

**How it works:**

1. **Discovery**: Finds benchmark instances based on mode:
    - PR mode: Analyzes PR diff to find modified instances
    - All mode: Scans packages directory for all instances
    - Package mode: Finds instances in specified package
2. **Dependency Resolution**: Groups instances by required benchmark packages
3. **Isolation**: Creates temporary virtual environments for each dependency set
4. **Installation**: Installs required benchmark packages using `uv` (10-100x
   faster) or `pip`
5. **Validation**: Validates each instance's `space.yaml` structure using
   Pydantic models and ADO dry-run
6. **Reporting**: Displays results in table or JSON format with validation
   status, errors, and warnings

**Requirements:**

- For PR mode: GitHub CLI (`gh`) must be installed and authenticated
- ADO must be included as a dependency in benchmark packages

#### nexus validate logical-benchmarks

Validate logical benchmark YAML files for schema correctness and referential integrity.

**Usage:**

```bash
# Validate all files under ./benchmarks (default)
nexus validate logical-benchmarks [OPTIONS]

# Validate all files under a custom directory
nexus validate logical-benchmarks --benchmarks-root <path> [OPTIONS]

# Validate a single file
nexus validate logical-benchmarks --file <path> [OPTIONS]
```

**Options:**

- `--benchmarks-root PATH`: Path to the directory containing logical benchmark YAML files (default: `./benchmarks`)
- `--file FILE`: Validate a single logical benchmark YAML file instead of the whole directory
- `-o, --output-format [table|json|yaml]`: Output format (default: `table`)
- `--output-file PATH`: Write results to a file. Format is inferred from the file extension
  (`.json`/`.yaml`) unless `--output-format` is also set

**Examples:**

Validate all logical benchmarks in the default directory:

```bash
nexus validate logical-benchmarks
```

Validate logical benchmarks in a custom directory:

```bash
nexus validate logical-benchmarks --benchmarks-root path/to/benchmarks
```

Validate a single file:

```bash
nexus validate logical-benchmarks --file benchmarks/inference_serving.yaml
```

Get results in JSON format:

```bash
nexus validate logical-benchmarks -o json
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

**Usage:**

```bash
nexus run benchmarks --pr <pr_url> [OPTIONS]
```

!!! warning

    This command requires the [GitHub CLI (`gh`)](https://cli.github.com/) to be installed and
    configured in the command execution environment.

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
- `--dry-run`: List benchmark instances without executing them (dry run)
- `--output-file <path>`: Output file path for execution results. If not
  specified, results are printed to screen.
- `-o, --output-format <format>`: Output format: 'json' or 'yaml'. Can be used
  with or without `--output-file`. When used without `--output-file`, prints
  formatted output to console. When used with `--output-file`, overrides format
  inference from file extension (defaults to json).

**Behavior:**

The command automatically:

1. Checks if the local repository is on the same commit as the PR
2. If not, checks out the PR code to a temporary directory
3. Analyzes the PR to find new or changed benchmark instances
4. Executes the benchmarks (unless `--dry-run` is specified)
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

List benchmarks in a PR without executing (dry run):

```bash
nexus run benchmarks --pr https://github.com/IBM/algorithm-nexus/pull/123 --dry-run
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

Execute benchmarks and save results to a file:

```bash
nexus run benchmarks \
  --pr https://github.com/IBM/algorithm-nexus/pull/123 \
  --output-file benchmark_results.json
```

Execute benchmarks and save results in YAML format:

```bash
nexus run benchmarks \
  --pr https://github.com/IBM/algorithm-nexus/pull/123 \
  --output-file results.yaml \
  --output-format yaml
```

**Output Format:**

By default, the command outputs results in a human-readable format showing the
status, message, and IDs for each benchmark instance.

To get structured output (JSON or YAML), use the `--output-format` option:

```bash
# Print JSON to console
algorithm-nexus run packages/terratorch/models/prithvi/benchmark_instances/flood-test \
  --output-format json

# Print YAML to console
algorithm-nexus run packages/terratorch/models/prithvi/benchmark_instances/flood-test \
  --output-format yaml
```

The structured output (JSON) has the following format:

```json
{
    "instances": [
        {
            "instance_path": "packages/<package>/models/<model>/benchmark_instances/test_benchmark",
            "status": "started",
            "message": "Successfully started on Ray cluster with job ID: raysubmit_snRVd4ZqTTKcaR3W | Space ID: space-a009d7-default",
            "space_id": "space-a009d7-default",
            "operation_id": "randomwalk-123456-default",
            "ray_job_id": "raysubmit_snRVd4ZqTTKcaR3W"
        }
    ]
}
```

**Status Values:**

- `success`: Benchmark completed successfully (local execution)
- `started`: Benchmark started on Ray cluster (remote execution)
- `failed`: Benchmark execution failed
- `unknown`: Status could not be determined

**Execution Mode Comparison:**

| Field          | Local Mode (`--remote` not set)                                              | Remote Mode (`--remote` set)                                                 |
| -------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `status`       | `success` (on success)<br>`failed` (on error)<br>`unknown` (if undetermined) | `started` (on success)<br>`failed` (on error)<br>`unknown` (if undetermined) |
| `operation_id` | ADO operation ID                                                             | `null`                                                                       |
| `ray_job_id`   | `null`                                                                       | Ray job ID                                                                   |
| Notes          | Operation completes locally                                                  | Job submitted to Ray cluster                                                 |

When `operation_id` is `null` (in remote mode), users will need to inspect the
Ray job logs to extract the ADO operation ID once execution completes.

In case of failure (either mode), the `status` will be `failed` and the
`message` field will contain the reason for the failure.

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
nexus validate package .
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
# First, check what benchmarks would be executed (dry run)
nexus run benchmarks \
  --pr https://github.com/IBM/algorithm-nexus/pull/123 \
  --dry-run

# Execute benchmarks locally
nexus run benchmarks \
  --pr https://github.com/IBM/algorithm-nexus/pull/123

# Execute benchmarks on a remote Ray cluster
nexus run benchmarks \
  --pr https://github.com/IBM/algorithm-nexus/pull/123 \
  --remote config/remote-context.yaml \
  --context config/ado-context.yaml \
  --output-file pr123_results.json
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
