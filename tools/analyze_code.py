#!/usr/bin/env python3
"""
ARMv6K Static Code Analyzer, Function Boundary Detector, Literal Pool Xref Resolver,
and Subsystem Categorizer for Shin Megami Tensei IV (code.bin).
"""

import argparse
import bisect
import csv
import json
import re
import struct
from collections import Counter, defaultdict
from pathlib import Path

TEXT_VADDR = 0x00100000
TEXT_SIZE = 0x002FE624
TEXT_END = TEXT_VADDR + TEXT_SIZE
TEXT_ALIGNED_SIZE = 0x002FF000

RODATA_VADDR = 0x003FF000
RODATA_SIZE = 0x0002BB78
RODATA_END = RODATA_VADDR + RODATA_SIZE
RODATA_ALIGNED_SIZE = 0x0002C000
RODATA_FILE_OFFSET = 0x002FF000

DATA_VADDR = 0x0042B000
DATA_SIZE = 0x0004B644
DATA_END = DATA_VADDR + DATA_SIZE
DATA_FILE_OFFSET = 0x0032B000

BSS_VADDR = 0x00477000
BSS_SIZE = 0x000797F0
BSS_END = BSS_VADDR + BSS_SIZE


def vaddr_to_offset(vaddr: int) -> int:
    if TEXT_VADDR <= vaddr < TEXT_VADDR + TEXT_ALIGNED_SIZE:
        return vaddr - TEXT_VADDR
    if RODATA_VADDR <= vaddr < RODATA_VADDR + RODATA_ALIGNED_SIZE:
        return RODATA_FILE_OFFSET + (vaddr - RODATA_VADDR)
    if DATA_VADDR <= vaddr < DATA_VADDR + 0x4C000:
        return DATA_FILE_OFFSET + (vaddr - DATA_VADDR)
    raise ValueError(f"Virtual address out of mapped code.bin range: 0x{vaddr:08x}")


def classify_string(s: str) -> str | None:
    low = s.lower()
    if any(
        kw in low
        for kw in (
            "nn::",
            "nn_gx_",
            "dmp_texenv",
            "nintendo",
            "ctr::",
            "fs:ldr",
            "fs:user",
            "mobiclip",
        )
    ):
        return "nn_sdk"
    if any(
        kw in low
        for kw in (
            "\\camp\\",
            "/camp",
            "gauntletappmenu",
            "camp",
            "demonica",
        )
    ):
        return "camp"
    if any(
        kw in low
        for kw in (
            "\\shop\\",
            "/shop",
            "shopmain",
            "shop_",
            "macca",
            "relic",
        )
    ):
        return "shop"
    if any(
        kw in low
        for kw in (
            "\\unite\\",
            "/unite",
            "fusion",
            "bible",
            "compendium",
            "devilbook",
        )
    ):
        return "unite"
    if any(
        kw in low
        for kw in (
            "\\battle\\",
            "/battle",
            "btlmain",
            "btlstage",
            "enemydraw",
            "btl ",
            "btl_",
            "damage",
            "press",
            "smirk",
        )
    ):
        return "battle"
    if any(
        kw in low
        for kw in (
            "saveloadui",
            "saveloader",
            "searchwin",
            "namemain",
            "\\result\\",
            "\\font\\",
            "/status",
            "/terminal",
            "/title",
            "tbcr",
            "tbl1",
            ".tbb",
            "hud",
            "gauge",
            "window",
            "cursor",
            "asdtmspr",
            "asdlistbox",
            "bustup",
            "menu",
            "icon",
            "banner",
            "panel",
        )
    ):
        return "ui"
    if any(
        kw in low
        for kw in (
            ".bf",
            "flw0",
            "flow",
            ".mbm",
            "msg",
            "script",
            "questscr",
            "aoc_scr",
        )
    ):
        return "script_vm"
    if any(
        kw in low
        for kw in (
            "asdsdk",
            "\\map\\",
            "\\mapnavi\\",
            "\\event\\",
            "\\sound\\",
            "\\cec\\",
            "\\addon\\",
            "/map",
            "/event",
            "/mikado",
            "/player",
            "/effect",
            ".bam",
            ".stex",
            ".bcenv",
            ".bccam",
        )
    ):
        return "engine"
    return None


def extract_strings(code_bytes: bytes) -> dict[int, tuple[str, str, str]]:
    """
    Scans .rodata and .data for printable ASCII strings >= 4 chars.
    Also indexes 4-byte aligned starts inside matched regions (e.g., when preceded by float bytes).
    Returns dict: vaddr -> (section_name, symbol_name, string_preview)
    """
    strings: dict[int, tuple[str, str, str]] = {}
    ascii_re = re.compile(rb"[\x20-\x7e]{4,}\x00")

    sections = [
        ("rodata", RODATA_VADDR, RODATA_FILE_OFFSET, RODATA_SIZE),
        ("data", DATA_VADDR, DATA_FILE_OFFSET, DATA_SIZE),
    ]
    used_names: Counter[str] = Counter()

    def register_str(sec_name: str, vaddr: int, text: str) -> None:
        if len(text) < 4 or vaddr in strings:
            return
        # Prefer original Atlus source file basename if present
        cpp_m = re.search(r"([A-Za-z0-9_]+)\.(?:cpp|c|h)", text)
        if cpp_m:
            clean_ident = f"s_src_{cpp_m.group(1)}"
        else:
            clean_ident = re.sub(r"[^a-zA-Z0-9_]+", "_", text)[:28].strip("_")
            if not clean_ident or clean_ident[0].isdigit():
                clean_ident = f"str_{vaddr:08x}"
            else:
                clean_ident = f"s_{clean_ident}"
        used_names[clean_ident] += 1
        if used_names[clean_ident] > 1:
            clean_ident = f"{clean_ident}_{vaddr:08x}"
        strings[vaddr] = (sec_name, clean_ident, text[:96])

    for sec_name, base_vaddr, file_off, sec_size in sections:
        chunk = code_bytes[file_off : file_off + sec_size]
        for m in ascii_re.finditer(chunk):
            raw = m.group(0)[:-1]
            text = raw.decode("ascii", "ignore").strip()
            if len(text) < 4:
                continue
            vaddr = base_vaddr + m.start()
            register_str(sec_name, vaddr, text)
            # If the string contains 'c:\SMT4' at a 4-byte aligned inner offset, register that aligned start too
            idx_c = raw.lower().find(b"c:\\smt4")
            if idx_c > 0:
                inner_vaddr = base_vaddr + m.start() + idx_c
                inner_text = raw[idx_c:].decode("ascii", "ignore").strip()
                register_str(sec_name, inner_vaddr, inner_text)
            # Also register first 4-byte aligned boundary if unaligned start had 1-3 garbage ASCII bytes
            if (vaddr & 3) != 0:
                pad = 4 - (vaddr & 3)
                if len(raw) - pad >= 4:
                    aligned_vaddr = vaddr + pad
                    aligned_text = raw[pad:].decode("ascii", "ignore").strip()
                    register_str(sec_name, aligned_vaddr, aligned_text)

    return strings


def analyze_binary(
    code_path: Path, game_info_path: Path, write_csv: bool = True
) -> tuple[list[dict], list[dict]]:
    code_bytes = Path(code_path).read_bytes()
    _ = json.loads(Path(game_info_path).read_text(encoding="utf-8"))

    config_dir = Path(game_info_path).parent
    funcs_csv = config_dir / "functions.csv"
    syms_csv = config_dir / "symbols.csv"

    strings = extract_strings(code_bytes)

    num_words = TEXT_SIZE // 4
    words = struct.unpack_from(f"<{num_words}I", code_bytes, 0)

    literal_pool_indices: set[int] = set()
    literal_loads: dict[int, int] = {}
    bl_targets: set[int] = {0}
    call_edges: list[tuple[int, int]] = []

    thumb_crt_start_idx = (0x00100048 - TEXT_VADDR) >> 2
    thumb_crt_end_idx = (0x00101300 - TEXT_VADDR) >> 2

    # Pass 1A: Identify all PC-relative literal pool entries (LDR, VLDR float/double, ADR inline strings)
    for idx, word in enumerate(words):
        if thumb_crt_start_idx <= idx < thumb_crt_end_idx:
            continue
        if idx in literal_pool_indices:
            continue

        cond = (word >> 28) & 0xF
        if cond == 0xF:
            continue

        # PC-relative LDR: LDR Rd, [PC, #+-imm12]
        if (word & 0x0F7F0000) == 0x051F0000:
            up = (word >> 23) & 1
            imm12 = word & 0xFFF
            pc_idx = idx + 2
            offset_words = (imm12 >> 2) if up else -(imm12 >> 2)
            lit_idx = pc_idx + offset_words
            if 0 <= lit_idx < num_words and (imm12 & 3) == 0:
                literal_pool_indices.add(lit_idx)
                literal_loads[idx] = words[lit_idx]
            continue

        # PC-relative VFP VLDR: VLDR Sn/Dn, [PC, #+-imm8*4]
        if (word & 0x0F3F0E00) == 0x0D1F0A00:
            up = (word >> 23) & 1
            imm8 = word & 0xFF
            offset_words = imm8 if up else -imm8
            lit_idx = idx + 2 + offset_words
            if 0 <= lit_idx < num_words:
                literal_pool_indices.add(lit_idx)
                # Double precision (coproc 11) occupies 2 words
                if (word & 0x00000100) != 0 and (lit_idx + 1) < num_words:
                    literal_pool_indices.add(lit_idx + 1)
            continue

        # PC-relative ADR: ADD Rd, PC, #imm (encoding: (word & 0x0FEF0000) == 0x028F0000)
        if (word & 0x0FEF0000) == 0x028F0000:
            rot = ((word >> 8) & 0xF) * 2
            imm8 = word & 0xFF
            imm = ((imm8 >> rot) | (imm8 << (32 - rot))) & 0xFFFFFFFF if rot else imm8
            t_off = (idx << 2) + 8 + imm
            if 0 <= t_off < TEXT_SIZE - 4 and (t_off & 3) == 0:
                s_bytes = code_bytes[t_off : t_off + 128].split(b"\x00", 1)[0]
                if len(s_bytes) >= 3 and all(0x20 <= b <= 0x7E for b in s_bytes):
                    s_text = s_bytes.decode("ascii", "ignore").strip()
                    t_vaddr = TEXT_VADDR + t_off
                    span_words = (len(s_bytes) + 1 + 3) >> 2
                    for w_off in range(span_words):
                        if (t_off >> 2) + w_off < num_words:
                            literal_pool_indices.add((t_off >> 2) + w_off)
                    if t_vaddr not in strings and len(s_text) >= 3:
                        clean_ident = re.sub(r"[^a-zA-Z0-9_]+", "_", s_text)[:28].strip("_")
                        strings[t_vaddr] = ("text", f"s_{clean_ident}_{t_vaddr:08x}", s_text[:96])
                    literal_loads[idx] = t_vaddr
            continue

    # Pass 1B: Scan non-literal-pool ARM instructions for BL / BLX call targets
    for idx, word in enumerate(words):
        if thumb_crt_start_idx <= idx < thumb_crt_end_idx:
            continue
        if idx in literal_pool_indices:
            continue

        cond = (word >> 28) & 0xF
        if (cond != 0xF and ((word >> 24) & 0xF) == 0xB) or (
            cond == 0xF and ((word >> 25) & 0x7) == 0x5
        ):
            imm24 = word & 0xFFFFFF
            if imm24 & 0x800000:
                imm24 -= 0x1000000
            target_idx = idx + 2 + imm24
            if 0 <= target_idx < num_words and target_idx not in literal_pool_indices:
                bl_targets.add(target_idx)
                call_edges.append((idx, target_idx))

    func_starts: set[int] = set(bl_targets) - literal_pool_indices
    func_starts.add(0)
    func_starts.add((0x00100048 - TEXT_VADDR) >> 2)  # end of __init_bss

    def is_terminator(w_idx: int) -> bool:
        if w_idx < 0 or w_idx in literal_pool_indices:
            return True
        pw = words[w_idx]
        return (
            pw == 0xE12FFF1E  # bx lr
            or (pw & 0x0FFF8000) == 0x08BD8000  # pop {..., pc}
            or (pw & 0xFF000000) == 0xEA000000  # unconditional b
            or (pw & 0x0FFFFFF0) == 0x012FFF10  # bx reg
            or (pw & 0x0FBF0FFF) == 0x010F0000  # mrs / end padding
        )

    for idx, word in enumerate(words):
        if idx in literal_pool_indices or idx in func_starts:
            continue
        cond = (word >> 28) & 0xF
        if cond == 0xE and ((word & 0x0FFF4000) == 0x092D4000 or word == 0xE52DE004):
            if is_terminator(idx - 1):
                func_starts.add(idx)

    # Check function pointers in .rodata and .data (vtables, callback tables)
    for sec_off, sec_sz in ((RODATA_FILE_OFFSET, RODATA_SIZE), (DATA_FILE_OFFSET, DATA_SIZE)):
        sec_words = struct.unpack_from(f"<{sec_sz // 4}I", code_bytes, sec_off)
        for ptr in sec_words:
            if TEXT_VADDR <= ptr < TEXT_END and (ptr & 3) == 0:
                t_idx = (ptr - TEXT_VADDR) >> 2
                if t_idx not in literal_pool_indices and t_idx > 0:
                    w = words[t_idx]
                    if is_terminator(t_idx - 1) and (w >> 28) == 0xE:
                        func_starts.add(t_idx)

    sorted_starts = sorted(func_starts)

    func_cats: list[Counter[str]] = [Counter() for _ in range(len(sorted_starts))]
    func_src_hint: list[str | None] = [None] * len(sorted_starts)

    for insn_idx, lit_val in literal_loads.items():
        if lit_val in strings:
            _, _, s_text = strings[lit_val]
            f_pos = bisect.bisect_right(sorted_starts, insn_idx) - 1
            if f_pos >= 0:
                cat = classify_string(s_text)
                if cat:
                    func_cats[f_pos][cat] += 5
                cpp_m = re.search(r"([A-Za-z0-9_]+)\.(?:cpp|c)", s_text)
                if cpp_m and not func_src_hint[f_pos]:
                    func_src_hint[f_pos] = cpp_m.group(1)

    start_to_fpos = {s_idx: i for i, s_idx in enumerate(sorted_starts)}
    caller_to_callees: dict[int, list[int]] = defaultdict(list)
    callee_to_callers: dict[int, list[int]] = defaultdict(list)

    for caller_insn, target_idx in call_edges:
        callee_pos = start_to_fpos.get(target_idx)
        if callee_pos is None:
            continue
        caller_pos = bisect.bisect_right(sorted_starts, caller_insn) - 1
        if caller_pos >= 0 and caller_pos != callee_pos:
            caller_to_callees[caller_pos].append(callee_pos)
            callee_to_callers[callee_pos].append(caller_pos)

    resolved_cats: list[str] = ["unknown"] * len(sorted_starts)
    for i, start_idx in enumerate(sorted_starts):
        vaddr = TEXT_VADDR + (start_idx << 2)
        if vaddr < 0x00102500:
            resolved_cats[i] = "crt"
        elif func_cats[i]:
            resolved_cats[i] = func_cats[i].most_common(1)[0][0]

    # Propagate categories across call graph (2 hops)
    for _ in range(2):
        next_cats = list(resolved_cats)
        for i in range(len(sorted_starts)):
            if next_cats[i] != "unknown":
                continue
            votes: Counter[str] = Counter()
            for c in caller_to_callees.get(i, ()):
                if resolved_cats[c] not in ("unknown", "crt"):
                    votes[resolved_cats[c]] += 1
            for p in callee_to_callers.get(i, ()):
                if resolved_cats[p] not in ("unknown", "crt"):
                    votes[resolved_cats[p]] += 1
            if votes:
                next_cats[i] = votes.most_common(1)[0][0]
        resolved_cats = next_cats

    existing_overrides: dict[str, dict] = {}
    if funcs_csv.exists():
        with open(funcs_csv, "r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                if row.get("status") and row["status"] != "todo":
                    existing_overrides[row["address"]] = row

    functions: list[dict] = []
    for i, start_idx in enumerate(sorted_starts):
        end_idx = sorted_starts[i + 1] if (i + 1) < len(sorted_starts) else num_words
        vaddr = TEXT_VADDR + (start_idx << 2)
        size_bytes = (end_idx - start_idx) << 2
        addr_hex = f"0x{vaddr:08x}"

        if addr_hex in existing_overrides:
            ov = existing_overrides[addr_hex]
            functions.append(
                {
                    "address": addr_hex,
                    "size": size_bytes,
                    "status": ov["status"],
                    "category": ov["category"],
                    "name": ov["name"],
                    "src_file": ov["src_file"],
                }
            )
            continue

        cat = resolved_cats[i]
        hint = func_src_hint[i]
        if vaddr == 0x00100000:
            name = "__start"
        elif vaddr == 0x00100024:
            name = "__init_bss"
        elif hint:
            name = f"{hint}_func_{vaddr:08x}"
        else:
            name = f"func_{vaddr:08x}" if cat == "unknown" else f"{cat}_func_{vaddr:08x}"

        functions.append(
            {
                "address": addr_hex,
                "size": size_bytes,
                "status": "todo",
                "category": cat,
                "name": name,
                "src_file": "",
            }
        )

    symbols: list[dict] = []
    for vaddr in sorted(strings.keys()):
        sec_name, sym_name, preview = strings[vaddr]
        symbols.append(
            {
                "address": f"0x{vaddr:08x}",
                "section": sec_name,
                "type": "asciz",
                "name": sym_name,
                "string_preview": preview,
            }
        )

    if write_csv:
        with open(funcs_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["address", "size", "status", "category", "name", "src_file"],
            )
            writer.writeheader()
            writer.writerows(functions)

        with open(syms_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["address", "section", "type", "name", "string_preview"],
            )
            writer.writeheader()
            writer.writerows(symbols)

    return functions, symbols


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze SMT4 code.bin")
    parser.add_argument(
        "--code",
        type=Path,
        default=Path("extracted/exefs/code.bin"),
        help="Path to decompressed code.bin",
    )
    parser.add_argument(
        "--info",
        type=Path,
        default=Path("config/game_info.json"),
        help="Path to game_info.json",
    )
    args = parser.parse_args()

    funcs, syms = analyze_binary(args.code, args.info, write_csv=True)
    cat_counts = Counter(f["category"] for f in funcs)
    cat_bytes = defaultdict(int)
    for f in funcs:
        cat_bytes[f["category"]] += int(f["size"])

    print(
        f"Discovered {len(funcs)} functions ({sum(int(f['size']) for f in funcs):,} bytes) and {len(syms)} string symbols."
    )
    for cat, count in cat_counts.most_common():
        print(f"  {cat:12s}: {count:5d} funcs ({cat_bytes[cat] / 1024:7.1f} KB)")


if __name__ == "__main__":
    main()
