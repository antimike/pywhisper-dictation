# Contributing

## Setup

Needs [uv](https://docs.astral.sh/uv/), [just](https://github.com/casey/just) and PortAudio
(`portaudio` on Fedora/Arch, `libportaudio2` on Debian/Ubuntu);
[pipx](https://pipx.pypa.io/) for installing the command, gitleaks and pre-commit for the hooks.

```sh
uv sync                 # create .venv with the dev dependencies
pre-commit install      # gitleaks + ruff on every commit
just test               # pytest (no network, no microphone)
just lint               # ruff check + format check (what CI runs)
just fmt                # format and apply safe fixes
just install-dev        # editable pipx install of `pywhisper-dictation`
```

## Coding standards

Tooling enforces what it can (ruff's rule set and line length are in `pyproject.toml`); the rest
is here.

- **Python 3.11+.** `from __future__ import annotations` first in every module; PEP 604 unions
  and built-in generics. Type hints on every function signature.
- **`pathlib.Path`**, not `os.path` string handling.
- **CLI:** argparse only, with the shared `HelpFormatter` in `cli.py`; `--loglevel` always.
- **stdout is the transcript and nothing else.** Data goes to stdout with `print`; diagnostics
  go to stderr through `logging` (`RichHandler`). Anything that could write to stdout
  (whisper.cpp's C logging, progress bars) is redirected. A key bind pastes stdout verbatim, so
  a stray line on stdout is a bug.
- **Stay compositor-blind.** No typing, clipboard, hotkey or window-system code; callers pipe
  stdout where they want it ([design](docs/design.md), "Scope").
- **Local only.** No network access except the explicit model download; no telemetry; never
  write audio or transcripts to disk.
- **Errors:** expected failures end with `sys.exit("pywhisper-dictation: <message>")`
  (lowercase, no trailing period) and a non-zero status; tracebacks are for bugs. Never
  swallow an exception.
- **No hard-coded paths or credentials.** Paths come from XDG variables, platformdirs, the
  environment or arguments.
- **Subprocesses** (if any) with an argument list, `text=True`, and an explicit `check=`.
- **The audio callback stays trivial:** copy the frame into a queue and return. No logging,
  allocation-heavy work or locks there.
- **Comments** say why, not what; docstrings carry the reference documentation.
- **No speculative code:** no flags, hooks or modules without a current caller.

## Tests

- `pytest`, no network, no microphone, no model download. Audio and model layers are replaced
  by fakes; VAD tests feed synthetic frames.
- Tests that need a real model or device carry the `integration` marker and run only on demand
  (`just test -m integration`).
- Never commit audio recordings or model files (`.gitignore` blocks `*.wav`, `*.flac`, `*.bin`).
- A test written for a bug must fail without the fix and pass with it.

## Commits

- [Conventional Commits](https://www.conventionalcommits.org/): `<type>(<scope>): <description>`,
  for example `feat(vad): keep a pre-roll buffer`.
- One logical change per commit; a feature lands layer by layer (vad, audio, transcribe,
  control, CLI), each with its tests.
- Feature branches for anything bigger than a small fix; `main` stays releasable.
- Update `CHANGELOG.md` under `[Unreleased]` in the same commit as a user-visible change, and
  `docs/design.md` when a design decision changes.

## Releases

[Semantic Versioning](https://semver.org/); the CLI flags, the stdout format and the exit
statuses are the public interface. To release: move the `[Unreleased]` entries under the new
version in `CHANGELOG.md`, set `version` in `pyproject.toml`, commit, and tag `vX.Y.Z` on that
commit. Installs pin a tag:
`pipx install git+https://github.com/antimike/pywhisper-dictation@vX.Y.Z`.
