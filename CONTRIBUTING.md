# Contributing

> **Note:** This project is currently in closed beta. We are not accepting
> external contributions at this time. This guide is intended for IBM
> contributors only.

## For IBM Contributors

This guide provides development setup and coding standards for IBM contributors
working on Algorithm Nexus during the closed beta phase.

If you would like to fix a bug, please
[raise an issue](https://github.com/ibm/algorithm-nexus/issues) before sending a
pull request so it can be tracked.

### Merge approval

The project maintainers use LGTM (Looks Good To Me) in comments on the code
review to indicate acceptance. A change requires LGTMs from one of the
maintainers.

For a list of the maintainers, see the [MAINTAINERS.md](MAINTAINERS.md) page.

## Legal

Each source file must include a license header for the MIT License. Using the
SPDX format is the simplest approach. e.g.

```text
# Copyright IBM Corporation 2025, 2026
# SPDX-License-Identifier: Apache-2.0
```

<!-- markdownlint-disable line-length -->

We have tried to make it as easy as possible to make contributions. This applies
to how we handle the legal aspects of contribution. We use the same approach -
the
[Developer's Certificate of Origin 1.1 (DCO)](https://github.com/hyperledger/fabric/blob/master/docs/source/DCO1.1.txt) -
that the Linux® Kernel
[community](https://elinux.org/Developer_Certificate_Of_Origin) uses to manage
code contributions.

<!-- markdownlint-enable line-length -->

We simply ask that when submitting a patch for review, the developer must
include a sign-off statement in the commit message.

Here is an example Signed-off-by line, which indicates that the submitter
accepts the DCO:

```text
Signed-off-by: John Doe <john.doe@example.com>
```

You can include this automatically when you commit a change to your local git
repository using the following command:

```commandline
git commit -s
```

## Communication

You can get in touch with us by starting a
[discussion](https://github.com/IBM/algorithm-nexus/discussions) on GitHub.

## Commit and PR title guidelines

We require commits and PR titles to conform to the
[conventional commits standard](https://www.conventionalcommits.org/en/v1.0.0/)
and follow the
[Angular convention](https://github.com/angular/angular/blob/22b96b9/CONTRIBUTING.md#-commit-message-guidelines).
In a nutshell, the commit message should be structured as follows:

> [!TIP]
>
> It is highly recommended to include the scope in the PR title and in all the
> commits

```plaintext
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Where `type` is one of the following:

- **build**: Changes that affect the build system (e.g., pyproject.toml files,
  Dockerfiles, etc.) or external dependencies.
- **ci**: Changes to CI-related configuration files and scripts
- **docs**: Documentation only changes
- **feat**: A new feature
- **fix**: A bug fix
- **perf**: A code change that improves performance
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **style**: Changes that do not affect the meaning of the code (white-space,
  formatting, etc)
- **test**: Adding missing tests or correcting existing tests
- **chore** (discouraged): Minor changes that don't fit in other categories

## Coding style guidelines

We require code and markup to adhere to certain rules. We enforce these rules
through the following tools:

- [Black](https://black.readthedocs.io/) - Python code formatting
- [Ruff](https://docs.astral.sh/ruff/) - Python linting
- [uv](https://github.com/astral-sh/uv) - Dependency management
- [Copywrite](https://github.com/hashicorp/copywrite) - License header
  management
- [Markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2) -
  Markdown linting
- [Yamlfmt](https://github.com/google/yamlfmt) - YAML formatting

Before submitting a pull request, you must ensure that all of the following
checks pass.

### Using Pre-commit Hooks (Recommended)

We provide pre-commit hooks that automatically run these checks before each
commit. To set up pre-commit hooks:

1. Install development dependencies (includes pre-commit and all linting tools):

   ```commandline
   uv sync --group dev
   ```

2. Install the git hook scripts:

   ```commandline
   pre-commit install --install-hooks
   pre-commit install --hook-type commit-msg
   ```

3. (Optional) Run against all files:

   ```commandline
   pre-commit run --all-files
   ```

Once installed, the hooks will run automatically on `git commit`. If any checks
fail, the commit will be aborted and you'll need to fix the issues before
committing again.

### Manual Verification

Alternatively, you can manually verify that your code conforms to these rules by
running the following commands:

```commandline
black --check .
ruff check
uv lock --check
copywrite headers --plan
markdownlint-cli2 "**/*.md" "#.venv" "#.tox"
detect-secrets scan --update .secrets.baseline
detect-secrets audit .secrets.baseline --fail-on-unaudited --fail-on-live --fail-on-audited-real
yamlfmt -lint -exclude ".venv" -exclude ".tox" .
```

The `uv lock --check` command verifies that the `uv.lock` lockfile is up-to-date
with the dependencies specified in `pyproject.toml`. If this check fails, run
`uv lock` to regenerate the lockfile.
