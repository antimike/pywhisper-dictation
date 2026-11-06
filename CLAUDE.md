# pywhisper-dictation

Local push-to-talk dictation CLI: microphone → whisper.cpp (pywhispercpp) → stdout (Python, uv,
pipx). Read [README.md](README.md) for the goal, [docs/design.md](docs/design.md) for the
proposed design and its open questions, and [CONTRIBUTING.md](CONTRIBUTING.md) for the coding
standards, commit and release rules (the source of truth for them in this repo).

- **Public repository.** No secrets, client or employer names, real hostnames or private repo
  names in code, tests or docs. gitleaks runs as a pre-commit hook; on MH's machine also run
  `~/.local/share/chezmoi/tools/public-scan/public-scan` before each commit.
- **Scope is fixed by MH's decisions** (design.md, "Scope"): stdout only, compositor-blind, no
  transcript log. Key binds, `wl-copy`/`wtype` pipes and notifications belong to MH's dotfiles
  (`~/.local/share/chezmoi`); ask for them there with the `ticket` command, never edit that
  repo from here.
- **Never record MH's microphone or download a model without asking** (a download is network
  traffic of hundreds of MB; recording is MH's voice). Tests use fakes; integration tests are
  run by hand with MH.
- Run `just lint` and `just test` fresh before claiming anything passes.
- Confirm with MH before pushing, tagging, creating the GitHub repository, or anything else
  outward-facing.
- Commits written with Claude end with the `Co-Authored-By` trailer (the README's provenance
  note relies on it).

## Beads

Work items are tracked with `bd` (prefix `dic`, embedded mode). `.beads/` is gitignored: this
repo is public, and bead notes are working notes. Settings: `dolt.auto-commit batch`, `no-push`,
`no-git-ops`. No Dolt remote: never add one pointing at this repo.

- Use `bd ready` / `bd show` / `bd update` / `bd close`; no TODO lists in files.
- **Interim backup**: at session end run `bd dolt commit` and
  `bd export --output .beads/issues.jsonl` (local only).
- Never `bd dolt push` (MH's rule: it stalls; Dolt-side pushes are MH's, by hand).

## Start prompt

> Work in `~/.local/src/pywhisper-dictation`. Read `CLAUDE.md`, `README.md`, `docs/design.md`
> and `CONTRIBUTING.md`. First settle the design's open questions with me and evaluate
> faster-whisper-dictation briefly (design, "Prior art"), then build v0.1 (`bd ready` shows
> what is next): vad, audio, transcribe, control, CLI, then the model benchmark. One commit per
> layer, on a feature branch. Confirm with me before pushing, recording, downloading models or
> creating the GitHub repo.
