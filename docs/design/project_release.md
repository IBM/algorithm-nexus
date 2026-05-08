# Algorithm Nexus Release

## Summary

Algorithm Nexus releases provide the `nexus` CLI, publish optional dependency
groups for different installation needs, and are tagged in the repository with
the corresponding release version. In practice, users can either install just
the CLI, install a dependency variant directly, or install a pre-resolved
requirements file for a specific release.

## Release Definition

Each release includes:

- The CLI code and installation of the `nexus` executable.
- Four optional dependency groups: `cli`, `ecosystems`, `candidate`, and
  `product`.
- A git tag that matches the released version.

Release cadence:

- Releases happen monthly and should anticipate the product release code freeze
  by 1 week, giving some buffer for last-minute issues.
- Between regular releases, a pre-release is released for each newly added
  package or model.

## Release Usage

Users can use a release in the following ways.

### 1. Install CLI

Install the dependencies needed for the `nexus` CLI.

```bash
uv pip install algorithm-nexus[cli]
```

### 2. Install one of the variants

For example, install the `product` variant and let dependencies versions be
resolved at runtime.

`uv pip install algorithm-nexus[product]`

### 3. Install one of the variants with pre-resolved dependencies

For example, install the `product` variant with dependency versions resolved
statically by Algorithm Nexus.

```bash
uv pip install -r https://raw.githubusercontent.com/IBM/algorithm-nexus/refs/tags/{version}/requirements-{variant}.txt
```

Note that for this installation mode users will have to use the link to the raw
requirements file and explicitly specify in the URL the version (`{version}`)
and and the variant (`{variant}`) of the Algorithm Nexus release they want to
install.
