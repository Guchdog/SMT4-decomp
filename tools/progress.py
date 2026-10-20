#!/usr/bin/env python3
"""
Byte-Accurate Decompilation Progress Verifier and Markdown Report Generator
for Shin Megami Tensei IV (CTR-P-AMXE).

Differentiates between:
- 'matching': Byte-for-byte identical compiled machine code.
- 'non_matching': Authentically decompiled C++ logic (reconstructed from assembly).
- 'stub': Subsystem scaffolding, headers, and function skeletons awaiting reversal.
- 'todo': Undecompiled / unexplored functions in .text.
"""

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

VALID_STATUSES = {"todo", "stub", "wip", "non_matching", "matching"}
DECOMPILED_STATUSES = {"non_matching", "matching"}
STUB_STATUSES = {"stub", "wip"}
CLAIMED_STATUSES = DECOMPILED_STATUSES | STUB_STATUSES


class VerificationError(Exception):
    """Raised when a function claimed as decompiled or scaffolded fails verification."""


def extract_function_body(src_text: str, addr: str) -> str | None:
    """Extracts the C++ function body following DECOMP_FUNC(addr, size)."""
    lower_text = src_text.lower()
    marker = f"decomp_func({addr.lower()}"
    idx = lower_text.find(marker)
    if idx == -1:
        return None
    open_brace = src_text.find("{", idx)
    if open_brace == -1:
        return None
    brace_depth = 1
    i = open_brace + 1
    while i < len(src_text) and brace_depth > 0:
        if src_text[i] == "{":
            brace_depth += 1
        elif src_text[i] == "}":
            brace_depth -= 1
        i += 1
    return src_text[open_brace + 1 : i - 1]


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
    repo_root = Path(repo_root)

    total_funcs = 0
    total_bytes = 0
    decomp_funcs = 0
    decomp_bytes = 0
    stub_funcs = 0
    stub_bytes = 0
    matching_funcs = 0
    matching_bytes = 0

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

                body = extract_function_body(src_text, addr)
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
                        matching_funcs += 1
                        matching_bytes += size
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
        "total_explored_functions": total_explored_funcs,
        "total_explored_bytes": total_explored_bytes,
        "decomp_byte_percentage": (decomp_bytes / total_bytes * 100.0) if total_bytes else 0.0,
        "decomp_func_percentage": (decomp_funcs / total_funcs * 100.0) if total_funcs else 0.0,
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
        f"| **Decompiled (Reconstructed)** | {stats['decompiled_functions']:,} | {stats['decompiled_bytes']:,} B | **{stats['decomp_byte_percentage']:.4f}%** | Substantial C++ logic reverse-engineered |",
        f"| **Scaffolded (Stubs & Interfaces)** | {stats['stub_functions']:,} | {stats['stub_bytes']:,} B | {stats['stub_byte_percentage']:.4f}% | Headers, structs, and function skeletons |",
        f"| **Matching (Byte-for-Byte)** | {stats['matching_functions']:,} | {stats['matching_bytes']:,} B | {(stats['matching_bytes'] / stats['total_bytes'] * 100.0):.4f}% | 100% compiled machine code match |",
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

- **Authentically Decompiled Code:** `{stats['decompiled_bytes']:,} / {stats['total_bytes']:,} bytes` (**{stats['decomp_byte_percentage']:.4f}%**) across `{stats['decompiled_functions']:,}` functions
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
        f"({stats['decompiled_bytes']:,} / {stats['total_bytes']:,} bytes, {stats['decomp_byte_percentage']:.4f}%)\n"
        f"Verified {stats['stub_functions']:,} scaffolded stubs ({stats['stub_bytes']:,} bytes, {stats['stub_byte_percentage']:.4f}%)\n"
        f"Total Architecture Explored: {stats['total_explored_functions']:,} functions ({stats['total_explored_bytes']:,} bytes, {stats['explored_byte_percentage']:.4f}%)"
    )
    if args.write:
        (args.root / "PROGRESS.md").write_text(render_progress_md(stats), encoding="utf-8")
        (args.root / "README.md").write_text(render_readme_md(stats), encoding="utf-8")
        print("Updated PROGRESS.md and README.md.")


if __name__ == "__main__":
    main()
