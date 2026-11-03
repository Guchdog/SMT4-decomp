import subprocess, time, os
from pathlib import Path

CCI = Path(r"E:\emulador3ds\00040000000E5C00 Shin Megami Tensei IV (CTR-P-AMXE) (v0.1.0) (U).piratelegit-decrypted.cci")
MAKEROM = Path(r"E:\emulador3ds\makerom.exe")
STAGING = Path(r"E:\SMT4decomp\build\cia-staging")
STAGING.mkdir(parents=True, exist_ok=True)
NCCH0 = STAGING / "ncch0.bin"
OUT_CIA = STAGING / "test_ncch0.cia"

NCCH0_OFFSET = 0x4000
NCCH0_SIZE = 0x6FCC9000

if not NCCH0.exists() or NCCH0.stat().st_size != NCCH0_SIZE:
    print(f"Extracting NCCH0 ({NCCH0_SIZE / (1024*1024):.2f} MB)...")
    t0 = time.time()
    with open(CCI, "rb") as fin, open(NCCH0, "wb") as fout:
        fin.seek(NCCH0_OFFSET)
        remaining = NCCH0_SIZE
        chunk = 32 * 1024 * 1024
        while remaining > 0:
            to_read = min(remaining, chunk)
            fout.write(fin.read(to_read))
            remaining -= to_read
    print(f"NCCH0 extracted in {time.time() - t0:.2f}s")
else:
    print("NCCH0 already exists")

cmd = [
    str(MAKEROM),
    "-f", "cia",
    "-target", "t",
    "-ignoresign",
    "-content", f"{NCCH0}:0:0x0000",
    "-o", str(OUT_CIA)
]

print("Running:", " ".join(cmd))
res = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:\n", res.stdout)
print("STDERR:\n", res.stderr)
print("Exit code:", res.returncode)
if OUT_CIA.exists():
    print(f"SUCCESS! Built CIA: {OUT_CIA.stat().st_size} bytes")
