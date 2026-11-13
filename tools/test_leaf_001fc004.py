#!/usr/bin/env python3
"""Differential test for script_vm_func_001fc004 (0x001FC004) using Unicorn ARM.

The candidate body is compiled from ``src/engine/leaf_batch28_a.cpp`` and run
against the pinned original in separate ARM11/VFP machines with identical
fixtures.  The only direct helper (0x00287D54, a 3D distance) is replaced by a
deterministic hook that records the six raw single-precision arguments and
returns scripted single-precision results, so every selection boundary can be
driven exactly.

Coverage:
  * header kind gate: match, low/high halfword variants and mismatch;
  * per-record gates (active byte, state word, ready byte) and their order;
  * 0/1/2/3/4/32 ready entries, including the ``best_index == -1`` path that
    addresses the tail of the table header;
  * strict ``distance < best`` at 90000.0f, the neighbouring representable
    values, negative zero, negative, +inf, -inf and NaN;
  * ties (first index wins) and selection of the last record (index 31);
  * pass-3 reset of measured-but-unselected records, including an already -1
    reset word;
  * ordered call log, final table/view/global memory, PC, SP, callee-saved
    r4-r11 and LR, plus every non-stack write byte.

Negative controls mutate the pending marker, best-start, ready offset, result
base, result-valid byte, call argument order and the ``<`` comparison; each
mutant must be detected by at least one case.
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
SOURCE = ROOT / "src/engine/leaf_batch28_a.cpp"
OUT_DIR = ROOT / "build/test_leaf_001fc004"

FUNC_ADDR = 0x001FC004
FUNC_SIZE = 416
FUNC_SYMBOL = "script_vm_func_001fc004"

DISTANCE_ADDR = 0x00287D54

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000
DATA_ADDR = 0x00440000
DATA_SIZE = 0x00010000
TABLE_ADDR = 0x00600000
TABLE_SIZE = 0x00001000
VIEW_ADDR = 0x00700000
VIEW_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

TASK_TABLE_SLOT = 0x0044CD88
VIEW_WORK_SLOT = 0x00447E88

ENTRY_HEADER = 0x58
ENTRY_STRIDE = 76
ENTRY_COUNT = 32
RESULT_BASE = 0x9E4
RESULT_STRIDE = 76

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
S_REGS = [getattr(arm, f"UC_ARM_REG_S{i}") for i in range(6)]

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def bits_f32(bits: int) -> float:
    return struct.unpack("<f", struct.pack("<I", bits & 0xFFFFFFFF))[0]


NAN_BITS = 0x7FC00000
NAN_PAYLOAD_BITS = 0x7F800001


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if FUNC_SYMBOL in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"{FUNC_SYMBOL} not found in {obj_file}: {sorted(funcs)}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (1, 28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        if "00287d54" not in rel.symbol_name:
            raise RuntimeError(f"unexpected call relocation: {rel.symbol_name}")
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (DISTANCE_ADDR - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        cond = original & 0xFF000000
        struct.pack_into(
            "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
        )
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch28_a.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"compilation failed: {result.stderr}")
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
        raise RuntimeError(f"mutant compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def pattern(size: int, seed: int = 11) -> bytes:
    return bytes(((i * 37 + seed) & 0xFF) for i in range(size))


def make_entry(
    *,
    active: int = 1,
    state: int = 1,
    ready: int = 1,
    position=(1.5, -2.5, 3.5),
    payload0: int | None = None,
    payload1: int | None = None,
    reset: int = 0x40000000,
    marker: int = 0x48000000,
    distance_bits: int = 0xDEADBEEF,
) -> dict:
    return {
        "active": active,
        "state": state,
        "ready": ready,
        "position": position,
        "payload0": payload0,
        "payload1": payload1,
        "reset": reset,
        "marker": marker,
        "distance_bits": distance_bits,
    }


def configured_entry(index: int) -> dict:
    return make_entry(
        active=1,
        state=0x11111111,
        ready=1,
        position=(index + 0.5, index + 1.5, index + 2.5),
        payload0=0x18000000 | index,
        payload1=0x1C000000 | index,
        reset=0x40000000 | index,
        marker=0x48000000 | index,
        distance_bits=0x44000000 | index,
    )


def inactive_entry(index: int) -> dict:
    return make_entry(
        active=0,
        state=0x11111111,
        ready=0,
        position=(index + 0.5, index + 1.5, index + 2.5),
        payload0=0x18000000 | index,
        payload1=0x1C000000 | index,
        reset=0x40000000 | index,
        marker=0x48000000 | index,
        distance_bits=0x44000000 | index,
    )


def build_table(case: dict) -> bytes:
    page = bytearray(pattern(TABLE_SIZE))
    struct.pack_into("<H", page, 4, case.get("kind", 0x65) & 0xFFFF)
    for offset, value in case.get("header_words", {}).items():
        struct.pack_into("<I", page, offset, value & 0xFFFFFFFF)

    overrides = case.get("entries", {})
    for index in range(ENTRY_COUNT):
        entry = overrides.get(index)
        if entry is None:
            entry = (
                configured_entry(index)
                if case.get("all_configured", False)
                else inactive_entry(index)
            )
        base = ENTRY_HEADER + index * ENTRY_STRIDE
        page[base + 0x00] = entry["active"] & 0xFF
        struct.pack_into("<I", page, base + 0x04, entry["state"] & 0xFFFFFFFF)
        struct.pack_into("<3f", page, base + 0x0C, *entry["position"])
        payload0 = entry["payload0"]
        payload1 = entry["payload1"]
        if payload0 is None:
            payload0 = 0x18000000 | index
        if payload1 is None:
            payload1 = 0x1C000000 | index
        struct.pack_into("<I", page, base + 0x18, payload0 & 0xFFFFFFFF)
        struct.pack_into("<I", page, base + 0x1C, payload1 & 0xFFFFFFFF)
        page[base + 0x3C] = entry["ready"] & 0xFF
        struct.pack_into("<I", page, base + 0x40, entry["reset"] & 0xFFFFFFFF)
        struct.pack_into("<I", page, base + 0x44, entry["distance_bits"] & 0xFFFFFFFF)
        struct.pack_into("<I", page, base + 0x48, entry["marker"] & 0xFFFFFFFF)
    return bytes(page)


def build_view(case: dict) -> bytes:
    page = bytearray(pattern(VIEW_SIZE, seed=23))
    struct.pack_into("<3f", page, 0x1C, *case.get("view", (1.0, 2.0, 3.0)))
    return bytes(page)


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(TABLE_ADDR, TABLE_SIZE)
        self.uc.mem_map(VIEW_ADDR, VIEW_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        self.uc.mem_write(DISTANCE_ADDR, struct.pack("<I", 0xE12FFF1E))  # bx lr
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE,
            self._on_distance,
            begin=DISTANCE_ADDR,
            end=DISTANCE_ADDR,
        )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.script: list = []
        self.script_mode = "script"

    # ---------------------------------------------------------------- helpers
    def _on_distance(self, uc, address, size, user_data) -> None:
        raw = tuple(uc.reg_read(reg) for reg in S_REGS)
        self.call_log.append(raw)
        call_index = len(self.call_log) - 1

        if self.script_mode == "derive":
            values = [bits_f32(value) for value in raw]
            result = (
                values[3]
                + 2.0 * values[4]
                + 3.0 * values[5]
                + values[0]
                + 2.0 * values[1]
                + 3.0 * values[2]
            )
            ret_bits = f32_bits(result)
        elif call_index < len(self.script):
            ret_bits = self.script[call_index] & 0xFFFFFFFF
        else:
            ret_bits = f32_bits(float(call_index + 1))
        uc.reg_write(arm.UC_ARM_REG_S0, ret_bits)

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.script = list(case.get("distances", []))
        self.script_mode = case.get("distance_mode", "script")

        self.uc.mem_write(CODE_ADDR, b"\x00" * CODE_SIZE)
        # Re-install the helper stub because the clear above covers its page.
        self.uc.mem_write(DISTANCE_ADDR, struct.pack("<I", 0xE12FFF1E))
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(DATA_ADDR, b"\x00" * DATA_SIZE)
        self.uc.mem_write(TABLE_ADDR, build_table(case))
        self.uc.mem_write(VIEW_ADDR, build_view(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        self.uc.mem_write(
            TASK_TABLE_SLOT, struct.pack("<I", TABLE_ADDR)
        )
        self.uc.mem_write(VIEW_WORK_SLOT, struct.pack("<I", VIEW_ADDR))

        self.writes = []
        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        for reg in (arm.UC_ARM_REG_R0, arm.UC_ARM_REG_R1, arm.UC_ARM_REG_R2,
                    arm.UC_ARM_REG_R3):
            self.uc.reg_write(reg, 0xA5A5A5A5)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"crash at PC=0x{pc:08x}: {error}") from error

        write_bytes = set()
        for address, size, _value in self.writes:
            if STACK_ADDR <= address < STACK_ADDR + STACK_SIZE:
                continue
            write_bytes.update(range(address, address + size))

        return {
            "r0": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "lr": self.uc.reg_read(arm.UC_ARM_REG_LR),
            "callee_saved": {
                name: self.uc.reg_read(reg)
                for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "table": bytes(self.uc.mem_read(TABLE_ADDR, TABLE_SIZE)),
            "view": bytes(self.uc.mem_read(VIEW_ADDR, VIEW_SIZE)),
            "data": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
            "write_bytes": write_bytes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    # The reconstructed function is void.  Its residual r0 and LR (last call
    # return address) are caller-saved compiler state, so they are recorded but
    # not compared; PC, SP, callee-saved registers and memory are.
    keys = ["pc", "sp", "callee_saved", "call_log", "table", "view",
            "data", "write_bytes"]
    for key in keys:
        if orig[key] != cand[key]:
            if key in ("table", "view", "data"):
                left = orig[key]
                right = cand[key]
                diff = [i for i, (a, b) in enumerate(zip(left, right)) if a != b]
                problems.append(
                    f"{key} differs at {len(diff)} bytes, first {diff[:12]}"
                )
            elif key == "write_bytes":
                problems.append(
                    f"write_bytes differ: only_orig={sorted(orig[key] - cand[key])[:16]} "
                    f"only_cand={sorted(cand[key] - orig[key])[:16]}"
                )
            else:
                problems.append(
                    f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}"
                )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "kind": 0x65,
        "view": (1.0, 2.0, 3.0),
        "entries": {},
        "distances": [],
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- header gate -------------------------------------------------------
    cases.append(base_case("kind 0x0065 full path", entries={0: configured_entry(0)},
                           distances=[f32_bits(10.0)]))
    for kind in (0x0000, 0x0064, 0x0066, 0x0165, 0x6500, 0xFFFF):
        cases.append(base_case(f"kind 0x{kind:04x} early return", kind=kind,
                               entries={0: configured_entry(0)},
                               distances=[f32_bits(10.0)]))

    # --- per-record gates --------------------------------------------------
    cases.append(base_case("no records at all"))
    cases.append(base_case(
        "active zero", entries={0: make_entry(active=0, state=1, ready=1)}))
    cases.append(base_case(
        "state zero", entries={0: make_entry(active=1, state=0, ready=1)}))
    cases.append(base_case(
        "ready zero", entries={0: make_entry(active=1, state=1, ready=0)}))
    cases.append(base_case(
        "all gates pass with 0xff bytes",
        entries={0: make_entry(active=0xFF, state=0xFFFFFFFF, ready=0x80,
                               position=(7.0, 8.0, 9.0))},
        distances=[f32_bits(1.0)]))
    cases.append(base_case(
        "mixed gates with one ready record",
        entries={
            0: make_entry(active=0, state=1, ready=1),
            1: make_entry(active=1, state=0, ready=1),
            2: make_entry(active=1, state=1, ready=0),
            3: make_entry(active=1, state=1, ready=1),
        },
        distances=[f32_bits(42.0)]))

    # --- candidate counts / negative index path ---------------------------
    cases.append(base_case(
        "one ready record (two header-index slots)",
        entries={5: configured_entry(5)}, distances=[f32_bits(100.0)],
        header_words={0x0C: 0x0C0C0C0C, 0x18: 0x18181818,
                      0x1C: 0x1C1C1C1C, 0x40: 0x40404040,
                      0x48: 0x48484848}))
    cases.append(base_case(
        "two ready records (one header-index slot)",
        entries={9: configured_entry(9), 5: configured_entry(5)},
        distances=[f32_bits(500.0), f32_bits(100.0)]))
    cases.append(base_case(
        "exactly three ready records",
        entries={7: configured_entry(7), 2: configured_entry(2),
                 19: configured_entry(19)},
        distances=[f32_bits(30.0), f32_bits(10.0), f32_bits(20.0)]))
    cases.append(base_case(
        "four ready records, one leftover",
        entries={0: configured_entry(0), 1: configured_entry(1),
                 2: configured_entry(2), 3: configured_entry(3)},
        distances=[f32_bits(40.0), f32_bits(10.0), f32_bits(20.0),
                   f32_bits(30.0)]))
    cases.append(base_case(
        "five ready records, resets already -1 and live",
        entries={
            0: make_entry(active=1, state=1, ready=1, position=(0.0, 0.0, 0.0),
                          reset=0xFFFFFFFF),
            1: make_entry(active=1, state=1, ready=1, position=(1.0, 0.0, 0.0),
                          reset=0x12345678),
            2: configured_entry(2),
            3: configured_entry(3),
            4: configured_entry(4),
        },
        distances=[f32_bits(50.0), f32_bits(40.0), f32_bits(30.0),
                   f32_bits(20.0), f32_bits(10.0)]))
    cases.append(base_case(
        "all 32 ready, select last three",
        all_configured=True,
        distances=[f32_bits(1000.0 - i) for i in range(ENTRY_COUNT)]))
    cases.append(base_case(
        "last record selected first",
        entries={31: configured_entry(31), 30: configured_entry(30),
                 29: configured_entry(29)},
        distances=[f32_bits(0.0), f32_bits(1.0), f32_bits(2.0)]))

    # --- strict comparison and IEEE boundaries ----------------------------
    cases.append(base_case(
        "90000 boundary exactly and neighbours",
        entries={0: configured_entry(0), 1: configured_entry(1),
                 2: configured_entry(2), 3: configured_entry(3)},
        distances=[f32_bits(90000.0), f32_bits(89999.9921875),
                   f32_bits(90000.0078125), f32_bits(90001.0)]))
    cases.append(base_case(
        "distance greater than best start",
        entries={0: configured_entry(0), 1: configured_entry(1)},
        distances=[f32_bits(90001.0), f32_bits(100000.0)]))
    cases.append(base_case(
        "negative zero, negative and infinities",
        entries={i: configured_entry(i) for i in range(5)},
        distances=[f32_bits(-1000.0), f32_bits(-0.0), 0x7F800000,
                   0xFF800000, f32_bits(5.0)]))
    cases.append(base_case(
        "NaN candidates are not selected",
        entries={i: configured_entry(i) for i in range(4)},
        distances=[NAN_BITS, NAN_PAYLOAD_BITS, f32_bits(7.0), f32_bits(8.0)]))
    cases.append(base_case(
        "only NaN candidate keeps -1 index",
        entries={0: configured_entry(0)}, distances=[NAN_BITS]))
    cases.append(base_case(
        "ties keep the lowest index each round",
        entries={i: configured_entry(i) for i in range(5)},
        distances=[f32_bits(10.0), f32_bits(10.0), f32_bits(10.0),
                   f32_bits(10.0), f32_bits(5.0)]))

    # --- argument forwarding / view position ------------------------------
    cases.append(base_case(
        "argument-derived returns",
        distance_mode="derive",
        view=(-1.5, 0.25, 8.0),
        entries={0: make_entry(position=(0.5, 0.75, 1.25)),
                 17: make_entry(position=(-2.0, 3.5, 4.0)),
                 31: make_entry(position=(5.0, -6.0, 7.0))}))
    cases.append(base_case(
        "large finite view and positions",
        view=(1.0e20, -1.0e20, 3.0e10),
        entries={0: make_entry(position=(-1.0e20, 1.0e20, -3.0e10))},
        distances=[f32_bits(123.0)]))
    cases.append(base_case(
        "zero view and zero positions",
        view=(0.0, 0.0, 0.0),
        entries={0: make_entry(position=(0.0, 0.0, 0.0))},
        distances=[f32_bits(0.0)]))
    cases.append(base_case(
        "tiny subnormal distances",
        entries={0: configured_entry(0), 1: configured_entry(1),
                 2: configured_entry(2)},
        distances=[0x00000001, 0x80000001, 0x00000002]))

    return cases


def run_case_set(orig_code: bytes, cand_code: bytes, cases: list[dict]) -> int:
    passed = 0
    for case in cases:
        orig = Runner().run(orig_code, case)
        cand = Runner().run(cand_code, case)
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
    print("Testing script_vm_func_001fc004 (0x001FC004)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(call relocation resolved to 0x00287D54)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    controls = (
        ("pending_marker", "constexpr u32 kPendingMarker = 999;",
         "constexpr u32 kPendingMarker = 998;"),
        ("best_start", "constexpr f32 kBestStart     = 90000.0f;",
         "constexpr f32 kBestStart     = 0.0f;"),
        ("ready_offset", "constexpr s32 kEntryReady        = 0x3c;",
         "constexpr s32 kEntryReady        = 0x38;"),
        ("result_base", "constexpr s32 kResultBase   = 0x9e4;",
         "constexpr s32 kResultBase   = 0x9e8;"),
        ("result_valid", "constexpr s32 kResultValid       = 0x14;",
         "constexpr s32 kResultValid       = 0x15;"),
        ("argument_order", "engine_func_00287d54(view_x, view_y, view_z,",
         "engine_func_00287d54(entry_x, entry_y, entry_z,"),
        ("strict_compare", "if (distance < best) {",
         "if (distance <= best) {"),
    )
    for name, old, new in controls:
        mutant = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, case)
            bad = Runner().run(mutant, case)
            if compare(orig, bad):
                detected = True
                break
        if not detected:
            raise SystemExit(f"negative control failed: {name} was not detected")
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
