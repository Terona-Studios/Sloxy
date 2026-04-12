import struct
import zipfile

JAR = r"C:\Users\majko\Documents\PROJECTS\Server Jars\Sloxy\Sloxy.jar"
CLASS_NAME = "net/md_5/bungee/BungeeCord.class"
OUT = r"C:\Users\majko\Documents\PROJECTS\Server Jars\Sloxy\_BungeeCord_utf8.txt"


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
                out.append(raw.decode("latin1", errors="ignore"))
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

with zipfile.ZipFile(JAR, "r") as zf:
    data = zf.read(CLASS_NAME)

vals = utf8_constants(data)
with open(OUT, "w", encoding="utf-8") as f:
    for idx, s in enumerate(vals, 1):
        if s and all((ord(ch) >= 32 or ch in "\t\n\r") for ch in s):
            f.write(f"{idx:04d}: {s}\n")

