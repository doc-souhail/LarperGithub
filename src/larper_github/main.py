"""Command line entry point."""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .activity import Entry, build_entries, is_active_day, is_due, read_log, write_log
from .config import Config, ConfigError, load_config, resolve_config_path

log = logging.getLogger("larper_github")


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="larper-github",
        description="Append labelled entries to an activity log and commit them.",
    )
    parser.add_argument("--config", type=Path, help="config file (default: config.yml)")
    parser.add_argument("--check-config", action="store_true", help="validate the config and exit")
    parser.add_argument("--dry-run", action="store_true",
                        help="show what would happen, change nothing")
    parser.add_argument("--force", action="store_true",
                        help="ignore the weekday and interval checks")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser.parse_args(argv)


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True, text=True)


def commit_entry(config: Config, entry: Entry, log_path: Path) -> None:
    git("add", "--", str(log_path))
    git(
        "-c", f"user.name={config.author_name}",
        "-c", f"user.email={config.author_email}",
        "commit", "--quiet", "-m", entry.commit_message(),
    )


def run(config: Config, now: datetime, *, dry_run: bool, force: bool) -> int:
    """Generate and commit today's entries. Returns the number of commits made."""
    log_path = Path(config.log_path)
    lines = read_log(log_path)
    today = now.date()

    if not force and not is_active_day(config, today):
        log.info("%s is not an active weekday, nothing to do.", today.strftime("%A"))
        return 0
    if not force and not is_due(config, lines, today):
        log.info("Interval of %d day(s) has not elapsed, nothing to do.", config.interval_days)
        return 0

    entries = build_entries(config, now)
    for entry in entries:
        line = entry.log_line(config.project_name)
        if dry_run:
            log.info("[dry run] would commit: %s", line)
            continue
        lines.append(line)
        write_log(log_path, lines, config.max_log_lines)
        lines = read_log(log_path)
        commit_entry(config, entry, log_path)
        log.info("Committed entry %d/%d", entry.index, entry.total)
    return 0 if dry_run else len(entries)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = parse_args(argv)
    try:
        config_path = resolve_config_path(args.config)
        config = load_config(config_path)
        log.info("Using config: %s", config_path)
        if args.check_config:
            log.info("Configuration is valid.")
            return 0
        run(config, datetime.now(timezone.utc), dry_run=args.dry_run, force=args.force)
    except ConfigError as exc:
        log.error("%s", exc)
        return 2
    except subprocess.CalledProcessError as exc:
        log.error("git failed: %s", (exc.stderr or "").strip() or exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
