#!/usr/bin/env python3
"""Build a pinned H2 production patch from extracted ARM objects.

This is deliberately pinned to the one audited .text page-tail cave and the
current production symbol map. It rejects unknown ELF relocations or layout
changes instead of acting as a general linker.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import capstone

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.h2_calc_code_patch import (
    CODE_DEFAULT, apply_ips, encode_ips,
    elf_function_section_offset, normalize_local_text_addends,
    rebase_local_text_relocations,
)
from tools.semantic_experiment import arm_branch

DRAW_SYMBOL = "ui_func_002cafd0"
DRAW_HELPER = "_ZL38title_config_draw_cached_render_updatejj"
DRAW_LITERAL = "_ZL15kDrawTextFormat"
CALC_SYMBOL = "script_vm_func_001ea928"
CALC_SOURCE = ROOT / "src/engine/leaf_batch46_b.cpp"
DRAW_SOURCE = ROOT / "src/engine/leaf_batch43_a.cpp"
SECONDARY_SOURCE = ROOT / "src/engine/leaf_batch32_c.cpp"
CALC_VMA = 0x001EA928
CALC_CAVE_VMA = 0x003FE624
CALC_SIZE = 2096
DRAW_VMA = 0x002CAFD0
DRAW_SPAN = 1932
SECONDARY_VMA = 0x002CAEF0
SECONDARY_SPAN = 224
SECONDARY_CAVE_VMA = 0x003FEED4
SECONDARY_SIZE = 292
INIT_VMA = 0x002F4CA0
INIT_SIZE = 572
INIT_SYMBOL = "_ZN4smt44camp25titleConfig_func_002f4ca0EPv"
INIT_STRING_POOL_VMA = 0x0042AB78
INIT_STRING_POOL_SIZE = 68
READY_VMA = 0x002FC0EC
READY_SPAN = 52
READY_SIZE = 48
READY_SYMBOL = "ui_func_002fc0ec"
READY_CALL_OFFSET = 28
READY_HELPER_SYMBOL = "battle_func_002bf41c"
READY_HELPER_VMA = 0x002BF41C
DRAW_HELPER_VMA = 0x003FEE54
TAIL_END_VMA = 0x003FF000
ORIGINAL_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
EXPECTED_DRAW_SOURCE_SHA256 = "5ca7486aaa1244ae5e95b9e5073a7f1c49d1568cd6ad01139bc14bd86c0c0726"
EXPECTED_CALC_SOURCE_SHA256 = "c76ab50c12589404ca81e35373c8b136c50c91eb63c5af805bf05cc44c6081c7"
EXPECTED_CALC_OBJECT_SHA256 = "94197ad141393099a25e679b73457f127c54c7155fa4d8c2ff25270f8ca620fd"
EXPECTED_DRAW_OBJECT_SHA256 = "250598c55e1b175f1e9316425cc83810331340e92286346b8d5f87b9dd89adb4"
EXPECTED_DRAW_AUDIT_SHA256 = "d12c6949c29b787f1e467ff70c6a9d39fa566601811ace70fb5dc08587153e2d"
EXPECTED_SECONDARY_SOURCE_SHA256 = "56893b2c7e6fd76ffe5552d23483467e9ee6a34b7375a3f39d67d41da0d6d2fa"
EXPECTED_SECONDARY_OBJECT_SHA256 = "681e67ee676c636d756e50f668101913ce344d7626b0efc31c9bd4888315e164"
SECONDARY_SYMBOL = "engine_func_002caef0"
INIT_SOURCE = ROOT / "src/camp/title_flow.cpp"
READY_SOURCE = ROOT / "src/engine/leaf_batch26_b.cpp"
EXPECTED_INIT_SOURCE_SHA256 = "11b5360c77aecb4ab0e510774fd42a1cb479e8343aff4bb1a30d4cadeccc1b5e"
EXPECTED_INIT_OBJECT_SHA256 = "432664ba70073ff98c2fed19559d4f663f0e4dd9732c519e1bf66eda4dcfe82d"
EXPECTED_READY_SOURCE_SHA256 = "609aaf963db8129a560293c8d1e65b3c6df8fa016673d28b0143535dadb4e4ee"
EXPECTED_READY_OBJECT_SHA256 = "2c0ca7a51729389cce55cf31476f9a3075b50b3b4ef3cabebba9cffe0382b37d"
EXPECTED_INIT_AUDIT_SHA256 = "38a537d1926aa8212820c43664ca0b69c0eb2da7c6f2e1479052bf6a51aeaea6"
EXPECTED_INIT_REVIEW_SHA256 = "2dc2987819942042acb8b24a874b76927d1b8e645e8f36dff531ceb7cc5e960b"
EXPECTED_READY_REVIEW_SHA256 = "382903ff87f9b7f2bcfc4c1151f9920187d1def54ec1f4212fe9f00f57677767"
INIT_STRINGS = (
    (0, b"TITLE_CONFIG_MAIN\0", 20),
    (20, b"TITLE_CONFIG D\0", 16),
    (36, b"camp/config.bf\0", 16),
    (52, b"camp/config.mbm\0", 16),
)
U32 = 0xFFFFFFFF


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def align_up(value: int, alignment: int) -> int:
    return (value + alignment - 1) & -alignment


def parse_elf32(path: Path) -> dict:
    data = path.read_bytes()
    if len(data) < 52 or data[:4] != b"\x7fELF" or data[4] != 1 or data[5] != 1:
        raise ValueError(f"{path}: expected little-endian ELF32")
    header = struct.unpack_from("<16sHHIIIIIHHHHHH", data, 0)
    shoff, shentsize, shnum, shstrndx = header[6], header[11], header[12], header[13]
    if shentsize < 40 or shnum == 0 or shstrndx >= shnum:
        raise ValueError("invalid ELF section table")
    sections = [struct.unpack_from("<IIIIIIIIII", data, shoff + i * shentsize)
                for i in range(shnum)]
    shstr = sections[shstrndx]
    shstr_data = data[shstr[4]:shstr[4] + shstr[5]]

    def string(table: bytes, offset: int) -> str:
        if offset >= len(table):
            raise ValueError("ELF string offset out of range")
        end = table.find(b"\0", offset)
        if end < 0:
            raise ValueError("unterminated ELF string")
        return table[offset:end].decode("utf-8", errors="replace")

    names = [string(shstr_data, section[0]) for section in sections]
    symtab_idx = next((i for i, s in enumerate(sections) if s[1] == 2), None)
    if symtab_idx is None:
        raise ValueError("ELF object has no SHT_SYMTAB")
    symtab = sections[symtab_idx]
    strtab = sections[symtab[6]]
    strdata = data[strtab[4]:strtab[4] + strtab[5]]
    entry_size = symtab[9] or 16
    if entry_size < 16 or symtab[5] % entry_size:
        raise ValueError("invalid ELF symbol table")
    symbols = []
    for i in range(symtab[5] // entry_size):
        name_off, value, size, info, other, shndx = struct.unpack_from(
            "<IIIBBH", data, symtab[4] + i * entry_size)
        symbols.append({"name": string(strdata, name_off), "value": value & ~1,
                        "size": size, "type": info & 0xF, "shndx": shndx})

    relocs = []
    for sec_idx, sec in enumerate(sections):
        if sec[1] not in (4, 9) or sec[6] != symtab_idx:
            continue
        rela = sec[1] == 4
        default_size = 12 if rela else 8
        rsize = sec[9] or default_size
        if rsize < default_size or sec[5] % rsize:
            raise ValueError("invalid ELF relocation table")
        for i in range(sec[5] // rsize):
            pos = sec[4] + i * rsize
            offset, info = struct.unpack_from("<II", data, pos)
            sym_idx, rel_type = info >> 8, info & 0xFF
            if sym_idx >= len(symbols):
                raise ValueError("ELF relocation symbol index out of range")
            explicit = struct.unpack_from("<i", data, pos + 8)[0] if rela else None
            relocs.append({"section": sec[7], "offset": offset,
                           "type": rel_type, "symbol_index": sym_idx,
                           "symbol": symbols[sym_idx], "explicit_addend": explicit})
    return {"data": data, "sections": sections, "section_names": names,
            "symbols": symbols, "relocations": relocs}


def symbol(elf: dict, name: str) -> dict:
    found = [s for s in elf["symbols"] if s["name"] == name]
    if len(found) != 1:
        raise ValueError(f"expected one ELF symbol {name}, found {len(found)}")
    return found[0]


def symbol_bytes(elf: dict, sym: dict) -> bytes:
    if sym["shndx"] == 0 or sym["shndx"] >= len(elf["sections"]):
        raise ValueError(f"symbol {sym['name']} is undefined or has invalid section")
    section = elf["sections"][sym["shndx"]]
    start = section[4] + sym["value"]
    end = start + sym["size"]
    if end > len(elf["data"]):
        raise ValueError(f"symbol {sym['name']} exceeds object file")
    return elf["data"][start:end]


def function_relocations(elf: dict, sym: dict) -> list[dict]:
    selected = []
    for rel in elf["relocations"]:
        if rel["section"] != sym["shndx"]:
            continue
        if sym["value"] <= rel["offset"] < sym["value"] + sym["size"]:
            row = dict(rel)
            row["function_offset"] = rel["offset"] - sym["value"]
            selected.append(row)
    return sorted(selected, key=lambda r: r["function_offset"])


def patch_call(instruction: int, place: int, target: int) -> int:
    # Accept only ARM BL-immediate calls; no BLX interworking or condition drift.
    if instruction & 0x0F000000 != 0x0B000000:
        raise ValueError(f"R_ARM_CALL site is not ARM BL immediate: {instruction:#010x}")
    displacement = target - place - 8
    if displacement & 3 or not -(1 << 25) <= displacement < (1 << 25):
        raise ValueError("ARM BL target is unaligned or out of range")
    return (instruction & 0xFF000000) | 0x0B000000 | ((displacement >> 2) & 0xFFFFFF)


def arm_branch_target(instruction: int, place: int) -> int:
    displacement = (instruction & 0xFFFFFF) << 2
    if displacement & 0x02000000:
        displacement -= 0x04000000
    return place + 8 + displacement


def verify_draw_return_boundary(body: bytes, code_size: int = 1424) -> dict:
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoder.detail = True
    if code_size <= 0 or code_size > len(body) or code_size & 3:
        raise ValueError("invalid Draw main code/data boundary")
    instructions = list(decoder.disasm(body[:code_size], DRAW_VMA))
    if sum(i.size for i in instructions) != code_size or not instructions:
        raise ValueError("Draw production main code prefix does not fully decode as ARM")
    last = instructions[-1]
    if last.mnemonic != "pop" or "pc" not in last.op_str or last.address + last.size != DRAW_VMA + code_size:
        raise ValueError("Draw main must restore saved registers into PC before its literal pool")
    # No direct branch may transfer execution into the trailing constant pool.
    for insn in instructions:
        if insn.group(capstone.CS_GRP_JUMP):
            for operand in insn.operands:
                if operand.type == capstone.arm.ARM_OP_IMM and operand.imm >= DRAW_VMA + code_size:
                    raise ValueError("Draw control-flow branch enters its trailing literal pool")
    return {"terminal_vma": hex(last.address), "instruction": f"{last.mnemonic} {last.op_str}",
            "code_bytes": code_size, "literal_pool": [hex(DRAW_VMA + code_size),
                                                          hex(DRAW_VMA + len(body))]}


def verify_retained_draw_suffix(image: bytes, text_size: int) -> dict:
    suffix_start, suffix_end = 0x002CB588, 0x002CB75C
    text_vma = 0x00100000
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoder.detail = True
    incoming = []
    for off in range(0, text_size - 3, 4):
        address = text_vma + off
        if 0x00100048 <= address < 0x00101300:  # known Thumb CRT interval
            continue
        word = struct.unpack_from("<I", image, off)[0]
        if (word >> 25) & 7 != 5:
            continue
        decoded = list(decoder.disasm(image[off:off + 4], address))
        if (len(decoded) != 1 or not
                (decoded[0].group(capstone.CS_GRP_JUMP)
                 or decoded[0].group(capstone.CS_GRP_CALL))):
            continue
        target = decoded[0].operands[0].imm
        if suffix_start <= target < suffix_end:
            incoming.append((address, target))
    expected = {
        (0x002CB0AC, 0x002CB74C),  # overwritten main-to-suffix edge
        (0x002CB580, 0x002CB6D4),  # overwritten instruction, replaced by the new literal pool
        (0x002CB598, 0x002CB648), (0x002CB5D0, 0x002CB674),
        (0x002CB60C, 0x002CB6A0), (0x002CB644, 0x002CB734),
        (0x002CB670, 0x002CB5BC), (0x002CB69C, 0x002CB5F4),
        (0x002CB6D0, 0x002CB734),
    }
    if set(incoming) != expected:
        raise ValueError(f"Draw retained-suffix branch graph changed: {incoming!r}")
    replacement_end = 0x002CB588
    external = [(source, target) for source, target in incoming
                if not (DRAW_VMA <= source < suffix_end)]
    if external:
        raise ValueError(f"external direct branches enter retained Draw suffix: {external!r}")
    pointer_hits = []
    for off in range(0, len(image) - 3, 4):
        value = struct.unpack_from("<I", image, off)[0] & ~1
        if suffix_start <= value < suffix_end:
            pointer_hits.append((off, value))
    if pointer_hits:
        raise ValueError(f"aligned absolute pointers enter retained Draw suffix: {pointer_hits!r}")
    overwritten_sources = {source for source, _ in incoming if source < replacement_end}
    if overwritten_sources != {0x002CB0AC, 0x002CB580}:
        raise ValueError(f"Draw main-to-suffix edges are not all in the replacement: {overwritten_sources!r}")
    return {"suffix": [hex(suffix_start), hex(suffix_end)],
            "direct_branch_sources": [{"source": hex(a), "target": hex(b)}
                                      for a, b in sorted(incoming)],
            "overwritten_main_edges": ["0x2cb0ac->0x2cb74c", "0x2cb580->0x2cb6d4"],
            "aligned_absolute_pointer_hits": 0,
            "retained_suffix_reachable_from_replacement_entry": False}


def build_combined_patch(image: bytes, calc_obj: Path, draw_obj: Path,
                         game: dict, secondary_obj: Path | None = None,
                         init_obj: Path | None = None,
                         ready_obj: Path | None = None) -> tuple[bytes, bytes, dict]:
    if len(image) != int(game["code_bin_size"]) or sha256(image) != ORIGINAL_SHA256:
        raise ValueError("input is not the pinned original code.bin")
    text = game["segments"]["text"]
    text_vma = int(text["vaddr"], 16)
    text_size = int(text["size"], 16)
    text_aligned = int(text["aligned_size"], 16)
    if text_vma != 0x00100000 or text_size != 0x002FE624 or text_aligned != 0x002FF000:
        raise ValueError("pinned .text layout differs from audited placement contract")
    cave_end = text_vma + text_aligned
    if cave_end != TAIL_END_VMA or CALC_CAVE_VMA != text_vma + text_size:
        raise ValueError("audited .text page-tail bounds changed")

    calc_elf, draw_elf = parse_elf32(calc_obj), parse_elf32(draw_obj)
    secondary_elf = parse_elf32(secondary_obj) if secondary_obj is not None else None
    if (init_obj is None) != (ready_obj is None):
        raise ValueError("initializer and ready-gate objects must be supplied together")
    init_elf = parse_elf32(init_obj) if init_obj is not None else None
    ready_elf = parse_elf32(ready_obj) if ready_obj is not None else None
    calc_source_hash = sha256(CALC_SOURCE.read_bytes())
    draw_source_hash = sha256(DRAW_SOURCE.read_bytes())
    if calc_source_hash != EXPECTED_CALC_SOURCE_SHA256:
        raise ValueError("production Calc source differs from reviewed integration")
    if draw_source_hash != EXPECTED_DRAW_SOURCE_SHA256:
        raise ValueError("production Draw source differs from reviewed split probe")
    if sha256(calc_obj.read_bytes()) != EXPECTED_CALC_OBJECT_SHA256:
        raise ValueError("production Calc object differs from reviewed integration")
    if sha256(draw_obj.read_bytes()) != EXPECTED_DRAW_OBJECT_SHA256:
        raise ValueError("production Draw object differs from reviewed split probe")
    if secondary_obj is not None:
        if sha256(SECONDARY_SOURCE.read_bytes()) != EXPECTED_SECONDARY_SOURCE_SHA256:
            raise ValueError("production Secondary source differs from reviewed integration")
        if sha256(secondary_obj.read_bytes()) != EXPECTED_SECONDARY_OBJECT_SHA256:
            raise ValueError("production Secondary object differs from reviewed integration")
    if init_obj is not None and ready_obj is not None:
        if sha256(INIT_SOURCE.read_bytes()) != EXPECTED_INIT_SOURCE_SHA256:
            raise ValueError("production initializer source differs from reviewed integration")
        if sha256(init_obj.read_bytes()) != EXPECTED_INIT_OBJECT_SHA256:
            raise ValueError("production initializer object differs from reviewed integration")
        if sha256(READY_SOURCE.read_bytes()) != EXPECTED_READY_SOURCE_SHA256:
            raise ValueError("production ready-gate source differs from reviewed integration")
        if sha256(ready_obj.read_bytes()) != EXPECTED_READY_OBJECT_SHA256:
            raise ValueError("production ready-gate object differs from reviewed integration")
        init_audit = ROOT / "docs/agent-work/h2-init-inplace-string-placement-audit.md"
        init_review = ROOT / "docs/agent-work/h2-init-inplace-production-review.md"
        ready_review = ROOT / "docs/agent-work/h2-ready-direct-call-review.md"
        if sha256(init_audit.read_bytes()) != EXPECTED_INIT_AUDIT_SHA256:
            raise ValueError("initializer string-placement audit differs from the reviewed input")
        if sha256(init_review.read_bytes()) != EXPECTED_INIT_REVIEW_SHA256:
            raise ValueError("initializer production review differs from the reviewed input")
        if sha256(ready_review.read_bytes()) != EXPECTED_READY_REVIEW_SHA256:
            raise ValueError("ready-gate production review differs from the reviewed input")
    audit_path = ROOT / "docs/agent-work/h2-draw-interior-entry-audit.md"
    if sha256(audit_path.read_bytes()) != EXPECTED_DRAW_AUDIT_SHA256:
        raise ValueError("Draw interior-entry audit differs from the reviewed frozen report")
    calc_sym = symbol(calc_elf, CALC_SYMBOL)
    draw_sym = symbol(draw_elf, DRAW_SYMBOL)
    helper_sym = symbol(draw_elf, DRAW_HELPER)
    format_sym = symbol(draw_elf, DRAW_LITERAL)
    calc_body = symbol_bytes(calc_elf, calc_sym)
    draw_body = symbol_bytes(draw_elf, draw_sym)
    helper_body = symbol_bytes(draw_elf, helper_sym)
    format_bytes = symbol_bytes(draw_elf, format_sym)
    secondary_sym = (symbol(secondary_elf, SECONDARY_SYMBOL)
                     if secondary_elf is not None else None)
    secondary_body = (symbol_bytes(secondary_elf, secondary_sym)
                      if secondary_elf is not None else b"")
    init_sym = symbol(init_elf, INIT_SYMBOL) if init_elf is not None else None
    init_body = symbol_bytes(init_elf, init_sym) if init_sym is not None else b""
    ready_sym = symbol(ready_elf, READY_SYMBOL) if ready_elf is not None else None
    ready_body = symbol_bytes(ready_elf, ready_sym) if ready_sym is not None else b""
    if len(calc_body) != CALC_SIZE:
        raise ValueError(f"production Calc symbol changed size: {len(calc_body)}")
    if len(draw_body) != 1464 or len(draw_body) > DRAW_SPAN:
        raise ValueError(f"production Draw main size changed or exceeds span: {len(draw_body)}")
    draw_return = verify_draw_return_boundary(draw_body)
    if len(helper_body) != 124 or format_bytes != b"%s\0":
        raise ValueError("Draw helper or format literal differs from reviewed split probe")
    if function_relocations(draw_elf, helper_sym):
        raise ValueError("outlined Draw helper unexpectedly has relocations")
    if secondary_sym is not None:
        if len(secondary_body) != SECONDARY_SIZE:
            raise ValueError(f"production Secondary symbol changed size: {len(secondary_body)}")
        if function_relocations(secondary_elf, secondary_sym):
            raise ValueError("production Secondary unexpectedly has ELF relocations")
    ready_reloc_rows = []
    if init_sym is not None and ready_sym is not None:
        if len(init_body) != INIT_SIZE or function_relocations(init_elf, init_sym):
            raise ValueError("production initializer size or relocation set changed")
        if len(ready_body) != READY_SIZE:
            raise ValueError(f"production ready-gate symbol changed size: {len(ready_body)}")
        ready_reloc_rows = function_relocations(ready_elf, ready_sym)
        if len(ready_reloc_rows) != 1:
            raise ValueError("ready gate must have exactly one R_ARM_CALL relocation")
        ready_rel = ready_reloc_rows[0]
        if (ready_rel["type"] != 28 or ready_rel["function_offset"] != READY_CALL_OFFSET
                or ready_rel["symbol"]["name"] != READY_HELPER_SYMBOL
                or ready_rel["explicit_addend"] is not None):
            raise ValueError("ready-gate relocation differs from the reviewed exact call map")
        unresolved_ready_call = struct.unpack_from("<I", ready_body, READY_CALL_OFFSET)[0]
        if unresolved_ready_call != 0xEBFFFFFE:
            raise ValueError("ready-gate R_ARM_CALL opcode/addend differs from reviewed form")

    calc_reloc_rows = function_relocations(calc_elf, calc_sym)
    calc_relocs = extract_elf_functions_detailed(calc_obj)[CALC_SYMBOL][1]
    calc_section_offset = elf_function_section_offset(calc_obj, CALC_SYMBOL)
    calc_body = normalize_local_text_addends(calc_body, calc_relocs, calc_section_offset)
    calc_body, calc_local_rows = rebase_local_text_relocations(
        calc_body, calc_relocs, CALC_CAVE_VMA)
    if len(calc_reloc_rows) != 4 or any(r["type"] != 2 for r in calc_reloc_rows):
        raise ValueError("Calc relocation set differs from four local R_ARM_ABS32 references")

    draw_relocs = function_relocations(draw_elf, draw_sym)
    calls = [r for r in draw_relocs if r["type"] == 28]
    abs_relocs = [r for r in draw_relocs if r["type"] == 2]
    if len(draw_relocs) != 8 or len(calls) != 7 or len(abs_relocs) != 1:
        raise ValueError("Draw relocation set differs from reviewed 7-call/1-ABS32 map")
    if [r["function_offset"] for r in calls] != [332, 400, 440, 480, 524, 804, 840]:
        raise ValueError("Draw helper-call relocation offsets differ from the reviewed map")
    if abs_relocs[0]["function_offset"] != 1460:
        raise ValueError("Draw literal relocation offset differs from the reviewed map")
    if any(r["symbol"]["name"] != DRAW_HELPER or r["explicit_addend"] is not None
           for r in calls):
        raise ValueError("Draw calls target an unexpected helper or have explicit addends")

    rodata_idx = format_sym["shndx"]
    if draw_elf["section_names"][rodata_idx] != ".rodata":
        raise ValueError("Draw format literal is not in local .rodata")
    abs_row = abs_relocs[0]
    abs_sym = abs_row["symbol"]
    if abs_sym["shndx"] != rodata_idx or abs_sym["type"] != 3:
        raise ValueError("Draw ABS32 must target the local .rodata section symbol")
    abs_off = abs_row["function_offset"]
    addend = struct.unpack_from("<I", draw_body, abs_off)[0]
    literal_section_offset = abs_sym["value"] + addend
    if literal_section_offset != format_sym["value"]:
        raise ValueError("Draw ABS32 addend does not resolve to kDrawTextFormat")
    if abs_row["explicit_addend"] is not None:
        raise ValueError("unexpected RELA addend at Draw format relocation")

    helper_offset = DRAW_HELPER_VMA - CALC_CAVE_VMA
    literal_offset = align_up(helper_offset + len(helper_body), 4)
    literal_vma = CALC_CAVE_VMA + literal_offset
    cave_capacity = cave_end - CALC_CAVE_VMA
    secondary_offset = (SECONDARY_CAVE_VMA - CALC_CAVE_VMA
                        if secondary_sym is not None else None)
    tail_payload_end = literal_offset + len(format_bytes)
    tail_rounded_end = align_up(tail_payload_end, 4)
    if secondary_offset is not None:
        if secondary_offset != align_up(tail_rounded_end, 4):
            raise ValueError("Secondary VMA does not immediately follow aligned Draw literal")
        secondary_end = secondary_offset + len(secondary_body)
        secondary_rounded_end = align_up(secondary_end, 4)
    else:
        secondary_end = tail_rounded_end
        secondary_rounded_end = tail_rounded_end
    if helper_offset != CALC_SIZE or secondary_rounded_end > cave_capacity:
        raise ValueError("Calc/Draw placement overlaps or exceeds audited cave tail")

    # Normalize Calc references above; resolve Draw's seven calls and one local data pointer.
    placed_draw = bytearray(draw_body)
    call_rows = []
    for rel in calls:
        off = rel["function_offset"]
        if off < 0 or off + 4 > len(placed_draw) or off & 3:
            raise ValueError("Draw call relocation offset is invalid")
        instruction = struct.unpack_from("<I", placed_draw, off)[0]
        target = DRAW_HELPER_VMA + (helper_sym["value"] - helper_sym["value"])
        encoded = patch_call(instruction, DRAW_VMA + off, target)
        struct.pack_into("<I", placed_draw, off, encoded)
        call_rows.append({"offset": off, "target": hex(target),
                          "original_word": hex(instruction), "patched_word": hex(encoded),
                          "type": "R_ARM_CALL"})
    struct.pack_into("<I", placed_draw, abs_off, literal_vma)

    placed_ready = bytearray(ready_body)
    ready_call_row = None
    if ready_sym is not None:
        original_call = struct.unpack_from("<I", placed_ready, READY_CALL_OFFSET)[0]
        struct.pack_into("<I", placed_ready, READY_CALL_OFFSET,
                         patch_call(original_call, READY_VMA + READY_CALL_OFFSET,
                                    READY_HELPER_VMA))
        ready_call_row = {"offset": READY_CALL_OFFSET,
                          "site_vma": hex(READY_VMA + READY_CALL_OFFSET),
                          "target_vma": hex(READY_HELPER_VMA),
                          "original_word": hex(original_call),
                          "patched_word": hex(struct.unpack_from("<I", placed_ready,
                                                                  READY_CALL_OFFSET)[0]),
                          "type": "R_ARM_CALL"}

    init_pool = bytearray(INIT_STRING_POOL_SIZE) if init_sym is not None else bytearray()
    if init_sym is not None:
        for pool_offset, payload, slot_size in INIT_STRINGS:
            if len(payload) > slot_size or pool_offset + slot_size > len(init_pool):
                raise ValueError("initializer string pool definition is malformed")
            init_pool[pool_offset:pool_offset + len(payload)] = payload
        rodata = game["segments"]["rodata"]
        rodata_vma, rodata_size = int(rodata["vaddr"], 16), int(rodata["size"], 16)
        rodata_file_offset = int(rodata["file_offset"], 16)
        rodata_aligned = int(rodata["aligned_size"], 16)
        if (rodata_vma != 0x003FF000 or rodata_size != 0x0002BB78
                or rodata_aligned != 0x0002C000
                or INIT_STRING_POOL_VMA != rodata_vma + rodata_size):
            raise ValueError("audited initializer string pool no longer begins at .rodata tail")
        init_pool_off = rodata_file_offset + INIT_STRING_POOL_VMA - rodata_vma
        if any(image[init_pool_off:init_pool_off + len(init_pool)]):
            raise ValueError("audited initializer string pool tail is not zero-filled")
        for pool_offset, payload, slot_size in INIT_STRINGS:
            if init_pool[pool_offset:pool_offset + len(payload)] != payload:
                raise ValueError("initializer string-pool payload differs from audited bytes")
            if any(init_pool[pool_offset + len(payload):pool_offset + slot_size]):
                raise ValueError("initializer string-pool padding is not zero-filled")

    # Both bodies are required to end in an ARM return; no truncation or veneer is allowed.
    if struct.unpack_from("<I", calc_body, len(calc_body) - 4)[0] == 0:
        raise ValueError("unexpected zero terminal word in Calc body")
    if struct.unpack_from("<I", placed_draw, len(placed_draw) - 4)[0] == 0:
        raise ValueError("unexpected zero terminal word in Draw body")

    text_offset = int(text["file_offset"], 16)
    calc_entry_off = text_offset + CALC_VMA - text_vma
    calc_cave_off = text_offset + CALC_CAVE_VMA - text_vma
    draw_main_off = text_offset + DRAW_VMA - text_vma
    helper_off = text_offset + DRAW_HELPER_VMA - text_vma
    if any(image[calc_cave_off:calc_cave_off + cave_capacity]):
        raise ValueError("audited .text page tail is not entirely zero in original image")
    if CALC_VMA < text_vma or CALC_VMA + 4 > text_vma + text_size:
        raise ValueError("Calc entry lies outside original .text")
    init_off = text_offset + INIT_VMA - text_vma if init_sym is not None else None
    ready_off = text_offset + READY_VMA - text_vma if ready_sym is not None else None
    if draw_main_off < 0 or draw_main_off + len(placed_draw) > len(image):
        raise ValueError("Draw replacement exceeds the original image")
    if draw_main_off + len(placed_draw) > text_offset + text_size:
        raise ValueError("Draw replacement exceeds original executable .text")
    replaced_end = DRAW_VMA + len(placed_draw)
    if replaced_end != 0x002CB588:
        raise ValueError("Draw in-place write interval differs from audited 1,464-byte placement")
    suffix_audit = verify_retained_draw_suffix(image, text_size)
    # The pinned original had one main-to-suffix branch and a suffix back-edge.
    # Replacing the main removes the former; the new body returns before the
    # retained suffix, so its back-edge cannot be reached from the entry.
    original_draw = image[draw_main_off:draw_main_off + DRAW_SPAN]
    word_to_suffix = struct.unpack_from("<I", original_draw, 0xDC)[0]
    suffix_edge_addr = 0x002CB748
    suffix_edge_file = text_offset + suffix_edge_addr - text_vma
    suffix_backedge = struct.unpack_from("<I", image, suffix_edge_file)[0]
    if (arm_branch_target(word_to_suffix, DRAW_VMA + 0xDC) != 0x002CB74C
            or arm_branch_target(suffix_backedge, suffix_edge_addr) != 0x002CB0B0):
        raise ValueError("pinned Draw main/suffix cross-edge map changed")

    calc_branch = arm_branch(CALC_VMA, CALC_CAVE_VMA)
    secondary_branch = (arm_branch(SECONDARY_VMA, SECONDARY_CAVE_VMA)
                        if secondary_sym is not None else None)
    cave_blob = bytearray(cave_capacity)
    cave_blob[:len(calc_body)] = calc_body
    cave_blob[helper_offset:helper_offset + len(helper_body)] = helper_body
    cave_blob[literal_offset:literal_offset + len(format_bytes)] = format_bytes
    if secondary_sym is not None:
        cave_blob[secondary_offset:secondary_end] = secondary_body
    records = [(calc_entry_off, calc_branch), (draw_main_off, bytes(placed_draw),),
               (calc_cave_off, bytes(cave_blob))]
    if secondary_branch is not None:
        secondary_entry_off = text_offset + SECONDARY_VMA - text_vma
        records.append((secondary_entry_off, secondary_branch))
    if init_sym is not None:
        if init_off is None or init_off + len(init_body) > text_offset + text_size:
            raise ValueError("in-place initializer replacement exceeds original executable .text")
        records.append((init_off, init_body))
        records.append((init_pool_off, bytes(init_pool)))
    if ready_sym is not None:
        if ready_off is None or ready_off + len(placed_ready) > text_offset + text_size:
            raise ValueError("in-place ready-gate replacement exceeds original executable .text")
        records.append((ready_off, bytes(placed_ready)))
    patched = bytearray(image)
    for offset, payload in records:
        patched[offset:offset + len(payload)] = payload
    ips = encode_ips(records, len(image))
    reapplied = apply_ips(image, ips)
    if reapplied != bytes(patched):
        raise ValueError("serialized IPS does not reproduce the combined image")
    allowed = set(range(calc_entry_off, calc_entry_off + 4))
    allowed.update(range(draw_main_off, draw_main_off + len(placed_draw)))
    allowed.update(range(calc_cave_off, calc_cave_off + len(cave_blob)))
    if secondary_branch is not None:
        allowed.update(range(secondary_entry_off, secondary_entry_off + len(secondary_branch)))
    if init_sym is not None:
        allowed.update(range(init_off, init_off + len(init_body)))
        allowed.update(range(init_pool_off, init_pool_off + len(init_pool)))
    if ready_sym is not None:
        allowed.update(range(ready_off, ready_off + len(placed_ready)))
    changed = {i for i, (a, b) in enumerate(zip(image, patched)) if a != b}
    if not changed <= allowed:
        raise ValueError("combined patch changes bytes outside authorized replacement ranges")

    manifest = {
        "schema": 1, "original_sha256": sha256(image),
        "patched_sha256": sha256(bytes(patched)), "ips_sha256": sha256(ips),
        "placements": {
            "calc_entry": {"vma": hex(CALC_VMA), "bytes": len(calc_branch),
                           "target": hex(CALC_CAVE_VMA)},
            "calc_body": {"vma": hex(CALC_CAVE_VMA), "bytes": len(calc_body),
                          "relocations": calc_local_rows},
            "draw_main": {"vma": hex(DRAW_VMA), "bytes": len(placed_draw),
                          "original_span": DRAW_SPAN,
                          "write_end_exclusive": hex(replaced_end),
                          "return_boundary": draw_return,
                          "retained_suffix": {**suffix_audit,
                                              "backedge_source": hex(suffix_edge_addr),
                                              "backedge_target": "0x2cb0b0"},
                          "helper_calls": call_rows,
                          "format_relocation": {"offset": abs_off, "target": hex(literal_vma),
                                                "section_addend": hex(addend)}},
            "draw_helper": {"vma": hex(DRAW_HELPER_VMA), "bytes": len(helper_body)},
            "draw_format_literal": {"vma": hex(literal_vma), "bytes_hex": format_bytes.hex()},
            **({"secondary_entry": {"vma": hex(SECONDARY_VMA), "bytes": len(secondary_branch),
                                     "target": hex(SECONDARY_CAVE_VMA),
                                     "original_span": SECONDARY_SPAN},
                "secondary_body": {"vma": hex(SECONDARY_CAVE_VMA),
                                   "bytes": len(secondary_body), "relocations": 0}}
               if secondary_sym is not None else {}),
            **({"initializer": {"vma": hex(INIT_VMA), "bytes": len(init_body),
                                 "original_span": INIT_SIZE,
                                 "symbol": INIT_SYMBOL,
                                 "string_pool_vma": hex(INIT_STRING_POOL_VMA),
                                 "string_pool_bytes": len(init_pool),
                                 "strings": [{"vma": hex(INIT_STRING_POOL_VMA + off),
                                              "payload_hex": payload.hex(),
                                              "slot_bytes": slot}
                                             for off, payload, slot in INIT_STRINGS]},
                "ready_gate": {"vma": hex(READY_VMA), "bytes": len(placed_ready),
                               "original_span": READY_SPAN,
                               "relocations": [ready_call_row]}}
               if init_sym is not None and ready_sym is not None else {}),
            "cave": {"start": hex(CALC_CAVE_VMA), "end_exclusive": hex(TAIL_END_VMA),
                     "capacity": cave_capacity,
                     "tail_rounded_bytes": secondary_rounded_end,
                     "remaining_bytes": cave_capacity - secondary_rounded_end},
        },
        "sources": {"calc": {"path": str(CALC_SOURCE),
                              "sha256": calc_source_hash,
                              "object_sha256": sha256(calc_obj.read_bytes()),
                              "symbol": CALC_SYMBOL},
                    "draw": {"path": str(DRAW_SOURCE),
                             "sha256": draw_source_hash,
                             "object_sha256": sha256(draw_obj.read_bytes()),
                             "symbol": DRAW_SYMBOL, "helper": DRAW_HELPER},
                    **({"secondary": {"path": str(SECONDARY_SOURCE),
                                       "sha256": sha256(SECONDARY_SOURCE.read_bytes()),
                                       "object_sha256": sha256(secondary_obj.read_bytes()),
                                       "symbol": SECONDARY_SYMBOL}}
                       if secondary_obj is not None else {}),
                    **({"initializer": {"path": str(INIT_SOURCE),
                                         "sha256": sha256(INIT_SOURCE.read_bytes()),
                                         "object_sha256": sha256(init_obj.read_bytes()),
                                         "symbol": INIT_SYMBOL},
                        "ready_gate": {"path": str(READY_SOURCE),
                                       "sha256": sha256(READY_SOURCE.read_bytes()),
                                       "object_sha256": sha256(ready_obj.read_bytes()),
                                       "symbol": READY_SYMBOL}}
                       if init_obj is not None and ready_obj is not None else {})},
        "production_symbols": {
            **({"initializer_sha256": sha256(init_body),
                "initializer_string_pool_sha256": sha256(bytes(init_pool)),
                "ready_gate_sha256": sha256(bytes(placed_ready))}
               if init_sym is not None and ready_sym is not None else {}),
            **({"secondary_sha256": sha256(secondary_body)} if secondary_sym is not None else {})},
        "ips_records": [{"offset": hex(o), "length": len(p), "sha256": sha256(p)}
                        for o, p in sorted(records)],
        "changed_bytes": len(changed),
        "limits": ["This is an offline final-address image patch; caller/runtime equivalence is not established.",
                   "Requires independent Draw interior-entry/literal audit and the reviewed source handoff before promotion."]
    }
    return bytes(patched), ips, manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=CODE_DEFAULT)
    parser.add_argument("--calc-object", type=Path, required=True)
    parser.add_argument("--draw-object", type=Path, required=True)
    parser.add_argument("--secondary-object", type=Path)
    parser.add_argument("--init-object", type=Path)
    parser.add_argument("--ready-object", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.mkdir(parents=True)
    image = args.code.read_bytes()
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    patched, ips, manifest = build_combined_patch(
        image, args.calc_object, args.draw_object, game, args.secondary_object,
        args.init_object, args.ready_object)
    (args.output / "code.combined.bin").write_bytes(patched)
    (args.output / "code.combined.ips").write_bytes(ips)
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"patched_sha256": manifest["patched_sha256"],
                      "ips_sha256": manifest["ips_sha256"],
                      "changed_bytes": manifest["changed_bytes"],
                      "manifest": str(args.output / "manifest.json")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
