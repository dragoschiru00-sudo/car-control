#!/usr/bin/env python3
"""
Local host for the Car Control learning page + Ollama tutor proxy.

Why this exists: GitHub Pages is public HTTPS and cannot reliably call
http://localhost:11434 (mixed content / private network blocking). Run this
instead and the page talks to Ollama through a same-origin /api/chat route.

    python serve.py            # http://localhost:8765
    python serve.py 0.0.0.0    # expose on the LAN

Endpoints:
    GET  /            -> static files
    GET  /api/status  -> {"ok":true,"models":[...]}
    POST /api/chat    -> streams Ollama NDJSON straight back to the browser
"""

import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
OLLAMA = os.environ.get("OLLAMA_HOST_URL", "http://127.0.0.1:11434")
MAX_BODY = 100_000
PER_HOUR = int(os.environ.get("RATE_PER_HOUR", "30"))

# crude but effective abuse cap for a publicly exposed box
_lock = threading.Lock()
_hits = {}      # ip -> [timestamps]
_inflight = {}  # ip -> count


def _allowed(ip):
    now = time.time()
    with _lock:
        if _inflight.get(ip, 0) >= 1:
            return False, "one question at a time"
        hits = [t for t in _hits.get(ip, []) if now - t < 3600]
        if len(hits) >= PER_HOUR:
            return False, "hourly limit reached"
        hits.append(now)
        _hits[ip] = hits
        _inflight[ip] = _inflight.get(ip, 0) + 1
    return True, ""


def _done(ip):
    with _lock:
        _inflight[ip] = max(0, _inflight.get(ip, 1) - 1)



class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def log_message(self, fmt, *args):
        sys.stderr.write("[serve] " + (fmt % args) + "\n")

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/api/status"):
            try:
                with urllib.request.urlopen(OLLAMA + "/api/tags", timeout=4) as r:
                    data = json.loads(r.read().decode("utf-8"))
                models = [m.get("name") for m in data.get("models", [])]
                body = json.dumps({"ok": True, "models": models}).encode()
                self.send_response(200)
            except Exception as e:
                body = json.dumps({"ok": False, "error": str(e)}).encode()
                self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self._cors()
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def do_POST(self):
        if not self.path.startswith("/api/chat"):
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            self.send_error(413, "too large")
            return
        ip = self.client_address[0]
        ok, why = _allowed(ip)
        if not ok:
            body = json.dumps({"error": why}).encode()
            self.send_response(429)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self._cors()
            self.end_headers()
            self.wfile.write(body)
            return
        payload = self.rfile.read(length) if length else b"{}"
        req = urllib.request.Request(
            OLLAMA + "/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            upstream = urllib.request.urlopen(req, timeout=300)
        except urllib.error.HTTPError as e:
            _done(ip)
            body = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self._cors()
            self.end_headers()
            self.wfile.write(body)
            return
        except Exception as e:
            _done(ip)
            body = json.dumps({"error": str(e)}).encode()
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self._cors()
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson")
        self.send_header("Cache-Control", "no-cache")
        self._cors()
        self.end_headers()
        try:
            while True:
                chunk = upstream.read1(4096)
                if not chunk:
                    break
                self.wfile.write(chunk)
                self.wfile.flush()
        except Exception:
            pass
        finally:
            upstream.close()
            _done(ip)


def main():
    port = 8765
    host = "127.0.0.1"
    if len(sys.argv) > 1 and sys.argv[1] not in ("", "-"):
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    print(f"Car Control -> http://{host}:{port}   (Ollama at {OLLAMA})")
    print("Ollama must be running:  ollama serve")
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
