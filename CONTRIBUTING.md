# Contributing

This is a small project and it should stay small. Bug fixes, documentation corrections and test improvements are the most useful contributions. New features are welcome if they fit in a few dozen lines and need no new dependencies. Open an issue first for anything bigger.

## Development setup

```
python -m venv .venv && source .venv/bin/activate
pip install -e .
python -m unittest discover -s tests -t .
```

Tests use only the standard library and also run under pytest if you have it.

## Guidelines

- Python 3.11+, type hints, PEP 8, small functions.
- Add or update tests for behaviour changes.
- Keep the README, the config example and the code consistent with each other.
- Do not add features meant to hide the automated nature of the commits or to get around GitHub's contribution rules. Those will not be merged.

## Pull requests

Describe what changed and why, and add a line to `CHANGELOG.md` under "Unreleased".
