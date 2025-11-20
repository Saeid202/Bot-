from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class Handler(BaseHTTPRequestHandler):
    def _read_json(self):
        length = int(self.headers.get('content-length', 0))
        if length:
            raw = self.rfile.read(length).decode('utf-8')
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return None
        return None

    def _send_json(self, obj, status=200):
        data = json.dumps(obj).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path.endswith('/start'):
            body = self._read_json() or {}
            print('START called with', body)
            self._send_json({'jobId': 'job-local-123'})
            return
        if self.path.endswith('/insert-products'):
            body = self._read_json() or {}
            products = body.get('products') if isinstance(body, dict) else None
            print('INSERT called, received', len(products) if products else 0)
            self._send_json({'ok': True, 'received': len(products) if products else 0})
            return
        if self.path.endswith('/complete'):
            body = self._read_json() or {}
            print('COMPLETE called with', body)
            self._send_json({'ok': True})
            return
        # Unknown path
        self._send_json({'error': 'unknown path'}, status=404)

if __name__ == '__main__':
    port = 3000
    server = HTTPServer(('0.0.0.0', port), Handler)
    print(f'Serving API stub on http://0.0.0.0:{port}/api/scraper')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('Shutting down')
        server.server_close()
