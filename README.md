# md-extractor

[![CI](https://github.com/MarcosAlves90/export-to-md/actions/workflows/ci.yml/badge.svg)](https://github.com/MarcosAlves90/export-to-md/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![CLI](https://img.shields.io/badge/interface-CLI-2E3440)
![Markdown](https://img.shields.io/badge/output-Markdown-000000?logo=markdown&logoColor=white)
![Dependency](https://img.shields.io/badge/dependency-pathspec-4B8BBE)

Export a source directory into Markdown files that are easier to inspect,
archive, or paste into LLM workflows. The CLI respects `.gitignore`, skips
`.git`, preserves the original tree, and writes each export under
`markdown_export/<folder-name>/`.

## Features

- Respects `.gitignore` using `pathspec`
- Excludes `.git` and the configured output directory
- Writes output to `<output>/<source-folder-name>/`
- Preserves the source directory structure inside the export folder
- Creates one Markdown file per source file
- Adds file metadata: relative path, size, estimated MIME type, and SHA-256
- Detects likely binary files and omits raw binary content
- Omits raw content for files above the configured size limit
- Generates `TREE.md`, `SUMMARY.md`, and optionally `PROJECT_CONTEXT.md`

## Output Files

| File | Purpose |
|---|---|
| `TREE.md` | Directory tree for the exported project |
| `SUMMARY.md` | File counts, directory counts, total bytes, and extension stats |
| `PROJECT_CONTEXT.md` | Consolidated text context for LLM review |
| `<source-file>.md` | Metadata and content for each exported source file |

## Installation

Install from a local checkout:

```bash
python3 -m pip install .
```

Install directly from GitHub:

```bash
python3 -m pip install "git+https://github.com/MarcosAlves90/export-to-md.git"
```

If you prefer an isolated global install from a local checkout, `pipx` also works:

```bash
pipx install .
```

For development setup details, see [docs/SETUP.md](docs/SETUP.md).

For local development, use:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## Usage

Export a folder into `markdown_export/<folder-name>/`:

```bash
md-extractor /path/to/folder
```

Choose a different base output folder:

```bash
md-extractor /path/to/folder -o markdown_export
```

Increase the per-file raw content limit:

```bash
md-extractor /path/to/folder --max-file-size-mb 5
```

Increase the consolidated context limit:

```bash
md-extractor /path/to/folder --max-combined-size-mb 20
```

Skip `PROJECT_CONTEXT.md`:

```bash
md-extractor /path/to/folder --no-consolidated
```

## CLI Reference

```text
usage: md-extractor [-h] [-o OUTPUT]
                    [--max-file-size-mb MAX_FILE_SIZE_MB]
                    [--max-combined-size-mb MAX_COMBINED_SIZE_MB]
                    [--no-consolidated]
                    folder
```

| Argument | Default | Description |
|---|---:|---|
| `folder` | required | Source folder to analyze |
| `-o, --output` | `markdown_export` | Base folder where `<source-folder-name>/` is created |
| `--max-file-size-mb` | `2` | Maximum individual file size for raw content |
| `--max-combined-size-mb` | `10` | Maximum size for `PROJECT_CONTEXT.md` content |
| `--no-consolidated` | `false` | Do not generate `PROJECT_CONTEXT.md` |

## Example Output

```text
markdown_export/
└── my-project/
    ├── TREE.md
    ├── SUMMARY.md
    ├── PROJECT_CONTEXT.md
    ├── README.md.md
    └── src/
        ├── main.py.md
        └── services/
            └── user.py.md
```

## Validation

Verified commands:

```bash
./.venv/bin/python -m unittest discover -v
./.venv/bin/python -m py_compile export_to_md_v3.py md_extractor/cli.py md_extractor/__main__.py
./.venv/bin/python -m md_extractor . -o /private/tmp/md-extractor-output-2 --max-combined-size-mb 1
```

See [docs/SETUP.md](docs/SETUP.md), [docs/TESTING.md](docs/TESTING.md), and
[CHANGELOG.md](CHANGELOG.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Commits must use Conventional Commits.
