#!/usr/bin/env python3
"""Differential test for ui_func_0037c808 (0x0037c808) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the ui_func_0037c808 body and
resolves its two direct calls to the real unsigned-divide helper that is copied
from the pinned image at its original address.  The original function
(extracted/exefs/code.bin) and the candidate then run in separate Unicorn
machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log: vtable query (host, param, info pointer), both
    0x2C6C10 divide calls (numerator, denominator) and the optional selection
    callback (out pointer, param); stack pointers are normalised;
  * host/vtable page, singleton page, object page and target page byte-for-byte;
  * any emulated write outside the private stack.

Coverage: null singleton host; vtable-query failure; counts 0..8 including the
zero-word loop; object byte 0x24 zero/non-zero; signed-looking boundaries
(0x80/0xFF bytes, high-bit words, inner-1 wrap); divisor 1 and 0xFFFFFFFF;
callback absent, present-and-failing, present-and-succeeding with zero and
non-zero selected values.  Negative controls mutate the buffer constant, a
descriptor byte and the divide expression; each must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_0037c808"

FUNC_ADDR = 0x0037C808
FUNC_SIZE = 476

# One flat code page covers the function, the divide helper and both stubs.
CODE_ADDR = 0x00100000
CODE_SIZE = 0x00400000

SINGLETON_ADDR = 0x00470000
SINGLETON_SIZE = 0x00004000
HOST_ADDR = 0x00820000
VTABLE_ADDR = 0x00810000
QUERY_STUB = 0x00800000
CALLBACK_STUB = 0x00800010
OBJECT_ADDR = 0x00710000
OBJECT_SIZE = 0x00002000
LINK_ADDR = OBJECT_ADDR + 0x1800
TARGET_ADDR = 0x00720000
TARGET_SIZE = 0x00001000
STACK_ADDR = 0x09000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

DIV_ADDR = 0x002C6C10
DIV_ENTRY_SIZE = 0x30
DIV_BODY_START = 0x002C6190
DIV_BODY_END = 0x002C62A0

# Sentinel used to distinguish "written" from "untouched" target fields.
TARGET_FILL = 0xA5
OBJECT_FILL = 0x5A
SINGLETON_FILL = 0xC3

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


def read_image(address: int, size: int) -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(address - 0x00100000)
        return handle.read(size)


def get_orig_bytes() -> bytes:
    return read_image(FUNC_ADDR, FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0037c808" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"ui_func_0037c808 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (1, 28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        if "002c6c10" not in rel.symbol_name:
            raise RuntimeError(f"unexpected call target: {rel.symbol_name}")
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (DIV_ADDR - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        cond = original & 0xFF000000
        struct.pack_into(
            "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
        )
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch41_c.o"
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


# --------------------------------------------------------------------- fixtures
def build_singleton(case: dict) -> bytes:
    page = bytearray([SINGLETON_FILL] * SINGLETON_SIZE)
    host = 0 if case.get("host_null", False) else HOST_ADDR
    # 0x00473540 is SINGLETON_ADDR + 0x3540.
    pocket = 0x3540
    struct.pack_into("<I", page, pocket, 0x11111111)
    struct.pack_into("<I", page, pocket + 4, host)
    return bytes(page)


def build_host() -> bytes:
    page = bytearray(0x1000)
    struct.pack_into("<I", page, 0x000, VTABLE_ADDR)
    # Vtable slot +8 is the query callback; other slots are inert sentinels.
    struct.pack_into("<I", page, 0x008, QUERY_STUB)
    struct.pack_into("<I", page, 0x00C, 0xDDDDDDDD)
    return bytes(page)


def build_object(case: dict) -> bytes:
    page = bytearray([OBJECT_FILL] * OBJECT_SIZE)
    struct.pack_into("<I", page, 0x10, case.get("obj_word10", 0x01234567))
    struct.pack_into("<I", page, 0x14, case.get("obj_param14", 0x89ABCDEF))
    struct.pack_into("<I", page, 0x18, LINK_ADDR)
    struct.pack_into("<I", page, LINK_ADDR - OBJECT_ADDR + 0x10,
                     case.get("link_word10", 0x0BADF00D))
    page[0x24] = case.get("obj_byte24", 1) & 0xFF
    struct.pack_into("<I", page, 0x28, case.get("obj_word28", 100) & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x2C, case.get("obj_word2C", 50) & 0xFFFFFFFF)
    struct.pack_into("<H", page, 0x30, case.get("obj_half30", 0x1234) & 0xFFFF)
    callback = 0 if case.get("callback_absent", True) else CALLBACK_STUB
    struct.pack_into("<I", page, 0xC24, callback)
    struct.pack_into("<I", page, 0xC28, case.get("callback_param", 0xFEEDFACE))
    return bytes(page)


def build_target() -> bytes:
    return bytes([TARGET_FILL] * TARGET_SIZE)


def read_c_string(uc, address: int, limit: int = 32) -> bytes:
    out = bytearray()
    for index in range(limit):
        byte = uc.mem_read(address + index, 1)[0]
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


class LeafRunner:
    """One Unicorn machine with deterministic indirect-call stubs."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        # The singleton page (0x00473540) lives inside the flat code mapping;
        # it only holds fixture words and no executed code.
        self.uc.mem_map(HOST_ADDR, 0x1000)
        self.uc.mem_map(0x00800000, 0x1000)
        self.uc.mem_map(VTABLE_ADDR, 0x1000)
        self.uc.mem_map(OBJECT_ADDR, OBJECT_SIZE)
        self.uc.mem_map(TARGET_ADDR, TARGET_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        # Real divide helper at its original address; both binaries reach it.
        self.uc.mem_write(DIV_ADDR, read_image(DIV_ADDR, DIV_ENTRY_SIZE))
        self.uc.mem_write(
            DIV_BODY_START, read_image(DIV_BODY_START, DIV_BODY_END - DIV_BODY_START)
        )

        self.uc.mem_write(QUERY_STUB, struct.pack("<I", 0xE12FFF1E))  # bx lr
        self.uc.mem_write(CALLBACK_STUB, struct.pack("<I", 0xE12FFF1E))  # bx lr
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE, self._on_stub, begin=QUERY_STUB, end=QUERY_STUB
        )
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE,
            self._on_stub,
            begin=CALLBACK_STUB,
            end=CALLBACK_STUB,
        )
        # Observe the real divide helper entry without replacing it.
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE, self._on_div, begin=DIV_ADDR, end=DIV_ADDR
        )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)
        self.uc.mem_write(HOST_ADDR, build_host())
        self.uc.mem_write(VTABLE_ADDR, build_host())
        self.uc.mem_write(0x00800020, struct.pack("<I", 0x12345678))

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_div(self, uc, address: int, size: int, user_data) -> None:
        self.call_log.append(
            (
                "div",
                (
                    uc.reg_read(arm.UC_ARM_REG_R0),
                    uc.reg_read(arm.UC_ARM_REG_R1),
                ),
            )
        )

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)

        if address == QUERY_STUB:
            self.call_log.append(("query", (r0, r1, r2)))
            if self.case.get("info_ret", 1) == 0:
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
                return
            # The original never reads the fourth word; it is still written
            # through the callee-owned 16-byte block for symmetry.
            values = struct.pack(
                "<IIII",
                self.case.get("count", 0) & 0xFFFFFFFF,
                self.case.get("info_word1", 0x11112222) & 0xFFFFFFFF,
                self.case.get("divisor", 7) & 0xFFFFFFFF,
                0x33334444,
            )
            uc.mem_write(r2, values)
            uc.reg_write(arm.UC_ARM_REG_R0, 1)
        elif address == CALLBACK_STUB:
            self.call_log.append(("callback", (r0, r1)))
            if self.case.get("callback_ret", 1) == 0:
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
                return
            uc.mem_write(
                r0, struct.pack("<I", self.case.get("selected", 0xCAFEBABE) & 0xFFFFFFFF)
            )
            uc.reg_write(arm.UC_ARM_REG_R0, 1)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    @staticmethod
    def _normalise(log) -> list:
        normalised = []
        for name, args in log:
            out = []
            for arg in args:
                if isinstance(arg, int) and STACK_ADDR <= arg < STACK_ADDR + STACK_SIZE:
                    out.append("<stack>")
                else:
                    out.append(arg)
            normalised.append((name, tuple(out)))
        return normalised

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(SINGLETON_ADDR, build_singleton(case))
        self.uc.mem_write(OBJECT_ADDR, build_object(case))
        self.uc.mem_write(TARGET_ADDR, build_target())
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, OBJECT_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, TARGET_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22223333)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x44445555)
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
            if not in_stack:
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self._normalise(self.call_log),
            "fixtures": {
                "singleton": bytes(self.uc.mem_read(SINGLETON_ADDR, SINGLETON_SIZE)),
                "object": bytes(self.uc.mem_read(OBJECT_ADDR, OBJECT_SIZE)),
                "target": bytes(self.uc.mem_read(TARGET_ADDR, TARGET_SIZE)),
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
            problems.append(
                f"fixture {key} differs (first byte offset {first})"
            )
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        # Write ordering is not observable: no two fixture regions alias.
        if sorted(orig["unexpected_writes"]) != sorted(cand["unexpected_writes"]):
            problems.append(
                "unexpected writes orig="
                f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
            )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "host_null": False,
        "info_ret": 1,
        "count": 0,
        "info_word1": 0x11112222,
        "divisor": 7,
        "obj_word10": 0x01234567,
        "obj_param14": 0x89ABCDEF,
        "obj_byte24": 1,
        "obj_word28": 100,
        "obj_word2C": 50,
        "obj_half30": 0x1234,
        "callback_absent": True,
        "callback_param": 0xFEEDFACE,
        "callback_ret": 1,
        "selected": 0xCAFEBABE,
        "link_word10": 0x0BADF00D,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- early returns
    cases.append(base_case("null singleton host", host_null=True))
    cases.append(base_case("vtable query returns zero", info_ret=0))

    # --- entry loop bounds: counts 0..8 with both byte 0x24 forms
    for count in range(0, 9):
        cases.append(base_case(f"count {count} byte24=0", count=count, obj_byte24=0))
    for count in (1, 2, 3, 5, 8):
        cases.append(base_case(f"count {count} byte24=1", count=count, obj_byte24=1))
    # The byte-index loop truncates each index to 8 bits; 256/257 cross that
    # boundary and also exercise a larger word area at target+0x60.
    for count in (255, 256, 257, 300):
        cases.append(base_case(f"count {count} index wrap", count=count, obj_byte24=1))

    # --- byte 0x24 boundary values (non-zero means "derived span")
    for byte in (0x00, 0x01, 0x7F, 0x80, 0xFF):
        cases.append(base_case(f"object byte24 0x{byte:02x}", obj_byte24=byte, count=2))

    # --- exact division, remainder and inner-1 wrap
    for source, inner, divisor in (
        (100, 50, 7),
        (0, 0, 1),
        (0xFFFFFFFF, 0, 1),
        (0xFFFFFFFF, 0xFFFFFFFF, 1),
        (0x7FFFFFFF, 0x80000000, 3),
        (0x80000000, 0x7FFFFFFF, 0xFFFFFFFF),
        (100, 50, 0xFFFFFFFF),
        (1, 1, 2),
        (0xFFFFFFFE, 0x00010000, 0xFFFF),
    ):
        cases.append(
            base_case(
                f"source 0x{source:08x} inner 0x{inner:08x} div 0x{divisor:08x}",
                obj_word28=source,
                obj_word2C=inner,
                divisor=divisor,
                count=2,
            )
        )
        cases.append(
            base_case(
                f"byte24=0 source 0x{source:08x} inner 0x{inner:08x} "
                f"div 0x{divisor:08x}",
                obj_word28=source,
                obj_word2C=inner,
                divisor=divisor,
                obj_byte24=0,
                count=2,
            )
        )

    # --- callback absent / present
    cases.append(base_case("callback absent", callback_absent=True))
    cases.append(
        base_case(
            "callback present, success, non-zero selected",
            callback_absent=False,
            callback_ret=1,
            selected=0xDEADBEEF,
        )
    )
    cases.append(
        base_case(
            "callback present, success, zero selected",
            callback_absent=False,
            callback_ret=1,
            selected=0,
        )
    )
    cases.append(
        base_case(
            "callback present, returns zero",
            callback_absent=False,
            callback_ret=0,
            selected=0x11112222,
        )
    )

    # --- copied object fields, halfword and link word boundaries
    for word10, half30, link in (
        (0x00000000, 0x0000, 0x00000000),
        (0xFFFFFFFF, 0xFFFF, 0xFFFFFFFF),
        (0x80000000, 0x8000, 0x7FFFFFFF),
    ):
        cases.append(
            base_case(
                f"copied 0x{word10:08x}/0x{half30:04x}/0x{link:08x}",
                obj_word10=word10,
                obj_half30=half30,
                link_word10=link,
                callback_absent=False,
            )
        )

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = LeafRunner().run(orig_code, case)
        cand = LeafRunner().run(cand_code, case)
        # Guard against a silent early return masking the rest of the contract.
        if not case.get("host_null", False) and case.get("info_ret", 1):
            expected = 3 + (0 if case.get("callback_absent", True) else 1)
            assert len(orig["call_log"]) >= expected, (
                f"{case['name']}: expected at least {expected} calls, "
                f"got {orig['call_log']}"
            )
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
    print("Testing ui_func_0037c808 (0x0037c808)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        f"(relocations resolved to 0x{DIV_ADDR:08x})."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        (
            "buffer_constant",
            "constexpr u32 kBufferWord = 0x800;",
            "constexpr u32 kBufferWord = 0x801;",
        ),
        (
            "descriptor_byte45",
            "store_u8(target + kTargetByte45, 0x40);",
            "store_u8(target + kTargetByte45, 0x41);",
        ),
        (
            "inner_minus_one",
            "const u32 inner_quotient = ui_func_002c6c10(inner - 1, divisor);",
            "const u32 inner_quotient = ui_func_002c6c10(inner, divisor);",
        ),
        (
            "index_base",
            "constexpr u32 kTargetIndices49 = 0x49;",
            "constexpr u32 kTargetIndices49 = 0x4A;",
        ),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = LeafRunner().run(orig_code, case)
            bad = LeafRunner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
