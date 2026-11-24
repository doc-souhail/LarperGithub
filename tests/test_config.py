import tempfile
import unittest
from pathlib import Path

from larper_github.config import ConfigError, load_config, parse_config


class ParseConfigTests(unittest.TestCase):
    def test_empty_config_uses_defaults(self):
        cfg = parse_config({})
        self.assertEqual(cfg.interval_days, 1)
        self.assertEqual(cfg.max_commits_per_run, 3)
        self.assertEqual(cfg.active_weekdays, ("mon", "tue", "wed", "thu", "fri"))

    def test_valid_overrides(self):
        cfg = parse_config({
            "project_name": "Demo",
            "schedule": {"interval_days": 2, "active_weekdays": ["sat"], "max_commits_per_run": 5},
            "activity_log": {"path": "logs/a.txt", "max_lines": 50},
            "author": {"name": "Me", "email": "me@users.noreply.github.com"},
        })
        self.assertEqual(cfg.project_name, "Demo")
        self.assertEqual(cfg.active_weekdays, ("sat",))
        self.assertEqual(cfg.log_path, "logs/a.txt")

    def assert_invalid(self, raw, fragment):
        with self.assertRaises(ConfigError) as ctx:
            parse_config(raw)
        self.assertIn(fragment, str(ctx.exception))

    def test_commit_limit_enforced(self):
        self.assert_invalid({"schedule": {"max_commits_per_run": 11}}, "max_commits_per_run")
        self.assert_invalid({"schedule": {"max_commits_per_run": 0}}, "max_commits_per_run")

    def test_bool_is_not_an_int(self):
        self.assert_invalid({"schedule": {"interval_days": True}}, "interval_days")

    def test_bad_weekday(self):
        self.assert_invalid({"schedule": {"active_weekdays": ["monday"]}}, "active_weekdays")
        self.assert_invalid({"schedule": {"active_weekdays": []}}, "active_weekdays")
        self.assert_invalid({"schedule": {"active_weekdays": ["mon", "mon"]}}, "active_weekdays")

    def test_log_path_must_stay_inside_repo(self):
        self.assert_invalid({"activity_log": {"path": "../x.txt"}}, "activity_log.path")
        self.assert_invalid({"activity_log": {"path": "/etc/x"}}, "activity_log.path")

    def test_unknown_keys_rejected(self):
        self.assert_invalid({"frequency": "daily"}, "Unknown option 'frequency'")
        self.assert_invalid({"schedule": {"foo": 1}}, "schedule.foo")

    def test_all_errors_reported_together(self):
        with self.assertRaises(ConfigError) as ctx:
            parse_config({"schedule": {"interval_days": 0, "max_commits_per_run": 99}})
        message = str(ctx.exception)
        self.assertIn("interval_days", message)
        self.assertIn("max_commits_per_run", message)

    def test_top_level_must_be_mapping(self):
        self.assert_invalid(["a"], "mapping")


class LoadConfigTests(unittest.TestCase):
    def test_missing_file(self):
        with self.assertRaises(ConfigError):
            load_config(Path("does-not-exist.yml"))

    def test_invalid_yaml(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "c.yml"
            path.write_text("a: [unclosed", encoding="utf-8")
            with self.assertRaises(ConfigError):
                load_config(path)

    def test_shipped_example_is_valid(self):
        example = Path(__file__).resolve().parent.parent / "config.example.yml"
        self.assertEqual(load_config(example).project_name, "LARPergitHub")


if __name__ == "__main__":
    unittest.main()
