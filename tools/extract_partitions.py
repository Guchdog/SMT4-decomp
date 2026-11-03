import subprocess, sys
from pathlib import Path

ROOT = Path(r"C:\Users\altair\.codex\worktrees\semantic-equivalence-experiment\SMT4decomp")
CCI = Path(r"E:\emulador3ds\00040000000E5C00 Shin Megami Tensei IV (CTR-P-AMXE) (v0.1.0) (U).piratelegit-decrypted.cci")
CTRTOOL = Path(r"E:\emulador3ds\ctrtool.exe")
OUT = Path(r"E:\SMT4decomp\build\cia-staging")
OUT.mkdir(parents=True, exist_ok=True)

print("Extracting RomFS, PlainRgn, and ExeFS from decrypted CCI...")
cmd = [
    str(CTRTOOL),
    "-p", # plain
    "-n", "0", # partition 0
    f"--romfs={OUT / 'romfs.bin'}",
    f"--plainrgn={OUT / 'plainrgn.bin'}",
    f"--logo={OUT / 'logo.bin'}",
    str(CCI)
]

print("Running:", " ".join(cmd))
res = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:", res.stdout)
if res.stderr:
    print("STDERR:", res.stderr)
print("Exit code:", res.returncode)
