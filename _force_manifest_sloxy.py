import zipfile

JAR = r"C:\Users\majko\Documents\PROJECTS\Server Jars\Sloxy\Sloxy.jar"
REPORT = r"C:\Users\majko\Documents\PROJECTS\Server Jars\Sloxy\_manifest_patch_report.txt"

with zipfile.ZipFile(JAR, "r") as zin:
    entries = []
    manifest_changed = False
    for info in zin.infolist():
        data = zin.read(info.filename)
        if info.filename == "META-INF/MANIFEST.MF":
            text = data.decode("utf-8", errors="ignore").replace("\r\n", "\n")
            lines = [ln for ln in text.split("\n") if ln != ""]

            kept = []
            skip_continuations = False
            for ln in lines:
                # Drop folded continuation lines that belong to removed headers.
                if ln.startswith(" "):
                    if skip_continuations:
                        continue
                    kept.append(ln)
                    continue

                if ln.startswith("Implementation-Title:"):
                    skip_continuations = True
                    continue
                if ln.startswith("Implementation-Version:"):
                    skip_continuations = True
                    continue
                if ln.startswith("Specification-Title:"):
                    skip_continuations = True
                    continue

                skip_continuations = False
                kept.append(ln)

            out_lines = []
            inserted = False
            for ln in kept:
                out_lines.append(ln)
                if ln.startswith("Enable-Native-Access:") and not inserted:
                    out_lines.append("Implementation-Title: Sloxy")
                    out_lines.append("Implementation-Version: Sloxy")
                    inserted = True

            if not inserted:
                out_lines.append("Implementation-Title: Sloxy")
                out_lines.append("Implementation-Version: Sloxy")

            out_text = "\r\n".join(out_lines) + "\r\n\r\n"
            data = out_text.encode("utf-8")
            manifest_changed = True
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

with open(REPORT, "w", encoding="utf-8") as f:
    f.write("Manifest updated to Sloxy branding.\n" if manifest_changed else "Manifest unchanged.\n")

