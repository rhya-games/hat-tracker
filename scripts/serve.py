#!/usr/bin/env python3
"""Serve public/ on localhost and keep the tracker's progress in progress.json at the repo root.
  python3 scripts/serve.py [port]      (default 8765)
GET /api/progress returns the file ({} if missing); POST /api/progress replaces it (JSON object only, written atomically).
Commit progress.json to keep a history of your progress."""
import json, os, sys, tempfile
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROGRESS = ROOT / 'progress.json'
MAX = 2_000_000

class Handler(SimpleHTTPRequestHandler):
    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code); self.send_header('Content-Type', 'application/json'); self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        if self.path.split('?')[0] != '/api/progress': return super().do_GET()
        try: self._json(200, json.loads(PROGRESS.read_text()) if PROGRESS.exists() else {})
        except (OSError, ValueError): self._json(500, {'error': 'progress.json is unreadable'})

    def do_POST(self):
        if self.path.split('?')[0] != '/api/progress': return self._json(404, {'error': 'not found'})
        n = int(self.headers.get('Content-Length') or 0)
        if n > MAX: return self._json(413, {'error': 'too large'})
        try:
            data = json.loads(self.rfile.read(n))
            if not isinstance(data, dict): raise ValueError
        except ValueError: return self._json(400, {'error': 'expected a JSON object'})
        fd, tmp = tempfile.mkstemp(dir=ROOT, prefix='.progress-', suffix='.tmp')
        with os.fdopen(fd, 'w') as f: json.dump(data, f, indent=1, sort_keys=True); f.write('\n')
        os.replace(tmp, PROGRESS); self._json(200, {'ok': True})

    def end_headers(self):
        if not self.path.startswith('/api/'): self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    srv = ThreadingHTTPServer(('127.0.0.1', port), partial(Handler, directory=str(ROOT / 'public')))
    print(f'http://localhost:{port}/  (progress saved to {PROGRESS})'); srv.serve_forever()
