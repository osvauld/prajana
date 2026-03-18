"""
transport.py — Unix socket communication.

One function. Used by every bus node and session.
Sends a JSON command, reads until a complete JSON response arrives.
"""

import json
import socket as socket_mod


def send(sock_path: str, cmd: dict, timeout: float = 10.0) -> dict:
    """
    Send cmd to the Unix socket at sock_path.
    Returns the parsed JSON response, or {'status':'error','message':...} on failure.
    """
    try:
        with socket_mod.socket(socket_mod.AF_UNIX, socket_mod.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect(sock_path)
            s.sendall((json.dumps(cmd) + "\n").encode())
            data = b""
            while True:
                chunk = s.recv(65536)
                if not chunk:
                    break
                data += chunk
                try:
                    return json.loads(data.decode())
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        return {"status": "error", "message": f"socket not found: {sock_path}"}
    except ConnectionRefusedError:
        return {"status": "error", "message": f"connection refused: {sock_path}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    return {"status": "error", "message": "empty response"}
