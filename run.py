import os
import sys
import socket
import uvicorn

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0

if __name__ == "__main__":
    port = 8000
    if is_port_in_use(port):
        print(f"Notice: Port {port} is currently busy, starting on port 8080 instead.")
        port = 8080
    print(f"Starting YPlane Web Admin on http://127.0.0.1:{port}")
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=True)

