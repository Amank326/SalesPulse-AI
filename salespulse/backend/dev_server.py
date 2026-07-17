import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import hashlib
import datetime

USERS = {}

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def make_token(email):
    raw = f"{email}:{datetime.datetime.now().isoformat()}:dev_secret"
    return hashlib.sha256(raw.encode()).hexdigest()

class Handler(BaseHTTPRequestHandler):
    def _set_json(self, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_json()

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/api/health' or path == '/api/health/':
            self._set_json(200)
            self.wfile.write(json.dumps({'status':'ok','service':'SalesPulse Dev'}).encode())
            return
        if path == '/api/analytics':
            # return demo analytics
            self._set_json(200)
            data = {
                "total_revenue": 9157,
                "total_orders": 20,
                "avg_order": 457.85,
                "cancellation_rate": 25.0,
                "top_product": "Chicken Biryani"
            }
            self.wfile.write(json.dumps(data).encode())
            return
        self._set_json(404)
        self.wfile.write(json.dumps({'detail':'Not found'}).encode())

    def do_POST(self):
        path = urlparse(self.path).path
        # Debug logging: show incoming request details to help debug client issues
        length = int(self.headers.get('content-length', 0))
        raw = self.rfile.read(length) if length else b''
        try:
            body = json.loads(raw.decode()) if raw else {}
        except Exception:
            body = {}
        try:
            client = self.client_address
        except Exception:
            client = ('unknown', 0)
        print(f"\n[DEV_SERVER] POST {path} from {client} content-length={length}")
        print(f"[DEV_SERVER] Headers: {dict(self.headers)}")
        print(f"[DEV_SERVER] Raw body: {raw!r}")
        print(f"[DEV_SERVER] Parsed JSON: {body}")

        if path == '/api/register':
            email = body.get('email')
            name = body.get('name')
            password = body.get('password')
            if not email or not password:
                self._set_json(400)
                self.wfile.write(json.dumps({'detail':'Missing fields'}).encode())
                return
            if email in USERS:
                self._set_json(400)
                self.wfile.write(json.dumps({'detail':'Email already registered'}).encode())
                return
            USERS[email] = {'name': name or '', 'email': email, 'password': hash_password(password), 'token': None}
            self._set_json(200)
            self.wfile.write(json.dumps({'message':'Account created successfully'}).encode())
            return

        if path == '/api/login':
            email = body.get('email')
            password = body.get('password')
            user = USERS.get(email)
            if not user or user.get('password') != hash_password(password):
                self._set_json(401)
                self.wfile.write(json.dumps({'detail':'Invalid credentials'}).encode())
                return
            token = make_token(email)
            user['token'] = token
            self._set_json(200)
            self.wfile.write(json.dumps({'token':token, 'name': user.get('name'), 'email': email}).encode())
            return

        # Default
        self._set_json(404)
        self.wfile.write(json.dumps({'detail':'Not found'}).encode())

def run(port=8000):
    server = HTTPServer(('127.0.0.1', port), Handler)
    print(f"Dev server listening on http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('Shutting down')
        server.server_close()

if __name__ == '__main__':
    run()
