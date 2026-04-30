# Nexus Package Template

This is a template for creating a new Nexus package. Follow the instructions
below to customize it for your model.

## Quick Start

1. **Copy this template** to create your package:

   ```bash
   cp -r templates/packages/package-name /path/to/your-package
   cd /path/to/your-package
   ```

2. **Rename the model directory**:

   ```bash
   mv models/model-name models/your-model-name
   ```

3. **Update `nexus.yaml`**:
   - Replace `your-package-name` with your Python package name

4. **Update `models/your-model-name/model.yaml`**:
   - Replace `your-org/your-model-name` with your Hugging Face model repository
     ID
   - Optionally set `owner` with the GitHub username of the model owner
   - Add vLLM configuration if needed (or remove the commented vllm section)

5. **Add optional documentation**:
   - Create `models/your-model-name/usage.md` with usage examples (optional)

6. **Validate your package**:

   ```bash
   an validate /path/to/your-package
   ```

## Package Structure

```text
your-package/
├── nexus.yaml              # Required: Package configuration
├── skills/                 # Optional: Agent skills resources
└── models/
    └── your-model-name/
        ├── model.yaml      # Required: Model configuration
        └── usage.md        # Optional: Usage documentation
```

## Configuration Guidelines

### nexus.yaml

- `package.name`: Must match your Python package name (e.g., "terratorch")

### model.yaml

- `model.id`: Hugging Face model repository identifier (e.g.,
  "ibm-nasa-geospatial/Prithvi-EO-2.0-300M-TL")
- `model.owner`: (Optional) GitHub username of the model owner. If omitted,
  defaults to the Nexus package owner
- `model.vllm`: (Optional) Only include if your model requires additional vLLM
  plugins for the candidate or product variants
  - `enabled`: Must be `true` if the vllm section is present
  - `plugins.general`: (Optional) General vLLM plugin that loads the model class
  - `plugins.io_processors`: (Optional) List of vLLM IO processor plugins

## Documentation

For detailed documentation on Nexus package requirements, see:

- [Nexus Package Requirements](../../docs/requirements/nexus_package.md)
- [Contributing Guide](../../CONTRIBUTING.md)

## Validation

Before submitting your package, ensure it passes validation:

```bash
an validate /path/to/your-package
```

The validator checks:

- Package structure (required files and directories)
- YAML syntax
- Schema validation (field types and required fields)
- Cross-validation (e.g., vLLM enabled requires vLLM testing)
- Model declarations match directories
