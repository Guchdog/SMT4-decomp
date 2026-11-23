#!/usr/bin/env python3
"""Differential test for engine_func_002adc74 (0x002adc74) using Unicorn ARM.

Compiles ``src/engine/leaf_batch41_c.cpp``, extracts the
``engine_func_002adc74`` body, resolves its direct calls to deterministic stubs
at the original target addresses, and runs the pinned original
(``extracted/exefs/code.bin``) against the candidate in separate Unicorn
machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log with every register argument, every architected stack
    argument, the contents of the 0x10-byte command and 0x14-byte request
    buffers, the staged handle and the two callback-wrapper words;
  * the raw ``svc #0x23`` event with its r0 value (interrupt hook for the
    original, explicit helper stub for the candidate);
  * the record page, callback page, object vtable page, shared-block page,
    descriptor page and the 0x0042/0x0044/0x004D data pages;
  * the ``*out`` cell and any CPU write outside the private stack, the callback
    page and the ``*out`` cell.

Coverage: both signs of the request result (0, positive, 0x7FFFFFFF,
0x80000000, 0xFFFFFFFF), both signs of the init result, the shared-context
null gate, the constructor null gate, the wrapper-allocation null gate (which
exercises the raw svc), all 0x00/0x01/0x7F/0x80/0xFE/0xFF descriptor selector
bytes, zero/high-bit handles, reply values and descriptor words, and zero /
all-ones trailing parameters.

Negative controls mutate the request magic, selector fill, handle offset,
record size, callback vtable, both virtual release slots, the reply count, the
error status, the success store and the svc call; each mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_002adc74"

FUNC_ADDR = 0x002ADC74
FUNC_SIZE = 448

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # covers 0x00145E9C..0x003E0030

PAGE_VTABLE = 0x00420000
PAGE_VTABLE_SIZE = 0x00010000
PAGE_SHARED = 0x0044E000
PAGE_SHARED_SIZE = 0x00002000
PAGE_POOL = 0x004D4000
PAGE_POOL_SIZE = 0x00001000

SHARED_BASE = 0x0044E650
RECORD = 0x00710000
OBJ_VTABLE = 0x00720000
CALLBACK = 0x00730000
OUT_ADDR = 0x00740000
DESC = 0x00750000
PAGE_SIZE = 0x00001000

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000
ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Original direct-call targets; the stubs live at the same addresses so the
# pinned original and the relocated candidate resolve identically.
STUB_146284 = 0x00146284
STUB_2C4B30 = 0x002C4B30
STUB_14636C = 0x0014636C
STUB_2B5D70 = 0x002B5D70
STUB_2B5D0C = 0x002B5D0C
STUB_145E9C = 0x00145E9C

# Raw-svc and virtual-release stubs (never reachable through direct relocs of
# the original body).
SVC_STUB = 0x003E0000
OBJ_RELEASE = 0x003E0010
CB_RELEASE = 0x003E0020
ALT_RELEASE = 0x003E0030

HELPER_STUBS = {
    STUB_146284: "engine_func_00146284",
    STUB_2C4B30: "engine_func_002c4b30",
    STUB_14636C: "func_0014636c",
    STUB_2B5D70: "func_002b5d70",
    STUB_2B5D0C: "engine_func_002b5d0c",
    STUB_145E9C: "ui_func_00145e9c",
}

STACK_ARGS = {
    STUB_146284: 0,
    STUB_2C4B30: 0,
    STUB_14636C: 0,
    STUB_2B5D70: 8,
    STUB_2B5D0C: 0,
    STUB_145E9C: 3,
}

RELEASE_NAMES = {
    OBJ_RELEASE: "record_release_vtable_0x30",
    CB_RELEASE: "callback_release_vtable_0x2c",
    ALT_RELEASE: "alt_release_vtable",
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

OUT_SENTINEL = 0xDEADBEEF
POISON = 0xA5


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "002adc74" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_002adc74 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (1, 28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        if "002addd4" in rel.symbol_name:
            target = SVC_STUB
        else:
            target = None
            for address in HELPER_STUBS:
                if f"{address:08x}" in rel.symbol_name:
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
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch41_c.o"
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


class ADC74Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(PAGE_VTABLE, PAGE_VTABLE_SIZE)
        self.uc.mem_map(PAGE_SHARED, PAGE_SHARED_SIZE)
        self.uc.mem_map(PAGE_POOL, PAGE_POOL_SIZE)
        for address in (RECORD, OBJ_VTABLE, CALLBACK, OUT_ADDR, DESC):
            self.uc.mem_map(address, PAGE_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        bx_lr = struct.pack("<I", 0xE12FFF1E)
        for address in (*HELPER_STUBS, SVC_STUB, OBJ_RELEASE, CB_RELEASE,
                        ALT_RELEASE):
            self.uc.mem_write(address, bx_lr)
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)
        self.uc.hook_add(unicorn.UC_HOOK_INTR, self._on_intr)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}

    @staticmethod
    def _norm(value: int) -> object:
        if STACK_ADDR <= value < STACK_ADDR + STACK_SIZE:
            return "<stack>"
        return value

    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        return struct.unpack(f"<{count}I", self.uc.mem_read(sp, 4 * count))

    def _read_words(self, address: int, count: int) -> tuple:
        return struct.unpack(f"<{count}I", self.uc.mem_read(address, 4 * count))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_intr(self, uc, intno, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(("svc_0x23", (r0,)))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_146284:
            self.call_log.append(("engine_func_00146284", ()))
            uc.reg_write(
                arm.UC_ARM_REG_R0,
                0 if self.case.get("shared_null") else RECORD,
            )
        elif address == STUB_2C4B30:
            self.call_log.append(("engine_func_002c4b30", (r0, r1)))
            if r1:
                uc.mem_write(r0, b"\x00" * r1)
        elif address == STUB_14636C:
            self.call_log.append(("func_0014636c", (r0,)))
            if self.case.get("ctor_null"):
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
            else:
                uc.mem_write(r0, struct.pack("<I", OBJ_VTABLE))
                uc.reg_write(arm.UC_ARM_REG_R0, r0)
            # The pinned callee ends with r12 == 0xFFFFFFFF (`mvn ip,#0` at
            # 0x001463EC is its last r12 write).  The caller consumes that
            # leftover r12 in its `bic ip,ip,#0xff` selector build, so the stub
            # reproduces the callee's scratch-register side effect.
            uc.reg_write(arm.UC_ARM_REG_R12, 0xFFFFFFFF)
        elif address == STUB_2B5D70:
            stack = self._stack_words(STACK_ARGS[STUB_2B5D70])
            handle = self._read_words(r0, 1)[0]
            command = self._read_words(stack[1], 4)
            request = self._read_words(stack[4], 5)
            self.call_log.append(
                (
                    "func_002b5d70",
                    (
                        self._norm(r0),
                        self._norm(r1),
                        r2,
                        r3,
                        stack[0],
                        self._norm(stack[1]),
                        stack[2],
                        stack[3],
                        self._norm(stack[4]),
                        stack[5],
                        stack[6],
                        stack[7],
                        handle,
                    )
                    + command
                    + request,
                )
            )
            uc.mem_write(r1, struct.pack("<I", self.case["reply"]))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["send_status"])
        elif address == STUB_2B5D0C:
            self.call_log.append(("engine_func_002b5d0c", (r0,)))
            uc.reg_write(
                arm.UC_ARM_REG_R0,
                0 if self.case.get("wrapper_null") else CALLBACK,
            )
        elif address == STUB_145E9C:
            stack = self._stack_words(STACK_ARGS[STUB_145E9C])
            wrapper = self._read_words(r1, 2)
            self.call_log.append(
                (
                    "ui_func_00145e9c",
                    (self._norm(r0), self._norm(r1), r2, r3)
                    + stack
                    + wrapper,
                )
            )
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["init_status"])
        elif address == SVC_STUB:
            self.call_log.append(("svc_0x23", (r0,)))
        elif address in RELEASE_NAMES:
            self.call_log.append((RELEASE_NAMES[address], (r0,)))
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)

        record = bytearray([POISON]) * PAGE_SIZE
        self.uc.mem_write(RECORD, bytes(record))
        callback = bytearray([POISON]) * PAGE_SIZE
        self.uc.mem_write(CALLBACK, bytes(callback))

        obj_vtable = bytearray([POISON]) * PAGE_SIZE
        struct.pack_into("<I", obj_vtable, 0x2C, ALT_RELEASE)
        struct.pack_into("<I", obj_vtable, 0x30, OBJ_RELEASE)
        self.uc.mem_write(OBJ_VTABLE, bytes(obj_vtable))

        shared_page = bytearray([POISON]) * PAGE_SHARED_SIZE
        struct.pack_into(
            "<I", shared_page, (SHARED_BASE - PAGE_SHARED) + 0x10, case["handle"]
        )
        self.uc.mem_write(PAGE_SHARED, bytes(shared_page))

        descriptor = bytearray([POISON]) * PAGE_SIZE
        struct.pack_into(
            "<4I",
            descriptor,
            0,
            case["d0"],
            case["d1"],
            case["d2"],
            case["d3"],
        )
        self.uc.mem_write(DESC, bytes(descriptor))

        vtable_page = bytearray([POISON]) * PAGE_VTABLE_SIZE
        struct.pack_into("<I", vtable_page, 0x998 + 0x2C, CB_RELEASE)
        struct.pack_into("<I", vtable_page, 0x998 + 0x30, ALT_RELEASE)
        self.uc.mem_write(PAGE_VTABLE, bytes(vtable_page))

        self.uc.mem_write(PAGE_POOL, bytes([POISON]) * PAGE_POOL_SIZE)
        self.uc.mem_write(OUT_ADDR, struct.pack("<I", OUT_SENTINEL))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.uc.mem_write(
            ENTRY_SP,
            struct.pack("<III", case["arg5"], case["arg6"], case["arg7"]),
        )

        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, OUT_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, DESC)
        self.uc.reg_write(arm.UC_ARM_REG_R2, case["arg3"])
        self.uc.reg_write(arm.UC_ARM_REG_R3, case["arg4"])
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_callback = CALLBACK <= address < CALLBACK + PAGE_SIZE
            in_out = OUT_ADDR <= address < OUT_ADDR + 4
            if not (in_stack or in_callback or in_out):
                unexpected_writes.append((address, size, _value))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "fixtures": {
                "record": bytes(self.uc.mem_read(RECORD, PAGE_SIZE)),
                "callback": bytes(self.uc.mem_read(CALLBACK, PAGE_SIZE)),
                "obj_vtable": bytes(self.uc.mem_read(OBJ_VTABLE, PAGE_SIZE)),
                "descriptor": bytes(self.uc.mem_read(DESC, PAGE_SIZE)),
                "vtable_page": bytes(self.uc.mem_read(PAGE_VTABLE, PAGE_VTABLE_SIZE)),
                "shared_page": bytes(self.uc.mem_read(PAGE_SHARED, PAGE_SHARED_SIZE)),
                "pool_page": bytes(self.uc.mem_read(PAGE_POOL, PAGE_POOL_SIZE)),
                "out": bytes(self.uc.mem_read(OUT_ADDR, 4)),
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
            problems.append(f"fixture {key} was modified differently")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "d0": 0x11111111,
        "d1": 0x22222222,
        "d2": 0x33,
        "d3": 0x44444444,
        "arg3": 0x00000003,
        "arg4": 0x00000004,
        "arg5": 0x00000005,
        "arg6": 0x00000006,
        "arg7": 0x00000007,
        "handle": 0xABCD1234,
        "reply": 0x55667788,
        "send_status": 0,
        "init_status": 0,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    cases.append(base_case("success baseline"))

    # --- request result sign gate (only the sign bit is observed)
    for status in (1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        cases.append(base_case(f"request status 0x{status:08x}", send_status=status))

    # --- init result sign gate
    for status in (1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        cases.append(base_case(f"init status 0x{status:08x}", init_status=status))

    # --- allocation / lookup failures
    cases.append(base_case("shared context null", shared_null=True))
    cases.append(base_case("constructor null", ctor_null=True))
    cases.append(base_case("wrapper allocation null", wrapper_null=True))
    cases.append(
        base_case("wrapper null with high reply", wrapper_null=True,
                  reply=0xFFFFFFFF, send_status=0x7FFFFFFF)
    )

    # --- descriptor selector byte boundaries
    for selector in (0x00, 0x01, 0x7F, 0x80, 0xFE, 0xFF):
        cases.append(base_case(f"descriptor byte 0x{selector:02x}", d2=selector))

    # --- zero / high-bit words
    cases.append(base_case("zero words", d0=0, d1=0, d2=0, d3=0, handle=0,
                           reply=0, arg3=0, arg4=0, arg5=0, arg6=0, arg7=0))
    cases.append(
        base_case(
            "all ones",
            d0=0xFFFFFFFF,
            d1=0xFFFFFFFF,
            d2=0xFFFFFFFF,
            d3=0xFFFFFFFF,
            handle=0xFFFFFFFF,
            reply=0xFFFFFFFF,
            arg3=0xFFFFFFFF,
            arg4=0xFFFFFFFF,
            arg5=0xFFFFFFFF,
            arg6=0xFFFFFFFF,
            arg7=0xFFFFFFFF,
        )
    )
    cases.append(base_case("handle 0", handle=0))
    cases.append(base_case("reply high bit", reply=0x80000000))
    cases.append(base_case("descriptor words high bit", d0=0x80000000,
                           d1=0x7FFFFFFF, d3=0x80000000))

    # --- failure combinations that also exercise the high bits
    cases.append(
        base_case("request failure with all ones", send_status=0xFFFFFFFE,
                  d0=0xFFFFFFFF, d3=0xFFFFFFFF, handle=0xFFFFFFFF)
    )
    cases.append(
        base_case("init failure with high words", init_status=0x80000001,
                  d0=0x80000000, reply=0xFFFFFFFF)
    )

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = ADC74Runner().run(orig_code, case)
        cand = ADC74Runner().run(cand_code, case)
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
    print("Testing engine_func_002adc74 (0x002adc74)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B.")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("request_magic", "constexpr u32 kRequestMagic = 0x2345678A;",
         "constexpr u32 kRequestMagic = 0x2345678B;"),
        ("selector_fill", "constexpr u32 kSelectorFill = 0xFFFFFF00;",
         "constexpr u32 kSelectorFill = 0xFFFF0000;"),
        ("handle_offset", "constexpr u32 kSharedHandleOffset = 0x10;",
         "constexpr u32 kSharedHandleOffset = 0x14;"),
        ("record_size", "constexpr u32 kRecordSize = 0x130;",
         "constexpr u32 kRecordSize = 0x12F;"),
        ("callback_vtable", "constexpr u32 kCallbackVtable = 0x00420998;",
         "constexpr u32 kCallbackVtable = 0x0042099C;"),
        ("record_release_slot",
         "constexpr u32 kRecordReleaseSlot = 0x30 / 4;",
         "constexpr u32 kRecordReleaseSlot = 0x2C / 4;"),
        ("callback_release_slot",
         "constexpr u32 kCallbackReleaseSlot = 0x2C / 4;",
         "constexpr u32 kCallbackReleaseSlot = 0x30 / 4;"),
        ("buffer_count_a", "constexpr u32 kBufferCountA = 2;",
         "constexpr u32 kBufferCountA = 3;"),
        ("error_status", "constexpr u32 kErrorStatus = 0xD8604659;",
         "constexpr u32 kErrorStatus = 0xD8604658;"),
        ("success_store",
         "    *out = static_cast<u32>(reinterpret_cast<std::uintptr_t>(record));\n"
         "    return 0;",
         "    *out = static_cast<u32>(reinterpret_cast<std::uintptr_t>(record) + 4u);\n"
         "    return 0;"),
        ("svc_removed", "        engine_svc_002addd4(reply);\n", ""),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = ADC74Runner().run(orig_code, case)
            try:
                bad = ADC74Runner().run(mutant_code, case)
            except RuntimeError:
                detected = True
                break
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
