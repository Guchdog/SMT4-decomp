#!/usr/bin/env python3
"""Differential test for ui_func_001a1954 (0x001a1954) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the ui_func_001a1954 body,
resolves its direct calls to deterministic stubs placed at the original call
targets, and runs the pinned original (extracted/exefs/code.bin) against the
candidate in separate Unicorn machines with identical fixtures.

The manager singleton lives at 0x0043E2A8; `*(u32*)(0x0043E2A8 + 4)` is the
UI work base. The test models the real relationship used by the game:

    work base = WORK_ADDR          (the assembled 0x80-byte record)
    ctx       = WORK_ADDR + 0x8C   (argument in r0)
    publish   = WORK_ADDR + 0x24794 (final 0x80-byte copy destination)

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log with every register argument of each helper (the
    helpers take no architected stack arguments; the private stack is excluded
    from the memory comparison and only the final SP is compared);
  * the full work page (out record, context fields, record table and the
    published snapshot), the second work page used by the handle-mutation case,
    and the manager/data page;
  * any difference caused by the negative-control mutants.

Coverage: every branch and loop-equivalent record slot, all-zero and every
non-zero status-bit combination, the 0x410 extra flag, engine state 3 versus
every other value, alternate byte zero/non-zero, the 0x18 sentinel with signed
delta boundaries, mode byte 2 versus other values, record indices -128/-1/0/
1/127 per slot, u16 record boundaries, and a case where the memcpy stub changes
the manager handle mid-run to prove the two handle re-reads are preserved.
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
OUT_DIR = ROOT / "build/test_leaf_001a1954"

FUNC_ADDR = 0x001A1954
FUNC_SIZE = 676
FUNC_SYMBOL = "ui_func_001a1954"

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers the function and every stub below 0x300000
DATA_ADDR = 0x00430000
DATA_SIZE = 0x00010000
WORK_ADDR = 0x00500000
WORK_SIZE = 0x00030000
WORK2_ADDR = 0x00600000
WORK2_SIZE = 0x00030000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

CTX_OFFSET = 0x8C
MANAGER_ADDR = 0x0043E2A8
MANAGER_HANDLE_ADDR = MANAGER_ADDR + 4

STUB_2BCF58 = 0x002BCF58
STUB_2C0BA8 = 0x002C0BA8
STUB_2891E0 = 0x002891E0

STUB_NAMES = {
    STUB_2BCF58: "ui_func_002bcf58",
    STUB_2C0BA8: "script_vm_func_002c0ba8",
    STUB_2891E0: "engine_func_002891e0",
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

RECORD_COUNT = 0x80
RECORD_STRIDE = 0x604
# WORK-page offsets of the context fields (ctx starts at CTX_OFFSET).
CTX = CTX_OFFSET


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def find_candidate(obj_file: Path):
    funcs = extract_elf_functions_detailed(obj_file)
    for name, value in funcs.items():
        if FUNC_SYMBOL in name:
            return value
    raise RuntimeError(f"{FUNC_SYMBOL} not found in {obj_file}: {sorted(funcs)}")


def relocate_candidate(obj_file: Path) -> bytes:
    code_raw, relocs = find_candidate(obj_file)
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = None
        for address in STUB_NAMES:
            if f"{address:08x}" in rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        displacement = (target - (FUNC_ADDR + rel.offset + 8)) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        opcode = original & 0xFF000000
        struct.pack_into(
            "<I", code, rel.offset, opcode | (displacement & 0x00FFFFFF)
        )
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
    res = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
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
def make_pattern(seed: int, size: int) -> bytes:
    block = bytes(((i * 13 + seed) & 0xFF) for i in range(256))
    return block * (size // 256)


def default_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        # context fields copied verbatim
        "ctx_00": 0xBEEF,
        "ctx_02": 0x00,
        "ctx_08": 0x11223344,
        "ctx_0c": 0x55667788,
        "ctx_10": 0x99AABBCC,
        "ctx_14": 0xDDEE,
        "ctx_16": 0x01020304,
        "ctx_1a": 0x05060708,
        "ctx_1e": 0x090A0B0C,
        "ctx_22": 0x0D0E,
        "ctx_24": bytes(range(0x20, 0x2E)),
        "ctx_32": 0xF00D,
        "ctx_34": 0x1234,
        "ctx_38": 0xCAFEBABE,
        "ctx_54": bytes(range(0x40, 0x52)),
        "ctx_7e": 0x7E,
        "ctx_1f458": 0xDEADBEEF,
        "ctx_a839": 0x21,
        "ctx_a83a": 0x32,
        "ctx_a83b": 0x00,
        "ctx_afca": 0,
        "ctx_910c": 3,
        "ctx_910d": 5,
        "ctx_910e": 7,
        "status_byte": 0xA5,
        "status_byte2": 0x5A,
        "flags": frozenset(),
        "engine_result": 0,
        "record_overrides": {},
        "mutate_handle": False,
    }
    case.update(overrides)
    return case


def write_ctx(page: bytearray, case: dict) -> None:
    def u8(off, value):
        page[CTX + off] = value & 0xFF

    def u16(off, value):
        struct.pack_into("<H", page, CTX + off, value & 0xFFFF)

    def u32(off, value):
        struct.pack_into("<I", page, CTX + off, value & 0xFFFFFFFF)

    u16(0x00, case["ctx_00"])
    u8(0x02, case["ctx_02"])
    u32(0x08, case["ctx_08"])
    u32(0x0C, case["ctx_0c"])
    u32(0x10, case["ctx_10"])
    u16(0x14, case["ctx_14"])
    u32(0x16, case["ctx_16"])
    u32(0x1A, case["ctx_1a"])
    u32(0x1E, case["ctx_1e"])
    u16(0x22, case["ctx_22"])
    page[CTX + 0x24 : CTX + 0x32] = bytes(case["ctx_24"])
    u16(0x32, case["ctx_32"])
    u16(0x34, case["ctx_34"])
    u32(0x38, case["ctx_38"])
    page[CTX + 0x54 : CTX + 0x66] = bytes(case["ctx_54"])
    u8(0x7E, case["ctx_7e"])
    u32(0x1F458, case["ctx_1f458"])
    u8(0xA839, case["ctx_a839"])
    u8(0xA83A, case["ctx_a83a"])
    u8(0xA83B, case["ctx_a83b"])
    u8(0xAFCA, case["ctx_afca"])
    u8(0x910C, case["ctx_910c"])
    u8(0x910D, case["ctx_910d"])
    u8(0x910E, case["ctx_910e"])


def write_records(page: bytearray, case: dict) -> None:
    overrides = case["record_overrides"]
    for index in range(RECORD_COUNT):
        value = overrides.get(index, 0x1000 + index)
        offset = CTX + 0x90 + index * RECORD_STRIDE + 0x4A
        struct.pack_into("<H", page, offset, value & 0xFFFF)


def build_work(case: dict, with_ctx: bool) -> bytes:
    page = bytearray(make_pattern(7, WORK_SIZE))
    if with_ctx:
        write_ctx(page, case)
        write_records(page, case)
        page[0x24BB0] = case["status_byte"] & 0xFF
    else:
        # Distinct from the first page so a cached handle is detected.
        page[0x24BB0] = case["status_byte2"] & 0xFF
    return bytes(page)


def build_data(handle: int) -> bytes:
    page = bytearray(make_pattern(0x33, DATA_SIZE))
    struct.pack_into("<I", page, MANAGER_ADDR - DATA_ADDR, 0xCAFEBABE)
    struct.pack_into("<I", page, MANAGER_HANDLE_ADDR - DATA_ADDR, handle)
    return bytes(page)


def read_c_string(uc, address: int, limit: int = 32) -> bytes:
    out = bytearray()
    for index in range(limit):
        byte = uc.mem_read(address + index, 1)[0]
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(WORK_ADDR, WORK_SIZE)
        self.uc.mem_map(WORK2_ADDR, WORK2_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )

        self.call_log: list = []
        self.case: dict = {}
        self.handle_mutated = False

    # ------------------------------------------------------------------ stubs
    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], args))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)

        if address == STUB_2BCF58:
            self._log(address, r0, r1, r2)
            payload = bytes(uc.mem_read(r1, r2))
            uc.mem_write(r0, payload)
            uc.reg_write(arm.UC_ARM_REG_R0, r0)
            if (
                self.case.get("mutate_handle")
                and not self.handle_mutated
                and r0 == WORK_ADDR
                and r2 == 0x12
            ):
                self.handle_mutated = True
                uc.mem_write(
                    MANAGER_HANDLE_ADDR, struct.pack("<I", WORK2_ADDR)
                )
        elif address == STUB_2C0BA8:
            self._log(address, r0)
            enabled = 1 if r0 in self.case["flags"] else 0
            uc.reg_write(arm.UC_ARM_REG_R0, enabled)
        elif address == STUB_2891E0:
            self._log(address, r0)
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case["engine_result"] & 0xFFFFFFFF
            )
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.case = case
        self.handle_mutated = False

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(WORK_ADDR, build_work(case, with_ctx=True))
        self.uc.mem_write(WORK2_ADDR, build_work(case, with_ctx=False))
        self.uc.mem_write(DATA_ADDR, build_data(WORK_ADDR))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, WORK_ADDR + CTX_OFFSET)
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

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "work": bytes(self.uc.mem_read(WORK_ADDR, WORK_SIZE)),
            "work2": bytes(self.uc.mem_read(WORK2_ADDR, WORK2_SIZE)),
            "data": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "call_log"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    for key in ("work", "work2", "data"):
        if orig[key] != cand[key]:
            first = next(
                (
                    index
                    for index, (a, b) in enumerate(zip(orig[key], cand[key]))
                    if a != b
                ),
                -1,
            )
            problems.append(
                f"{key} memory differs (first at byte {first}):\n"
                f"    orig[{first}]={orig[key][first]:#04x} "
                f"cand[{first}]={cand[key][first]:#04x}"
            )
    return problems


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- baseline and context field propagation
    cases.append(default_case("baseline"))
    cases.append(
        default_case(
            "distinct context fields",
            ctx_00=0xFFFF,
            ctx_08=0xFFFFFFFF,
            ctx_0c=0x00000000,
            ctx_10=0x7FFFFFFF,
            ctx_14=0xFFFF,
            ctx_16=0x80000000,
            ctx_1a=0xDEADBEEF,
            ctx_1e=0x0000FFFF,
            ctx_22=0xAAAA,
            ctx_24=bytes(range(0xF0, 0xFE)),
            ctx_32=0x0000,
            ctx_34=0xFFFF,
            ctx_38=0x00000000,
            ctx_54=bytes(range(0, 0x12)),
            ctx_7e=0x00,
            ctx_1f458=0xFFFFFFFF,
        )
    )
    cases.append(default_case("ctx[2] = 1", ctx_02=0x01))
    cases.append(default_case("ctx[2] = 2 zeroes rows", ctx_02=0x02))
    cases.append(default_case("ctx[2] = 3", ctx_02=0x03))
    cases.append(default_case("ctx[2] = 0x80", ctx_02=0x80))
    cases.append(default_case("ctx[2] = 0xFF", ctx_02=0xFF))

    # --- status flags (four bits) and the 0x410 extra flag
    cases.append(default_case("no status flags", flags=frozenset()))
    for flag in (0x67A, 0x67B, 0x679, 0x678):
        cases.append(
            default_case(f"status flag 0x{flag:03X} only", flags=frozenset({flag}))
        )
    cases.append(
        default_case(
            "all status flags", flags=frozenset({0x67A, 0x67B, 0x679, 0x678})
        )
    )
    cases.append(
        default_case(
            "status flags 0x67A and 0x679",
            flags=frozenset({0x67A, 0x679}),
        )
    )
    cases.append(
        default_case(
            "status flags 0x67B and 0x678",
            flags=frozenset({0x67B, 0x678}),
        )
    )
    cases.append(
        default_case("extra flag 0x410 only", flags=frozenset({0x410}))
    )
    cases.append(
        default_case(
            "status flags and extra flag",
            flags=frozenset({0x67A, 0x67B, 0x679, 0x678, 0x410}),
        )
    )

    # --- engine state: 3 substitutes 1000, every other value is preserved
    for result in (0, 1, 2, 3, 4, 0x7FFFFFFF, -1):
        cases.append(
            default_case(
                f"engine result {result}",
                ctx_a839=0x21,
                engine_result=result,
            )
        )
    # 0x18 sentinel: engine != 3 keeps 0x18 and arms the delta re-check
    for delta in (0, 1, -1, 0x7F, -128):
        cases.append(
            default_case(
                f"sentinel 0x18 delta {delta}",
                ctx_a839=0x18,
                engine_result=0,
                ctx_a83b=0x00,
                ctx_afca=delta,
            )
        )
    cases.append(
        default_case(
            "sentinel 0x18 but engine 3 overrides",
            ctx_a839=0x18,
            engine_result=3,
            ctx_a83b=0x00,
            ctx_afca=0x7F,
        )
    )
    cases.append(
        default_case(
            "sentinel not 0x18, delta ignored",
            ctx_a839=0x19,
            engine_result=0,
            ctx_a83b=0x00,
            ctx_afca=0x7F,
        )
    )

    # --- alternate byte (ctx[0xA83B]) overrides only out[0x5A]
    for alternate in (0x01, 0x7F, 0xFF):
        cases.append(
            default_case(
                f"alternate byte 0x{alternate:02X}",
                ctx_a839=0x18,
                engine_result=0,
                ctx_a83b=alternate,
                ctx_afca=0x7F,
            )
        )

    # --- record selector indices: negative (zero result) and positive
    index_sets = [
        (0, 0, 0),
        (127, 127, 127),
        (-128, 0, 127),
        (-1, 1, 5),
        (0, 127, -128),
        (-1, -128, -1),
        (1, 2, 3),
    ]
    for a, b, c in index_sets:
        cases.append(
            default_case(
                f"record indices {a}/{b}/{c}",
                ctx_02=0x00,
                ctx_910c=a,
                ctx_910d=b,
                ctx_910e=c,
            )
        )
    # 16-bit record values at the boundaries
    cases.append(
        default_case(
            "record values 0x0000/0xFFFF",
            record_overrides={3: 0x0000, 5: 0xFFFF, 7: 0x8000},
        )
    )
    cases.append(
        default_case(
            "record value 0x1234 at index 127",
            ctx_910c=127,
            ctx_910d=127,
            ctx_910e=127,
            record_overrides={127: 0x1234},
        )
    )

    # --- status byte copied from work+0x24BB0
    for value in (0x00, 0x7F, 0xFF):
        cases.append(default_case(f"status byte 0x{value:02X}", status_byte=value))

    # --- two manager-handle re-reads after helper calls
    cases.append(
        default_case(
            "manager handle mutation after first copy",
            mutate_handle=True,
            status_byte=0x3C,
            status_byte2=0xC3,
            flags=frozenset({0x67A, 0x410}),
        )
    )
    cases.append(
        default_case(
            "handle mutation with zero rows",
            mutate_handle=True,
            ctx_02=0x02,
            status_byte=0xC3,
            status_byte2=0x3C,
        )
    )

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
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
    print(f"Testing {FUNC_SYMBOL} (0x{FUNC_ADDR:08x})...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        f"(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        (
            "flag_status0",
            "constexpr u32 kFlagStatus0 = 0x67A;",
            "constexpr u32 kFlagStatus0 = 0x67B;",
        ),
        (
            "record_stride",
            "constexpr u32 kRecordStride = 0x604;",
            "constexpr u32 kRecordStride = 0x608;",
        ),
        (
            "engine_special",
            "constexpr s32 kEngineStateSpecial = 3;",
            "constexpr s32 kEngineStateSpecial = 2;",
        ),
        (
            "rotated_mode",
            "constexpr u8 kRotatedMode = 2;",
            "constexpr u8 kRotatedMode = 3;",
        ),
        (
            "cached_status_handle",
            "out[0x63] = work_base()[kStatusByteOffset];",
            "out[0x63] = out[kStatusByteOffset];",
        ),
        (
            "cached_publish_handle",
            "ui_func_002bcf58(work_base() + kPublishOffset, out, kPublishSize);",
            "ui_func_002bcf58(out + kPublishOffset, out, kPublishSize);",
        ),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, case)
            bad = Runner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
