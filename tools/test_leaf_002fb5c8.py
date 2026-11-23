#!/usr/bin/env python3
"""Differential test for engine_func_002fb5c8 (0x002fb5c8, AsdGfx_ReleaseResource).

Compiles src/engine/leaf_batch41_c.cpp, extracts the reconstructed body,
resolves its three direct calls to deterministic stubs and its one rodata
reference, then runs the pinned original (extracted/exefs/code.bin) and the
candidate in identical Unicorn ARM machines.

Compared outputs:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log: 0x002C3290 string length, 0x002C31E8 name lookup
    (slot contents + key text + key length), 0x002A34A4 setter (element, mode,
    s0 bit pattern) and the indirect vtable query (receiver address);
  * every observable fixture page (low memory, manager/type-info page, model,
    vtable, element, descriptor, table, found, value, chain, rodata);
  * every non-stack write (address, size, value), including the +0x21C status
    store and the latent 0x21C store when the second type match fails.

Coverage: both global gates, null/zero-count/negative-count vectors, the signed
loop bound, both type-match outcomes and a null-model low-vector path, absent
descriptor/table, null find result, zero and non-zero found relative links,
tag bit set/clear (including the latent low read of 0x10), kind <= 0 / == 2 /
other positive / signed boundaries, the setter gate re-read, a setter that
shrinks the vector, and a setter that clears the manager gate.

Negative controls mutate the tag mask, the kind offset, the status offset, the
setter mode and the `<= 0` weight field; each mutant must be detected.
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
SOURCE = ROOT / "src/engine/leaf_batch41_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_002fb5c8"

FUNC_ADDR = 0x002FB5C8
FUNC_SIZE = 472

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers the function and every direct stub below 0x3F0000
LOW_ADDR = 0x00000000
LOW_SIZE = 0x00001000
MGR_ADDR = 0x00460000  # covers 0x00464AF0 and the two type-info identities
MGR_SIZE = 0x00020000
RODATA_ADDR = 0x00700000
RODATA_SIZE = 0x00001000
MODEL_ADDR = 0x00710000
PAGE_SIZE = 0x00001000
VTABLE_ADDR = 0x00711000
BEGIN_ADDR = 0x00712000
ELEM_ADDR = 0x00720000
DESC_ADDR = 0x00730000
TABLE_ADDR = 0x00740000
FOUND_ADDR = 0x00745000
VALUE_ADDR = 0x00748000
CHAIN_ADDR = 0x00750000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_STRLEN = 0x002C3290
STUB_FIND = 0x002C31E8
STUB_SETTER = 0x002A34A4
STUB_QUERY = 0x003E0000

STUB_NAMES = {
    STUB_STRLEN: "strlen_002c3290",
    STUB_FIND: "find_002c31e8",
    STUB_SETTER: "setter_002a34a4",
    STUB_QUERY: "vtable_query",
}

MODEL_TYPE_INFO = 0x00472180
STATUS_TYPE_INFO = 0x00472288

MANAGER = 0x00464AF0
MANAGER_FLAG01 = 0x01
MANAGER_PTR80 = 0x80
MANAGER_F60 = 0x60
MANAGER_F64 = 0x64

ELEM_STRIDE = 0x80
DESC_STRIDE = 0x100
TABLE_STRIDE = 0x40
FOUND_STRIDE = 0x40
VALUE_STRIDE = 0x40
CHAIN_STRIDE = 0x10

F60_BITS = 0x3FC00000  # 1.5f
F64_BITS = 0xC0100000  # -2.25f
SENTINEL_21C = 0xDEADBEEF

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

FIXTURE_PAGES = (
    ("low", LOW_ADDR, LOW_SIZE),
    ("mgr", MGR_ADDR, MGR_SIZE),
    ("model", MODEL_ADDR, PAGE_SIZE),
    ("vtable", VTABLE_ADDR, PAGE_SIZE),
    ("begin", BEGIN_ADDR, PAGE_SIZE),
    ("elem", ELEM_ADDR, PAGE_SIZE),
    ("desc", DESC_ADDR, PAGE_SIZE),
    ("table", TABLE_ADDR, PAGE_SIZE),
    ("found", FOUND_ADDR, PAGE_SIZE),
    ("value", VALUE_ADDR, PAGE_SIZE),
    ("chain", CHAIN_ADDR, PAGE_SIZE),
    ("rodata", RODATA_ADDR, RODATA_SIZE),
)


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


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


def extract_candidate(obj_file: Path) -> tuple[bytes, bytes]:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "002fb5c8" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_002fb5c8 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    stub_addresses = {
        "002c3290": STUB_STRLEN,
        "002c31e8": STUB_FIND,
        "002a34a4": STUB_SETTER,
    }
    for rel in relocs:
        if rel.relocation_type == 28:  # R_ARM_CALL
            target = None
            for key, address in stub_addresses.items():
                if key in rel.symbol_name:
                    target = address
                    break
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
            pc = FUNC_ADDR + rel.offset + 8
            displacement = (target - pc) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
            )
        elif rel.relocation_type == 2:  # R_ARM_ABS32 into .rodata ("shadow")
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            struct.pack_into("<I", code, rel.offset, RODATA_ADDR + addend)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )

    rodata = elf_sections(obj_file).get(".rodata", b"")
    if b"shadow\x00" not in rodata:
        raise RuntimeError("could not locate the 'shadow' literal in .rodata")
    return bytes(code), rodata


def compile_candidate(path: Path = SOURCE, obj_name: str = "leaf_batch41_c.o"):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / obj_name
    res = compile_tu_armv6k(path, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    return extract_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str):
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    return compile_candidate(mutant_src, f"mutant_{name}.o")


# --------------------------------------------------------------------- fixtures
def read_c_string(uc, address: int, limit: int = 64) -> bytes:
    out = bytearray()
    try:
        for index in range(limit):
            byte = uc.mem_read(address + index, 1)[0]
            if byte == 0:
                break
            out.append(byte)
    except Exception:
        return bytes(out)
    return bytes(out)


def table_address(index: int) -> int:
    return TABLE_ADDR + index * TABLE_STRIDE


def found_address(index: int) -> int:
    return FOUND_ADDR + index * FOUND_STRIDE


def value_address(index: int) -> int:
    return VALUE_ADDR + index * VALUE_STRIDE


def chain_address(index: int) -> int:
    return CHAIN_ADDR + index * CHAIN_STRIDE


def build_pages(case: dict) -> dict[str, tuple[int, bytes]]:
    pages: dict[str, bytearray] = {
        name: bytearray(size) for name, _addr, size in FIXTURE_PAGES
    }

    # Manager / type-info page.
    mgr = pages["mgr"]
    mgr[MANAGER - MGR_ADDR + MANAGER_FLAG01] = case.get("gate_flag", 1) & 0xFF
    struct.pack_into("<I", mgr, MANAGER - MGR_ADDR + MANAGER_PTR80,
                     case.get("gate_ptr", 0x00472000) & 0xFFFFFFFF)
    struct.pack_into("<I", mgr, MANAGER - MGR_ADDR + MANAGER_F60,
                     case.get("f60", F60_BITS) & 0xFFFFFFFF)
    struct.pack_into("<I", mgr, MANAGER - MGR_ADDR + MANAGER_F64,
                     case.get("f64", F64_BITS) & 0xFFFFFFFF)

    # Low page: the latent tag-clear kind read and the null-model vector.
    low = pages["low"]
    struct.pack_into("<I", low, 0x10, case.get("low_kind", 0) & 0xFFFFFFFF)
    if "low_begin" in case:
        struct.pack_into("<I", low, 0x164, case["low_begin"] & 0xFFFFFFFF)
        struct.pack_into("<I", low, 0x168, case["low_end"] & 0xFFFFFFFF)

    elements = case.get("elements", [])
    resource = case.get("resource", MODEL_ADDR)

    # Model object and vtable.
    model = pages["model"]
    struct.pack_into("<I", model, 0, VTABLE_ADDR)
    struct.pack_into("<I", model, 0x21C, SENTINEL_21C)
    if resource == MODEL_ADDR:
        struct.pack_into("<I", model, 0x164, BEGIN_ADDR)
        struct.pack_into("<I", model, 0x168,
                         case.get("vector_end", BEGIN_ADDR + 4 * len(elements)))
    vtable = pages["vtable"]
    struct.pack_into("<I", vtable, 8, STUB_QUERY)

    # Element pointer array.
    begin = pages["begin"]
    for index in range(len(elements)):
        struct.pack_into("<I", begin, index * 4, ELEM_ADDR + index * ELEM_STRIDE)

    # Per-element records.
    for index, elem in enumerate(elements):
        elem_base = ELEM_ADDR + index * ELEM_STRIDE
        pages["elem"][index * ELEM_STRIDE + 8 : index * ELEM_STRIDE + 12] = \
            struct.pack("<I", DESC_ADDR + index * DESC_STRIDE)

        desc_off = index * DESC_STRIDE
        desc_field = DESC_ADDR + desc_off + 0x14
        if elem.get("table", False):
            rel = (table_address(index) - desc_field) & 0xFFFFFFFF
            struct.pack_into("<I", pages["desc"], desc_off + 0x14, rel)
            struct.pack_into("<I", pages["table"],
                             index * TABLE_STRIDE, 0xAB000000 | index)
        else:
            struct.pack_into("<I", pages["desc"], desc_off + 0x14, 0)

        found = elem.get("found")
        if found is not None:
            found_base = found_address(index)
            if found.get("rel_zero", False):
                struct.pack_into("<I", pages["found"],
                                 index * FOUND_STRIDE + 0x0C, 0)
            else:
                value_field = found_base + 0x0C
                rel = (value_address(index) - value_field) & 0xFFFFFFFF
                struct.pack_into("<I", pages["found"],
                                 index * FOUND_STRIDE + 0x0C, rel)
                struct.pack_into("<I", pages["value"],
                                 index * VALUE_STRIDE + 0x00,
                                 found.get("tag", 0x20000000) & 0xFFFFFFFF)
                struct.pack_into("<I", pages["value"],
                                 index * VALUE_STRIDE + 0x10,
                                 found.get("kind", 0) & 0xFFFFFFFF)

    # Type-info chain.  Node first words point at the next node (0 terminates).
    chain = case.get("chain", [])
    chain_page = pages["chain"]
    for position, node in enumerate(chain):
        following = chain[position + 1] if position + 1 < len(chain) else 0
        if MGR_ADDR <= node < MGR_ADDR + MGR_SIZE:
            struct.pack_into("<I", mgr, node - MGR_ADDR,
                             following & 0xFFFFFFFF)
        else:
            struct.pack_into("<I", chain_page, node - CHAIN_ADDR,
                             following & 0xFFFFFFFF)

    return {name: (address, bytes(pages[name]))
            for name, address, _size in FIXTURE_PAGES}


def case_head(case: dict) -> int:
    chain = case.get("chain", [])
    return chain[0] if chain else 0


class FB5C8Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        for _name, address, size in FIXTURE_PAGES:
            self.uc.mem_map(address, size)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        # Enable the VFP coprocessor (CP10/CP11) for the `vldr s0` weights.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}
        self.find_index = 0

    # ------------------------------------------------------------------ stubs
    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], args))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value & 0xFFFFFFFF))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_STRLEN:
            text = read_c_string(uc, r0)
            self._log(address, text)
            uc.reg_write(arm.UC_ARM_REG_R0, len(text))
        elif address == STUB_FIND:
            slot_word = struct.unpack("<I", uc.mem_read(r0, 4))[0]
            key = read_c_string(uc, r1)
            self._log(address, "<stack>", key, r2, slot_word)
            index = None
            if TABLE_ADDR <= slot_word < TABLE_ADDR + PAGE_SIZE:
                index = (slot_word - TABLE_ADDR) // TABLE_STRIDE
            if index is None or index >= len(self.case.get("elements", [])):
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
            else:
                found = self.case["elements"][index].get("found")
                if found is None:
                    uc.reg_write(arm.UC_ARM_REG_R0, 0)
                else:
                    uc.reg_write(arm.UC_ARM_REG_R0, found_address(index))
            self.find_index += 1
        elif address == STUB_SETTER:
            bits = uc.reg_read(arm.UC_ARM_REG_S0) & 0xFFFFFFFF
            self._log(address, r0, r1, bits)
            if self.case.get("clear_gate_on_setter", False):
                uc.mem_write(MANAGER + MANAGER_FLAG01, b"\x00")
            if self.case.get("setter_shrinks_vector", False):
                resource = self.case.get("resource", MODEL_ADDR)
                begin = struct.unpack(
                    "<I", uc.mem_read(resource + 0x164, 4)
                )[0]
                uc.mem_write(resource + 0x168, struct.pack("<I", begin))
        elif address == STUB_QUERY:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, case_head(self.case))
        else:  # pragma: no cover - hook registration guarantees the set
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, rodata: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case
        self.find_index = 0

        self.uc.mem_write(FUNC_ADDR, code)
        pages = build_pages(case)
        for name, (address, data) in pages.items():
            self.uc.mem_write(address, data)
        rodata_page = bytearray(RODATA_SIZE)
        rodata_page[: len(rodata)] = rodata
        self.uc.mem_write(RODATA_ADDR, bytes(rodata_page))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        if case.get("resource", MODEL_ADDR) != MODEL_ADDR:
            # build_pages already encoded the model page; explicit resource 0
            # still needs the model page untouched except the sentinel.
            pass

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, case.get("resource", MODEL_ADDR))
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        non_stack_writes = [
            (address, size, value)
            for address, size, value in self.writes
            if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
        ]

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg)
                for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "writes": non_stack_writes,
            "fixtures": {
                name: bytes(self.uc.mem_read(address, size))
                for name, address, size in FIXTURE_PAGES
            },
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig="
            + repr(orig["call_log"])
            + "\n    cand="
            + repr(cand["call_log"])
        )
    if orig["writes"] != cand["writes"]:
        problems.append(
            "non-stack writes:\n    orig="
            + repr(orig["writes"])
            + "\n    cand="
            + repr(cand["writes"])
        )
    for name, _address, _size in FIXTURE_PAGES:
        if orig["fixtures"][name] != cand["fixtures"][name]:
            problems.append(f"fixture page {name} differs")
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "gate_flag": 1,
        "gate_ptr": 0x00472000,
        "f60": F60_BITS,
        "f64": F64_BITS,
        "chain": [MODEL_TYPE_INFO, STATUS_TYPE_INFO],
        "resource": MODEL_ADDR,
        "elements": [],
    }
    case.update(overrides)
    return case


def elem_entry(kind: int, *, table: bool = True, rel_zero: bool = False,
               tag: int = 0x20000000) -> dict:
    if not table:
        return {"table": False}
    return {
        "table": True,
        "found": {"kind": kind, "tag": tag, "rel_zero": rel_zero},
    }


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- global gates
    cases.append(base_case("gate flag 0", gate_flag=0))
    cases.append(base_case("gate flag 0x80", gate_flag=0x80))
    cases.append(base_case("list pointer 0", gate_ptr=0))
    cases.append(base_case("empty vector, both gates open"))
    cases.append(base_case("null resource, empty low vector", resource=0))

    # --- vector loop bounds
    cases.append(base_case("negative count (end < begin)", elements=[],
                          vector_end=BEGIN_ADDR - 4))
    cases.append(base_case("one element", elements=[elem_entry(1)]))
    cases.append(base_case("two elements", elements=[elem_entry(1),
                                                     elem_entry(3)]))

    # --- descriptor / table / find outcomes
    cases.append(base_case("descriptor table offset 0",
                           elements=[elem_entry(1, table=False)]))
    cases.append(base_case("find returns null",
                           elements=[{"table": True, "found": None}]))
    cases.append(base_case("found value link 0",
                           elements=[elem_entry(1, rel_zero=True)]))

    # --- kind branches (tag bit set)
    for kind in (-1, 0, 1, 2, 3, 0x7FFFFFFF, -0x80000000):
        cases.append(
            base_case(f"kind {kind}", elements=[elem_entry(kind)])
        )

    # --- tag bit clear: latent low read of address 0x10
    for low_kind in (5, -3, 0):
        cases.append(
            base_case(f"tag clear, low kind {low_kind}",
                      elements=[elem_entry(0, tag=0x00000000)],
                      low_kind=low_kind)
        )

    # --- type-match outcome combinations
    cases.append(base_case("first match only (status writes low 0x21C)",
                           chain=[MODEL_TYPE_INFO],
                           elements=[elem_entry(1)]))
    cases.append(base_case("status match only (null model, low vector)",
                           chain=[chain_address(0), STATUS_TYPE_INFO],
                           resource=0,
                           low_begin=BEGIN_ADDR,
                           low_end=BEGIN_ADDR + 4,
                           elements=[elem_entry(1)]))
    cases.append(base_case("no type match (null model, low vector)",
                           chain=[chain_address(0)],
                           resource=0,
                           low_begin=BEGIN_ADDR,
                           low_end=BEGIN_ADDR + 4,
                           elements=[elem_entry(2)]))
    cases.append(base_case("query returns 0",
                           chain=[], elements=[elem_entry(1)]))

    # --- setter gate re-read and vector re-read
    cases.append(base_case(
        "setter clears gate after first element",
        elements=[elem_entry(2), elem_entry(2)],
        clear_gate_on_setter=True,
    ))
    cases.append(base_case(
        "setter shrinks vector after first element",
        elements=[elem_entry(-1), elem_entry(-1)],
        setter_shrinks_vector=True,
    ))
    cases.append(base_case(
        "mixed weights over two elements",
        elements=[elem_entry(-1), elem_entry(2)],
    ))

    return cases


def run_case_set(orig_code, cand_code, rodata, cases) -> int:
    passed = 0
    for case in cases:
        orig = FB5C8Runner().run(orig_code, rodata, case)
        cand = FB5C8Runner().run(cand_code, rodata, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing engine_func_002fb5c8 (0x002fb5c8)...")
    orig_code = get_orig_bytes()
    cand_code, cand_rodata = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B, "
        f"rodata {len(cand_rodata)} B (relocations resolved)."
    )
    if len(cand_code) != FUNC_SIZE:
        raise SystemExit(
            f"candidate body is {len(cand_code)} B, expected {FUNC_SIZE} B"
        )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cand_rodata, cases)

    print("\nNegative controls:")
    controls = (
        ("value_tag_mask",
         "constexpr u32 kValueTagMask = 0x20000000;",
         "constexpr u32 kValueTagMask = 0x10000000;"),
        ("value_kind_offset",
         "constexpr u32 kValueKind10 = 0x10;",
         "constexpr u32 kValueKind10 = 0x14;"),
        ("status_offset",
         "constexpr u32 kStatusOffset21C = 0x21C;",
         "constexpr u32 kStatusOffset21C = 0x218;"),
        ("setter_mode",
         "constexpr s32 kSetterMode = 1;",
         "constexpr s32 kSetterMode = 2;"),
        ("low_weight_field",
         "constexpr u32 kManagerValue60 = 0x60;",
         "constexpr u32 kManagerValue60 = 0x64;"),
    )
    for name, old, new in controls:
        mutant_code, mutant_rodata = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = FB5C8Runner().run(orig_code, cand_rodata, case)
            bad = FB5C8Runner().run(mutant_code, mutant_rodata, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
