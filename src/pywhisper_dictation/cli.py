"""pywhisper-dictation: record one utterance, transcribe it locally, print it.

Records from the microphone until you stop talking (or until `pywhisper-dictation --stop`),
transcribes with whisper.cpp, and prints the text to stdout and nothing else, so a key bind
can pipe it anywhere:

    pywhisper-dictation | wl-copy

Not implemented yet: see docs/design.md for the planned behaviour.
"""

from __future__ import annotations

import argparse
from logging import getLogger

from rich.logging import RichHandler
from rich_argparse import RawDescriptionRichHelpFormatter

from pywhisper_dictation import __version__

PROG = "pywhisper-dictation"

logger = getLogger("pywhisper_dictation")


class HelpFormatter(argparse.ArgumentDefaultsHelpFormatter, RawDescriptionRichHelpFormatter):
    """Preserve description/epilog whitespace, show defaults, and style with Rich."""


def get_cli_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog=PROG, description=__doc__, formatter_class=HelpFormatter)
    parser.add_argument("--version", action="version", version=f"{PROG} {__version__}")
    parser.add_argument(
        "--loglevel",
        "-l",
        default="INFO",
        type=lambda v: v.strip().upper(),
        help="Logging verbosity (DEBUG, INFO, WARNING, ERROR).",
    )
    return parser.parse_args(argv)


def setup_logger(args: argparse.Namespace) -> None:
    # RichHandler writes to stderr: stdout carries only the transcript.
    logger.addHandler(RichHandler(level=args.loglevel))
    logger.setLevel(args.loglevel)


def main(argv: list[str] | None = None) -> int:
    args = get_cli_arguments(argv)
    setup_logger(args)
    raise SystemExit(f"{PROG}: not implemented yet (see docs/design.md)")


if __name__ == "__main__":
    raise SystemExit(main())
