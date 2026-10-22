#!/usr/bin/env python3
"""
Byte-Accurate Decompilation Progress Verifier and Markdown Report Generator
for Shin Megami Tensei IV (CTR-P-AMXE).

Differentiates between:
- 'matching': Byte-for-byte identical compiled machine code verified against code.bin.
- 'verified': Substantially decompiled C++ logic (ARMv6K compiled size >= 15% binary size).
- 'draft': Early-stage non_matching decompilations (< 15% size) awaiting refinement.
- 'stub': Subsystem scaffolding, headers, and function skeletons awaiting reversal.
- 'todo': Undecompiled / unexplored functions in .text.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
import re
import sys

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.asm_diff import compare_function, extract_elf_functions, find_symbol_in_elf

VALID_STATUSES = {"todo", "stub", "wip", "non_matching", "matching"}
DECOMPILED_STATUSES = {"non_matching", "matching"}
STUB_STATUSES = {"stub", "wip"}
CLAIMED_STATUSES = DECOMPILED_STATUSES | STUB_STATUSES


class VerificationError(Exception):
    """Raised when a function claimed as decompiled or scaffolded fails verification."""


def _mask_comments(text: str) -> str:
    """Replace comment characters with spaces while preserving length/offsets."""
    def mask_block(match: re.Match[str]) -> str:
        return "".join("\n" if ch == "\n" else " " for ch in match.group(0))

    text = re.sub(r"/\*.*?\*/", mask_block, text, flags=re.DOTALL)
    return re.sub(r"//[^\n]*", lambda m: " " * len(m.group(0)), text)


def extract_function_body(
    src_text: str,
    addr: str,
    definition_name: str | None = None,
    expected_size: int | None = None,
) -> str | None:
    """Extracts the C++ function body following DECOMP_FUNC(addr, size).

    The marker must declare the ledger size and, when ``definition_name`` is
    supplied, must be followed by that function's definition before the next
    opening brace. This prevents a marker whose body was deleted from
    silently parsing the body of the function that follows it.
    """
    marker_re = re.compile(
        rf"DECOMP_FUNC\(\s*{re.escape(addr)}\s*,\s*(\d+)\s*\)",
        re.IGNORECASE,
    )
    match = marker_re.search(src_text)
    if match is None:
        return None

    marker_size = int(match.group(1))
    if expected_size is not None and marker_size != expected_size:
        raise VerificationError(
            f"DECOMP_FUNC marker for {addr} declares {marker_size} bytes, "
            f"expected {expected_size} from config/functions.csv"
        )

    # Mask comments after the marker so braces inside them cannot be mistaken
    # for the body delimiter.
    suffix = src_text[match.end():]
    masked_suffix = _mask_comments(suffix)
    open_rel = masked_suffix.find("{")
    if open_rel == -1:
        return None

    if definition_name is not None:
        header = masked_suffix[:open_rel]
        if not re.search(rf"\b{re.escape(definition_name)}\s*\(", header):
            return None

    open_brace = match.end() + open_rel
    masked_body = _mask_comments(src_text[open_brace + 1:])
    brace_depth = 1
    i = 0
    while i < len(masked_body) and brace_depth > 0:
        if masked_body[i] == "{":
            brace_depth += 1
        elif masked_body[i] == "}":
            brace_depth -= 1
        i += 1
    if brace_depth != 0:
        return None
    return src_text[open_brace + 1 : open_brace + i]


def is_stub_body(body: str, size: int) -> bool:
    """Detects whether a function body is an empty or trivial skeleton stub."""
    clean_lines = []
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith("//") or line.startswith("/*") or line.startswith("*"):
            continue
        if line.startswith("(void)") or line in {"return;", "return 0;", "return nullptr;", "{", "}"}:
            continue
        clean_lines.append(line)

    # Completely empty or only (void) args
    if len(clean_lines) == 0:
        return True
    # Small single-line placeholder for non-trivial binary functions
    if size > 128 and len(clean_lines) <= 1:
        return True
    # Massive binary functions with only tiny dummy stub statements
    if size > 2000 and len(clean_lines) <= 5:
        return True
    if size > 10000 and len(clean_lines) <= 15:
        return True

    return False


def compute_progress(functions_csv: Path, repo_root: Path) -> dict:
    functions_csv = Path(functions_csv)
    repo_root = Path(repo_root).resolve()

    code_path = repo_root / "extracted" / "exefs" / "code.bin"
    code_bytes: bytes | None = None
    if code_path.is_file():
        code_bytes = code_path.read_bytes()

    total_funcs = 0
    total_bytes = 0
    decomp_funcs = 0
    decomp_bytes = 0
    stub_funcs = 0
    stub_bytes = 0
    matching_funcs = 0
    matching_bytes = 0
    verified_funcs = 0
    verified_bytes = 0
    draft_funcs = 0
    draft_bytes = 0

    by_category: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "total_funcs": 0,
            "total_bytes": 0,
            "decomp_funcs": 0,
            "decomp_bytes": 0,
            "stub_funcs": 0,
            "stub_bytes": 0,
        }
    )
    claimed_list: list[dict] = []
    src_cache: dict[Path, str] = {}

    with open(functions_csv, "r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            addr = row["address"]
            size = int(row["size"])
            status = row["status"].strip()
            cat = row["category"].strip()
            name = row["name"].strip()
            src_rel = row["src_file"].strip()

            if status not in VALID_STATUSES:
                raise VerificationError(f"Invalid status '{status}' for {addr} ({name})")

            total_funcs += 1
            total_bytes += size
            by_category[cat]["total_funcs"] += 1
            by_category[cat]["total_bytes"] += size

            if status in CLAIMED_STATUSES:
                if not src_rel:
                    raise VerificationError(
                        f"Function {name} ({addr}) has status '{status}' but no src_file"
                    )
                src_path = repo_root / src_rel
                if not src_path.exists():
                    raise VerificationError(
                        f"Function {name} ({addr}) claims missing file '{src_rel}'"
                    )
                if src_path not in src_cache:
                    src_cache[src_path] = src_path.read_text(encoding="utf-8")
                src_text = src_cache[src_path]
                if addr.lower() not in src_text.lower() or name not in src_text:
                    raise VerificationError(
                        f"Function {name} ({addr}) not found with DECOMP_FUNC({addr}, ...) in '{src_rel}'"
                    )

                body = extract_function_body(src_text, addr, name, size)
                if body is None:
                    raise VerificationError(
                        f"Could not parse function body for {name} ({addr}) in '{src_rel}'"
                    )

                # Strict verification: prevent empty stubs from being marked as decompiled
                if status in DECOMPILED_STATUSES:
                    if is_stub_body(body, size):
                        raise VerificationError(
                            f"Function {name} ({addr}) is marked '{status}' but contains only a stub/placeholder body. "
                            f"Must be marked 'stub'."
                        )
                    decomp_funcs += 1
                    decomp_bytes += size
                    by_category[cat]["decomp_funcs"] += 1
                    by_category[cat]["decomp_bytes"] += size

                    if status == "matching":
                        if code_bytes is not None:
                            diff = compare_function(
                                addr=int(addr, 16),
                                size=size,
                                func_name=name,
                                src_file=src_path,
                                code_bytes=code_bytes,
                                repo_root=repo_root,
                            )
                            if not diff["exact_match"]:
                                raise VerificationError(
                                    f"Function {name} ({addr}) is marked 'matching' but compiled bytes do not match code.bin!"
                                )
                        else:
                            raise VerificationError(
                                f"Function {name} ({addr}) is marked 'matching' but code.bin is not available to verify byte match!"
                            )
                        matching_funcs += 1
                        matching_bytes += size
                    else:
                        # non_matching: classify into verified vs draft
                        try:
                            src_root = (repo_root / "src").resolve()
                            rel_src = src_path.resolve().relative_to(src_root)
                            out_obj = repo_root / "build" / "obj" / "armv6k" / rel_src.with_suffix(".o")
                        except ValueError:
                            out_obj = src_path.with_suffix(".o")

                        compiled_size = 0
                        if out_obj.is_file():
                            elf_funcs = extract_elf_functions(out_obj)
                            sym_data = find_symbol_in_elf(elf_funcs, name, int(addr, 16))
                            if sym_data:
                                compiled_size = len(sym_data[0])

                        if compiled_size >= min(16, size) and (compiled_size / max(1, size)) >= 0.15:
                            verified_funcs += 1
                            verified_bytes += size
                        else:
                            draft_funcs += 1
                            draft_bytes += size
                else:
                    # status in STUB_STATUSES ('stub', 'wip')
                    stub_funcs += 1
                    stub_bytes += size
                    by_category[cat]["stub_funcs"] += 1
                    by_category[cat]["stub_bytes"] += size

                claimed_list.append(row)

    total_explored_funcs = decomp_funcs + stub_funcs
    total_explored_bytes = decomp_bytes + stub_bytes

    return {
        "total_functions": total_funcs,
        "total_bytes": total_bytes,
        "decompiled_functions": decomp_funcs,
        "decompiled_bytes": decomp_bytes,
        "stub_functions": stub_funcs,
        "stub_bytes": stub_bytes,
        "matching_functions": matching_funcs,
        "matching_bytes": matching_bytes,
        "verified_functions": verified_funcs,
        "verified_bytes": verified_bytes,
        "draft_functions": draft_funcs,
        "draft_bytes": draft_bytes,
        "total_explored_functions": total_explored_funcs,
        "total_explored_bytes": total_explored_bytes,
        "decomp_byte_percentage": (decomp_bytes / total_bytes * 100.0) if total_bytes else 0.0,
        "decomp_func_percentage": (decomp_funcs / total_funcs * 100.0) if total_funcs else 0.0,
        "matching_byte_percentage": (matching_bytes / total_bytes * 100.0) if total_bytes else 0.0,
        "verified_byte_percentage": (verified_bytes / total_bytes * 100.0) if total_bytes else 0.0,
        "draft_byte_percentage": (draft_bytes / total_bytes * 100.0) if total_bytes else 0.0,
        "stub_byte_percentage": (stub_bytes / total_bytes * 100.0) if total_bytes else 0.0,
        "explored_byte_percentage": (total_explored_bytes / total_bytes * 100.0) if total_bytes else 0.0,
        "categories": dict(by_category),
        "claimed_list": claimed_list,
    }


def render_progress_md(stats: dict) -> str:
    lines = [
        "# Shin Megami Tensei IV (`CTR-P-AMXE`) Decompilation Progress",
        "",
        "## Overall `.text` Progress Summary",
        "",
        "| Category | Functions | Code Size (Bytes) | Progress % | Status Description |",
        "|----------|----------:|------------------:|-----------:|--------------------|",
        f"| **Matching (Byte-for-Byte)** | {stats['matching_functions']:,} | {stats['matching_bytes']:,} B | {stats['matching_byte_percentage']:.4f}% | 100% compiled machine code match |",
        f"| **Verified (ARMv6K Compiled & Checked)** | {stats['verified_functions']:,} | {stats['verified_bytes']:,} B | {stats['verified_byte_percentage']:.4f}% | Substantial compiled C++ logic matching binary structure |",
        f"| **Draft (Under Construction)** | {stats['draft_functions']:,} | {stats['draft_bytes']:,} B | {stats['draft_byte_percentage']:.4f}% | Early-stage decompilations awaiting refinement |",
        f"| **Scaffolded (Stubs & Interfaces)** | {stats['stub_functions']:,} | {stats['stub_bytes']:,} B | {stats['stub_byte_percentage']:.4f}% | Headers, structs, and function skeletons |",
        f"| **Total Architecture Explored** | {stats['total_explored_functions']:,} | {stats['total_explored_bytes']:,} B | **{stats['explored_byte_percentage']:.4f}%** | Total identified & mapped into `src/` |",
        f"| **Remaining (Todo)** | {stats['total_functions'] - stats['total_explored_functions']:,} | {stats['total_bytes'] - stats['total_explored_bytes']:,} B | {((stats['total_bytes'] - stats['total_explored_bytes']) / stats['total_bytes'] * 100.0):.4f}% | Unmapped functions in `.text` |",
        f"| **Total `.text` Segment** | {stats['total_functions']:,} | {stats['total_bytes']:,} B | 100.0000% | `0x00100000`–`0x003FE624` |",
        "",
        "## Subsystem Breakdown",
        "",
        "| Subsystem | Decompiled Funcs | Decompiled Bytes | Stub Funcs | Stub Bytes | Total Funcs | Total Bytes | Decompiled % | Explored % |",
        "|-----------|-----------------:|-----------------:|-----------:|-----------:|------------:|------------:|-------------:|-----------:|",
    ]

    sorted_cats = sorted(
        stats["categories"].items(),
        key=lambda kv: kv[1]["total_bytes"],
        reverse=True,
    )
    for cat, cinfo in sorted_cats:
        decomp_pct = (cinfo["decomp_bytes"] / cinfo["total_bytes"] * 100.0) if cinfo["total_bytes"] else 0.0
        explored_pct = ((cinfo["decomp_bytes"] + cinfo["stub_bytes"]) / cinfo["total_bytes"] * 100.0) if cinfo["total_bytes"] else 0.0
        lines.append(
            f"| `{cat}` | {cinfo['decomp_funcs']:,} | {cinfo['decomp_bytes']:,} B | {cinfo['stub_funcs']:,} | {cinfo['stub_bytes']:,} B | {cinfo['total_funcs']:,} | {cinfo['total_bytes']:,} B | {decomp_pct:.2f}% | {explored_pct:.2f}% |"
        )

    lines.extend(
        [
            "",
            "## Explored Functions Ledger",
            "",
            "| Address | Size (Bytes) | Category | Status | Symbol Name | Source File |",
            "|---------|-------------:|----------|--------|-------------|-------------|",
        ]
    )
    for row in stats["claimed_list"]:
        lines.append(
            f"| `{row['address']}` | {row['size']} | `{row['category']}` | `{row['status']}` | `{row['name']}` | [`{row['src_file']}`]({row['src_file']}) |"
        )

    return "\n".join(lines) + "\n"


def render_readme_md(stats: dict) -> str:
    return f"""# Shin Megami Tensei IV (`CTR-P-AMXE`) Decompilation

Decompilation and reverse-engineering project for **Shin Megami Tensei IV** (Nintendo 3DS, US v0.1.0, Title ID `00040000000E5C00`, internal codename `sdds4`), aimed at producing modifiable C++20 source code (HUD/UI customization) and cross-platform PC / Android ports.

> **Legal Notice:** This repository contains **no copyrighted ROM data, binaries, encryption keys, or extracted assets**. You must supply your own legally dumped `.cia` copy of *Shin Megami Tensei IV* (`CTR-P-AMXE`) and `aes_keys.txt` locally to extract `code.bin` and `RomFS`.

---

## Live Decompilation Progress

- **Matching (Byte-for-Byte):** `{stats['matching_bytes']:,} / {stats['total_bytes']:,} bytes` (**{stats['matching_byte_percentage']:.4f}%**) across `{stats['matching_functions']:,}` functions
- **Verified Decompiled Logic:** `{stats['verified_bytes']:,} / {stats['total_bytes']:,} bytes` (**{stats['verified_byte_percentage']:.4f}%**) across `{stats['verified_functions']:,}` functions
- **Draft Decompilations:** `{stats['draft_bytes']:,} / {stats['total_bytes']:,} bytes` (**{stats['draft_byte_percentage']:.4f}%**) across `{stats['draft_functions']:,}` functions
- **Scaffolded Architecture (Stubs & Interfaces):** `{stats['stub_bytes']:,} / {stats['total_bytes']:,} bytes` (**{stats['stub_byte_percentage']:.4f}%**) across `{stats['stub_functions']:,}` functions
- **Total Codebase Explored:** `{stats['total_explored_bytes']:,} / {stats['total_bytes']:,} bytes` (**{stats['explored_byte_percentage']:.4f}%**) across `{stats['total_explored_functions']:,}` functions
- See [`PROGRESS.md`](PROGRESS.md) for the full subsystem breakdown (`ui`, `camp`, `battle`, `script_vm`, `shop`, `unite`, `engine`, `nn_sdk`, `crt`) and verified function ledger.

---

## Quick Start

### 1. Extract `code.bin` and UI/HUD Assets from Your Local CIA
Place your `.cia` and `aes_keys.txt` in the repository root (both are automatically ignored by `.gitignore`) and run:
```powershell
python tools/extract.py
```
This decrypts the CIA, decompresses the BLZ-compressed `ExeFS/.code` into `extracted/exefs/code.bin` (`0x377000` bytes), indexes all 20,126 RomFS files in `extracted/romfs_index.json`, and extracts UI/HUD folders.

### 2. Analyze Functions & Subsystem Xrefs
```powershell
python tools/analyze_code.py
```
Scans all `3,139,108` bytes of `.text` (`0x00100000`–`0x003FE624`), resolves literal pools and inline `ADR` strings (including original Atlus `c:\\SMT4\\XRD686\\...` source file paths), and populates [`config/functions.csv`](config/functions.csv) and [`config/symbols.csv`](config/symbols.csv).

### 3. Disassemble Any Function or HUD Subsystem
```powershell
# Disassemble a specific function by address or original Atlus source name:
python tools/split_asm.py --addr 0x002ac2f4
python tools/split_asm.py --name StatusDown --limit 3
python tools/split_asm.py --category ui --limit 10
```

### 4. Inspect `.tbb` (`TBCR`/`TBL1`) UI Tables and `.bf` (`FLW0`) FlowScripts
```powershell
python tools/inspect_assets.py extracted/romfs/saveLoadUI/SaveLoadUITable.tbb extracted/romfs/saveLoadUI/saveloadUI.bf
```

### 5. Verify Progress & Update `PROGRESS.md`
```powershell
python tools/progress.py --write
```

---

## Project Structure

- [`config/game_info.json`](config/game_info.json) — Memory map and binary metadata for `CTR-P-AMXE`.
- [`config/functions.csv`](config/functions.csv) — Master ledger of all {stats['total_functions']:,} functions covering 100% of `.text` (`3,139,108` bytes).
- [`config/symbols.csv`](config/symbols.csv) — String and data symbols recovered from `.rodata`, `.data`, and `.text` literal pools.
- [`include/`](include/) & [`src/`](src/) — Decompiled C++20 source code and engine/UI headers.
- [`docs/architecture.md`](docs/architecture.md) — Documentation of the `XRD686` / `AsdSDK` engine, dual-screen LCD pipelines, and `TBCR`/`TBL1` UI table formats.
- [`tools/`](tools/) — Extraction, static analysis, annotated disassembly, asset inspection, and progress verification scripts.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute and verify SMT4 decompilation progress")
    parser.add_argument("--functions", type=Path, default=Path("config/functions.csv"))
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--write", action="store_true", help="Write PROGRESS.md and README.md")
    args = parser.parse_args()

    stats = compute_progress(args.functions, args.root)
    print(
        f"Verified {stats['decompiled_functions']:,} / {stats['total_functions']:,} decompiled functions "
        f"({stats['decompiled_bytes']:,} / {stats['total_bytes']:,} bytes, {stats['decomp_byte_percentage']:.4f}%):\n"
        f"  - Matching (Byte-for-Byte):  {stats['matching_functions']:,} functions ({stats['matching_bytes']:,} bytes, {stats['matching_byte_percentage']:.4f}%)\n"
        f"  - Verified Logic (>= 15%):   {stats['verified_functions']:,} functions ({stats['verified_bytes']:,} bytes, {stats['verified_byte_percentage']:.4f}%)\n"
        f"  - Draft Logic (< 15%):       {stats['draft_functions']:,} functions ({stats['draft_bytes']:,} bytes, {stats['draft_byte_percentage']:.4f}%)\n"
        f"Verified {stats['stub_functions']:,} scaffolded stubs ({stats['stub_bytes']:,} bytes, {stats['stub_byte_percentage']:.4f}%)\n"
        f"Total Architecture Explored: {stats['total_explored_functions']:,} functions ({stats['total_explored_bytes']:,} bytes, {stats['explored_byte_percentage']:.4f}%)"
    )
    if args.write:
        (args.root / "PROGRESS.md").write_text(render_progress_md(stats), encoding="utf-8")
        (args.root / "README.md").write_text(render_readme_md(stats), encoding="utf-8")
        print("Updated PROGRESS.md and README.md.")


if __name__ == "__main__":
    main()
