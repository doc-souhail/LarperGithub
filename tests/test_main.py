import os
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from larper_github.config import Config
from larper_github.main import run

NOW = datetime(2026, 11, 24, 9, 17, tzinfo=timezone.utc)  # Tuesday


class RunTests(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        os.chdir(self._tmp.name)
        subprocess.run(["git", "init", "--quiet"], check=True)

    def tearDown(self):
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def commit_count(self):
        result = subprocess.run(["git", "rev-list", "--count", "HEAD"],
                                capture_output=True, text=True)
        return int(result.stdout.strip()) if result.returncode == 0 else 0

    def test_commits_and_author(self):
        cfg = Config(max_commits_per_run=3, author_name="Test Bot", author_email="t@example.com")
        made = run(cfg, NOW, dry_run=False, force=False)
        self.assertTrue(1 <= made <= 3)
        self.assertEqual(self.commit_count(), made)
        out = subprocess.run(["git", "log", "-1", "--format=%an <%ae>%n%B"],
                             capture_output=True, text=True).stdout
        self.assertIn("Test Bot <t@example.com>", out)
        self.assertIn("Automated-By: LARPergitHub", out)

    def test_second_run_same_day_does_nothing(self):
        cfg = Config()
        run(cfg, NOW, dry_run=False, force=False)
        before = self.commit_count()
        self.assertEqual(run(cfg, NOW, dry_run=False, force=False), 0)
        self.assertEqual(self.commit_count(), before)

    def test_inactive_day_skipped_unless_forced(self):
        cfg = Config(active_weekdays=("sat",))
        self.assertEqual(run(cfg, NOW, dry_run=False, force=False), 0)
        self.assertGreaterEqual(run(cfg, NOW, dry_run=False, force=True), 1)

    def test_dry_run_changes_nothing(self):
        self.assertEqual(run(Config(), NOW, dry_run=True, force=False), 0)
        self.assertFalse(Path("activity/log.txt").exists())
        self.assertEqual(self.commit_count(), 0)


if __name__ == "__main__":
    unittest.main()
