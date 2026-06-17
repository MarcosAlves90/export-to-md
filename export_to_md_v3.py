#!/usr/bin/env python3
"""Compatibility entrypoint for the packaged CLI."""

from md_extractor.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
