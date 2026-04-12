"""Model inspection — list blocks, read parameters, read configuration."""

import io

from simulink_mcp.app import mcp, matlab_eval, escape_matlab, get_engine


@mcp.tool()
def list_blocks(model_name: str, search_depth: int = 2, block_type: str = "") -> str:
    """List all blocks in a Simulink model or subsystem.

    Args:
        model_name: Model name or subsystem path (e.g. 'mymodel' or 'mymodel/Subsys').
        search_depth: How many levels deep to search (default 2).
        block_type: Optional Simulink BlockType filter (e.g. 'Gain', 'Sum').
    """
    try:
        eng = get_engine()
        out = io.StringIO()
        err = io.StringIO()

        # find_system is called via feval (parameterized, no injection risk)
        if block_type:
            blocks = eng.find_system(
                model_name, "SearchDepth", search_depth,
                "BlockType", block_type,
                nargout=1, stdout=out, stderr=err,
            )
        else:
            blocks = eng.find_system(
                model_name, "SearchDepth", search_depth,
                nargout=1, stdout=out, stderr=err,
            )

        if not blocks:
            return f"No blocks found in '{model_name}' (depth={search_depth})."

        lines: list[str] = []
        lines.append(f"Blocks in '{model_name}' (depth={search_depth}"
                      + (f", type='{block_type}'" if block_type else "")
                      + f"): {len(blocks)} found\n")

        for path in blocks:
            try:
                bt = eng.get_param(path, "BlockType",
                                   nargout=1, stdout=io.StringIO(), stderr=io.StringIO())
            except Exception:
                bt = "unknown"
            lines.append(f"  {path}  [{bt}]")

        return "\n".join(lines)

    except Exception as e:
        return f"Error listing blocks: {e}"


@mcp.tool()
def get_block_params(block_path: str) -> str:
    """Get all dialog parameters of a Simulink block.

    Args:
        block_path: Full block path (e.g. 'mymodel/Gain1').
    """
    try:
        eng = get_engine()
        escaped = escape_matlab(block_path)

        matlab_eval(
            f"celldisp_out = fieldnames(get_param('{escaped}', 'DialogParameters'));",
        )

        param_names = eng.eval(
            "celldisp_out",
            nargout=1,
            stdout=io.StringIO(),
            stderr=io.StringIO(),
        )

        if not param_names:
            return f"No dialog parameters found for '{block_path}'."

        lines: list[str] = []
        lines.append(f"Dialog parameters for '{block_path}' ({len(param_names)} params):\n")

        for name in param_names:
            try:
                val = eng.get_param(block_path, name,
                                    nargout=1, stdout=io.StringIO(), stderr=io.StringIO())
                lines.append(f"  {name} = {val}")
            except Exception as ex:
                lines.append(f"  {name} = <error: {ex}>")

        eng.eval("clear celldisp_out;", nargout=0,
                 stdout=io.StringIO(), stderr=io.StringIO())

        return "\n".join(lines)

    except Exception as e:
        return f"Error getting block parameters: {e}"


_MODEL_CONFIG_PARAMS = [
    "Solver",
    "SolverType",
    "StartTime",
    "StopTime",
    "MaxStep",
    "MinStep",
    "InitialStep",
    "AbsTol",
    "RelTol",
    "SaveOutput",
    "SaveState",
    "SaveTime",
    "SignalLogging",
    "SignalLoggingName",
    "SimulationMode",
]


@mcp.tool()
def get_model_config(model_name: str) -> str:
    """Get model-level simulation configuration parameters.

    Args:
        model_name: Name of the loaded Simulink model.
    """
    try:
        eng = get_engine()

        lines: list[str] = [f"Simulation configuration for '{model_name}':\n"]

        for param in _MODEL_CONFIG_PARAMS:
            try:
                val = eng.get_param(model_name, param,
                                    nargout=1, stdout=io.StringIO(), stderr=io.StringIO())
                lines.append(f"  {param}: {val}")
            except Exception as ex:
                lines.append(f"  {param}: <error: {ex}>")

        return "\n".join(lines)

    except Exception as e:
        return f"Error getting model config: {e}"
