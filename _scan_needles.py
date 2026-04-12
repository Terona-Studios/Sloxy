import struct
import zipfile

JAR = r"C:\Users\majko\Documents\PROJECTS\Server Jars\Sloxy\Sloxy.jar"
OUT = r"C:\Users\majko\Documents\PROJECTS\Server Jars\Sloxy\_needle_hits.txt"
NEEDLES = [
    "flamecord.yml",
    "sloxy.yml",
    "Using libdeflate",
    "libdeflate",
    "StatusRequest",
    "handle",
    "setVersion",
    "ServerPing$Protocol",
    "Sloxy (SloBlock Proxy)",
    "FlameCord",
]


def utf8_constants(data):
    cp_count = struct.unpack(">H", data[8:10])[0]
    i = 1
    pos = 10
    out = []
    while i < cp_count and pos < len(data):
        tag = data[pos]
        pos += 1
        if tag == 1:
            ln = struct.unpack(">H", data[pos:pos + 2])[0]
            pos += 2
            raw = data[pos:pos + ln]
            pos += ln
            try:
                out.append(raw.decode("utf-8"))
            except UnicodeDecodeError:
                pass
        elif tag in (3, 4):
            pos += 4
        elif tag in (5, 6):
            pos += 8
            i += 1
        elif tag in (7, 8, 16, 19, 20):
            pos += 2
        elif tag in (9, 10, 11, 12, 17, 18):
            pos += 4
        elif tag == 15:
            pos += 3
        else:
            break
        i += 1
    return out

lines = []
with zipfile.ZipFile(JAR, "r") as zf:
    for name in zf.namelist():
        if not name.endswith(".class"):
            continue
        vals = utf8_constants(zf.read(name))
        hits = [s for s in vals if any(n in s for n in NEEDLES)]
        if hits:
            lines.append(f"[{name}]")
            for h in sorted(set(hits)):
                lines.append(h)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

