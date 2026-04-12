import json
import socket
import struct
import subprocess
import time
from pathlib import Path

ROOT = Path(r"C:\Users\majko\Documents\PROJECTS\Server Jars\Sloxy")
JAR = ROOT / "Sloxy.jar"
OUT = ROOT / "_runtime_verify_result.txt"


def pack_varint(value: int) -> bytes:
    out = bytearray()
    value &= 0xFFFFFFFF
    while True:
        b = value & 0x7F
        value >>= 7
        if value != 0:
            out.append(b | 0x80)
        else:
            out.append(b)
            break
    return bytes(out)


def read_varint(sock: socket.socket) -> int:
    num = 0
    shift = 0
    while True:
        b = sock.recv(1)
        if not b:
            raise RuntimeError("socket closed while reading varint")
        val = b[0]
        num |= (val & 0x7F) << shift
        if (val & 0x80) == 0:
            return num
        shift += 7
        if shift > 35:
            raise RuntimeError("varint too large")


def recv_exact(sock: socket.socket, n: int) -> bytes:
    data = bytearray()
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise RuntimeError("socket closed early")
        data.extend(chunk)
    return bytes(data)


def ping_version(host: str, port: int) -> str:
    with socket.create_connection((host, port), timeout=5) as s:
        s.settimeout(5)
        hb = host.encode("utf-8")
        hs_payload = b"".join(
            [
                pack_varint(0x00),
                pack_varint(769),
                pack_varint(len(hb)),
                hb,
                struct.pack(">H", port),
                pack_varint(1),
            ]
        )
        s.sendall(pack_varint(len(hs_payload)) + hs_payload)
        s.sendall(pack_varint(1) + pack_varint(0x00))
        _packet_len = read_varint(s)
        packet_id = read_varint(s)
        if packet_id != 0x00:
            raise RuntimeError(f"unexpected status packet id {packet_id}")
        js_len = read_varint(s)
        payload = recv_exact(s, js_len)
        data = json.loads(payload.decode("utf-8"))
        return data.get("version", {}).get("name", "<missing>")


proc = subprocess.Popen(
    ["java", "-jar", str(JAR)],
    cwd=str(ROOT),
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)

version_name = "<unread>"
error = ""
try:
    time.sleep(8)
    version_name = ping_version("127.0.0.1", 25577)
except Exception as ex:
    error = str(ex)
finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()

out_lines = [f"version_name={version_name}"]
if error:
    out_lines.append(f"error={error}")

OUT.write_text("\n".join(out_lines) + "\n", encoding="utf-8")

