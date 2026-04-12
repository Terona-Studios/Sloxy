import zipfile

JAR = r"C:\Users\majko\Documents\PROJECTS\Server Jars\Sloxy\Sloxy.jar"
OUT = r"C:\Users\majko\Documents\PROJECTS\Server Jars\Sloxy\_manifest_from_jar.txt"

with zipfile.ZipFile(JAR, "r") as zf:
    data = zf.read("META-INF/MANIFEST.MF")

with open(OUT, "w", encoding="utf-8") as f:
    f.write(data.decode("utf-8", errors="ignore"))

