# simulink-mcp

MCP server for MATLAB Simulink. Python package in `simulink_mcp/`.

## Structure

- `simulink_mcp/app.py` — FastMCP instance, MATLAB engine manager, helpers (`escape_matlab`, `matlab_eval`, `capture_figures`)
- `simulink_mcp/tools/` — Tool modules: model_management (4), inspection (3), modification (5), simulation (2)
- `simulink_mcp/__init__.py` — Registers all tools, exports `main()`
- `simulink_mcp/__main__.py` — `python -m simulink_mcp` entry point

## Key Patterns

- All MATLAB eval calls go through `matlab_eval()` for stdout/stderr isolation
- User inputs in eval strings **must** be escaped with `escape_matlab()` (single-quote doubling)
- Temp MATLAB workspace variables use `__mcp_` prefix and are always cleaned up with `clear`
- MATLAB engine is lazily initialized on first tool call — never `import matlab.engine` at module level
- Tools return error strings on failure, never raise exceptions through MCP

## Running

```bash
python -m simulink_mcp        # stdio transport
simulink-mcp                   # if pip-installed
```

Requires MATLAB with Simulink and `matlabengine` pip package installed separately.
