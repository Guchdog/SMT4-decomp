#!/usr/bin/env python3
"""Differential test for func_0035b364 (0x0035b364) using Unicorn ARM.

The candidate body is compiled from ``src/engine/leaf_batch45_a.cpp``, its
direct calls are relocated to deterministic stubs placed at the original call
targets, and the pinned original (``extracted/exefs/code.bin``) is executed in
a separate Unicorn machine with identical fixtures.

The original reaches its per-character handlers through the member-function
pointer table at 0x00472B80, so the real table bytes are copied into the image
and every table target has a stub.  The candidate uses direct calls to the same
symbols.

Compared on every case:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log (allocator requests and every dispatched handler with
    its scanner pointer, the node handed to it and any stack arguments);
  * the full scanner object page, the UTF-16 text page, the node pool and the
    dispatch table bytes (all persistent observable memory);
  * any emulated write outside the private stack (plumbing check).

Coverage: empty/already-finished scans, cursor in the middle, truncated length,
space/ideographic-space skipping, every one of the sixteen dispatch-table
entries, characters on both sides of the 0x20..0x7E table range (0x1F, 0x7F,
0x80, 0xFFFF), "\\Q".."\\E" verbatim mode including its last-character
boundaries, a stray "\\E" abort, the trailing-backslash handler result, all
node-allocator failure positions, handler non-zero result propagation, depth
sign boundaries, pre-existing list nodes and entry-field overwriting.
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
SOURCE = ROOT / "src/engine/leaf_batch45_a.cpp"
OUT_DIR = ROOT / "build/test_leaf_0035b364"

FUNC_ADDR = 0x0035B364
FUNC_SIZE = 616

# Original dispatch table: 0x5F entries of 8 bytes ({handler, this-adjust}),
# indexed by character - 0x20 (the object address is 0x00472B80, and the
# scanner indexes with the raw character, so the first live entry for ' ' is
# 0x00472B80 + 8 * 0x20 = 0x00472C80).  Every shipped adjust word is zero.
DISPATCH_TABLE_ADDR = 0x00472C80
DISPATCH_TABLE_SIZE = 0x5F * 8

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00500000  # covers the function, every stub and 0x00472B80
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
SCANNER_ADDR = 0x00710000
SCANNER_SIZE = 0x00001000
TEXT_ADDR = 0x00720000
TEXT_SIZE = 0x00001000
NODES_ADDR = 0x00730000
NODES_SIZE = 0x00001000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Original direct-call targets.
STUB_ALLOC = 0x00238C44

STUB_0035B254 = 0x0035B254  # '.'
STUB_0035B294 = 0x0035B294  # '+'
STUB_0035B2D4 = 0x0035B2D4  # '$'
STUB_0035B324 = 0x0035B324  # '-'
STUB_0035BBC4 = 0x0035BBC4  # default
STUB_0035BBF8 = 0x0035BBF8  # '*'
STUB_0035BC38 = 0x0035BC38  # '?'
STUB_0035BC78 = 0x0035BC78  # '&'
STUB_0035BCF8 = 0x0035BCF8  # '\'
STUB_0035BD64 = 0x0035BD64  # '{'
STUB_0035BF8C = 0x0035BF8C  # '^'
STUB_0035BFCC = 0x0035BFCC  # '|'
STUB_0035C128 = 0x0035C128  # '('
STUB_0035C168 = 0x0035C168  # ')'
STUB_0035C1A8 = 0x0035C1A8  # '['
STUB_0035C210 = 0x0035C210  # ']'

STUB_NAMES = {
    STUB_ALLOC: "func_00238c44",
    STUB_0035B254: "func_0035b254",
    STUB_0035B294: "func_0035b294",
    STUB_0035B2D4: "func_0035b2d4",
    STUB_0035B324: "func_0035b324",
    STUB_0035BBC4: "func_0035bbc4",
    STUB_0035BBF8: "func_0035bbf8",
    STUB_0035BC38: "func_0035bc38",
    STUB_0035BC78: "func_0035bc78",
    STUB_0035BCF8: "func_0035bcf8",
    STUB_0035BD64: "func_0035bd64",
    STUB_0035BF8C: "func_0035bf8c",
    STUB_0035BFCC: "func_0035bfcc",
    STUB_0035C128: "func_0035c128",
    STUB_0035C168: "func_0035c168",
    STUB_0035C1A8: "func_0035c1a8",
    STUB_0035C210: "func_0035c210",
}

HANDLER_STUBS = [address for address in STUB_NAMES if address != STUB_ALLOC]

CALLEE_SAVED = {
    "r4": arm.UC_ARM_REG_R4,
    "r5": arm.UC_ARM_REG_R5,
    "r6": arm.UC_ARM_REG_R6,
    "r7": arm.UC_ARM_REG_R7,
    "r8": arm.UC_ARM_REG_R8,
    "r9": arm.UC_ARM_REG_R9,
    "r10": arm.UC_ARM_REG_R10,
    "r11": arm.UC_ARM_REG_R11,
}
CALLEE_SAVED_START = {
    "r4": 0x44444444,
    "r5": 0x55555555,
    "r6": 0x66666666,
    "r7": 0x77777777,
    "r8": 0x88888888,
    "r9": 0x99999999,
    "r10": 0xAAAAAAAA,
    "r11": 0xBBBBBBBB,
}

# Scanner field offsets (recovered from the ARM body).
OFF_LIST_NEXT = 0x00
OFF_LIST_PREV = 0x04
OFF_ALLOCATOR = 0x08
OFF_TEXT = 0x0C
OFF_CURSOR = 0x10
OFF_LENGTH = 0x14
OFF_DEPTH = 0x18

# Node field offsets.
NODE_NEXT = 0x00
NODE_PREV = 0x04
NODE_TYPE = 0x08
NODE_CHAR = 0x0A
NODE_VALUE = 0x0C
NODE_STRIDE = 0x10


# --------------------------------------------------------------------- images
def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def get_dispatch_table() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(DISPATCH_TABLE_ADDR - 0x00100000)
        return f.read(DISPATCH_TABLE_SIZE)


def elf_sections(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize = struct.unpack_from("<H", data, 46)[0]
    e_shnum = struct.unpack_from("<H", data, 48)[0]
    e_shstrndx = struct.unpack_from("<H", data, 50)[0]
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    shstr = sections[e_shstrndx]
    shstrtab = data[shstr[4] : shstr[4] + shstr[5]]
    result: dict[str, bytes] = {}
    for section in sections:
        end = shstrtab.find(b"\x00", section[0])
        name = shstrtab[section[0] : end].decode("ascii", errors="replace")
        result[name] = data[section[4] : section[4] + section[5]]
    return result


def get_symbol_offset(obj_file: Path, name: str) -> int:
    data = obj_file.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize = struct.unpack_from("<H", data, 46)[0]
    e_shnum = struct.unpack_from("<H", data, 48)[0]
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    symtab = [section for section in sections if section[1] == 2][0]
    strtab = sections[symtab[6]]
    for index in range(symtab[5] // 16):
        st_name, st_value, _st_size, _info, _other, _shndx = struct.unpack_from(
            "<IIIBBH", data, symtab[4] + index * 16
        )
        symbol = data[strtab[4] + st_name :].split(b"\x00")[0].decode(
            "ascii", errors="replace"
        )
        if symbol == name:
            return st_value
    raise RuntimeError(f"symbol {name} not found in {obj_file}")


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0035b364" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"func_0035b364 not found in {obj_file}: {sorted(funcs)}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    func_sym_offset = get_symbol_offset(obj_file, "func_0035b364")

    for rel in relocs:
        if rel.relocation_type == 28:  # R_ARM_CALL
            target = None
            for address, name in STUB_NAMES.items():
                if f"{address:08x}" in rel.symbol_name.lower():
                    target = address
                    break
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
            displacement = (target - (FUNC_ADDR + rel.offset + 8)) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
            )
        elif rel.relocation_type == 2:  # R_ARM_ABS32
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            if rel.symbol_name not in ("", ".text"):
                raise RuntimeError(
                    f"unexpected ABS32 relocation against {rel.symbol_name!r}"
                )
            # Compatibility-switch table entries are local .text labels.
            if not (func_sym_offset <= addend < func_sym_offset + len(code_raw)):
                raise RuntimeError(
                    f"ABS32 addend 0x{addend:x} outside the function body"
                )
            struct.pack_into(
                "<I",
                code,
                rel.offset,
                FUNC_ADDR + (addend - func_sym_offset),
            )
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name!r}"
            )
    return bytes(code)


def compile_candidate(source: Path, obj_file: Path) -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    res = compile_tu_armv6k(source, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_baseline() -> bytes:
    return compile_candidate(SOURCE, OUT_DIR / "leaf_batch45_a.o")


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    return compile_candidate(mutant_src, OUT_DIR / f"mutant_{name}.o")


# ------------------------------------------------------------------ fixtures
def units(*values: int) -> list[int]:
    return list(values)


def ascii_units(text: str) -> list[int]:
    return [ord(character) for character in text]


def base_case(name: str, text: list[int], **overrides) -> dict:
    case = {
        "name": name,
        "text": list(text),
        "cursor": 0,
        "length": len(text),
        "depth": 0,
        "fail_alloc_at": None,
        "force_result": {},
        "initial_node": None,
        "scanner_fill": 0xA5,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- entry / termination
    cases.append(base_case("empty text", []))
    cases.append(base_case("cursor already at length", [0x41, 0x42], cursor=2))
    cases.append(base_case("cursor at the last character", ascii_units("ABCD"),
                           cursor=3))
    cases.append(base_case("single last character", units(0x41), cursor=0))
    cases.append(base_case("single character", [0x41]))
    cases.append(base_case("two characters", ascii_units("AB")))
    cases.append(base_case("start in the middle", ascii_units("ABCD"), cursor=2))
    cases.append(base_case("truncated length", ascii_units("ABCD"), length=3))
    cases.append(
        base_case("entry overwrites scanner fields",
                  ascii_units("AB"), cursor=2, depth=0x7FFFFFFF)
    )

    # --- whitespace skipping
    cases.append(base_case("space then character", units(0x20, 0x41)))
    cases.append(base_case("ideographic space then character", units(0x3000, 0x41)))
    cases.append(base_case("space only", units(0x20)))
    cases.append(base_case("ideographic space only", units(0x3000)))
    cases.append(
        base_case("interleaved spaces", units(0x41, 0x20, 0x3000, 0x42, 0x20))
    )

    # --- verbatim mode
    cases.append(base_case("verbatim two characters", units(0x5C, 0x51, 0x41, 0x42)))
    cases.append(
        base_case("verbatim terminated", units(0x5C, 0x51, 0x41, 0x42, 0x5C, 0x45))
    )
    cases.append(base_case("verbatim empty", units(0x5C, 0x51, 0x5C, 0x45)))
    cases.append(base_case("verbatim unterminated", units(0x5C, 0x51, 0x41)))
    cases.append(
        base_case("verbatim skips spaces",
                  units(0x5C, 0x51, 0x20, 0x3000, 0x41, 0x5C, 0x45))
    )
    cases.append(
        base_case("verbatim literal backslash", units(0x5C, 0x51, 0x5C, 0x5C, 0x45))
    )
    cases.append(
        base_case("verbatim backslash as last unit", units(0x5C, 0x51, 0x5C))
    )
    cases.append(
        base_case("verbatim escape ending at the boundary",
                  units(0x5C, 0x51, 0x41, 0x5C, 0x45))
    )
    cases.append(
        base_case("verbatim spaces to end", units(0x5C, 0x51, 0x20, 0x3000))
    )
    cases.append(
        base_case("verbatim then plain text", units(0x5C, 0x51, 0x41, 0x5C, 0x45, 0x42))
    )

    # --- stray end-of-verbatim abort
    cases.append(base_case("stray verbatim end", units(0x5C, 0x45)))
    cases.append(base_case("character then stray end", units(0x41, 0x5C, 0x45)))
    cases.append(
        base_case("stray end after whitespace", units(0x20, 0x5C, 0x45))
    )

    # --- dispatch table: every entry, depth 0
    cases.append(base_case("dollar", units(0x24)))
    cases.append(base_case("ampersand", units(0x26)))
    cases.append(base_case("open parenthesis", units(0x28)))
    cases.append(base_case("close parenthesis", units(0x29)))
    cases.append(base_case("asterisk", units(0x2A)))
    cases.append(base_case("plus", units(0x2B)))
    cases.append(base_case("minus", units(0x2D)))
    cases.append(base_case("dot", units(0x2E)))
    cases.append(base_case("question mark", units(0x3F)))
    cases.append(base_case("open bracket", units(0x5B)))
    cases.append(base_case("backslash escaped character", units(0x5C, 0x41)))
    cases.append(base_case("close bracket", units(0x5D)))
    cases.append(base_case("caret", units(0x5E)))
    cases.append(base_case("open brace", units(0x7B, 0x31, 0x7D)))
    cases.append(base_case("close brace as plain text", units(0x7D)))
    cases.append(base_case("pipe", units(0x7C)))

    # --- dispatch table: every entry, depth > 0 (open bracket raises depth)
    cases.append(
        base_case(
            "all specials inside brackets",
            units(0x5B, 0x24, 0x26, 0x28, 0x29, 0x2A, 0x2B, 0x2D, 0x2E, 0x3F,
                  0x5E, 0x7C, 0x5D),
        )
    )
    cases.append(base_case("nested brackets", units(0x5B, 0x5B, 0x41, 0x5D, 0x5D)))
    cases.append(
        base_case("bracket caret form", units(0x5B, 0x5E, 0x41, 0x5D))
    )
    cases.append(
        base_case("bracket caret at the length boundary", units(0x5B, 0x5E))
    )

    # --- '&' selection
    cases.append(base_case("ampersand doubled", units(0x26, 0x26)))
    cases.append(base_case("ampersand doubled in brackets", units(0x5B, 0x26, 0x26, 0x5D)))
    cases.append(base_case("ampersand at the length boundary", units(0x5B, 0x26)))

    # --- '{' numeric forms
    for form in ("{1}", "{0}", "{65535}", "{65536}", "{1,2}", "{65535,0}",
                 "{1,2", "{,}", "{12}", "{", "{1", "{1,}", "{1,x}"):
        cases.append(base_case(f"brace form {form}", ascii_units(form)))
    cases.append(base_case("brace form inside brackets",
                           units(0x5B, *ascii_units("{1}"), 0x5D)))

    # --- table range boundaries and non-ASCII units
    for value in (0x1F, 0x7F, 0x80, 0x100, 0x3001, 0xFFFF, 0x0021, 0x007E):
        cases.append(base_case(f"plain unit 0x{value:04x}", units(value)))
        cases.append(base_case(f"bracketed unit 0x{value:04x}",
                               units(0x5B, value, 0x5D)))

    # --- allocator failures at every node position
    for fail_at in (0, 1, 2):
        cases.append(
            base_case(f"allocator fails at allocation {fail_at}",
                      ascii_units("AB"), fail_alloc_at=fail_at)
        )
    cases.append(
        base_case("allocator fails at the terminator",
                  ascii_units("AB"), fail_alloc_at=2)
    )
    cases.append(
        base_case("allocator fails in verbatim mode",
                  units(0x5C, 0x51, 0x41, 0x42), fail_alloc_at=1)
    )

    # --- handler results propagate
    cases.append(
        base_case("dot handler reports 5", units(0x2E),
                  force_result={(STUB_0035B254, 0): 5})
    )
    cases.append(
        base_case("open bracket handler reports 7", units(0x5B),
                  force_result={(STUB_0035C1A8, 0): 7})
    )
    cases.append(
        base_case("second handler invocation reports 9",
                  units(0x24, 0x24),
                  force_result={(STUB_0035B2D4, 1): 9})
    )
    cases.append(
        base_case("negative handler result propagates",
                  units(0x7C), force_result={(STUB_0035BFCC, 0): -1})
    )

    # --- pre-existing circular list node
    cases.append(
        base_case("pre-existing list node", ascii_units("A"),
                  initial_node=NODES_ADDR + 0x200)
    )
    cases.append(
        base_case("pre-existing list node, two characters", ascii_units("AB"),
                  initial_node=NODES_ADDR + 0x200)
    )
    return cases


# --------------------------------------------------------------------- runner
def read_c_string(uc, address: int, limit: int = 32) -> bytes:
    out = bytearray()
    for index in range(limit):
        byte = uc.mem_read(address + index, 1)[0]
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


class ScannerRunner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(SCANNER_ADDR, SCANNER_SIZE)
        self.uc.mem_map(TEXT_ADDR, TEXT_SIZE)
        self.uc.mem_map(NODES_ADDR, NODES_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.alloc_index = 0
        self.call_index: dict[int, int] = {}
        self.case: dict = {}

    # ------------------------------------------------------------ primitives
    def _rd32(self, address: int) -> int:
        return struct.unpack("<I", self.uc.mem_read(address, 4))[0]

    def _wr32(self, address: int, value: int) -> None:
        self.uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))

    def _rd16(self, address: int) -> int:
        return struct.unpack("<H", self.uc.mem_read(address, 2))[0]

    def _wr16(self, address: int, value: int) -> None:
        self.uc.mem_write(address, struct.pack("<H", value & 0xFFFF))

    def _wr8(self, address: int, value: int) -> None:
        self.uc.mem_write(address, bytes([value & 0xFF]))

    def _rd_s32(self, address: int) -> int:
        return struct.unpack("<i", self.uc.mem_read(address, 4))[0]

    def _normalise(self, value: int) -> object:
        if STACK_ADDR <= value < STACK_ADDR + STACK_SIZE:
            return "<stack>"
        return value

    # ----------------------------------------------------------------- stubs
    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address],) + tuple(args))

    def _node(self, slot_address: int) -> int:
        return self._rd32(slot_address)

    def _char_at(self, text: int, cursor: int) -> int:
        return self._rd16(text + cursor * 2)

    def _model_handler(self, address: int, node: int, self_address: int,
                       cursor: int, length: int, depth: int, text: int) -> int:
        """Deterministic model of the real handler's observable effects."""
        if address == STUB_0035BBC4:  # default: literal character node
            self._wr8(node + NODE_TYPE, 0x00)
            self._wr16(node + NODE_CHAR, self._char_at(text, cursor))
            self._wr32(self_address + OFF_CURSOR, cursor + 1)
            return 0

        if address == STUB_0035B254:  # '.'
            if depth > 0:
                self._wr8(node + NODE_TYPE, 0x00)
                self._wr16(node + NODE_CHAR, 0x2E)
            else:
                self._wr8(node + NODE_TYPE, 0x07)
                self._wr8(node + NODE_CHAR, 0x00)
            self._wr32(self_address + OFF_CURSOR, cursor + 1)
            return 0

        if address == STUB_0035B294:  # '+'
            if depth > 0:
                self._wr8(node + NODE_TYPE, 0x00)
                self._wr16(node + NODE_CHAR, 0x2B)
            else:
                self._wr8(node + NODE_TYPE, 0x0D)
            self._wr32(self_address + OFF_CURSOR, cursor + 1)
            return 0

        if address == STUB_0035B2D4:  # '$'
            if depth > 0:
                self._wr8(node + NODE_TYPE, 0x00)
                self._wr16(node + NODE_CHAR, 0x24)
            else:
                self._wr8(node + NODE_TYPE, 0x11)
                self._wr8(node + NODE_CHAR, 0x01)
            self._wr32(self_address + OFF_CURSOR, cursor + 1)
            return 0

        if address == STUB_0035B324:  # '-'
            if depth > 0:
                self._wr8(node + NODE_TYPE, 0x00)
                self._wr16(node + NODE_CHAR, 0x2D)
            else:
                self._wr8(node + NODE_TYPE, 0x05)
            self._wr32(self_address + OFF_CURSOR, cursor + 1)
            return 0

        if address == STUB_0035BBF8:  # '*'
            if depth > 0:
                self._wr8(node + NODE_TYPE, 0x00)
                self._wr16(node + NODE_CHAR, 0x2A)
            else:
                self._wr8(node + NODE_TYPE, 0x0C)
            self._wr32(self_address + OFF_CURSOR, cursor + 1)
            return 0

        if address == STUB_0035BC38:  # '?'
            if depth > 0:
                self._wr8(node + NODE_TYPE, 0x00)
                self._wr16(node + NODE_CHAR, 0x3F)
            else:
                self._wr8(node + NODE_TYPE, 0x0B)
            self._wr32(self_address + OFF_CURSOR, cursor + 1)
            return 0

        if address == STUB_0035BC78:  # '&'
            doubled = (depth > 0 and cursor != length - 1 and
                       self._char_at(text, cursor + 1) == 0x26)
            if doubled:
                self._wr8(node + NODE_TYPE, 0x06)
                self._wr32(self_address + OFF_CURSOR, cursor + 2)
            else:
                self._wr8(node + NODE_TYPE, 0x00)
                self._wr16(node + NODE_CHAR, 0x26)
                self._wr32(self_address + OFF_CURSOR, cursor + 1)
            return 0

        if address == STUB_0035BCF8:  # '\'
            self._wr32(self_address + OFF_CURSOR, cursor + 1)
            if cursor + 1 == length:
                return 4
            self._wr8(node + NODE_TYPE, 0x00)
            self._wr16(node + NODE_CHAR, self._char_at(text, cursor + 1))
            self._wr32(self_address + OFF_CURSOR, cursor + 2)
            return 0

        if address == STUB_0035BD64:  # '{'
            if depth > 0:
                self._wr8(node + NODE_TYPE, 0x00)
                self._wr16(node + NODE_CHAR, 0x7B)
                self._wr32(self_address + OFF_CURSOR, cursor + 1)
                return 0
            return self._model_brace(node, self_address, cursor, length, text)

        if address == STUB_0035BF8C:  # '^'
            if depth > 0:
                self._wr8(node + NODE_TYPE, 0x00)
                self._wr16(node + NODE_CHAR, 0x5E)
            else:
                self._wr8(node + NODE_TYPE, 0x11)
            self._wr32(self_address + OFF_CURSOR, cursor + 1)
            return 0

        if address == STUB_0035BFCC:  # '|'
            if depth > 0:
                self._wr8(node + NODE_TYPE, 0x00)
                self._wr16(node + NODE_CHAR, 0x7C)
            else:
                self._wr8(node + NODE_TYPE, 0x01)
            self._wr32(self_address + OFF_CURSOR, cursor + 1)
            return 0

        if address == STUB_0035C128:  # '('
            if depth > 0:
                self._wr8(node + NODE_TYPE, 0x00)
                self._wr16(node + NODE_CHAR, 0x28)
            else:
                self._wr8(node + NODE_TYPE, 0x09)
            self._wr32(self_address + OFF_CURSOR, cursor + 1)
            return 0

        if address == STUB_0035C168:  # ')'
            if depth > 0:
                self._wr8(node + NODE_TYPE, 0x00)
                self._wr16(node + NODE_CHAR, 0x29)
            else:
                self._wr8(node + NODE_TYPE, 0x0A)
            self._wr32(self_address + OFF_CURSOR, cursor + 1)
            return 0

        if address == STUB_0035C1A8:  # '['
            caret = (cursor != length - 1 and
                     self._char_at(text, cursor + 1) == 0x5E)
            if caret:
                self._wr8(node + NODE_TYPE, 0x03)
                self._wr32(self_address + OFF_CURSOR, cursor + 2)
            else:
                self._wr8(node + NODE_TYPE, 0x02)
                self._wr32(self_address + OFF_CURSOR, cursor + 1)
            self._wr32(self_address + OFF_DEPTH,
                       self._rd32(self_address + OFF_DEPTH) + 1)
            return 0

        if address == STUB_0035C210:  # ']'
            self._wr8(node + NODE_TYPE, 0x04)
            self._wr32(self_address + OFF_CURSOR, cursor + 1)
            self._wr32(self_address + OFF_DEPTH,
                       self._rd32(self_address + OFF_DEPTH) - 1)
            return 0

        raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def _model_brace(self, node: int, self_address: int, cursor: int,
                     length: int, text: int) -> int:
        """Deterministic numeric-brace parser model (0x0035BD64)."""
        index = cursor + 1
        self._wr32(self_address + OFF_CURSOR, index)
        if index == length:
            return 3

        def digits(position: int) -> tuple[int, int] | None:
            if position == length:
                return None
            unit = self._char_at(text, position)
            if unit < 0x30 or unit > 0x39:
                return None
            value = 0
            while position != length:
                unit = self._char_at(text, position)
                if unit < 0x30 or unit > 0x39:
                    break
                value = value * 10 + (unit - 0x30)
                if value >= 0x10000:
                    return None
                position += 1
            return value, position

        first = digits(index)
        if first is None:
            self._wr32(self_address + OFF_CURSOR, index)
            return 3
        first_value, index = first
        self._wr32(self_address + OFF_CURSOR, index)
        if index == length:
            return 3
        unit = self._char_at(text, index)
        if unit == 0x7D:
            self._wr16(node + NODE_CHAR, first_value)
            self._wr8(node + NODE_TYPE, 0x0E)
            self._wr32(self_address + OFF_CURSOR, index + 1)
            return 0
        if unit != 0x2C:
            return 3
        index += 1
        self._wr32(self_address + OFF_CURSOR, index)
        if index == length:
            return 3
        second = digits(index)
        if second is None:
            return 3
        second_value, index = second
        self._wr32(self_address + OFF_CURSOR, index)
        if index == length:
            return 3
        if self._char_at(text, index) != 0x7D:
            return 3
        self._wr16(node + NODE_CHAR, first_value)
        self._wr16(node + NODE_VALUE, second_value)
        self._wr8(node + NODE_TYPE, 0x10)
        self._wr32(self_address + OFF_CURSOR, index + 1)
        return 0

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)

        if address == STUB_ALLOC:
            index = self.alloc_index
            self.alloc_index += 1
            self._log(address, r0, r1)
            if self.case.get("fail_alloc_at") == index:
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
            else:
                uc.reg_write(arm.UC_ARM_REG_R0, NODES_ADDR + index * NODE_STRIDE)
            return

        node = self._node(r1)
        cursor = self._rd32(r0 + OFF_CURSOR)
        length = self._rd32(r0 + OFF_LENGTH)
        depth = self._rd_s32(r0 + OFF_DEPTH)
        text = self._rd32(r0 + OFF_TEXT)
        invocation = self.call_index.get(address, 0)
        self.call_index[address] = invocation + 1

        self._log(address, r0, self._normalise(r1), node, cursor)

        forced = self.case.get("force_result", {}).get((address, invocation))
        if forced is not None:
            result = forced
        else:
            result = self._model_handler(address, node, r0, cursor, length,
                                         depth, text)
        uc.reg_write(arm.UC_ARM_REG_R0, result & 0xFFFFFFFF)

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, table: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.alloc_index = 0
        self.call_index = {}
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(DISPATCH_TABLE_ADDR, table)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        # Scanner page: sentinel list, hostile field values that the entry
        # bounds must overwrite, and the caller-visible cursor.
        scanner = bytearray([case["scanner_fill"] & 0xFF]) * SCANNER_SIZE
        self.uc.mem_write(SCANNER_ADDR, bytes(scanner))
        self._wr32(SCANNER_ADDR + OFF_LIST_NEXT, SCANNER_ADDR)
        self._wr32(SCANNER_ADDR + OFF_LIST_PREV, SCANNER_ADDR)
        self._wr32(SCANNER_ADDR + OFF_ALLOCATOR, 0x11111111)
        self._wr32(SCANNER_ADDR + OFF_TEXT, 0x22222222)
        self._wr32(SCANNER_ADDR + OFF_CURSOR, case["cursor"] & 0xFFFFFFFF)
        self._wr32(SCANNER_ADDR + OFF_LENGTH, 0x33333333)
        self._wr32(SCANNER_ADDR + OFF_DEPTH, case["depth"] & 0xFFFFFFFF)

        # Text page.
        text = bytearray(TEXT_SIZE)
        for index, unit in enumerate(case["text"]):
            struct.pack_into("<H", text, index * 2, unit & 0xFFFF)
        self.uc.mem_write(TEXT_ADDR, bytes(text))

        # Node pool.
        self.uc.mem_write(NODES_ADDR, bytes(NODES_SIZE))
        initial = case.get("initial_node")
        if initial is not None:
            self._wr32(initial + NODE_NEXT, SCANNER_ADDR)
            self._wr32(initial + NODE_PREV, SCANNER_ADDR)
            self._wr8(initial + NODE_TYPE, 0x5A)
            self._wr16(initial + NODE_CHAR, 0x1234)
            self._wr32(SCANNER_ADDR + OFF_LIST_NEXT, initial)
            self._wr32(SCANNER_ADDR + OFF_LIST_PREV, initial)

        self.writes = []
        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SCANNER_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x00ABCDEF)
        self.uc.reg_write(arm.UC_ARM_REG_R2, TEXT_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R3, case["length"] & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            if address is None:
                continue
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_scanner = SCANNER_ADDR <= address < SCANNER_ADDR + SCANNER_SIZE
            in_nodes = NODES_ADDR <= address < NODES_ADDR + NODES_SIZE
            if not (in_stack or in_scanner or in_nodes):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self.call_log,
            "memory": {
                "scanner": bytes(self.uc.mem_read(SCANNER_ADDR, SCANNER_SIZE)),
                "text": bytes(self.uc.mem_read(TEXT_ADDR, TEXT_SIZE)),
                "nodes": bytes(self.uc.mem_read(NODES_ADDR, NODES_SIZE)),
                "table": bytes(
                    self.uc.mem_read(DISPATCH_TABLE_ADDR, DISPATCH_TABLE_SIZE)
                ),
            },
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig=" + repr(orig["call_log"])
            + "\n    cand=" + repr(cand["call_log"])
        )
    for key in ("scanner", "text", "nodes", "table"):
        if orig["memory"][key] != cand["memory"][key]:
            left = orig["memory"][key]
            right = cand["memory"][key]
            diff = next(
                (index for index, (a, b) in enumerate(zip(left, right)) if a != b),
                None,
            )
            problems.append(f"memory {key} differs at byte {diff}")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def run_case_set(orig_code, cand_code, table, cases) -> int:
    passed = 0
    for case in cases:
        orig = ScannerRunner().run(orig_code, table, case)
        cand = ScannerRunner().run(cand_code, table, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  (ret={orig['ret']}, "
              f"{len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing func_0035b364 (0x0035b364)...")
    orig_code = get_orig_bytes()
    table = get_dispatch_table()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B, "
        f"dispatch table {len(table)} B."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, table, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("verbatim_end", "constexpr u16 kVerbatimEnd = 0x45;",
         "constexpr u16 kVerbatimEnd = 0x46;"),
        ("ideographic_space", "constexpr u16 kIdeographicSpace = 0x3000;",
         "constexpr u16 kIdeographicSpace = 0x3001;"),
        ("terminator_type", "constexpr u8 kTerminatorType = 0x12;",
         "constexpr u8 kTerminatorType = 0x11;"),
        ("space", "constexpr u16 kSpace = 0x0020;",
         "constexpr u16 kSpace = 0x0009;"),
        ("quote_start", "constexpr u16 kVerbatimStart = 0x51;",
         "constexpr u16 kVerbatimStart = 0x50;"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = ScannerRunner().run(orig_code, table, case)
            bad = ScannerRunner().run(mutant_code, table, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
