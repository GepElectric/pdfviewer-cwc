from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Callable


def run_app(
    *,
    command_provider: Callable[[], list[str]] | None = None,
    stop_event=None,
    on_health: Callable[..., None] | None = None,
    start_hidden: bool = False,
    config_dir: Path | None = None,
    data_dir: Path | None = None,
    log_dir: Path | None = None,
) -> None:
    root = tk.Tk()
    root.title("Example Module")
    root.geometry("760x480")
    root.minsize(640, 400)

    status_var = tk.StringVar(value="Idle")

    shell = ttk.Frame(root, padding=16)
    shell.pack(fill="both", expand=True)

    ttk.Label(shell, text="Example Module", font=("Segoe UI Semibold", 18)).pack(anchor="w")
    ttk.Label(
        shell,
        text="Ovo je minimalni Companion module template. Ovdje dodajes svoj stvarni UI i business logiku.",
        wraplength=680,
    ).pack(anchor="w", pady=(8, 12))

    ttk.Label(shell, textvariable=status_var).pack(anchor="w")

    info = tk.Text(shell, height=16, wrap="word")
    info.pack(fill="both", expand=True, pady=(12, 0))
    info.insert(
        "1.0",
        "\n".join(
            [
                "Hosted dirs:",
                f"config_dir = {config_dir}",
                f"data_dir   = {data_dir}",
                f"log_dir    = {log_dir}",
                "",
                "Implement here:",
                "- your UI",
                "- your runtime logic",
                "- your Open Pipe / DB / API code",
            ]
        ),
    )

    closed = {"done": False}

    def _show() -> None:
        root.deiconify()
        root.lift()
        try:
            root.focus_force()
        except Exception:
            pass

    def _close() -> None:
        if closed["done"]:
            return
        closed["done"] = True
        try:
            root.destroy()
        except Exception:
            pass

    def _tick() -> None:
        if closed["done"]:
            return
        if command_provider is not None:
            for cmd in command_provider():
                if cmd == "show":
                    _show()
                elif cmd == "close":
                    _close()
                    return
        if stop_event is not None and stop_event.is_set():
            _close()
            return
        if on_health is not None:
            try:
                on_health(status="running", ui_ready=True, pipe_connected=False, last_error="")
            except Exception:
                pass
        root.after(250, _tick)

    root.protocol("WM_DELETE_WINDOW", _close)
    if start_hidden:
        root.withdraw()
        status_var.set("Hosted / hidden")
    else:
        status_var.set("Standalone")
    _tick()
    root.mainloop()
