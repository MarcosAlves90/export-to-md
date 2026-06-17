# Setup

## Requirements

- Python 3.10 or newer
- `pip`
- `git` if installing from a Git repository URL

## Install from a local checkout

Register the global command from the repository root:

```bash
python3 -m pip install .
```

After installation, the command is available as:

```bash
md-extractor --help
```

## Install directly from GitHub

Install from the default branch:

```bash
python3 -m pip install "git+https://github.com/MarcosAlves90/export-to-md.git"
```

Install a specific ref:

```bash
python3 -m pip install "git+https://github.com/MarcosAlves90/export-to-md.git@main"
```

These commands are intended for end users but were not verified in this sandbox because outbound network access is blocked.

## Development setup

Create a virtual environment and install the project in editable mode:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## Validation

Verified in this repository:

```bash
./.venv/bin/python -m unittest discover -v
./.venv/bin/python -m py_compile export_to_md_v3.py md_extractor/cli.py md_extractor/__main__.py
./.venv/bin/python -m md_extractor . -o /private/tmp/md-extractor-output-2 --max-combined-size-mb 1
```
