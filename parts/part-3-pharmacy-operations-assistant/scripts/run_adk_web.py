#!/usr/bin/env python3
"""Bootstrap dependencies and launch the local ADK Web prototype."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import shutil
import subprocess
import sys
import sysconfig
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from typing import Protocol

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
STARTUP_TIMEOUT_SECONDS = 45.0


class LauncherError(RuntimeError):
    """Raised when the local prototype cannot be prepared or started safely."""


class RunningProcess(Protocol):
    """Small process interface used by the readiness check."""

    def poll(self) -> int | None: ...


def require_supported_python() -> None:
    """Fail early when the interpreter cannot satisfy the project contract."""

    if not (sys.version_info >= (3, 11) and sys.version_info < (3, 15)):
        raise LauncherError("Python 3.11 through 3.14 is required to run this prototype.")


def create_env_if_missing(project_root: Path = PROJECT_ROOT) -> bool:
    """Prompt once for the Gemini key and create a private `.env` from the template."""

    env_path = project_root / ".env"
    if env_path.exists():
        print(f"Using existing configuration at {env_path}.")
        return False

    template_path = project_root / ".env.example"
    if not template_path.is_file():
        raise LauncherError(f"Configuration template is missing: {template_path}")

    api_key = getpass.getpass("Enter your Gemini API key (input is hidden): ").strip()
    if not api_key or "\n" in api_key or "\r" in api_key:
        raise LauncherError("A non-empty, single-line Gemini API key is required.")

    template = template_path.read_text(encoding="utf-8")
    marker = "GOOGLE_API_KEY="
    if marker not in template:
        raise LauncherError(f"{template_path} does not define GOOGLE_API_KEY.")

    content = template.replace(marker, f"GOOGLE_API_KEY={json.dumps(api_key)}", 1)
    try:
        descriptor = os.open(env_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        print(f"Using configuration created concurrently at {env_path}.")
        return False

    with os.fdopen(descriptor, "w", encoding="utf-8") as env_file:
        env_file.write(content)
    print(f"Created private configuration at {env_path}.")
    return True


def _user_uv_path() -> Path:
    executable = "uv.exe" if os.name == "nt" else "uv"
    user_scheme = sysconfig.get_preferred_scheme("user")
    return Path(sysconfig.get_path("scripts", scheme=user_scheme)) / executable


def discover_uv() -> Path | None:
    """Find uv on PATH or in the current Python user's script directory."""

    path_entry = shutil.which("uv")
    if path_entry:
        return Path(path_entry)

    candidates = (_user_uv_path(), Path(sys.executable).resolve().parent / _user_uv_path().name)
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def ensure_uv() -> Path:
    """Return the uv executable, installing its PyPI package for this user if needed."""

    uv_path = discover_uv()
    if uv_path:
        print(f"Using uv at {uv_path}.")
        return uv_path

    print("uv was not found; installing it for the current Python user...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--user", "uv"],
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise LauncherError(
            "uv installation failed. Install it from https://docs.astral.sh/uv/ and retry."
        ) from error

    uv_path = discover_uv()
    if uv_path is None:
        raise LauncherError(
            f"uv was installed but its executable was not found. Add {_user_uv_path().parent} "
            "to PATH and retry."
        )
    print(f"Installed uv at {uv_path}.")
    return uv_path


def install_dependencies(uv_path: Path, project_root: Path = PROJECT_ROOT) -> None:
    """Install exactly the dependencies recorded in the lockfile."""

    print("Installing locked project dependencies...")
    try:
        subprocess.run(
            [str(uv_path), "sync", "--locked"],
            cwd=project_root,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise LauncherError("Dependency installation failed.") from error


def wait_until_ready(
    process: RunningProcess,
    url: str,
    timeout_seconds: float = STARTUP_TIMEOUT_SECONDS,
) -> None:
    """Wait until ADK Web responds or the child process fails."""

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        exit_code = process.poll()
        if exit_code is not None:
            raise LauncherError(f"ADK Web exited before startup (exit code {exit_code}).")
        try:
            with urllib.request.urlopen(url, timeout=1):  # noqa: S310 - fixed loopback URL
                return
        except urllib.error.HTTPError:
            return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.25)
    raise LauncherError(f"ADK Web did not become ready within {timeout_seconds:g} seconds.")


def run_adk_web(
    uv_path: Path,
    port: int,
    open_browser: bool,
    project_root: Path = PROJECT_ROOT,
) -> int:
    """Start ADK Web, open its local UI, and keep it running until stopped."""

    url = f"http://{DEFAULT_HOST}:{port}"
    command = [
        str(uv_path),
        "run",
        "adk",
        "web",
        "--host",
        DEFAULT_HOST,
        "--port",
        str(port),
        "--no-reload",
        ".",
    ]
    print(f"Starting ADK Web at {url} ...")
    try:
        process = subprocess.Popen(command, cwd=project_root)
    except OSError as error:
        raise LauncherError("ADK Web could not be started.") from error

    try:
        wait_until_ready(process, url)
        if open_browser and not webbrowser.open(url, new=2):
            print(f"A browser could not be opened automatically. Open {url} manually.")
        elif open_browser:
            print(f"Opened {url} in your browser.")
        else:
            print(f"ADK Web is ready at {url}.")
        print("Select `app` in ADK Web. Press Ctrl+C here to stop the server.")
        return process.wait()
    except KeyboardInterrupt:
        print("\nStopping ADK Web...")
        return 0
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def parse_args(arguments: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        choices=range(1, 65536),
        metavar="PORT",
        help=f"loopback port for ADK Web (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="start ADK Web without opening the default browser",
    )
    return parser.parse_args(arguments)


def main(arguments: list[str] | None = None) -> int:
    """Prepare the project and run the local ADK Web interface."""

    args = parse_args(arguments)
    try:
        require_supported_python()
        create_env_if_missing()
        uv_path = ensure_uv()
        install_dependencies(uv_path)
        return run_adk_web(uv_path, args.port, not args.no_browser)
    except LauncherError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
