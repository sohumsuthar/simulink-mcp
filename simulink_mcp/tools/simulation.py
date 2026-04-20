"""Simulation — run models and extract signal data."""

import base64
import io
from typing import Union

from mcp.server.fastmcp.utilities.types import Image

from simulink_mcp.app import mcp, matlab_eval, escape_matlab, capture_figures


# structured_output=False because the return type includes
# mcp.server.fastmcp.utilities.types.Image, which FastMCP cannot turn
# into a pydantic output schema (Image isn't a BaseModel and has no
# __get_pydantic_core_schema__). Without this flag, pydantic >= 2.12
# raises PydanticSchemaGenerationError at module import time.
@mcp.tool(structured_output=False)
def simulate(
    model_name: str,
    stop_time: str = "",
    solver: str = "",
    return_figures: bool = True,
) -> list[Union[str, Image]]:
    """Run a Simulink simulation and return results plus any open figures."""
    try:
        name = escape_matlab(model_name)

        if stop_time:
            matlab_eval(
                f"set_param('{name}', 'StopTime', '{escape_matlab(stop_time)}');"
            )
        if solver:
            matlab_eval(
                f"set_param('{name}', 'Solver', '{escape_matlab(solver)}');"
            )

        matlab_eval(
            f"set_param('{name}', 'SaveOutput', 'on', 'SaveTime', 'on');"
        )
        matlab_eval(f"simOut = sim('{name}');")

        # Gather metadata
        logged_vars_raw, _, _ = matlab_eval("strjoin(simOut.who, ', ');", nargout=1)
        logged_vars = str(logged_vars_raw).strip()

        time_info = ""
        try:
            has_tout, _, _ = matlab_eval(
                "any(strcmp(simOut.who, 'tout'));", nargout=1
            )
            if has_tout:
                t_start, _, _ = matlab_eval("simOut.get('tout').Data(1);", nargout=1)
                t_end, _, _ = matlab_eval("simOut.get('tout').Data(end);", nargout=1)
                t_len, _, _ = matlab_eval(
                    "length(simOut.get('tout').Data);", nargout=1
                )
                time_info = (
                    f"Time range: {float(t_start):.4g} - {float(t_end):.4g} s "
                    f"({int(t_len)} samples)"
                )
        except Exception:
            try:
                t_start, _, _ = matlab_eval("simOut.tout(1);", nargout=1)
                t_end, _, _ = matlab_eval("simOut.tout(end);", nargout=1)
                t_len, _, _ = matlab_eval("length(simOut.tout);", nargout=1)
                time_info = (
                    f"Time range: {float(t_start):.4g} - {float(t_end):.4g} s "
                    f"({int(t_len)} samples)"
                )
            except Exception:
                time_info = "Time vector: not available"

        logsout_info = ""
        try:
            has_logsout, _, _ = matlab_eval(
                "any(strcmp(simOut.who, 'logsout'));", nargout=1
            )
            if has_logsout:
                n_signals, _, _ = matlab_eval(
                    "simOut.logsout.numElements;", nargout=1
                )
                logsout_info = f"Logged signals (logsout): {int(n_signals)} element(s)"
                try:
                    names_raw, _, _ = matlab_eval(
                        "strjoin(arrayfun(@(k) simOut.logsout.getElement(k).Name, "
                        "1:simOut.logsout.numElements, 'UniformOutput', false), ', ');",
                        nargout=1,
                    )
                    logsout_info += f"\n  Names: {str(names_raw).strip()}"
                except Exception:
                    pass
        except Exception:
            pass

        status_info = ""
        try:
            status_raw, _, _ = matlab_eval(
                "simOut.SimulationMetadata.ExecutionInfo.StopEvent;", nargout=1
            )
            status_info = f"Stop event: {str(status_raw).strip()}"
        except Exception:
            status_info = "Simulation completed"

        summary_lines = [
            f"Simulation of '{model_name}' finished.",
            status_info,
        ]
        if time_info:
            summary_lines.append(time_info)
        if logged_vars:
            summary_lines.append(f"Logged variables: {logged_vars}")
        if logsout_info:
            summary_lines.append(logsout_info)

        results: list[Union[str, Image]] = ["\n".join(summary_lines)]

        if return_figures:
            figures = capture_figures(dpi=100, close_after=True)
            for png_bytes, fig_name in figures:
                encoded = base64.b64encode(png_bytes).decode()
                results.append(Image(data=encoded, format="png"))

        return results

    except Exception as e:
        return [f"Error during simulation: {e}"]


@mcp.tool()
def get_simulation_data(variable_name: str, max_points: int = 1000) -> str:
    """Extract specific signal data from the last simulation run (simOut)."""
    try:
        try:
            exists, _, _ = matlab_eval("exist('simOut', 'var');", nargout=1)
            if int(exists) == 0:
                return (
                    "No simulation output found. Run simulate() first to "
                    "populate simOut in the MATLAB workspace."
                )
        except Exception:
            return "Could not check MATLAB workspace - is the engine running?"

        var = escape_matlab(variable_name)
        var_retrieved = False

        try:
            matlab_eval(f"__mcp_data = simOut.get('{var}');")
            var_retrieved = True
        except Exception:
            pass

        if not var_retrieved:
            try:
                matlab_eval(f"__mcp_data = simOut.{variable_name};")
                var_retrieved = True
            except Exception:
                pass

        if not var_retrieved:
            try:
                matlab_eval(
                    f"__mcp_data = simOut.logsout.getElement('{var}').Values;"
                )
                var_retrieved = True
            except Exception:
                return (
                    f"Variable '{variable_name}' not found in simOut. "
                    f"Available variables: check simOut.who or use simulate() first."
                )

        class_raw, _, _ = matlab_eval("class(__mcp_data);", nargout=1)
        data_class = str(class_raw).strip()

        # --- Dataset ---
        if data_class in (
            "Simulink.SimulationData.Dataset",
            "Simulink.SimulationData.Signal",
        ):
            n_elem, _, _ = matlab_eval("__mcp_data.numElements;", nargout=1)
            lines = [
                f"Variable '{variable_name}' is a {data_class} "
                f"with {int(n_elem)} element(s).",
            ]
            try:
                names_raw, _, _ = matlab_eval(
                    "strjoin(arrayfun(@(k) __mcp_data.getElement(k).Name, "
                    "1:__mcp_data.numElements, 'UniformOutput', false), ', ');",
                    nargout=1,
                )
                lines.append(f"Elements: {str(names_raw).strip()}")
            except Exception:
                pass
            matlab_eval("clear __mcp_data;")
            return "\n".join(lines)

        # --- Timeseries ---
        is_timeseries = (
            data_class == "timeseries" or "timeseries" in data_class.lower()
        )

        if is_timeseries:
            n_points, _, _ = matlab_eval("length(__mcp_data.Time);", nargout=1)
            n_points = int(n_points)
            size_raw, _, _ = matlab_eval(
                "mat2str(size(__mcp_data.Data));", nargout=1
            )

            lines = [
                f"Variable '{variable_name}' - timeseries",
                f"  Points: {n_points}",
                f"  Data size: {str(size_raw).strip()}",
            ]

            if n_points == 0:
                matlab_eval("clear __mcp_data;")
                lines.append("  (empty timeseries)")
                return "\n".join(lines)

            if n_points > max_points:
                matlab_eval(
                    f"__mcp_idx = round(linspace(1, "
                    f"length(__mcp_data.Time), {max_points}));"
                )
                matlab_eval("__mcp_t = __mcp_data.Time(__mcp_idx);")
                matlab_eval("__mcp_d = __mcp_data.Data(__mcp_idx, :);")
                lines.append(
                    f"  (downsampled from {n_points} to {max_points} points)"
                )
                actual_points = max_points
            else:
                matlab_eval("__mcp_t = __mcp_data.Time;")
                matlab_eval("__mcp_d = __mcp_data.Data;")
                actual_points = n_points

            lines.append("")
            lines.append("Time | Value(s)")
            lines.append("-" * 40)

            if actual_points > 25:
                for row_idx in range(1, 11):
                    t_val, _, _ = matlab_eval(f"__mcp_t({row_idx});", nargout=1)
                    d_val, _, _ = matlab_eval(
                        f"mat2str(__mcp_d({row_idx}, :), 6);", nargout=1
                    )
                    lines.append(f"{float(t_val):.6g}  {str(d_val).strip()}")
                lines.append(f"  ... ({actual_points - 20} rows omitted) ...")
                for row_idx in range(actual_points - 9, actual_points + 1):
                    t_val, _, _ = matlab_eval(f"__mcp_t({row_idx});", nargout=1)
                    d_val, _, _ = matlab_eval(
                        f"mat2str(__mcp_d({row_idx}, :), 6);", nargout=1
                    )
                    lines.append(f"{float(t_val):.6g}  {str(d_val).strip()}")
            else:
                for row_idx in range(1, actual_points + 1):
                    t_val, _, _ = matlab_eval(f"__mcp_t({row_idx});", nargout=1)
                    d_val, _, _ = matlab_eval(
                        f"mat2str(__mcp_d({row_idx}, :), 6);", nargout=1
                    )
                    lines.append(f"{float(t_val):.6g}  {str(d_val).strip()}")

            matlab_eval("clear __mcp_data __mcp_t __mcp_d __mcp_idx;")
            return "\n".join(lines)

        # --- Plain numeric array ---
        size_raw, _, _ = matlab_eval("mat2str(size(__mcp_data));", nargout=1)
        numel_raw, _, _ = matlab_eval("numel(__mcp_data);", nargout=1)
        n_elem = int(numel_raw)

        lines = [
            f"Variable '{variable_name}' - {data_class}",
            f"  Size: {str(size_raw).strip()}",
            f"  Elements: {n_elem}",
        ]

        if n_elem == 0:
            matlab_eval("clear __mcp_data;")
            lines.append("  (empty)")
            return "\n".join(lines)

        is_vector = False
        try:
            ndims_raw, _, _ = matlab_eval("ndims(__mcp_data);", nargout=1)
            min_dim, _, _ = matlab_eval("min(size(__mcp_data));", nargout=1)
            if int(ndims_raw) <= 2 and int(min_dim) <= 1:
                is_vector = True
        except Exception:
            pass

        if is_vector and n_elem <= max_points:
            if n_elem > 25:
                lines.append("")
                for idx in range(1, 11):
                    val, _, _ = matlab_eval(f"__mcp_data({idx});", nargout=1)
                    lines.append(f"  [{idx}] {float(val):.6g}")
                lines.append(f"  ... ({n_elem - 20} elements omitted) ...")
                for idx in range(n_elem - 9, n_elem + 1):
                    val, _, _ = matlab_eval(f"__mcp_data({idx});", nargout=1)
                    lines.append(f"  [{idx}] {float(val):.6g}")
            else:
                lines.append("")
                for idx in range(1, n_elem + 1):
                    val, _, _ = matlab_eval(f"__mcp_data({idx});", nargout=1)
                    lines.append(f"  [{idx}] {float(val):.6g}")
        elif is_vector and n_elem > max_points:
            lines.append(
                f"  (vector has {n_elem} elements, showing downsampled)"
            )
            matlab_eval(
                f"__mcp_idx = round(linspace(1, "
                f"numel(__mcp_data), {max_points}));"
            )
            matlab_eval("__mcp_sub = __mcp_data(__mcp_idx);")
            lines.append("")
            for idx in range(1, 11):
                val, _, _ = matlab_eval(f"__mcp_sub({idx});", nargout=1)
                lines.append(f"  [{idx}] {float(val):.6g}")
            lines.append(f"  ... ({max_points - 20} points omitted) ...")
            for idx in range(max_points - 9, max_points + 1):
                val, _, _ = matlab_eval(f"__mcp_sub({idx});", nargout=1)
                lines.append(f"  [{idx}] {float(val):.6g}")
            matlab_eval("clear __mcp_idx __mcp_sub;")
        else:
            lines.append("")
            try:
                preview_raw, _, _ = matlab_eval(
                    "mat2str(__mcp_data(1:min(10,end), 1:min(10,end)), 6);",
                    nargout=1,
                )
                lines.append(
                    f"  Preview (up to 10x10):\n  {str(preview_raw).strip()}"
                )
            except Exception:
                lines.append("  (could not preview matrix data)")

        matlab_eval("clear __mcp_data;")
        return "\n".join(lines)

    except Exception as e:
        try:
            matlab_eval("clear __mcp_data __mcp_t __mcp_d __mcp_idx __mcp_sub;")
        except Exception:
            pass
        return f"Error extracting data: {e}"
