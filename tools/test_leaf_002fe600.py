#!/usr/bin/env python3
"""Differential test for ui_func_002fe600 (0x002fe600) using Unicorn ARM.

Compiles ``src/engine/leaf_batch45_a.cpp``, extracts the ``ui_func_002fe600``
body, resolves its four direct call relocations to deterministic stubs and runs
the pinned original (``extracted/exefs/code.bin``) against the candidate on
separate Unicorn ARM machines with identical fixtures.

Recovered contract (see ``docs/function-records/002fe600.md``)::

    s32 ui_func_002fe600(OutputRecord* out, s32 capacity,
                         const u8* source, const CatalogSlot* catalog,
                         s32 catalog_count);

Compared per case:
  * return r0, continuation PC, final SP, callee-saved r4-r11 and s16-s31;
  * the ordered call log with every meaningful register argument;
  * the full output, source and catalog pages (byte for byte);
  * every emulated write outside the private stack (must stay in the output
    page and match between original and candidate).

Coverage: key <= 0, catalog_count <= 0, search miss, the computed-entry null
exit (catalog base 0 plus key at address 4), group_count <= 0, repeat 0 and
negative repeats, signed capacity boundaries (0, negative, partial, exact,
oversized), catalog indices 0/3/127/128/129/200 (the signed low-byte selector),
modes 0/1/2/3/4/-1, target values 0/negative/fractional/NaN/+-inf/oversized,
division clamp boundaries (current <, == and >= target), grey-byte saturation
and wrap, wrapping `step*(repeat-1)` products, and multi-group accumulation.

Negative controls mutate the color scale, group stride, mode-1 range, clamp
comparison, selector comparison and group index; each mutant must be detected.
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
SOURCE_FILE = ROOT / "src/engine/leaf_batch45_a.cpp"
OUT_DIR = ROOT / "build/test_leaf_002fe600"

FUNC_ADDR = 0x002FE600
FUNC_SIZE = 628

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # covers the function and all stubs below 0x400000
SOURCE_ADDR = 0x00710000
SOURCE_SIZE = 0x00010000
CATALOG_ADDR = 0x00720000
CATALOG_SIZE = 0x00010000
OUT_ADDR = 0x00730000
OUT_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000
ZERO_ADDR = 0x00000000
ZERO_SIZE = 0x00001000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_3DF0D8 = 0x003DF0D8
STUB_293CA8 = 0x00293CA8
STUB_297004 = 0x00297004
STUB_2C615C = 0x002C615C

STUB_NAMES = {
    STUB_3DF0D8: "func_003df0d8",
    STUB_293CA8: "ui_func_00293ca8",
    STUB_297004: "ui_func_00297004",
    STUB_2C615C: "ui_func_002c615c",
}

MUTABLE_CALL_TARGETS = {
    "3df0d8": STUB_3DF0D8,
    "293ca8": STUB_293CA8,
    "297004": STUB_297004,
    "2c615c": STUB_2C615C,
}

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

VFP_CALLEE_SAVED = {
    f"s{index}": getattr(arm, f"UC_ARM_REG_S{index}") for index in range(16, 32)
}
VFP_CALLEE_SAVED_START = {
    f"s{index}": 0x3F800000 | index for index in range(16, 32)
}

MAX_CATALOG_SLOTS = 208  # holds index 200 at stride 0x48


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


def relocate_candidate(obj_file: Path):
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "002fe600" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"ui_func_002fe600 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    resolved = []
    for rel in relocs:
        if rel.relocation_type in (1, 28, 29):
            target = None
            for needle, address in MUTABLE_CALL_TARGETS.items():
                if needle in rel.symbol_name:
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
            resolved.append((rel.symbol_name, target))
        elif rel.relocation_type == 2:  # R_ARM_ABS32
            raise RuntimeError(
                f"unexpected data relocation {rel.symbol_name} at {rel.offset:#x}"
            )
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
    return bytes(code), resolved


def compile_candidate_baseline():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
    result = compile_tu_armv6k(SOURCE_FILE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str):
    text = SOURCE_FILE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    result = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


# --------------------------------------------------------------------- fixtures
def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def build_source(case: dict) -> bytes:
    page = bytearray(SOURCE_SIZE)
    struct.pack_into("<i", page, 0x18, case["key"])
    struct.pack_into("<i", page, 0x1C, case["group_count"])
    struct.pack_into("<i", page, 0x20, case["mode"])
    for index, group in enumerate(case.get("groups", ())):
        count, step, f08, f0c, f10 = group
        base = 0x28 + index * 0x14
        struct.pack_into("<i", page, base + 0x00, count)
        struct.pack_into("<i", page, base + 0x04, step)
        struct.pack_into("<I", page, base + 0x08, f32_bits(f08))
        struct.pack_into("<I", page, base + 0x0C, f32_bits(f0c))
        struct.pack_into("<I", page, base + 0x10, f32_bits(f10))
    # Unrelated filler so accidental source writes are visible.
    for index in range(0x200, 0x240):
        page[index] = (index * 7) & 0xFF
    return bytes(page)


def build_catalog(case: dict) -> bytes:
    page = bytearray(CATALOG_SIZE)
    for index in range(MAX_CATALOG_SLOTS):
        struct.pack_into("<i", page, index * 0x48 + 4, (index + 1) * 0x101 + 3)
    if case.get("match_index") is not None:
        struct.pack_into(
            "<i", page, case["match_index"] * 0x48 + 4, case["key"]
        )
    return bytes(page)


def build_out(case: dict) -> bytes:
    return bytes([case.get("out_fill", 0xCC)]) * OUT_SIZE


def signed_divmod(numerator: int, denominator: int) -> tuple[int, int]:
    """Truncating signed division; a zero divisor yields (0, 0) in the stub."""
    numerator = numerator - (1 << 32) if numerator & 0x80000000 else numerator
    denominator = denominator - (1 << 32) if denominator & 0x80000000 else denominator
    if denominator == 0:
        return 0, 0
    quotient = abs(numerator) // abs(denominator)
    if (numerator < 0) != (denominator < 0):
        quotient = -quotient
    remainder = numerator - quotient * denominator
    return quotient & 0xFFFFFFFF, remainder & 0xFFFFFFFF


class FE600Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(SOURCE_ADDR, SOURCE_SIZE)
        self.uc.mem_map(CATALOG_ADDR, CATALOG_SIZE)
        self.uc.mem_map(OUT_ADDR, OUT_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.uc.mem_map(ZERO_ADDR, ZERO_SIZE)

        # Enable CP10/CP11 access and the VFP unit.
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
        self.range_index = 0
        self.case: dict = {}

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], args))

    def _set_s0_bits(self, bits: int) -> None:
        self.uc.reg_write(arm.UC_ARM_REG_S0, bits & 0xFFFFFFFF)

    def _next_range_value(self) -> int:
        values = self.case.get("range_values", ())
        if self.range_index < len(values):
            value = values[self.range_index]
        else:
            value = values[-1] if values else 0
        self.range_index += 1
        return value

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_3DF0D8:
            self._log(address, r0)
            self._set_s0_bits(f32_bits(self.case["scale"]))
        elif address == STUB_293CA8:
            self._log(address, r0, r1)
            self._set_s0_bits(f32_bits(self.case["unit_target"]))
        elif address == STUB_297004:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, self._next_range_value() & 0xFFFFFFFF)
        elif address == STUB_2C615C:
            quotient, remainder = signed_divmod(r0, r1)
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, quotient)
            uc.reg_write(arm.UC_ARM_REG_R1, remainder)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(
                f"unexpected stub 0x{address:08x} args {r0:#x} {r1:#x} "
                f"{r2:#x} {r3:#x}"
            )

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.range_index = 0
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(SOURCE_ADDR, build_source(case))
        self.uc.mem_write(CATALOG_ADDR, build_catalog(case))
        self.uc.mem_write(OUT_ADDR, build_out(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.uc.mem_write(ZERO_ADDR, b"\x00" * ZERO_SIZE)
        # The null-entry case runs with catalog = 0, so the search reads the
        # first slot key directly from address 4.
        self.uc.mem_write(ZERO_ADDR + 4, struct.pack("<i", case["key"]))
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, OUT_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case["capacity"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R2, SOURCE_ADDR)
        self.uc.reg_write(
            arm.UC_ARM_REG_R3, case.get("catalog", CATALOG_ADDR) & 0xFFFFFFFF
        )
        # Fifth argument lives at [sp].
        self.uc.mem_write(
            ENTRY_SP, struct.pack("<I", case["catalog_count"] & 0xFFFFFFFF)
        )
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)
        for name, bits in VFP_CALLEE_SAVED_START.items():
            self.uc.reg_write(VFP_CALLEE_SAVED[name], bits)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_out = OUT_ADDR <= address < OUT_ADDR + OUT_SIZE
            if not (in_stack or in_out):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "vfp_callee_saved": {
                name: self.uc.reg_read(reg)
                for name, reg in VFP_CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "fixtures": {
                "source": bytes(
                    self.uc.mem_read(SOURCE_ADDR, SOURCE_SIZE)
                ),
                "catalog": bytes(
                    self.uc.mem_read(CATALOG_ADDR, CATALOG_SIZE)
                ),
                "out": bytes(self.uc.mem_read(OUT_ADDR, OUT_SIZE)),
            },
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "vfp_callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig="
            + repr(orig["call_log"])
            + "\n    cand="
            + repr(cand["call_log"])
        )
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            first = next(
                (i for i, (a, b) in enumerate(zip(value, cand["fixtures"][key])) if a != b),
                None,
            )
            problems.append(f"fixture {key} differs (first byte {first})")
    if orig["unexpected_writes"] != cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    if orig["unexpected_writes"]:
        problems.append(f"original wrote outside allowed regions: {orig['unexpected_writes']}")
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "key": 0x1234,
        "group_count": 1,
        "mode": 0,
        "groups": ((1, 0, 0.0, 0.0, 0.0),),
        "catalog_count": 8,
        "match_index": 0,
        "capacity": 32,
        "scale": 1.0,
        "unit_target": 0.0,
        "range_values": (0,),
        "out_fill": 0xCC,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- early exits -------------------------------------------------------
    cases.append(base_case("key 0 returns 0", key=0))
    cases.append(base_case("key negative returns 0", key=-1))
    cases.append(base_case("catalog_count 0 returns 0", catalog_count=0))
    cases.append(base_case("catalog_count negative returns 0", catalog_count=-3))
    cases.append(base_case("search miss returns 0", key=0x7FFF0000, match_index=None))
    cases.append(
        base_case(
            "search miss with matching later index out of range",
            key=0x1000,
            catalog_count=3,
            match_index=None,
        )
    )
    cases.append(
        base_case(
            "computed entry null returns 0",
            key=0x1234,
            catalog=0,
            catalog_count=1,
            match_index=0,
        )
    )

    # --- group_count gates ------------------------------------------------
    cases.append(base_case("group_count 0 after scale call", group_count=0))
    cases.append(base_case("group_count negative after scale call", group_count=-4))
    cases.append(
        base_case("repeat 0 produces nothing", groups=((0, 0, 0.0, 0.0, 0.0),))
    )
    cases.append(
        base_case("negative repeat produces nothing",
                   groups=((-3, 0, 0.0, 0.0, 0.0),))
    )

    # --- capacity boundaries ---------------------------------------------
    base_group = (3, 4, 1.5, 0.5, 2.0)
    for capacity in (0, -1, 1, 2, 3, 4, 0x7FFFFFFF):
        cases.append(
            base_case(
                f"capacity {capacity}",
                capacity=capacity,
                groups=(base_group,),
                match_index=1,
                unit_target=5.0,
                mode=0,
            )
        )

    # --- catalog index / signed low-byte selector -------------------------
    for index in (0, 3, 127, 128, 129, 200):
        cases.append(
            base_case(
                f"catalog index {index}",
                catalog_count=max(index + 2, 8),
                match_index=index,
                groups=((2, 2, 0.5, 0.25, 1.0),),
                capacity=4,
                unit_target=2.0,
                mode=2,
                range_values=(1,),
            )
        )

    # --- unit-selection modes --------------------------------------------
    mode_groups = ((2, 3, 0.25, 0.75, 4.0),)
    for mode in (0, 1, 2, 3, 4, -1):
        cases.append(
            base_case(
                f"mode {mode}",
                mode=mode,
                groups=mode_groups,
                capacity=4,
                match_index=2,
                unit_target=7.0,
                range_values=(2, 0x12345678),
            )
        )
    # mode 1 inclusive range endpoint and shift truncation
    for value in (0, 3, 4, 0xFFFFFFFF):
        cases.append(
            base_case(
                f"mode 1 random 0x{value & 0xFFFFFFFF:08x}",
                mode=1,
                groups=((1, 0, 0.0, 1.0, 0.0),),
                capacity=1,
                match_index=0,
                unit_target=1.0,
                range_values=(value,),
                out_fill=0x11,
            )
        )
    # mode 2 large / negative range values truncate through u16
    for value in (0x12345678, -1, 0x10000, 0x7FFFFFFF):
        cases.append(
            base_case(
                f"mode 2 random 0x{value & 0xFFFFFFFF:08x}",
                mode=2,
                groups=((1, 0, 0.0, 1.0, 0.0),),
                capacity=1,
                match_index=0,
                unit_target=6.0,
                range_values=(value,),
                out_fill=0x11,
            )
        )

    # --- target values / clamp boundary ----------------------------------
    for target in (0.0, 1.0, -1.0, 3.9, -2.7, 1e10, -1e10,
                   float("nan"), float("inf"), float("-inf")):
        cases.append(
            base_case(
                f"target {target!r}",
                mode=0,
                groups=((2, 1, 0.0, 0.5, 1.0),),
                capacity=2,
                match_index=0,
                unit_target=target,
                out_fill=0x11,
            )
        )
        cases.append(
            base_case(
                f"target {target!r} with prefilled unit value",
                mode=3,
                groups=((2, 1, 0.0, 0.5, 1.0),),
                capacity=2,
                match_index=0,
                unit_target=target,
                out_fill=0x22,
            )
        )
    # current == target exactly (division called), current < target (skipped)
    cases.append(
        base_case(
            "clamp equal current and target",
            mode=2,
            groups=((1, 0, 0.0, 0.5, 0.0),),
            capacity=1,
            match_index=0,
            unit_target=9.0,
            range_values=(9,),
            out_fill=0x11,
        )
    )
    cases.append(
        base_case(
            "clamp current below target",
            mode=2,
            groups=((1, 0, 0.0, 0.5, 0.0),),
            capacity=1,
            match_index=0,
            unit_target=10.0,
            range_values=(8,),
            out_fill=0x11,
        )
    )
    cases.append(
        base_case(
            "clamp negative remainder from prefilled s16",
            mode=3,
            groups=((1, 0, 0.0, 0.5, 0.0),),
            capacity=1,
            match_index=0,
            unit_target=-7.0,
            out_fill=0xF0,
        )
    )

    # --- grey byte conversion --------------------------------------------
    for grey in (0.0, 0.001, 0.5, 1.0, 1.5, 2.0, -0.1, float("nan")):
        cases.append(
            base_case(
                f"grey {grey!r}",
                groups=((1, 0, 0.0, grey, 0.0),),
                capacity=1,
                match_index=0,
                unit_target=0.0,
                mode=0,
            )
        )

    # --- scale values -----------------------------------------------------
    for scale in (0.0, 1.0, -1.0, 0.5, 2.25, 100.0):
        cases.append(
            base_case(
                f"scale {scale!r}",
                groups=((2, 5, 0.5, 0.75, 3.0),),
                capacity=4,
                match_index=0,
                scale=scale,
                unit_target=3.0,
                mode=0,
            )
        )

    # --- wrapping step*(repeat-1) and multi-group accumulation ------------
    for repeat, step in ((1, 0x7FFFFFFF), (2, 0x40000000), (2, 0x7FFFFFFF),
                         (3, 0x40000000), (2, -0x80000000), (5, -3)):
        cases.append(
            base_case(
                f"repeat {repeat} step 0x{step & 0xFFFFFFFF:08x}",
                groups=((repeat, step, -1.25, 0.9, 6.5),),
                capacity=8,
                match_index=0,
                unit_target=4.0,
                mode=0,
            )
        )
    cases.append(
        base_case(
            "three groups accumulate z and offsets",
            groups=(
                (1, 1, 1.25, 0.1, 2.0),
                (2, 2, -0.5, 0.25, 3.0),
                (3, 3, 0.75, 0.5, 4.0),
            ),
            capacity=16,
            match_index=5,
            unit_target=2.0,
            mode=2,
            range_values=(0, 1, 2, 3, 4, 5),
        )
    )
    cases.append(
        base_case(
            "capacity stops mid second group",
            groups=(
                (2, 1, 1.0, 0.1, 1.0),
                (4, 2, 2.0, 0.9, 2.0),
            ),
            capacity=3,
            match_index=0,
            unit_target=0.0,
            mode=0,
        )
    )

    # --- out record prefill / preserved byte +0x07 ------------------------
    cases.append(
        base_case(
            "output prefill 0xA5",
            groups=((2, 0, 0.0, 0.3, 1.0),),
            capacity=2,
            match_index=0,
            mode=0,
            out_fill=0xA5,
            unit_target=0.0,
        )
    )

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = FE600Runner().run(orig_code, case)
        cand = FE600Runner().run(cand_code, case)
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
    print("Testing ui_func_002fe600 (0x002fe600)...")
    orig_code = get_orig_bytes()
    cand_code, resolved = compile_candidate_baseline()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B")
    for symbol, target in resolved:
        print(f"  relocation {symbol} -> 0x{target:08x}")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    mutants = (
        ("color_scale", "constexpr f32 kColorScale = 255.0f;",
         "constexpr f32 kColorScale = 254.0f;"),
        ("group_stride", "constexpr u32 kSourceGroupsOffset = 0x28;",
         "constexpr u32 kSourceGroupsOffset = 0x2C;"),
        ("mode1_range", "ui_func_00297004(0, 4)",
         "ui_func_00297004(0, 5)"),
        ("clamp_equal", "if (current >= target) {",
         "if (current > target) {"),
        ("selector_zero", "if (selector >= 0) {",
         "if (selector > 0) {"),
        ("group_index", "out->field_1C = static_cast<u16>(group_index);",
         "out->field_1C = static_cast<u16>(group_index + 1);"),
    )
    for name, old, new in mutants:
        mutant_code, _ = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = FE600Runner().run(orig_code, case)
            bad = FE600Runner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
