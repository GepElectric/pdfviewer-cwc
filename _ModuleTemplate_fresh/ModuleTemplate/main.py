from __future__ import annotations

import sys
import threading
from pathlib import Path

from example_module.app import run_app
from hosted_runtime import HealthState, ModuleCommandServer, install_shutdown_handlers, parse_module_runtime_args


APP_VERSION = "0.1.0"


def main(argv: list[str] | None = None) -> int:
    _args, runtime = parse_module_runtime_args(argv, default_module_id="example_module")

    config_dir = runtime.config_dir or Path(__file__).resolve().parent
    data_dir = runtime.data_dir or config_dir
    log_dir = runtime.log_dir or config_dir
    config_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    stop_event = threading.Event()
    install_shutdown_handlers(stop_event)

    health = HealthState(runtime.module_id, APP_VERSION)
    health.update(
        status="starting",
        hosted=runtime.hosted,
        host_instance_id=runtime.host_instance_id or "",
        config_dir=str(config_dir),
        data_dir=str(data_dir),
        log_dir=str(log_dir),
    )

    command_queue: list[str] = []
    queue_lock = threading.Lock()
    command_server: ModuleCommandServer | None = None

    def _push_command(cmd: str) -> None:
        with queue_lock:
            command_queue.append(cmd)

    def _pop_commands() -> list[str]:
        with queue_lock:
            items = list(command_queue)
            command_queue.clear()
            return items

    def _handle_control_command(command: str, _payload: dict) -> dict:
        cmd = str(command or "").strip().lower()
        if cmd == "open_main_window":
            _push_command("show")
            return {"ok": True, "command": cmd}
        if cmd == "get_status":
            return health.snapshot() | {"ui_ready": True}
        if cmd == "shutdown":
            stop_event.set()
            _push_command("close")
            return {"ok": True, "command": cmd}
        raise ValueError(f"Unsupported command: {command}")

    if runtime.command_pipe:
        command_server = ModuleCommandServer(runtime.command_pipe, _handle_control_command)
        command_server.start()
        health.update(command_pipe=runtime.command_pipe)

    def _on_health(**fields) -> None:
        health.update(**fields)

    try:
        run_app(
            command_provider=_pop_commands,
            stop_event=stop_event,
            on_health=_on_health,
            start_hidden=runtime.hosted,
            config_dir=config_dir,
            data_dir=data_dir,
            log_dir=log_dir,
        )
    finally:
        health.update(status="stopped")
        if command_server is not None:
            command_server.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
