# Contributing

Keep changes small, reviewable, and tied to one clear purpose.

## Commit Messages

All commits must follow the Conventional Commits format:

```text
<type>(optional-scope): <description>
```

Examples:

```text
docs: improve README usage examples
fix: skip output directory during export
refactor(cli): simplify argument parsing
```

Use one of these commit types:

| Type | Use when |
|---|---|
| `feat` | Adding user-facing functionality |
| `fix` | Fixing incorrect behavior |
| `docs` | Updating documentation only |
| `refactor` | Changing structure without changing behavior |
| `test` | Adding or updating tests |
| `chore` | Maintenance that does not affect runtime behavior |
| `ci` | Updating CI or automation |
| `build` | Updating packaging, dependencies, or build setup |

Rules:

- Use lowercase commit types.
- Keep the subject line under 72 characters when practical.
- Use the imperative mood: `fix`, `add`, `update`, not `fixed` or `adds`.
- Do not combine unrelated changes in one commit.
- Use a body when the reason or tradeoff is not obvious from the diff.

## Branch Names

Use short, descriptive branch names:

```text
docs/readme-contributing
fix/output-directory-skip
refactor/export-config
```

## Pull Requests

Each pull request should include:

- What changed
- Why it changed
- How it was validated
- Any known risks or follow-up work

## Validation

Before opening a pull request, run:

```bash
python -m unittest discover -v
python -m py_compile export_to_md_v3.py md_extractor/cli.py md_extractor/__main__.py
```

If the package is installed, also run a small export:

```bash
md-extractor . -o /tmp/md-extractor-output --max-combined-size-mb 1
```
