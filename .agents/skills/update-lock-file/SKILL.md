---
name: update-lock-file
description: >
    Use when the user wants to update the project lock file and requirements
    files. Syncs uv.lock with origin/main, regenerates lock, and exports all
    requirement files, then commits the result.
---

# Update Lock File and Requirements Files

Follow these steps in order to update the project lock file and requirement
files.

## 1. Verify the Branch is Up-to-Date with origin/main

Run the following command to check how many commits the current branch is behind
`origin/main`:

```bash
git fetch origin main && git rev-list --count HEAD..origin/main
```

- If the count is **0**, the branch is up-to-date. Continue to Step 2.
- If the count is **greater than 0**, the branch is behind. Inform the user and
  ask whether they would like you to rebase the current branch on top of
  `origin/main`. Wait for their response before proceeding.
    - If the user says **yes**, run:

        ```bash
        git rebase origin/main
        ```

        If the rebase exits with a non-zero status, stop and report the error to
        the user — do not attempt to resolve conflicts automatically.

    - If the user says **no**, stop here and let the user update the branch
      before retrying.

## 2. Perform the Dependency Update

Run the following commands **in order**, one at a time. Stop and report any
failure before proceeding to the next command.

```bash
git restore --source origin/main -- uv.lock
```

```bash
uv lock
```

```bash
uv export --frozen --no-emit-project --no-default-groups --no-header --extra=candidate --output-file=requirements-candidate.txt
```

```bash
uv export --frozen --no-emit-project --no-default-groups --no-header --extra=ecosystem --output-file=requirements-ecosystem.txt
```

```bash
uv export --frozen --no-emit-project --no-default-groups --no-header --extra=product --output-file=requirements-product.txt
```

## 3. Commit the Updated Files

Stage and commit the lock file and all three requirements files:

```bash
git add uv.lock requirements-candidate.txt requirements-ecosystem.txt requirements-product.txt
git commit -m "chore(dependencies): Updated lock file and requirement files"
```

If there are no files to be committed it means the project dependencies are
already up-to date, inform the user and stop. Otherwise, commit the changes and
confirm to the user that the commit was created successfully.
