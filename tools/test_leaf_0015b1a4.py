#!/usr/bin/env python3
"""Differential test for func_0015b1a4 (0x0015b1a4) using Unicorn ARM.

Compiles src/engine/leaf_batch28_a.cpp, extracts the func_0015b1a4 body,
resolves its direct call to the 0x002A1A08 copy helper and its
g_GpuCommandCursor reference, then runs the pinned original
(extracted/exefs/code.bin) and the candidate on separate Unicorn machines with
identical fixtures.

Compared outputs per case:
  * continuation PC, final SP and the callee-saved r4-r11 values;
  * the ordered call log with every helper argument: the destination pointer,
    the (stack-normalised) source pointer and the four source words read from
    it, plus every indirect vtable-slot call with its receiver;
  * the full observable data region (fixtures, matrices, command buffer and the
    cursor global) and a check that no write escapes the command buffer, the
    cursor global or the private stack frame;
  * an independent model of the emitted headers, block payloads, transformed
    matrix payload and final cursor.

VFP is enabled through CPACR/FPEXC. The original VFP sequence is unfused
(vmul/vmla with separate rounding, matching the candidate's vmul/vadd), so the
command-stream payload words are compared bit for bit.

Coverage: node pointer null and non-null, the render-gate bit cleared and set
with unrelated bits, entry-flag bit 1 cleared/set, node+0x0C zero/non-zero,
vtable slot 0x14 not called / called, a vtable callee that rewrites the scale
triple and the raw fourth word (tests the post-call reload), signed-zero and
denormal VFP boundaries, non-finite operands, raw 0xE4 word patterns, and
non-zero initial cursors. Negative controls mutate the record marker, the
render-gate bit, the matrix-2 offset and the scale offset; each mutant must be
detected.
"""

from __future__ import annotations

import math
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
OUT_DIR = ROOT / "build/test_leaf_0015b1a4"

FUNC_ADDR = 0x0015B1A4
FUNC_SIZE = 408

# ---------------------------------------------------------------------------
# Emulated address space
# ---------------------------------------------------------------------------
CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000          # covers 0x15B1A4 and the stubs at 0x2A1A08/0x2A1B00
DATA_ADDR = 0x00400000
DATA_SIZE = 0x00080000          # fixtures, command buffer and cursor global
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

# Direct-call / indirect-call stubs.
STUB_COPY = 0x002A1A08
STUB_VTABLE = 0x002A1B00
BX_LR = 0xE12FFF1E

# Fixture placement inside DATA.
OBJECT = 0x00400000
STATE = 0x00400100
FLAGS = 0x00400200
NODE = 0x00400300
VTABLE = 0x00400400
ENTRY = 0x00400500
MATRIX_OWNER = 0x00400600
MATRIX_ONE = 0x00401000
CMD_BUFFER = 0x00404000
CMD_BUFFER_SIZE = 0x00004000
CURSOR_GLOBAL = 0x004652A0

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

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
VFP_SCRATCH_START = {
    "s0": 0x3F800000,
    "s1": 0xBF800000,
    "s2": 0x40000000,
    "s3": 0xC0000000,
    "s4": 0x3F000000,
    "s5": 0xBF000000,
    "s6": 0x40400000,
    "s7": 0xC0400000,
    "s8": 0x40800000,
    "s9": 0xC0800000,
    "s10": 0x40A00000,
    "s11": 0xC0A00000,
    "s12": 0x40C00000,
    "s13": 0xC0C00000,
    "s14": 0x40E00000,
    "s15": 0xC0E00000,
}

GLOBAL_CURSOR_SYMBOL = "g_GpuCommandCursor"
COPY_HELPER_SYMBOL = "func_002a1a08"

F32_MAX = 3.4028234663852886e38
F32_OVERFLOW = 3.402823669209385e38  # midpoint between FLT_MAX and 2**128

DEFAULT_MATRIX_ONE = (
    1.0, 0.5, 0.25, 99.0,
    2.0, -1.0, 0.125, 98.0,
    -2.0, 4.0, 0.5, 97.0,
    7.0, 8.0, 9.0, 96.0,
)
DEFAULT_MATRIX_TWO = (
    0.5, 2.0, -1.5, 95.0,
    3.0, 0.25, 0.5, 94.0,
    -4.0, 1.5, 2.0, 93.0,
    6.0, 5.0, 4.0, 92.0,
)
DEFAULT_BLOCK_B8 = (0x11223344, 0x55667788, 0x99AABBCC, 0xDDEEFF00)
DEFAULT_BLOCK_C8 = (0x01020304, 0x05060708, 0x090A0B0C, 0x0D0E0F10)


# ---------------------------------------------------------------------------
# Candidate preparation
# ---------------------------------------------------------------------------
def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def compile_candidate(src: Path, obj: Path) -> bytes:
    obj.parent.mkdir(parents=True, exist_ok=True)
    result = compile_tu_armv6k(src, obj, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"compilation failed for {src}:\n{result.stderr}")

    funcs = extract_elf_functions_detailed(obj)
    if "func_0015b1a4" not in funcs:
        raise RuntimeError(
            f"func_0015b1a4 not found in {obj}: {sorted(funcs)}"
        )
    raw, relocs = funcs["func_0015b1a4"]
    code = bytearray(raw)

    for rel in relocs:
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            if rel.symbol_name != COPY_HELPER_SYMBOL:
                raise RuntimeError(f"unexpected call relocation: {rel}")
            instruction = struct.unpack_from("<I", code, rel.offset)[0]
            pc = FUNC_ADDR + rel.offset + 8
            displacement = (STUB_COPY - pc) >> 2
            struct.pack_into(
                "<I",
                code,
                rel.offset,
                (instruction & 0xFF000000) | (displacement & 0x00FFFFFF),
            )
        elif rel.relocation_type == 2:  # R_ARM_ABS32
            if rel.symbol_name != GLOBAL_CURSOR_SYMBOL:
                raise RuntimeError(f"unexpected abs32 relocation: {rel}")
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            if addend != 0:
                raise RuntimeError(
                    f"unexpected {GLOBAL_CURSOR_SYMBOL} addend 0x{addend:08x}"
                )
            struct.pack_into("<I", code, rel.offset, CURSOR_GLOBAL)
        else:
            raise RuntimeError(f"unsupported relocation: {rel}")
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    return compile_candidate(SOURCE, OUT_DIR / "leaf_batch28_a.o")


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant = OUT_DIR / f"mutant_{name}.cpp"
    mutant.write_text(text.replace(old, new), encoding="utf-8")
    return compile_candidate(mutant, OUT_DIR / f"mutant_{name}.o")


# ---------------------------------------------------------------------------
# Float helpers (single precision, no fused operations)
# ---------------------------------------------------------------------------
def f32(value: float) -> float:
    """Round a double to single precision, overflowing to infinity like VFP."""
    if value != value:
        return value
    if value >= F32_OVERFLOW:
        return float("inf")
    if value <= -F32_OVERFLOW:
        return float("-inf")
    try:
        return struct.unpack("<f", struct.pack("<f", value))[0]
    except OverflowError:  # pragma: no cover - just below the overflow gate
        return math.copysign(F32_MAX, value)


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def dot3(matrix, i0: int, i1: int, i2: int, a: float, b: float, c: float) -> float:
    """matrix[i0]*a + matrix[i1]*b + matrix[i2]*c with single rounding."""
    partial = f32(f32(matrix[i0] * a) + f32(matrix[i1] * b))
    return f32(partial + f32(matrix[i2] * c))


# ---------------------------------------------------------------------------
# Machine
# ---------------------------------------------------------------------------
class Machine:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        # Enable CP10/CP11 access and the VFP unit.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        bx_lr = struct.pack("<I", BX_LR)
        for address, hook in (
            (STUB_COPY, self._on_copy),
            (STUB_VTABLE, self._on_vtable),
        ):
            self.uc.mem_write(address, bx_lr)
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, hook, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.outside_stack_writes: list = []
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    @staticmethod
    def _normalise(pointer: int):
        if STACK_ADDR <= pointer < STACK_ADDR + STACK_SIZE:
            return "<stack>"
        return pointer

    def _on_copy(self, uc, address: int, size: int, user_data) -> None:
        dst = uc.reg_read(arm.UC_ARM_REG_R0)
        src = uc.reg_read(arm.UC_ARM_REG_R1)
        words = struct.unpack("<4I", uc.mem_read(src, 16))
        self.call_log.append(
            ("func_002a1a08", dst, self._normalise(src)) + words
        )
        # Exact body of 0x002A1A08: 4 words stored in reverse order.
        uc.mem_write(dst, struct.pack("<4I", words[3], words[2], words[1], words[0]))

    def _on_vtable(self, uc, address: int, size: int, user_data) -> None:
        receiver = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(("vtable_14", receiver))
        mutate = self.case.get("vtable_mutate")
        if mutate is not None:
            a, b, c, raw = mutate
            write_f32(uc, ENTRY + 0xD8, a)
            write_f32(uc, ENTRY + 0xDC, b)
            write_f32(uc, ENTRY + 0xE0, c)
            write_u32(uc, ENTRY + 0xE4, raw)
        uc.reg_write(arm.UC_ARM_REG_R0, MATRIX_ONE)

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE):
            self.outside_stack_writes.append(address)

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        uc = self.uc
        self.call_log = []
        self.outside_stack_writes = []
        self.case = case

        # Wipe everything the case can observe, then install fixtures.
        uc.mem_write(DATA_ADDR, b"\x00" * DATA_SIZE)
        uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        uc.mem_write(FUNC_ADDR, code)
        uc.mem_write(CMD_BUFFER, b"\xCC" * CMD_BUFFER_SIZE)
        # Unicorn 2.1.4 keeps translated blocks across mem_write; drop them.
        uc.ctl_flush_tb()

        write_u32(uc, OBJECT + 0x08, STATE)
        write_u32(uc, OBJECT + 0x44, NODE if case["node_present"] else 0)
        write_u32(uc, OBJECT + 0xA4, MATRIX_OWNER)
        write_u32(uc, STATE + 0x08, FLAGS)
        write_u32(uc, FLAGS, case["gate_flags"])

        write_u32(uc, NODE + 0x00, VTABLE)
        write_u32(uc, NODE + 0x08, ENTRY)
        write_u32(uc, NODE + 0x0C, case["node_field0c"])
        write_u32(uc, VTABLE + 0x14, STUB_VTABLE)

        write_u32(uc, ENTRY + 0x18, case["entry_flags18"])
        write_words(uc, ENTRY + 0xB8, case["block_b8"])
        write_words(uc, ENTRY + 0xC8, case["block_c8"])
        a, b, c = case["scale"]
        write_f32(uc, ENTRY + 0xD8, a)
        write_f32(uc, ENTRY + 0xDC, b)
        write_f32(uc, ENTRY + 0xE0, c)
        write_u32(uc, ENTRY + 0xE4, case["entry_raw_e4"])

        write_floats(uc, MATRIX_ONE, case["matrix_one"])
        write_floats(uc, MATRIX_OWNER + 0x148, case["matrix_two"])

        write_u32(uc, CURSOR_GLOBAL, case["cursor"])

        uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R0, OBJECT)
        uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            uc.reg_write(CALLEE_SAVED[name], value)
        for name, bits in VFP_SCRATCH_START.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), bits)

        try:
            uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        return {
            "ret": uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "data": bytes(uc.mem_read(DATA_ADDR, DATA_SIZE)),
            "cursor": read_u32(uc, CURSOR_GLOBAL),
            "outside_stack_writes": list(self.outside_stack_writes),
        }


def write_u32(uc, address: int, value: int) -> None:
    uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))


def read_u32(uc, address: int) -> int:
    return struct.unpack("<I", uc.mem_read(address, 4))[0]


def write_words(uc, address: int, words) -> None:
    uc.mem_write(address, struct.pack("<4I", *words))


def write_f32(uc, address: int, value: float) -> None:
    uc.mem_write(address, struct.pack("<f", value))


def write_floats(uc, address: int, values) -> None:
    uc.mem_write(address, struct.pack("<16f", *values))


def read_word(blob: bytes, virt: int) -> int:
    return struct.unpack_from("<I", blob, virt - DATA_ADDR)[0]


def read_bytes(blob: bytes, virt: int, size: int) -> bytes:
    return blob[virt - DATA_ADDR : virt - DATA_ADDR + size]


# ---------------------------------------------------------------------------
# Independent model
# ---------------------------------------------------------------------------
def gate_passes(case: dict) -> bool:
    return case["node_present"] and (case["gate_flags"] & 4) != 0


def vtable_called(case: dict) -> bool:
    return (
        gate_passes(case)
        and (case["entry_flags18"] & 2) != 0
        and case["node_field0c"] != 0
    )


def model_records(case: dict):
    """Return ((header0, header1, payload_words), ...) or None if gated."""
    if not gate_passes(case):
        return None

    called = vtable_called(case)
    a, b, c = case["scale"]
    raw_e4 = case["entry_raw_e4"]
    if called and case.get("vtable_mutate") is not None:
        a, b, c, raw_e4 = case["vtable_mutate"]

    if called:
        m = case["matrix_one"]
        x = dot3(m, 0, 1, 2, f32(a), f32(b), f32(c))
        y = dot3(m, 4, 5, 6, f32(a), f32(b), f32(c))
        z = dot3(m, 8, 9, 10, f32(a), f32(b), f32(c))
    else:
        x, y, z = f32(a), f32(b), f32(c)

    n = case["matrix_two"]
    p0 = dot3(n, 0, 1, 2, x, y, z)
    p1 = dot3(n, 4, 5, 6, x, y, z)
    p2 = dot3(n, 8, 9, 10, x, y, z)
    p3 = raw_e4

    b8 = case["block_b8"]
    c8 = case["block_c8"]
    third_payload = None
    if not case.get("skip_model_payload"):
        third_payload = (
            p3 & 0xFFFFFFFF,
            f32_bits(p2),
            f32_bits(p1),
            f32_bits(p0),
        )
    records = (
        (0x80000016, 0x804F02C0, (b8[3], b8[2], b8[1], b8[0])),
        (0x80000017, 0x804F02C0, (c8[3], c8[2], c8[1], c8[0])),
        (0x80000018, 0x804F02C0, third_payload),
    )
    return records, p3 & 0xFFFFFFFF


def check_expectations(case: dict, result: dict) -> None:
    name = case["name"]
    assert result["pc"] == TRAP_ADDR, f"did not return to LR on {name}"
    assert result["ret"] == expected_incidental_r0(case), (
        f"original scratch r0 on {name}: 0x{result['ret']:08x}"
    )
    assert result["sp"] == ENTRY_SP, f"SP not restored on {name}"
    assert result["callee_saved"] == CALLEE_SAVED_START, (
        f"callee-saved registers clobbered on {name}"
    )

    allowed = {CURSOR_GLOBAL}
    for offset in range(0, 0x48, 4):
        allowed.add(case["cursor"] + offset)
    stray = [
        address
        for address in result["outside_stack_writes"]
        if address not in allowed
        and not (CMD_BUFFER <= address < CMD_BUFFER + CMD_BUFFER_SIZE)
    ]
    assert not stray, f"unexpected writes on {name}: {stray}"

    model = model_records(case)
    blob = result["data"]
    if model is None:
        assert result["cursor"] == case["cursor"], f"cursor moved on gated {name}"
        assert read_bytes(blob, CMD_BUFFER, CMD_BUFFER_SIZE) == (
            b"\xCC" * CMD_BUFFER_SIZE
        ), f"command buffer touched on gated {name}"
        assert result["call_log"] == [], f"calls on gated {name}"
        return
    records, raw_e4 = model

    assert result["cursor"] == case["cursor"] + 0x48, (
        f"cursor on {name}: 0x{result['cursor']:08x}"
    )
    assert len(result["call_log"]) == len(records) + (1 if vtable_called(case) else 0), (
        f"call count on {name}: {result['call_log']}"
    )

    for index, (header0, header1, payload) in enumerate(records):
        base = case["cursor"] + index * 0x18
        assert read_word(blob, base) == header0, f"header0 of record {index} on {name}"
        assert read_word(blob, base + 4) == header1, (
            f"header1 of record {index} on {name}"
        )
        if payload is None:
            # Non-finite operands: NaN payload bits are implementation-defined,
            # so only the verbatim 0xE4 word is modelled independently.
            assert read_word(blob, base + 8) == raw_e4, (
                f"raw fourth word of record {index} on {name}"
            )
            continue
        got = read_bytes(blob, base + 8, 16)
        want = struct.pack("<4I", *payload)
        assert got == want, (
            f"payload of record {index} on {name}: "
            f"{got.hex()} != {want.hex()}"
        )


def expected_incidental_r0(case: dict) -> int:
    """r0 on return; the void ABI leaves a scratch value on the gate path."""
    if not case["node_present"]:
        return OBJECT
    if not gate_passes(case):
        return 4                     # leftover of `bics r0, #4, flags`
    return case["cursor"] + 0x48     # final command-stream cursor


def compare(orig: dict, cand: dict, case: dict) -> list[str]:
    problems = []
    for key in ("pc", "sp", "callee_saved", "call_log", "cursor"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    # A void function's r0 is scratch on the gate-failure early return: the
    # original leaves the 4 returned by `bics` while the candidate leaves the
    # loaded flag byte. Elsewhere the value is reproduced and compared.
    gate_failed_by_flags = case["node_present"] and not gate_passes(case)
    if not gate_failed_by_flags and orig["ret"] != cand["ret"]:
        problems.append(f"ret:\n    orig=0x{orig['ret']:08x}\n    cand=0x{cand['ret']:08x}")
    if orig["data"] != cand["data"]:
        index = next(
            i for i in range(0, len(orig["data"]), 4)
            if orig["data"][i : i + 4] != cand["data"][i : i + 4]
        )
        problems.append(
            "data differs first at 0x"
            f"{DATA_ADDR + index:08x}: "
            f"orig={orig['data'][index:index + 4].hex()} "
            f"cand={cand['data'][index:index + 4].hex()}"
        )
    return problems


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------
def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "node_present": True,
        "gate_flags": 0x00000004,
        "entry_flags18": 0x00000002,
        "node_field0c": 0x00000001,
        "vtable_mutate": None,
        "scale": (1.5, 2.0, -0.5),
        "entry_raw_e4": 0xDEADBEEF,
        "matrix_one": DEFAULT_MATRIX_ONE,
        "matrix_two": DEFAULT_MATRIX_TWO,
        "block_b8": DEFAULT_BLOCK_B8,
        "block_c8": DEFAULT_BLOCK_C8,
        "cursor": CMD_BUFFER,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- render gate -------------------------------------------------------
    cases.append(base_case("gate: node pointer null", node_present=False))
    cases.append(base_case("gate: render flags zero", gate_flags=0x00000000))
    cases.append(
        base_case("gate: bit 2 clear, every other bit set", gate_flags=0xFFFFFFFB)
    )
    cases.append(
        base_case("gate: bit 2 set with unrelated high bits", gate_flags=0xFFFFFFF4)
    )
    cases.append(base_case("gate: bit 2 set alone", gate_flags=0x00000004))

    # --- entry-flag bit 1 and node+0x0C -----------------------------------
    cases.append(
        base_case(
            "entry bit 1 clear, node field non-zero",
            entry_flags18=0x00000000,
            node_field0c=5,
        )
    )
    cases.append(
        base_case(
            "entry bit 1 set, node field zero",
            entry_flags18=0x00000002,
            node_field0c=0,
        )
    )
    cases.append(
        base_case(
            "entry flags bit 0 only, node field non-zero",
            entry_flags18=0x00000001,
            node_field0c=1,
        )
    )
    cases.append(
        base_case(
            "entry flags all bits set",
            entry_flags18=0xFFFFFFFF,
            node_field0c=1,
        )
    )
    cases.append(
        base_case(
            "node field all bits set",
            node_field0c=0xFFFFFFFF,
        )
    )
    cases.append(
        base_case(
            "node field high bit only",
            node_field0c=0x80000000,
        )
    )
    cases.append(
        base_case(
            "entry flags bit 1 plus unrelated bits",
            entry_flags18=0xFFFFFFFE,
        )
    )

    # --- vtable callee rewrites the scale triple (post-call reload) --------
    cases.append(
        base_case(
            "vtable rewrites scale and raw word",
            vtable_mutate=(5.0, 6.0, 7.0, 0xCAFEBABE),
        )
    )
    cases.append(
        base_case(
            "vtable mutation supplied but entry bit 1 clear",
            entry_flags18=0x00000000,
            vtable_mutate=(5.0, 6.0, 7.0, 0xCAFEBABE),
        )
    )
    cases.append(
        base_case(
            "vtable mutation supplied but node field zero",
            node_field0c=0,
            vtable_mutate=(5.0, 6.0, 7.0, 0xCAFEBABE),
        )
    )

    # --- VFP boundaries ---------------------------------------------------
    cases.append(
        base_case("vfp: all-zero scale", scale=(0.0, 0.0, 0.0))
    )
    cases.append(
        base_case("vfp: signed-zero scale", scale=(-0.0, 0.0, -0.0))
    )
    cases.append(
        base_case(
            "vfp: powers-of-two matrices",
            matrix_one=(0.5, 2.0, -4.0, 0.0, 1.5, -2.5, 8.0, 0.0,
                        16.0, 0.25, -0.5, 0.0, 0.0, 0.0, 0.0, 0.0),
            matrix_two=(2.0, -0.5, 0.25, 0.0, -8.0, 4.0, 0.125, 0.0,
                        0.5, -16.0, 3.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            scale=(3.0, -2.0, 0.5),
        )
    )
    cases.append(
        base_case(
            "vfp: denormal products",
            scale=(1e-40, -3e-41, 2e-39),
            matrix_one=(1e-38, 2e-39, -1e-40, 0.0, 5e-38, -2e-38, 4e-40,
                        0.0, 1e-39, 3e-38, -5e-39, 0.0,
                        0.0, 0.0, 0.0, 0.0),
            matrix_two=(2e-38, -1e-39, 3e-40, 0.0, 4e-39, 2e-38, -2e-39,
                        0.0, 5e-40, 1e-38, -3e-38, 0.0,
                        0.0, 0.0, 0.0, 0.0),
        )
    )
    cases.append(
        base_case(
            "vfp: overflow to infinity",
            scale=(3.0e38, -3.0e38, 3.0e38),
            matrix_one=(10.0, -10.0, 10.0, 0.0, -10.0, 10.0, -10.0, 0.0,
                        10.0, 10.0, -10.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            matrix_two=(10.0, -10.0, 10.0, 0.0, -10.0, 10.0, -10.0, 0.0,
                        10.0, 10.0, -10.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            skip_model_payload=True,
        )
    )
    cases.append(
        base_case(
            "vfp: infinities and NaN operand",
            scale=(float("inf"), float("-inf"), float("nan")),
            skip_model_payload=True,
        )
    )
    cases.append(
        base_case(
            "vfp: NaN matrix rows",
            matrix_one=(float("nan"), 1.0, 2.0, 0.0, 3.0, float("-nan"), 4.0,
                        0.0, 5.0, 6.0, 7.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            skip_model_payload=True,
        )
    )

    # --- raw fourth word ---------------------------------------------------
    cases.append(base_case("raw word: all bits set", entry_raw_e4=0xFFFFFFFF))
    cases.append(base_case("raw word: NaN bit pattern", entry_raw_e4=0x7FC00001))
    cases.append(base_case("raw word: zero", entry_raw_e4=0x00000000))

    # --- copy blocks and cursor -------------------------------------------
    cases.append(
        base_case(
            "copy: distinct block words",
            block_b8=(0xA0B0C0D0, 0x10203040, 0x50607080, 0x90A0B0C0),
            block_c8=(0xDEAD0001, 0xBEEF0002, 0xCAFE0003, 0xF00D0004),
        )
    )
    cases.append(
        base_case("copy: zero block words", block_b8=(0, 0, 0, 0),
                  block_c8=(0, 0, 0, 0))
    )
    cases.append(
        base_case("cursor: non-zero offset", cursor=CMD_BUFFER + 0x400)
    )
    cases.append(
        base_case("cursor: near buffer end", cursor=CMD_BUFFER + 0x3F00)
    )
    cases.append(
        base_case(
            "combined: vtable transform at offset cursor",
            cursor=CMD_BUFFER + 0x800,
            entry_flags18=0xFFFFFFFF,
            node_field0c=0x80000000,
            scale=(-1.0, 0.0, 2.5),
        )
    )

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = Machine().run(orig_code, case)
        cand = Machine().run(cand_code, case)
        problems = compare(orig, cand, case)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        check_expectations(case, orig)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing func_0015b1a4 (0x0015b1a4)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(f"  original: {len(orig_code)} B, candidate: {len(cand_code)} B")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        (
            "record_marker",
            "constexpr u32 kGpuHeaderMarker = 0x804f02c0u;",
            "constexpr u32 kGpuHeaderMarker = 0x804f02c1u;",
        ),
        (
            "render_gate_bit",
            "constexpr u32 kRenderGateBit   = 4u;",
            "constexpr u32 kRenderGateBit   = 8u;",
        ),
        (
            "matrix_two_offset",
            "const u8* const m = matrix_set + 0x148;",
            "const u8* const m = matrix_set + 0x14c;",
        ),
        (
            "scale_offset",
            "f32 x = LoadF32(entry, 0xd8);",
            "f32 x = LoadF32(entry, 0xdc);",
        ),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Machine().run(orig_code, case)
            bad = Machine().run(mutant_code, case)
            if compare(orig, bad, case):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
