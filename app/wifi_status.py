from __future__ import annotations

import socket


def is_network_available(host: str = "1.1.1.1", port: int = 53, timeout_seconds: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            return True
    except OSError:
        return False

