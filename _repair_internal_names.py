import struct
import zipfile

JAR_PATH = r"C:\Users\majko\Documents\PROJECTS\Server Jars\Sloxy\Sloxy.jar"
REPORT_PATH = r"C:\Users\majko\Documents\PROJECTS\Server Jars\Sloxy\_repair_internal_names_report.txt"

REVERT_MAP = {
    "getSloxyConfiguration": "getFlameCordConfiguration",
    "SloxyStatsCommand.java": "FlameCordStatsCommand.java",
    "SloxyWhitelistCommand.java": "FlameCordWhitelistCommand.java",
    "SloxyCommand.java": "FlameCordCommand.java",
    "SloxyConfiguration.java": "FlameCordConfiguration.java",
    "Sloxy.java": "FlameCord.java",
}


def patch_class(data):
    if len(data) < 10 or data[:4] != b"\xCA\xFE\xBA\xBE":
        return data, []

    out = bytearray()
    out.extend(data[:10])
    cp_count = struct.unpack(">H", data[8:10])[0]
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

            ns = REVERT_MAP.get(s, s)
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


report = []
with zipfile.ZipFile(JAR_PATH, "r") as zin:
    entries = []
    for info in zin.infolist():
        data = zin.read(info.filename)
        if info.filename.endswith(".class"):
            patched, changes = patch_class(data)
            if changes:
                report.append(f"[{info.filename}]")
                for old, new in changes:
                    report.append(f"- {old}")
                    report.append(f"+ {new}")
                data = patched
        entries.append((info, data))

with zipfile.ZipFile(JAR_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zout:
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

with open(REPORT_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(report) + ("\n" if report else "No internal-name repairs were required.\n"))

