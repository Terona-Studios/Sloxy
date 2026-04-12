import hashlib
import os
import struct
import zipfile
from datetime import datetime

ROOT = r"C:\Users\majko\Documents\PROJECTS\Server Jars\Sloxy"
JAR = os.path.join(ROOT, "Sloxy.jar")
OUT = os.path.join(ROOT, "_final_patch_status.txt")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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


def class_has(name, needle):
    with zipfile.ZipFile(JAR, "r") as zf:
        vals = utf8_constants(zf.read(name))
    return any(needle in v for v in vals)


manifest_text = ""
with zipfile.ZipFile(JAR, "r") as zf:
    manifest_text = zf.read("META-INF/MANIFEST.MF").decode("utf-8", errors="ignore")

checks = {
    "manifest_impl_title": "Implementation-Title: Sloxy" in manifest_text,
    "manifest_impl_version": "Implementation-Version: Sloxy" in manifest_text,
    "bungeecord_has_brand_version": class_has("net/md_5/bungee/BungeeCord.class", "Sloxy (SloBlock Proxy)"),
    "queryhandler_proxy_name": class_has("net/md_5/bungee/query/QueryHandler.class", "Sloxy_Proxy"),
    "reload_message_rebranded": class_has("net/md_5/bungee/command/CommandReload.class", "Sloxy has been reloaded."),
    "iputils_prefix_rebranded": class_has("dev/_2lstudios/flamecord/utils/IPUtils.class", "[\u00a75Slo\u00a7bxy]"),
}

visible_scan = os.path.join(ROOT, "_visible_flamecord_remaining.txt")
visible_result = "(not-run)"
if os.path.exists(visible_scan):
    with open(visible_scan, "r", encoding="utf-8") as f:
        visible_result = f.read().strip()

stat = os.stat(JAR)

lines = [
    "Sloxy JAR Patch Status",
    "======================",
    f"Timestamp: {datetime.now().isoformat()}",
    f"Jar: {JAR}",
    f"Size: {stat.st_size}",
    f"SHA256: {sha256(JAR)}",
    "",
    "Checks:",
]
for k, v in checks.items():
    lines.append(f"- {k}: {'PASS' if v else 'FAIL'}")

lines.extend(
    [
        "",
        "Visible FlameCord scan:",
        visible_result,
        "",
        "Note:",
        "- Startup ASCII banner insertion and global PREFIX constant injection were not bytecode-inserted in this pass.",
        "- Display/log branding and manifest fields were patched in-place without touching protocol IDs/handshake logic.",
    ]
)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

