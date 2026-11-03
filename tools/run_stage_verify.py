import os, sys, subprocess, hashlib
from pathlib import Path

ROOT = Path(r"C:\Users\altair\.codex\worktrees\semantic-equivalence-experiment\SMT4decomp")
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from tools.h2_calc_code_patch import encode_ips

def run_stage(n):
    stage_dir = ROOT / f"build/codex-h19-check/final-rebuild-v14/h{n}"
    image_path = stage_dir / f"code.h{n}-final.bin"
    ips_path = stage_dir / f"code.h{n}-final.ips"
    
    if not image_path.exists():
        print(f"Error: {image_path} does not exist")
        return False
        
    orig = (ROOT / "extracted/exefs/code.bin").read_bytes()
    img = image_path.read_bytes()
    
    # Generate IPS
    recs = []
    i = 0
    while i < len(orig):
        if orig[i] == img[i]:
            i += 1
            continue
        s = i
        while i < len(orig) and orig[i] != img[i] and i - s < 65535:
            i += 1
        recs.append((s, img[s:i]))
    ips_path.write_bytes(encode_ips(recs, len(orig)))
    print(f"Generated IPS for H{n}: {len(ips_path.read_bytes())} bytes")
    
    out_dir = ROOT / f"build/codex-h19-check/test-h{n}-rsp-run"
    if out_dir.exists():
        import shutil
        shutil.rmtree(out_dir)
    port = 60100 + n * 10
    
    cmd = [
        sys.executable, "tools/h2_autonomous_gdb_verify.py",
        "--azahar", r"E:\SMT4decomp\build\h0-h3-closure-20261028\h2-rsp-corrected-run001\original\app\azahar.exe",
        "--final-image", str(image_path),
        "--final-ips", str(ips_path),
        "--output-dir", str(out_dir),
        "--base-port", str(port)
    ]
    
    print(f"Running H{n} verification on port {port}...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:", res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)
    print(f"Exit code for H{n}: {res.returncode}")
    return res.returncode == 0

if __name__ == "__main__":
    target = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    run_stage(target)
