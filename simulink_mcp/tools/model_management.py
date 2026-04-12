"""Model lifecycle — load, close, create, save."""

from simulink_mcp.app import mcp, matlab_eval, escape_matlab, normalize_path


@mcp.tool()
def load_model(model_path: str) -> str:
    """Load a Simulink .slx model and return a summary of its top-level blocks."""
    try:
        path = normalize_path(model_path)

        dir_path = "/".join(path.split("/")[:-1])
        if dir_path:
            matlab_eval(f"addpath('{escape_matlab(dir_path)}');")

        matlab_eval(f"load_system('{escape_matlab(path)}');")

        filename = path.split("/")[-1]
        model_name = filename.rsplit(".", 1)[0] if "." in filename else filename

        result, _, _ = matlab_eval(
            f"strjoin(find_system('{escape_matlab(model_name)}', "
            f"'SearchDepth', 1), newline);",
            nargout=1,
        )

        blocks = [b for b in str(result).splitlines() if b and b != model_name]

        summary = f"Loaded model: {model_name}\n"
        if blocks:
            summary += f"Top-level blocks ({len(blocks)}):\n"
            for b in blocks:
                summary += f"  - {b}\n"
        else:
            summary += "No top-level blocks found.\n"

        return summary.strip()

    except Exception as e:
        return f"Error loading model: {e}"


@mcp.tool()
def close_model(model_name: str, save: bool = False) -> str:
    """Close a loaded Simulink model, optionally saving it first."""
    try:
        name = escape_matlab(model_name)
        if save:
            matlab_eval(f"save_system('{name}');")
            matlab_eval(f"close_system('{name}');")
            return f"Model '{model_name}' saved and closed."
        else:
            matlab_eval(f"close_system('{name}', 0);")
            return f"Model '{model_name}' closed without saving."

    except Exception as e:
        return f"Error closing model: {e}"


@mcp.tool()
def create_model(model_name: str, model_path: str = "") -> str:
    """Create a new blank Simulink model and save it."""
    try:
        name = escape_matlab(model_name)
        matlab_eval(f"new_system('{name}');")

        if model_path:
            path = normalize_path(model_path)
            if not path.endswith(".slx"):
                path = f"{path}/{model_name}.slx"
            matlab_eval(f"save_system('{name}', '{escape_matlab(path)}');")
            return f"Created and saved model '{model_name}' at {path}."
        else:
            matlab_eval(f"save_system('{name}');")
            return f"Created and saved model '{model_name}' in current MATLAB directory."

    except Exception as e:
        return f"Error creating model: {e}"


@mcp.tool()
def save_model(model_name: str, file_path: str = "") -> str:
    """Save a currently loaded Simulink model, optionally to a specific path."""
    try:
        name = escape_matlab(model_name)
        if file_path:
            path = escape_matlab(normalize_path(file_path))
            matlab_eval(f"save_system('{name}', '{path}');")
            return f"Model '{model_name}' saved to {file_path}."
        else:
            matlab_eval(f"save_system('{name}');")
            return f"Model '{model_name}' saved."

    except Exception as e:
        return f"Error saving model: {e}"
