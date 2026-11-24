# LARPergitHub

A small tool that writes scheduled, clearly labelled entries to a log file in a dedicated repository and commits them with GitHub Actions. It exists to let you see how automated commits show up on a GitHub contribution graph. It is a joke project and an experiment, not a way to represent work you did not do.

## What it does

On a schedule, a GitHub Actions workflow appends one to a few lines to `activity/log.txt` and makes one commit per line. Each commit message contains the tag `[larper-github]` and an `Automated-By: LARPergitHub` trailer, and each log line says it was machine generated. The number of commits per day and the wording of each line are derived from the date, so the same date always produces the same output.

## How it works

1. The workflow in `.github/workflows/activity.yml` runs on a fixed cron time (daily at 09:17 UTC by default) and on manual dispatch.
2. It installs the package and validates the configuration. An invalid configuration fails the run with a readable message.
3. `larper-github` checks that today is an active weekday and that the configured interval has passed since the last log entry. If not, it exits without committing.
4. Otherwise it appends the entries, trims the log to the configured length, and commits each entry separately.
5. The workflow pushes using the built-in `GITHUB_TOKEN`.

The cron expression cannot read the config file. The time of day lives in the workflow; everything else lives in the config.

## Features

- One YAML config file with validation that reports every problem at once.
- Configurable interval, active weekdays, commit limit (1 to 10) and log size.
- Deterministic, plainly worded log entries that describe only the automation itself.
- Least-privilege workflow: `contents: write` on one job, nothing else.
- One dependency (PyYAML) and no network access beyond the git push.

## Requirements

- A GitHub account and a repository you own, used only for this.
- Python 3.11 or newer and Git, for local use. The workflow brings its own.

## Installation

Create a new empty repository on GitHub (for example `activity-log`), then:

```
git clone https://github.com/<you>/larper-github.git activity-log
cd activity-log
git remote set-url origin https://github.com/<you>/activity-log.git
cp config.example.yml config.yml
python -m venv .venv && source .venv/bin/activate
pip install .
python -m unittest discover -s tests -t .
```

The last command is optional and runs the test suite. Edit `config.yml`, then commit and push:

```
git add config.yml && git commit -m "Add config" && git push -u origin main
```

If `config.yml` is missing, the tool falls back to `config.example.yml`.

## GitHub repository setup

1. Open the repository's Settings, Actions, General.
2. Under Workflow permissions, leave the default or select read and write. The workflow requests `contents: write` itself, but an organisation policy can override that.
3. Make sure Actions are enabled for the repository.
4. Decide on visibility. In a public repository the log and commit history are visible to everyone. In a private repository, other people see nothing, and your profile shows the activity only if you enable "Private contributions" in your profile settings, in which case it appears without any detail.

Do not use this in a repository that belongs to someone else, or in a repository that holds real work.

## GitHub Actions configuration

The workflow is ready to use. Things you may want to change:

- **Time of day:** edit the `cron` line in `.github/workflows/activity.yml`. Times are UTC.
- **Which commits count for your profile:** see the author settings below.

Actions and the checkout step are referenced by major version tag. Pin them to commit SHAs if you want stricter supply-chain control.

## Configuration reference

```yaml
project_name: LARPergitHub
schedule:
  interval_days: 1
  active_weekdays: [mon, tue, wed, thu, fri]
  max_commits_per_run: 3
activity_log:
  path: activity/log.txt
  max_lines: 500
author:
  name: github-actions[bot]
  email: 41898282+github-actions[bot]@users.noreply.github.com
```

| Option | Default | Allowed values |
| --- | --- | --- |
| `project_name` | `LARPergitHub` | 1 to 60 characters, single line. Appears in log lines. |
| `schedule.interval_days` | `1` | Integer, 1 to 30. Minimum days between runs that write entries. |
| `schedule.active_weekdays` | `mon` to `fri` | Non-empty list from `mon`, `tue`, `wed`, `thu`, `fri`, `sat`, `sun`. |
| `schedule.max_commits_per_run` | `3` | Integer, 1 to 10. The actual daily number is between 1 and this value. |
| `activity_log.path` | `activity/log.txt` | Relative path inside the repository. No `..`. |
| `activity_log.max_lines` | `500` | Integer, 10 to 100000. Older lines are dropped. |
| `author.name` | `github-actions[bot]` | Non-empty single line. |
| `author.email` | bot noreply address | Must contain `@` and no spaces. |

Unknown options are rejected, which catches typos.

Commits authored by the Actions bot are not linked to your profile, so they will not appear on your graph. To experiment with your own graph, set `author.name` to your name and `author.email` to your GitHub noreply address (Settings, Emails). Your own account is then the author of automated commits, and the messages and log lines still label them as automated.

## Manual execution

On GitHub: Actions tab, select the `activity` workflow, Run workflow. Tick `force` to skip the weekday and interval checks.

Locally, from inside a clone of your activity repository:

```
larper-github --check-config      # validate config only
larper-github --dry-run --force   # show what would be committed
larper-github --force             # write and commit locally
git push
```

Local runs create real commits in the repository you run them in. Do it in the activity repository only.

## Troubleshooting

**The workflow did not run at the expected time.** Scheduled runs are best effort and are often delayed by many minutes, sometimes skipped at busy times. Use manual dispatch to test.

**The run succeeded but no commit appeared.** The day is probably not an active weekday, or the interval has not passed. The log output says which. Use `force` to confirm everything else works.

**"Invalid configuration".** The message lists each problem with the option name. Run `larper-github --check-config` locally.

**Push fails with a permission error.** Check Settings, Actions, General, Workflow permissions, and any organisation policy.

**Commits exist but the graph is empty.** See the limitations below.

**The schedule stopped after a while.** GitHub can disable scheduled workflows in repositories with no recent activity. Re-enable the workflow in the Actions tab.

## Known limitations

- GitHub decides what appears on the contribution graph. Commits count only when the author email belongs to your account, the commits are on the default branch, and the repository is not a fork. The graph can also lag. Nothing here guarantees that any commit will show up, and the tool makes no attempt to work around those rules.
- Scheduled workflows can be late, skipped, or disabled by GitHub after inactivity.
- All commits in a run share one timestamp.
- Time of day cannot be set from the config file because cron lives in the workflow.
- If you change `max_commits_per_run`, the daily count changes, since it is derived from the date.

## Security considerations

- The workflow uses only the built-in `GITHUB_TOKEN`, with `contents: write` on a single job. No secrets are needed or read.
- The tool collects and sends nothing. Its only network activity is the git push.
- The config file is public if the repository is. Use a noreply email address, not your personal one.
- The log path is restricted to the repository directory.
- Report vulnerabilities as described in `SECURITY.md`.

## Responsible use

Use this only in a repository you own, and only to look at how automation appears on GitHub. The entries are labelled as automated and say nothing about development work. Do not use it to suggest experience or output you do not have, for example in a job application. Reviewers and platforms are free to treat automated activity as such.

## License

MIT. See `LICENSE`.

## Contributing

Small fixes and clear bug reports are welcome. See `CONTRIBUTING.md`.
