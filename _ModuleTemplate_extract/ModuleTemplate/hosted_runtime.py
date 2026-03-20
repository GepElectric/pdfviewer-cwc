from __future__ import annotations

import argparse
import json
import signal
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ModuleRuntimeArgs:
    module_id: str
    config_dir: Path | None
    data_dir: Path | None
    log_dir: Path | None
    command_pipe: str | None
    host_instance_id: str | None
    hosted: bool


def parse_module_runtime_args(argv: list[str] | None = None, *, default_module_id: str) -> tuple[argparse.Namespace, ModuleRuntimeArgs]:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--module-id", default=default_module_id)
    parser.add_argument("--config-dir")
    parser.add_argument("--data-dir")
    parser.add_argument("--log-dir")
    parser.add_argument("--command-pipe")
    parser.add_argument("--host-instance-id")
    parser.add_argument("--hosted", action="store_true")
    args, unknown = parser.parse_known_args(argv)
    args._unknown_args = unknown
    runtime = ModuleRuntimeArgs(
        module_id=str(args.module_id or default_module_id),
        config_dir=Path(args.config_dir).resolve() if args.config_dir else None,
        data_dir=Path(args.data_dir).resolve() if args.data_dir else None,
        log_dir=Path(args.log_dir).resolve() if args.log_dir else None,
        command_pipe=str(args.command_pipe).strip() if args.command_pipe else None,
        host_instance_id=str(args.host_instance_id).strip() if args.host_instance_id else None,
        hosted=bool(args.hosted),
    )
    return args, runtime


class HealthState:
    def __init__(self, module_id: str, version: str = "0.1.0") -> None:
        self._lock = threading.Lock()
        self._state: dict[str, Any] = {
            "module_id": module_id,
            "version": version,
            "status": "starting",
            "started_at": _utc_now(),
            "updated_at": _utc_now(),
            "last_error": "",
            "pipe_connected": False,
        }

    def update(self, **fields: Any) -> None:
        with self._lock:
            self._state.update(fields)
            self._state["updated_at"] = _utc_now()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._state)


class ModuleCommandServer:
    def __init__(self, pipe_name: str, handler: Callable[[str, dict[str, Any]], dict[str, Any] | None]) -> None:
        self.pipe_name = pipe_name
        self.handler = handler
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._loop, daemon=True, name=f"CmdPipe:{self.pipe_name}")
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        try:
            send_module_command(self.pipe_name, "__stop__", timeout_ms=250)
        except Exception:
            pass
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _loop(self) -> None:
        import win32file
        import win32pipe

        while not self._stop_event.is_set():
            pipe = win32pipe.CreateNamedPipe(
                self.pipe_name,
                win32pipe.PIPE_ACCESS_DUPLEX,
                win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                1,
                65536,
                65536,
                0,
                None,
            )
            try:
                win32pipe.ConnectNamedPipe(pipe, None)
                _, raw = win32file.ReadFile(pipe, 65536)
                payload = json.loads(raw.decode("utf-8") or "{}")
                command = str(payload.get("command", "")).strip()
                body = payload.get("payload", {})
                if not isinstance(body, dict):
                    body = {}
                if command == "__stop__":
                    response = {"ok": True}
                else:
                    response = self.handler(command, body) or {"ok": True}
                win32file.WriteFile(pipe, json.dumps(response, ensure_ascii=False).encode("utf-8"))
            except Exception as exc:
                try:
                    win32file.WriteFile(pipe, json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False).encode("utf-8"))
                except Exception:
                    pass
            finally:
                try:
                    win32file.CloseHandle(pipe)
                except Exception:
                    pass


def send_module_command(pipe_name: str, command: str, payload: dict[str, Any] | None = None, timeout_ms: int = 2000) -> dict[str, Any]:
    import win32file
    import win32pipe

    win32pipe.WaitNamedPipe(pipe_name, timeout_ms)
    handle = win32file.CreateFile(
        pipe_name,
        win32file.GENERIC_READ | win32file.GENERIC_WRITE,
        0,
        None,
        win32file.OPEN_EXISTING,
        0,
        None,
    )
    try:
        request = json.dumps(
            {
                "type": "command",
                "request_id": uuid.uuid4().hex[:10],
                "command": command,
                "payload": payload or {},
            },
            ensure_ascii=False,
        ).encode("utf-8")
        win32file.WriteFile(handle, request)
        _, raw = win32file.ReadFile(handle, 65536)
        return json.loads(raw.decode("utf-8") or "{}")
    finally:
        win32file.CloseHandle(handle)


def install_shutdown_handlers(stop_event: threading.Event) -> None:
    def _handle(_signum, _frame):
        stop_event.set()

    for sig_name in ("SIGINT", "SIGTERM", "SIGBREAK"):
        sig = getattr(signal, sig_name, None)
        if sig is None:
            continue
        try:
            signal.signal(sig, _handle)
        except Exception:
            pass
