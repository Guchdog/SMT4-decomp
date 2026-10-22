"""Freestanding ARMv6K compilation pipeline and build verification for 3DS ELF32 targets."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys


def find_clang() -> Path:
    """Locate the clang++ executable from environment, PATH, or standard installation paths."""
    env_path = os.environ.get("CLANG_PATH")
    if env_path:
        p = Path(env_path)
        if p.is_file():
            return p

    which_clang = shutil.which("clang++") or shutil.which("clang++.exe")
    if which_clang:
        return Path(which_clang).resolve()

    candidates = [
        Path(r"C:\msys64\clang64\bin\clang++.exe"),
        Path(r"C:\msys64\ucrt64\bin\clang++.exe"),
        Path(r"C:\msys64\mingw64\bin\clang++.exe"),
        Path(r"C:\Program Files\LLVM\bin\clang++.exe"),
        Path("/usr/bin/clang++"),
        Path("/usr/local/bin/clang++"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()

    raise FileNotFoundError(
        "Clang++ compiler not found. Please install Clang or set CLANG_PATH."
    )


def get_clang_resource_dir(clang: Path | None = None) -> Path:
    """Query clang++ for its builtin resource directory."""
    if clang is None:
        clang = find_clang()

    res = subprocess.run(
        [str(clang), "-print-resource-dir"],
        capture_output=True,
        text=True,
        check=True,
    )
    resource_dir = Path(res.stdout.strip())
    if not resource_dir.exists():
        raise FileNotFoundError(
            f"Clang resource directory not found at {resource_dir}"
        )
    return resource_dir


def get_armv6k_flags(
    repo_root: Path = Path("."), clang: Path | None = None
) -> list[str]:
    """Construct compiler flags isolating the 3DS ARMv6K build from host Win32 headers."""
    repo_root = Path(repo_root).resolve()
    resource_dir = get_clang_resource_dir(clang)
    freestanding_dir = repo_root / "include" / "freestanding"
    resource_include_dir = resource_dir / "include"
    include_dir = repo_root / "include"

    return [
        "--target=armv6k-none-eabihf",
        "-mcpu=mpcore",
        "-mfpu=vfpv2",
        "-mfloat-abi=hard",
        "-O2",
        "-std=c++20",
        "-fno-exceptions",
        "-fno-rtti",
        "-ffreestanding",
        "-nostdinc",
        "-nostdinc++",
        "-isystem",
        str(freestanding_dir),
        "-isystem",
        str(resource_include_dir),
        f"-I{include_dir}",
    ]


def compile_tu_armv6k(
    src_file: Path, out_obj: Path, repo_root: Path = Path(".")
) -> subprocess.CompletedProcess:
    """Compile a single C++ translation unit to a 3DS ARMv6K ELF32 object file."""
    src_file = Path(src_file)
    out_obj = Path(out_obj)
    repo_root = Path(repo_root).resolve()
    clang = find_clang()

    out_obj.parent.mkdir(parents=True, exist_ok=True)
    flags = get_armv6k_flags(repo_root, clang)
    cmd = [str(clang)] + flags + ["-c", str(src_file), "-o", str(out_obj)]

    return subprocess.run(cmd, capture_output=True, text=True)


def compile_all_armv6k(
    repo_root: Path = Path("."),
    out_dir: Path = Path("build/obj/armv6k"),
    force: bool = False,
) -> dict:
    """Compile all C++ translation units under src/ to ARMv6K object files.

    Returns:
        dict with keys:
            total: int, total translation units discovered
            succeeded: int, count of successfully compiled / up-to-date objects
            failed: list of (src_path, stderr) for failing units
            objects: mapping from source path (str and relative posix) to compiled object Path
    """
    repo_root = Path(repo_root).resolve()
    out_dir = Path(out_dir)
    if not out_dir.is_absolute():
        out_dir = repo_root / out_dir

    src_root = repo_root / "src"
    cpp_files = sorted(src_root.rglob("*.cpp"))

    total = len(cpp_files)
    succeeded = 0
    failed: list[tuple[str, str]] = []
    objects: dict[str, Path] = {}

    for src_file in cpp_files:
        rel = src_file.relative_to(src_root)
        out_obj = out_dir / rel.with_suffix(".o")
        rel_posix = src_file.relative_to(repo_root).as_posix()

        # mtime caching: skip recompilation if object is newer than source file
        if not force and out_obj.exists():
            try:
                if out_obj.stat().st_mtime >= src_file.stat().st_mtime:
                    succeeded += 1
                    objects[str(src_file)] = out_obj
                    objects[rel_posix] = out_obj
                    continue
            except OSError:
                pass

        res = compile_tu_armv6k(src_file, out_obj, repo_root=repo_root)
        if res.returncode == 0 and out_obj.exists():
            succeeded += 1
            objects[str(src_file)] = out_obj
            objects[rel_posix] = out_obj
        else:
            failed.append((rel_posix, res.stderr))

    return {
        "total": total,
        "succeeded": succeeded,
        "failed": failed,
        "objects": objects,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compile SMT4 translation units to 3DS ARMv6K ELF32 object files"
    )
    parser.add_argument(
        "--repo-root", type=Path, default=Path("."), help="Path to repository root"
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("build/obj/armv6k"),
        help="Output directory for compiled .o objects",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force recompilation even if object files are newer than source",
    )
    parser.add_argument(
        "--tu",
        type=Path,
        default=None,
        help="Compile a specific translation unit only",
    )
    args = parser.parse_args()

    try:
        clang = find_clang()
        print(f"Using Clang compiler: {clang}")
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.tu:
        src_file = args.tu
        out_obj = args.out_dir / src_file.name.replace(".cpp", ".o")
        print(f"Compiling {src_file} -> {out_obj}...")
        res = compile_tu_armv6k(src_file, out_obj, repo_root=args.repo_root)
        if res.returncode == 0:
            print("OK")
            sys.exit(0)
        else:
            print(res.stderr, file=sys.stderr)
            sys.exit(1)

    print("Compiling all translation units to 3DS ARMv6K...")
    result = compile_all_armv6k(
        repo_root=args.repo_root, out_dir=args.out_dir, force=args.force
    )
    print(f"Results: {result['succeeded']}/{result['total']} succeeded.")

    if result["failed"]:
        print(f"\n{len(result['failed'])} translation unit(s) failed:", file=sys.stderr)
        for path, err in result["failed"]:
            print(f"--- {path} ---", file=sys.stderr)
            print(err, file=sys.stderr)
        sys.exit(1)

    print("All translation units compiled successfully!")


if __name__ == "__main__":
    main()
