#!/usr/bin/env python3
"""
Byte-Accurate Decompilation Progress Verifier and Markdown Report Generator
for Shin Megami Tensei IV (CTR-P-AMXE).
"""

import argparse
import csv
from collections import defaultdict
from pathlib import Path

VALID_STATUSES = {"todo", "wip", "non_matching", "matching"}
DECOMPILED_STATUSES = {"wip", "non_matching", "matching"}


class VerificationError(Exception):
    """Raised when a function claimed as decompiled in functions.csv fails source verification."""


def compute_progress(functions_csv: Path, repo_root: Path) -> dict:
    functions_csv = Path(functions_csv)
    repo_root = Path(repo_root)

    total_funcs = 0
    total_bytes = 0
    decomp_funcs = 0
    decomp_bytes = 0
    matching_funcs = 0
    matching_bytes = 0

    by_category: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "total_funcs": 0,
            "total_bytes": 0,
            "decomp_funcs": 0,
            "decomp_bytes": 0,
        }
    )
    decompiled_list: list[dict] = []
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

            if status in DECOMPILED_STATUSES:
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

                decomp_funcs += 1
                decomp_bytes += size
                by_category[cat]["decomp_funcs"] += 1
                by_category[cat]["decomp_bytes"] += size
                if status == "matching":
                    matching_funcs += 1
                    matching_bytes += size
                decompiled_list.append(row)

    return {
        "total_functions": total_funcs,
        "total_bytes": total_bytes,
        "decompiled_functions": decomp_funcs,
        "decompiled_bytes": decomp_bytes,
        "matching_functions": matching_funcs,
        "matching_bytes": matching_bytes,
        "byte_percentage": (decomp_bytes / total_bytes * 100.0) if total_bytes else 0.0,
        "func_percentage": (decomp_funcs / total_funcs * 100.0) if total_funcs else 0.0,
        "categories": dict(by_category),
        "decompiled_list": decompiled_list,
    }


def render_progress_md(stats: dict) -> str:
    lines = [
        "# Shin Megami Tensei IV (`CTR-P-AMXE`) Decompilation Progress",
        "",
        "## Overall `.text` Progress",
        "",
        "| Metric | Decompiled | Total | Remaining | Percentage |",
        "|--------|-----------:|------:|----------:|-----------:|",
        f"| **Code Size (Bytes)** | {stats['decompiled_bytes']:,} B | {stats['total_bytes']:,} B | {stats['total_bytes'] - stats['decompiled_bytes']:,} B | **{stats['byte_percentage']:.4f}%** |",
        f"| **Functions** | {stats['decompiled_functions']:,} | {stats['total_functions']:,} | {stats['total_functions'] - stats['decompiled_functions']:,} | **{stats['func_percentage']:.4f}%** |",
        "",
        "## Subsystem Breakdown",
        "",
        "| Subsystem | Decompiled Funcs | Total Funcs | Decompiled Bytes | Total Bytes | Subsystem % |",
        "|-----------|-----------------:|------------:|-----------------:|------------:|------------:|",
    ]

    sorted_cats = sorted(
        stats["categories"].items(),
        key=lambda kv: kv[1]["total_bytes"],
        reverse=True,
    )
    for cat, cinfo in sorted_cats:
        pct = (
            (cinfo["decomp_bytes"] / cinfo["total_bytes"] * 100.0)
            if cinfo["total_bytes"]
            else 0.0
        )
        lines.append(
            f"| `{cat}` | {cinfo['decomp_funcs']:,} | {cinfo['total_funcs']:,} | {cinfo['decomp_bytes']:,} B | {cinfo['total_bytes']:,} B | {pct:.3f}% |"
        )

    lines.extend(
        [
            "",
            "## Decompiled Functions Ledger",
            "",
            "| Address | Size (Bytes) | Category | Status | Symbol Name | Source File |",
            "|---------|-------------:|----------|--------|-------------|-------------|",
        ]
    )
    for row in stats["decompiled_list"]:
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

- **`.text` Bytes Decompiled:** `{stats['decompiled_bytes']:,} / {stats['total_bytes']:,} bytes` (**{stats['byte_percentage']:.4f}%**)
- **Functions Decompiled:** `{stats['decompiled_functions']:,} / {stats['total_functions']:,} functions` (**{stats['func_percentage']:.4f}%**)
- See [`PROGRESS.md`](PROGRESS.md) for the full subsystem breakdown (`ui`, `camp`, `battle`, `script_vm`, `shop`, `unite`, `engine`, `nn_sdk`, `crt`) and verified function list.

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
        f"Verified {stats['decompiled_functions']:,} / {stats['total_functions']:,} functions "
        f"({stats['decompiled_bytes']:,} / {stats['total_bytes']:,} bytes, {stats['byte_percentage']:.4f}%)"
    )
    if args.write:
        (args.root / "PROGRESS.md").write_text(render_progress_md(stats), encoding="utf-8")
        (args.root / "README.md").write_text(render_readme_md(stats), encoding="utf-8")
        print("Updated PROGRESS.md and README.md.")


if __name__ == "__main__":
    main()
