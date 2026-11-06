# Design

Status: **proposed** (2026-11-06). Decisions already made by MH are marked *decided*; the rest
is a proposal for the first v0.1 session to confirm or change. Open questions are collected at
the end. Facts marked *verified* were checked on the development machine (Fedora 44, Python
3.12, i7-9750H 6c/12t, no GPU use) on 2026-11-06; the rest are to verify.

## Goal

Speech-to-text for typing into terminals (Claude Code, shells, editors) and other apps, run
entirely on the local machine. It replaces cloud dictation (for example Claude Code's `/voice`,
which sends audio to a server and needs an account flag) with a small CLI that a key bind
can pipe anywhere.

## Scope

*Decided:*

- **One job:** record one utterance, transcribe it, print the text to stdout, exit.
- **Compositor-blind.** No typing, clipboard, paste, hotkey grabbing or window-system code.
  The caller's key bind pipes stdout to `wl-copy`, `wtype`, `xdotool type`, `clip.exe` and so
  on. (The author's own key binds live in their dotfiles, not here.)
- **No transcript log.** Text exists only on stdout.
- **An independent package** that depends on pywhispercpp, not an extra or example inside it.

Out of scope for v0.1: continuous or "assistant" dictation, a resident daemon, GPU builds,
non-CPU backends, a waybar/tray indicator, desktop notifications (the caller can wrap the
command; see open question 4).

## Command-line interface

```
pywhisper-dictation [--model NAME] [--language CODE] [--prompt TEXT]
                    [--max-duration SEC] [--silence MS] [--vad-level 0-3]
                    [--device DEV] [--loglevel LEVEL]
pywhisper-dictation --stop
pywhisper-dictation --list-devices
```

- **Default run:** start recording at once, wait for speech, stop after `--silence` ms of
  trailing silence (proposed default 1200 ms), after `--max-duration` seconds (proposed 60), or
  on `--stop`; then transcribe and print.
- **`--stop`** (*decided:* a second invocation must be able to stop a running one): reads the
  pidfile, sends the running process a signal, exits 0. The running process stops recording
  and **still transcribes** what it has (push-to-talk "release"). Cancelling without output
  is open question 2.
- **`--list-devices`:** input devices from `sounddevice.query_devices()`, one per line (for
  `--device`).
- **Settings precedence:** flags, then environment variables (`PYWHISPER_DICTATION_MODEL`,
  `..._LANGUAGE`, `..._DEVICE`, `..._PROMPT`), then defaults. A config file is open question 6.
- argparse with the shared `HelpFormatter` (Rich + defaults) and `--loglevel`, per
  [CONTRIBUTING.md](../CONTRIBUTING.md).

### Output contract

stdout is the interface; a key bind pastes whatever appears there, so it must never carry
anything but the transcript.

- Exactly one line: the segments joined with single spaces, leading/trailing whitespace
  stripped, then `\n`. (Open question 5: keep or drop the newline; `wtype` would type it.)
- All logs, progress bars (pywhispercpp's tqdm download bar) and whisper.cpp's own C-level
  logging go to stderr or nowhere. **To verify:** whisper.cpp writes from C, below Python's
  `sys.stdout`; pywhispercpp's `redirect_whispercpp_logs_to` parameter controls it. A test
  must run the real CLI with stdout captured and assert it holds only the transcript.
- Whisper's non-speech markers (`[BLANK_AUDIO]`, `(music)` and similar) are dropped.
- Exit status: 0 with a transcript; 1 on errors (`sys.exit("pywhisper-dictation: ...")`);
  2 on usage errors (argparse). No speech at all: open question 1.

### Single instance and the pidfile

- Pidfile at `$XDG_RUNTIME_DIR/pywhisper-dictation.pid` (fallback: the platformdirs runtime
  dir). Taken with an exclusive `fcntl.flock` for the process lifetime, so a stale file from a
  crash is harmless (the lock is gone) and a second recording run fails fast with "already
  recording".
- `--stop` reads the pid, checks the lock is held (so it never signals an unrelated process
  that reused the pid), and sends `SIGUSR1`. `SIGINT`/`SIGTERM` keep their usual meaning.
- A key bind can then be one key for start (`pywhisper-dictation | wl-copy`) and one for stop,
  or one toggle key in the caller's script: `pywhisper-dictation --stop || pywhisper-dictation
  | ...` (`--stop` exits 1 when nothing is running).

## Audio capture

- **sounddevice** (PortAudio bindings; the Linux wheel is pure Python and loads the system
  `libportaudio`, *verified* 0.5.6 with PortAudio 19.7.0, default input device found). One
  code path for Fedora, other distros and WSL2.
- `sounddevice.RawInputStream` at **16 kHz, mono, int16**, blocks of **30 ms (480 samples)**:
  whisper.cpp wants 16 kHz mono, and webrtcvad takes 10/20/30 ms int16 frames at 16 kHz.
  If a device refuses 16 kHz, fall back to its default rate and resample (to verify on
  real hardware; PipeWire's ALSA plugin normally resamples for us).
- The callback only copies frames into a `queue.Queue`; VAD and buffering run on the main
  thread. Nothing blocking in the callback.
- **Latency trick:** start the stream first and load the model on a worker thread in parallel,
  so model load time overlaps with speaking. To measure in the benchmark.
- **WSL2 (to verify):** PortAudio talks ALSA; under WSLg, ALSA reaches the PulseAudio server
  only through the ALSA pulse plugin (`libasound2-plugins` on Debian/Ubuntu). Document it in
  the README once tested.
- Optional fallback to an external recorder (`pw-record`, `arecord`) only if a platform turns
  out not to work with PortAudio. Not in v0.1.

## End of speech

- **webrtcvad-wheels** (maintained fork of `webrtcvad` with prebuilt wheels for CPython
  3.10-3.14; plain `webrtcvad` is sdist-only), *verified* it imports.
- A small state machine over 30 ms frames, pure and unit-tested with synthetic frames:
  - `waiting`: no speech yet. Keep a short pre-roll ring buffer (~300 ms) so the first
    syllable is not cut. Give up after a lead-in timeout (proposed 8 s) with no speech.
  - `speaking`: speech started once a window of frames is mostly voiced (for example 6 of 10).
  - `trailing`: after `--silence` ms of unvoiced frames, stop.
  - `--stop`, `--max-duration`, `SIGINT` end any state.
- Aggressiveness `--vad-level` 0-3 (webrtcvad's modes), proposed default 2.

## Transcription

- **Engine:** pywhispercpp **1.5.1**, pinned exactly (*decided*). Prebuilt manylinux wheels
  for CPython 3.9-3.15 (~4.7 MB) bundle whisper.cpp 1.8.5, ggml and libgomp, CPU backend.
  Runtime deps: numpy, requests, tqdm, platformdirs. Not Fedora's `python3-pywhispercpp`
  (1.4.0, distro-only) and not the `whisper-cpp` package (libraries, no CLI).
- `Model(model, models_dir=..., redirect_whispercpp_logs_to=None|stderr, n_threads=...)`, then
  `model.transcribe(float32_array, language=..., initial_prompt=...)` (*verified*
  signatures; the numpy input path is to verify: float32 in [-1, 1] at 16 kHz).
- `n_threads`: proposed default = physical cores (6 here), to tune in the benchmark.
- `initial_prompt` (`--prompt`): biases decoding toward vocabulary such as "Hyprland, chezmoi,
  pywhispercpp, Claude Code". To evaluate in the benchmark.
- Language: proposed default `en` with the English-only `.en` models (better and faster for
  English); `--language auto` with a multilingual model as the opt-in.

## Models

- whisper.cpp ggml models from Hugging Face (`ggerganov/whisper.cpp`). pywhispercpp knows 33
  names (`tiny.en` ... `large-v3-turbo-q8_0`, *verified*).
- Location: pywhispercpp's default is `platformdirs.user_data_dir("pywhispercpp")/models`, i.e.
  `~/.local/share/pywhispercpp/models` (*verified*). Proposed: keep it, so models are shared
  with other pywhispercpp users; `--models-dir`/env override only if needed.
- **Download integrity (finding, *verified* in pywhispercpp 1.5.1 `utils.download_model`):**
  it fetches from the repository's `main` branch, does not check the HTTP status (an error
  page would be saved as the model file), keeps no checksum, and returns `None` for an
  unknown name. Proposed: our own small downloader that pins a Hugging Face revision, checks
  `raise_for_status`, streams to a temp file, verifies a SHA-256 from a table in this repo
  for the models we support, and renames into place. Open question 3.
- **Default model** (*decided*): chosen by the v0.1 benchmark; start with `base.en`.
- **Benchmark** (*decided* as a v0.1 task) on the development CPU:
  - models: `tiny.en`, `base.en`, `small.en` (plus their `q5_1` and `q8_0` variants) and
    `large-v3-turbo-q5_0`;
  - latency: model load time and transcription time for ~10 s utterances, with 4/6/12 threads;
  - accuracy: word error rate on a fixed set of recorded prompts, including technical
    vocabulary (tool names, paths, flags), with and without `initial_prompt`;
  - output: a table in `docs/benchmark.md` and the chosen default. The recordings stay out of
    the repository (the author's voice); the prompt texts and the script go in `tools/`.
- **GPU** (*decided:* later, not v0.1): pywhispercpp built from source with Vulkan or CUDA for
  the 4 GB T1000, measured against compositor jank and VRAM use first.

## Packaging and installation

- `pipx install` from a pinned git tag; one venv holds pywhispercpp and its deps. On the
  author's machine their dotfiles install it through their pinned-pipx installer and add
  `portaudio` to their package map (done 2026-11-06).
- Python **3.11+** (proposed): `tomllib` if a config file comes (open question 6), and every
  dependency ships 3.11-3.14 wheels. CI tests 3.11-3.14.
- CI installs `libportaudio2` so `import sounddevice` works; tests never open a real device.
- Dependencies pinned: pywhispercpp exactly (its bundled whisper.cpp is the engine);
  sounddevice and webrtcvad-wheels with lower bounds; `uv.lock` for development.

## Privacy and supply chain

- No network access after the model download; no telemetry; no transcript log (*decided*).
- Runtime dependencies: pywhispercpp (upstream CI-built wheels), sounddevice, webrtcvad-wheels,
  rich, rich-argparse, plus pywhispercpp's numpy, requests, tqdm, platformdirs. Pin versions;
  review the diff of pywhispercpp's bundled whisper.cpp on upgrades.
- Model files verified by checksum once open question 3 is settled.

## Module layout (proposed)

```
src/pywhisper_dictation/
  cli.py        argparse, settings precedence, main(), exit codes
  audio.py      sounddevice stream -> frame queue; device listing
  vad.py        the end-of-speech state machine (pure; no I/O)
  transcribe.py model loading (worker thread), transcribe, text clean-up
  models.py     model names, download with checksum (if Q3 says so)
  control.py    pidfile lock and --stop signalling
```

## Testing

- pytest, no network, no microphone, no model download in CI.
- `vad.py` with synthetic frame sequences (voiced/unvoiced flags), `control.py` with a child
  process and a temp runtime dir, text clean-up with sample segment lists, the CLI with the
  audio and model layers replaced by fakes.
- An opt-in marker (`-m integration`) for a real-model test on a short generated or recorded
  clip, run by hand on the development machine, plus the stdout-cleanliness test.

## Prior art

Checked on PyPI 2026-11-06 unless marked.

| Project | Engine | Notes |
|---|---|---|
| faster-whisper-dictation 0.2.0 (2026-03, MIT) | faster-whisper or a WhisperLiveKit server | Closest: sounddevice + Silero VAD, toggle/hold modes, X11 and Wayland. Owns the global hotkey (pynput/evdev) and types via ydotool on Wayland; no stdout mode seen in its README. Evaluate briefly before v0.1. |
| whisper-dictation 0.4.3 (2023) | openai-whisper (pinned 2023) | KDE Wayland, daemon + toggle client, clipboard via wl-copy. Stale. |
| whisper-mic 1.4.4 (2024) | openai-whisper + torch | Mic demo; heavy. |
| daobidao | Qwen3-ASR on onnxruntime | X11 and macOS; types the text. |
| voxtype, blurt | | macOS only. |
| wkey | OpenAI cloud API | Not local. |
| pywhisper (2022), dictate (2017) | | A wrapper library and an unrelated project. |
| nerd-dictation (not on PyPI; from memory, verify) | VOSK | `begin`/`end` subcommands and a stdout output mode: the closest control model. |
| whisper.cpp `whisper-stream` (from memory, verify) | whisper.cpp | Continuous streaming example, not a one-shot CLI. |

None is a compositor-blind, stdout-only, whisper.cpp-based one-shot CLI.

pywhispercpp's own examples show the APIs: `pwcpp-recording` (fixed-duration mic capture),
`pwcpp-assistant` (VAD-chunked live transcription with webrtcvad, the model for `vad.py`),
`pwcpp-livestream` (stream URL; needs an undeclared `ffmpeg-python`).

## Open questions

1. **No speech** (lead-in timeout, or only non-speech markers): exit 0 with empty stdout, or a
   distinct non-zero status (proposed: 3) so a key bind's pipe can skip pasting nothing?
2. **Cancel:** add `--cancel` (stop and discard, exit non-zero, no output) next to `--stop`?
3. **Model download:** own downloader with pinned revision + SHA-256 table (proposed), or use
   pywhispercpp's `download_model` and only check the file afterwards?
4. **Feedback while recording:** none from this tool (the caller wraps it with `notify-send`
   or a bar indicator; proposed), or an opt-in `--notify` using `notify-send` when present?
5. **Trailing newline** on stdout: keep (Unix convention; proposed) or drop (`wtype` and
   terminals would submit it)? Callers can strip it with `tr -d '\n'` either way.
6. **Config file** (`$XDG_CONFIG_HOME/pywhisper-dictation/config.toml`) in v0.1, or flags and
   environment variables only (proposed for v0.1)?
7. **Defaults** to confirm: silence 1200 ms, lead-in 8 s, max 60 s, VAD level 2, `en`.
