## Requirements summary
- Expose a global command named `md-extractor`.
- Support installation on macOS, Linux, and Windows.
- Preserve current CLI behavior and flags.
- Keep the existing script path usable during the transition.

## Approaches considered

### 1. Python package with `console_scripts`
Use `pyproject.toml` with a standard build backend and register `md-extractor` as a console entrypoint. Move the implementation into a package module and keep a thin compatibility shim for the old script.

Trade-offs: simplest cross-platform path with native `pip` support; still depends on a Python runtime being installed.

### 2. Shell and batch wrapper scripts around the current file
Keep the script as-is and add wrapper launchers for Unix shells and Windows batch/PowerShell. Users would manually place the wrappers on PATH.

Trade-offs: low code churn in the Python logic; poor install story, shell-specific behavior, and higher maintenance across OSes.

### 3. Native standalone binaries
Bundle the tool into platform-specific executables via a freezer such as PyInstaller. Distribute one binary per target OS.

Trade-offs: best end-user ergonomics after distribution; highest complexity, larger artifacts, and extra release/build maintenance.

## Evaluation

| Approach | Simplicity | Scalability | Dev speed | Operational cost | Fit to constraints |
|----------|-----------|-------------|-----------|------------------|--------------------|
| Python package with `console_scripts` | ✓✓ | ✓ | ✓✓ | ✓✓ | ✓✓ |
| Shell and batch wrappers | ✓ | ✗ | ✓ | ✓ | ✗ |
| Native standalone binaries | ✗ | ✓ | ✗ | ✗ | ✓ |

## Selected approach
**Selected:** Python package with `console_scripts`

**Rationale:** This is the smallest responsible change that turns the project into a globally installable command while remaining OS-agnostic. It uses the standard Python packaging path that already works across macOS, Linux, and Windows, preserves the existing implementation with minimal refactoring, and avoids the maintenance burden of platform-specific wrappers or binary release tooling.

**Key risk:** Packaging refactors can accidentally break imports or the legacy script path if compatibility is not preserved.

## Deferred decisions
- Whether to publish the package to PyPI.
- Whether to add native binary builds in CI for users without Python tooling.
- Whether to rename internal modules and tests after the compatibility period.
