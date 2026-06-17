# Requirements — md-extractor
> version: 1 | date: 2026-06-17 | status: approved

## Problem statement
Users need `md-extractor` to behave like an installable terminal command instead of a repository-local Python script. The command must be installable globally and run consistently on macOS, Linux, and Windows.

## Users and roles
- Developer using local terminal workflows and LLM tooling.
- Technical level: comfortable installing Python-based CLI tools globally.

## Functional requirements
1. [P0] The project must expose a global terminal command named `md-extractor`.
2. [P0] Installing the project with standard Python packaging tools must register the `md-extractor` command in the user's environment.
3. [P0] The command behavior and CLI flags must remain functionally equivalent to the current script behavior.
4. [P1] The existing script entrypoint should remain usable to avoid breaking current local workflows and tests immediately.
5. [P1] The repository documentation must describe global installation and command usage for macOS, Linux, and Windows.

## Non-functional requirements
- Cross-platform: must work on macOS, Linux, and Windows without shell-specific wrappers.
- Maintainability: avoid introducing a more complex distribution model than the project needs.
- Correctness: packaging changes must not alter export semantics.

## Out of scope
- Publishing to PyPI.
- Producing native standalone binaries.
- Rewriting the export engine or changing output format.

## Open questions
- None for the current implementation scope.

## Risks
- Users without Python on PATH still cannot run the tool; packaging only solves command registration once Python/pip are available.
- Refactoring the single-file script into a package can break imports or tests if compatibility is not preserved.
