
import socket
import sys

command = (sys.argv[1] if len(sys.argv) > 1 else "SHOW").upper()

try:
    with socket.create_connection(("127.0.0.1", 47854), timeout=1.0) as s:
        s.sendall(command.encode("utf-8"))
except OSError:
    raise SystemExit(1)
