#!/usr/bin/env python3
"""
Byte-Accurate Decompilation Progress Verifier and Markdown Report Generator
for Shin Megami Tensei IV (CTR-P-AMXE).

Differentiates between:
- 'matching': Byte-for-byte identical compiled machine code verified against code.bin.
- 'compiled': ARMv6K compiled size >= 15% binary size; no semantic verification.
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
from tools.build_check import ensure_tu_armv6k

VALID_STATUSES = {"todo", "stub", "wip", "non_matching", "matching", "matching_span"}
DECOMPILED_STATUSES = {"non_matching", "matching"}
SPAN_STATUSES = {"matching_span"}
STUB_STATUSES = {"stub", "wip"}
CLAIMED_STATUSES = DECOMPILED_STATUSES | SPAN_STATUSES | STUB_STATUSES
# Number of exact-matching functions converted from assembly wrappers to typed
# C++ in the semantic reconstruction batches. Keep this milestone count in sync
# when accepting or reverting such a batch; it is distinct from size coverage.
SEMANTIC_CPP_RECONSTRUCTIONS = 60


class VerificationError(Exception):
    """Raised when a function claimed as decompiled or scaffolded fails verification."""


def _mask_comments(text: str) -> str:
    """Replace comment characters with spaces while preserving length/offsets."""
    def mask_block(match: re.Match[str]) -> str:
        return "".join("\n" if ch == "\n" else " " for ch in match.group(0))

    text = re.sub(r"/\*.*?\*/", mask_block, text, flags=re.DOTALL)
    return re.sub(r"//[^\n]*", lambda m: " " * len(m.group(0)), text)


_NON_FUNCTION_PAREN_WORDS = {
    "alignas",
    "alignof",
    "asm",
    "catch",
    "decltype",
    "if",
    "noexcept",
    "requires",
    "sizeof",
    "static_assert",
    "switch",
    "throw",
    "while",
    "__asm__",
    "__attribute__",
    "__declspec",
    "__extension__",
}
_ASM_ALIAS_RE = re.compile(
    r"\b(?:asm|__asm__)\s*\(\s*\"([^\"]+)\"\s*\)"
)
_LEDGER_SPELLING_PIN_RE = re.compile(
    r'\[\[\s*deprecated\s*\(\s*"([^\"]+)"\s*\)\s*\]\]'
)


def _function_declaration_identity(declaration: str) -> tuple[str, str | None] | None:
    """Return the C identifier and optional explicit asm symbol for a declaration."""
    names: list[str] = []
    depth = 0
    quote: str | None = None
    escaped = False

    for i, char in enumerate(declaration):
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in {'"', "'"}:
            quote = char
            continue
        if char == "(":
            if depth == 0:
                name_match = re.search(r"([A-Za-z_]\w*)\s*$", declaration[:i])
                if name_match:
                    name = name_match.group(1)
                    if name not in _NON_FUNCTION_PAREN_WORDS:
                        names.append(name)
            depth += 1
        elif char == ")" and depth:
            depth -= 1

    if not names:
        return None
    alias_match = _ASM_ALIAS_RE.search(declaration)
    alias = alias_match.group(1) if alias_match else None
    return names[-1], alias


def _header_defines_symbol(
    header: str, definition_name: str, address: str
) -> bool:
    """Check that the definition before the body identifies the ledger entry."""
    declaration_parts = header.split(";")
    final_declaration = declaration_parts[-1]
    final_identity = _function_declaration_identity(final_declaration)
    declarations = [
        _function_declaration_identity(part) for part in declaration_parts
    ]
    declarations = [identity for identity in declarations if identity is not None]
    if final_identity is None:
        return False

    c_identifier, _ = final_identity
    if c_identifier == definition_name:
        return True

    # An alias is valid only when a declaration for this exact C identifier
    # explicitly maps it to the ledger name. This rejects a detached prototype
    # followed by an unrelated function definition.
    if any(
        declared_identifier == c_identifier and alias == definition_name
        for declared_identifier, alias in declarations
    ):
        return True

    # A small number of legacy definitions pin the ledger spelling in a
    # deprecated attribute. Accept only the exact symbol/address pin attached
    # to the definition immediately before the body, never an earlier prototype.
    pin_match = _LEDGER_SPELLING_PIN_RE.search(final_declaration)
    if pin_match is None:
        return False
    expected_pin = re.fullmatch(
        rf"{re.escape(definition_name)}\s*\(\s*(0[xX][0-9a-fA-F]+)\s*\)"
        rf"\s+ledger spelling pin",
        pin_match.group(1),
    )
    return (
        expected_pin is not None
        and int(expected_pin.group(1), 16) == int(address, 16)
    )


def extract_function_body(
    src_text: str,
    addr: str,
    definition_name: str | None = None,
    expected_size: int | None = None,
    marker_type: str = "DECOMP_FUNC",
) -> str | None:
    """Extract the C++ body following a DECOMP_FUNC or DECOMP_SPAN marker.

    The marker must declare the ledger size and, when ``definition_name`` is
    supplied, must be followed by that function's definition before the next
    opening brace. This prevents a marker whose body was deleted from
    silently parsing the body of the function that follows it.
    """
    marker_re = re.compile(
        rf"{re.escape(marker_type)}\(\s*{re.escape(addr)}\s*,\s*(\d+)\s*\)",
        re.IGNORECASE,
    )
    match = marker_re.search(src_text)
    if match is None:
        return None

    marker_size = int(match.group(1))
    if expected_size is not None and marker_size != expected_size:
        raise VerificationError(
            f"{marker_type} marker for {addr} declares {marker_size} bytes, "
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
        if not _header_defines_symbol(header, definition_name, addr):
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
    masked = _mask_comments(body)
    clean_lines = []
    for line in masked.splitlines():
        line = line.strip()
        if not line:
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
    """Measure source coverage and exact matches.

    ``compiled_*`` measures only compilation and a 15% size threshold. The
    legacy ``verified_*`` fields are compatibility aliases for those metrics;
    neither establishes semantic equivalence.
    """
    functions_csv = Path(functions_csv)
    repo_root = Path(repo_root).resolve()

    code_path = repo_root / "extracted" / "exefs" / "code.bin"
    code_bytes: bytes | None = None
    if code_path.is_file():
        code_bytes = code_path.read_bytes()

    total_funcs = 0
    total_bytes = 0
    total_spans = 0
    total_span_bytes = 0
    decomp_funcs = 0
    decomp_bytes = 0
    stub_funcs = 0
    stub_bytes = 0
    matching_funcs = 0
    matching_bytes = 0
    matching_spans = 0
    matching_span_bytes = 0
    verified_funcs = 0
    verified_bytes = 0
    draft_funcs = 0
    draft_bytes = 0

    by_category: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "total_funcs": 0,
            "total_bytes": 0,
            "total_spans": 0,
            "total_span_bytes": 0,
            "decomp_funcs": 0,
            "decomp_bytes": 0,
            "matching_funcs": 0,
            "matching_bytes": 0,
            "matching_spans": 0,
            "matching_span_bytes": 0,
            "verified_funcs": 0,
            "verified_bytes": 0,
            "draft_funcs": 0,
            "draft_bytes": 0,
            "stub_funcs": 0,
            "stub_bytes": 0,
        }
    )
    claimed_list: list[dict] = []
    src_cache: dict[Path, str] = {}
    validated_objects: set[Path] = set()

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

            is_span = cat == "raw_span"
            if is_span and status != "matching_span":
                raise VerificationError(
                    f"Raw span {name} ({addr}) must use status 'matching_span', got '{status}'"
                )
            if status == "matching_span" and not is_span:
                raise VerificationError(
                    f"Span {name} ({addr}) must use category 'raw_span'"
                )

            if is_span:
                total_spans += 1
                total_span_bytes += size
                by_category[cat]["total_spans"] += 1
                by_category[cat]["total_span_bytes"] += size
            else:
                total_funcs += 1
                by_category[cat]["total_funcs"] += 1
            total_bytes += size
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
                marker_type = "DECOMP_SPAN" if is_span else "DECOMP_FUNC"
                if addr.lower() not in src_text.lower() or name not in src_text:
                    raise VerificationError(
                        f"Entry {name} ({addr}) not found with {marker_type}({addr}, ...) in '{src_rel}'"
                    )

                body = extract_function_body(
                    src_text, addr, name, size, marker_type=marker_type
                )
                if body is None:
                    raise VerificationError(
                        f"Could not parse {'raw span' if is_span else 'function'} body for "
                        f"{name} ({addr}) in '{src_rel}'"
                    )

                if is_span:
                    if code_bytes is None:
                        raise VerificationError(
                            f"Raw span {name} ({addr}) is marked 'matching_span' but code.bin is not available"
                        )
                    diff = compare_function(
                        addr=int(addr, 16),
                        size=size,
                        func_name=name,
                        src_file=src_path,
                        code_bytes=code_bytes,
                        repo_root=repo_root,
                        validated_object_cache=validated_objects,
                    )
                    if not diff["exact_match"]:
                        raise VerificationError(
                            f"Raw span {name} ({addr}) is marked 'matching_span' but compiled bytes do not match code.bin!"
                        )
                    matching_spans += 1
                    matching_span_bytes += size
                    matching_bytes += size
                    by_category[cat]["matching_spans"] += 1
                    by_category[cat]["matching_span_bytes"] += size
                    by_category[cat]["matching_bytes"] += size
                    claimed_list.append(row)
                    continue

                # Strict verification: an empty source body may be the complete
                # reconstruction of a real ``bx lr`` function.  Matching claims
                # therefore get checked against the original bytes before the
                # source-level placeholder heuristic is applied.  Non-matching
                # empty bodies are still rejected as stubs.
                if status in DECOMPILED_STATUSES:
                    if status != "matching" and is_stub_body(body, size):
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
                                validated_object_cache=validated_objects,
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
                        by_category[cat]["matching_funcs"] += 1
                        by_category[cat]["matching_bytes"] += size
                    else:
                        # Classify size coverage only; this does not verify logic.
                        try:
                            src_root = (repo_root / "src").resolve()
                            rel_src = src_path.resolve().relative_to(src_root)
                            out_obj = repo_root / "build" / "obj" / "armv6k" / rel_src.with_suffix(".o")
                        except ValueError:
                            out_obj = src_path.with_suffix(".o")

                        cache_key = out_obj.resolve()
                        if cache_key not in validated_objects or not out_obj.is_file():
                            result = ensure_tu_armv6k(src_path, out_obj, repo_root=repo_root)
                            if result.returncode != 0 or not out_obj.is_file():
                                raise VerificationError(
                                    f"Compilation failed for {name} ({addr}): {result.stderr.strip()}"
                                )
                            validated_objects.add(cache_key)
                        elf_funcs = extract_elf_functions(out_obj)
                        sym_data = find_symbol_in_elf(elf_funcs, name, int(addr, 16))
                        if sym_data is None:
                            raise VerificationError(f"Compiled symbol missing for {name} ({addr})")
                        compiled_size = len(sym_data[0])

                        if compiled_size >= min(16, size) and (compiled_size / max(1, size)) >= 0.15:
                            verified_funcs += 1
                            verified_bytes += size
                            by_category[cat]["verified_funcs"] += 1
                            by_category[cat]["verified_bytes"] += size
                        else:
                            draft_funcs += 1
                            draft_bytes += size
                            by_category[cat]["draft_funcs"] += 1
                            by_category[cat]["draft_bytes"] += size
                else:
                    # status in STUB_STATUSES ('stub', 'wip')
                    stub_funcs += 1
                    stub_bytes += size
                    by_category[cat]["stub_funcs"] += 1
                    by_category[cat]["stub_bytes"] += size

                claimed_list.append(row)

    total_explored_funcs = decomp_funcs + stub_funcs
    total_explored_bytes = decomp_bytes + stub_bytes + matching_span_bytes
    for cinfo in by_category.values():
        cinfo["compiled_funcs"] = cinfo["verified_funcs"]
        cinfo["compiled_bytes"] = cinfo["verified_bytes"]

    return {
        "total_functions": total_funcs,
        "total_bytes": total_bytes,
        "total_spans": total_spans,
        "total_span_bytes": total_span_bytes,
        "decompiled_functions": decomp_funcs,
        "decompiled_bytes": decomp_bytes,
        "stub_functions": stub_funcs,
        "stub_bytes": stub_bytes,
        "matching_functions": matching_funcs,
        "matching_bytes": matching_bytes,
        "matching_spans": matching_spans,
        "matching_span_bytes": matching_span_bytes,
        "verified_functions": verified_funcs,
        "verified_bytes": verified_bytes,
        "compiled_functions": verified_funcs,
        "compiled_bytes": verified_bytes,
        "draft_functions": draft_funcs,
        "draft_bytes": draft_bytes,
        "total_explored_functions": total_explored_funcs,
        "total_explored_bytes": total_explored_bytes,
        "decomp_byte_percentage": (decomp_bytes / total_bytes * 100.0) if total_bytes else 0.0,
        "decomp_func_percentage": (decomp_funcs / total_funcs * 100.0) if total_funcs else 0.0,
        "matching_byte_percentage": (matching_bytes / total_bytes * 100.0) if total_bytes else 0.0,
        "verified_byte_percentage": (verified_bytes / total_bytes * 100.0) if total_bytes else 0.0,
        "compiled_byte_percentage": (verified_bytes / total_bytes * 100.0) if total_bytes else 0.0,
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
        "Primary goal: [editable C++ semantics](docs/functional-status.md). Byte identity is optional; the reference coverage below includes assembly/raw wrappers and is not semantic completion.",
        "",
        "## Reference `.text` Coverage Summary",
        "",
        "| Category | Functions | Code Size (Bytes) | Progress % | Status Description |",
        "|----------|----------:|------------------:|-----------:|--------------------|",
        f"| **Matching (Byte-for-Byte)** | {stats['matching_functions']:,} functions + {stats['matching_spans']:,} raw spans | {stats['matching_bytes']:,} B | **{stats['matching_byte_percentage']:.4f}%** | Exact ARMv6K bytes verified against code.bin |",
        f"| **Compiled Coverage (≥15% size)** | {stats['compiled_functions']:,} | {stats['compiled_bytes']:,} B | {stats['compiled_byte_percentage']:.4f}% | Compiles to ARMv6K ELF .o; size threshold only, logic unverified |",
        f"| **Draft Logic (<15% size)** | {stats['draft_functions']:,} | {stats['draft_bytes']:,} B | {stats['draft_byte_percentage']:.4f}% | Early draft reconstructions awaiting control-flow recovery |",
        f"| **Scaffolded (Stubs & Interfaces)** | {stats['stub_functions']:,} | {stats['stub_bytes']:,} B | {stats['stub_byte_percentage']:.4f}% | Headers, structs, and function skeletons |",
        f"| **Total Architecture Explored** | {stats['total_explored_functions']:,} functions + {stats['matching_spans']:,} raw spans | {stats['total_explored_bytes']:,} B | {stats['explored_byte_percentage']:.4f}% | Mapped into `src/` (functions and verified raw spans) |",
        f"| **Remaining (Todo)** | {stats['total_functions'] - stats['total_explored_functions']:,} functions | {stats['total_bytes'] - stats['total_explored_bytes']:,} B | {((stats['total_bytes'] - stats['total_explored_bytes']) / stats['total_bytes'] * 100.0):.4f}% | Unmapped `.text` bytes |",
        f"| **Total `.text` Segment** | {stats['total_functions']:,} functions + {stats['total_spans']:,} raw spans | {stats['total_bytes']:,} B | 100.0000% | `0x00100000`–`0x003FE624` |",
        "",
        "Compiled coverage and draft totals use original function sizes, not recovered instruction counts. Compilation and size do not establish behavioral equivalence. Matching functions and explicitly labeled raw spans are counted only after exact byte comparison with code.bin.",
        "",
        "Machine-readable `compiled_*` fields describe size coverage; legacy `verified_*` fields remain aliases for compatibility and do not mean verified logic.",
        "",
        "## Subsystem Breakdown",
        "",
        "| Subsystem | Matching | Compiled Coverage (≥15%) | Draft (<15%) | Stubs | Total Explored | Total Subsystem | Matching % | Explored % |",
        "|-----------|---------:|----------------:|-------------:|------:|---------------:|----------------:|-----------:|-----------:|",
    ]

    sorted_cats = sorted(
        stats["categories"].items(),
        key=lambda kv: kv[1]["total_bytes"],
        reverse=True,
    )
    for cat, cinfo in sorted_cats:
        matching_pct = (cinfo["matching_bytes"] / cinfo["total_bytes"] * 100.0) if cinfo["total_bytes"] else 0.0
        explored_bytes = cinfo["decomp_bytes"] + cinfo["stub_bytes"] + cinfo["matching_span_bytes"]
        explored_funcs = cinfo["decomp_funcs"] + cinfo["stub_funcs"]
        explored_pct = (explored_bytes / cinfo["total_bytes"] * 100.0) if cinfo["total_bytes"] else 0.0
        lines.append(
            f"| `{cat}` | {cinfo['matching_funcs']:,} ({cinfo['matching_bytes']:,} B) | {cinfo['verified_funcs']:,} ({cinfo['verified_bytes']:,} B) | {cinfo['draft_funcs']:,} ({cinfo['draft_bytes']:,} B) | {cinfo['stub_funcs']:,} ({cinfo['stub_bytes']:,} B) | {explored_funcs:,} ({explored_bytes:,} B) | {cinfo['total_funcs']:,} ({cinfo['total_bytes']:,} B) | {matching_pct:.4f}% | {explored_pct:.2f}% |"
        )

    lines.extend(
        [
            "",
            "## Explored Entries Ledger",
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

Decompilation and reverse-engineering project for **Shin Megami Tensei IV** (Nintendo 3DS, US v0.1.0, Title ID `00040000000E5C00`, internal codename `sdds4`), aimed at recovering modifiable C++20 source code. The current build targets 3DS ARMv6K objects and a static library; linking a runnable game and PC / Android ports are future work.

> **Legal Notice:** This repository contains **no copyrighted ROM data, binaries, encryption keys, or extracted assets**. You must supply your own legally dumped `.cia` copy of *Shin Megami Tensei IV* (`CTR-P-AMXE`) and `aes_keys.txt` locally to extract `code.bin` and `RomFS`.

---

## Primary goal: editable C++ semantics

Find and reconstruct readable C++ with supported behavior. Byte-for-byte identity is not an acceptance requirement. Prioritize coherent H1 behavior, differential/caller evidence, and integration; do not optimize the project around matching opcodes.

Follow the [functional status](docs/functional-status.md), [milestone plan](docs/reconstruction-milestones.md), and [per-function workflow](docs/function-reconstruction-workflow.md). The [generated candidate inventory](docs/semantic-inventory.md) measures experimental definitions and static evidence links, not equivalence or integration. H0 records a limited patched-game smoke test; H1 main-menu reconstruction remains active.

Use the [agent workflow](docs/agent-workflow.md) for bounded parallel contracts, implementation and independent review; the coordinator owns shared files, integration and the CPU budget.

Find new semantic work or review existing C++ for validation/integration:

```powershell
python tools/find_candidates.py --limit 20
python tools/find_candidates.py --include-existing-candidates --limit 20
```

## Reference byte coverage

- **Matching (Byte-for-Byte):** `{stats['matching_bytes']:,} / {stats['total_bytes']:,} bytes` (**{stats['matching_byte_percentage']:.4f}%**) across `{stats['matching_functions']:,}` functions and `{stats['matching_spans']:,}` explicitly labeled raw spans (each exact-checked against 3DS ARMv6K code.bin)
- **Readable C++ reconstructions:** `{SEMANTIC_CPP_RECONSTRUCTIONS}` functions have been converted from assembly wrappers to typed C++ while retaining byte-for-byte ARMv6K output. Recent batches cover engine state/accessors, UI and camp record updates, shop/texture comparators, Script VM helpers, queue/list operations, record initialization, float state updates, a zeroing helper, and a state getter. These semantic milestones are tracked separately from the size-based coverage categories below.
- **Compiled Coverage (≥15% size):** `{stats['compiled_bytes']:,} / {stats['total_bytes']:,} bytes` (**{stats['compiled_byte_percentage']:.4f}%**) across `{stats['compiled_functions']:,}` functions (ARMv6K compilation and size threshold only; logic unverified)
- **Draft Logic (<15% size):** `{stats['draft_bytes']:,} / {stats['total_bytes']:,} bytes` (**{stats['draft_byte_percentage']:.4f}%**) across `{stats['draft_functions']:,}` functions (early-stage draft reconstructions)
- **Scaffolded Architecture (Stubs & Interfaces):** `{stats['stub_bytes']:,} / {stats['total_bytes']:,} bytes` (**{stats['stub_byte_percentage']:.4f}%**) across `{stats['stub_functions']:,}` functions (headers, structs, function skeletons)
- **Total Codebase Explored:** `{stats['total_explored_bytes']:,} / {stats['total_bytes']:,} bytes` (**{stats['explored_byte_percentage']:.4f}%**) across `{stats['total_explored_functions']:,}` functions and `{stats['matching_spans']:,}` exact raw spans (all explored bytes mapped into `src/`)
- See [`PROGRESS.md`](PROGRESS.md) for the full subsystem breakdown (`ui`, `camp`, `battle`, `script_vm`, `shop`, `unite`, `engine`, `nn_sdk`, `crt`) and explored function ledger. Coverage totals use original function sizes and do not measure behavioral equivalence.

---

## Quick Start

Install Python dependencies with `python -m pip install -r requirements.txt`. Clang is required for ARM compilation; CMake and Ninja are required for the CMake build. See [development setup](docs/development.md) for compiler configuration, build commands, and tests. Run `python -m unittest discover -s tests -v` for tests; tests requiring private game files skip when those files are absent.

### 1. Extract `code.bin` and UI/HUD Assets from Your Local CIA
Place your `.cia` and `aes_keys.txt` in the repository root (both are automatically ignored by `.gitignore`) and run:
```powershell
python tools/extract.py
```
This auto-selects a CIA only when exactly one is present; otherwise pass `--cia path/to/game.cia`. It decrypts the CIA, decompresses the BLZ-compressed `ExeFS/.code` into `extracted/exefs/code.bin` (`0x377000` bytes), verifies its size and SHA-256 against the configured revision by default, indexes all 20,126 RomFS files in `extracted/romfs_index.json`, and extracts UI/HUD folders.

### 2. Analyze Functions & Subsystem Xrefs
```powershell
python tools/analyze_code.py
```
Scans all `3,139,108` bytes of `.text` (`0x00100000`–`0x003FE624`), resolves literal pools and inline `ADR` strings (including original Atlus `c:\\SMT4\\XRD686\\...` source file paths), and writes review proposals to `build/analysis/functions.csv`, `symbols.csv`, and `ledger_diff.json`. The curated files in `config/` are never overwritten; review boundary changes before manually accepting individual discoveries.

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
- [`config/functions.csv`](config/functions.csv) — Master ledger of {stats['total_functions']:,} callable functions and {stats['total_spans']:,} explicitly labeled non-function spans covering 100% of `.text` (`3,139,108` bytes).
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
        f"Recorded {stats['decompiled_functions']:,} / {stats['total_functions']:,} mapped function implementations (including assembly/raw wrappers) "
        f"({stats['decompiled_bytes']:,} / {stats['total_bytes']:,} bytes, {stats['decomp_byte_percentage']:.4f}%):\n"
        f"  - Matching (Byte-for-Byte):  {stats['matching_functions']:,} functions + {stats['matching_spans']:,} raw spans ({stats['matching_bytes']:,} bytes, {stats['matching_byte_percentage']:.4f}%)\n"
        f"  - Compiled Coverage (>=15%): {stats['compiled_functions']:,} functions ({stats['compiled_bytes']:,} bytes, {stats['compiled_byte_percentage']:.4f}%; logic unverified)\n"
        f"  - Draft Logic (< 15%):       {stats['draft_functions']:,} functions ({stats['draft_bytes']:,} bytes, {stats['draft_byte_percentage']:.4f}%)\n"
        f"Verified {stats['stub_functions']:,} scaffolded stubs ({stats['stub_bytes']:,} bytes, {stats['stub_byte_percentage']:.4f}%)\n"
        f"Total Architecture Explored: {stats['total_explored_functions']:,} functions + {stats['matching_spans']:,} raw spans ({stats['total_explored_bytes']:,} bytes, {stats['explored_byte_percentage']:.4f}%)"
    )
    if args.write:
        (args.root / "PROGRESS.md").write_text(render_progress_md(stats), encoding="utf-8")
        (args.root / "README.md").write_text(render_readme_md(stats), encoding="utf-8")
        print("Updated PROGRESS.md and README.md.")


if __name__ == "__main__":
    main()
