# Contributing

## Setup

```bash
git clone https://github.com/sohumsuthar/simulink-mcp.git
cd simulink-mcp
pip install -e .
```

You'll need MATLAB with Simulink and the [MATLAB Engine for Python](https://www.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html) installed.

## Guidelines

- One fix or feature per PR. Keep changes focused.
- All user inputs flowing into `matlab_eval()` must be escaped with `escape_matlab()` from `app.py`.
- Temp MATLAB workspace variables must use the `__mcp_` prefix and be cleaned up with `clear`.
- Test against a real MATLAB instance. There is no mock test suite.
- Don't add `import matlab.engine` at module level — the import is deferred to `get_engine()` to keep server startup fast.

## Reporting Issues

Open a GitHub issue with your MATLAB version, Python version, the tool call that failed, and the full error message.
