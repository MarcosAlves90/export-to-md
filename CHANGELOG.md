# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project follows Semantic Versioning.

## [Unreleased]

## [1.0.0] - 2026-06-17
### Added
- Python packaging via `pyproject.toml`.
- Global CLI command `md-extractor` through `console_scripts`.
- Package entrypoints under `md_extractor/`.
- Installation guidance for local, global, and Git-based usage.

### Changed
- Moved the main CLI implementation out of the repository-root script into a package module.
- Kept `export_to_md_v3.py` as a compatibility shim.
