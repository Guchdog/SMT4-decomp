#!/usr/bin/env python3
"""Differential test for engine_func_0013056c (0x0013056c) using Unicorn ARM.

Compiles src/engine/leaf_batch34_c.cpp, extracts the engine_func_0013056c body,
resolves its seven direct calls to deterministic stubs at the original target
addresses, and runs the pinned original (extracted/exefs/code.bin) against the
candidate in two Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and the callee-saved r4-r11;
  * the ordered call log, including every register argument, the architected
    stack arguments of 0x002AC8E4 / 0x0014056C / 0x00140318 and the pre-filled
    contents of the 0x0014D404 / 0x0014D448 output records as the callees see
    them (this pins the original's { -1, -1, 0 } / { 0, -1*4, 0, 0, 0 } clears);
  * the full contents of the self, context, second-context and stream pages;
  * every emulated write outside the private stack.

Coverage: the lookup-failure, -1-sentinel and all four 0x00141940 kind results;
both walk forms with an empty range, a single index, zero and maximum indices,
and the unsigned 0x7FFFFFFF..0x80000000 boundary (a signed comparison would
stop early); every combination of the two flag bits the function reads plus
flag bits it must ignore; empty, partial and full id sets; helper failure on the
first and on a later iteration of each loop; key/extra/stream sentinels and a
null key; and a mid-walk rewrite of self->context, which must be re-read before
every helper call.

Negative controls mutate the two flag masks, the empty-id sentinel, the
candidate-slot count, the 0x002AC8E4 mode word and the 0x00140318 alternate
selector; each mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_0013056c"

FUNC_ADDR = 0x0013056C
FUNC_SIZE = 432

# The body and every stub target live between 0x00100000 and 0x00300000.
CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000
SELF_ADDR = 0x00710000
SELF_SIZE = 0x00001000
CTX_ADDR = 0x00711000
CTX_SIZE = 0x00001000
CTX2_ADDR = 0x00712000
CTX2_SIZE = 0x00001000
STREAM_ADDR = 0x00713000
STREAM_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_14D404 = 0x0014D404
STUB_141940 = 0x00141940
STUB_2ACA0C = 0x002ACA0C
STUB_2AC8E4 = 0x002AC8E4
STUB_14D448 = 0x0014D448
STUB_14056C = 0x0014056C
STUB_140318 = 0x00140318

STUB_NAMES = {
    STUB_14D404: "engine_func_0014d404",
    STUB_141940: "engine_func_00141940",
    STUB_2ACA0C: "engine_func_002aca0c",
    STUB_2AC8E4: "engine_func_002ac8e4",
    STUB_14D448: "engine_func_0014d448",
    STUB_14056C: "engine_func_0014056c",
    STUB_140318: "engine_func_00140318",
}

# Number of architected stack words each helper receives.
STACK_ARGS = {
    STUB_14D404: 0,
    STUB_141940: 0,
    STUB_2ACA0C: 0,
    STUB_2AC8E4: 1,   # mode (0)
    STUB_14D448: 0,
    STUB_14056C: 1,   # extra
    STUB_140318: 2,   # extra, alternate selector
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

# 0x0014D448 record: 0x1C bytes, four u32 id slots at +0x04..+0x10.
RECORD_PREFILL_SIZE = 0x1C
# 0x0014D404 record: three words at [sp+0x08].
RANGE_PREFILL_SIZE = 0x0C

EMPTY_ID = 0xFFFFFFFF
KEY_SENTINEL = 0x00B0B0B0
VTABLE_SENTINEL = 0xC0DEC0DE


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0013056c" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_0013056c not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type != 28:  # R_ARM_CALL
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = None
        for address, name in STUB_NAMES.items():
            if name == rel.symbol_name:
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


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch34_c.o"
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
def pattern_page(size: int, salt: int) -> bytes:
    return bytes(((index * 7 + salt) & 0xFF) for index in range(size))


def build_self(case: dict) -> bytes:
    page = bytearray(pattern_page(SELF_SIZE, 0x31))
    struct.pack_into("<I", page, 0x00, VTABLE_SENTINEL)
    struct.pack_into("<I", page, 0x04, case.get("context", CTX_ADDR) & 0xFFFFFFFF)
    return bytes(page)


def build_ctx(size: int, salt: int) -> bytes:
    return pattern_page(size, salt)


def build_stream(case: dict) -> bytes:
    return pattern_page(STREAM_SIZE, 0x77)


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(SELF_ADDR, SELF_SIZE)
        self.uc.mem_map(CTX_ADDR, CTX_SIZE)
        self.uc.mem_map(CTX2_ADDR, CTX2_SIZE)
        self.uc.mem_map(STREAM_ADDR, STREAM_SIZE)
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
        self.case: dict = {}
        self.key_calls = 0
        self.record_calls = 0
        self.prepass_calls = 0
        self.id_calls = 0
        self.forward_calls = 0

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _pick(sequence, index: int, default: int = 1) -> int:
        if not sequence:
            return default
        return sequence[index] if index < len(sequence) else sequence[-1]

    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        raw = self.uc.mem_read(sp, 4 * count)
        return struct.unpack(f"<{count}I", raw)

    def _log(self, address: int, args: tuple) -> None:
        self.call_log.append(
            (STUB_NAMES[address], args + self._stack_words(STACK_ARGS[address]))
        )

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    # -------------------------------------------------------------------- stubs
    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        case = self.case

        if address == STUB_14D404:
            prefill = struct.unpack("<3I", uc.mem_read(r2, RANGE_PREFILL_SIZE))
            self._log(address, (r0, r1) + prefill)
            if case["lookup_ok"]:
                uc.mem_write(
                    r2,
                    struct.pack(
                        "<3I",
                        case["begin"] & 0xFFFFFFFF,
                        case["end"] & 0xFFFFFFFF,
                        case["payload"] & 0xFFFFFFFF,
                    ),
                )
            uc.reg_write(
                arm.UC_ARM_REG_R0, 1 if case["lookup_ok"] else 0
            )
        elif address == STUB_141940:
            self._log(address, (r0, r1))
            uc.reg_write(
                arm.UC_ARM_REG_R0, case["kind"] & 0xFFFFFFFF
            )
        elif address == STUB_2ACA0C:
            self._log(address, (r0,))
            self.key_calls += 1
            result = case.get("key", KEY_SENTINEL)
            uc.reg_write(arm.UC_ARM_REG_R0, result & 0xFFFFFFFF)
            if case.get("mutate_context_at") == self.key_calls:
                uc.mem_write(
                    SELF_ADDR + 0x04,
                    struct.pack("<I", case.get("new_context", CTX2_ADDR)),
                )
        elif address == STUB_2AC8E4:
            self._log(address, (r0, r1, r2, r3))
            index = self.prepass_calls
            self.prepass_calls += 1
            uc.reg_write(
                arm.UC_ARM_REG_R0,
                self._pick(case.get("prepass_results"), index) & 0xFFFFFFFF,
            )
        elif address == STUB_14D448:
            raw = bytes(uc.mem_read(r2, RECORD_PREFILL_SIZE))
            word0, id0, id1, id2, id3, word14 = struct.unpack_from("<6I", raw, 0)
            self._log(
                address,
                (r0, r1, word0, id0, id1, id2, id3, word14, raw[0x18], raw[0x19]),
            )
            sets = case.get("id_sets")
            if sets is None:
                ids = case.get("ids", (EMPTY_ID,) * 4)
            else:
                ids = sets[min(self.record_calls, len(sets) - 1)]
            self.record_calls += 1
            uc.mem_write(
                r2,
                struct.pack(
                    "<6I",
                    0x60000000 | self.record_calls,
                    ids[0] & 0xFFFFFFFF,
                    ids[1] & 0xFFFFFFFF,
                    ids[2] & 0xFFFFFFFF,
                    ids[3] & 0xFFFFFFFF,
                    0x14000000 | self.record_calls,
                )
                + bytes((0x18, 0x19)),
            )
            uc.reg_write(
                arm.UC_ARM_REG_R0,
                self._pick(case.get("record_results"), self.record_calls - 1)
                & 0xFFFFFFFF,
            )
        elif address == STUB_14056C:
            self._log(address, (r0, r1, r2, r3))
            index = self.id_calls
            self.id_calls += 1
            uc.reg_write(
                arm.UC_ARM_REG_R0,
                self._pick(case.get("id_results"), index) & 0xFFFFFFFF,
            )
        elif address == STUB_140318:
            self._log(address, (r0, r1, r2, r3))
            index = self.forward_calls
            self.forward_calls += 1
            uc.reg_write(
                arm.UC_ARM_REG_R0,
                self._pick(case.get("forward_results"), index) & 0xFFFFFFFF,
            )
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
        self.key_calls = 0
        self.record_calls = 0
        self.prepass_calls = 0
        self.id_calls = 0
        self.forward_calls = 0

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(SELF_ADDR, build_self(case))
        self.uc.mem_write(CTX_ADDR, build_ctx(CTX_SIZE, 0x11))
        self.uc.mem_write(CTX2_ADDR, build_ctx(CTX2_SIZE, 0x22))
        self.uc.mem_write(STREAM_ADDR, build_stream(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        # Fifth argument sits at the caller's SP, before the frame is built.
        self.uc.mem_write(
            ENTRY_SP, struct.pack("<I", case.get("extra", 0) & 0xFFFFFFFF)
        )
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case.get("selector", 0) & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R2, case.get("stream", STREAM_ADDR))
        self.uc.reg_write(arm.UC_ARM_REG_R3, case.get("flags", 0) & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(
                FUNC_ADDR, TRAP_ADDR, timeout=5_000_000, count=1_000_000
            )
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        external_writes = [
            (address, size, value)
            for address, size, value in self.writes
            if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
        ]

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self._normalise(self.call_log),
            "external_writes": external_writes,
            "fixtures": {
                "self": bytes(self.uc.mem_read(SELF_ADDR, SELF_SIZE)),
                "ctx": bytes(self.uc.mem_read(CTX_ADDR, CTX_SIZE)),
                "ctx2": bytes(self.uc.mem_read(CTX2_ADDR, CTX2_SIZE)),
                "stream": bytes(self.uc.mem_read(STREAM_ADDR, STREAM_SIZE)),
            },
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
    if orig["external_writes"] != cand["external_writes"]:
        problems.append(
            "external writes:\n    orig="
            + repr(orig["external_writes"])
            + "\n    cand="
            + repr(cand["external_writes"])
        )
    return problems


# ----------------------------------------------------------------------- cases
def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "lookup_ok": 1,
        "begin": 1,
        "end": 1,
        "payload": 0x11110000,
        "kind": 1,
        "flags": 0,
        "selector": 0x0000ABCD,
        "extra": 0xE0000001,
        "stream": STREAM_ADDR,
        "key": KEY_SENTINEL,
        "ids": (EMPTY_ID,) * 4,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- lookup failure, sentinel and every 0x00141940 kind result
    cases.append(base_case("range lookup fails", lookup_ok=0))
    cases.append(
        base_case("begin sentinel -1", begin=0xFFFFFFFF, end=0xFFFFFFFF)
    )
    cases.append(base_case("begin sentinel -1 with flags", begin=0xFFFFFFFF,
                           end=0, flags=0xFFFFFFFF))
    for kind in (0, 2, 4, 0x7FFFFFFF, -1):
        cases.append(
            base_case(f"kind {kind} is a no-op success", begin=2, end=4, kind=kind,
                      flags=1)
        )

    # --- id-range form (kind 1): empty ranges
    cases.append(base_case("id range end < begin", begin=4, end=3, flags=0xF))
    cases.append(
        base_case("id range end < begin, unsigned maximum", begin=0xFFFFFFFF,
                  end=0xFFFFFFFE, flags=1)
    )

    # --- id-range form: flags the function ignores
    cases.append(base_case("id range flags 0", begin=0, end=0))
    cases.append(base_case("id range flag bit 1 only", begin=0, end=0, flags=0x02))
    cases.append(base_case("id range flag bit 4 only", begin=0, end=0, flags=0x10))
    cases.append(
        base_case("id range high flag bits only", begin=0, end=0, flags=0xFFFFFFF0)
    )

    # --- id-range form: pre-pass only
    cases.append(
        base_case("id range pre-pass single", begin=0, end=0, flags=0x01,
                  ids=(0x51, -1, -1, -1))
    )
    cases.append(
        base_case("id range pre-pass three indices", begin=2, end=4, flags=0x01)
    )
    cases.append(
        base_case("id range pre-pass null key", begin=1, end=2, flags=0x01, key=0)
    )
    cases.append(
        base_case("id range pre-pass unsigned boundary", begin=0x7FFFFFFF,
                  end=0x80000000, flags=0x01)
    )
    cases.append(
        base_case("id range pre-pass maximum single index", begin=0xFFFFFFFE,
                  end=0xFFFFFFFE, flags=0x01)
    )

    # --- id-range form: record expansion only
    cases.append(
        base_case("id range records all empty", begin=3, end=3, flags=0x0C)
    )
    cases.append(
        base_case("id range records flag bit 2", begin=3, end=3, flags=0x04,
                  ids=(0x42, -1, -1, -1))
    )
    cases.append(
        base_case("id range records flag bit 3", begin=3, end=3, flags=0x08,
                  ids=(0x43, -1, -1, -1))
    )
    cases.append(
        base_case("id range records partial ids", begin=5, end=5, flags=0x0C,
                  ids=(0x30, -1, 0x10, -1))
    )
    cases.append(
        base_case("id range records all four ids", begin=5, end=5, flags=0x0C,
                  ids=(1, 2, 3, 4))
    )
    cases.append(
        base_case("id range records duplicate ids", begin=6, end=6, flags=0x0C,
                  ids=(7, 7, -1, 7))
    )
    cases.append(
        base_case("id range records negative ids", begin=6, end=6, flags=0x0C,
                  ids=(0x80000000, -2, -3, -4))
    )
    cases.append(
        base_case("id range records every index", begin=0, end=2, flags=0x0C,
                  id_sets=[(0x11, -1, -1, -1), (-1, 0x22, -1, -1), (0x33, -1, -1, 0x44)])
    )

    # --- id-range form: both flag groups, full mask and sentinels
    cases.append(
        base_case("id range both flag groups", begin=1, end=2, flags=0x0F,
                  ids=(0x21, -1, -1, 0x22))
    )
    cases.append(
        base_case("id range full flags word", begin=1, end=1, flags=0xFFFFFFFF,
                  ids=(0x31, -1, -1, -1))
    )
    cases.append(
        base_case("id range extra zero", begin=1, end=2, flags=0x0F, extra=0,
                  ids=(0x41, -1, -1, -1))
    )
    cases.append(
        base_case("id range odd stream and selector", begin=1, end=1,
                  flags=0x0F, stream=0xDEADBEEF, selector=0xFFFFFFFF,
                  ids=(0x61, -1, -1, -1))
    )

    # --- id-range form: helper failures stop the walk immediately
    cases.append(
        base_case("id range pre-pass fails first", begin=0, end=3, flags=1,
                  prepass_results=[0])
    )
    cases.append(
        base_case("id range pre-pass fails second", begin=0, end=3, flags=1,
                  prepass_results=[1, 0])
    )
    cases.append(
        base_case("id range record load fails first", begin=0, end=3, flags=8,
                  record_results=[0])
    )
    cases.append(
        base_case("id range record load fails second", begin=0, end=3, flags=8,
                  record_results=[1, 0], ids=(0x71, -1, -1, -1))
    )
    cases.append(
        base_case("id range id writer fails first", begin=0, end=3, flags=8,
                  ids=(0x81, 0x82, -1, -1), id_results=[0])
    )
    cases.append(
        base_case("id range id writer fails third", begin=0, end=3, flags=8,
                  ids=(0x83, 0x84, 0x85, -1), id_results=[1, 1, 0])
    )
    cases.append(
        base_case("id range maximum indices with early failure",
                  begin=0xFFFFFFFE, end=0xFFFFFFFF, flags=8,
                  ids=(0x91, -1, -1, -1), id_results=[0])
    )
    cases.append(
        base_case("id range maximum indices fails on wrap step",
                  begin=0xFFFFFFFD, end=0xFFFFFFFF, flags=8,
                  ids=(0x92, -1, -1, -1), id_results=[1, 0])
    )
    cases.append(
        base_case("id range writer fails after full success", begin=0, end=1,
                  flags=0x0C, ids=(0xA1, -1, -1, -1), id_results=[1, 0])
    )

    # --- id-range form: self->context is re-read before each helper call
    cases.append(
        base_case("id range context rewritten mid-walk", begin=0, end=1,
                  flags=0x0F, ids=(0xB1, -1, -1, -1), mutate_context_at=2,
                  new_context=CTX2_ADDR)
    )
    cases.append(
        base_case("id range context rewritten before records", begin=0, end=1,
                  flags=0x08, ids=(0xB2, -1, -1, -1), mutate_context_at=1,
                  new_context=CTX2_ADDR)
    )

    # --- forwarded form (kind 3)
    cases.append(
        base_case("forward single index", begin=9, end=9, kind=3, flags=0)
    )
    cases.append(
        base_case("forward three indices", begin=1, end=3, kind=3, flags=0xFF)
    )
    cases.append(
        base_case("forward end < begin", begin=4, end=3, kind=3)
    )
    cases.append(
        base_case("forward unsigned boundary", begin=0x7FFFFFFF, end=0x80000000,
                  kind=3)
    )
    cases.append(
        base_case("forward zero and sentinel arguments", begin=0, end=0, kind=3,
                  extra=0, selector=0xFFFFFFFF, stream=0xDEADBEEF)
    )
    cases.append(
        base_case("forward maximum indices with early failure",
                  begin=0xFFFFFFFE, end=0xFFFFFFFF, kind=3,
                  forward_results=[1, 0])
    )
    cases.append(
        base_case("forward fails second", begin=0, end=3, kind=3,
                  forward_results=[1, 0])
    )
    cases.append(
        base_case("forward fails third", begin=0, end=3, kind=3,
                  forward_results=[1, 1, 0])
    )

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    orig_runner = Runner()
    cand_runner = Runner()
    passed = 0
    for case in cases:
        orig = orig_runner.run(orig_code, case)
        cand = cand_runner.run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls, "
              f"ret {orig['ret']})")
    return passed


def main() -> None:
    print("Testing engine_func_0013056c (0x0013056c)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        f"(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("prepass_flag", "constexpr u32 kPrePassFlag = 0x01;",
         "constexpr u32 kPrePassFlag = 0x02;"),
        ("record_flag_mask", "constexpr u32 kRecordFlags = 0x0C;",
         "constexpr u32 kRecordFlags = 0x08;"),
        ("empty_id", "constexpr u32 kEmptyId = 0xFFFFFFFFu;",
         "constexpr u32 kEmptyId = 0xFFFFFFFEu;"),
        ("id_slot_count",
         "                for (u32 slot = 0; slot < kIdSlotCount; ++slot) {\n"
         "                    const u32 id = candidates.ids[slot];",
         "                for (u32 slot = 0; slot < kIdSlotCount - 1; ++slot) {\n"
         "                    const u32 id = candidates.ids[slot];"),
        ("prepass_mode", "if (pre_pass(self, key, stream, extra, 0) == 0) {",
         "if (pre_pass(self, key, stream, extra, 1) == 0) {"),
        ("forward_selector",
         "if (forward(self, index, stream, flags, extra, selector) == 0) {",
         "if (forward(self, index, stream, flags, extra, flags) == 0) {"),
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
