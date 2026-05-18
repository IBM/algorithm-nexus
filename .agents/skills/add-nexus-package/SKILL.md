---
name: add-nexus-package
description:
  Step-by-step guidance for contributing a new algorithm stack python package to
  Algorithm Nexus. It ensures all configuration files are properly created,
  validates the structure of the required nexus package, and helps classify and
  add the algorithm stack package as a dependency. Use when users want to create
  a Nexus package for their python library or add their python library to
  algorithm nexus.
---

# Adding an Algorithm Stack Package to Algorithm Nexus

## Prerequisites

To add an algorithm stack package to Algorithm Nexus the below package level
information is required:

- `package_name` (string, required): Name of the Nexus package to be added as
  per the
  [prerequisites](../../../docs/contributing/add_new_nexus_package.md#prerequisites)
  in the _Contributing a python algorithm package to Algorithm Nexus_.
- `package_url` (string, required): URL of the python package repository on
  GitHub.
- `package_version` (string, required): GitHub release version of the python
  package to be added to the dependencies.
- `is vllm and optional dependency`: The python package can be installed without
  vLLM in the dependencies, or with vLLM via an optional dependency group.

If this information is not available stop.

It is optional to include models information in the package. However, for a
model to be included, the following information is required:

- `huggingface_id` (string, required): Hugging Face model repository identifier.
- `name` (string, required): Name of the model to be used as folder name.
- `owner` (string, optional): GitHub username of model owner
- `requires_vllm` (boolean, required): Whether the model uses vLLM for serving
- `vllm_plugins` (string, required): If the model uses vLLM it might also
  require a set of vlLM plugins.
  - `general` (string, optional): name of the general plugin required for
    loading the model with vLLM
  - `io_processors` (list of strings, optional): list of io processor plugins
    that the model supports for pre/post processing with vLLM

If a model has been specified to be added and the above information is not
available, stop.

## Steps

Follow the below steps to create the Nexus Package:

1. **Inspect the Algorithm Stack Package Source**: Inspect the code to extract
   information about the package.
2. **Identify the Nexus Variant**: Identify which nexus variant should the
   python package be added to.
3. **Create Nexus Package Structure**: Create the necessary Nexus package folder
   structure and populate config files.
4. **Validate the Nexus Package**: Run `nexus validate` to check structure.
5. **Add Algorithm Stack Package as an Algorithm Nexus Dependency**: Use
   `uv add` with correct variant classification.
6. **Write Report**: Write a report of the changes made and any errors
   encountered.

## 1. Inspect the Algorithm Stack Package Source

If the python package repository is not checked out locally, clone the
repository to a temporary location.

Inspect the source code to identify:

- Available models and their Hugging Face ID.
  - No two models can have the same Hugging Face ID. If that's the case, stop.
  - Extract the model name from the Hugging Face ID, i.e. model-name in
    "org/model-name".
- Whether the package requires vLLM or not, and if it does whether vLLM is a
  mandatory or optional requirement.
- The GitHub release version of the python package to be installed.
  - If no specific GitHub release version is provided by the user, inspect the
    repository to identify the latest GitHub release.
  - If no GitHub release is available, stop and inform the user that a GitHub
    release is required.

## 2. Identify the Nexus Variant

Using the prerequisite information you can infer the distribution variant the
algorithm stack package should be added to by following the instructions in the
[_Variant Association Rules_ section](../../../docs/design/dependency-resolution.md#4-variant-association-rules)
of the dependency resolution design document.

No algorithm stack package can be added to the `product` variant.

## 3. Create Nexus Package Structure

Using the prerequisite information create the Nexus package structure as
outlined in the
[_Create a Nexus package for your algorithm_ section](../../../docs/contributing/add_new_nexus_package.md#step-3-create-a-nexus-package-for-your-algorithm)
of the _Contributing a python algorithm package to Algorithm Nexus_ document. If
models are to be included, follow the instructions in
[_Describe the Models in Your Algorithm Package_ section](../../../docs/contributing/add_new_nexus_package.md#describe-the-models-in-your-algorithm-package)
of the _Contributing a python algorithm package to Algorithm Nexus_ documentat.

## 4. Validate the Nexus Package

```bash
uv run nexus validate packages/<package-name>
```

If the validation is successful, the tool will print a success message
`Validation Successful`. Continue to the next step.

If the validation is not successful, it will print `Validation Failed` followed
by a list of the errors.

There are two main reasons for a failure:

1. A file is missing from the package or models directory.
2. A Pydantic failure indicating the schema for the package or one of the model
   configuration files is not correct.

For pydantic failures, iterate on the validation until the failures are
resolved. If a failure is related to a missing file, check the instructions in
step 2 to identify and add the missing file, and run the validation again.

## 5. Add Algorithm Stack Package as an Algorithm Nexus Dependency

For each variant the algorithm stack package was identified as belonging to in
step 1, follow the instructions in
[`Step 2: Add your algorithm package to the Algorithm Nexus dependencies`](../../../docs/contributing/add_new_nexus_package.md#step-2-add-your-algorithm-package-to-the-algorithm-nexus-dependencies).

In case of failure with uv when adding the algorithm stack package to a variant:

- Report the error with some suggested fixes.
- Do not attempt changing the dependencies of the project to fix the errors.
- Skip this variant and continue to the next variant if any.

## 6. Write Report

Generate a report of the changes and unresolved issues following the
[New Nexus Package PR template](../../../.github/PULL_REQUEST_TEMPLATE/new_nexus_package.md).
Only add a summary of the changes, without including the rationale behind the
changes. Save the report as a markdown in a file.
