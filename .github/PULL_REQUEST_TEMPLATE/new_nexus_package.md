---
name: New Nexus Package
about: Submit a new Nexus package to Algorithm Nexus
title: "feat(package): Add [package-name] Nexus package"
labels: "nexus-package"
---

## Package Information

**Package Name:** <!-- e.g., terratorch -->

**Python Package Source:** <!-- GitHub URL -->

**Brief Description of the Package**:

<!-- This package enables this class of algorithms/models, etc. -->

**Distribution Variant(s):** <!-- Check all that apply -->

- [ ] Ecosystem (no vLLM dependency)
- [ ] Candidate (with vLLM dependency)
- [ ] Product (to be added by maintainers)

## Models Included

<!-- List all models included in this Nexus package -->

| Model Name             | Hugging Face ID                                           | Requires vLLM   | Owner                                                 |
| ---------------------- | --------------------------------------------------------- | --------------- | ----------------------------------------------------- |
| <!-- e.g., prithvi --> | <!-- e.g., ibm-nasa-geospatial/Prithvi-EO-2.0-300M-TL --> | <!-- Yes/No --> | <!-- GitHub username or leave blank for "default" --> |

## Checklist

Please ensure you have completed all the following steps before submitting this
PR:

### Step 1: Create Your Nexus Package

- [ ] Copied the Nexus package template to `packages/<package-name>/`
- [ ] Updated the nexus package folder with your models and configuration

### Step 2: Validate Your Nexus Package

- [ ] Ran `uv run an validate packages/<package-name>` successfully

### Step 3: Add Your Package to Algorithm Nexus

- [ ] Added package to appropriate variant(s) using `uv add`
- [ ] Verified lockfile updated with `uv lock --check`

## Additional Information

<!-- Add any additional context, notes, or special considerations for reviewers -->

## I need help with this PR

<!-- If you are unable to pass the dependencies resolution (i.e., you have tried to
fix it yourself, and still it does not work), describe your issue by provideding the
uv logs and any other information that could help themaintainers addressing your
specific problem.-->

## Related Issues

<!-- Link any related issues, e.g., Closes #123 -->
