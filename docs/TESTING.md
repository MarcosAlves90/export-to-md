# Testing

This project uses Python's standard `unittest` runner to keep the test setup
small and dependency-free.

## Test Pyramid

The project is a single-file CLI, so the test suite is intentionally weighted
toward fast integration-style tests that exercise the real filesystem in a
temporary directory.

| Level | Scope |
|---|---|
| Unit | Pure helpers such as validation and content classification, added as behavior grows |
| Integration | CLI export flow against temporary folders and generated Markdown files |
| End-to-end | Not used; there is no browser, service, or deployed environment |

## Local Commands

Run the test suite:

```bash
python -m unittest discover -v
```

Run the syntax check:

```bash
python -m py_compile export_to_md_v3.py
```

## CI Policy

Every pull request and push to `main` must pass:

- dependency installation from `requirements.txt`
- Python syntax check
- automated tests
