import io
import struct
import zipfile

JAR_PATH = r"C:\Users\majko\Documents\PROJECTS\Server Jars\Sloxy\Sloxy.jar"
REPORT_PATH = r"C:\Users\majko\Documents\PROJECTS\Server Jars\Sloxy\_branding_patch_report.txt"


def parse_and_patch_class(data, class_name):
    if len(data) < 10 or data[:4] != b"\xCA\xFE\xBA\xBE":
        return data, []

    out = bytearray()
    out.extend(data[:10])
    cp_count = struct.unpack(">H", data[8:10])[0]
    pos = 10
    idx = 1
    changes = []

    while idx < cp_count:
        tag = data[pos]
        out.append(tag)
        pos += 1

        if tag == 1:  # Utf8
            ln = struct.unpack(">H", data[pos:pos + 2])[0]
            pos += 2
            raw = data[pos:pos + ln]
            pos += ln

            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                out.extend(struct.pack(">H", ln))
                out.extend(raw)
                idx += 1
                continue

            new_text = text

            # Targeted branding replacements for user-visible text only.
            if "[FlameCord]" in new_text:
                new_text = new_text.replace("[FlameCord]", "[\u00a75Slo\u00a7bxy]")

            if "FlameCord" in new_text:
                # Keep internal names/descriptors/packages untouched.
                is_internal = (
                    "/" in new_text
                    or new_text.startswith("Ldev/_2lstudios/flamecord")
                    or new_text.startswith("dev/_2lstudios/flamecord")
                )
                if not is_internal:
                    new_text = new_text.replace("FlameCord", "Sloxy")

            if new_text == "2.5.5":
                new_text = "Sloxy (SloBlock Proxy)"

            if new_text == "FlameCord_Proxy":
                new_text = "Sloxy_Proxy"

            if new_text == "FlameCord":
                new_text = "Sloxy (SloBlock Proxy)"

            if new_text != text:
                changes.append((text, new_text))

            new_raw = new_text.encode("utf-8")
            out.extend(struct.pack(">H", len(new_raw)))
            out.extend(new_raw)

        elif tag in (3, 4):
            out.extend(data[pos:pos + 4])
            pos += 4
        elif tag in (5, 6):
            out.extend(data[pos:pos + 8])
            pos += 8
            idx += 1
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

        idx += 1

    out.extend(data[pos:])
    return bytes(out), changes


def patch_manifest(data):
    text = data.decode("utf-8", errors="ignore")
    original = text
    text = text.replace("Implementation-Title: FlameCord", "Implementation-Title: Sloxy")
    text = text.replace("Implementation-Version: FlameCord", "Implementation-Version: Sloxy")
    if "Implementation-Title:" in text:
        lines = []
        for line in text.splitlines():
            if line.startswith("Implementation-Title:"):
                lines.append("Implementation-Title: Sloxy")
            elif line.startswith("Implementation-Version:"):
                lines.append("Implementation-Version: Sloxy")
            else:
                lines.append(line)
        text = "\n".join(lines) + "\n"
    changed = text != original
    return text.encode("utf-8"), changed


report_lines = []
with zipfile.ZipFile(JAR_PATH, "r") as zin:
    items = []
    for info in zin.infolist():
        data = zin.read(info.filename)
        changed = False

        if info.filename.endswith(".class"):
            patched, changes = parse_and_patch_class(data, info.filename)
            if changes:
                changed = True
                data = patched
                report_lines.append(f"[{info.filename}]")
                for old, new in changes:
                    report_lines.append(f"- {old}")
                    report_lines.append(f"+ {new}")
        elif info.filename == "META-INF/MANIFEST.MF":
            patched, m_changed = patch_manifest(data)
            if m_changed:
                changed = True
                data = patched
                report_lines.append("[META-INF/MANIFEST.MF]")
                report_lines.append("- normalized Implementation-Title/Implementation-Version to Sloxy")

        items.append((info, data, changed))

with zipfile.ZipFile(JAR_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zout:
    for info, data, _ in items:
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
    if report_lines:
        f.write("\n".join(report_lines) + "\n")
    else:
        f.write("No changes applied.\n")

