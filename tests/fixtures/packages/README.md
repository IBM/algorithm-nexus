# Test Package Fixtures

This directory contains sample Nexus packages for testing validation.

## Valid Package (`valid-package/`)

A complete, valid Nexus package that passes all validation checks.

**Structure:**

- ✅ Valid `nexus.yaml` with package metadata
- ✅ Optional `AGENTS.md` for embedded agent skills
- ✅ One declared model: `example-model`
- ✅ Complete model configuration with vLLM support
- ✅ Required `usage.md` documentation
- ✅ Required `tests/` directory with test files
- ✅ Optional `benchmarks/` directory with custom benchmark

**Usage:**

```bash
algorithm-nexus validate tests/fixtures/packages/valid-package
```

Expected result: ✅ Validation successful

---

## Invalid Package (`invalid-package/`)

A Nexus package with multiple validation errors for testing error detection.

**Issues:**

1. ❌ **Missing model ID**: `broken-model/model.yaml` is missing the required
   `id` field
2. ❌ **Missing vLLM testing**: `broken-model` defines `vllm` but doesn't
   provide `testing.vllm`
3. ❌ **Missing tests directory**: `broken-model` doesn't have required tests
   directory
4. ❌ **Undeclared model**: `undeclared-model` exists but is not declared in
   `nexus.yaml`

**Usage:**

```bash
algorithm-nexus validate tests/fixtures/packages/invalid-package
```

Expected result: ❌ Validation failed with multiple errors

---

## Testing with Fixtures

These fixtures can be used in automated tests:

```python
from pathlib import Path
from algorithm_nexus.cli import _validate_package_directory, ValidationErrorCollector

def test_valid_package():
    collector = ValidationErrorCollector()
    package_dir = Path("tests/fixtures/packages/valid-package")
    _validate_package_directory(package_dir, collector)
    assert not collector.has_errors

def test_invalid_package():
    collector = ValidationErrorCollector()
    package_dir = Path("tests/fixtures/packages/invalid-package")
    _validate_package_directory(package_dir, collector)
    assert collector.has_errors
    assert len(collector.errors) >= 5  # Multiple errors expected
```
