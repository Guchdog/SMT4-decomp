#!/usr/bin/env python3
"""Differential test for ui_func_003477f8 (0x003477f8) with Unicorn ARM.

Compiles src/engine/leaf_batch45_b.cpp, extracts the ui_func_003477f8 body,
resolves its two direct calls to deterministic stubs at the original call
targets, and runs the pinned original (extracted/exefs/code.bin) against the
candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * continuation PC, final SP, and callee-saved r4-r11;
  * the ordered call log with every register argument (including the 12 matrix
    floats and the 3 scale floats forwarded to func_0023e55c, and the two
    ui_func_002c615c arguments);
  * the full self, array, config, vobj and vtable pages;
  * any emulated write outside the private stack and the two documented
    fixture buffers.

Coverage: the +0x30 divisor zero/non-zero paths, both `ui_func_002c615c` high
word outcomes (advance / skip), angle advances that stay in range, land exactly
on 360, wrap above 360, land exactly on 0, wrap below 0, including -0.0; the LUT
65536 reduction loop just below, exactly on, and above its bound in both signs;
zero and non-zero uv deltas over all four 20-byte elements; and distinct scale
deltas. Negative controls mutate the uv loop bound, the 360 wrap constant, the
divisor high-word test, and m[15].
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

ORIG_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SOURCE = ROOT / "src" / "engine" / "leaf_batch45_b.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_003477f8"

FUNC_ADDR = 0x003477F8
FUNC_SIZE = 904
LUT_ADDR = 0x00407FC0
LUT_BYTES = 0x1000

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00400000  # 0x00100000..0x00500000, covers code, LUT and stubs

SELF_ADDR = 0x20000000
ARR_ADDR = 0x20001000
OBJ14_ADDR = 0x20002000
OBJ14_VT_ADDR = 0x20002100
CFG_ADDR = 0x20003000
PAGE_SIZE = 0x100

STACK_BASE = 0x7F000000
STACK_SIZE = 0x00010000
STACK_INIT = STACK_BASE + STACK_SIZE - 0x200
LR_SENTINEL = 0x90000000

# Original direct-call targets; stubs live at the same addresses so the
# original bytes and the relocated candidate resolve identically.
STUB_FUNC_0023E55C = 0x0023E55C
STUB_UI_FUNC_002C615C = 0x002C615C
VFN_OBJ14 = 0x00410000

STUB_NAMES = {
    STUB_FUNC_0023E55C: "func_0023e55c",
    STUB_UI_FUNC_002C615C: "ui_func_002c615c",
}

CALLEE_SAVED = {
    "r4": 0x44444444,
    "r5": 0x55555555,
    "r6": 0x66666666,
    "r7": 0x77777777,
    "r8": 0x88888888,
    "r9": 0x99999999,
    "r10": 0xAAAAAAAA,
    "r11": 0xBBBBBBBB,
}


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def read_lut() -> bytes:
    data = ORIG_BIN.read_bytes()
    start = LUT_ADDR - 0x00100000
    return data[start : start + LUT_BYTES]


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def locate_function(funcs: dict, needle: str):
    for name, value in funcs.items():
        if needle in name:
            return value
    raise RuntimeError(f"{needle} not found; available: {sorted(funcs)}")


def compile_candidate():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_b.o"
    res = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"compile failed:\n{res.stderr}")
    code_raw, relocs = locate_function(
        extract_elf_functions_detailed(obj_file), "003477f8"
    )
    return code_raw, relocs


def compile_mutant(name: str, old: str, new: str):
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    res = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"mutant compile failed:\n{res.stderr}")
    code_raw, relocs = locate_function(
        extract_elf_functions_detailed(obj_file), "003477f8"
    )
    return code_raw, relocs


def patch_bl(code: bytearray, at_off: int, src_pc: int, dst_pc: int) -> None:
    delta = (dst_pc - (src_pc + 8)) >> 2
    cond = code[at_off + 3]
    struct.pack_into("<I", code, at_off, (cond << 24) | (delta & 0x00FFFFFF))


def build_fixtures(case: dict) -> dict[str, bytes]:
    self_page = bytearray(b"\xA5" * PAGE_SIZE)
    struct.pack_into("<I", self_page, 0x04, ARR_ADDR)
    struct.pack_into("<I", self_page, 0x14, OBJ14_ADDR)
    struct.pack_into("<f", self_page, 0x58, case["ang_init"])
    struct.pack_into("<f", self_page, 0x5C, case["sc_init"])
    struct.pack_into("<I", self_page, 0x60, CFG_ADDR)

    obj14_page = bytearray(b"\xA5" * PAGE_SIZE)
    struct.pack_into("<I", obj14_page, 0x00, OBJ14_VT_ADDR)
    struct.pack_into("<I", obj14_page, 0x04, case.get("numerator", 0x12345678))

    vtable_page = bytearray(b"\xA5" * PAGE_SIZE)
    struct.pack_into("<I", vtable_page, 0x08, VFN_OBJ14)

    cfg_page = bytearray(b"\xA5" * PAGE_SIZE)
    struct.pack_into("<f", cfg_page, 0x20, case.get("du", 0.0))
    struct.pack_into("<f", cfg_page, 0x24, case.get("dv", 0.0))
    struct.pack_into("<f", cfg_page, 0x28, case.get("da", 0.0))
    struct.pack_into("<f", cfg_page, 0x2C, case.get("ds", 0.0))
    struct.pack_into("<I", cfg_page, 0x30, case.get("denom", 0) & 0xFFFFFFFF)

    arr_page = bytearray(b"\xA5" * PAGE_SIZE)
    for index in range(4):
        base = index * 20
        struct.pack_into("<f", arr_page, base + 0x0C, case["uv_init"][index][0])
        struct.pack_into("<f", arr_page, base + 0x10, case["uv_init"][index][1])

    return {
        "self": bytes(self_page),
        "obj14": bytes(obj14_page),
        "vtable": bytes(vtable_page),
        "cfg": bytes(cfg_page),
        "arr": bytes(arr_page),
    }


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        cpacr = self.uc.reg_read(arm.UC_ARM_REG_C1_C0_2)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, cpacr | (0xF << 20))
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(SELF_ADDR, 0x00100000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.mem_write(VFN_OBJ14, struct.pack("<I", 0xE12FFF1E))
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE, self._on_stub, begin=VFN_OBJ14, end=VFN_OBJ14
        )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def _on_stub(self, uc, address, size, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)

        if address == VFN_OBJ14:
            self.call_log.append(("vfn_obj14", r0))
        elif address == STUB_UI_FUNC_002C615C:
            self.call_log.append(("ui_func_002c615c", r0, r1))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("div_lo", 0) & 0xFFFFFFFF)
            uc.reg_write(arm.UC_ARM_REG_R1, self.case.get("div_hi", 0) & 0xFFFFFFFF)
        elif address == STUB_FUNC_0023E55C:
            src = struct.unpack("<12I", uc.mem_read(r1, 48))
            scale = struct.unpack("<3I", uc.mem_read(r2, 12))
            self.call_log.append(("func_0023e55c", r0, r1, r2, src, scale))
            scale_f = struct.unpack("<3f", struct.pack("<3I", *scale))
            src_f = struct.unpack("<12f", struct.pack("<12I", *src))
            out = [
                f32(src_f[0] * scale_f[0]),
                f32(src_f[1] * scale_f[0]),
                f32(src_f[2] * scale_f[0]),
                f32(src_f[3] * scale_f[0]),
                f32(src_f[4] * scale_f[1]),
                f32(src_f[5] * scale_f[1]),
                f32(src_f[6] * scale_f[1]),
                f32(src_f[7] * scale_f[1]),
                f32(src_f[8] * scale_f[2]),
                f32(src_f[9] * scale_f[2]),
                f32(src_f[10] * scale_f[2]),
                f32(src_f[11] * scale_f[2]),
            ]
            uc.mem_write(r0, struct.pack("<12f", *out))
        else:  # pragma: no cover - registration guard
            raise AssertionError(f"unexpected stub 0x{address:08x}")

    def run(
        self, code: bytes, relocs: list, case: dict, *, is_orig: bool
    ) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case

        buf = bytearray(code)
        entry = FUNC_ADDR if is_orig else 0x00400000
        if not is_orig:
            by_name = {name: addr for addr, name in STUB_NAMES.items()}
            for rel in relocs:
                if rel.relocation_type not in (28, 29):
                    raise RuntimeError(
                        f"unexpected relocation type {rel.relocation_type} "
                        f"for {rel.symbol_name}"
                    )
                if rel.symbol_name not in by_name:
                    raise RuntimeError(f"unexpected call target {rel.symbol_name}")
                patch_bl(buf, rel.offset, entry + rel.offset, by_name[rel.symbol_name])

        self.uc.mem_write(entry, bytes(buf))
        self.uc.mem_write(LUT_ADDR, read_lut())

        fixtures = build_fixtures(case)
        self.uc.mem_write(SELF_ADDR, fixtures["self"])
        self.uc.mem_write(ARR_ADDR, fixtures["arr"])
        self.uc.mem_write(CFG_ADDR, fixtures["cfg"])
        self.uc.mem_write(OBJ14_ADDR, fixtures["obj14"])
        self.uc.mem_write(OBJ14_VT_ADDR, fixtures["vtable"])
        self.uc.mem_write(STACK_BASE, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        self.uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for name, value in CALLEE_SAVED.items():
            self.uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), value)

        try:
            self.uc.emu_start(entry, LR_SENTINEL, count=200_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, _size in self.writes:
            in_stack = STACK_BASE <= address < STACK_BASE + STACK_SIZE
            in_self = SELF_ADDR <= address < SELF_ADDR + PAGE_SIZE
            in_arr = ARR_ADDR <= address < ARR_ADDR + PAGE_SIZE
            if not (in_stack or in_self or in_arr):
                unexpected_writes.append((address, _size))

        return {
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(getattr(arm, f"UC_ARM_REG_{name.upper()}"))
                for name in CALLEE_SAVED
            },
            "call_log": list(self.call_log),
            "memory": {
                "self": bytes(self.uc.mem_read(SELF_ADDR, PAGE_SIZE)),
                "arr": bytes(self.uc.mem_read(ARR_ADDR, PAGE_SIZE)),
                "cfg": bytes(self.uc.mem_read(CFG_ADDR, PAGE_SIZE)),
                "obj14": bytes(self.uc.mem_read(OBJ14_ADDR, PAGE_SIZE)),
                "vtable": bytes(self.uc.mem_read(OBJ14_VT_ADDR, PAGE_SIZE)),
            },
            "unexpected_writes": unexpected_writes,
        }


def normalise_call_log(log: list) -> list:
    """Replace stack addresses with a stable token (frame layouts differ)."""
    normalised = []
    for name, *args in log:
        out = []
        for arg in args:
            if isinstance(arg, int) and STACK_BASE <= arg < STACK_BASE + STACK_SIZE:
                out.append("<stack>")
            else:
                out.append(arg)
        normalised.append((name, tuple(out)))
    return normalised


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    orig = dict(orig)
    cand = dict(cand)
    orig["call_log"] = normalise_call_log(orig["call_log"])
    cand["call_log"] = normalise_call_log(cand["call_log"])
    for key in ("pc", "sp", "callee_saved", "call_log"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    for key, value in orig["memory"].items():
        if value != cand["memory"][key]:
            problems.append(f"memory {key} differs")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "ang_init": 0.0,
        "sc_init": 1.0,
        "du": 0.0,
        "dv": 0.0,
        "da": 0.0,
        "ds": 0.0,
        "denom": 0,
        "div_lo": 0,
        "div_hi": 0,
        "numerator": 0x12345678,
        "uv_init": [(0.25, -0.5), (1.5, 2.5), (-3.5, 4.5), (7.25, -8.75)],
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- divisor zero: advance is unconditional and the helper is not called.
    cases.append(
        base_case("denom 0, small positive delta", ang_init=10.0, da=5.0,
                  du=0.5, dv=-0.25, ds=0.125)
    )
    cases.append(
        base_case("denom 0, sum exactly 360", ang_init=350.0, da=10.0)
    )
    cases.append(
        base_case("denom 0, sum exactly 0", ang_init=10.0, da=-10.0)
    )
    cases.append(
        base_case("denom 0, sum above 360", ang_init=359.5, da=1.0)
    )
    cases.append(
        base_case("denom 0, sum below 0", ang_init=5.0, da=-15.0)
    )
    cases.append(
        base_case("denom 0, sum exactly -360", ang_init=-350.0, da=-10.0)
    )
    cases.append(
        base_case("denom 0, negative init", ang_init=-100.0, da=0.0)
    )
    cases.append(
        base_case("denom 0, negative zero", ang_init=-0.0, da=-0.0)
    )
    cases.append(
        base_case("denom 0, tiny angle", ang_init=0.001, da=0.0)
    )
    cases.append(
        base_case("denom 0, near 360", ang_init=359.999, da=0.0)
    )

    # --- divisor non-zero, high word zero: advance happens (helper called).
    cases.append(
        base_case("denom 1, hi 0 -> advance", ang_init=20.0, da=3.0,
                  denom=1, div_lo=0xDEADBEEF, div_hi=0, numerator=0xCAFEBABE)
    )
    cases.append(
        base_case("denom 0xFFFFFFFF, hi 0 -> advance", ang_init=270.0, da=100.0,
                  denom=0xFFFFFFFF, div_hi=0)
    )
    cases.append(
        base_case("denom 7, hi 0 -> wrap below", ang_init=1.0, da=-2.0,
                  denom=7, div_lo=3, div_hi=0)
    )

    # --- divisor non-zero, high word non-zero: angle advance is skipped.
    cases.append(
        base_case("denom 1, hi 1 -> skip", ang_init=45.0, da=1000.0,
                  denom=1, div_lo=0, div_hi=1)
    )
    cases.append(
        base_case("denom 0xFFFFFFFF, hi 0xFFFFFFFF -> skip", ang_init=-45.0,
                  da=1000.0, denom=0xFFFFFFFF, div_hi=0xFFFFFFFF)
    )
    cases.append(
        base_case("skip keeps negative angle (LUT neg)", ang_init=-30.0,
                  da=5.0, denom=3, div_hi=2)
    )

    # --- LUT 65536 reduction loop boundaries (only reachable when skipped).
    for name, angle in (
        ("just below 65536 bound", 92159.5),
        ("exactly on 65536 bound", 92160.0),
        ("above 65536 bound", 100000.0),
        ("negative just below bound", -92159.5),
        ("negative exactly on bound", -92160.0),
        ("negative above bound", -200000.0),
        ("two reductions", -200000.5),
    ):
        cases.append(
            base_case(f"skip, {name}", ang_init=angle, da=0.0,
                      denom=1, div_hi=1)
        )

    # --- uv deltas: zero, mixed signs, and all four elements distinct.
    cases.append(
        base_case("zero uv deltas", du=0.0, dv=0.0, ang_init=33.0)
    )
    cases.append(
        base_case("negative uv deltas", du=-0.125, dv=-1024.5, ang_init=33.0,
                  ds=-0.5, sc_init=3.0)
    )
    cases.append(
        base_case("large uv deltas", du=1.0e6, dv=-1.0e6, ang_init=180.0,
                  ds=2.0, sc_init=-1.5)
    )
    cases.append(
        base_case("scale negative delta", ds=-1.0, sc_init=0.0, ang_init=90.0)
    )
    cases.append(
        base_case("scale makes zero", ds=-1.0, sc_init=0.0, ang_init=-90.0,
                  denom=5, div_hi=0)
    )

    return cases


def run_all(orig_code, cand_code, relocs, cases) -> int:
    passed = 0
    for case in cases:
        orig = Runner().run(orig_code, [], case, is_orig=True)
        cand = Runner().run(cand_code, relocs, case, is_orig=False)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> int:
    print("Testing ui_func_003477f8 (0x003477f8)...")
    orig_code = get_orig_bytes()
    cand_code, relocs = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B, "
        f"{len(relocs)} call relocations."
    )

    cases = make_cases()
    passed = run_all(orig_code, cand_code, relocs, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("uv_loop_bound", "for (s32 i = 0; i < 4; ++i) {",
         "for (s32 i = 0; i < 3; ++i) {"),
        ("wrap_constant",
         "            } else if (ang < 0.0f) {\n"
         "                ang += 360.0f;\n"
         "                *reinterpret_cast<float*>(self + 0x58) = ang;\n"
         "            }",
         "            } else if (ang < 0.0f) {\n"
         "                ang += 359.0f;\n"
         "                *reinterpret_cast<float*>(self + 0x58) = ang;\n"
         "            }"),
        ("divisor_high_test",
         "advance = (static_cast<u32>(quotient >> 32) == 0);",
         "advance = (static_cast<u32>(quotient >> 32) != 0);"),
        ("scale_multiplier", "*pscale = *pscale * (ds + 1.0f);",
         "*pscale = *pscale * (ds + 2.0f);"),
        ("matrix_15", "    m[15] = 1.0f;\n\n    // 5. Advance the scale",
         "    m[15] = 0.0f;\n\n    // 5. Advance the scale"),
    ):
        mutant_code, mutant_relocs = compile_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, [], case, is_orig=True)
            bad = Runner().run(mutant_code, mutant_relocs, case, is_orig=False)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control not detected: {name}"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
