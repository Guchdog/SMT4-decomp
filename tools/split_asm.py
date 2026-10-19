#!/usr/bin/env python3
"""
Annotated ARMv6K Disassembler for Shin Megami Tensei IV (code.bin).
Resolves function call targets, PC-relative literal pool loads, and .rodata string xrefs.
"""

import argparse
import csv
import struct
import sys
from pathlib import Path
import capstone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.analyze_code import TEXT_VADDR, vaddr_to_offset


def load_lookup_tables(
    functions_csv: Path, symbols_csv: Path
) -> tuple[list[dict], dict[int, str], dict[int, tuple[str, str]]]:
    funcs: list[dict] = []
    func_names: dict[int, str] = {}
    if functions_csv.exists():
        with open(functions_csv, "r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                addr = int(row["address"], 16)
                funcs.append(row)
                func_names[addr] = row["name"]

    symbols: dict[int, tuple[str, str]] = {}
    if symbols_csv.exists():
        with open(symbols_csv, "r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                addr = int(row["address"], 16)
                symbols[addr] = (row["name"], row["string_preview"])

    return funcs, func_names, symbols


def disassemble_function(
    code_bytes: bytes,
    addr: int,
    size: int,
    symbols: dict[int, tuple[str, str] | str],
    func_names: dict[int, str],
    thumb: bool | None = None,
) -> str:
    if thumb is None:
        thumb = 0x00100048 <= addr < 0x00101300
    offset = vaddr_to_offset(addr)
    chunk = code_bytes[offset : offset + size]
    num_words = size // 4
    words = struct.unpack_from(f"<{num_words}I", chunk, 0)

    # First pass: locate literal pool slots and inline ADR strings referenced inside this function
    literal_addrs: dict[int, int] = {}
    inline_str_addrs: dict[int, tuple[str, int]] = {}  # lit_addr -> (text, aligned_byte_len)
    ldr_targets: dict[int, int] = {}
    if not thumb:
        for i, w in enumerate(words):
            insn_addr = addr + (i << 2)
            cond = (w >> 28) & 0xF
            if cond != 0xF and (w & 0x0F7F0000) == 0x051F0000:
                up = (w >> 23) & 1
                imm12 = w & 0xFFF
                lit_addr = (insn_addr + 8 + imm12) if up else (insn_addr + 8 - imm12)
                ldr_targets[insn_addr] = lit_addr
                if addr <= lit_addr < addr + size and ((lit_addr - addr) & 3) == 0:
                    lit_idx = (lit_addr - addr) >> 2
                    literal_addrs[lit_addr] = words[lit_idx]
            elif cond != 0xF and (w & 0x0F3F0E00) == 0x0D1F0A00:
                up = (w >> 23) & 1
                imm8 = (w & 0xFF) << 2
                lit_addr = (insn_addr + 8 + imm8) if up else (insn_addr + 8 - imm8)
                if addr <= lit_addr < addr + size and ((lit_addr - addr) & 3) == 0:
                    lit_idx = (lit_addr - addr) >> 2
                    literal_addrs[lit_addr] = words[lit_idx]
                    ldr_targets[insn_addr] = lit_addr
            elif cond != 0xF and (w & 0x0FEF0000) == 0x028F0000:
                rot = ((w >> 8) & 0xF) * 2
                imm8 = w & 0xFF
                imm = ((imm8 >> rot) | (imm8 << (32 - rot))) & 0xFFFFFFFF if rot else imm8
                lit_addr = insn_addr + 8 + imm
                if addr <= lit_addr < addr + size and ((lit_addr - addr) & 3) == 0:
                    rel_off = lit_addr - addr
                    s_bytes = chunk[rel_off : rel_off + 128].split(b"\x00", 1)[0]
                    if len(s_bytes) >= 3 and all(0x20 <= b <= 0x7E for b in s_bytes):
                        aligned_len = (len(s_bytes) + 1 + 3) & ~3
                        inline_str_addrs[lit_addr] = (
                            s_bytes.decode("ascii", "ignore"),
                            aligned_len,
                        )
                        ldr_targets[insn_addr] = lit_addr

    cs = capstone.Cs(
        capstone.CS_ARCH_ARM,
        capstone.CS_MODE_THUMB if thumb else capstone.CS_MODE_ARM,
    )
    fname = func_names.get(addr, f"func_{addr:08x}")
    lines = [
        f".section .text",
        ".thumb" if thumb else ".arm",
        f".global {fname}",
        f".type {fname}, %function",
        f"{fname}:",
    ]

    def format_sym(val: int) -> str:
        if val in symbols:
            entry = symbols[val]
            if isinstance(entry, tuple):
                return f'{entry[0]} ("{entry[1]}")'
            return str(entry)
        if val in func_names:
            return func_names[val]
        return f"0x{val:08x}"

    data_starts = set(literal_addrs.keys()) | set(inline_str_addrs.keys())
    pos = 0
    while pos < size:
        cur_addr = addr + pos
        if cur_addr in inline_str_addrs:
            s_text, aligned_len = inline_str_addrs[cur_addr]
            lines.append(f'0x{cur_addr:08x}:  .asciz "{s_text}"')
            lines.append("             .balign 4")
            pos += aligned_len
            continue
        if cur_addr in literal_addrs:
            val = literal_addrs[cur_addr]
            comment = f" @ -> {format_sym(val)}" if (val in symbols or val in func_names) else ""
            lines.append(f"0x{cur_addr:08x}:  .word 0x{val:08x}{comment}")
            pos += 4
            continue

        # Disassemble contiguous instruction span up to next literal pool / inline string entry
        next_lit = min(
            (la for la in data_starts if la > cur_addr),
            default=addr + size,
        )
        span_bytes = chunk[pos : next_lit - addr]
        disassembled_any = False
        for insn in cs.disasm(span_bytes, cur_addr):
            disassembled_any = True
            comment = ""
            if insn.address in ldr_targets:
                lit_addr = ldr_targets[insn.address]
                if lit_addr in inline_str_addrs:
                    comment = f' @ &"{inline_str_addrs[lit_addr][0]}" (0x{lit_addr:08x})'
                elif addr <= lit_addr < addr + size:
                    val = literal_addrs.get(lit_addr)
                    if val is not None:
                        comment = f" @ =0x{val:08x} ({format_sym(val)})"
            elif insn.mnemonic.startswith(("bl", "b")) and insn.op_str.startswith("#0x"):
                try:
                    target = int(insn.op_str[1:], 16)
                    if target in func_names:
                        comment = f" @ {func_names[target]}"
                except ValueError:
                    pass
            lines.append(
                f"0x{insn.address:08x}:  {insn.mnemonic:8s} {insn.op_str}{comment}"
            )
            pos = (insn.address - addr) + insn.size

        if not disassembled_any:
            w = struct.unpack_from("<I", chunk, pos)[0]
            lines.append(f"0x{cur_addr:08x}:  .word 0x{w:08x}")
            pos += 4

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Disassemble SMT4 functions from code.bin")
    parser.add_argument("--code", type=Path, default=Path("extracted/exefs/code.bin"))
    parser.add_argument("--functions", type=Path, default=Path("config/functions.csv"))
    parser.add_argument("--symbols", type=Path, default=Path("config/symbols.csv"))
    parser.add_argument("--addr", type=str, default=None, help="Hex address of function")
    parser.add_argument("--name", type=str, default=None, help="Function name substring")
    parser.add_argument("--category", type=str, default=None, help="Subsystem category")
    parser.add_argument("--limit", type=int, default=5, help="Max functions to print")
    parser.add_argument("--out-dir", type=Path, default=None, help="Write .s files to directory")
    args = parser.parse_args()

    code_bytes = args.code.read_bytes()
    funcs, func_names, symbols = load_lookup_tables(args.functions, args.symbols)

    selected: list[dict] = []
    for row in funcs:
        if args.addr and int(row["address"], 16) == int(args.addr, 16):
            selected.append(row)
        elif args.name and args.name.lower() in row["name"].lower():
            selected.append(row)
        elif args.category and row["category"] == args.category:
            selected.append(row)

    if not selected and not (args.addr or args.name or args.category):
        selected = funcs[: args.limit]
    else:
        selected = selected[: args.limit]

    for row in selected:
        f_addr = int(row["address"], 16)
        f_size = int(row["size"])
        asm = disassemble_function(code_bytes, f_addr, f_size, symbols, func_names)
        if args.out_dir:
            cat_dir = args.out_dir / row["category"]
            cat_dir.mkdir(parents=True, exist_ok=True)
            (cat_dir / f"{row['name']}.s").write_text(asm, encoding="utf-8")
        else:
            print(f"// Function: {row['name']} ({row['address']}, {f_size} bytes, category={row['category']})")
            print(asm)


if __name__ == "__main__":
    main()
