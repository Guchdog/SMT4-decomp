#!/usr/bin/env python3
"""Differential test for func_0015a620 (0x0015a620) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the func_0015a620 body,
resolves its tail branch to the 0x002A20A8 command-list registration helper
and its g_GpuCommandCursor reference (0x004652A0), then runs the pinned
original (extracted/exefs/code.bin) and the candidate on separate Unicorn
machines with identical fixtures.

Compared outputs per case:
  * continuation PC, final SP, the callee-saved r4-r11 values and r0;
  * the ordered call log of the tail-called helper with both register
    arguments (the self-relative list pointer and slot 0x17);
  * the full observable data region (fixtures, command buffer and the cursor
    global) plus a check that no write escapes the command buffer, the cursor
    global or the private stack frame;
  * an independent model of the emitted record, the advanced cursor and the
    self-relative list pointer.

VFP is enabled through CPACR/FPEXC.  The original clamp and conversion are
`vcmpe`/`vmovgt`/`vmovlo` followed by `vmla.f32` + `vcvt.u32.f32`; the
candidate's plain `0.5f + clamped * 255.0f` is compiled as `vmul` + `vadd`
(two roundings).  That intermediate difference never changes the truncated
byte over the reachable [0, 1] clamp domain, which is covered by an explicit
boundary sweep; the record bytes are compared bit for bit.  The fourth channel
is converted and then masked away by the original
(`bic lr, ip, #0xff000000`); the candidate keeps the same expression but the
conversion has no data result.

Coverage: null state pointer, entry-flag bit 1 cleared/set with unrelated bits,
channel values covering both clamp bounds, signed zero, denormals, infinities,
NaN, truncation boundaries around 0.5 and 127.5, the self-relative list pointer
zero / positive / wrap-around, several cursor offsets, and junk r1/r2/r3.
Negative controls mutate the record headers, the flag bit, the list base, the
rounding bias and the cursor advance; each mutant must be detected.
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
SOURCE = ROOT / "src/engine/leaf_batch41_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_0015a620"

FUNC_ADDR = 0x0015A620
FUNC_SIZE = 416

# ---------------------------------------------------------------------------
# Emulated address space
# ---------------------------------------------------------------------------
CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000          # covers 0x0015A620 and the stub at 0x002A20A8
DATA_ADDR = 0x00400000
DATA_SIZE = 0x00080000          # fixtures, command buffer and the cursor global
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

STUB_2A20A8 = 0x002A20A8
BX_LR = 0xE12FFF1E

# Fixture placement inside DATA.
OBJECT = 0x00400000
STATE = 0x00400100
ENTRY = 0x00400200
CMD_BUFFER = 0x00404000
CMD_BUFFER_SIZE = 0x00004000
CURSOR_GLOBAL = 0x004652A0

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Literal-pool values recovered from 0x0015A7A4..0x0015A7B8.
HEADER_RGB = 0x000400E0
HEADER_END = 0x000F00E1
FLAGGED_LEAD = 0x00010000
COMMAND_SLOT = 0x17
COMMAND_BYTES = 0x10

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

CURSOR_SYMBOL = "g_GpuCommandCursor"
HELPER_SYMBOL = "ui_func_002a20a8"

F32_MAX = 3.4028234663852886e38
F32_OVERFLOW = 3.402823669209385e38


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
    if "func_0015a620" not in funcs:
        raise RuntimeError(f"func_0015a620 not found in {obj}: {sorted(funcs)}")
    raw, relocs = funcs["func_0015a620"]
    code = bytearray(raw)

    for rel in relocs:
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            if rel.symbol_name != HELPER_SYMBOL:
                raise RuntimeError(f"unexpected call relocation: {rel}")
            instruction = struct.unpack_from("<I", code, rel.offset)[0]
            pc = FUNC_ADDR + rel.offset + 8
            displacement = (STUB_2A20A8 - pc) >> 2
            struct.pack_into(
                "<I",
                code,
                rel.offset,
                (instruction & 0xFF000000) | (displacement & 0x00FFFFFF),
            )
        elif rel.relocation_type == 2:  # R_ARM_ABS32
            if rel.symbol_name != CURSOR_SYMBOL:
                raise RuntimeError(f"unexpected abs32 relocation: {rel}")
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            if addend != 0:
                raise RuntimeError(
                    f"unexpected {CURSOR_SYMBOL} addend 0x{addend:08x}"
                )
            struct.pack_into("<I", code, rel.offset, CURSOR_GLOBAL)
        else:
            raise RuntimeError(f"unsupported relocation: {rel}")
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    return compile_candidate(SOURCE, OUT_DIR / "leaf_batch41_c.o")


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


def bits_f32(bits: int) -> float:
    return struct.unpack("<f", struct.pack("<I", bits & 0xFFFFFFFF))[0]


def clamp_channel(value: float) -> float:
    """VFP clamp: NaN compares false against both bounds and passes through."""
    if value > 1.0:
        return 1.0
    if value < 0.0:
        return 0.0
    return value


def channel_byte_variants(value: float):
    """Return (fused_byte, split_byte) or None when either is undefined.

    The fixture stores single-precision floats, so the value is rounded to f32
    before clamping.  The original VMLA result is compared against both the
    fused (single-rounding) and the split (multiply rounded, then add rounded)
    interpretations; the model check is skipped when they disagree so that the
    differential comparison alone decides those inputs.
    """
    clamped = clamp_channel(f32(value))
    if clamped != clamped or math.isinf(clamped):
        return None
    exact = 0.5 + clamped * 255.0
    fused = f32(exact)
    split = f32(0.5 + f32(clamped * 255.0))
    if math.isinf(fused) or math.isinf(split):
        return None
    return (int(fused) & 0xFF, int(split) & 0xFF)


# ---------------------------------------------------------------------------
# Machine
# ---------------------------------------------------------------------------
class Machine:
    """One Unicorn machine with a deterministic stub at 0x002A20A8."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        # Enable CP10/CP11 access and the VFP unit.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        self.uc.mem_write(STUB_2A20A8, struct.pack("<I", BX_LR))
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE, self._on_helper, begin=STUB_2A20A8,
            end=STUB_2A20A8,
        )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []

    # ------------------------------------------------------------------ stubs
    @staticmethod
    def _normalise(pointer: int):
        if STACK_ADDR <= pointer < STACK_ADDR + STACK_SIZE:
            return "<stack>"
        return pointer

    def _on_helper(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        sp = uc.reg_read(arm.UC_ARM_REG_SP)
        self.call_log.append(("ui_func_002a20a8", self._normalise(r0), r1, sp))
        # Deterministic, argument-dependent return value so the caller-visible
        # r0 is checked without modelling the real helper.
        uc.reg_write(arm.UC_ARM_REG_R0, (0x5A5A0000 ^ r0 ^ (r1 << 8)) & 0xFFFFFFFF)

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE):
            self.writes.append((address, size))

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        uc = self.uc
        self.call_log = []
        self.writes = []

        # Wipe everything the case can observe, then install fixtures.
        uc.mem_write(DATA_ADDR, b"\x00" * DATA_SIZE)
        uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        uc.mem_write(CMD_BUFFER, b"\xCC" * CMD_BUFFER_SIZE)
        uc.mem_write(FUNC_ADDR, code)
        # Unicorn 2.1.4 keeps translated blocks across mem_write; drop them.
        uc.ctl_flush_tb()

        write_u32(uc, OBJECT + 0xA0, STATE if case["state_present"] else 0)
        write_u32(uc, STATE + 0x08, ENTRY)

        write_u32(uc, ENTRY + 0x18, case["flags_18"])
        b4, b8, bc, c0 = case["channels"]
        write_f32(uc, ENTRY + 0xB4, b4)
        write_f32(uc, ENTRY + 0xB8, b8)
        write_f32(uc, ENTRY + 0xBC, bc)
        write_f32(uc, ENTRY + 0xC0, c0)
        write_u32(uc, ENTRY + 0xC4, case["rel_c4"])

        write_u32(uc, CURSOR_GLOBAL, case["cursor"])

        uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R0, OBJECT)
        uc.reg_write(arm.UC_ARM_REG_R1, case["junk"][0])
        uc.reg_write(arm.UC_ARM_REG_R2, case["junk"][1])
        uc.reg_write(arm.UC_ARM_REG_R3, case["junk"][2])
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
            "writes": list(self.writes),
        }


def write_u32(uc, address: int, value: int) -> None:
    uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))


def read_u32(uc, address: int) -> int:
    return struct.unpack("<I", uc.mem_read(address, 4))[0]


def write_f32(uc, address: int, value: float) -> None:
    uc.mem_write(address, struct.pack("<f", value))


def read_word(blob: bytes, virt: int) -> int:
    return struct.unpack_from("<I", blob, virt - DATA_ADDR)[0]


# ---------------------------------------------------------------------------
# Independent model
# ---------------------------------------------------------------------------
def model(case: dict):
    """Return (record_words, list_pointer) or None for the gated path."""
    if not case["state_present"]:
        return None

    lead = FLAGGED_LEAD if (case["flags_18"] & 2) != 0 else 0
    rgb = 0
    for index, value in enumerate(case["channels"][:3]):
        variants = channel_byte_variants(value)
        if variants is None or variants[0] != variants[1]:
            rgb = None
            break
        rgb |= variants[0] << (8 * index)
    record = (lead, HEADER_RGB, rgb, HEADER_END)

    offset = case["rel_c4"]
    list_pointer = (ENTRY + 0xC4 + offset) & 0xFFFFFFFF if offset else 0
    return record, list_pointer


def check_expectations(case: dict, result: dict) -> None:
    name = case["name"]
    assert result["pc"] == TRAP_ADDR, f"did not return on {name}"
    assert result["sp"] == ENTRY_SP, f"SP not restored on {name}"
    assert result["callee_saved"] == CALLEE_SAVED_START, (
        f"callee-saved registers clobbered on {name}"
    )

    expected = model(case)
    if expected is None:
        assert result["call_log"] == [], f"calls on gated {name}"
        assert result["cursor"] == case["cursor"], f"cursor moved on gated {name}"
        assert result["writes"] == [], f"writes on gated {name}"
        assert result["ret"] == 0, f"returned r0 on gated {name}"
        return

    record, list_pointer = expected
    assert result["writes"], f"no write observed on {name}"
    assert result["cursor"] == case["cursor"] + COMMAND_BYTES, (
        f"cursor on {name}: 0x{result['cursor']:08x}"
    )
    assert len(result["call_log"]) == 1, f"call count on {name}"
    logged = result["call_log"][0]
    assert logged[0] == HELPER_SYMBOL, f"helper name on {name}: {logged}"
    assert logged[1] == list_pointer, (
        f"helper list pointer on {name}: 0x{logged[1]:08x} != "
        f"0x{list_pointer:08x}"
    )
    assert logged[2] == COMMAND_SLOT, f"helper slot on {name}: {logged[2]}"
    assert logged[3] == ENTRY_SP, f"helper stack pointer on {name}: {logged[3]}"
    assert result["ret"] == (
        0x5A5A0000 ^ list_pointer ^ (COMMAND_SLOT << 8)
    ), f"returned r0 on {name}: 0x{result['ret']:08x}"

    blob = result["data"]
    for index, word in enumerate(record):
        if word is None:
            continue
        got = read_word(blob, case["cursor"] + index * 4)
        assert got == word, (
            f"record word {index} on {name}: 0x{got:08x} != 0x{word:08x}"
        )
    # The cursor global itself.
    assert read_word(blob, CURSOR_GLOBAL) == case["cursor"] + COMMAND_BYTES


def compare(orig: dict, cand: dict, case: dict) -> list[str]:
    problems = []
    for key in ("pc", "sp", "callee_saved", "call_log", "cursor", "ret"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
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

    def stray(writes):
        allowed = {CURSOR_GLOBAL}
        for offset in range(0, COMMAND_BYTES, 4):
            allowed.add(case["cursor"] + offset)
        return sorted(
            {
                address
                for address, _size in writes
                if address not in allowed
                and not (CMD_BUFFER <= address < CMD_BUFFER + CMD_BUFFER_SIZE)
            }
        )

    if stray(orig["writes"]) != stray(cand["writes"]):
        problems.append(
            f"stray writes: orig={stray(orig['writes'])} "
            f"cand={stray(cand['writes'])}"
        )
    return problems


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------
def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "state_present": True,
        "flags_18": 0x00000002,
        "channels": (0.0, 0.5, 1.0, 0.25),
        "rel_c4": 0x200,
        "cursor": CMD_BUFFER,
        "junk": (0x11111111, 0x22222222, 0x33333333),
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- null state pointer: nothing is read or emitted --------------------
    cases.append(base_case("gate: state pointer null", state_present=False))
    cases.append(
        base_case(
            "gate: state pointer null, junk registers",
            state_present=False,
            junk=(0xDEADBEEF, 0xFFFFFFFF, 0x80000000),
        )
    )

    # --- entry flag bit 1 --------------------------------------------------
    for flags in (
        0x00000000,
        0x00000002,
        0x00000001,
        0x00000003,
        0xFFFFFFFF,
        0xFFFFFFFD,
        0x00010000,
        0x00000006,
    ):
        cases.append(base_case(f"flags 0x{flags:08x}", flags_18=flags))

    # --- channel values ----------------------------------------------------
    cases.append(base_case("channels all zero", channels=(0.0, 0.0, 0.0, 0.0)))
    cases.append(base_case("channels all one", channels=(1.0, 1.0, 1.0, 1.0)))
    cases.append(
        base_case(
            "channels quarter steps",
            channels=(0.0, 0.25, 0.5, 0.75),
        )
    )
    cases.append(
        base_case(
            "channels clamped above one",
            channels=(1.5, 100.0, 3.4028234663852886e38, 2.0),
        )
    )
    cases.append(
        base_case(
            "channels clamped below zero",
            channels=(-0.5, -100.0, -3.4028234663852886e38, -1.0),
        )
    )
    cases.append(
        base_case(
            "channels signed zero",
            channels=(-0.0, 0.0, -0.0, -0.0),
        )
    )
    cases.append(
        base_case(
            "channels denormal",
            channels=(1e-40, -3e-41, 2e-39, -1e-45),
        )
    )
    cases.append(
        base_case(
            "channels infinities",
            channels=(float("inf"), float("-inf"), float("inf"), float("-inf")),
        )
    )
    cases.append(
        base_case(
            "channels NaN",
            channels=(float("nan"), 0.5, float("nan"), 1.0),
        )
    )
    cases.append(
        base_case(
            "channels truncation boundary 0.5",
            channels=(0.5, 0.49803922, 0.5019608, 0.0),
        )
    )
    cases.append(
        base_case(
            "channels truncation boundary 127.5",
            channels=(1.0 / 255.0, 2.0 / 255.0, 127.0 / 255.0, 1.0),
        )
    )
    cases.append(
        base_case(
            "channels next-to-boundary floats",
            channels=(0.0019607843, 0.99999994, 0.9999999, 0.0039215689),
        )
    )
    cases.append(
        base_case(
            "channels distinct bytes",
            channels=(0x11 / 255.0, 0x22 / 255.0, 0x33 / 255.0, 0x44 / 255.0),
        )
    )

    # --- dense sweep across the 0.5 + 255*x truncation boundaries ---------
    # Values straddle each k + 0.5 boundary by a couple of float steps, which
    # is where a fused VMLA and the candidate's vmul + vadd can disagree in the
    # intermediate value.
    for k in (1, 64, 127, 128, 192, 254):
        center = f32_bits(f32((k + 0.5) / 255.0))
        values = tuple(
            bits_f32(center + step) for step in (-2, -1, 0, 1)
        )
        cases.append(
            base_case(f"truncation boundary sweep k={k}", channels=values)
        )

    # --- self-relative list pointer ---------------------------------------
    for rel in (0, 1, 4, 0x100, 0x200, 0x800, 0xFFFFF000, 0xFFFFFF00):
        cases.append(base_case(f"rel_c4 0x{rel:08x}", rel_c4=rel))

    # --- cursor positions --------------------------------------------------
    for offset in (0, 4, 0x400, 0x1000, 0x3F00):
        cases.append(
            base_case(f"cursor +0x{offset:x}", cursor=CMD_BUFFER + offset)
        )

    # --- junk incoming registers must not leak into the record ------------
    cases.append(
        base_case(
            "junk registers all ones",
            junk=(0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF),
        )
    )
    cases.append(
        base_case(
            "junk registers distinct",
            junk=(0xCAFEBABE, 0x12345678, 0x9ABCDEF0),
            flags_18=0xFFFFFFFF,
            channels=(1.0, 0.0, 1.0, 0.0),
        )
    )

    # --- combined ----------------------------------------------------------
    cases.append(
        base_case(
            "combined: flagged, wrapped list, offset cursor",
            flags_18=0x00000002,
            channels=(0.2, 0.4, 0.8, 0.6),
            rel_c4=0xFFFFF800,
            cursor=CMD_BUFFER + 0x1234,
        )
    )
    cases.append(
        base_case(
            "combined: null list, cursor near end",
            flags_18=0xFFFFFFFC,
            channels=(1.0, 1.0, 0.0, 0.0),
            rel_c4=0,
            cursor=CMD_BUFFER + 0x3F00,
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
    print("Testing func_0015a620 (0x0015a620)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(f"  original: {len(orig_code)} B, candidate: {len(cand_code)} B")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        (
            "rgb_header",
            "constexpr u32 kCommandHeaderRgb = 0x000400E0;",
            "constexpr u32 kCommandHeaderRgb = 0x000400E1;",
        ),
        (
            "end_header",
            "constexpr u32 kCommandHeaderEnd = 0x000F00E1;",
            "constexpr u32 kCommandHeaderEnd = 0x000F00E0;",
        ),
        (
            "flag_bit",
            "constexpr u32 kEntryFlagBit = 2;",
            "constexpr u32 kEntryFlagBit = 4;",
        ),
        (
            "list_base",
            "reinterpret_cast<u8*>(&entry->rel_c4) + offset",
            "reinterpret_cast<u8*>(entry) + offset",
        ),
        (
            "round_bias",
            "constexpr f32 kRoundBias = 0.5f;",
            "constexpr f32 kRoundBias = 0.25f;",
        ),
        (
            "cursor_advance",
            "constexpr u32 kCommandWords = 4;",
            "constexpr u32 kCommandWords = 3;",
        ),
        (
            "channel_span",
            "constexpr f32 kChannelSpan = 255.0f;",
            "constexpr f32 kChannelSpan = 254.0f;",
        ),
        (
            "command_slot",
            "constexpr u32 kCommandSlot = 0x17;",
            "constexpr u32 kCommandSlot = 0x16;",
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
