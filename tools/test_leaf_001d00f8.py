#!/usr/bin/env python3
"""Differential test for camp_func_001d00f8 (0x001d00f8) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the camp_func_001d00f8 body,
resolves its direct calls to deterministic stubs placed at the original
addresses, and runs the pinned original (extracted/exefs/code.bin) against the
candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11 and d8-d15;
  * the ordered call log with the architected arguments of every helper
    (5 helpers, no stack arguments) including the duplicate 0x29EC14 lookup;
  * the full contents of the state block, candidate/partner/selected arrays and
    the entry/partner-record/object pages;
  * every write outside the private stack, as an unordered set (the original
    stores the append cursor before the id, the candidate after it; both write
    the same bytes to the same addresses).

Coverage: candidateCount 0, -1 and INT_MIN; every candidate id zero; a single
candidate with and without the affinity bonus, the partner bonus and a battle
object; partnerCount 0, -1 and 1..3 with zero, non-matching and matching
partners (first and later positions, natural loop end and break); selectedCount
0, -1 and 2 with affinity and entry[2] penalties; score ties broken by equal,
greater and smaller 16-bit ids (including duplicate ids); level mask boundary
(0x00, 0x0F, 0x10, 0x1F, 0xE0, 0xFF); affinity 0x00/0x7F/0x80/0xFF equality;
post-selection partner consumption (append + slot clearing) with and without a
matching partner; null 0x2AE3F0 results; null 0x2840B8 results forwarded to the
stubbed 0x26A86C; and a null 0x29EC14 result, where both implementations fault
on the same unaligned read of address 0.

Domain limits: the five helpers are stubbed, so their own bodies are not
compared.  A null 0x2840B8 result is forwarded verbatim; the pinned 0x26A86C
would dereference it, which this harness cannot observe because it stubs that
helper.  NaN scores are unreachable (all scores are level + level * 0.01f plus
small integer weights for level in 0..31).
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
OUT_DIR = ROOT / "build/test_leaf_001d00f8"

FUNC_ADDR = 0x001D00F8
FUNC_SIZE = 684

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers 0x1D00F8 and every stub below 0x2B0000

STATE_ADDR = 0x00700000
STATE_SIZE = 0x00001000
CAND_ADDR = 0x00710000
PARTNER_ADDR = 0x00720000
SELECTED_BASE = 0x00730000
SELECTED_SIZE = 0x00002000
SELECTED_PTR = SELECTED_BASE + 0x1000  # index -1 still lands in mapped memory
ENTRY_ADDR = 0x00740000
RECORD_ADDR = 0x00750000
OBJECT_ADDR = 0x00760000
ARRAY_SIZE = 0x00001000

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_STRIDE = 8
RECORD_STRIDE = 0x40
OBJECT_STRIDE = 0x40

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_2A86C = 0x0026A86C
STUB_2A904 = 0x0026A904
STUB_2840B8 = 0x002840B8
STUB_29EC14 = 0x0029EC14
STUB_2AE3F0 = 0x002AE3F0

STUB_NAMES = {
    STUB_29EC14: "camp_func_0029ec14",
    STUB_2A904: "camp_func_0026a904",
    STUB_2840B8: "camp_func_002840b8",
    STUB_2A86C: "camp_func_0026a86c",
    STUB_2AE3F0: "battle_func_002ae3f0",
}

# Architected argument registers per helper; scratch registers are ignored.
STUB_ARGS = {
    STUB_29EC14: (arm.UC_ARM_REG_R0,),
    STUB_2A904: (arm.UC_ARM_REG_R0,),
    STUB_2840B8: (arm.UC_ARM_REG_R0,),
    STUB_2A86C: (arm.UC_ARM_REG_R0, arm.UC_ARM_REG_R1),
    STUB_2AE3F0: (arm.UC_ARM_REG_R0,),
}

# Stack words each helper receives (all five take only register arguments).
STACK_ARGS = {address: 0 for address in STUB_NAMES}

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
VFP_SAVED = {
    "d8": arm.UC_ARM_REG_D8,
    "d9": arm.UC_ARM_REG_D9,
    "d10": arm.UC_ARM_REG_D10,
    "d11": arm.UC_ARM_REG_D11,
    "d12": arm.UC_ARM_REG_D12,
    "d13": arm.UC_ARM_REG_D13,
    "d14": arm.UC_ARM_REG_D14,
    "d15": arm.UC_ARM_REG_D15,
}


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    functions = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in functions.items():
        if "001d00f8" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"camp_func_001d00f8 not found in {obj_file}: {sorted(functions)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = None
        for address, name in STUB_NAMES.items():
            if f"{address:08x}" in rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        cond = original & 0xFF000000
        struct.pack_into("<I", code, rel.offset, cond | (displacement & 0x00FFFFFF))
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    result = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def filler(size: int, seed: int) -> bytes:
    return bytes(((index * 37) + seed) & 0xFF for index in range(size))


def base_case(name: str, ids, **overrides) -> dict:
    case = {
        "name": name,
        "ids": list(ids),
        "count": len(ids),
        "partners": [],
        "partner_count": None,
        "selected": [],
        "selected_count": None,
        "preferred": 0x00,
        "entries": {},
        "affinity": {},
        "objects": [],
        "matches": set(),
        "null_entry": [],
        "null_record": [],
    }
    case.update(overrides)
    if case["partner_count"] is None:
        case["partner_count"] = len(case["partners"])
    if case["selected_count"] is None:
        case["selected_count"] = len(case["selected"])
    return case


class LeafRunner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        # ARMv6K core with VFP: the original and candidate both use vpush/vadd.
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)  # CP10/CP11 on
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)    # FPEXC.EN
        for base, size in (
            (CODE_ADDR, CODE_SIZE),
            (STATE_ADDR, STATE_SIZE),
            (CAND_ADDR, ARRAY_SIZE),
            (PARTNER_ADDR, ARRAY_SIZE),
            (SELECTED_BASE, SELECTED_SIZE),
            (ENTRY_ADDR, ARRAY_SIZE),
            (RECORD_ADDR, ARRAY_SIZE),
            (OBJECT_ADDR, ARRAY_SIZE),
            (STACK_ADDR, STACK_SIZE),
            (TRAP_ADDR, 0x1000),
        ):
            self.uc.mem_map(base, size)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)
        self.uc.hook_add(
            unicorn.UC_HOOK_MEM_READ_UNMAPPED, self._on_unmapped_read
        )

        self.call_log: list = []
        self.writes: list = []
        self.unmapped_reads: list = []
        self.faulted = False
        self.entry_index: dict[int, int] = {}
        self.record_index: dict[int, int] = {}
        self.object_index: dict[int, int] = {}
        self.entry_rev: dict[int, int] = {}
        self.record_rev: dict[int, int] = {}
        self.object_rev: dict[int, int] = {}
        self.affinity: dict[int, int] = {}
        self.matches: set = set()
        self.null_entry: set = set()
        self.null_record: set = set()

    # ------------------------------------------------------------------ stubs
    def _stack_words(self, sp: int, count: int) -> tuple:
        if count == 0:
            return ()
        raw = self.uc.mem_read(sp, 4 * count)
        return struct.unpack(f"<{count}I", raw)

    def _log(self, address: int, uc, resolved=None) -> None:
        values = []
        for index, register in enumerate(STUB_ARGS[address]):
            values.append(uc.reg_read(register))
        if resolved is not None:
            values = resolved
        sp = uc.reg_read(arm.UC_ARM_REG_SP)
        self.call_log.append(
            (
                STUB_NAMES[address],
                tuple(values) + self._stack_words(sp, STACK_ARGS[address]),
            )
        )

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)

        if address == STUB_29EC14:
            self._log(address, uc)
            if r0 in self.null_entry:
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
            else:
                index = self.entry_index.get(r0, 0xFF)
                uc.reg_write(
                    arm.UC_ARM_REG_R0, ENTRY_ADDR + index * ENTRY_STRIDE
                )
        elif address == STUB_2A904:
            self._log(address, uc)
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.affinity.get(r0, (r0 ^ 0xA5) & 0xFF)
            )
        elif address == STUB_2840B8:
            self._log(address, uc)
            if r0 in self.null_record:
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
            else:
                index = self.record_index.get(r0, 0xFF)
                uc.reg_write(
                    arm.UC_ARM_REG_R0, RECORD_ADDR + index * RECORD_STRIDE
                )
        elif address == STUB_2A86C:
            record = uc.reg_read(arm.UC_ARM_REG_R0)
            obj = uc.reg_read(arm.UC_ARM_REG_R1)
            record_id = self.record_rev.get(record, record)
            object_id = self.object_rev.get(obj, obj)
            self._log(address, uc, resolved=(record_id, object_id))
            matched = (record_id, object_id) in self.matches
            uc.reg_write(arm.UC_ARM_REG_R0, 1 if matched else 0)
        elif address == STUB_2AE3F0:
            self._log(address, uc)
            if r0 in self.object_index:
                uc.reg_write(
                    arm.UC_ARM_REG_R0,
                    OBJECT_ADDR + self.object_index[r0] * OBJECT_STRIDE,
                )
            else:
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_unmapped_read(self, uc, access, address, size, value, user_data):
        self.unmapped_reads.append((address, size))
        return False  # let Unicorn raise so the run stops like the real fault

    # -------------------------------------------------------------- fixtures
    def _build_pages(self, case: dict) -> None:
        uc = self.uc
        ids = list(case["ids"])
        partners = list(case["partners"])
        selected = list(case["selected"])
        objects = list(case["objects"])

        entry_ids = sorted(set(ids) | set(selected))
        self.entry_index = {ident: n for n, ident in enumerate(entry_ids)}
        self.record_index = {ident: n for n, ident in enumerate(sorted(set(partners)))}
        self.object_index = {ident: n for n, ident in enumerate(sorted(set(objects)))}
        self.entry_rev = {
            ENTRY_ADDR + n * ENTRY_STRIDE: ident
            for ident, n in self.entry_index.items()
        }
        self.record_rev = {
            RECORD_ADDR + n * RECORD_STRIDE: ident
            for ident, n in self.record_index.items()
        }
        self.object_rev = {
            OBJECT_ADDR + n * OBJECT_STRIDE: ident
            for ident, n in self.object_index.items()
        }
        self.affinity = {k: v & 0xFF for k, v in case["affinity"].items()}
        self.matches = set(case["matches"])
        self.null_entry = set(case["null_entry"])
        self.null_record = set(case["null_record"])

        state = bytearray(filler(STATE_SIZE, 0x11))
        struct.pack_into("<I", state, 0x00, 0xDEAD0000)
        struct.pack_into("<I", state, 0x04, CAND_ADDR)
        struct.pack_into("<I", state, 0x08, case["count"] & 0xFFFFFFFF)
        struct.pack_into("<I", state, 0x0C, PARTNER_ADDR)
        struct.pack_into("<I", state, 0x10, case["partner_count"] & 0xFFFFFFFF)
        struct.pack_into("<I", state, 0x14, 0xA5A50014)
        struct.pack_into("<I", state, 0x18, 0xA5A50018)
        struct.pack_into("<I", state, 0x1C, SELECTED_PTR)
        struct.pack_into("<I", state, 0x20, case["selected_count"] & 0xFFFFFFFF)
        struct.pack_into("<I", state, 0x24, 0xA5A50024)
        struct.pack_into("<I", state, 0x28, 0xA5A50028)
        state[0x2C] = case["preferred"] & 0xFF

        candidates = bytearray(filler(ARRAY_SIZE, 0x22))
        for index, ident in enumerate(ids):
            struct.pack_into("<H", candidates, index * 2, ident & 0xFFFF)

        partner_array = bytearray(filler(ARRAY_SIZE, 0x33))
        for index, ident in enumerate(partners):
            struct.pack_into("<H", partner_array, index * 2, ident & 0xFFFF)

        selected_array = bytearray(filler(SELECTED_SIZE, 0x44))
        for index, ident in enumerate(selected):
            struct.pack_into(
                "<H", selected_array, 0x1000 + index * 2, ident & 0xFFFF
            )

        entry_page = bytearray(filler(ARRAY_SIZE, 0x55))
        for ident, index in self.entry_index.items():
            specified = case["entries"].get(ident)
            if specified is None:
                entry_type = (ident ^ 0x5A) & 0xFF
                entry_flags = (ident * 13) & 0xFF
            else:
                entry_type, entry_flags = specified
            base = index * ENTRY_STRIDE
            entry_page[base + 0] = (0xC0 | (index & 0x3F)) & 0xFF
            entry_page[base + 1] = 0x5A
            entry_page[base + 2] = entry_type & 0xFF
            entry_page[base + 3] = entry_flags & 0xFF
            struct.pack_into("<I", entry_page, base + 4, 0xE0000000 | index)

        record_page = bytearray(filler(ARRAY_SIZE, 0x66))
        for ident, index in self.record_index.items():
            base = index * RECORD_STRIDE
            record_page[base + 0] = (0xD0 | (index & 0x0F)) & 0xFF
            record_page[base + 2] = (ident ^ 0x3C) & 0xFF
            struct.pack_into("<I", record_page, base + 4, 0xD0000000 | ident)

        object_page = bytearray(filler(ARRAY_SIZE, 0x77))
        for ident, index in self.object_index.items():
            base = index * OBJECT_STRIDE
            object_page[base + 0] = (0xF0 | (index & 0x0F)) & 0xFF
            object_page[base + 0x23] = (ident ^ 0x81) & 0xFF
            object_page[base + 0x28] = (ident ^ 0x27) & 0xFF
            struct.pack_into("<I", object_page, base + 0x38, 0xF0000000 | ident)

        self.pages = {
            "state": (STATE_ADDR, bytes(state)),
            "candidates": (CAND_ADDR, bytes(candidates)),
            "partners": (PARTNER_ADDR, bytes(partner_array)),
            "selected": (SELECTED_BASE, bytes(selected_array)),
            "entries": (ENTRY_ADDR, bytes(entry_page)),
            "records": (RECORD_ADDR, bytes(record_page)),
            "objects": (OBJECT_ADDR, bytes(object_page)),
        }
        for _name, (base, data) in self.pages.items():
            uc.mem_write(base, data)

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        uc = self.uc
        self.call_log = []
        self.writes = []
        self.unmapped_reads = []
        self.faulted = False

        uc.mem_write(FUNC_ADDR, code)
        self._build_pages(case)
        uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R0, STATE_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            uc.reg_write(CALLEE_SAVED[name], value)
        for index, name in enumerate(VFP_SAVED):
            uc.reg_write(VFP_SAVED[name], 0xD0000000 + index * 0x01010101)

        try:
            uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except unicorn.UcError:
            self.faulted = True

        leaks = []
        for address, size, _value in self.writes:
            if STACK_ADDR <= address < STACK_ADDR + STACK_SIZE:
                continue
            inside = (
                STATE_ADDR <= address < STATE_ADDR + STATE_SIZE
                or CAND_ADDR <= address < CAND_ADDR + ARRAY_SIZE
                or PARTNER_ADDR <= address < PARTNER_ADDR + ARRAY_SIZE
                or SELECTED_BASE <= address < SELECTED_BASE + SELECTED_SIZE
            )
            if not inside:
                leaks.append((address, size))

        return {
            "ret": uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: uc.reg_read(register)
                for name, register in CALLEE_SAVED.items()
            },
            "vfp_saved": {
                name: uc.reg_read(register) for name, register in VFP_SAVED.items()
            },
            "call_log": list(self.call_log),
            "external_writes": sorted(
                (address, size, value)
                for address, size, value in self.writes
                if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
            ),
            "leaks": leaks,
            "unmapped_reads": list(self.unmapped_reads),
            "faulted": self.faulted,
            "pages": {
                name: bytes(uc.mem_read(base, len(data)))
                for name, (base, data) in self.pages.items()
            },
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    if orig["faulted"] or cand["faulted"]:
        if orig["faulted"] != cand["faulted"]:
            problems.append(
                f"fault mismatch: orig={orig['faulted']} cand={cand['faulted']}"
            )
        if orig["call_log"] != cand["call_log"]:
            problems.append(
                "call_log before fault:\n    orig="
                + repr(orig["call_log"])
                + "\n    cand="
                + repr(cand["call_log"])
            )
        if orig["unmapped_reads"] != cand["unmapped_reads"]:
            problems.append(
                "unmapped reads:\n    orig="
                + repr(orig["unmapped_reads"])
                + "\n    cand="
                + repr(cand["unmapped_reads"])
            )
        return problems

    for key in ("ret", "pc", "sp", "callee_saved", "vfp_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig="
            + repr(orig["call_log"])
            + "\n    cand="
            + repr(cand["call_log"])
        )
    if orig["external_writes"] != cand["external_writes"]:
        problems.append(
            "external writes:\n    orig="
            + repr(orig["external_writes"])
            + "\n    cand="
            + repr(cand["external_writes"])
        )
    for name in orig["pages"]:
        if orig["pages"][name] != cand["pages"][name]:
            problems.append(f"page {name} was modified differently")
    if orig["leaks"] or cand["leaks"]:
        problems.append(
            f"writes outside fixtures: orig={orig['leaks']} cand={cand['leaks']}"
        )
    return problems


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- empty / rejected state (signed candidateCount boundary)
    cases.append(base_case("candidateCount 0", [], count=0))
    cases.append(base_case("candidateCount -1", [], count=-1))
    cases.append(base_case("candidateCount INT_MIN", [], count=-0x80000000))

    # --- candidate ids zero (loop body skipped, no selection)
    cases.append(base_case("single zero candidate", [0]))
    cases.append(base_case("three zero candidates", [0, 0, 0]))

    # --- single candidate, no bonus: plain append and id clearing
    cases.append(
        base_case(
            "single candidate level 5",
            [0x0101],
            entries={0x0101: (0x21, 0x05)},
            preferred=0x00,
        )
    )
    cases.append(
        base_case(
            "single candidate level 0 with high flag bits",
            [0x0101],
            entries={0x0101: (0x22, 0xE0)},
        )
    )
    cases.append(
        base_case(
            "single candidate level 31 with flag bits 0xFF",
            [0x0101],
            entries={0x0101: (0x23, 0xFF)},
        )
    )
    cases.append(
        base_case(
            "single candidate affinity bonus",
            [0x0101],
            entries={0x0101: (0x24, 0x01)},
            preferred=0xA5,
            affinity={0x0101: 0xA5},
        )
    )

    # --- affinity equality boundaries (unsigned byte compare)
    for preferred, value in ((0x80, 0x80), (0x80, 0x7F), (0xFF, 0xFF),
                             (0x00, 0x00), (0x00, 0xFF)):
        cases.append(
            base_case(
                f"affinity preferred 0x{preferred:02x} vs 0x{value:02x}",
                [0x0101, 0x0202],
                entries={0x0101: (0x31, 0x0A), 0x0202: (0x32, 0x0A)},
                preferred=preferred,
                affinity={0x0101: value, 0x0202: value},
            )
        )

    # --- level mask boundary decides the winner (0x10 vs 0x0F)
    cases.append(
        base_case(
            "level mask bit 4 decides winner",
            [0x0101, 0x0102],
            entries={0x0101: (0x11, 0x10), 0x0102: (0x12, 0x0F)},
        )
    )
    cases.append(
        base_case(
            "level mask bit 4 reversed order",
            [0x0102, 0x0101],
            entries={0x0101: (0x11, 0x10), 0x0102: (0x12, 0x0F)},
        )
    )

    # --- plain score ordering
    cases.append(
        base_case(
            "higher level wins",
            [0x0101, 0x0202],
            entries={0x0101: (0x41, 0x03), 0x0202: (0x42, 0x1D)},
        )
    )
    cases.append(
        base_case(
            "higher level wins reversed order",
            [0x0202, 0x0101],
            entries={0x0101: (0x41, 0x03), 0x0202: (0x42, 0x1D)},
        )
    )

    # --- equal scores: 16-bit unsigned id tie-break
    cases.append(
        base_case(
            "equal score, later smaller id replaces",
            [0x0005, 0x0003],
            entries={0x0005: (0x51, 0x08), 0x0003: (0x52, 0x08)},
        )
    )
    cases.append(
        base_case(
            "equal score, later larger id keeps first",
            [0x0003, 0x0005],
            entries={0x0003: (0x51, 0x08), 0x0005: (0x52, 0x08)},
        )
    )
    cases.append(
        base_case(
            "equal score and equal ids, later index replaces",
            [0x0007, 0x0007],
            entries={0x0007: (0x53, 0x09)},
        )
    )
    cases.append(
        base_case(
            "equal score, 16-bit ids 0x00FF vs 0x0100",
            [0x0100, 0x00FF],
            entries={0x0100: (0x54, 0x0C), 0x00FF: (0x55, 0x0C)},
        )
    )

    # --- affinity bonus flips the winner
    cases.append(
        base_case(
            "affinity bonus flips winner",
            [0x0011, 0x0022],
            entries={0x0011: (0x61, 0x14), 0x0022: (0x62, 0x14)},
            preferred=0x33,
            affinity={0x0011: 0x33, 0x0022: 0x44},
        )
    )
    cases.append(
        base_case(
            "affinity bonus does not flip",
            [0x0011, 0x0022],
            entries={0x0011: (0x61, 0x14), 0x0022: (0x62, 0x15)},
            preferred=0x33,
            affinity={0x0011: 0x33, 0x0022: 0x44},
        )
    )

    # --- partner bonus
    cases.append(
        base_case(
            "partner bonus decides tied level",
            [0x0011, 0x0022],
            entries={0x0011: (0x71, 0x14), 0x0022: (0x72, 0x14)},
            partners=[0x0044],
            objects=[0x0022],
            matches={(0x0044, 0x0022)},
        )
    )
    cases.append(
        base_case(
            "partner bonus absent keeps id tie-break",
            [0x0011, 0x0022],
            entries={0x0011: (0x71, 0x14), 0x0022: (0x72, 0x14)},
            partners=[0x0044],
            objects=[0x0022],
            matches=set(),
        )
    )
    cases.append(
        base_case(
            "partner bonus with zero partner first",
            [0x0011, 0x0022],
            entries={0x0011: (0x71, 0x14), 0x0022: (0x72, 0x14)},
            partners=[0x0000, 0x0044, 0x0055],
            objects=[0x0022],
            matches={(0x0044, 0x0022)},
        )
    )
    cases.append(
        base_case(
            "partner bonus matches later partner",
            [0x0011, 0x0022],
            entries={0x0011: (0x71, 0x14), 0x0022: (0x72, 0x14)},
            partners=[0x0044, 0x0055],
            objects=[0x0022],
            matches={(0x0055, 0x0022)},
        )
    )
    cases.append(
        base_case(
            "partnerCount 0 with object",
            [0x0011, 0x0022],
            entries={0x0011: (0x71, 0x14), 0x0022: (0x72, 0x14)},
            objects=[0x0011, 0x0022],
        )
    )
    cases.append(
        base_case(
            "partnerCount -1 with object",
            [0x0011, 0x0022],
            entries={0x0011: (0x71, 0x14), 0x0022: (0x72, 0x14)},
            partners=[0x0044],
            partner_count=-1,
            objects=[0x0011, 0x0022],
            matches={(0x0044, 0x0011), (0x0044, 0x0022)},
        )
    )

    # --- selected-list penalties
    cases.append(
        base_case(
            "selected affinity penalty flips winner",
            [0x0011, 0x0022],
            entries={0x0011: (0x81, 0x10), 0x0022: (0x82, 0x10)},
            selected=[0x0033],
            affinity={0x0011: 0x66, 0x0033: 0x66, 0x0022: 0x77},
        )
    )
    cases.append(
        base_case(
            "selected entry[2] penalty flips winner",
            [0x0011, 0x0022],
            entries={0x0011: (0x91, 0x10), 0x0022: (0x92, 0x10),
                     0x0033: (0x91, 0x00)},
            selected=[0x0033],
        )
    )
    cases.append(
        base_case(
            "selected double penalty",
            [0x0011, 0x0022],
            entries={0x0011: (0xA1, 0x10), 0x0022: (0xA2, 0x10),
                     0x0033: (0xA1, 0x00)},
            selected=[0x0033],
            affinity={0x0011: 0x88, 0x0033: 0x88},
        )
    )
    cases.append(
        base_case(
            "selectedCount 0",
            [0x0011],
            entries={0x0011: (0xB1, 0x05)},
            selected=[],
        )
    )
    cases.append(
        base_case(
            "selectedCount -1 skips penalties",
            [0x0011],
            entries={0x0011: (0xB1, 0x05)},
            selected=[0x0033],
            selected_count=-1,
        )
    )
    cases.append(
        base_case(
            "two selected entries both penalise",
            [0x0011, 0x0022],
            entries={0x0011: (0xC1, 0x10), 0x0022: (0xC2, 0x12),
                     0x0033: (0xC1, 0x00), 0x0044: (0xC1, 0x00)},
            selected=[0x0033, 0x0044],
            affinity={0x0011: 0x99, 0x0033: 0x99, 0x0044: 0x99},
        )
    )

    # --- post-selection partner consumption
    cases.append(
        base_case(
            "consume matching partner after selection",
            [0x0011, 0x0022],
            entries={0x0011: (0xD1, 0x10), 0x0022: (0xD2, 0x05)},
            partners=[0x0000, 0x0044],
            objects=[0x0011],
            matches={(0x0044, 0x0011)},
        )
    )
    cases.append(
        base_case(
            "consume later matching partner",
            [0x0011],
            entries={0x0011: (0xD1, 0x10)},
            partners=[0x0044, 0x0055],
            objects=[0x0011],
            matches={(0x0055, 0x0011)},
        )
    )
    cases.append(
        base_case(
            "chosen object null leaves partners",
            [0x0011],
            entries={0x0011: (0xD1, 0x10)},
            partners=[0x0044],
            objects=[],
            matches={(0x0044, 0x0011)},
        )
    )
    cases.append(
        base_case(
            "chosen object non-null, no partner match",
            [0x0011],
            entries={0x0011: (0xD1, 0x10)},
            partners=[0x0044, 0x0055],
            objects=[0x0011],
            matches=set(),
        )
    )
    cases.append(
        base_case(
            "chosen object non-null, partnerCount 0",
            [0x0011],
            entries={0x0011: (0xD1, 0x10)},
            partners=[],
            objects=[0x0011],
        )
    )

    # --- null helper results reachable from the caller
    cases.append(
        base_case(
            "null 0x2840B8 record forwarded",
            [0x0011],
            entries={0x0011: (0xE1, 0x10)},
            partners=[0x0044],
            objects=[0x0011],
            null_record=[0x0044],
            matches={(0x0044, 0x0011)},
        )
    )
    cases.append(
        base_case(
            "null 0x29EC14 entry faults in both",
            [0x0077],
            null_entry=[0x0077],
        )
    )

    # --- mixed larger list
    cases.append(
        base_case(
            "mixed list of five candidates",
            [0x0101, 0x0000, 0x0202, 0x0303, 0x0404],
            entries={
                0x0101: (0xF1, 0x02),
                0x0202: (0xF2, 0x12),
                0x0303: (0xF3, 0x12),
                0x0404: (0xF4, 0x04),
            },
            partners=[0x0000, 0x0055],
            objects=[0x0303],
            matches={(0x0055, 0x0303)},
            selected=[0x0066],
            affinity={0x0303: 0x42, 0x0066: 0x42},
            preferred=0x42,
        )
    )

    return cases


def run_case_set(orig_code: bytes, cand_code: bytes, cases) -> int:
    passed = 0
    for case in cases:
        orig = LeafRunner().run(orig_code, case)
        cand = LeafRunner().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        suffix = " (both fault)" if orig["faulted"] else ""
        print(
            f"  [PASS] {case['name']}  "
            f"({len(orig['call_log'])} calls, ret {orig['ret']}){suffix}"
        )
    return passed


def main() -> None:
    print("Testing camp_func_001d00f8 (0x001d00f8)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    mutations = (
        (
            "level_mask",
            "constexpr u8 kLevelMask = 0x1F;",
            "constexpr u8 kLevelMask = 0x0F;",
        ),
        (
            "affinity_compare",
            "if (state->preferredAffinity == affinity) {",
            "if (state->preferredAffinity != affinity) {",
        ),
        (
            "tie_break",
            "} else if (state->candidateIds[i] <= state->candidateIds[bestIndex]) {",
            "} else if (state->candidateIds[i] < state->candidateIds[bestIndex]) {",
        ),
        (
            "selected_affinity_penalty",
            "if (camp_unit_affinity_0026a904(selectedId) == affinity) {\n"
            "                score -= kOne;",
            "if (camp_unit_affinity_0026a904(selectedId) == affinity) {\n"
            "                score += kOne;",
        ),
        (
            "partner_bonus_sign",
            "                if (camp_unit_record_matches_0026a86c(record, object) != 0) {\n"
            "                    score += kOne;",
            "                if (camp_unit_record_matches_0026a86c(record, object) != 0) {\n"
            "                    score -= kOne;",
        ),
        (
            "partner_slot_clear",
            "state->partnerIds[j] = 0;",
            "state->partnerIds[j] = 1;",
        ),
        (
            "candidate_slot_clear",
            "state->candidateIds[bestIndex] = 0;",
            "state->candidateIds[bestIndex] = 1;",
        ),
        (
            "duplicate_entry_lookup",
            "(void)camp_unit_entry_0029ec14(id);",
            ";",
        ),
    )
    for name, old, new in mutations:
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = LeafRunner().run(orig_code, case)
            mutant = LeafRunner().run(mutant_code, case)
            if compare(orig, mutant):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
