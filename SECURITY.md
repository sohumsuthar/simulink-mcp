# Security

## Reporting Vulnerabilities

If you find a security issue, please open a GitHub issue or contact the maintainer directly rather than disclosing publicly.

## MATLAB Injection

This server passes parameters into MATLAB `eval()` and `set_param()` calls. All string inputs are escaped via `escape_matlab()` to prevent injection. If you find a bypass, please report it.
