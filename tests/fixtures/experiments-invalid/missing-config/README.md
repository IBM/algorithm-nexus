This fixture is intentionally missing `experiment_package.yaml`.
It is used to manually test that `nexus validate experiments` fails with a
clear error when an experiment directory lacks the required file.

Run:

```bash
uv run nexus validate experiments --experiments-root tests/fixtures/experiments-invalid
```

Expected: Error about missing `experiment_package.yaml` for `missing-config`.
