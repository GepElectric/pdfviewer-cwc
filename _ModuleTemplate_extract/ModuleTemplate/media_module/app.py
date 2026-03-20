from __future__ import annotations

import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable

from media_module.pdf_server import MediaLocalServer


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
    media_server = MediaLocalServer()
    media_server.start()

    root = tk.Tk()
    root.title("Media Companion Module")
    root.geometry("860x560")
    root.minsize(780, 500)

    status_var = tk.StringVar(value="Idle")
    source_var = tk.StringVar(value="")
    server_var = tk.StringVar(value=f"Local media server: {media_server.base_url}")

    shell = ttk.Frame(root, padding=16)
    shell.pack(fill="both", expand=True)

    ttk.Label(shell, text="Media Companion Module", font=("Segoe UI Semibold", 18)).pack(anchor="w")
    ttk.Label(
        shell,
        text="Otvori lokalni media sadrzaj preko localhost servera ili direktni web link u browseru.",
        wraplength=780,
    ).pack(anchor="w", pady=(8, 12))

    ttk.Label(shell, textvariable=status_var).pack(anchor="w")
    ttk.Label(shell, textvariable=server_var).pack(anchor="w", pady=(4, 12))

    entry_row = ttk.Frame(shell)
    entry_row.pack(fill="x")

    source_entry = ttk.Entry(entry_row, textvariable=source_var)
    source_entry.pack(side="left", fill="x", expand=True)

    def _browse_media() -> None:
        selected = filedialog.askopenfilename(
            title="Odaberi media file",
            filetypes=[
                ("Media files", "*.pdf;*.mp4;*.webm;*.ogg;*.mov;*.m4v;*.mkv;*.mp3;*.wav;*.aac;*.m4a;*.flac;*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.webp;*.svg"),
                ("All files", "*.*"),
            ],
        )
        if selected:
            source_var.set(selected)
            status_var.set("Media selected")

    ttk.Button(entry_row, text="Browse", command=_browse_media).pack(side="left", padx=(8, 0))

    button_row = ttk.Frame(shell)
    button_row.pack(fill="x", pady=(12, 12))

    def _normalize_source(raw_value: str) -> tuple[str, str]:
        value = str(raw_value or "").strip()
        if not value:
            return "", ""
        if value.lower().startswith(("http://", "https://")):
            return value, value
        if value.lower().startswith("file:///"):
            local_path = value[8:].replace("/", "\\")
            return media_server.build_media_url(local_path), local_path
        local_path = str(Path(value))
        return media_server.build_media_url(local_path), local_path

    def _open_media() -> None:
        target_url, source_label = _normalize_source(source_var.get())
        if not target_url:
            messagebox.showwarning("Media", "Upisi ili odaberi media putanju/link.")
            return
        webbrowser.open(target_url)
        status_var.set(f"Opened: {source_label or target_url}")

    def _copy_url() -> None:
        target_url, _source_label = _normalize_source(source_var.get())
        if not target_url:
            messagebox.showwarning("Media", "Nema media putanje/linka za copy.")
            return
        root.clipboard_clear()
        root.clipboard_append(target_url)
        status_var.set("Copied viewer URL")

    ttk.Button(button_row, text="Open Media", command=_open_media).pack(side="left")
    ttk.Button(button_row, text="Copy URL", command=_copy_url).pack(side="left", padx=(8, 0))

    info = tk.Text(shell, height=16, wrap="word")
    info.pack(fill="both", expand=True, pady=(12, 0))
    info.insert(
        "1.0",
        "\n".join(
            [
                "Hosted dirs and runtime info:",
                f"config_dir = {config_dir}",
                f"data_dir   = {data_dir}",
                f"log_dir    = {log_dir}",
                f"local_media_server = {media_server.base_url}",
                "",
                "How it works:",
                "- local disk paths are exposed through localhost media server",
                "- http/https links are opened directly",
                "- supports pdf, image, audio and video content",
                "- use Copy URL for the CWC property value",
            ]
        ),
    )
    info.configure(state="disabled")

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
        media_server.stop()
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
