#!/usr/bin/env python3
"""
ARMv6K ELF32 Assembly Diffing & Disassembly Verification Engine for Shin Megami Tensei IV.

Extracts compiled machine code from ELF32 object files, matches symbols, and
performs byte-level and instruction mnemonic comparisons against extracted/exefs/code.bin.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import struct
import sys
import capstone

# Ensure project root is importable
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.build_check import ensure_tu_armv6k

@dataclass(frozen=True)
class ElfRelocation:
    """A relocation located inside one extracted function symbol."""

    offset: int
    relocation_type: int
    symbol_name: str
    explicit_addend: int | None = None


_ELF_CACHE: dict[
    tuple[str, float], dict[str, tuple[bytes, tuple[ElfRelocation, ...]]]
] = {}


def extract_elf_functions_detailed(
    obj_path: Path,
) -> dict[str, tuple[bytes, tuple[ElfRelocation, ...]]]:
    """Parse a 32-bit little-endian ARM ELF object file.

    Returns:
        dict mapping symbol name to (function_bytes, relocations), where each
        relocation offset is relative to the extracted function's first byte.
    """
    obj_path = Path(obj_path)
    if not obj_path.is_file():
        return {}

    cache_key = None
    try:
        mtime = obj_path.stat().st_mtime
        cache_key = (str(obj_path.resolve()), mtime)
        if cache_key in _ELF_CACHE:
            return _ELF_CACHE[cache_key]
    except OSError:
        pass

    data = obj_path.read_bytes()
    if len(data) < 52 or data[:4] != b"\x7fELF":
        return {}

    # Elf32_Ehdr
    (
        e_ident,
        e_type,
        e_machine,
        e_version,
        e_entry,
        e_phoff,
        e_shoff,
        e_flags,
        e_ehsize,
        e_phentsize,
        e_phnum,
        e_shentsize,
        e_shnum,
        e_shstrndx,
    ) = struct.unpack_from("<16sHHIIIIIHHHHHH", data, 0)

    if e_shnum == 0 or e_shoff == 0:
        return {}

    # Read section headers (Elf32_Shdr)
    sections: list[tuple[int, int, int, int, int, int, int, int, int, int]] = []
    for i in range(e_shnum):
        sh = struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        sections.append(sh)

    # shstrtab for section names
    if e_shstrndx >= len(sections):
        return {}
    shstr = sections[e_shstrndx]
    shstrtab = data[shstr[4] : shstr[4] + shstr[5]]

    def get_sh_name(offset: int) -> str:
        end = shstrtab.find(b"\x00", offset)
        if end == -1:
            end = len(shstrtab)
        return shstrtab[offset:end].decode("ascii", errors="replace")

    sec_names = [get_sh_name(s[0]) for s in sections]

    # Locate .symtab (SHT_SYMTAB = 2)
    symtab_idx = None
    for idx, s in enumerate(sections):
        if s[1] == 2:
            symtab_idx = idx
            break
    if symtab_idx is None:
        return {}

    symtab_sec = sections[symtab_idx]
    strtab_idx = symtab_sec[6]  # sh_link
    if strtab_idx >= len(sections):
        return {}
    strtab_sec = sections[strtab_idx]
    strtab_data = data[strtab_sec[4] : strtab_sec[4] + strtab_sec[5]]

    def get_sym_name(offset: int) -> str:
        end = strtab_data.find(b"\x00", offset)
        if end == -1:
            end = len(strtab_data)
        return strtab_data[offset:end].decode("ascii", errors="replace")

    entsize = symtab_sec[9] or 16
    count = symtab_sec[5] // entsize
    symbols: list[tuple[str, int, int, int, int]] = []
    for i in range(count):
        st_name, st_value, st_size, st_info, st_other, st_shndx = struct.unpack_from(
            "<IIIBBH", data, symtab_sec[4] + i * entsize
        )
        symbols.append(
            (get_sym_name(st_name), st_value & ~1, st_size, st_info & 0x0F, st_shndx)
        )

    # SHT_REL = 9, SHT_RELA = 4.  Keep relocation type and symbol so the
    # verifier can resolve supported calls against the function ledger.
    relocs_by_target: dict[int, list[tuple[int, int, str, int | None]]] = {}
    for rel_sec in sections:
        if rel_sec[1] not in (4, 9):
            continue
        target_sec = rel_sec[7]  # sh_info holds the relocated section index
        symtab_for_reloc = rel_sec[6]  # sh_link holds the symbol table index
        if symtab_for_reloc != symtab_idx:
            continue
        is_rela = rel_sec[1] == 4
        default_entsize = 12 if is_rela else 8
        reloc_entsize = rel_sec[9] or default_entsize
        if reloc_entsize < default_entsize:
            continue
        rel_list = relocs_by_target.setdefault(target_sec, [])
        for rel_i in range(rel_sec[5] // reloc_entsize):
            rel_pos = rel_sec[4] + rel_i * reloc_entsize
            r_offset, r_info = struct.unpack_from("<II", data, rel_pos)
            symbol_index = r_info >> 8
            relocation_type = r_info & 0xFF
            explicit_addend = None
            if is_rela:
                (explicit_addend,) = struct.unpack_from("<i", data, rel_pos + 8)
            symbol_name = (
                symbols[symbol_index][0] if symbol_index < len(symbols) else ""
            )
            rel_list.append(
                (r_offset, relocation_type, symbol_name, explicit_addend)
            )

    funcs: dict[str, tuple[bytes, tuple[ElfRelocation, ...]]] = {}

    for sym_name, st_value, st_size, st_type, st_shndx in symbols:
        if 0 < st_shndx < len(sections):
            sec = sections[st_shndx]
            sec_name = sec_names[st_shndx]
            # Must be executable section (.text or SHF_EXECINSTR = 0x4)
            if (sec[2] & 0x4) or sec_name.startswith(".text"):
                if st_type == 2 or st_size > 0:  # STT_FUNC or non-empty size
                    if sym_name:
                        func_bytes = data[
                            sec[4] + st_value : sec[4] + st_value + st_size
                        ]
                        relocs = relocs_by_target.get(st_shndx, [])
                        function_relocs = tuple(
                            ElfRelocation(
                                r_off - st_value,
                                reloc_type,
                                target_name,
                                explicit_addend,
                            )
                            for r_off, reloc_type, target_name, explicit_addend in relocs
                            if st_value <= r_off < st_value + st_size
                        )
                        funcs[sym_name] = (func_bytes, function_relocs)

    if cache_key is not None:
        _ELF_CACHE[cache_key] = funcs
    return funcs


def extract_elf_functions(obj_path: Path) -> dict[str, tuple[bytes, set[int]]]:
    """Parse functions while preserving the legacy relocation-offset result."""
    return {
        name: (func_bytes, {rel.offset // 4 for rel in relocations})
        for name, (func_bytes, relocations) in extract_elf_functions_detailed(
            obj_path
        ).items()
    }


def find_symbol_in_elf(
    funcs: dict[str, tuple],
    func_name: str,
    addr: int | None = None,
) -> tuple | None:
    """Find a symbol in extracted ELF functions using exact, Itanium mangled, or address match."""
    if func_name in funcs:
        return funcs[func_name]

    # Itanium C++ mangling matches: e.g. "20engine_func_0011b838".
    needle = f"{len(func_name)}{func_name}"
    mangled_matches = [
        val
        for sname, val in funcs.items()
        if needle in sname and not sname.startswith("_ZZ")
    ]
    if len(mangled_matches) == 1:
        return mangled_matches[0]
    if len(mangled_matches) > 1:
        return None

    # Address tag match (e.g. "0011b838" in "_Z..._func_0011b838...")
    if addr is not None:
        addr_tag = f"{addr:08x}"
        address_matches = [val for sname, val in funcs.items() if addr_tag in sname]
        if len(address_matches) == 1:
            return address_matches[0]

    return None


@lru_cache(maxsize=8)
def _function_addresses_from_csv(
    csv_path: str, mtime_ns: int, file_size: int
) -> dict[str, int]:
    """Return only uniquely named function symbols from a functions ledger."""
    del mtime_ns, file_size
    addresses_by_name: dict[str, set[int]] = {}
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            name = row.get("name", "").strip()
            address = row.get("address", "").strip()
            if not name or not address:
                continue
            try:
                value = int(address, 16)
            except ValueError:
                continue
            addresses_by_name.setdefault(name, set()).add(value)
    return {
        name: next(iter(values))
        for name, values in addresses_by_name.items()
        if len(values) == 1
    }


def load_function_addresses(functions_csv: Path) -> dict[str, int]:
    """Read a cached exact-name-to-address map from a function ledger."""
    functions_csv = Path(functions_csv)
    try:
        stat = functions_csv.stat()
    except OSError:
        return {}
    return _function_addresses_from_csv(
        str(functions_csv.resolve()), stat.st_mtime_ns, stat.st_size
    )


def normalize_resolved_arm_calls(
    compiled_bytes: bytes,
    relocations: tuple[ElfRelocation, ...] | list[ElfRelocation],
    expected_bytes: bytes,
    function_addr: int,
    functions_csv: Path,
) -> bytes | None:
    """Resolve only unambiguous ARM-state R_ARM_CALLs against the ledger.

    The object branch immediate is linker-owned, so it is not trusted as proof.
    Instead, the relocation must identify a uniquely named ledger function, the
    original instruction at that offset must be an unconditional ARM BL to that
    exact address, and the object opcode must match the original BL opcode. Any
    other relocation or interworking case remains unresolved and fails closed.
    """
    if not relocations:
        return compiled_bytes
    if len(compiled_bytes) != len(expected_bytes) or not expected_bytes:
        return None
    if 0x00100048 <= function_addr < 0x00101300:
        return None  # Thumb branch relocations are not supported here.

    function_addresses = load_function_addresses(functions_csv)
    if not function_addresses:
        return None

    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    cs.detail = True
    expected_insns = {
        insn.address - function_addr: insn
        for insn in cs.disasm(expected_bytes, function_addr)
    }
    normalized = bytearray(compiled_bytes)
    seen_offsets: set[int] = set()

    for reloc in relocations:
        offset = reloc.offset
        if (
            reloc.relocation_type != 28  # R_ARM_CALL
            or reloc.explicit_addend is not None
            or offset in seen_offsets
            or offset < 0
            or offset % 4
            or offset + 4 > len(expected_bytes)
        ):
            return None
        seen_offsets.add(offset)

        target_addr = function_addresses.get(reloc.symbol_name)
        if target_addr is None:
            return None
        if 0x00100048 <= target_addr < 0x00101300:
            return None  # Do not infer ARM/Thumb interworking or veneer behavior.

        expected_insn = expected_insns.get(offset)
        if (
            expected_insn is None
            or expected_insn.mnemonic.lower() != "bl"
            or not expected_insn.operands
            or expected_insn.operands[-1].type != capstone.arm.ARM_OP_IMM
            or expected_insn.operands[-1].imm != target_addr
        ):
            return None

        compiled_word = struct.unpack_from("<I", compiled_bytes, offset)[0]
        expected_word = struct.unpack_from("<I", expected_bytes, offset)[0]
        # R_ARM_CALL may fill only the branch displacement; the condition and
        # opcode must already be the same BL instruction as in the executable.
        # The assembler's canonical implicit addend for ``bl symbol`` is -8,
        # encoded as imm24 == 0xfffffe. Reject altered addends rather than
        # assuming the relocation still names the exact ledger target.
        if (
            (compiled_word & 0xFF000000) != (expected_word & 0xFF000000)
            or (compiled_word & 0x00FFFFFF) != 0x00FFFFFE
        ):
            return None
        normalized[offset : offset + 4] = expected_bytes[offset : offset + 4]

    return bytes(normalized)


def compare_function(
    addr: int | str,
    size: int,
    func_name: str,
    src_file: Path,
    code_bytes: bytes,
    repo_root: Path = Path("."),
) -> dict:
    """Compare a decompiled function against original code.bin bytes.

    Compiles src_file to an ARMv6K object file (or reuses cached object if up to date),
    extracts the function machine code, and computes exact match, byte match ratio,
    Capstone mnemonic match ratio, and side-by-side assembly diff.
    """
    repo_root = Path(repo_root).resolve()
    src_file = Path(src_file)
    if not src_file.is_absolute():
        src_file = repo_root / src_file

    if isinstance(addr, str):
        addr_int = int(addr, 16) if addr.startswith("0x") else int(addr)
    else:
        addr_int = int(addr)
    addr_str = f"0x{addr_int:08x}"

    # Determine object file destination
    try:
        src_root = (repo_root / "src").resolve()
        rel_src = src_file.resolve().relative_to(src_root)
        out_obj = repo_root / "build" / "obj" / "armv6k" / rel_src.with_suffix(".o")
    except ValueError:
        out_obj = src_file.with_suffix(".o")

    res = ensure_tu_armv6k(src_file, out_obj, repo_root=repo_root)
    if res.returncode != 0 or not out_obj.exists():
        return {
            "addr": addr_str,
            "name": func_name,
            "expected_size": size,
            "compiled_size": 0,
            "exact_match": False,
            "byte_match_ratio": 0.0,
            "mnemonic_match_ratio": 0.0,
            "diff_lines": [f"Compilation failed: {res.stderr.strip()}"],
        }

    elf_funcs = extract_elf_functions_detailed(out_obj)
    sym_data = find_symbol_in_elf(elf_funcs, func_name, addr_int)
    if sym_data is None:
        return {
            "addr": addr_str,
            "name": func_name,
            "expected_size": size,
            "compiled_size": 0,
            "exact_match": False,
            "byte_match_ratio": 0.0,
            "mnemonic_match_ratio": 0.0,
            "diff_lines": [f"Symbol '{func_name}' not found in {out_obj.name}"],
        }

    compiled_bytes, relocations = sym_data
    compiled_size = len(compiled_bytes)

    # Slice expected bytes from code.bin (base 0x00100000)
    offset = addr_int - 0x00100000
    if 0 <= offset and offset + size <= len(code_bytes):
        expected_bytes = code_bytes[offset : offset + size]
    else:
        expected_bytes = b""

    normalized_bytes = normalize_resolved_arm_calls(
        compiled_bytes,
        relocations,
        expected_bytes,
        addr_int,
        repo_root / "config" / "functions.csv",
    )
    exact_match = (
        size > 0
        and compiled_size == size
        and normalized_bytes is not None
        and normalized_bytes == expected_bytes
    )
    comparison_bytes = normalized_bytes or compiled_bytes

    # Compute byte_match_ratio
    matching_bytes = 0
    compare_len = min(len(comparison_bytes), len(expected_bytes), size)
    for i in range(compare_len):
        if comparison_bytes[i] == expected_bytes[i]:
            matching_bytes += 1

    byte_match_ratio = round(matching_bytes / max(1, size), 4)

    # Capstone disassembly
    thumb = 0x00100048 <= addr_int < 0x00101300
    cs = capstone.Cs(
        capstone.CS_ARCH_ARM,
        capstone.CS_MODE_THUMB if thumb else capstone.CS_MODE_ARM,
    )
    comp_insns = list(cs.disasm(comparison_bytes, addr_int))
    exp_insns = list(cs.disasm(expected_bytes, addr_int))

    matching_mnemonics = sum(
        1 for ci, ei in zip(comp_insns, exp_insns) if ci.mnemonic == ei.mnemonic
    )
    total_insns = max(len(exp_insns), len(comp_insns), 1)
    mnemonic_match_ratio = round(matching_mnemonics / total_insns, 4) if (comp_insns or exp_insns) else 0.0

    # Format side-by-side diff lines
    diff_lines: list[str] = []
    max_insns = max(len(exp_insns), len(comp_insns))
    for i in range(max_insns):
        ei = exp_insns[i] if i < len(exp_insns) else None
        ci = comp_insns[i] if i < len(comp_insns) else None
        cur_addr = addr_int + (i * (2 if thumb else 4))

        exp_str = f"{ei.mnemonic} {ei.op_str}" if ei else "<none>"
        comp_str = f"{ci.mnemonic} {ci.op_str}" if ci else "<none>"

        if ei and ci and ei.mnemonic == ci.mnemonic and ei.op_str == ci.op_str:
            mark = "  "
        else:
            mark = "<>"

        diff_lines.append(f"0x{cur_addr:08x}:  {exp_str:<34} {mark}  {comp_str}")

    return {
        "addr": addr_str,
        "name": func_name,
        "expected_size": size,
        "compiled_size": compiled_size,
        "exact_match": exact_match,
        "byte_match_ratio": byte_match_ratio,
        "mnemonic_match_ratio": mnemonic_match_ratio,
        "diff_lines": diff_lines,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ARMv6K ELF32 Assembly Diffing & Disassembly Verifier"
    )
    parser.add_argument("--addr", type=str, default=None, help="Function virtual address (e.g. 0x0011b838)")
    parser.add_argument("--name", type=str, default=None, help="Function symbol name")
    parser.add_argument("--functions", type=Path, default=Path("config/functions.csv"))
    parser.add_argument("--code", type=Path, default=Path("extracted/exefs/code.bin"))
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()

    if not args.addr and not args.name:
        parser.error("Specify --addr or --name to diff.")

    if not args.code.is_file():
        print(f"Error: {args.code} not found.", file=sys.stderr)
        sys.exit(1)

    code_bytes = args.code.read_bytes()

    # Search for target row in functions.csv
    target_row = None
    with open(args.functions, "r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if args.addr and row["address"].lower() == args.addr.lower():
                target_row = row
                break
            if args.name and row["name"] == args.name:
                target_row = row
                break

    if target_row is None:
        print(f"Function {args.addr or args.name} not found in {args.functions}", file=sys.stderr)
        sys.exit(1)

    if not target_row.get("src_file", "").strip():
        print(f"Function {target_row.get('name', '')} ({target_row.get('address', '')}) has no src_file assigned in {args.functions}", file=sys.stderr)
        sys.exit(1)

    addr = int(target_row["address"], 16)
    size = int(target_row["size"])
    name = target_row["name"]
    src_file = args.root / target_row["src_file"]

    res = compare_function(addr, size, name, src_file, code_bytes, repo_root=args.root)

    print(f"=== Function: {res['name']} ({res['addr']}) ===")
    print(f"Expected Size: {res['expected_size']} B | Compiled Size: {res['compiled_size']} B")
    print(f"Exact Match:   {res['exact_match']}")
    print(f"Byte Match:    {res['byte_match_ratio'] * 100.0:.2f}%")
    print(f"Mnemonic Match:{res['mnemonic_match_ratio'] * 100.0:.2f}%")
    print("\nDisassembly Diff (Original code.bin  vs  Compiled ARMv6K):")
    print("-" * 75)
    for line in res["diff_lines"]:
        print(line)
    print("-" * 75)


if __name__ == "__main__":
    main()
