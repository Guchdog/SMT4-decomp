import os, sys, importlib
from pathlib import Path

ROOT = Path(r"C:\Users\altair\.codex\worktrees\semantic-equivalence-experiment\SMT4decomp")
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

for n in range(12, 20):
    mod = importlib.import_module(f"tools.h{n}_staged_image_patch")
    subs = getattr(mod, "SUBSYSTEMS", getattr(mod, "CRT_SUBSYSTEMS", []))
    print(f"=== H{n} ({len(subs)} subsystems) ===")
    for s in subs:
        print(f"  {s.get('id', '?')}: {hex(s.get('addr', 0))} {s.get('cand_fn', '?')} ({s.get('size', 0)} bytes) src: {s.get('src')}")
