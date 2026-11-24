# Security Policy

## Supported versions

Only the latest release receives fixes.

## Reporting a vulnerability

Please do not open a public issue for security problems. Use GitHub's private vulnerability reporting on this repository (Security tab, Report a vulnerability). Include what you found, how to reproduce it, and the version. You can expect an initial reply within a few days.

## Scope notes

The tool reads a local config file, writes one log file inside the repository, and runs `git add`, `git commit` and (in the workflow) `git push`. It uses no secrets beyond the workflow's built-in `GITHUB_TOKEN` and sends no data anywhere else.
