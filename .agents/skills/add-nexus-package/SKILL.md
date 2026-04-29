---
name: add-nexus-package
description: Step-by-step guidance for contributing a new Nexus package to Algorithm Nexus, from initial setup through pull request submission. It ensures all configuration files are properly created, validates the package structure, and helps classify and add the package as a dependency. Use when users want to create a new Nexus package and contribute it via a pull request.
---

# Add Nexus Package

## Steps

The skill guides users through these steps:

1. **Identify package information**: Collect all the information on package and
   models to identify package classification and models.
2. **Create New Branch**: Create a new branch for the package addition
3. **Create Package Structure**: Copy template and create package directory,
   created thenecessary subfolders and config files.
4. **Validate Package**: Run `an validate` to check structure
5. **Add Dependency**: Use `uv add` with correct variant classification
6. **Commit Changes**: Commit with DCO sign-off
7. **Open Pull Request**: Use the New Nexus Package PR template

## 1. Identify package information

The main information required for the package are split between package level
and model level information.

Package level information:

- `package_name` (string, required): Name of the Python package to add (e.g.,
  "terratorch")

Model level information: Each model object contains:

- `name` (string, required): Model directory name
- `huggingface_id` (string, required): Hugging Face model repository identifier
- `owner` (string, optional): GitHub username of model owner
- `requires_vllm` (boolean, required): Whether the model uses vLLM for serving
- `vllm_plugins` (string, required): If the model uses vLLM it might also
  require a set of vlLM plugins.
  - `general` (string, optional): name of the general plugin required for
    loading the model with vLLM
  - `io_processors` (list of strings, optional): list of io processor plugins
    that the model supports for pre/post processing with vLLM

If one of the models requires vLLM, ask the user whether vLLM is a required
dependency or an optional one.

Using the above information you can infer the classification of the package:

- _Ecosystem-Only Packages_: Don't require vLLM neither as a default or optional
  dependency.
- _vLLM-Dependent Packages_: Requires vLLM as a mandatory dependency
- _vLLM-Agnostic Packages_: Declares vLLM as an optional dependency but not as a
  required one.

Also, ask the user if they want to create usage documentation for any of their
models. If that's the cas help them draft it.

## 2. Create New Branch

Create a new git branch named `add-<package-name>-package`

## 3. Create package structure

Copy the package template to the final package destination

```bash
cp -r templates/nexus-package-template packages/<package-name>
```

Then populate the package `nexus.yaml` with the package level information. For
each model, if any, create a sub folder with the model name and populate the
`model.yaml` file with the model level information.

If the users have created usage documentation for their models it should be
placed inside each model subfolder in a file named `usage.md`.

The template `assets/templates/nexus-package-template` provides exampls for the
package structure and config filaes (package `nexus.yaml` and model
`model.yaml`).

After populating the package structure, remove any files that are part of
the template and that are not needed for this package
(e.g., the sample model folder).

## 4. Validate Package

```bash
uv run an validate packages/<package-name>
```

Notes:

- Ask for user confirmation before running the validation command.

### 4.1 Example Package Validation Outputs

If the validation is successful a message will be printed to the console.

```bash
╭───────────────────────────────────────────────────────────────────────────────────────────────────────── Validation Successful ─────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ ✓ All validation checks passed                                                                                                                                                                                                          │
│                                                                                                                                                                                                                                         │
│ Optional files/directories:                                                                                                                                                                                                             │
│ i Optional package directory missing: skills                                                                                                                                                                                            │
│ i Optional model file missing for 'minimal-model': usage.md                                                                                                                                                                             │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

In case the validation is not successful, the tool will provide a list of issues
like in the snippet below

```bash
╭─────────────────────────────────────────────────────────────────────────────────────────────────────────── Validation Failed ───────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ ✗ /Users/christian/workspace/algorithm-nexus/tests/fixtures/packages/invalid-package/nexus.yaml                                                                                                                                         │
│   Field: models                                                                                                                                                                                                                         │
│   Error: Extra inputs are not permitted                                                                                                                                                                                                 │
│ ✗ /Users/christian/workspace/algorithm-nexus/tests/fixtures/packages/invalid-package/models/undeclared-model/model.yaml                                                                                                                 │
│   Field: model.testing                                                                                                                                                                                                                  │
│   Error: Extra inputs are not permitted                                                                                                                                                                                                 │
│ ✗ /Users/christian/workspace/algorithm-nexus/tests/fixtures/packages/invalid-package/models/broken-model/model.yaml                                                                                                                     │
│   Field: model.id                                                                                                                                                                                                                       │
│   Error: This required field is missing                                                                                                                                                                                                 │
│ ✗ /Users/christian/workspace/algorithm-nexus/tests/fixtures/packages/invalid-package/models/broken-model/model.yaml                                                                                                                     │
│   Field: model.testing                                                                                                                                                                                                                  │
│   Error: Extra inputs are not permitted                                                                                                                                                                                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## 5. Add Dependency

Depending on the package classification coming out of step 1, add the python
package to the dependencies with uv.

The general command for adding a package to the dependencies is:

```bash
uv add <package-name> --optional <variant>
```

The variant depends to the package classification:

- `ecosystem`: for Ecosystems-Only and vLLM Agnostic packages
- `candidate`: for vLLM-Dependent and vLLM Agnostic packages

Notes:

- Never add a package to the `product` variant
- For packages to be added to multiple variants, run the command once for each
  variant separately.
- Do not run `uv add` in any different way other than the above example.
- Ask for user confirmation before running any command.

In case of failure, help the user troubleshooting the error by interpreting the
output messages and providing potential solutions. Ask the user for confirmation
before making any change towards solving the dependency issue.

## 6. Commit Changes\*\*

Commit with DCO sign-off, this is achieved by adding the -s flag to the git
commit command.

Example commit command:

```bash
git commit -s -m "feat(package): Add <package-name> Nexus package"
```

## 7. Open Pull Request

Once all the above have been done, create the pull request text by following the
template in `./assets/templates/new_nexus_package_pr.md`.
