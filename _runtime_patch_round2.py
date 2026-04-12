import re
import struct
import zipfile

JAR = r"C:\Users\majko\Documents\PROJECTS\Server Jars\Sloxy\Sloxy.jar"
OUT = r"C:\Users\majko\Documents\PROJECTS\Server Jars\Sloxy\_runtime_patch_round2_report.txt"

IDENT_RE = re.compile(r"^[A-Za-z0-9_$/;:<>()\[\].,-]+$")


def is_internal_constant(s):
    if s.startswith("dev/_2lstudios/flamecord"):
        return True
    if s.startswith("Ldev/_2lstudios/flamecord"):
        return True
    if s.startswith("getFlameCord"):
        return True
    if s.startswith("FlameCord") and s.endswith(".java"):
        return True
    if "/" in s and " " not in s and IDENT_RE.match(s):
        return True
    if s.startswith("L") and "/" in s and s.endswith(";"):
        return True
    if IDENT_RE.match(s) and " " not in s and "FlameCord" in s:
        return True
    return False


def patch_class(data, class_name):
    if len(data) < 10 or data[:4] != b"\xCA\xFE\xBA\xBE":
        return data, []

    cp_count = struct.unpack(">H", data[8:10])[0]
    out = bytearray(data[:10])
    pos = 10
    i = 1
    changes = []

    while i < cp_count:
        tag = data[pos]
        out.append(tag)
        pos += 1

        if tag == 1:
            ln = struct.unpack(">H", data[pos:pos + 2])[0]
            pos += 2
            raw = data[pos:pos + ln]
            pos += ln

            try:
                s = raw.decode("utf-8")
            except UnicodeDecodeError:
                out.extend(struct.pack(">H", ln))
                out.extend(raw)
                i += 1
                continue

            ns = s

            # Runtime config filename enforcement.
            if "flamecord.yml" in ns:
                ns = ns.replace("flamecord.yml", "sloxy.yml")

            # Runtime startup path branding near native compression log.
            if class_name == "net/md_5/bungee/BungeeCord.class":
                if ns == "Sloxy is using ":
                    ns = "Using "
                elif ns == " compression":
                    ns = " compression\n \n\u00a75Slo\u00a7bxy \u00a78(\u00a7fSloBlock Proxy\u00a78)\n\u00a7fProxy started\n "

            # Visible log/prefix replacements.
            if "[FlameCord]" in ns:
                ns = ns.replace("[FlameCord]", "[\u00a75Slo\u00a7bxy]")

            if "FlameCord" in ns and not is_internal_constant(ns):
                ns = ns.replace("FlameCord", "Sloxy")

            if ns != s:
                changes.append((s, ns))

            nb = ns.encode("utf-8")
            out.extend(struct.pack(">H", len(nb)))
            out.extend(nb)

        elif tag in (3, 4):
            out.extend(data[pos:pos + 4])
            pos += 4
        elif tag in (5, 6):
            out.extend(data[pos:pos + 8])
            pos += 8
            i += 1
        elif tag in (7, 8, 16, 19, 20):
            out.extend(data[pos:pos + 2])
            pos += 2
        elif tag in (9, 10, 11, 12, 17, 18):
            out.extend(data[pos:pos + 4])
            pos += 4
        elif tag == 15:
            out.extend(data[pos:pos + 3])
            pos += 3
        else:
            return data, []

        i += 1

    out.extend(data[pos:])
    return bytes(out), changes


entries = []
report = []
with zipfile.ZipFile(JAR, "r") as zin:
    for info in zin.infolist():
        data = zin.read(info.filename)
        if info.filename.endswith(".class"):
            patched, changes = patch_class(data, info.filename)
            if changes:
                data = patched
                report.append(f"[{info.filename}]")
                for old, new in changes:
                    report.append(f"- {old}")
                    report.append(f"+ {new}")
        entries.append((info, data))

with zipfile.ZipFile(JAR, "w", compression=zipfile.ZIP_DEFLATED) as zout:
    for info, data in entries:
        zinfo = zipfile.ZipInfo(info.filename)
        zinfo.date_time = info.date_time
        zinfo.compress_type = zipfile.ZIP_DEFLATED
        zinfo.external_attr = info.external_attr
        zinfo.comment = info.comment
        zinfo.extra = info.extra
        zinfo.create_system = info.create_system
        zinfo.flag_bits = info.flag_bits
        zout.writestr(zinfo, data)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(report) + ("\n" if report else "No changes applied.\n"))

