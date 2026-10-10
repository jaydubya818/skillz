"""Loopback-only ephemeral prototype with a random session capability; no deployment."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
from .application import Application
from .catalog import build_catalog
from .governance import GovernedRegistry
from .manifest import ValidationError

WEB = Path(__file__).parent / 'web'

class PrototypeServer(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, address, app, token):
        if address[0] != '127.0.0.1':
            raise ValueError('prototype must bind loopback')
        self.app, self.token = app, token
        super().__init__(address, Handler)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _valid_origin(self):
        expected = f'127.0.0.1:{self.server.server_port}'
        return self.headers.get('Host') == expected and self.headers.get('Origin', 'http://' + expected) == 'http://' + expected

    def _send(self, status, body, mime='application/json'):
        encoded = json.dumps(body).encode() if mime == 'application/json' else body
        self.send_response(status)
        self.send_header('Content-Type', mime + '; charset=utf-8')
        self.send_header('Content-Length', str(len(encoded)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        if not self._valid_origin():
            return self._send(403, {'error': 'request denied'})
        files = {'/': ('index.html', 'text/html'), '/app.js': ('app.js', 'application/javascript'), '/styles.css': ('styles.css', 'text/css')}
        if self.path not in files:
            return self._send(404, {'error': 'unavailable'})
        name, mime = files[self.path]
        self._send(200, (WEB / name).read_bytes(), mime)

    def do_POST(self):
        supplied = self.headers.get('X-MySkills-Session', '')
        if self.path != '/api' or not self._valid_origin() or not secrets.compare_digest(supplied, self.server.token):
            return self._send(403, {'error': 'request denied'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 1 <= size <= 65536 or self.headers.get('Content-Type') != 'application/json':
                raise ValidationError('invalid request')
            self.connection.settimeout(5)
            payload = json.loads(self.rfile.read(size))
            if type(payload) is not dict or set(payload) != {'action', 'params'}:
                raise ValidationError('invalid request')
            result = self.server.app.execute(payload['action'], payload['params'])
            self._send(200, {'result': result})
        except (ValidationError, ValueError, TypeError, KeyError):
            self._send(400, {'error': 'Action could not be completed. Refresh the current state and review the request.'})

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    catalog = build_catalog(Path(__file__).parents[1])
    if catalog['failures']:
        raise SystemExit('catalog validation failed')
    app = Application(GovernedRegistry(catalog['skills']))
    token = secrets.token_urlsafe(32)
    server = PrototypeServer(('127.0.0.1', args.port), app, token)
    print(json.dumps({'url': f'http://127.0.0.1:{server.server_port}/#session={token}', 'mode': 'EPHEMERAL_LOCAL_PROTOTYPE'}), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == '__main__':
    main()
