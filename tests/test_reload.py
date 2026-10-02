import os
import time
from pathlib import Path

import pytest
from reload import ConfigChangePoller


def test_a_config_change_replaces_the_process_with_the_restart_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given a poller watching a config file
    config_file = tmp_path / "config.yml"
    config_file.write_text("a: 1")
    command = ["app", "--config-file", str(config_file)]
    poller = ConfigChangePoller(path=str(config_file), command=command)
    replaced_with: list[list[str]] = []

    def fake_execvp(file: str, args: list[str]) -> None:
        replaced_with.append([file, *args[1:]])
        poller.stop()

    monkeypatch.setattr(os, "execvp", fake_execvp)
    monkeypatch.setattr(time, "sleep", lambda seconds: None)

    # When the config file changes and the poller runs
    os.utime(config_file, (1, config_file.stat().st_mtime + 10))
    poller.poll()

    # Then this process is replaced by the restart command, not left running beside it
    assert replaced_with == [command]
