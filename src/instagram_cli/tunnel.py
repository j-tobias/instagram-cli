"""Context manager that serves local files via an ngrok public tunnel."""
from __future__ import annotations

import mimetypes
import shutil
import socket
import tempfile
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pyngrok import conf as ngrok_conf
from pyngrok import ngrok


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@contextmanager
def public_tunnel(
    files: list[Path],
    authtoken: str = "",
) -> Generator[callable, None, None]:
    """Serve *files* locally and expose them via an ngrok HTTPS tunnel.

    Yields a ``url_for(path) -> str`` callable that returns the public URL
    for each file.  The tunnel is torn down when the context exits.
    """
    tmp = Path(tempfile.mkdtemp(prefix="instagram_tunnel_"))
    server: uvicorn.Server | None = None
    tunnel = None
    try:
        # Copy files; resolve collisions
        name_map: dict[Path, str] = {}
        used: set[str] = set()
        for p in files:
            name = p.name
            if name in used:
                i = 1
                while f"{p.stem}_{i}{p.suffix}" in used:
                    i += 1
                name = f"{p.stem}_{i}{p.suffix}"
            used.add(name)
            name_map[p] = name
            shutil.copy2(p, tmp / name)

        app = FastAPI(docs_url=None, redoc_url=None)

        @app.api_route("/file/{filename}", methods=["GET", "HEAD"])
        async def serve_file(filename: str) -> FileResponse:
            safe = Path(filename).name
            file_path = tmp / safe
            if not file_path.exists():
                raise HTTPException(status_code=404)
            mime, _ = mimetypes.guess_type(str(file_path))
            return FileResponse(str(file_path), media_type=mime or "application/octet-stream")

        port = _free_port()
        server = uvicorn.Server(uvicorn.Config(app, host="0.0.0.0", port=port, log_level="error"))
        t = threading.Thread(target=server.run, daemon=True)
        t.start()
        for _ in range(40):
            if server.started:
                break
            time.sleep(0.25)

        if authtoken:
            ngrok_conf.get_default().auth_token = authtoken
        tunnel = ngrok.connect(port)

        base = tunnel.public_url

        def url_for(path: Path) -> str:
            return f"{base}/file/{name_map[path]}"

        yield url_for
    finally:
        if tunnel is not None:
            try:
                ngrok.disconnect(tunnel.public_url)
                ngrok.kill()
            except Exception:
                pass
        if server is not None:
            server.should_exit = True
        shutil.rmtree(tmp, ignore_errors=True)
