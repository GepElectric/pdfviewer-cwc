from __future__ import annotations

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from typing import Callable
from urllib.parse import parse_qs, quote, unquote, urlparse


class _MediaRequestHandler(BaseHTTPRequestHandler):
    resolver: Callable[[str], Path | None] | None = None

    def do_HEAD(self) -> None:  # noqa: N802
        self._handle_request(send_body=False)

    def do_GET(self) -> None:  # noqa: N802
        self._handle_request(send_body=True)

    def _handle_request(self, *, send_body: bool) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self.send_response(200)
            self._write_cors_headers()
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            if send_body:
                self.wfile.write(b"ok")
            return

        if parsed.path == "/browse":
            self._handle_browse(parsed, send_body=send_body)
            return

        if parsed.path not in ("/media", "/pdf"):
            self.send_error(404, "Not found")
            return

        raw_path = parse_qs(parsed.query).get("path", [""])[0]
        local_path = unquote(raw_path)
        resolver = self.resolver
        file_path = resolver(local_path) if resolver is not None else None
        if file_path is None or not file_path.exists() or not file_path.is_file():
            self.send_error(404, "File not found")
            return

        try:
            file_size = file_path.stat().st_size
        except OSError as error:
            self.send_error(500, f"Failed to stat file: {error}")
            return

        mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        range_header = self.headers.get("Range")
        start = 0
        end = file_size - 1
        status_code = 200

        if range_header and range_header.startswith("bytes="):
            byte_range = range_header[6:].split(",", 1)[0]
            start_text, end_text = byte_range.split("-", 1)
            try:
                if start_text:
                    start = int(start_text)
                if end_text:
                    end = int(end_text)
                if start < 0 or end >= file_size or start > end:
                    raise ValueError("Invalid range")
                status_code = 206
            except ValueError:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{file_size}")
                self.end_headers()
                return

        content_length = end - start + 1
        self.send_response(status_code)
        self._write_cors_headers()
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(content_length))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-store")
        if status_code == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
        self.end_headers()

        if not send_body:
            return

        try:
            with file_path.open("rb") as stream:
                stream.seek(start)
                remaining = content_length
                while remaining > 0:
                    chunk = stream.read(min(64 * 1024, remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)
        except OSError as error:
            self.send_error(500, f"Failed to read file: {error}")

    def _handle_browse(self, parsed, *, send_body: bool) -> None:
        query = parse_qs(parsed.query)
        root_value = unquote(query.get("root", [""])[0])
        relative_value = unquote(query.get("path", [""])[0])
        if not root_value:
            self._write_json({"error": "Missing root folder."}, status_code=400, send_body=send_body)
            return

        root_path = self._resolve_and_validate_root(root_value)
        if root_path is None:
            self._write_json({"error": "Root folder not found."}, status_code=404, send_body=send_body)
            return

        current_path = root_path if not relative_value else (root_path / Path(relative_value))
        current_path = current_path.resolve(strict=False)
        if not current_path.exists() or not current_path.is_dir() or not self._is_within_root(root_path, current_path):
            self._write_json({"error": "Requested folder is outside root."}, status_code=403, send_body=send_body)
            return

        root_folders = [
            {"name": child.name, "relativePath": self._relative_path(root_path, child)}
            for child in sorted(root_path.iterdir(), key=lambda entry: entry.name.lower())
            if child.is_dir()
        ]

        folders = [
            {
                "name": child.name,
                "relativePath": self._relative_path(root_path, child),
                "fullPath": str(child),
                "type": "folder",
            }
            for child in sorted(current_path.iterdir(), key=lambda entry: entry.name.lower())
            if child.is_dir()
        ]

        files = [
            {
                "name": child.name,
                "relativePath": self._relative_path(root_path, child),
                "fullPath": str(child),
                "type": "file",
            }
            for child in sorted(current_path.iterdir(), key=lambda entry: entry.name.lower())
            if child.is_file()
        ]

        current_relative = "" if current_path == root_path else self._relative_path(root_path, current_path)
        payload = {
            "rootFolder": str(root_path),
            "currentFolder": str(current_path),
            "currentRelativePath": current_relative,
            "rootFolders": root_folders,
            "folders": folders,
            "files": files,
        }
        self._write_json(payload, send_body=send_body)

    def _write_json(self, payload, *, status_code: int = 200, send_body: bool = True) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self._write_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if send_body:
            self.wfile.write(body)

    def _write_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self._write_cors_headers()
        self.end_headers()

    @staticmethod
    def _resolve_and_validate_root(raw_path: str) -> Path | None:
        try:
            candidate = Path(raw_path).resolve(strict=False)
        except OSError:
            return None
        if not candidate.exists() or not candidate.is_dir():
            return None
        return candidate

    @staticmethod
    def _is_within_root(root_path: Path, candidate: Path) -> bool:
        try:
            candidate.relative_to(root_path)
            return True
        except ValueError:
            return candidate == root_path

    @staticmethod
    def _relative_path(root_path: Path, child_path: Path) -> str:
        return str(child_path.relative_to(root_path))

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


class MediaLocalServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 8765) -> None:
        self.host = host
        self.port = port
        self._server: ThreadingHTTPServer | None = None
        self._thread: Thread | None = None

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def build_media_url(self, local_path: str) -> str:
        return f"{self.base_url}/media?path={quote(local_path)}"

    def build_pdf_url(self, local_path: str) -> str:
        return self.build_media_url(local_path)

    def build_browse_url(self, root_path: str, relative_path: str = "") -> str:
        return f"{self.base_url}/browse?root={quote(root_path)}&path={quote(relative_path)}"

    def start(self) -> None:
        if self._server is not None:
            return

        _MediaRequestHandler.resolver = self._resolve_path
        self._server = ThreadingHTTPServer((self.host, self.port), _MediaRequestHandler)
        self._thread = Thread(target=self._server.serve_forever, daemon=True, name="MediaLocalServer")
        self._thread.start()

    def stop(self) -> None:
        if self._server is None:
            return

        self._server.shutdown()
        self._server.server_close()
        self._server = None
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    @staticmethod
    def _resolve_path(raw_path: str) -> Path | None:
        if not raw_path:
            return None

        candidate = Path(raw_path)
        if candidate.exists():
            return candidate

        return None


PdfLocalServer = MediaLocalServer
