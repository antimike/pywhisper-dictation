from __future__ import annotations

import pytest

from pywhisper_dictation import __version__
from pywhisper_dictation.cli import main


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])
    assert exit_info.value.code == 0
    assert capsys.readouterr().out.strip() == f"pywhisper-dictation {__version__}"


def test_unimplemented_run_fails_with_nothing_on_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main([])
    assert exit_info.value.code != 0
    assert capsys.readouterr().out == ""
