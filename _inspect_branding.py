import struct
import zipfile

JAR = r"C:\Users\majko\Documents\PROJECTS\Server Jars\Sloxy\Sloxy.jar"
CLASSES = [
    "net/md_5/bungee/api/ProxyServer.class",
    "net/md_5/bungee/command/CommandBungee.class",
    "net/md_5/bungee/BungeeCord.class",
    "net/md_5/bungee/protocol/ProtocolConstants.class",
    "net/md_5/bungee/query/QueryHandler.class",
    "dev/_2lstudios/flamecord/utils/IPUtils.class",
    "dev/_2lstudios/flamecord/managers/UserWhitelistManager.class",
]

KEYS = [
    "FlameCord",
    "BungeeCord",
    "Sloxy",
    "version",
    "Version",
    "1.7",
    "1.21",
    "Proxy",
    "[",
    "]",
    "&",
    "\u00a7",
    "game_version",
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


with zipfile.ZipFile(JAR) as zf:
    for cls in CLASSES:
        print(f"\n[{cls}]")
        try:
            consts = utf8_constants(zf.read(cls))
        except KeyError:
            print("(missing)")
            continue
        shown = set()
        for s in consts:
            if s in shown:
                continue
            if any(k in s for k in KEYS):
                print(s)
                shown.add(s)

