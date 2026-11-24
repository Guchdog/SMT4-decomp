#!/usr/bin/env python3
"""Differential test for engine_func_002b5820 (0x002B5820) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the engine_func_002b5820 body,
resolves every direct call to a deterministic stub placed at the original
target address, and runs the pinned original (extracted/exefs/code.bin) against
the candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and the callee-saved r4-r11;
  * the ordered call log: every helper with all register arguments, the two
    architected stack arguments of 0x00148210, the 64-bit sleep request, and
    the `svc #0x28` system-tick reads;
  * the whole globals page (0x00400000..0x00480000, which holds the marker
    words at 0x0044E370/0x0044E378) and every write outside the private stack.

Coverage: both entry marker equalities suppressing the tick baseline; the
normal baseline read; success with and without the latched bit-16 follow-up;
negative results that are not the retry code; the 0xC8A0CC02 retry path with
its marker-equality exit, its marker-equality no-clock retry, and the signed
elapsed comparison in both directions across tick wrap-around and 64-bit
sign boundaries; the `size > 0x1000` notification including a mid-loop
republish of a marker word; the buffer/length gate with each side zero; and
the `size == 0x1000` boundary.  Negative controls mutate the retry code, the
size guard, the notification flag mask/shift, the follow-up latch, the sleep
request, the tick scaling, a marker address and the elapsed comparison; each
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
SOURCE = ROOT / "src/engine/leaf_batch41_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_002b5820"

FUNC_ADDR = 0x002B5820
FUNC_SIZE = 484

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # 0x00148210 .. 0x002BCE48 plus the function
GLOBAL_ADDR = 0x00400000
GLOBAL_SIZE = 0x00080000  # covers 0x0044E370..0x0044E380
OUT_ADDR = 0x00500000
OUT_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

PRIMARY_ADDR = 0x0044E370   # 0x0044E370, two u32 loads in the retry path
SECONDARY_ADDR = 0x0044E378  # 0x0044E378, one ldrd everywhere

BUFFER_OUT = OUT_ADDR + 0x100
EXTRA_ARG = 0x1234ABCD

STUB_REQUEST = 0x00148210       # func_00148210
STUB_FOLLOWUP = 0x00147FE0      # engine_func_00147fe0
STUB_NOTIFY = 0x002BCE48        # engine_func_002bce48
STUB_LOCK = 0x002BB6B8          # engine_func_002bb6b8
STUB_UNLOCK = 0x002BB648        # engine_func_002bb648
STUB_CONTEXT = 0x002BB440       # func_002bb440
STUB_SLEEP = 0x002BB490         # camp_func_002bb490

STUB_NAMES = {
    STUB_REQUEST: "func_00148210",
    STUB_FOLLOWUP: "engine_func_00147fe0",
    STUB_NOTIFY: "engine_func_002bce48",
    STUB_LOCK: "engine_func_002bb6b8",
    STUB_UNLOCK: "engine_func_002bb648",
    STUB_CONTEXT: "func_002bb440",
    STUB_SLEEP: "camp_func_002bb490",
}

# Architected stack words each helper receives.
STACK_ARGS = {
    STUB_REQUEST: 2,   # length, extra
    STUB_FOLLOWUP: 0,
    STUB_NOTIFY: 0,
    STUB_LOCK: 0,
    STUB_UNLOCK: 0,
    STUB_CONTEXT: 0,
    STUB_SLEEP: 0,     # the 64-bit value is in r0:r1
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

MAX_LOOP_CALLS = 16


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    functions = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in functions.items():
        if "002b5820" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_002b5820 missing from {obj_file}: {sorted(functions)}"
        )

    code, relocs = candidate
    code = bytearray(code)
    for rel in relocs:
        if rel.relocation_type not in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            raise RuntimeError(
                f"unexpected relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = None
        for address, name in STUB_NAMES.items():
            if name == rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        displacement = (target - (FUNC_ADDR + rel.offset + 8)) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        condition = original & 0xFF000000
        struct.pack_into(
            "<I", code, rel.offset, condition | (displacement & 0x00FFFFFF)
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
    try:
        result = compile_tu_armv6k(mutant_src, obj_file, ROOT)
        if result.returncode != 0:
            raise RuntimeError(f"Mutant compilation failed: {result.stderr}")
        return relocate_candidate(obj_file)
    finally:
        # Each mutant is a full copy of the translation unit; keep the
        # workspace small by discarding it once its body has been extracted.
        for path in OUT_DIR.glob(f"mutant_{name}.*"):
            path.unlink(missing_ok=True)


class Script:
    """Scripted return values for one stub, repeating the final entry."""

    def __init__(self, values, default=0):
        self.values = list(values)
        self.default = default
        self.index = 0

    def next(self):
        if self.index < len(self.values):
            value = self.values[self.index]
            self.index += 1
            return value
        return self.default


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(GLOBAL_ADDR, GLOBAL_SIZE)
        self.uc.mem_map(OUT_ADDR, OUT_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_INTR, self._on_interrupt)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.scripts: dict = {}
        self.case: dict = {}
        self.request_calls = 0

    # ------------------------------------------------------------------ stubs
    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        raw = self.uc.mem_read(sp, 4 * count)
        return struct.unpack(f"<{count}I", raw)

    def _log(self, address: int, *args) -> None:
        self.call_log.append(
            (STUB_NAMES[address], args + self._stack_words(STACK_ARGS[address]))
        )

    def _script(self, name: str):
        return self.scripts[name]

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def _on_interrupt(self, uc, intno, user_data) -> None:
        if intno != 2:  # ARM SVC
            return
        pc = uc.reg_read(arm.UC_ARM_REG_PC)
        instruction = struct.unpack("<I", uc.mem_read(pc - 4, 4))[0]
        immediate = instruction & 0x00FFFFFF
        if immediate != 0x28:
            raise AssertionError(f"unexpected svc #{immediate:#x}")
        tick = self._script("ticks").next() & 0xFFFFFFFFFFFFFFFF
        self.call_log.append(("svcGetSystemTick", (tick,)))
        uc.reg_write(arm.UC_ARM_REG_R0, tick & 0xFFFFFFFF)
        uc.reg_write(arm.UC_ARM_REG_R1, (tick >> 32) & 0xFFFFFFFF)

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_REQUEST:
            self.request_calls += 1
            if self.request_calls > MAX_LOOP_CALLS:
                raise AssertionError("retry loop exceeded the scripted depth")
            self._log(address, r0, r1, r2, r3)
            result = self._script("request").next() & 0xFFFFFFFF
            uc.reg_write(arm.UC_ARM_REG_R0, result)
            # A case may republish a marker word between the entry comparison
            # and the error-path comparison.
            update = self.case.get("marker_update")
            if update is not None and update[0] == self.request_calls:
                if update[1] is not None:
                    self.uc.mem_write(
                        PRIMARY_ADDR,
                        struct.pack("<Q", update[1] & 0xFFFFFFFFFFFFFFFF),
                    )
                if update[2] is not None:
                    self.uc.mem_write(
                        SECONDARY_ADDR,
                        struct.pack("<Q", update[2] & 0xFFFFFFFFFFFFFFFF),
                    )
        elif address == STUB_FOLLOWUP:
            self._log(address, r0)
            self._script("followup").next()
        elif address == STUB_NOTIFY:
            # 0x002BCE48 ignores r0 (it stores 0 before tail-calling
            # 0x002AD8A8), so the dead caller-saved value is not compared.
            self._log(address)
            self._script("notify").next()
        elif address == STUB_LOCK:
            self._log(address)
            self._script("lock").next()
        elif address == STUB_UNLOCK:
            self._log(address)
            self._script("unlock").next()
        elif address == STUB_CONTEXT:
            self._log(address)
            result = self._script("context").next() & 0xFFFFFFFF
            uc.reg_write(arm.UC_ARM_REG_R0, result)
        elif address == STUB_SLEEP:
            delay = ((r1 & 0xFFFFFFFF) << 32) | (r0 & 0xFFFFFFFF)
            self._log(address, delay)
            self._script("sleep").next()
        else:  # pragma: no cover
            raise AssertionError(f"unexpected stub address {address:#x}")

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
        self.request_calls = 0
        self.scripts = {
            "request": Script(case.get("request", [0])),
            "followup": Script(case.get("followup", [0])),
            "notify": Script(case.get("notify", [0])),
            "lock": Script(case.get("lock", [0])),
            "unlock": Script(case.get("unlock", [0])),
            "context": Script(case.get("context", [0x12340000])),
            "sleep": Script(case.get("sleep", [0])),
            "ticks": Script(case.get("ticks", [0])),
        }

        self.uc.mem_write(FUNC_ADDR, code)

        # Globals page: deterministic filler plus the case markers.
        self.uc.mem_write(GLOBAL_ADDR, b"\x00" * GLOBAL_SIZE)
        self.uc.mem_write(
            PRIMARY_ADDR,
            struct.pack("<Q", case.get("primary", 0) & 0xFFFFFFFFFFFFFFFF),
        )
        self.uc.mem_write(
            SECONDARY_ADDR,
            struct.pack("<Q", case.get("secondary", 0) & 0xFFFFFFFFFFFFFFFF),
        )

        # Output page: sentinel filler so untouched words are still compared.
        self.uc.mem_write(OUT_ADDR, b"\xA5" * OUT_SIZE)

        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, case.get("arg0", 0x11110000))
        self.uc.reg_write(arm.UC_ARM_REG_R1, case.get("flags", 0) & 0xFFFFFFFF)
        buffer = case.get("buffer", BUFFER_OUT)
        self.uc.reg_write(arm.UC_ARM_REG_R2, buffer & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R3, case.get("size", 4) & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        # [sp+0x00] = extra, [sp+0x04] = padding (never read by the original),
        # [sp+0x08] = 64-bit timeout.
        sp = ENTRY_SP
        self.uc.mem_write(
            sp,
            struct.pack(
                "<II",
                case.get("extra", EXTRA_ARG) & 0xFFFFFFFF,
                0xDEADBEEF,
            ),
        )
        self.uc.mem_write(
            sp + 8, struct.pack("<Q", case.get("timeout", 0) & 0xFFFFFFFFFFFFFFFF)
        )

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except unicorn.UcError as error:
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"emulation failed at PC=0x{pc:08x}: {error}") from error
        except AssertionError as error:
            raise RuntimeError(
                f"{error} (PC=0x{self.uc.reg_read(arm.UC_ARM_REG_PC):08x})"
            ) from error

        unexpected_writes = sorted(
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
            "call_log": self._normalise(self.call_log),
            "globals": bytes(self.uc.mem_read(GLOBAL_ADDR, GLOBAL_SIZE)),
            "outputs": bytes(self.uc.mem_read(OUT_ADDR, OUT_SIZE)),
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "call_log"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["unexpected_writes"] != cand["unexpected_writes"]:
        problems.append(
            "writes:\n    orig="
            + repr(orig["unexpected_writes"])
            + "\n    cand="
            + repr(cand["unexpected_writes"])
        )
    for key in ("globals", "outputs"):
        if orig[key] != cand[key]:
            first = next(
                index
                for index, (left, right) in enumerate(zip(orig[key], cand[key]))
                if left != right
            )
            problems.append(
                f"{key} differ from byte {first:#x}: "
                f"orig={orig[key][first:first + 8]!r} "
                f"cand={cand[key][first:first + 8]!r}"
            )
    return problems


M64 = 0xFFFFFFFFFFFFFFFF
TICK_MAGIC = 0x3BAD34AEE


def multiply_high_unsigned(a: int, b: int) -> int:
    low_low = (a & 0xFFFFFFFF) * (b & 0xFFFFFFFF)
    low_high = (a & 0xFFFFFFFF) * (b >> 32)
    high_low = (a >> 32) * (b & 0xFFFFFFFF)
    high_high = (a >> 32) * (b >> 32)
    middle = (low_low >> 32) + (low_high & 0xFFFFFFFF) + (high_low & 0xFFFFFFFF)
    return (
        high_high + (low_high >> 32) + (high_low >> 32) + (middle >> 32)
    ) & M64


def multiply_high_signed(a: int, b: int) -> int:
    high = multiply_high_unsigned(a, b)
    if a >> 63:
        high = (high - b) & M64
    if b >> 63:
        high = (high - a) & M64
    return high


def tick_to_nanoseconds(tick: int) -> int:
    low = (tick * TICK_MAGIC & M64) >> 32
    high = (multiply_high_signed(tick, TICK_MAGIC) << 32) & M64
    return (low + high) & M64


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "timeout": 0x0000000000001000,
        "primary": 0,
        "secondary": 0,
        "arg0": 0x11110000,
        "flags": 0,
        "buffer": BUFFER_OUT,
        "size": 4,
        "extra": EXTRA_ARG,
        "request": [0],
        "followup": [0],
        "notify": [0],
        "lock": [0],
        "unlock": [0],
        "context": [0x12340000],
        "sleep": [0],
        "ticks": [0, 0, 0, 0],
    }
    case.update(overrides)
    return case


def make_cases() -> list:
    cases = []
    marker = 0x1122334455667788

    # --- entry marker equalities suppress the baseline tick read.
    cases.append(
        base_case(
            "timeout equals the secondary marker, success",
            timeout=marker, primary=0, secondary=marker,
        )
    )
    cases.append(
        base_case(
            "timeout equals the primary marker, success",
            timeout=marker, primary=marker, secondary=0,
        )
    )

    # --- plain success paths.
    cases.append(base_case("success with baseline tick 0"))
    cases.append(
        base_case(
            "success with a non-zero baseline tick",
            ticks=[0x0123456789ABCDEF], timeout=0x7FFFFFFFFFFFFFFF,
        )
    )
    cases.append(
        base_case(
            "success with every argument distinct",
            arg0=0xFEEDFACE, flags=0x00020005, size=0x800,
            extra=0x0BADF00D, context=[0xCAFEBABE],
        )
    )

    # --- bit-16 follow-up latch.
    cases.append(
        base_case(
            "flags bit 16 set, success calls the follow-up with 0",
            flags=0x00010000,
        )
    )
    cases.append(
        base_case(
            "flags bit 16 set, negative non-retry result skips the follow-up",
            flags=0x00010000, request=[0xC8A0CC04],
        )
    )
    cases.append(
        base_case(
            "flags bit 16 clear, success skips the follow-up",
            flags=0x00030000 & ~0x00010000,
        )
    )
    cases.append(
        base_case(
            "flags bit 20 only, success skips the follow-up",
            flags=0x00100000,
        )
    )

    # --- negative results other than the retry code return at once.
    for code in (0xC8A0CC04, 0xE0A0CC08, 0xC8A0CFF0, 0x80000000):
        cases.append(
            base_case(
                f"negative result 0x{code:08X} returns without a retry",
                request=[code], ticks=[0],
            )
        )

    # --- the size notification and its boundaries.
    cases.append(
        base_case(
            "size 0x1001 notifies with flags & 0x10000 == 0",
            size=0x1001, ticks=[0],
        )
    )
    cases.append(
        base_case(
            "size 0x1001 notifies with flags & 0x10000 != 0",
            size=0x1001, flags=0x00010000, ticks=[0],
        )
    )
    cases.append(
        base_case(
            "size 0x1000 does not notify",
            size=0x1000,
        )
    )
    cases.append(
        base_case(
            "size 0xFFFFFFFF notifies and forwards the raw size",
            size=0xFFFFFFFF, ticks=[0],
        )
    )
    cases.append(
        base_case(
            "size 0x1001 notifies again on every retry",
            size=0x1001, request=[0xC8A0CC02, 0], timeout=0x7FFFFFFFFFFFFFFF,
            ticks=[0, 1],
        )
    )

    # --- the buffer/length gate.
    cases.append(
        base_case(
            "null buffer with non-zero size collapses both to zero",
            buffer=0, size=9,
        )
    )
    cases.append(
        base_case(
            "zero size with a non-null buffer collapses both to zero",
            buffer=BUFFER_OUT, size=0,
        )
    )
    cases.append(
        base_case(
            "null buffer with zero size still notifies when size > 0x1000? no",
            buffer=0, size=0,
        )
    )

    # --- retry via marker equality exits.
    cases.append(
        base_case(
            "retry code, secondary marker republished mid-loop returns",
            timeout=marker, primary=marker, secondary=0x99,
            request=[0xC8A0CC02], ticks=[0],
            marker_update=(1, None, marker & 0xFFFFFFFFFFFFFFFF),
        )
    )
    cases.append(
        base_case(
            "retry code, primary marker republished mid-loop retries without a clock",
            timeout=marker, primary=0x77, secondary=0x88,
            request=[0xC8A0CC02, 0],
            ticks=[0x500],                       # only the entry baseline
            marker_update=(1, marker, None),
        )
    )
    cases.append(
        base_case(
            "retry code, both markers unchanged, elapsed exceeds timeout",
            timeout=0, primary=marker, secondary=marker + 1,
            request=[0xC8A0CC02], ticks=[0, 1],
        )
    )
    cases.append(
        base_case(
            "retry code, elapsed below timeout retries then succeeds",
            timeout=0x7FFFFFFFFFFFFFFF, primary=marker, secondary=marker + 1,
            request=[0xC8A0CC02, 0], ticks=[0, 1],
        )
    )
    cases.append(
        base_case(
            "retry code twice, then success",
            timeout=0x7FFFFFFFFFFFFFFF, primary=marker, secondary=marker + 1,
            request=[0xC8A0CC02, 0xC8A0CC02, 0], ticks=[0, 1, 2],
        )
    )

    # --- signed elapsed comparison across boundaries and wrap-around.
    for baseline, now, timeout, label in (
        (0, 0, 0, "zero elapsed, zero timeout retries"),
        (0, 0, 0xFFFFFFFFFFFFFFFF, "zero elapsed, signed -1 timeout returns"),
        (0, 1, 0, "one tick elapsed, zero timeout returns"),
        (0, 1, 0xFFFFFFFFFFFFFFFF, "one tick elapsed, signed -1 timeout returns"),
        (0xFFFFFFFFFFFFFFFF, 1, 0x7FFFFFFFFFFFFFFF, "wrap to two ticks, huge timeout"),
        (0x10, 0, 0x8000000000000000, "negative timeout boundary"),
        (0, 0x0000000100000000, 0x7FFFFFFFFFFFFFFF, "34-bit span boundary"),
        (0xAAAAAAAA00000000, 0x5555555500000000, 0x00000000FFFFFFFF, "high-word wrap"),
        (0x8000000000000000, 0, 0, "baseline sign bit"),
        (0, 0x8000000000000000, 0, "now sign bit"),
        (0xFFFFFFFFFFFFFFFF, 0, 0, "elapsed of -1 tick"),
        (0xFFFFFFFFFFFFFFFF, 0, 0x8000000000000000, "negative elapsed, negative timeout"),
    ):
        cases.append(
            base_case(
                f"ticks {label} (0x{baseline:016x} -> 0x{now:016x}, "
                f"timeout 0x{timeout:016x})",
                timeout=timeout,
                primary=marker,
                secondary=marker + 1,
                request=[0xC8A0CC02, 0xC8A0CC02, 0],
                ticks=[baseline, now, now, now],
            )
        )

    # --- elapsed value pinned exactly: timeout at elapsed-1 / elapsed /
    # elapsed+1 must produce return / retry / retry for the same delta.
    for baseline, now in (
        (0, 1),
        (0, 0x1000),
        (0, 0x0000000100000000),
        (0xFFFFFFFFFFFFFFFF, 1),
        (0x8000000000000000, 0),
        (0, 0x8000000000000000),
        (0xAAAAAAAA00000000, 0x5555555500000000),
        (0x0123456789ABCDEF, 0xFEDCBA9876543210),
        (0xFFFFFFFF00000000, 0x00000000FFFFFFFF),
        (0x123456789ABCDEF0, 0x123456789ABCDEF0),
    ):
        elapsed = tick_to_nanoseconds((now - baseline) & M64)
        for offset, expect in ((-1, "return"), (0, "retry"), (1, "retry")):
            timeout = (elapsed + offset) & M64
            cases.append(
                base_case(
                    f"elapsed pin 0x{baseline:016x}->0x{now:016x}: "
                    f"timeout=elapsed{offset:+d} (0x{timeout:016x}) -> {expect}",
                    timeout=timeout,
                    primary=marker,
                    secondary=marker + 1,
                    # A retry expects a second, successful attempt; a return
                    # expects the first result to be used directly.
                    request=([0xC8A0CC02, 0] if expect == "retry"
                             else [0xC8A0CC02]),
                    ticks=[baseline, now],
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
    print("Testing engine_func_002b5820 (0x002b5820)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B.")
    if len(orig_code) != FUNC_SIZE:
        raise SystemExit("unexpected original size")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("retry_code", "constexpr u32 kRetryCode = 0xC8A0CC02u;",
         "constexpr u32 kRetryCode = 0xC8A0CC04u;"),
        ("maximum_size", "constexpr u32 kMaximumSize = 0x1000u;",
         "constexpr u32 kMaximumSize = 0x0FFFu;"),
        ("marker_pair_high", "static_cast<uintptr_t>(address + 4)",
         "static_cast<uintptr_t>(address + 8)"),
        ("followup_shift", "((flags >> 16) & 1u) != 0;",
         "((flags >> 15) & 1u) != 0;"),
        ("followup_latch", "((flags >> 16) & 1u) != 0;",
         "((flags >> 16) & 1u) == 0;"),
        ("sleep_request", "constexpr u32 kRetrySleepNanoseconds = 10000000u;",
         "constexpr u32 kRetrySleepNanoseconds = 10000001u;"),
        ("tick_magic", "constexpr u64 kTickNanosecondsMagic = 0x3BAD34AEEull;",
         "constexpr u64 kTickNanosecondsMagic = 0x3BAD34AEDull;"),
        ("secondary_marker", "constexpr u32 kSecondaryMarkerAddress = 0x0044E378u;",
         "constexpr u32 kSecondaryMarkerAddress = 0x0044E37Cu;"),
        ("elapsed_compare",
         "if (static_cast<s64>(timeout_nanoseconds) <",
         "if (static_cast<s64>(timeout_nanoseconds) <="),
        ("gate", "if (data == 0 || length == 0) {",
         "if (data == 0 && length == 0) {"),
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
