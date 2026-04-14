schema_version = 1

project {
  license        = "Apache-2.0"
  copyright_year = 2024

  header_ignore = [
    # Ignore generated files
    "**/*.md",
    "**/*.json",
    "**/*.yaml",
    "**/*.yml",
    "**/*.toml",
    "**/*.txt",
    "**/*.lock",

    # Ignore directories
    ".venv/**",
    ".tox/**",
    "**/__pycache__/**",
    "*.egg-info/**",
    "dist/**",
    "build/**",
    ".pytest_cache/**",
    ".ruff_cache/**",
    ".mypy_cache/**",

    # Ignore specific files
    "LICENSE",
    ".gitignore",
    ".secrets.baseline",
    ".pre-commit-config.yaml",
    ".copywrite.hcl",
  ]
}
