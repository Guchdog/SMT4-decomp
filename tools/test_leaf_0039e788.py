#!/usr/bin/env python3
"""Differential test for engine_func_0039e788 (0x0039e788) using Unicorn ARM.

Compiles src/engine/leaf_batch45_b.cpp, extracts the engine_func_0039e788 body,
resolves its two direct calls to deterministic stubs at the pinned addresses,
and runs the original (extracted/exefs/code.bin) against the candidate in
separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log, including the r0 argument of each helper;
  * the full self, engine-context, screen, map-state and stack pages;
  * every non-stack write address/size.

Coverage: both coordinate layouts (engine-context byte 12 vs every other
form), signed pass counts zero/positive/negative, inactive and active records,
all five neighbour pairings plus a full-word id that only matches the record
type's low byte, record modes 0/4/other and the 16-bit boundary, extent and
origin signs plus truncation, and positive/fractional packed dimensions.

Negative controls mutate the coordinate bias, the half/full extent selection,
and the paired-record result word; each mutant must be detected.
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
SOURCE = ROOT / "src/engine/leaf_batch45_b.cpp"
OUT_DIR = ROOT / "build/test_leaf_0039e788"

FUNC_ADDR = 0x0039E788
FUNC_SIZE = 844

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # function and both stubs (0x231F58, 0x2C2B1C)
SELF_ADDR = 0x00600000
SELF_SIZE = 0x00008000
CTX_ADDR = 0x00710000
CTX_SIZE = 0x00001000
SCREEN_ADDR = 0x00720000
SCREEN_SIZE = 0x00001000
MAP_ADDR = 0x0049F000
MAP_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_CONTEXT = 0x002C2B1C
STUB_SCREEN = 0x00231F58

STUB_NAMES = {
    STUB_CONTEXT: "engine_func_002c2b1c",
    STUB_SCREEN: "func_00231f58",
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

RECORD_STRIDE = 0x4C
PASS0_BASE = 0x0E88
PASS1_BASE = 0x5A90
HALF_VALUE_OFFSET = 0x1C
FULL_VALUE_OFFSET = 0x0C
HALF_COPY_OFFSET = 0x0A
FULL_COPY_OFFSET = 0x08
COUNT0_OFFSET = 0x5A88
COUNT1_OFFSET = 0x61B0
EXTENT_X_OFFSET = 0xB80
EXTENT_Y_OFFSET = 0xB84
CLEARED_OFFSET = 0x5A8D
CTX_STATE_OFFSET = 0xD5A
SCREEN_X_OFFSET = 0x38
SCREEN_Y_OFFSET = 0x3C
PAIR_ID_OFFSET = 0x924  # 0x0049F91C + 8 relative to MAP_ADDR

PAIRED_ACTIVE = 0xB4FF83FF
UNPAIRED_ACTIVE = 0xFFFFFF99
INACTIVE_MODE_VALUE = 0xFFFFFFFF


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


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


def relocate_candidate(obj_file: Path) -> tuple[bytes, bytes]:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0039e788" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_0039e788 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29):
            target = None
            for address, name in STUB_NAMES.items():
                if name in rel.symbol_name:
                    target = address
                    break
            if target is None:
                raise RuntimeError(
                    f"unresolved call relocation: {rel.symbol_name}"
                )
            displacement = (target - (FUNC_ADDR + rel.offset + 8)) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
            )
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )

    rodata = elf_sections(obj_file).get(".rodata.str1.1", b"")
    return bytes(code), rodata


def compile_candidate_baseline() -> tuple[bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_b.o"
    res = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> tuple[bytes, bytes]:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    res = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


# --------------------------------------------------------------------- fixtures
RECORD_DEFAULTS = {
    "active": 1,
    "kind": 0x00,
    "mode": 0,
    "copy": 0x1234,
    "v0": 100.0,
    "v1": 50.0,
    "v2": 32.0,
    "v3": 24.0,
}


def build_self(case: dict) -> bytes:
    page = bytearray(SELF_SIZE)
    struct.pack_into("<i", page, COUNT0_OFFSET, case.get("count0", 0))
    struct.pack_into("<i", page, COUNT1_OFFSET, case.get("count1", 0))
    struct.pack_into("<i", page, EXTENT_X_OFFSET, case.get("extent_x", 320))
    struct.pack_into("<i", page, EXTENT_Y_OFFSET, case.get("extent_y", 240))
    page[CLEARED_OFFSET] = case.get("cleared_before", 0x5A) & 0xFF

    full_scale = case.get("state", 0) == 12
    value_offset = FULL_VALUE_OFFSET if full_scale else HALF_VALUE_OFFSET
    copy_offset = FULL_COPY_OFFSET if full_scale else HALF_COPY_OFFSET

    for key, base in (("pass0", PASS0_BASE), ("pass1", PASS1_BASE)):
        records = case.get(key, ())
        for index, record in enumerate(records):
            fields = dict(RECORD_DEFAULTS)
            fields.update(record)
            offset = base + index * RECORD_STRIDE
            struct.pack_into("<H", page, offset + 0x34, fields["active"] & 0xFFFF)
            struct.pack_into("<H", page, offset + 0x2C, fields["mode"] & 0xFFFF)
            page[offset + 0x04] = fields["kind"] & 0xFF
            struct.pack_into("<H", page, offset + copy_offset,
                             fields["copy"] & 0xFFFF)
            # Unrelated bytes that must not be touched.
            struct.pack_into("<H", page, offset + 0x36, 0xA5A5)
            struct.pack_into("<I", page, offset + 0x48, 0xDEADBEEF)
            struct.pack_into("<f", page, offset + value_offset, fields["v0"])
            struct.pack_into("<f", page, offset + value_offset + 4, fields["v1"])
            struct.pack_into("<f", page, offset + value_offset + 8, fields["v2"])
            struct.pack_into("<f", page, offset + value_offset + 12, fields["v3"])
    return bytes(page)


def build_ctx(case: dict) -> bytes:
    page = bytearray(CTX_SIZE)
    page[CTX_STATE_OFFSET] = case.get("state", 0) & 0xFF
    return bytes(page)


def build_screen(case: dict) -> bytes:
    page = bytearray(SCREEN_SIZE)
    struct.pack_into("<f", page, SCREEN_X_OFFSET, case.get("origin_x", 0.0))
    struct.pack_into("<f", page, SCREEN_Y_OFFSET, case.get("origin_y", 0.0))
    return bytes(page)


def build_map(case: dict) -> bytes:
    page = bytearray(MAP_SIZE)
    struct.pack_into("<I", page, PAIR_ID_OFFSET, case.get("pair_id", 0x00) & 0xFFFFFFFF)
    # Neighbouring sentinels that must stay untouched.
    struct.pack_into("<I", page, PAIR_ID_OFFSET - 4, 0xC0DEC0DE)
    struct.pack_into("<I", page, PAIR_ID_OFFSET + 4, 0xFEEDFACE)
    return bytes(page)


class E788Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        # Enable CP10/CP11 so the VFP loads/conversions execute.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(SELF_ADDR, SELF_SIZE)
        self.uc.mem_map(CTX_ADDR, CTX_SIZE)
        self.uc.mem_map(SCREEN_ADDR, SCREEN_SIZE)
        self.uc.mem_map(MAP_ADDR, MAP_SIZE)
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

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append((STUB_NAMES[address], r0))
        if address == STUB_CONTEXT:
            uc.reg_write(arm.UC_ARM_REG_R0, CTX_ADDR)
        elif address == STUB_SCREEN:
            uc.reg_write(arm.UC_ARM_REG_R0, SCREEN_ADDR)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(SELF_ADDR, build_self(case))
        self.uc.mem_write(CTX_ADDR, build_ctx(case))
        self.uc.mem_write(SCREEN_ADDR, build_screen(case))
        self.uc.mem_write(MAP_ADDR, build_map(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        non_stack_writes = sorted(
            (address, size)
            for address, size in self.writes
            if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
        )

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "self": bytes(self.uc.mem_read(SELF_ADDR, SELF_SIZE)),
            "ctx": bytes(self.uc.mem_read(CTX_ADDR, CTX_SIZE)),
            "screen": bytes(self.uc.mem_read(SCREEN_ADDR, SCREEN_SIZE)),
            "map": bytes(self.uc.mem_read(MAP_ADDR, MAP_SIZE)),
            "non_stack_writes": non_stack_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "call_log"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    for key in ("self", "ctx", "screen", "map"):
        if orig[key] != cand[key]:
            first = next(
                (i for i, (a, b) in enumerate(zip(orig[key], cand[key])) if a != b),
                None,
            )
            problems.append(f"{key} memory differs (first byte {first})")
    if orig["non_stack_writes"] != cand["non_stack_writes"]:
        problems.append(
            "writes:\n    orig="
            + repr(orig["non_stack_writes"])
            + "\n    cand="
            + repr(cand["non_stack_writes"])
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "state": 0,
        "count0": 0,
        "count1": 0,
        "extent_x": 320,
        "extent_y": 240,
        "origin_x": 0.0,
        "origin_y": 0.0,
        "pair_id": 0x00,
        "pass0": (),
        "pass1": (),
    }
    case.update(overrides)
    return case


def record(**overrides) -> dict:
    fields = dict(RECORD_DEFAULTS)
    fields.update(overrides)
    return fields


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- pass selection, signed counts, inactive slots
    cases.append(base_case("both counts zero"))
    cases.append(base_case("negative counts skip both passes", count0=-1, count1=-7))
    cases.append(
        base_case(
            "pass1 only, signed count",
            count0=0,
            count1=2,
            pass1=(record(kind=0x11, copy=0x1111, mode=0),
                   record(kind=0x22, copy=0x2222, mode=4)),
        )
    )
    cases.append(
        base_case(
            "inactive record is not touched",
            count0=3,
            pass0=(record(active=0, kind=0x8D, mode=0, copy=0xAAAA),
                   record(active=0, kind=0x8D, mode=4, copy=0xBBBB),
                   record(active=0, kind=0x5C, mode=1, copy=0xCCCC)),
        )
    )
    cases.append(
        base_case(
            "active between inactive slots",
            count0=3,
            pass0=(record(active=0, copy=0xAAAA),
                   record(active=1, kind=0x33, copy=0x1357, mode=0),
                   record(active=0, copy=0xCCCC)),
        )
    )

    # --- coordinate layout selection: 12 vs every other byte value
    for state in (0, 11, 12, 13, 0xFF):
        cases.append(
            base_case(
                f"layout state {state}",
                state=state,
                count0=2,
                pass0=(record(kind=0x44, mode=0, copy=0x0102,
                              v0=95.5, v1=41.25, v2=12.75, v3=30.5),
                       record(kind=0x55, mode=4, copy=0x0304,
                              v0=180.0, v1=120.0, v2=1.0, v3=2.0)),
            )
        )

    # --- neighbour typing: exact id plus all four asymmetric pairs
    pair_cases = (
        (0x8D, 0x8D),
        (0x8D, 0x8E),
        (0x8E, 0x8D),
        (0x5C, 0x5D),
        (0x5D, 0x5C),
        (0x8D, 0x5D),
    )
    for kind, pair_id in pair_cases:
        cases.append(
            base_case(
                f"pair kind 0x{kind:02x} id 0x{pair_id:02x}",
                count0=1,
                pass0=(record(kind=kind, mode=0, copy=0x2222),),
                pair_id=pair_id,
            )
        )

    # --- full-word id: only the low byte matches the record kind
    cases.append(
        base_case(
            "id low byte only 0x8d",
            count0=1,
            pass0=(record(kind=0x8D, mode=0),),
            pair_id=0x0000018D,
        )
    )
    cases.append(
        base_case(
            "id 0xffffffff vs kind 0x8d",
            count0=1,
            pass0=(record(kind=0x8D, mode=0),),
            pair_id=0xFFFFFFFF,
        )
    )
    cases.append(
        base_case(
            "id 0x00008d00 vs kind 0x00",
            count0=1,
            pass0=(record(kind=0x00, mode=0),),
            pair_id=0x00008D00,
        )
    )

    # --- record mode: 0 and 4 select the pair/non-pair words; anything else
    # is the 0xFFFFFFFF sentinel regardless of pairing.
    for mode in (0, 1, 3, 4, 5, 0x8000, 0xFFFF):
        cases.append(
            base_case(
                f"mode {mode} paired",
                count0=1,
                pass0=(record(kind=0x8D, mode=mode),),
                pair_id=0x8E,
            )
        )
        cases.append(
            base_case(
                f"mode {mode} unpaired",
                count1=1,
                pass1=(record(kind=0x11, mode=mode),),
                pair_id=0x8E,
            )
        )

    # --- extents and origins: signs, zero, truncation, odd values
    for extent_x, extent_y, origin_x, origin_y in (
        (320, 240, 0.0, 0.0),
        (0, 0, 0.0, 0.0),
        (1, 1, 0.0, 0.0),
        (321, 241, 0.5, 0.5),
        (-1, -3, 0.0, 0.0),
        (-320, -240, 160.0, 120.0),
        (200, 150, 13.75, 7.25),
        (640, 480, -40.5, 100.25),
        (100, 60, 320.0, 240.0),
    ):
        cases.append(
            base_case(
                f"extent {extent_x}x{extent_y} origin {origin_x},{origin_y}",
                count0=2,
                count1=2,
                extent_x=extent_x,
                extent_y=extent_y,
                origin_x=origin_x,
                origin_y=origin_y,
                pass0=(record(kind=0x01, mode=0, v0=100.0, v1=50.0,
                              v2=32.0, v3=24.0),
                       record(kind=0x02, mode=4, v0=-20.5, v1=-10.25,
                              v2=0.0, v3=7.999)),
                pass1=(record(kind=0x03, mode=0, v0=12.5, v1=99.5,
                              v2=123.9, v3=0.5),
                       record(kind=0x04, mode=5, v0=500.0, v1=400.0,
                              v2=16777216.0, v3=255.75)),
            )
        )

    # --- both layouts with a full complement of active slots
    for state in (0, 12):
        cases.append(
            base_case(
                f"four active slots state {state}",
                state=state,
                count0=4,
                count1=3,
                pair_id=0x5D,
                pass0=(
                    record(kind=0x5D, mode=0, copy=0x1001, v0=10.0, v1=20.0,
                           v2=30.0, v3=40.0),
                    record(kind=0x5C, mode=4, copy=0x2002, v0=11.0, v1=21.0,
                           v2=31.0, v3=41.0),
                    record(active=0, kind=0x5D, mode=0, copy=0x3003),
                    record(kind=0x99, mode=2, copy=0x4004, v0=12.0, v1=22.0,
                           v2=32.0, v3=42.0),
                ),
                pass1=(
                    record(kind=0x5D, mode=0, copy=0x5005, v0=13.0, v1=23.0,
                           v2=33.0, v3=43.0),
                    record(active=0, kind=0x5C, mode=4, copy=0x6006),
                    record(kind=0x77, mode=4, copy=0x7007, v0=14.0, v1=24.0,
                           v2=34.0, v3=44.0),
                ),
            )
        )

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = E788Runner().run(orig_code, case)
        cand = E788Runner().run(cand_code, case)
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
    print("Testing engine_func_0039e788 (0x0039e788)...")
    orig_code = get_orig_bytes()
    cand_code, _cand_rodata = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        f"(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("coordinate_bias", " - 160.0f;", " - 159.0f;"),
        ("extent_selection",
         "static_cast<f32>(full_scale ? extent_x : extent_x / 2)",
         "static_cast<f32>(full_scale ? extent_x / 2 : extent_x)"),
        ("paired_result", "0xB4FF83FFu", "0xB4FF83FEu"),
        ("copy_offsets",
         "const u32 copy_offset = full_scale ? 0x08u : 0x0Au;",
         "const u32 copy_offset = full_scale ? 0x0Au : 0x08u;"),
    ):
        mutant_code, _ = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = E788Runner().run(orig_code, case)
            bad = E788Runner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
