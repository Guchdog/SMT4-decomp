import subprocess
from pathlib import Path

MAKEROM = r"E:\emulador3ds\makerom.exe"
CCI = r"E:\emulador3ds\00040000000E5C00 Shin Megami Tensei IV (CTR-P-AMXE) (v0.1.0) (U).piratelegit-decrypted.cci"
OUT_CIA = r"E:\SMT4decomp\build\cia-staging\test_orig.cia"

cmd = [
    MAKEROM,
    "-f", "cia",
    "-target", "t",
    "-ignoresign",
    "-o", OUT_CIA,
    "-ccitocia", CCI
]

print("Running:", " ".join(cmd))
res = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:", res.stdout)
if res.stderr:
    print("STDERR:", res.stderr)
print("Exit code:", res.returncode)
