from __future__ import annotations

import json
import secrets
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


STATE: dict[str, dict[str, object]] = {}


class MockHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        return

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/approve":
            query = parse_qs(parsed.query)
            user_code = query.get("user_code", [""])[0].upper()
            device_code = query.get("device_code", [""])[0]
            matching_code = device_code
            if user_code:
                matching_code = next(
                    (
                        code
                        for code, record in STATE.items()
                        if str(record.get("user_code", "")).upper() == user_code
                    ),
                    "",
                )
            if matching_code in STATE:
                STATE[matching_code]["approved"] = True
                self._send_html("<h1>SnapTrade device approved</h1><p>You can return to the display.</p>")
            else:
                self._send_html("<h1>Unknown device code</h1>", status=404)
            return

        if parsed.path == "/v1/portfolio":
            self._send_json(
                {
                    "items": [
                        {"name": "Cash", "value": "12382.16", "currency": "USD"},
                        {"name": "Investments", "value": "112000.00", "currency": "USD"},
                    ]
                }
            )
            return

        self._send_json({"error": "not_found"}, status=404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        body = self.rfile.read(int(self.headers.get("Content-Length", "0"))).decode()
        form = parse_qs(body)

        if parsed.path == "/v1/oauth/device_authorization/":
            device_code = secrets.token_urlsafe(24)
            user_code = secrets.token_hex(3).upper()
            STATE[device_code] = {"approved": False, "created_at": time.time(), "user_code": user_code}
            approve_url = f"http://127.0.0.1:8088/approve?user_code={user_code}"
            self._send_json(
                {
                    "device_code": device_code,
                    "user_code": user_code,
                    "verification_uri": "http://127.0.0.1:8088/approve",
                    "verification_uri_complete": approve_url,
                    "expires_in": 900,
                    "interval": 3,
                }
            )
            return

        if parsed.path == "/v1/oauth/token/":
            device_code = form.get("device_code", [""])[0]
            record = STATE.get(device_code)
            if not record:
                self._send_json({"error": "expired_token"}, status=400)
                return
            if time.time() - float(record["created_at"]) > 900:
                self._send_json({"error": "expired_token"}, status=400)
                return
            if not record["approved"]:
                self._send_json({"error": "authorization_pending"}, status=400)
                return
            self._send_json(
                {
                    "access_token": "mock-access-token",
                    "refresh_token": "mock-refresh-token",
                    "expires_in": 3600,
                    "token_type": "Bearer",
                    "scope": "accounts:read holdings:read",
                }
            )
            return

        if parsed.path == "/v1/oauth/revoke_token/":
            self._send_json({"revoked": True})
            return

        self._send_json({"error": "not_found"}, status=404)

    def _send_json(self, payload: dict, status: int = 200) -> None:
        raw = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _send_html(self, html: str, status: int = 200) -> None:
        raw = html.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


def run(host: str = "127.0.0.1", port: int = 8088) -> None:
    ThreadingHTTPServer((host, port), MockHandler).serve_forever()


if __name__ == "__main__":
    run()
