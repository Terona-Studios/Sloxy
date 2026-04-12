import struct
import zipfile

JAR = r"C:\Users\majko\Documents\PROJECTS\Server Jars\Sloxy\Sloxy.jar"
OUT = r"C:\Users\majko\Documents\PROJECTS\Server Jars\Sloxy\ping-version-string-scan.txt"


def utf8_constants(data):
    if len(data) < 10 or data[:4] != b"\xCA\xFE\xBA\xBE":
        return []
    cp_count = struct.unpack(">H", data[8:10])[0]
    i = 1
    pos = 10
    out = []
    while i < cp_count:
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

needles = ["1.7", "1.8", "1.21", "x-", "SUPPORTED_VERSIONS", "game_version", "ServerPing$Protocol"]
lines = []
with zipfile.ZipFile(JAR, "r") as zf:
    for name in zf.namelist():
        if not name.endswith(".class"):
            continue
        hits = [s for s in utf8_constants(zf.read(name)) if any(n in s for n in needles)]
        if hits:
            lines.append(f"[{name}]")
            for h in sorted(set(hits)):
                lines.append(h)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

