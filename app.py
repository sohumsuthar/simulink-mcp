"""
Simulink MCP Server - Shared application state.

This module holds the FastMCP instance and MATLAB engine manager.
Tool modules import from here to register their tools.
"""

import io
import os
import sys
import base64
import tempfile
import logging
from contextlib import contextmanager

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("simulink-mcp")

# ---------------------------------------------------------------------------
# FastMCP instance - all tool modules register on this
# ---------------------------------------------------------------------------
mcp = FastMCP(
    name="simulink",
    instructions=(
        "Simulink MCP server. "
        "Provides tools to load, inspect, modify, and simulate Simulink models "
        "via a persistent MATLAB engine session."
    ),
)

# ---------------------------------------------------------------------------
# MATLAB Engine Manager
# ---------------------------------------------------------------------------
_engine = None
_engine_lock = False  # simple re-entrance guard


def get_engine():
    """Return the shared MATLAB engine, starting it if necessary."""
    global _engine
    if _engine is None:
        import matlab.engine

        logger.info("Starting MATLAB engine (this takes ~15-20 s) …")
        _engine = matlab.engine.start_matlab()
        # Set default working directory
        workdir = os.environ.get(
            "SIMULINK_MCP_WORKDIR",
            os.path.expanduser("~"),
        )
        _engine.cd(workdir, nargout=0)
        logger.info("MATLAB engine ready.")
    return _engine


def restart_engine():
    """Kill and restart the MATLAB engine (recovery from crashes)."""
    global _engine
    if _engine is not None:
        try:
            _engine.quit()
        except Exception:
            pass
    _engine = None
    return get_engine()


def engine_is_alive() -> bool:
    """Check whether the current engine session is responsive."""
    if _engine is None:
        return False
    try:
        out = io.StringIO()
        _engine.eval("1;", nargout=0, stdout=out, stderr=io.StringIO())
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Helper: safe eval - captures stdout/stderr, never leaks to real stdout
# ---------------------------------------------------------------------------
def matlab_eval(code: str, nargout: int = 0):
    """
    Evaluate *code* in the MATLAB engine.

    Returns (result, stdout_text, stderr_text).
    *result* is only meaningful when nargout > 0.
    Raises on MATLAB errors.
    """
    eng = get_engine()
    out = io.StringIO()
    err = io.StringIO()
    if nargout == 0:
        eng.eval(code, nargout=0, stdout=out, stderr=err)
        return None, out.getvalue(), err.getvalue()
    else:
        result = eng.eval(code, nargout=nargout, stdout=out, stderr=err)
        return result, out.getvalue(), err.getvalue()


def matlab_feval(func: str, *args, nargout: int = 1):
    """Call a named MATLAB function via feval."""
    eng = get_engine()
    out = io.StringIO()
    err = io.StringIO()
    result = getattr(eng, func)(*args, nargout=nargout, stdout=out, stderr=err)
    return result, out.getvalue(), err.getvalue()


# ---------------------------------------------------------------------------
# Helper: capture all open figures as PNG bytes
# ---------------------------------------------------------------------------
FIGURE_TEMP_DIR = tempfile.mkdtemp(prefix="simulink_mcp_figs_")


def capture_figures(dpi: int = 100, close_after: bool = True) -> list[tuple[bytes, str]]:
    """
    Save every open MATLAB figure to a temp PNG and return a list of
    (png_bytes, figure_name) tuples.
    """
    eng = get_engine()
    out = io.StringIO()
    err = io.StringIO()

    # Get figure handles
    eng.eval("__mcp_figs = findobj('Type','figure');", nargout=0, stdout=out, stderr=err)
    n = int(eng.eval("length(__mcp_figs);", nargout=1, stdout=io.StringIO(), stderr=io.StringIO()))

    figures: list[tuple[bytes, str]] = []
    for i in range(1, n + 1):
        fname = os.path.join(FIGURE_TEMP_DIR, f"fig_{i}.png").replace("\\", "/")
        eng.eval(
            f"print(__mcp_figs({i}), '-dpng', '-r{dpi}', '{fname}');",
            nargout=0,
            stdout=io.StringIO(),
            stderr=io.StringIO(),
        )
        with open(fname, "rb") as f:
            png_bytes = f.read()

        # Get figure name/number for labeling
        fig_name = eng.eval(
            f"num2str(__mcp_figs({i}).Number);",
            nargout=1,
            stdout=io.StringIO(),
            stderr=io.StringIO(),
        )
        figures.append((png_bytes, f"Figure {fig_name}"))

        # Clean up temp file
        try:
            os.remove(fname)
        except OSError:
            pass

    if close_after and n > 0:
        eng.eval("close all;", nargout=0, stdout=io.StringIO(), stderr=io.StringIO())

    eng.eval("clear __mcp_figs;", nargout=0, stdout=io.StringIO(), stderr=io.StringIO())
    return figures


def normalize_path(p: str) -> str:
    """Normalize a Windows path to forward slashes for MATLAB."""
    return p.replace("\\", "/")
