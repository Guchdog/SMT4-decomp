#!/usr/bin/env python3
"""Differential test for engine_func_0015d944 (0x0015d944) using Unicorn ARM.

Compiles src/engine/leaf_batch44_b.cpp, extracts the engine_func_0015d944
body, resolves its direct calls to deterministic stubs placed at the original
targets, and runs the pinned original (extracted/exefs/code.bin) against the
candidate in separate machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and the callee-saved r4-r11;
  * the ordered call log with the architecturally defined arguments of every
    helper (id/factory/owner, manager/id, entry);
  * all 256 bytes of the object fixture (success tail, failure markers and the
    untouched sentinel fields);
  * every emulated write outside the private stack and the object fixture.

Coverage: the signed count clamp to [1, 2] (negative, zero, one, two, bigger
and INT_MIN), the 15-bit unsigned id saturation (negative, 0x7FFE/0x7FFF,
0x8000, 0xFFFF and INT_MAX), the single-slot failure path, both multi-slot
success paths, retry-on-existing-object with a later success, retry exhaustion
followed by partial cleanup, cleanup ordering over a null slot, and several
+0x0C word / +0x10 float-bit patterns.  Negative controls mutate the single
factory, the saturation boundary, the +0x10 store and the failure marker; each
mutant must be detected.
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
SOURCE = ROOT / "src/engine/leaf_batch44_b.cpp"
OUT_DIR = ROOT / "build/test_leaf_0015d944"

FUNC_ADDR = 0x0015D944
FUNC_SIZE = 408

# 0x100000..0x300000 covers the function and every helper stub below.
CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000
OBJ_ADDR = 0x00710000
OBJ_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100
OBJ_SNAPSHOT = 0x100

STUB_CREATE = 0x002BD48C   # engine_func_002bd48c(id, factory, owner)
STUB_MANAGER = 0x002BB270  # engine_func_002bb270()
STUB_EXISTS = 0x0015E590   # engine_func_0015e590(manager, id)
STUB_DESTROY = 0x002BD620  # engine_func_002bd620(entry)

STUB_NAMES = {
    STUB_CREATE: "engine_func_002bd48c",
    STUB_MANAGER: "engine_func_002bb270",
    STUB_EXISTS: "engine_func_0015e590",
    STUB_DESTROY: "engine_func_002bd620",
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

MAX_STUB_CALLS = 32


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0015d944" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_0015d944 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (1, 28, 29):  # PC24 / CALL / JUMP24
            target = None
            for address, _name in STUB_NAMES.items():
                if f"{address:08x}" in rel.symbol_name:
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
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch44_b.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_source = OUT_DIR / f"mutant_{name}.cpp"
    mutant_source.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    result = compile_tu_armv6k(mutant_source, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


class Leaf0015D944Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        # The original pushes/loads/stores s16/d8; enable VFP/NEON access.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(OBJ_ADDR, OBJ_SIZE)
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
        self.create_index = 0
        self.exists_index = 0
        self.create_results: list = [0]
        self.exists_results: list = [0]
        self.manager = 0
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    def _next(self, results: list, index: int) -> int:
        return results[min(index, len(results) - 1)]

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        if len(self.call_log) > MAX_STUB_CALLS:
            raise RuntimeError("stub call budget exceeded (possible retry loop)")

        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)

        if address == STUB_CREATE:
            self.call_log.append((STUB_NAMES[address], r0, r1, r2))
            result = self._next(self.create_results, self.create_index)
            self.create_index += 1
            uc.reg_write(arm.UC_ARM_REG_R0, result)
        elif address == STUB_MANAGER:
            self.call_log.append((STUB_NAMES[address],))
            uc.reg_write(arm.UC_ARM_REG_R0, self.manager)
        elif address == STUB_EXISTS:
            self.call_log.append((STUB_NAMES[address], r0, r1))
            result = self._next(self.exists_results, self.exists_index)
            self.exists_index += 1
            uc.reg_write(arm.UC_ARM_REG_R0, result)
        elif address == STUB_DESTROY:
            self.call_log.append((STUB_NAMES[address], r0))
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.create_index = 0
        self.exists_index = 0
        self.create_results = list(case.get("create_results", [0]))
        self.exists_results = list(case.get("exists_results", [0]))
        self.manager = case.get("manager", 0)
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(OBJ_ADDR, b"\xA5" * OBJ_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.uc.mem_write(
            ENTRY_SP,
            struct.pack("<I", case.get("float_bits", 0) & 0xFFFFFFFF),
        )
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, OBJ_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case.get("count", 0) & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R2, case.get("raw_id", 0) & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R3, case.get("arg_0c", 0) & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_obj = OBJ_ADDR <= address < OBJ_ADDR + OBJ_SIZE
            if not (in_stack or in_obj):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "obj": bytes(self.uc.mem_read(OBJ_ADDR, OBJ_SNAPSHOT)),
            "unexpected_writes": unexpected_writes,
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
    if orig["obj"] != cand["obj"]:
        problems.append(
            "object memory differs:\n    orig="
            + orig["obj"].hex()
            + "\n    cand="
            + cand["obj"].hex()
        )
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "count": 1,
        "raw_id": 1,
        "arg_0c": 0x11223344,
        "float_bits": 0x3F800000,
        "create_results": [0x11110000],
        "exists_results": [0],
        "manager": 0x00720000,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- signed count clamp: 0/negative -> 1, 2 stays, bigger -> 2
    for count in (1, 0, -1, -0x80000000, 2, 3, 0x7FFFFFFF):
        cases.append(
            base_case(
                f"count {count}",
                count=count,
                create_results=[0x11110000, 0x11110010],
            )
        )

    # --- 15-bit unsigned id saturation on the single-slot path
    for raw_id in (
        0,
        1,
        0x7FFE,
        0x7FFF,
        0x8000,
        0xFFFF,
        -1,
        -0x80000000,
        0x7FFFFFFF,
    ):
        cases.append(base_case(f"raw_id 0x{raw_id & 0xFFFFFFFF:08x}", raw_id=raw_id))

    # --- single-slot creation failure: no cleanup, no tail initialisation
    cases.append(
        base_case("single create failure", create_results=[0])
    )

    # --- multi-slot success and argument/float observation
    for arg_0c in (0x00000000, 0xFFFFFFFF, 0x12345678):
        cases.append(
            base_case(
                f"multi success arg_0c 0x{arg_0c:08x}",
                count=2,
                arg_0c=arg_0c,
                create_results=[0x11110000, 0x11110010],
            )
        )
    for float_bits in (0x00000000, 0x80000000, 0x7FC00000, 0xDEADBEEF, 0x3F800000):
        cases.append(
            base_case(
                f"multi success float_bits 0x{float_bits:08x}",
                count=2,
                float_bits=float_bits,
                create_results=[0x11110000, 0x11110010],
            )
        )

    # --- retry on an existing object, then succeed on the same slot
    cases.append(
        base_case(
            "multi retry then success",
            count=2,
            create_results=[0, 0x11110000, 0x11110010],
            exists_results=[1],
        )
    )
    cases.append(
        base_case(
            "multi retry twice then success",
            count=2,
            create_results=[0, 0, 0x11110000, 0x11110010],
            exists_results=[1, 1],
        )
    )
    cases.append(
        base_case(
            "multi retry with null manager still succeeds",
            count=2,
            manager=0,
            create_results=[0, 0x11110000, 0x11110010],
            exists_results=[0xFFFFFFFF],
        )
    )

    # --- multi failure: no existing object, partial set released
    cases.append(
        base_case(
            "multi first create fails (no existing)",
            count=2,
            create_results=[0, 0x11110010],
            exists_results=[0],
        )
    )
    cases.append(
        base_case(
            "multi second create fails (no existing)",
            count=2,
            create_results=[0x11110000, 0],
            exists_results=[0],
        )
    )
    cases.append(
        base_case(
            "multi retry exhausted then partial cleanup",
            count=2,
            create_results=[0, 0, 0x11110000, 0x11110010],
            exists_results=[1, 0, 0],
        )
    )
    cases.append(
        base_case(
            "multi all creations fail",
            count=2,
            create_results=[0],
            exists_results=[0],
        )
    )

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = Leaf0015D944Runner().run(orig_code, case)
        cand = Leaf0015D944Runner().run(cand_code, case)
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
    print("Testing engine_func_0015d944 (0x0015d944)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B (resolved).")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("single_factory", "constexpr u32 kSingleSlotFactory = 0x0015e458;",
         "constexpr u32 kSingleSlotFactory = 0x0015e46c;"),
        ("id_saturation_boundary", "id = 0x7FFF;", "id = 0x7FFE;"),
        ("float_store",
         "self->value_10 = __builtin_bit_cast(f32, stack_float_bits);",
         "self->value_10 = __builtin_bit_cast(f32, 0u);"),
        ("failure_marker", "self->failed_1b = 1;", "self->failed_1b = 0;"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Leaf0015D944Runner().run(orig_code, case)
            bad = Leaf0015D944Runner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
