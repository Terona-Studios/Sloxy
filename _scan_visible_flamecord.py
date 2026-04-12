import re
import struct
import zipfile

JAR = r"C:\Users\majko\Documents\PROJECTS\Server Jars\Sloxy\Sloxy.jar"
OUT = r"C:\Users\majko\Documents\PROJECTS\Server Jars\Sloxy\_visible_flamecord_remaining.txt"
IGNORE_EXACT = {
    "getFlameCordConfiguration",
    "FlameCord.java",
    "FlameCordCommand.java",
    "FlameCordStatsCommand.java",
    "FlameCordWhitelistCommand.java",
    "FlameCordConfiguration.java",
}

IDENT_RE = re.compile(r"^[A-Za-z0-9_$/;:<>()\[\].,-]+$")


def is_internal(s):
    if s in IGNORE_EXACT:
        return True
    if s.startswith("dev/_2lstudios/flamecord"):
        return True
    if s.startswith("Ldev/_2lstudios/flamecord"):
        return True
    if s.startswith("getFlameCord"):
        return True
    if s.startswith("FlameCord") and s.endswith(".java"):
        return True
    if s.startswith("L") and "/" in s and s.endswith(";"):
        return True
    if "/" in s and " " not in s and IDENT_RE.match(s):
        return True
    if IDENT_RE.match(s) and " " not in s and "FlameCord" in s:
        return True
    return False


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
        hits = []
        for s in utf8_constants(zf.read(name)):
            if "FlameCord" not in s:
                continue
            if is_internal(s):
                continue
            hits.append(s)
        if hits:
            lines.append(f"[{name}]")
            for h in sorted(set(hits)):
                lines.append(h)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + ("\n" if lines else "No visible FlameCord strings found.\n"))


