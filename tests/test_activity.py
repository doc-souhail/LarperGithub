import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

from larper_github.activity import (
    COMMIT_TAG, TRAILER, build_entries, commits_for_day, is_active_day,
    is_due, last_entry_date, read_log, write_log,
)
from larper_github.config import Config

NOW = datetime(2026, 11, 24, 9, 17, tzinfo=timezone.utc)  # a Tuesday


class GenerationTests(unittest.TestCase):
    def test_deterministic(self):
        cfg = Config()
        self.assertEqual(build_entries(cfg, NOW), build_entries(cfg, NOW))

    def test_count_within_limit(self):
        cfg = Config(max_commits_per_run=4)
        for offset in range(60):
            day = date.fromordinal(date(2026, 1, 1).toordinal() + offset)
            self.assertTrue(1 <= commits_for_day(cfg, day) <= 4)

    def test_max_one_always_gives_one(self):
        self.assertEqual(len(build_entries(Config(max_commits_per_run=1), NOW)), 1)

    def test_entries_are_labelled(self):
        entry = build_entries(Config(), NOW)[0]
        self.assertIn(COMMIT_TAG, entry.commit_message())
        self.assertIn(TRAILER, entry.commit_message())
        self.assertIn("[LARPergitHub]", entry.log_line("LARPergitHub"))


class ScheduleTests(unittest.TestCase):
    def test_active_weekdays(self):
        cfg = Config(active_weekdays=("tue",))
        self.assertTrue(is_active_day(cfg, date(2026, 11, 24)))
        self.assertFalse(is_active_day(cfg, date(2026, 11, 25)))

    def test_due_when_log_empty(self):
        self.assertTrue(is_due(Config(), [], date(2026, 11, 24)))

    def test_not_due_same_day(self):
        lines = ["2026-11-24T09:17:00Z [x] entry 1/1: a"]
        self.assertFalse(is_due(Config(), lines, date(2026, 11, 24)))

    def test_interval_respected(self):
        lines = ["2026-11-22T09:17:00Z [x] entry 1/1: a"]
        self.assertFalse(is_due(Config(interval_days=3), lines, date(2026, 11, 24)))
        self.assertTrue(is_due(Config(interval_days=2), lines, date(2026, 11, 24)))

    def test_comment_lines_ignored(self):
        self.assertIsNone(last_entry_date(["# header"]))


class LogFileTests(unittest.TestCase):
    def test_trims_to_max_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sub" / "log.txt"
            write_log(path, [f"line {i}" for i in range(30)], max_lines=10)
            lines = read_log(path)
            self.assertEqual(len(lines), 10)
            self.assertEqual(lines[-1], "line 29")

    def test_read_missing_file(self):
        self.assertEqual(read_log(Path("nope.txt")), [])


if __name__ == "__main__":
    unittest.main()
