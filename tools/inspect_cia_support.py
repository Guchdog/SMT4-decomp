from pathlib import Path
import re

exe_path = Path(r"E:\SMT4decomp\build\h0-h3-closure-20261028\h2-rsp-corrected-run001\original\app\azahar.exe")
data = exe_path.read_bytes()

matches = set()
for m in re.finditer(rb'[A-Za-z0-9_\-/\.]{3,}\.cia', data, re.IGNORECASE):
    matches.add(m.group(0).decode("ascii", errors="replace"))

print("Matches with .cia:")
for m in sorted(matches)[:30]:
    print(" ", m)

matches2 = set()
for m in re.finditer(rb'Install[A-Za-z0-9_ ]{0,30}', data, re.IGNORECASE):
    matches2.add(m.group(0).decode("ascii", errors="replace"))

print("\nMatches with Install:")
for m in sorted(matches2)[:30]:
    print(" ", m)
