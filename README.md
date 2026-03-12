# simulink-mcp

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that gives AI assistants direct access to **MATLAB Simulink** - load models, inspect blocks, modify parameters, run simulations, and get figures back as images.

Unlike general-purpose MATLAB MCP servers that only execute arbitrary code, this server provides **14 dedicated Simulink tools** with structured inputs and outputs, making it far more reliable for AI-driven model interaction.

## Features

| Tool | Description |
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
| `simulate` | Run a simulation and return figures as PNG images |
| `get_simulation_data` | Extract signal data from simulation results |

## Requirements

- **MATLAB** with **Simulink** (tested on R2024a/R2024b)
- **Python 3.11** (required by MATLAB Engine for Python on R2024a; check your version's compatibility)
- **MATLAB Engine for Python** installed (`matlabengine` pip package)
- `mcp[cli] >= 1.2.0`

## Installation

### 1. Install MATLAB Engine for Python

```bash
cd "C:\Program Files\MATLAB\R2024a\extern\engines\python"
pip install .
```

Or use the bundled install script (Windows):

```bash
install.bat
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Verify

```bash
python -c "import matlab.engine; print('OK')"
```

## Configuration

### Claude Desktop

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "simulink": {
      "command": "python",
      "args": ["C:/path/to/simulink-mcp/server.py"],
      "env": {
        "SIMULINK_MCP_WORKDIR": "C:/path/to/your/models"
      }
    }
  }
}
```

### Claude Code

```bash
claude mcp add simulink python /path/to/simulink-mcp/server.py
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SIMULINK_MCP_WORKDIR` | User home directory | MATLAB working directory on startup |

## Architecture

```
AI Assistant  <--stdio/MCP-->  server.py  <--MATLAB Engine API-->  MATLAB + Simulink
                                  |
                               app.py (FastMCP instance, engine manager, helpers)
                                  |
                    +-------------+-------------+-------------+
                    |             |             |             |
              model_mgmt    inspection    modification   simulation
              (4 tools)     (3 tools)     (5 tools)     (2 tools)
```

Key design decisions:

- **Lazy engine startup**: MATLAB starts on first tool call, not at server launch. This keeps MCP handshake fast (~0.5s) while MATLAB boots in the background (~15-20s).
- **Stdout isolation**: All `matlab.engine.eval()` calls capture stdout/stderr to `StringIO` objects. This prevents MATLAB output from corrupting the JSON-RPC stdio transport.
- **Persistent session**: The MATLAB engine persists across tool calls, so workspace variables (like `simOut`) survive between `simulate` and `get_simulation_data`.
- **Figure capture**: After simulation, all open MATLAB figures are exported as PNG and returned as base64-encoded images that AI assistants can display inline.

## Usage Examples

Once configured, your AI assistant can:

**Load and inspect a model:**
> "Load the model at C:/models/pid_controller.slx and show me the block structure"

**Modify parameters and simulate:**
> "Set the PID gains to P=10, I=0.5, D=2 and run a 50-second simulation"

**Compare configurations:**
> "Run the simulation with ode45, then switch to ode23s and compare the results"

**Build models from scratch:**
> "Create a new model with a step input, transfer function, and scope"

## Troubleshooting

**Server times out on startup**
- Make sure `import matlab.engine` is NOT at the top level of any tool module. The engine import is intentionally deferred to `app.py:get_engine()`.

**MATLAB engine crashes**
- Call `restart_engine()` or restart the MCP server. MATLAB sessions can crash on invalid Simulink operations.

**PID block "Failed to evaluate mask initialization commands"**
- Common on R2024a when `InitialConditionForIntegrator` or `InitialConditionForFilter` is outside the saturation limits. Fix by setting both the limit and IC simultaneously:
  ```
  set_param('model/PID', 'LowerSaturationLimit', '0', 'InitialConditionForIntegrator', '0')
  ```

## License

MIT
