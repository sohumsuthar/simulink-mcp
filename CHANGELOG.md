# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-05-14

### Fixed
- **Security:** `get_simulation_data` now validates `variable_name` as a MATLAB
  identifier (`^[A-Za-z][A-Za-z0-9_]*$`) before using it as a struct field
  accessor. Previously a name like `tout; disp('x')` would have executed as
  MATLAB code on one of the resolution paths.
- `simulate` registers cleanly under pydantic >= 2.12 / 2.13. The tool now
  declares `structured_output=False` because its `Image` return type cannot be
  turned into a pydantic output schema.

### Changed
- `requires-python` raised to `>=3.10`. The previous floor of 3.9 was
  unenforceable — every published version of the upstream `mcp` package
  requires Python >= 3.10, so 3.9 installs were already failing.

### Internal
- Renamed temp MATLAB workspace var `celldisp_out` → `__mcp_param_names` to
  match the `__mcp_` prefix convention.
- Added GitHub Actions CI: build + import on Python 3.10–3.12, ruff
  critical-rule lint, and `python -m build` + `twine check` package
  validation.

## [0.1.0] - 2026-04-12

Initial release. Pip-installable package exposing 14 Simulink MCP tools across
model management, inspection, modification, and simulation.
