#!/usr/bin/env python3
"""Autonomous verification runner for Milestone H20 Native Host Platform Abstraction Layer."""
from pathlib import Path
import subprocess
import sys
import shutil

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import find_clang

BUILD_DIR = ROOT / 'build/h20_native'
BUILD_DIR.mkdir(parents=True, exist_ok=True)

def main():
    print("=== Building & Running Milestone H20 Native Host Execution Suite ===")
    clang = find_clang()
    print(f"Using host compiler: {clang}")

    sources = [
        str(ROOT / 'tools/test_h20_native.cpp'),
        str(ROOT / 'src/hal/hal_system.cpp'),
        str(ROOT / 'src/hal/hal_filesystem.cpp'),
        str(ROOT / 'src/hal/hal_graphics.cpp'),
        str(ROOT / 'src/hal/hal_audio.cpp'),
        str(ROOT / 'src/hal/hal_input.cpp'),
    ]

    exe_path = BUILD_DIR / ('test_h20_native.exe' if sys.platform == 'win32' else 'test_h20_native')

    cmd = [
        str(clang),
        '-std=c++17',
        '-O2',
        f'-I{ROOT / "include"}',
        *sources,
        '-o', str(exe_path)
    ]

    print("Compiling native host executable...")
    compile_res = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if compile_res.returncode != 0:
        print(f"[FAIL] Native compilation error:\n{compile_res.stderr}")
        sys.exit(1)

    print(f"[OK] Native host binary compiled: {exe_path} ({exe_path.stat().st_size} bytes)")
    print("\nExecuting native host test suite...")
    env = dict(subprocess.os.environ)
    compiler_dir = str(clang.parent)
    if 'PATH' in env:
        env['PATH'] = f"{compiler_dir};{env['PATH']}"
    else:
        env['PATH'] = compiler_dir

    run_res = subprocess.run([str(exe_path)], cwd=str(ROOT), capture_output=True, text=True, env=env)
    print(run_res.stdout)
    if run_res.stderr:
        print(run_res.stderr, file=sys.stderr)

    if run_res.returncode != 0:
        print(f"[FAIL] Native host test suite failed with exit code {run_res.returncode}")
        sys.exit(run_res.returncode)

    print("[SUCCESS] All Milestone H20 Native Host tests completed with 100% success rate.")

if __name__ == '__main__':
    main()
