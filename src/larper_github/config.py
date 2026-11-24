"""Configuration loading and validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
MAX_COMMITS_LIMIT = 10
MAX_INTERVAL_DAYS = 30
BOT_NAME = "github-actions[bot]"
BOT_EMAIL = "41898282+github-actions[bot]@users.noreply.github.com"

DEFAULT_CONFIG_PATH = Path("config.yml")
FALLBACK_CONFIG_PATH = Path("config.example.yml")

_ALLOWED_KEYS: dict[str, set[str]] = {
    "": {"project_name", "schedule", "activity_log", "author"},
    "schedule": {"interval_days", "active_weekdays", "max_commits_per_run"},
    "activity_log": {"path", "max_lines"},
    "author": {"name", "email"},
}


class ConfigError(ValueError):
    """Raised when the configuration file is missing or invalid."""


@dataclass(frozen=True)
class Config:
    project_name: str = "LARPergitHub"
    interval_days: int = 1
    active_weekdays: tuple[str, ...] = ("mon", "tue", "wed", "thu", "fri")
    max_commits_per_run: int = 3
    log_path: str = "activity/log.txt"
    max_log_lines: int = 500
    author_name: str = BOT_NAME
    author_email: str = BOT_EMAIL


def resolve_config_path(explicit: Path | None) -> Path:
    """Return the config file to use: explicit path, config.yml, or the example."""
    if explicit is not None:
        return explicit
    if DEFAULT_CONFIG_PATH.exists():
        return DEFAULT_CONFIG_PATH
    return FALLBACK_CONFIG_PATH


def load_config(path: Path) -> Config:
    """Read and validate a YAML configuration file."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ConfigError(f"Config file not found: {path}") from None
    try:
        raw = yaml.safe_load(text) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path} is not valid YAML: {exc}") from None
    return parse_config(raw)


def parse_config(raw: Any) -> Config:
    """Validate a parsed config mapping. Reports every problem at once."""
    if not isinstance(raw, dict):
        raise ConfigError("Config must be a YAML mapping at the top level.")

    errors: list[str] = []
    sections = {name: _section(raw, name, errors) for name in _ALLOWED_KEYS if name}
    _check_unknown_keys(raw, sections, errors)

    defaults = Config()
    schedule, log, author = sections["schedule"], sections["activity_log"], sections["author"]

    project_name = raw.get("project_name", defaults.project_name)
    if not isinstance(project_name, str) or not 1 <= len(project_name.strip()) <= 60 \
            or "\n" in project_name:
        errors.append("project_name must be a single-line string of 1 to 60 characters.")

    interval = schedule.get("interval_days", defaults.interval_days)
    if not _is_int(interval) or not 1 <= interval <= MAX_INTERVAL_DAYS:
        errors.append(f"schedule.interval_days must be an integer from 1 to {MAX_INTERVAL_DAYS}.")

    weekdays = schedule.get("active_weekdays", list(defaults.active_weekdays))
    if not _valid_weekdays(weekdays):
        errors.append(
            "schedule.active_weekdays must be a non-empty list of unique values from: "
            + ", ".join(WEEKDAYS) + "."
        )

    max_commits = schedule.get("max_commits_per_run", defaults.max_commits_per_run)
    if not _is_int(max_commits) or not 1 <= max_commits <= MAX_COMMITS_LIMIT:
        errors.append(
            f"schedule.max_commits_per_run must be an integer from 1 to {MAX_COMMITS_LIMIT}."
        )

    log_path = log.get("path", defaults.log_path)
    if not _valid_log_path(log_path):
        errors.append("activity_log.path must be a relative path inside the repository.")

    max_lines = log.get("max_lines", defaults.max_log_lines)
    if not _is_int(max_lines) or not 10 <= max_lines <= 100_000:
        errors.append("activity_log.max_lines must be an integer from 10 to 100000.")

    name = author.get("name", defaults.author_name)
    if not isinstance(name, str) or not name.strip() or "\n" in name:
        errors.append("author.name must be a non-empty single-line string.")

    email = author.get("email", defaults.author_email)
    if not isinstance(email, str) or "@" not in email or any(c.isspace() for c in email):
        errors.append("author.email must look like an email address (no spaces).")

    if errors:
        raise ConfigError("Invalid configuration:\n" + "\n".join(f"  - {e}" for e in errors))

    return Config(
        project_name=project_name.strip(),
        interval_days=interval,
        active_weekdays=tuple(weekdays),
        max_commits_per_run=max_commits,
        log_path=log_path,
        max_log_lines=max_lines,
        author_name=name.strip(),
        author_email=email,
    )


def _section(raw: dict[str, Any], name: str, errors: list[str]) -> dict[str, Any]:
    value = raw.get(name, {})
    if value is None:
        return {}
    if not isinstance(value, dict):
        errors.append(f"'{name}' must be a mapping.")
        return {}
    return value


def _check_unknown_keys(
    raw: dict[str, Any], sections: dict[str, dict[str, Any]], errors: list[str]
) -> None:
    for key in raw:
        if key not in _ALLOWED_KEYS[""]:
            errors.append(f"Unknown option '{key}'.")
    for name, values in sections.items():
        for key in values:
            if key not in _ALLOWED_KEYS[name]:
                errors.append(f"Unknown option '{name}.{key}'.")


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _valid_weekdays(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(v, str) and v in WEEKDAYS for v in value)
        and len(set(value)) == len(value)
    )


def _valid_log_path(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts and "\\" not in value
