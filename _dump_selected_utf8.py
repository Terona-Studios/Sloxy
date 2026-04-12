import struct
import zipfile

JAR = r"C:\Users\majko\Documents\PROJECTS\Server Jars\Sloxy\Sloxy.jar"
OUT = r"C:\Users\majko\Documents\PROJECTS\Server Jars\Sloxy\_selected_utf8.txt"
CLASSES = [
    "net/md_5/bungee/command/CommandBungee.class",
    "net/md_5/bungee/api/ProxyServer.class",
    "net/md_5/bungee/connection/InitialHandler.class",
    "net/md_5/bungee/conf/Configuration.class",
    "dev/_2lstudios/flamecord/FlameCord.class",
    "dev/_2lstudios/flamecord/managers/UserWhitelistManager.class",
    "dev/_2lstudios/flamecord/utils/IPUtils.class",
    "net/md_5/bungee/command/CommandReload.class",
    "net/md_5/bungee/Bootstrap.class",
    "net/md_5/bungee/query/QueryHandler.class",
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

with zipfile.ZipFile(JAR, "r") as zf, open(OUT, "w", encoding="utf-8") as f:
    for cls in CLASSES:
        f.write(f"\n[{cls}]\n")
        try:
            vals = utf8_constants(zf.read(cls))
        except KeyError:
            f.write("(missing)\n")
            continue
        seen = set()
        for s in vals:
            if s in seen:
                continue
            seen.add(s)
            if any(k in s for k in ["FlameCord", "Sloxy", "version", "Version", "1.7", "1.21", "Proxy", "[", "]", "game_version", "\u00a7", "&"]):
                f.write(s + "\n")

