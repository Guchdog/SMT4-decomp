#!/usr/bin/env python3
"""Differential test for camp_func_0013b508 (0x0013b508) using Unicorn ARM.

Compiles src/engine/leaf_batch34_c.cpp, extracts the camp_func_0013b508 body,
resolves its direct calls to deterministic stubs, and runs the pinned original
(extracted/exefs/code.bin) against the candidate in separate Unicorn machines
with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log: every helper with all four register arguments, the
    architected stack arguments, the 64-bit sleep request, and both kernel
    services (`svc #0x28` tick, `svc #0x23` handle close) with r0 at entry;
  * the full globals page (0x00400000..0x00480000, which holds the two marker
    words at 0x0044E370/0x0044E378, the shared table word at 0x0044E368 and
    the shared word at 0x0044E390) and the whole output page;
  * every write performed outside the private stack.

Coverage: the unchanged-primary-marker short circuit (positive, zero and
negative forwarded results), both marker values suppressing the tick baseline,
a marker that changes while the loop runs, claim failure with the retry code and
with another negative code, the shared-word fast arm with null and non-null
outputs, the descriptor arm with every null/non-null output combination, buffer
present/absent with zero and non-zero counts, a kernel handle that must be
closed and one that must not, and the signed 64-bit elapsed comparison across
tick wrap-around, 64-bit boundaries and both comparison outcomes.  A dedicated
fault check confirms that both implementations take the unmapped write when the
second output pointer is null, since the fast arm stores through r1
unconditionally.

Negative controls mutate the retry code, the sleep request, the shared table
offset, a marker address, the buffer/count gate and the tick scaling; each
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
SOURCE = ROOT / "src/engine/leaf_batch34_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_0013b508"

FUNC_ADDR = 0x0013B508
FUNC_SIZE = 704

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # function plus every stub below 0x002BB6B8
GLOBAL_ADDR = 0x00400000
GLOBAL_SIZE = 0x00080000  # covers 0x0044E360..0x00465644
OUT_ADDR = 0x00700000
OUT_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

PRIMARY_ADDR = 0x0044E370
SECONDARY_ADDR = 0x0044E378
TABLE_WORD_ADDR = 0x0044E368
SHARED_WORD_ADDR = 0x0044E390
CLAIM_WORD_ADDR = 0x00465644

# Output slots inside the private output page.
FIRST_OUT = OUT_ADDR + 0x100
SECOND_OUT = OUT_ADDR + 0x200
BUFFER_OUT = OUT_ADDR + 0x300
FIFTH_OUT = OUT_ADDR + 0x400
SIXTH_OUT = OUT_ADDR + 0x500

# Original direct-call targets.  Stubs are placed at those very addresses so
# the pinned original and the relocated candidate reach the same code.
STUB_FORWARD = 0x0013B014       # func_0013b014
STUB_CLAIM = 0x0013B1E0         # func_0013b1e0
STUB_DESCRIPTOR = 0x0013B364    # func_0013b364
STUB_SHARED_READ = 0x002A84DC   # func_002a84dc
STUB_SHARED_WRITE = 0x002AD45C  # func_002ad45c
STUB_SHARED_RELEASE = 0x002A84D0  # func_002a84d0
STUB_ENGINE_VALUE = 0x002BB440  # func_002bb440
STUB_SLEEP = 0x002BB490         # camp_func_002bb490
STUB_ENGINE_UNLOCK = 0x002BB648  # engine_func_002bb648
STUB_ENGINE_LOCK = 0x002BB6B8   # engine_func_002bb6b8

STUB_NAMES = {
    STUB_FORWARD: "func_0013b014",
    STUB_CLAIM: "func_0013b1e0",
    STUB_DESCRIPTOR: "func_0013b364",
    STUB_SHARED_READ: "func_002a84dc",
    STUB_SHARED_WRITE: "func_002ad45c",
    STUB_SHARED_RELEASE: "func_002a84d0",
    STUB_ENGINE_VALUE: "func_002bb440",
    STUB_SLEEP: "camp_func_002bb490",
    STUB_ENGINE_UNLOCK: "engine_func_002bb648",
    STUB_ENGINE_LOCK: "engine_func_002bb6b8",
}

# Architected stack words each helper receives.
STACK_ARGS = {
    STUB_FORWARD: 3,      # fifth output, sixth output, 0
    STUB_CLAIM: 0,
    STUB_DESCRIPTOR: 3,   # count, fourth output, handle output
    STUB_SHARED_READ: 0,
    STUB_SHARED_WRITE: 0,
    STUB_SHARED_RELEASE: 0,
    STUB_ENGINE_VALUE: 0,
    STUB_SLEEP: 0,
    STUB_ENGINE_UNLOCK: 0,
    STUB_ENGINE_LOCK: 0,
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
        if "0013b508" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"camp_func_0013b508 missing from {obj_file}: {sorted(functions)}")

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
        struct.pack_into("<I", code, rel.offset, condition | (displacement & 0x00FFFFFF))
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch34_c.o"
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
        self.claim_calls = 0

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
        if immediate == 0x28:
            tick = self._script("ticks").next() & 0xFFFFFFFFFFFFFFFF
            self.call_log.append(("svcGetSystemTick", (tick,)))
            uc.reg_write(arm.UC_ARM_REG_R0, tick & 0xFFFFFFFF)
            uc.reg_write(arm.UC_ARM_REG_R1, (tick >> 32) & 0xFFFFFFFF)
        elif immediate == 0x23:
            handle = uc.reg_read(arm.UC_ARM_REG_R0)
            self.call_log.append(("svcCloseHandle", (handle,)))
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        else:  # pragma: no cover - defensive
            raise AssertionError(f"unexpected svc #{immediate:#x}")

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_FORWARD:
            self._log(address, r0, r1, r2, r3)
            result = self._script("forward").next() & 0xFFFFFFFF
            uc.reg_write(arm.UC_ARM_REG_R0, result)
        elif address == STUB_CLAIM:
            self.claim_calls += 1
            if self.claim_calls > MAX_LOOP_CALLS:
                raise AssertionError("retry loop exceeded the scripted depth")
            self._log(address)
            result = self._script("claim").next() & 0xFFFFFFFF
            uc.reg_write(arm.UC_ARM_REG_R0, result)
            # A case may republish one of the marker words between the entry
            # comparison and the error-path comparison.
            update = self.case.get("marker_update")
            if update is not None and update[0] == self.claim_calls:
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
        elif address == STUB_SHARED_READ:
            self._log(address)
            result = self._script("shared_read").next() & 0xFFFFFFFF
            uc.reg_write(arm.UC_ARM_REG_R0, result)
        elif address == STUB_SHARED_WRITE:
            self._log(address, r0)
            self._script("shared_write").next()
            self.uc.mem_write(SHARED_WORD_ADDR, struct.pack("<I", r0 & 0xFFFFFFFF))
        elif address == STUB_SHARED_RELEASE:
            self._log(address)
            self._script("release").next()
        elif address == STUB_ENGINE_LOCK:
            self._log(address)
            self._script("lock").next()
        elif address == STUB_ENGINE_UNLOCK:
            self._log(address)
            self._script("unlock").next()
        elif address == STUB_ENGINE_VALUE:
            self._log(address)
            result = self._script("engine_value").next() & 0xFFFFFFFF
            uc.reg_write(arm.UC_ARM_REG_R0, result)
        elif address == STUB_SLEEP:
            delay = r0 | (r1 << 32)
            self._log(address, delay)
            self._script("sleep").next()
        elif address == STUB_DESCRIPTOR:
            self._log(address, r0, r1, r2, r3)
            outputs = self.case.get("descriptor_outputs", (0, 0, 0, 0))
            value = self._script("descriptor").next() & 0xFFFFFFFF
            signed = value - (1 << 32) if value & 0x80000000 else value
            if signed >= 0:
                for pointer, output in zip((r0, r2), outputs[:2]):
                    self.uc.mem_write(pointer, struct.pack("<I", output & 0xFFFFFFFF))
                sp = uc.reg_read(arm.UC_ARM_REG_SP)
                _count_word, out_d, out_e = struct.unpack(
                    "<III", self.uc.mem_read(sp, 12)
                )
                self.uc.mem_write(out_d, struct.pack("<I", outputs[2] & 0xFFFFFFFF))
                self.uc.mem_write(out_e, struct.pack("<I", outputs[3] & 0xFFFFFFFF))
            uc.reg_write(arm.UC_ARM_REG_R0, value)
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
        self.claim_calls = 0
        self.scripts = {
            "forward": Script(case.get("forward", [0])),
            "claim": Script(case.get("claim", [1])),
            "shared_read": Script(case.get("shared_read", [0])),
            "shared_write": Script(case.get("shared_write", [0])),
            "release": Script(case.get("release", [0])),
            "lock": Script(case.get("lock", [0])),
            "unlock": Script(case.get("unlock", [0])),
            "engine_value": Script(case.get("engine_value", [0x12340000])),
            "sleep": Script(case.get("sleep", [0])),
            "descriptor": Script(case.get("descriptor", [0])),
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
        self.uc.mem_write(
            TABLE_WORD_ADDR, struct.pack("<I", case.get("table_word", 0) & 0xFFFFFFFF)
        )
        self.uc.mem_write(
            SHARED_WORD_ADDR,
            struct.pack("<I", case.get("shared_init", 0) & 0xFFFFFFFF),
        )
        self.uc.mem_write(CLAIM_WORD_ADDR, struct.pack("<I", 0x5A5A5A5A))

        # Output page: sentinel filler so untouched words are still compared.
        self.uc.mem_write(OUT_ADDR, b"\xA5" * OUT_SIZE)

        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(
            arm.UC_ARM_REG_R0, FIRST_OUT if case.get("first", True) else 0
        )
        self.uc.reg_write(
            arm.UC_ARM_REG_R1, SECOND_OUT if case.get("second", True) else 0
        )
        self.uc.reg_write(
            arm.UC_ARM_REG_R2, BUFFER_OUT if case.get("buffer", True) else 0
        )
        self.uc.reg_write(arm.UC_ARM_REG_R3, case.get("count", 0) & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        # Fifth and sixth outputs plus the 64-bit timeout on the stack at
        # +0x00, +0x04 and +0x08 (the original reads the pair as one 64-bit
        # value; the word at +0x0C is never read).
        sp = ENTRY_SP
        self.uc.mem_write(
            sp,
            struct.pack(
                "<II",
                FIFTH_OUT if case.get("fifth", True) else 0,
                SIXTH_OUT if case.get("sixth", True) else 0,
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
            raise RuntimeError(f"{error} (PC=0x{self.uc.reg_read(arm.UC_ARM_REG_PC):08x})") from error

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


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "timeout": 0x0000000000001000,
        "primary": 0,
        "secondary": 0,
        "table_word": 0x11223344,
        "count": 4,
        "claim": [1, 1, 1, 1],
        "shared_read": [0x00000001, 0x00000002],
        "forward": [0],
        "engine_value": [0x12340000],
        "descriptor": [0],
        "descriptor_outputs": (0xAAAABBBB, 0xCCCCDDDD, 0xEEEEFFFF, 0),
        "ticks": [0, 0],
    }
    case.update(overrides)
    return case


def make_cases() -> list:
    cases = []
    marker = 0x1122334455667788

    # --- unchanged primary marker: the whole routine is forwarded.
    cases.append(
        base_case(
            "primary marker forwarded, null result",
            timeout=marker, primary=marker, forward=[0],
        )
    )
    cases.append(
        base_case(
            "primary marker forwarded, positive result",
            timeout=marker, primary=marker, forward=[0x00000001],
        )
    )
    cases.append(
        base_case(
            "primary marker forwarded, negative result (no retry)",
            timeout=marker, primary=marker, forward=[0xC8A0CFEF],
        )
    )
    cases.append(
        base_case(
            "primary marker forwarded with null outputs",
            timeout=marker, primary=marker, first=False, second=False,
            buffer=False, fifth=False, sixth=False, count=0,
        )
    )

    # --- marker values suppress the baseline tick read.
    cases.append(
        base_case(
            "secondary marker skips baseline, claim failure retries via marker",
            timeout=0x99, primary=marker, secondary=0x99,
            claim=[0, 1, 1], shared_read=[0x55],
        )
    )
    cases.append(
        base_case(
            "primary marker equality after entry skips baseline comparison",
            timeout=0x99, primary=marker, secondary=0x77,
            claim=[0, 1, 1], shared_read=[0x55],
            marker_update=(1, 0x99, None),
        )
    )
    cases.append(
        base_case(
            "secondary marker changes while looping",
            timeout=0x99, primary=marker, secondary=0x77,
            claim=[0, 1, 1], shared_read=[0x55],
            marker_update=(1, None, 0x99),
        )
    )

    # --- other negative results retry without consulting the clock.
    cases.append(
        base_case(
            "descriptor failure retries then fast path",
            claim=[1, 1, 1], shared_read=[0, 0x77],
            descriptor=[0xE0A0CC08],
        )
    )
    cases.append(
        base_case(
            "claim failure retries twice",
            claim=[0, 0, 1, 1], shared_read=[0x66],
            ticks=[0, 10, 20],
        )
    )

    # --- fast arm (shared word non-zero): null and non-null outputs.
    cases.append(base_case("fast arm writes all outputs", claim=[1, 1]))
    cases.append(
        base_case(
            "fast arm with null first/fifth/sixth",
            claim=[1, 1], first=False, fifth=False, sixth=False,
        )
    )
    cases.append(
        base_case(
            "fast arm reads the shared table word at 0x0044E368",
            claim=[1, 1], table_word=0xDEADBEEF,
        )
    )

    # --- descriptor arm: buffer/count gate and null outputs.
    cases.append(
        base_case(
            "descriptor arm, buffer and count",
            claim=[1, 1], shared_read=[0], count=9,
        )
    )
    cases.append(
        base_case(
            "descriptor arm, count zero with buffer present",
            claim=[1, 1], shared_read=[0], count=0,
        )
    )
    cases.append(
        base_case(
            "descriptor arm, count one with buffer present",
            claim=[1, 1], shared_read=[0], count=1,
        )
    )
    cases.append(
        base_case(
            "descriptor arm, null buffer with non-zero count",
            claim=[1, 1], shared_read=[0], buffer=False, count=9,
        )
    )
    cases.append(
        base_case(
            "descriptor arm, every output null",
            claim=[1, 1], shared_read=[0], first=False, second=False,
            buffer=False, fifth=False, sixth=False, count=0,
        )
    )
    cases.append(
        base_case(
            "descriptor arm keeps a caller-supplied handle output open",
            claim=[1, 1], shared_read=[0],
            descriptor_outputs=(0x11, 0x22, 0x33, 0x0000BEEF),
        )
    )
    cases.append(
        base_case(
            "descriptor arm closes a handle written to the dummy slot",
            claim=[1, 1], shared_read=[0], sixth=False,
            descriptor_outputs=(0x11, 0x22, 0x33, 0x00000001),
        )
    )
    cases.append(
        base_case(
            "descriptor arm success then return",
            claim=[1, 1], shared_read=[0], descriptor=[0x7FFFFFFF],
        )
    )
    cases.append(
        base_case(
            "descriptor returns the retry code, elapsed check returns",
            claim=[1, 1], shared_read=[0, 0x55], descriptor=[0xC8A0CFEF],
            timeout=0, primary=marker, secondary=marker + 1, ticks=[0, 1000],
        )
    )
    cases.append(
        base_case(
            "descriptor returns the retry code, elapsed check retries",
            claim=[1, 1], shared_read=[0, 0x55], descriptor=[0xC8A0CFEF],
            timeout=0xFFFFFFFFFFFFFFFF, primary=marker, secondary=marker + 1,
            ticks=[0, 1000],
        )
    )

    # --- elapsed-time comparison: both outcomes and signed boundaries.
    for baseline, now, timeout, label in (
        (0, 0, 0, "zero elapsed, zero timeout retries"),
        (0, 0, 0xFFFFFFFFFFFFFFFF, "zero elapsed, huge timeout retries"),
        (0, 1000, 0, "small elapsed, zero timeout returns"),
        (0, 1000, 0xFFFFFFFFFFFFFFFF, "small elapsed, huge timeout retries"),
        (1000, 0, 0, "wrapping elapsed, zero timeout"),
        (1000, 0, 0xFFFFFFFFFFFFFFFF, "wrapping elapsed, huge timeout"),
        (0xFFFFFFFFFFFFFFFF, 1, 0xFFFFFFFFFFFFFFFF, "wrap to 2 ticks"),
        (0x10, 0, 0x8000000000000000, "negative timeout boundary"),
        (0, 0x0000000100000000, 0x7FFFFFFFFFFFFFFF, "34-bit span boundary"),
        (0xAAAAAAAA00000000, 0x5555555500000000, 0x00000000FFFFFFFF, "high-word wrap"),
        (0x8000000000000000, 0, 0, "baseline sign bit"),
        (0, 0x8000000000000000, 0, "now sign bit"),
    ):
        cases.append(
            base_case(
                f"ticks {label} (0x{baseline:016x} -> 0x{now:016x}, "
                f"timeout 0x{timeout:016x})",
                timeout=timeout,
                primary=marker,
                secondary=marker + 1,
                claim=[0, 1, 1],
                shared_read=[0x55],
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


def check_unconditional_store_fault(orig_code, cand_code) -> None:
    """The fast arm stores through r1 without a null check; both must fault."""
    case = base_case(
        "fast arm with a null second output",
        second=False,
        claim=[1, 1],
        shared_read=[0x00001234],
    )
    faults = []
    for code in (orig_code, cand_code):
        try:
            Runner().run(code, case)
        except RuntimeError as error:
            faults.append(str(error))
        else:  # pragma: no cover - diagnostic path
            raise AssertionError("the null second-output store did not fault")
    for fault in faults:
        assert "Invalid memory write" in fault, fault
    print("  [PASS] null second output faults in both implementations")


def main() -> None:
    print("Testing camp_func_0013b508 (0x0013b508)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B.")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nFault behaviour:")
    check_unconditional_store_fault(orig_code, cand_code)

    print("\nNegative controls:")
    for name, old, new in (
        ("retry_code", "constexpr u32 kClaimFailureCode = 0xC8A0CFEFu;",
         "constexpr u32 kClaimFailureCode = 0xC8A0CFF0u;"),
        ("sleep_request", "constexpr u32 kRetrySleepUnits = 10;",
         "constexpr u32 kRetrySleepUnits = 11;"),
        ("table_offset", "constexpr u32 kSharedTableWordOffset = 0x08;",
         "constexpr u32 kSharedTableWordOffset = 0x0C;"),
        ("secondary_marker", "constexpr u32 kSecondaryMarkerAddress = 0x0044E378u;",
         "constexpr u32 kSecondaryMarkerAddress = 0x0044E37Cu;"),
        ("buffer_gate", "descriptor_buffer != nullptr && descriptor_count != 0;",
         "descriptor_buffer != nullptr && descriptor_count > 1;"),
        ("tick_shift", "return (tick * kTickNanosecondsMagic >> 32) +",
         "return (tick * kTickNanosecondsMagic >> 24) +"),
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
