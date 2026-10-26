"""Freestanding ARMv6K compilation pipeline and build verification for 3DS ELF32 targets."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


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
    clang = (clang or find_clang()).resolve()
    stat = clang.stat()
    return _clang_resource_dir(str(clang), stat.st_mtime_ns, stat.st_size)


@lru_cache(maxsize=8)
def _clang_resource_dir(clang: str, mtime_ns: int, size: int) -> Path:
    """Cache queries only while the selected compiler executable is unchanged."""
    res = subprocess.run(
        [clang, "-print-resource-dir"],
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
    src_file = Path(src_file).resolve()
    out_obj = Path(out_obj).resolve()
    repo_root = Path(repo_root).resolve()
    clang = find_clang()

    out_obj.parent.mkdir(parents=True, exist_ok=True)
    flags = get_armv6k_flags(repo_root, clang)
    depfile = out_obj.with_suffix(out_obj.suffix + ".d")
    manifest = out_obj.with_suffix(out_obj.suffix + ".json")
    manifest.unlink(missing_ok=True)
    cmd = [str(clang)] + flags + ["-MD", "-MF", str(depfile), "-MT", "object",
                                "-c", str(src_file), "-o", str(out_obj)]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=repo_root)
    if result.returncode == 0 and out_obj.is_file():
        dependencies = _read_dependencies(depfile)
        dependencies.add(src_file)
        metadata = {
            "identity": _build_identity(repo_root, clang),
            "dependencies": {str(p): _file_hash(p) for p in sorted(dependencies)},
            "object_hash": _file_hash(out_obj),
        }
        manifest.write_text(json.dumps(metadata, sort_keys=True), encoding="utf-8")
    else:
        # A failed rebuild must never leave a previous successful object usable.
        out_obj.unlink(missing_ok=True)
    return result


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_dependencies(depfile: Path) -> set[Path]:
    """Read Clang Make dependencies, including system headers and escaped spaces."""
    text = depfile.read_text(encoding="utf-8").replace("\\\n", " ")
    # The fixed -MT value avoids confusing a Windows drive colon with the rule.
    payload = text.split(":", 1)[1]
    words = re.findall(r"(?:\\.|[^\s])+", payload)
    return {Path(re.sub(r"\\([ #:$\\])", r"\1", word)).resolve() for word in words}


@lru_cache(maxsize=8)
def _compiler_version(path: str, mtime_ns: int, size: int) -> str:
    return subprocess.run([path, "--version"], capture_output=True, text=True,
                          check=True).stdout


def _build_identity(repo_root: Path, clang: Path | None = None) -> dict:
    clang = (clang or find_clang()).resolve()
    stat = clang.stat()
    return {
        "compiler": str(clang),
        "compiler_version": _compiler_version(str(clang), stat.st_mtime_ns, stat.st_size),
        "compiler_mtime_ns": stat.st_mtime_ns,
        "flags": get_armv6k_flags(repo_root, clang),
    }


def is_object_current(src_file: Path, out_obj: Path, repo_root: Path = Path(".")) -> bool:
    """Validate source/header contents, compiler identity, flags, and object contents."""
    src_file, out_obj = Path(src_file).resolve(), Path(out_obj).resolve()
    try:
        metadata = json.loads(out_obj.with_suffix(out_obj.suffix + ".json").read_text(encoding="utf-8"))
        if metadata["identity"] != _build_identity(Path(repo_root).resolve()):
            return False
        dependencies = metadata["dependencies"]
        return (str(src_file) in dependencies and
                metadata["object_hash"] == _file_hash(out_obj) and
                all(_file_hash(Path(p)) == digest for p, digest in dependencies.items()))
    except (OSError, ValueError, KeyError, TypeError):
        return False


def ensure_tu_armv6k(src_file: Path, out_obj: Path, repo_root: Path = Path("."),
                      force: bool = False) -> subprocess.CompletedProcess:
    """Return a valid cached compilation, or rebuild with dependency tracking."""
    if not force and is_object_current(src_file, out_obj, repo_root):
        return subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    return compile_tu_armv6k(src_file, out_obj, repo_root)


def default_job_count() -> int:
    """Use the CPUs available to this process, falling back on older Python."""
    available = getattr(os, "process_cpu_count", os.cpu_count)()
    return max(1, available or 1)


def _positive_jobs(value: str) -> int:
    try:
        count = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("jobs must be a positive integer") from error
    if count < 1:
        raise argparse.ArgumentTypeError("jobs must be a positive integer")
    return count


def compile_all_armv6k(
    repo_root: Path = Path("."),
    out_dir: Path = Path("build/obj/armv6k"),
    force: bool = False,
    jobs: int | None = None,
) -> dict:
    """Compile independent translation units concurrently; preserve result order.

    Returns:
        dict with keys:
            total: int, total translation units discovered
            succeeded: int, count of successfully compiled / up-to-date objects
            failed: list of (src_path, stderr) for failing units
            objects: mapping from source path (str and relative posix) to compiled object Path
            jobs: actual worker count (zero for an empty source tree)
            compiled_count: successful compiler invocations
            cached_count: validated objects reused without invoking Clang
    """
    repo_root = Path(repo_root).resolve()
    out_dir = Path(out_dir)
    if not out_dir.is_absolute():
        out_dir = repo_root / out_dir

    src_root = repo_root / "src"
    cpp_files = sorted(src_root.rglob("*.cpp"))

    total = len(cpp_files)
    jobs = default_job_count() if jobs is None else jobs
    if not isinstance(jobs, int) or jobs < 1:
        raise ValueError("jobs must be a positive integer")
    worker_count = min(jobs, total)
    succeeded = 0
    compiled_count = 0
    cached_count = 0
    failed: list[tuple[str, str]] = []
    objects: dict[str, Path] = {}

    def compile_one(src_file: Path):
        rel = src_file.relative_to(src_root)
        out_obj = out_dir / rel.with_suffix(".o")
        res = ensure_tu_armv6k(src_file, out_obj, repo_root=repo_root, force=force)
        return src_file, out_obj, res

    if total:
        # Each TU owns a distinct object, depfile and manifest. Threads wait on
        # compiler subprocesses, so Python's GIL does not serialize Clang jobs.
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            for src_file, out_obj, res in executor.map(compile_one, cpp_files):
                rel_posix = src_file.relative_to(repo_root).as_posix()
                if res.returncode == 0 and out_obj.exists():
                    succeeded += 1
                    if res.args:
                        compiled_count += 1
                    else:
                        cached_count += 1
                    objects[str(src_file)] = out_obj
                    objects[rel_posix] = out_obj
                else:
                    failed.append((rel_posix, res.stderr))

    return {
        "total": total,
        "succeeded": succeeded,
        "failed": failed,
        "objects": objects,
        "jobs": worker_count,
        "compiled_count": compiled_count,
        "cached_count": cached_count,
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
        help="Force recompilation instead of reusing validated cached objects",
    )
    parser.add_argument(
        "--tu",
        type=Path,
        default=None,
        help="Compile a specific translation unit only",
    )
    parser.add_argument("-j", "--jobs", type=_positive_jobs,
                        help="Concurrent compiler jobs (default: available logical CPUs)")
    args = parser.parse_args()
    args.repo_root = args.repo_root.resolve()
    if not args.out_dir.is_absolute():
        args.out_dir = args.repo_root / args.out_dir

    try:
        clang = find_clang()
        print(f"Using Clang compiler: {clang}")
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.tu:
        src_file = (args.tu if args.tu.is_absolute() else args.repo_root / args.tu).resolve()
        try:
            rel = src_file.relative_to(args.repo_root / "src")
        except ValueError:
            rel = Path(src_file.name)
        out_obj = args.out_dir / rel.with_suffix(".o")
        print(f"Compiling {src_file} -> {out_obj}...")
        res = ensure_tu_armv6k(src_file, out_obj, repo_root=args.repo_root, force=args.force)
        if res.returncode == 0:
            print("OK")
            sys.exit(0)
        else:
            print(res.stderr, file=sys.stderr)
            sys.exit(1)

    jobs = args.jobs if args.jobs is not None else default_job_count()
    print(f"Compiling all translation units to 3DS ARMv6K (up to {jobs} parallel jobs)...")
    start = time.perf_counter()
    result = compile_all_armv6k(
        repo_root=args.repo_root, out_dir=args.out_dir, force=args.force, jobs=jobs
    )
    print(f"Results: {result['succeeded']}/{result['total']} succeeded.")
    print(f"Compiled: {result['compiled_count']}; up-to-date: {result['cached_count']}.")
    print(f"Elapsed: {time.perf_counter() - start:.2f}s; workers: {result['jobs']}.")

    if result["failed"]:
        print(f"\n{len(result['failed'])} translation unit(s) failed:", file=sys.stderr)
        for path, err in result["failed"]:
            print(f"--- {path} ---", file=sys.stderr)
            print(err, file=sys.stderr)
        sys.exit(1)

    print("All translation units compiled successfully!")


if __name__ == "__main__":
    main()
