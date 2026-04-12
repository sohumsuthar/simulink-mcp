<div align="center">

# simulink-mcp

**Give AI assistants direct access to MATLAB Simulink.**

[![License: PolyForm NC 1.0](https://img.shields.io/badge/license-PolyForm%20NC%201.0-blue)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue)](https://www.python.org)

</div>

---

14 structured [MCP](https://modelcontextprotocol.io) tools for loading models, inspecting blocks, tweaking parameters, running simulations, and capturing figures as images. Every operation is a typed tool call with validated inputs — no arbitrary code execution.

## Why this over a general MATLAB MCP server?

General-purpose MATLAB servers pass arbitrary code strings to `eval()`. That works until the AI hallucinates a function name, forgets a semicolon, or writes a `plot()` call that blocks forever. This server exposes Simulink operations as discrete, validated tools — the AI picks the right tool and fills in typed parameters instead of generating free-text MATLAB code.

## Install

### 1. MATLAB Engine for Python

The MATLAB Engine ships with every MATLAB installation:

```bash
cd <MATLAB_ROOT>/extern/engines/python
pip install .
```

`<MATLAB_ROOT>` is typically:
- **macOS:** `/Applications/MATLAB_R2024b.app`
- **Linux:** `/usr/local/MATLAB/R2024b`
- **Windows:** `C:\Program Files\MATLAB\R2024b`

### 2. simulink-mcp

```bash
pip install simulink-mcp
```

Or from source:

```bash
git clone https://github.com/sohumsuthar/simulink-mcp.git
cd simulink-mcp
pip install .
```

### 3. Verify

```bash
python -c "import matlab.engine; print('OK')"
```

## Configuration

### Claude Code

```bash
claude mcp add simulink -- python -m simulink_mcp
```

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "simulink": {
      "command": "python",
      "args": ["-m", "simulink_mcp"],
      "env": {
        "SIMULINK_MCP_WORKDIR": "/path/to/your/models"
      }
    }
  }
}
```

Then ask Claude to load a model and it'll take it from there.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SIMULINK_MCP_WORKDIR` | `~` | MATLAB working directory on startup |

## Tools

| Tool | What it does |
|------|-------------|
| `load_model` | Load a `.slx` model and list top-level blocks |
| `close_model` | Close a model (with optional save) |
| `create_model` | Create a new blank Simulink model |
| `save_model` | Save a model to disk |
| `list_blocks` | List blocks with configurable depth and type filtering |
| `get_block_params` | Read all dialog parameters of any block |
| `get_model_config` | Read solver, timing, and logging configuration |
| `set_block_param` | Set any block parameter via `set_param()` |
| `set_model_config` | Set model-level config (solver, stop time, etc.) |
| `add_block` | Add blocks from the Simulink library |
| `connect_blocks` | Wire block ports together with auto-routing |
| `delete_block` | Remove a block and its connected lines |
| `simulate` | Run a simulation and return figures as PNG |
| `get_simulation_data` | Extract signal data from simulation results |

## Architecture

```
Claude  <--stdio/MCP-->  simulink_mcp  <--Engine API-->  MATLAB + Simulink
                              |
                           app.py
                              |
                +------+------+------+---------+
                |      |      |      |         |
            model    inspect  modify  simulate
            (4)      (3)      (5)     (2)
```

- **Lazy engine startup** — MATLAB starts on first tool call, not server launch. MCP handshake finishes in ~0.5s; MATLAB boots in the background (~15-20s).
- **Stdout isolation** — Every MATLAB eval captures stdout/stderr to StringIO. Without this, MATLAB chatter corrupts the JSON-RPC stdio transport.
- **Persistent session** — The engine survives across tool calls. `simulate()` stores `simOut` in the workspace so `get_simulation_data()` can pull from it later.
- **Figure capture** — After simulation, open MATLAB figures are exported as PNG, base64-encoded, and returned inline. Figures are closed after capture to prevent accumulation.

## Compatibility

| MATLAB | Python | `matlabengine` on PyPI |
|--------|--------|------------------------|
| R2024a | 3.9 - 3.11 | `24.1.x` |
| R2024b | 3.9 - 3.12 | `24.2.x` |
| R2025a | 3.9 - 3.12 | `25.1.x` |
| R2025b | 3.9 - 3.12 | `25.2.x` |

Python 3.13 is not yet supported by any MATLAB release. The Engine API has been stable across all listed versions — no code changes needed when upgrading MATLAB.

## Troubleshooting

**Server times out on startup**
`import matlab.engine` is deferred to first tool call by design. If it appears at module level, move it inside the function.

**MATLAB engine crashes**
Restart the MCP server. MATLAB sessions can die on invalid Simulink operations.

**PID block "Failed to evaluate mask initialization commands"**
Common on R2024a when `InitialConditionForIntegrator` or `InitialConditionForFilter` falls outside saturation limits. Set both the limit and IC:
```
set_block_param("model/PID", "LowerSaturationLimit", "0")
set_block_param("model/PID", "InitialConditionForIntegrator", "0")
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[PolyForm Noncommercial 1.0.0](LICENSE) — free for non-commercial use.

## Contact

[sohumsuthar.com/contact](https://sohumsuthar.com/contact)
