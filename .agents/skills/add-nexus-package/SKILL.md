---
name: add-nexus-package
description:
  Step-by-step guidance for contributing a new Nexus package to Algorithm Nexus,
  from initial setup through pull request submission. It ensures all
  configuration files are properly created, validates the package structure, and
  helps classify and add the package as a dependency. Use when users want to
  create a new Nexus package and contribute it via a pull request.
---

# Add Nexus Package

## Prerequisites

For creating a Nexus Package you need to have package level information and,
optionally, if models are included in the package also model level information.
If this information is not available stop.

Package level information

- `package_name` (string, required): Name of the Python package to add (e.g.,
  "terratorch")
- `is vllm and optional dependency`: The python package can be installed without
  vLLM in the dependencies, or with vLLM via an optional dependency group.

Model level information (for each model):

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

## Steps

Follow the below steps to create the Nexus Package:

1. **Identify the Nexus Variant**: Identify which nexus variant should the
   python package be added to.
2. **Create Nexus Package Structure**: Copy template and create package.
   directory, created thenecessary subfolders and config files.
3. **Validate Package**: Run `an validate` to check structure.
4. **Add Dependency**: Use `uv add` with correct variant classification.
5. **Suggest Next Steps**: Suggest the user next steps after the Package is
   created.

## 1. Identify the Nexus Variant

Using the prerequisite information you can infer the classification of the
package:

- Packages that don't require vLLM neither as a default or optional dependency
  and are added only to the `ecosystem` variant.

- Packages that require vLLM as a mandatory dependency and are added only to the
  `candidate` variant.

- Packages that declare vLLM as an optional dependency are added to both
  `ecosystem` and `candidate` variants.

## 2. Create package structure

Using the template in `templates/nexus-package-template` as example, create a
folder under `packages/` named after the python package and populate the
`nexus.yaml` config file with the package level information. For any models, if
any, create a subfolder with the model name and populate the `model.yaml`
configuration file using the model level information.

## 3. Validate Package

```bash
uv run nexus validate packages/<package-name>
```

If the validation is successful, the tool will print a success message
`Validation Successful`. Continue to the next step.

If the validation is nor successful, it will print `Validation Failed` followed
by a list of the errors. There are two main reasons for a failure:

1. A file is missing from the package or model directory.
2. A Pydantic failure indicating the schema for the package or one of the model
   configurations file is not correct.

Keep iterating on the validation until the failures are resolved.

## 4. Add Dependency

Depending on the variants identified in Step 1, add the python package to
project dependencies dependencies with uv.

For each variant, run the following command:

```bash
uv add <package-name> --optional <variant> --no-sync
```

If vLLM is an optional dependency, add the package to the `candidate` variant in
the form `<package-name>[vLLM-dependency]` and to the `ecosystem` variant
without any extra dependencies related to vLLM.

For each successful `uv add` create the requirement file by running:

```bash
uv export --frozen --no-emit-project --no-default-groups \
          --no-header --extra=<variant> \
          --output-file=requirements-<variant>.txt

```

In case of failure of any of the uv add commands, report the error to the user,
provide some possible causes and solutions but do not attempt changing the
dependencies of the project to fix the errors. Attempt adding the python package
to all the variants identified in Step 1, even in case one fails. Do not execute
the next step in case there are failures in this step.

## 5. Suggest Next Steps

If all the above steps are successful suggest the user what to do next:

- Create a new branch and commit your changes referencing the instructions in
  `docs/contributing/add_new_nexus_package.md`.
- Open a PR on GitHub using the `New Nexus Package` template.
