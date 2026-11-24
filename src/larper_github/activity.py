"""Deterministic activity entry generation and log handling."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from .config import WEEKDAYS, Config

# Every message describes what the automation itself did. None of them
# claim any development work.
MESSAGES = (
    "scheduled run started",
    "schedule evaluated, entry appended",
    "configuration loaded without changes",
    "routine log entry written",
    "heartbeat recorded",
    "log marker added",
    "automated check-in completed",
    "run finished normally",
)

COMMIT_TAG = "[larper-github]"
TRAILER = "Automated-By: LARPergitHub"


@dataclass(frozen=True)
class Entry:
    """One log line, which also becomes one commit."""

    index: int
    total: int
    timestamp: datetime
    message: str

    def log_line(self, project_name: str) -> str:
        stamp = self.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        return f"{stamp} [{project_name}] entry {self.index}/{self.total}: {self.message}"

    def commit_message(self) -> str:
        return (
            f"chore(activity): automated entry {self.index}/{self.total} {COMMIT_TAG}"
            f"\n\n{self.message}\n\n{TRAILER}"
        )


def _digest(*parts: object) -> int:
    data = "|".join(str(p) for p in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(data).digest()[:8], "big")


def is_active_day(config: Config, day: date) -> bool:
    return WEEKDAYS[day.weekday()] in config.active_weekdays


def commits_for_day(config: Config, day: date) -> int:
    """Pick 1..max_commits_per_run, derived only from project name and date."""
    return _digest(config.project_name, day.isoformat()) % config.max_commits_per_run + 1


def last_entry_date(lines: list[str]) -> date | None:
    """Date of the newest log line, or None if the log has no valid entries."""
    for line in reversed(lines):
        try:
            return date.fromisoformat(line[:10])
        except ValueError:
            continue
    return None


def is_due(config: Config, lines: list[str], today: date) -> bool:
    last = last_entry_date(lines)
    return last is None or (today - last).days >= config.interval_days


def build_entries(config: Config, now: datetime) -> list[Entry]:
    day = now.date().isoformat()
    total = commits_for_day(config, now.date())
    return [
        Entry(
            index=i,
            total=total,
            timestamp=now,
            message=MESSAGES[_digest(config.project_name, day, i) % len(MESSAGES)],
        )
        for i in range(1, total + 1)
    ]


def read_log(path: Path) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def write_log(path: Path, lines: list[str], max_lines: int) -> None:
    """Write the log, keeping only the newest max_lines lines."""
    path.parent.mkdir(parents=True, exist_ok=True)
    kept = lines[-max_lines:]
    path.write_text("\n".join(kept) + "\n", encoding="utf-8")
