#!/usr/bin/env python3
"""Differential test for camp_func_00195044 (0x00195044) using Unicorn ARM.

Compiles src/engine/leaf_batch45_b.cpp, extracts the camp_func_00195044 body,
resolves its direct calls to deterministic stubs, and runs the pinned original
(extracted/exefs/code.bin) against the candidate in separate Unicorn machines
with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log with every register argument, the five architected
    stack arguments of 0x0029F878, and the pre-call value of its out flag;
  * the multiset of non-stack writes (address, width, value), order independent
    because the compiler may schedule independent field stores differently;
  * the full play-log workspace (0x488 bytes plus a sentinel guard), the TBB
    payload, the layout node buffer and the global pointer word.

Coverage: state 0/1/2/other, signed frame-counter bounds (zero, 4, 5, negative,
0x7FFFFFFF, 0x80000000, wrap), the sprite enable byte, the three touch
registrations and the 16-bit counter wrap, the visible-row loop bounds
(index >= row count, negative index, rows == 0, null payload, positive and
negative keys, multiple negative keys), the 0x0029F878 hit/changed and
hit/unchanged paths, the 0x0029F278 poll with <=5 and >5 row counts, the (0,0)
and bottom-right exits, poll-driven cursor movement, the select gate both
values, and the sprite-step enable byte.

Negative controls mutate the changed-dispatch id, the sprite enable offset and
the 0x0029F878 argument order; each mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_00195044"

FUNC_ADDR = 0x00195044
FUNC_SIZE = 868

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # function at 0x195044 plus every stub below 0x2C1830
DATA_ADDR = 0x00430000
DATA_SIZE = 0x00020000  # covers 0x0043DD08
WORK_ADDR = 0x00500000
WORK_SIZE = 0x00010000
TABLE_ADDR = 0x00700000
PAYLOAD_ADDR = 0x00710000
PAYLOAD_SIZE = 0x00010000
NODE_ADDR = 0x00720000
NODE_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100
GLOBAL_WORK = 0x0043DD08
WORK_BYTES = 0x488
WORK_COMPARE = 0x600

# Original direct-call targets; stubs are placed at the same addresses so both
# the original bytes and the relocated candidate resolve to them.
STUB_2B9220 = 0x002B9220
STUB_2B88C4 = 0x002B88C4
STUB_29F0F4 = 0x0029F0F4
STUB_2C0EC4 = 0x002C0EC4
STUB_2C0E9C = 0x002C0E9C
STUB_2C0E4C = 0x002C0E4C
STUB_290A4C = 0x00290A4C
STUB_2BF6D0 = 0x002BF6D0
STUB_29F878 = 0x0029F878
STUB_29F260 = 0x0029F260
STUB_29F248 = 0x0029F248
STUB_29F278 = 0x0029F278
STUB_2BC200 = 0x002BC200
STUB_2C1830 = 0x002C1830
STUB_2BDAC0 = 0x002BDAC0
STUB_2BF9F0 = 0x002BF9F0

STUB_NAMES = {
    STUB_2B9220: "camp_func_002b9220",
    STUB_2B88C4: "camp_func_002b88c4",
    STUB_29F0F4: "camp_func_0029f0f4",
    STUB_2C0EC4: "Tbb_GetGlobalSubTable",
    STUB_2C0E9C: "Tbb_GetPayloadData",
    STUB_2C0E4C: "Tbb_GetRowCount",
    STUB_290A4C: "camp_func_00290a4c",
    STUB_2BF6D0: "camp_func_002bf6d0",
    STUB_29F878: "camp_func_0029f878",
    STUB_29F260: "camp_func_0029f260",
    STUB_29F248: "camp_func_0029f248",
    STUB_29F278: "camp_func_0029f278",
    STUB_2BC200: "camp_func_002bc200",
    STUB_2C1830: "camp_func_002c1830",
    STUB_2BDAC0: "camp_func_002bdac0",
    STUB_2BF9F0: "ui_func_002bf9f0",
}

# Number of architected stack words each helper receives.
STACK_ARGS = {
    STUB_29F878: 5,  # a4, a5, out flag pointer, 0, 0
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

MASK32 = 0xFFFFFFFF


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "00195044" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"camp_func_00195044 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type != 28:  # R_ARM_CALL
            raise RuntimeError(
                f"unexpected relocation type {rel.relocation_type} "
                f"for {rel.symbol_name} at {rel.offset}"
            )
        target = None
        for address, name in STUB_NAMES.items():
            if name in rel.symbol_name or f"{address:08x}" in rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        condition = original & 0xFF000000
        struct.pack_into(
            "<I", code, rel.offset, condition | (displacement & 0x00FFFFFF)
        )
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_b.o"
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
def build_work(case: dict) -> bytes:
    work = bytearray(WORK_SIZE)
    # Deterministic sentinel pattern everywhere, then explicit fields.
    for index in range(0, WORK_SIZE, 4):
        struct.pack_into("<I", work, index, 0xA5A50000 | index)

    state = case.get("state", 1) & MASK32
    frame = case.get("frame", 0) & MASK32
    count = case.get("touch_count", 0x0010) & 0xFFFF
    handles = case.get("handles", (0x0100, 0x0101, 0x0102))
    visible = case.get("visible", ())

    work[0x2DA] = case.get("enable", 0) & 0xFF
    struct.pack_into("<I", work, 0x340, frame)
    struct.pack_into("<I", work, 0x344, state)
    struct.pack_into("<h", work, 0x348, _s16(handles[0]))
    struct.pack_into("<h", work, 0x34A, _s16(handles[1]))
    struct.pack_into("<h", work, 0x34C, _s16(handles[2]))
    struct.pack_into("<H", work, 0x358, count)

    for index, value in enumerate(visible):
        struct.pack_into("<H", work, 0x424 + index * 2, value & 0xFFFF)
    for index in range(50):
        struct.pack_into("<I", work, 0x35C + index * 4, 0xC0DE0000 | index)
    return bytes(work)


def _s16(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def build_payload(case: dict) -> bytes:
    payload = bytearray(PAYLOAD_SIZE)
    payload[:] = b"\xA5" * PAYLOAD_SIZE
    keys = case.get("keys", {})
    for index in range(8):
        key = keys.get(index, 0x0011 + index)
        struct.pack_into("<h", payload, index * 0x40, _s16(key))
    return bytes(payload)


def read_c_string(uc, address: int, limit: int = 32) -> bytes:  # unused helper
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
        self.uc.mem_map(TABLE_ADDR, 0x1000)
        self.uc.mem_map(PAYLOAD_ADDR, PAYLOAD_SIZE)
        self.uc.mem_map(NODE_ADDR, NODE_SIZE)
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
        self.indices: dict = {}
        self.exhausted: list = []

    # ------------------------------------------------------------- script state
    def _next(self, key: str, default: int = 0) -> int:
        script = self.case.get(key)
        if script is None:
            return default
        index = self.indices.get(key, 0)
        if index >= len(script):
            # A one-value script is a constant; longer scripts are exact
            # sequences and must not be over-consumed.
            if len(script) != 1:
                self.exhausted.append((key, index, len(script)))
            return script[-1] if script else default
        self.indices[key] = index + 1
        return script[index]

    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        raw = self.uc.mem_read(sp, 4 * count)
        return struct.unpack(f"<{count}I", raw)

    def _log(self, address: int, *args) -> None:
        self.call_log.append(
            (STUB_NAMES[address], args + self._stack_words(STACK_ARGS.get(address, 0)))
        )

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value & MASK32))

    # ------------------------------------------------------------------ stubs
    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_2B9220:
            self._log(address, r0, r1)
        elif address == STUB_2B88C4:
            self._log(address, r0, r1)
            handles = self.case.get("handle_returns", {})
            uc.reg_write(arm.UC_ARM_REG_R0, handles.get(r1, 0x1000 + r1) & MASK32)
        elif address == STUB_29F0F4:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self._next("f0f4", 0) & MASK32)
        elif address == STUB_2C0EC4:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, TABLE_ADDR)
        elif address == STUB_2C0E9C:
            self._log(address, r0)
            value = 0 if self.case.get("payload_null") else PAYLOAD_ADDR
            uc.reg_write(arm.UC_ARM_REG_R0, value)
        elif address == STUB_2C0E4C:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self._next("rows", 0) & MASK32)
        elif address == STUB_290A4C:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, self._next("counts", 0) & MASK32)
        elif address == STUB_2BF6D0:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, NODE_ADDR)
        elif address == STUB_29F878:
            sp = uc.reg_read(arm.UC_ARM_REG_SP)
            stack = struct.unpack("<IIIII", uc.mem_read(sp, 20))
            out_ptr = stack[2]
            pre_flag = uc.mem_read(out_ptr, 1)[0]
            self.call_log.append(
                (
                    STUB_NAMES[address],
                    (r0, r1, r2, r3) + stack + (pre_flag,),
                )
            )
            uc.mem_write(out_ptr, bytes([self._next("f878_flag", 0x5A) & 0xFF]))
            uc.reg_write(arm.UC_ARM_REG_R0, self._next("f878", 0) & MASK32)
        elif address == STUB_29F260:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self._next("f260", 0) & MASK32)
        elif address == STUB_29F248:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self._next("f248", 0) & MASK32)
        elif address == STUB_29F278:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, self._next("f278", 0) & MASK32)
        elif address == STUB_2BC200:
            self._log(address, r0)
        elif address == STUB_2C1830:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, self._next("gate", 0) & MASK32)
        elif address == STUB_2BDAC0:
            self._log(address, r0, r1, r2)
        elif address == STUB_2BF9F0:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self._next("step", 0) & MASK32)
        else:  # pragma: no cover
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case
        self.indices = {}
        self.exhausted = []

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(WORK_ADDR, build_work(case))
        self.uc.mem_write(PAYLOAD_ADDR, build_payload(case))
        self.uc.mem_write(NODE_ADDR, b"\x00" * NODE_SIZE)
        self.uc.mem_write(TABLE_ADDR, b"\x00" * 0x1000)
        self.uc.mem_write(DATA_ADDR, b"\x00" * DATA_SIZE)
        self.uc.mem_write(GLOBAL_WORK, struct.pack("<I", WORK_ADDR))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, 0x00000000)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        self.writes = []
        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error
        if self.uc.reg_read(arm.UC_ARM_REG_PC) != TRAP_ADDR:
            raise RuntimeError("candidate did not return to the trap address")

        non_stack_writes = [
            (address, size, value)
            for address, size, value in self.writes
            if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
        ]
        outside_work = [
            entry for entry in non_stack_writes
            if not (WORK_ADDR <= entry[0] < WORK_ADDR + WORK_BYTES)
        ]
        if outside_work:
            raise RuntimeError(f"write outside play-log work: {outside_work}")

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self._normalise(self.call_log),
            "writes": sorted(non_stack_writes),
            "work": bytes(self.uc.mem_read(WORK_ADDR, WORK_COMPARE)),
            "payload": bytes(self.uc.mem_read(PAYLOAD_ADDR, 0x200)),
            "node": bytes(self.uc.mem_read(NODE_ADDR, 0x40)),
            "global": bytes(self.uc.mem_read(GLOBAL_WORK, 4)),
            "exhausted": list(self.exhausted),
        }

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
    if orig["writes"] != cand["writes"]:
        problems.append(
            "non-stack writes:\n    orig="
            + repr(orig["writes"])
            + "\n    cand="
            + repr(cand["writes"])
        )
    for key in ("work", "payload", "node", "global"):
        if orig[key] != cand[key]:
            problems.append(f"memory {key} differs")
    if orig["exhausted"] or cand["exhausted"]:
        problems.append(
            f"script exhausted orig={orig['exhausted']} cand={cand['exhausted']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "state": 1,
        "frame": 0,
        "enable": 0,
        "touch_count": 0x0010,
        "handles": (0x0100, 0x0101, 0x0102),
        "visible": (),
        "rows": [0],
        "counts": [0],
        "f0f4": [0],
        "f260": [0],
        "f248": [0],
        "f278": [0],
        "f878": [0],
        "f878_flag": [0x5A],
        "gate": [0],
        "step": [0],
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- state 0: sprite re-arm loop bound is the signed frame counter
    for frame in (0, 1, 3, 4, 5, 0x7FFFFFFF, 0xFFFFFFFF, 0x80000000):
        cases.append(base_case(f"state 0 frame 0x{frame:08x}", state=0,
                               frame=frame))
    for frame, enable, count in (
        (4, 1, 0x0000),
        (5, 1, 0xFFFE),
        (0xFFFFFFFF, 1, 0xFFFF),
        (0x80000000, 1, 0x8001),
        (4, 0xFF, 0x0002),
    ):
        cases.append(
            base_case(
                f"state 0 frame 0x{frame:08x} enable {enable} count 0x{count:04x}",
                state=0,
                frame=frame,
                enable=enable,
                touch_count=count,
                handles=(0x12345678, 0x9ABCDEF0, 0x0000FFFF),
                handle_returns={0x1A: 0x12345678, 0x1B: 0x9ABCDEF0,
                                0x1C: 0x0000FFFF},
            )
        )

    # --- state 2: sprite steps and the enable byte
    for frame, enable in ((10, 0), (0, 1), (0xFFFFFFFF, 1),
                          (0x7FFFFFFF, 1), (0x80000000, 0)):
        cases.append(base_case(f"state 2 frame 0x{frame:08x} enable {enable}",
                               state=2, frame=frame, enable=enable))

    # --- other states: counter only
    for state in (3, 4, 0xFFFFFFFF):
        cases.append(base_case(f"state 0x{state:08x}", state=state, frame=7))

    # --- state 1 row loop bounds
    cases.append(
        base_case(
            "row loop: three rows, negative/zero/positive keys",
            visible=(0, 1, 2),
            f0f4=[3, 3, 3, 3],
            rows=[3],
            keys={0: -1, 1: 0, 2: 5},
            counts=[0x2A],
            f878=[1],
        )
    )
    cases.append(
        base_case(
            "row loop: negative and out-of-range visible indices",
            visible=(0xFFFF, 3, 0),
            f0f4=[3, 3, 3, 0],
            rows=[1],
            keys={0: -2, 3: -3},
            counts=[9],
            f878=[1],
        )
    )
    cases.append(
        base_case(
            "row loop: zero row count skips every lookup",
            visible=(0, 1),
            f0f4=[2, 2, 0],
            rows=[0],
            f878=[1],
        )
    )
    cases.append(
        base_case(
            "row loop: null payload with index 0 is not dereferenced",
            visible=(0,),
            f0f4=[1, 0],
            rows=[1],
            payload_null=True,
            f878=[1],
        )
    )
    cases.append(
        base_case(
            "row loop: positive keys only",
            visible=(0, 1),
            f0f4=[2, 2, 0],
            rows=[2],
            keys={0: 0, 1: 0x7FFF},
            f878=[1],
        )
    )
    cases.append(
        base_case(
            "row loop: 0x8000 key and dynamic row count",
            visible=(0, 1, 2),
            f0f4=[2, 2, 3, 3],
            rows=[2, 3, 3],
            keys={0: -0x8000, 1: -1, 2: -5},
            counts=[1, 2, 3],
            f878=[1],
        )
    )
    cases.append(
        base_case(
            "row loop: key 0xFFFF (negative one)",
            visible=(1,),
            f0f4=[1, 0],
            rows=[2],
            keys={1: 0xFFFF},
            counts=[0xFFFFFFFF],
            f878=[1],
        )
    )

    # --- state 1, 0x0029F878 reports a hit
    cases.append(
        base_case(
            "touch hit, cursor moved",
            visible=(0,),
            f0f4=[1, 0],
            rows=[1],
            keys={0: -1},
            counts=[4],
            f878=[1],
            f260=[5, 6],
            f878_flag=[0xA5],
        )
    )
    cases.append(
        base_case(
            "touch hit, cursor unchanged",
            visible=(0,),
            f0f4=[1, 0],
            rows=[1],
            keys={0: -1},
            counts=[4],
            f878=[1],
            f260=[5, 5],
            f878_flag=[0x00],
        )
    )

    # --- state 1, settled cursor and the select gate
    cases.append(
        base_case(
            "settled cursor, gate accepts",
            visible=(0,),
            f0f4=[1, 0],
            rows=[1],
            keys={0: -1},
            counts=[4],
            f878=[0],
            f278=[0],
            gate=[1],
            f260=[5, 5],
        )
    )
    cases.append(
        base_case(
            "settled cursor, gate rejects",
            visible=(0,),
            f0f4=[1, 0],
            rows=[1],
            keys={0: -1},
            counts=[4],
            f878=[0],
            f278=[0],
            gate=[0],
            f260=[5, 5],
        )
    )

    # --- state 1, cursor poll returned non-zero
    cases.append(
        base_case(
            "poll non-zero, row count <= 5, cursor unchanged",
            visible=(0,),
            f0f4=[1, 0, 5],
            rows=[1],
            keys={0: -1},
            counts=[4],
            f878=[0],
            f278=[1],
            f260=[5, 5],
        )
    )
    cases.append(
        base_case(
            "poll non-zero, row count > 5, cursor already moved",
            visible=(0,),
            f0f4=[1, 0, 6],
            rows=[1],
            keys={0: -1},
            counts=[4],
            f878=[0],
            f278=[1],
            f260=[5, 6, 6],
        )
    )
    cases.append(
        base_case(
            "poll loop exits at (0,0)",
            visible=(0,),
            f0f4=[1, 0, 6],
            rows=[1],
            keys={0: -1},
            counts=[4],
            f878=[0],
            f278=[1],
            f260=[5, 5, 0, 5],
            f248=[0],
        )
    )
    cases.append(
        base_case(
            "poll loop repeats once via (0,1) then exits",
            visible=(0,),
            f0f4=[1, 0, 6, 6],
            rows=[1],
            keys={0: -1},
            counts=[4],
            f878=[0],
            f278=[1, 1],
            f260=[0, 0, 0, 0, 0, 0, 0],
            f248=[1, 0],
        )
    )
    cases.append(
        base_case(
            "poll loop exits at bottom-right (count-5, 4)",
            visible=(0,),
            f0f4=[1, 0, 6, 6],
            rows=[1],
            keys={0: -1},
            counts=[4],
            f878=[0],
            f278=[1],
            f260=[5, 5, 1, 1, 5],
            f248=[4],
        )
    )
    cases.append(
        base_case(
            "poll loop bottom-right with count 7",
            visible=(0,),
            f0f4=[1, 0, 7, 7],
            rows=[1],
            keys={0: -1},
            counts=[4],
            f878=[0],
            f278=[1],
            f260=[5, 5, 2, 2, 5],
            f248=[4],
        )
    )
    cases.append(
        base_case(
            "poll loop (count-5, 3) then cursor moves",
            visible=(0,),
            f0f4=[1, 0, 7, 7],
            rows=[1],
            keys={0: -1},
            counts=[4],
            f878=[0],
            f278=[1],
            f260=[5, 5, 2, 2, 7, 7],
            f248=[3],
        )
    )

    return cases


def coverage_check(case: dict, result: dict) -> None:
    """Assert the original took the intended path for this fixture."""
    name = case["name"]
    frame = case.get("frame", 0) & MASK32
    expected_ret = (frame + 1) & MASK32
    assert result["ret"] == expected_ret, (
        f"{name}: ret 0x{result['ret']:08x} != 0x{expected_ret:08x}"
    )
    assert result["sp"] == ENTRY_SP, f"{name}: SP not restored"
    assert result["callee_saved"] == CALLEE_SAVED_START, (
        f"{name}: callee-saved registers changed"
    )
    state = case.get("state", 1) & MASK32
    work = result["work"]
    final_state = struct.unpack_from("<I", work, 0x344)[0]
    if state == 0:
        if case.get("enable", 0):
            assert final_state == 1, f"{name}: expected state 1, got {final_state}"
        else:
            assert final_state == 0, f"{name}: expected state 0, got {final_state}"
    elif state == 2:
        expected = 3 if case.get("enable", 0) else 2
        assert final_state == expected, f"{name}: expected state {expected}"
    elif state == 1:
        expected = case.get("expect_state", None)
        if expected is not None:
            assert final_state == expected, (
                f"{name}: expected state {expected}, got {final_state}"
            )
    else:
        assert final_state == state, f"{name}: default state changed"


def dispatch_ids(result: dict) -> list[int]:
    return [
        args[0]
        for name, args in result["call_log"]
        if name == "camp_func_002bc200"
    ]


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = Runner().run(orig_code, case)
        cand = Runner().run(cand_code, case)
        coverage_check(case, orig)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        ids = dispatch_ids(orig)
        if "expected_dispatch" in case:
            assert ids == case["expected_dispatch"], (
                f"{case['name']}: dispatch {ids} != {case['expected_dispatch']}"
            )
        passed += 1
        print(
            f"  [PASS] {case['name']}  "
            f"({len(orig['call_log'])} calls, {len(orig['writes'])} writes, "
            f"dispatch {[hex(i) for i in ids]})"
        )
    return passed


def main() -> None:
    print("Testing camp_func_00195044 (0x00195044)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        f"(relocations resolved)."
    )

    cases = make_cases()

    # The two movement fixtures have known dispatch-id expectations.
    for case in cases:
        if case["name"] in ("touch hit, cursor moved",
                            "poll non-zero, row count > 5, cursor already moved",
                            "poll loop (count-5, 3) then cursor moves"):
            case["expected_dispatch"] = [0x0100016C]
        elif case["name"] == "settled cursor, gate accepts":
            case["expected_dispatch"] = [0x0100016E]
            case["expect_state"] = 2
        elif case["name"] == "settled cursor, gate rejects":
            case["expected_dispatch"] = []

    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("dispatch_id", "kDispatchChanged = 0x0100016Cu",
         "kDispatchChanged = 0x0100016Du"),
        ("sprite_enable_offset", "kSpriteEnableOffset = 0x8A",
         "kSpriteEnableOffset = 0x89"),
        ("touch_arg_order", "work->touch_handle_1c,\n"
         "                               work->touch_handle_1a,",
         "work->touch_handle_1a,\n"
         "                               work->touch_handle_1c,"),
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
