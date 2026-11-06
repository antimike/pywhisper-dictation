# pywhisper-dictation

Local push-to-talk dictation for the command line: record from the microphone until you stop
talking (or until a second invocation says stop), transcribe with
[whisper.cpp](https://github.com/ggml-org/whisper.cpp) through
[pywhispercpp](https://github.com/absadiki/pywhispercpp), and print the text to stdout.
Nothing else.

```sh
pywhisper-dictation | wl-copy          # speak, pause, and the text is on the clipboard
pywhisper-dictation --stop             # from another key bind: stop the running one now
```

> **Status: design only, pre-alpha.** Nothing here runs yet. The agreed design is in
> [docs/design.md](docs/design.md); v0.1 is tracked in the project's (local) issue tracker.

## Why another one

- **Fully local.** Audio and text never leave the machine. The only network access is the
  one-time model download. No telemetry.
- **Stdout only.** It does not type, paste, grab hotkeys or talk to a compositor. Your key
  bind decides where the text goes (`wl-copy`, `xclip`, `wtype`, `clip.exe`, a file, a
  pipe into another tool), so the same command works on Wayland, X11, a text console and
  WSL2.
- **Small.** whisper.cpp on the CPU through a prebuilt wheel; no PyTorch, no CUDA toolkit,
  no daemon.

The design's "Prior art" section compares it with existing dictation tools.

## Requirements (planned)

- Python 3.11+ and [pipx](https://pipx.pypa.io/).
- PortAudio, the system audio library behind
  [sounddevice](https://python-sounddevice.readthedocs.io/): `portaudio` (Fedora, Arch),
  `libportaudio2` (Debian, Ubuntu, WSL2).
- A microphone that shows up as an ALSA device (PipeWire and PulseAudio provide one through
  their ALSA plugins).

## Install (once released)

```sh
pipx install git+https://github.com/antimike/pywhisper-dictation@vX.Y.Z
```

The first run downloads the selected whisper.cpp model (75-550 MB depending on size).

## Licence

MIT, see [LICENSE.md](LICENSE.md). Written with the help of Claude (Anthropic); commits it
co-wrote carry a `Co-Authored-By` trailer.
