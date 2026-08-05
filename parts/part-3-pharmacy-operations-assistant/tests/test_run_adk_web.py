from __future__ import annotations

import os
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from scripts import run_adk_web


def write_env_template(project_root: Path) -> None:
    (project_root / ".env.example").write_text(
        "GOOGLE_API_KEY=\nTELEGRAM_PUBLIC_ACCESS=false\n",
        encoding="utf-8",
    )


def test_existing_env_is_preserved_without_prompting(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("GOOGLE_API_KEY=existing\n", encoding="utf-8")
    monkeypatch.setattr(run_adk_web.getpass, "getpass", Mock(side_effect=AssertionError))

    created = run_adk_web.create_env_if_missing(tmp_path)

    assert created is False
    assert env_path.read_text(encoding="utf-8") == "GOOGLE_API_KEY=existing\n"


def test_missing_env_prompts_securely_and_uses_template(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    write_env_template(tmp_path)
    prompt = Mock(return_value="gemini-secret")
    monkeypatch.setattr(run_adk_web.getpass, "getpass", prompt)

    created = run_adk_web.create_env_if_missing(tmp_path)

    assert created is True
    assert (tmp_path / ".env").read_text(encoding="utf-8") == (
        'GOOGLE_API_KEY="gemini-secret"\nTELEGRAM_PUBLIC_ACCESS=false\n'
    )
    prompt.assert_called_once()
    if os.name != "nt":
        assert (tmp_path / ".env").stat().st_mode & 0o777 == 0o600


def test_empty_api_key_does_not_create_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    write_env_template(tmp_path)
    monkeypatch.setattr(run_adk_web.getpass, "getpass", lambda _prompt: "  ")

    with pytest.raises(run_adk_web.LauncherError, match="non-empty"):
        run_adk_web.create_env_if_missing(tmp_path)

    assert not (tmp_path / ".env").exists()


def test_ensure_uv_installs_for_current_user_when_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    installed_uv = tmp_path / "uv"
    discoveries = iter([None, installed_uv])
    run = Mock()
    monkeypatch.setattr(run_adk_web, "discover_uv", lambda: next(discoveries))
    monkeypatch.setattr(run_adk_web.subprocess, "run", run)

    result = run_adk_web.ensure_uv()

    assert result == installed_uv
    run.assert_called_once_with(
        [run_adk_web.sys.executable, "-m", "pip", "install", "--user", "uv"],
        check=True,
    )


def test_install_dependencies_uses_locked_sync(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    run = Mock()
    monkeypatch.setattr(run_adk_web.subprocess, "run", run)

    run_adk_web.install_dependencies(Path("/tools/uv"), tmp_path)

    run.assert_called_once_with(
        ["/tools/uv", "sync", "--locked"],
        cwd=tmp_path,
        check=True,
    )


def test_wait_until_ready_reports_an_early_server_exit() -> None:
    process = SimpleNamespace(poll=lambda: 7)

    with pytest.raises(run_adk_web.LauncherError, match="exit code 7"):
        run_adk_web.wait_until_ready(process, "http://127.0.0.1:8000")


def test_run_adk_web_opens_browser_after_readiness(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    process = Mock()
    process.poll.return_value = 0
    process.wait.return_value = 0
    popen = Mock(return_value=process)
    ready = Mock()
    open_browser = Mock(return_value=True)
    monkeypatch.setattr(run_adk_web.subprocess, "Popen", popen)
    monkeypatch.setattr(run_adk_web, "wait_until_ready", ready)
    monkeypatch.setattr(run_adk_web.webbrowser, "open", open_browser)

    result = run_adk_web.run_adk_web(Path("/tools/uv"), 8123, True, tmp_path)

    assert result == 0
    popen.assert_called_once_with(
        [
            "/tools/uv",
            "run",
            "adk",
            "web",
            "--host",
            "127.0.0.1",
            "--port",
            "8123",
            "--no-reload",
            ".",
        ],
        cwd=tmp_path,
    )
    ready.assert_called_once_with(process, "http://127.0.0.1:8123")
    open_browser.assert_called_once_with("http://127.0.0.1:8123", new=2)


def test_dependency_failure_is_reported_without_command_details(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        run_adk_web.subprocess,
        "run",
        Mock(side_effect=subprocess.CalledProcessError(1, ["uv", "sync"])),
    )

    with pytest.raises(run_adk_web.LauncherError, match="Dependency installation failed"):
        run_adk_web.install_dependencies(Path("uv"), tmp_path)
