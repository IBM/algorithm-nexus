# Nexus Package Template

This is a template for creating a new Nexus package. Follow the instructions
below to customize it for your model.

## Quick Start

1. **Copy this template** to create your package:

   ```bash
   cp -r templates/nexus-package-template /path/to/your-package
   cd /path/to/your-package
   ```

2. **Rename the model directory**:

   ```bash
   mv models/your-model-name models/your-actual-model-name
   ```

3. **Update `nexus.yaml`**:
   - Replace `your-package-name` with your package name
   - Replace `your-model-name` with your model directory name
   - Update version and agent_skills as needed

4. **Update `models/your-model-name/model.yaml`**:
   - Replace `your-org/your-model-name` with your model ID
   - Replace `your-gh-id` with the GitHub ID of the model owner if explicitly
     set.
   - Configure hardware requirements
   - Add vLLM configuration if needed (or remove the vllm section)
   - Update test commands

5. **Implement tests**:
   - Add actual inference tests in `tests/test_inference.py`
   - Add vLLM tests in `tests/test_vllm.py` (if using vLLM)

6. **Validate your package**:

   ```bash
   algorithm-nexus validate /path/to/your-package
   ```

## Package Structure

```text
your-package/
├── nexus.yaml              # Package configuration
├── models/
│   └── your-model-name/
│       ├── model.yaml      # Model configuration
│       └── tests/
│           ├── test_inference.py  # Inference tests
│           └── test_vllm.py       # vLLM tests (if applicable)
└── README.md
```

## Configuration Guidelines

### vLLM Configuration

- If your model uses vLLM, set `vllm.enabled: true` and provide vLLM testing
- If not using vLLM, remove the entire `vllm` section from `model.yaml`
- The `enabled` field must be `true` if the vllm section is present

### Testing Requirements

- All models must have a `tests/` directory with at least one test file
- Test commands must be specified in `model.testing.commands`
- If `vllm.enabled: true`, you must provide `model.testing.vllm.commands`

### Hardware Requirements

- Specify CPU requirements (cores and RAM)
- Optionally specify GPU requirements (type, count, cpu_fallback)

## Documentation

For detailed documentation on Nexus package requirements, see:

- [Nexus Package Requirements](../../docs/requirements/nexus_package.md)
- [Contributing Guide](../../CONTRIBUTING.md)

## Validation

Before submitting your package, ensure it passes validation:

```bash
algorithm-nexus validate /path/to/your-package
```

The validator checks:

- Package structure (required files and directories)
- YAML syntax
- Schema validation (field types and required fields)
- Cross-validation (e.g., vLLM enabled requires vLLM testing)
- Model declarations match directories
