import json
import socket
import struct

HOST = "127.0.0.1"
PORT = 25577
TIMEOUT = 5


def pack_varint(value):
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


def read_varint(sock):
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


def recv_exact(sock, n):
    data = bytearray()
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise RuntimeError("socket closed early")
        data.extend(chunk)
    return bytes(data)


with socket.create_connection((HOST, PORT), timeout=TIMEOUT) as s:
    s.settimeout(TIMEOUT)

    host_bytes = HOST.encode("utf-8")

    handshake_payload = b"".join(
        [
            pack_varint(0x00),  # handshake packet id
            pack_varint(769),   # protocol version (1.21.4-ish, ignored for status branding)
            pack_varint(len(host_bytes)),
            host_bytes,
            struct.pack(">H", PORT),
            pack_varint(1),  # next state: status
        ]
    )
    s.sendall(pack_varint(len(handshake_payload)) + handshake_payload)

    status_req = pack_varint(1) + pack_varint(0x00)
    s.sendall(status_req)

    _ = read_varint(s)  # packet length
    packet_id = read_varint(s)
    if packet_id != 0x00:
        raise RuntimeError("unexpected packet id: %d" % packet_id)

    json_len = read_varint(s)
    payload = recv_exact(s, json_len)
    data = json.loads(payload.decode("utf-8"))

print(data.get("version", {}).get("name", "<missing>"))

