import subprocess, sys
from pathlib import Path

ROOT = Path(r"C:\Users\altair\.codex\worktrees\semantic-equivalence-experiment\SMT4decomp")
MAKEROM = Path(r"E:\emulador3ds\makerom.exe")
STAGING = Path(r"E:\SMT4decomp\build\cia-staging")
EXTRACTED = Path(r"E:\SMT4decomp\extracted")
CODE_BIN = Path(r"E:\SMT4decomp\build\codex-h19-check\final-rebuild-v15\h19\code.h19-final.bin")

cxi_path = STAGING / "patched.cxi"

cmd = [
    str(MAKEROM),
    "-f", "ncch",
    "-target", "t",
    "-exheader", str(EXTRACTED / "exheader.bin"),
    "-code", str(CODE_BIN),
    "-icon", str(EXTRACTED / "exefs/icon.bin"),
    "-banner", str(EXTRACTED / "exefs/banner.bin"),
    "-logo", str(EXTRACTED / "exefs/logo.bin"),
    "-plainrgn", str(STAGING / "plainrgn.bin"),
    "-romfs", str(STAGING / "romfs.bin"),
    "-o", str(cxi_path),
]

print("Building CXI with makerom...")
print("Running:", " ".join(cmd))
res = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:", res.stdout)
if res.stderr:
    print("STDERR:", res.stderr)
print("Exit code:", res.returncode)
