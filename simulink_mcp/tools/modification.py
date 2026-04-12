"""Model modification — set parameters, add/connect/delete blocks."""

import json

from simulink_mcp.app import mcp, matlab_eval, escape_matlab


@mcp.tool()
def set_block_param(block_path: str, param_name: str, param_value: str) -> str:
    """Set a parameter on a Simulink block using set_param().

    Examples:
        set_block_param("mymodel/PID Controller", "P", "10")
        set_block_param("mymodel/Gain", "Gain", "2.5")
        set_block_param("mymodel/Transfer Fcn", "Numerator", "[1 2]")
    """
    try:
        matlab_eval(
            f"set_param('{escape_matlab(block_path)}', "
            f"'{escape_matlab(param_name)}', '{escape_matlab(param_value)}');"
        )
        return f"Set '{param_name}' = '{param_value}' on block '{block_path}'."

    except Exception as e:
        return f"Error setting block param: {e}"


@mcp.tool()
def set_model_config(model_name: str, params: str) -> str:
    """Set model-level configuration parameters.

    `params` is a JSON string of key-value pairs, e.g.:
        {"StopTime": "10", "Solver": "ode45"}

    Common parameters: Solver, StopTime, StartTime, MaxStep, AbsTol,
    RelTol, SaveOutput, SaveState.
    """
    try:
        param_dict = json.loads(params)
    except json.JSONDecodeError as e:
        return f"Invalid JSON in params: {e}"

    name = escape_matlab(model_name)
    set_params: list[str] = []
    errors: list[str] = []

    for key, value in param_dict.items():
        try:
            matlab_eval(
                f"set_param('{name}', '{escape_matlab(key)}', '{escape_matlab(value)}');"
            )
            set_params.append(f"  {key} = '{value}'")
        except Exception as e:
            errors.append(f"  {key}: {e}")

    parts: list[str] = []
    if set_params:
        parts.append(
            f"Set {len(set_params)} parameter(s) on '{model_name}':\n"
            + "\n".join(set_params)
        )
    if errors:
        parts.append(
            f"Failed to set {len(errors)} parameter(s):\n" + "\n".join(errors)
        )

    return "\n".join(parts) if parts else "No parameters provided."


@mcp.tool()
def add_block(source: str, destination: str, params: str = "") -> str:
    """Add a block from the Simulink library to a model.

    `source` is the library path, e.g.:
        "simulink/Continuous/Transfer Fcn"
        "simulink/Math Operations/Gain"
        "simulink/Sources/Step"
        "simulink/Sinks/Scope"

    `destination` is the target path in the model, e.g.: "mymodel/MyGain"

    `params` is an optional JSON string of parameter key-value pairs to set
    on the newly added block.
    """
    try:
        param_dict: dict[str, str] = {}
        if params:
            try:
                param_dict = json.loads(params)
            except json.JSONDecodeError as e:
                return f"Invalid JSON in params: {e}"

        src = escape_matlab(source)
        dst = escape_matlab(destination)

        if param_dict:
            param_args = ""
            for key, value in param_dict.items():
                param_args += f", '{escape_matlab(key)}', '{escape_matlab(value)}'"
            matlab_eval(f"add_block('{src}', '{dst}'{param_args});")
        else:
            matlab_eval(f"add_block('{src}', '{dst}');")

        result = f"Added block '{destination}' from '{source}'."
        if param_dict:
            param_list = ", ".join(f"{k}='{v}'" for k, v in param_dict.items())
            result += f" Parameters set: {param_list}."
        return result

    except Exception as e:
        return f"Error adding block: {e}"


@mcp.tool()
def connect_blocks(
    model_name: str,
    src_block: str,
    src_port: int,
    dst_block: str,
    dst_port: int,
) -> str:
    """Connect two blocks in a Simulink model via add_line().

    Port numbers are 1-indexed.
    `src_block` and `dst_block` are block names relative to the model
    (e.g., "Step" not "mymodel/Step").
    """
    try:
        if src_port < 1:
            return f"Invalid src_port ({src_port}): must be >= 1."
        if dst_port < 1:
            return f"Invalid dst_port ({dst_port}): must be >= 1."

        matlab_eval(
            f"add_line('{escape_matlab(model_name)}', "
            f"'{escape_matlab(src_block)}/{src_port}', "
            f"'{escape_matlab(dst_block)}/{dst_port}', "
            f"'autorouting', 'on');"
        )
        return (
            f"Connected '{src_block}' port {src_port} -> "
            f"'{dst_block}' port {dst_port} in model '{model_name}'."
        )

    except Exception as e:
        return f"Error connecting blocks: {e}"


@mcp.tool()
def delete_block(block_path: str) -> str:
    """Delete a block from a Simulink model.

    Connected lines are removed first via port handle inspection,
    then the block itself is deleted.
    """
    try:
        bp = escape_matlab(block_path)
        matlab_eval(
            f"__mcp_ph = get_param('{bp}', 'PortHandles');\n"
            f"__mcp_allports = [__mcp_ph.Inport, __mcp_ph.Outport, "
            f"__mcp_ph.Enable, __mcp_ph.Trigger, __mcp_ph.LConn, __mcp_ph.RConn];\n"
            f"for __mcp_i = 1:length(__mcp_allports)\n"
            f"    __mcp_ln = get_param(__mcp_allports(__mcp_i), 'Line');\n"
            f"    if __mcp_ln ~= -1\n"
            f"        delete_line(__mcp_ln);\n"
            f"    end\n"
            f"end\n"
            f"clear __mcp_ph __mcp_allports __mcp_i __mcp_ln;"
        )

        matlab_eval(f"delete_block('{bp}');")

        return f"Deleted block '{block_path}' and its connected lines."

    except Exception as e:
        return f"Error deleting block: {e}"
