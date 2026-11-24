#!/usr/bin/env python3
"""Differential test for engine_func_0010f120 (0x0010f120) using Unicorn ARM.

Compiles src/engine/leaf_batch45_b.cpp, extracts the engine_func_0010f120 body,
resolves its direct calls to deterministic stubs at the original addresses, and
runs the pinned original (extracted/exefs/code.bin) against the candidate in
separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11 and the VFP
    callee-saved s16-s23 (d8-d10);
  * the ordered call log: every register argument plus, for the float-taking
    helpers, the s0-s5 argument bits, the vec3 contents behind the 0x2C20A8
    pointers, and the shader-name string;
  * the full `self` page and the data page (shader name must stay untouched);
  * any write outside the private stack and the `self` page.

Coverage: allocation null / non-null, constructor return distinct from its
argument, shader load null / non-null and sizes 0 / 1 / 0x80 / 0x7FFFFFFF /
0xFFFFFFFF, keyframe lookups 0 / 0x7FFFFFFF / 0x80000000 / 0xFFFFFFFF for both
indices (0 and 2), and per-index table results including 0 and 0xFFFFFFFF.
Negative controls mutate the shader name, the allocation size, a camera block
offset, the projection aspect and the element enabled-byte offset; each mutant
must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_0010f120"

FUNC_ADDR = 0x0010F120
FUNC_SIZE = 836

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # 0x100000..0x400000 covers the function and the stubs
DATA_ADDR = 0x00409000
DATA_SIZE = 0x00001000
SELF_ADDR = 0x00700000
SELF_SIZE = 0x00020000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

SHADER_NAME_ADDR = 0x004092A8
SHADER_NAME = b"DefaultTextureVS.shbin\x00"

ALLOC_RESULT = 0x0071A000        # inside the self page, past the written fields
SHADER_DATA = 0x0071B000         # inside the self page, past the written fields

# Direct-call targets; stubs are placed at the original addresses so both the
# original bytes and the relocated candidate resolve to them.
STUB_ASD_MEMORY = 0x002C23F8
STUB_UI_INIT = 0x0011B4A8
STUB_FILE_LOAD = 0x002C5E3C
STUB_SHADER_UPLOAD = 0x0011B3B8
STUB_KEY_A = 0x002C1784
STUB_KEY_B = 0x002C17AC
STUB_MATRIX = 0x002BC170
STUB_MATRIX_POST = 0x002BC0B4
STUB_CAM_INIT = 0x002C2210
STUB_CAM_ORIENT = 0x002C20A8
STUB_CAM_PROJ = 0x002C1FFC
STUB_OBJ_INIT = 0x002BC014
STUB_ELEM_INIT = 0x0011B388
STUB_ELEM_LOOKUP = 0x0011A0C8

STUB_NAMES = {
    STUB_ASD_MEMORY: "AsdMemory_func_002c23f8",
    STUB_UI_INIT: "ui_func_0011b4a8",
    STUB_FILE_LOAD: "engine_func_002c5e3c",
    STUB_SHADER_UPLOAD: "engine_func_0011b3b8",
    STUB_KEY_A: "engine_func_002c1784",
    STUB_KEY_B: "engine_func_002c17ac",
    STUB_MATRIX: "engine_func_002bc170",
    STUB_MATRIX_POST: "engine_func_002bc0b4",
    STUB_CAM_INIT: "engine_func_002c2210",
    STUB_CAM_ORIENT: "engine_func_002c20a8",
    STUB_CAM_PROJ: "ui_func_002c1ffc",
    STUB_OBJ_INIT: "engine_func_002bc014",
    STUB_ELEM_INIT: "engine_func_0011b388",
    STUB_ELEM_LOOKUP: "engine_func_0011a0c8",
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

VFP_CALLEE_SAVED = {
    "s16": arm.UC_ARM_REG_S16,
    "s17": arm.UC_ARM_REG_S17,
    "s18": arm.UC_ARM_REG_S18,
    "s19": arm.UC_ARM_REG_S19,
    "s20": arm.UC_ARM_REG_S20,
    "s21": arm.UC_ARM_REG_S21,
    "s22": arm.UC_ARM_REG_S22,
    "s23": arm.UC_ARM_REG_S23,
}
VFP_CALLEE_SAVED_START = {
    "s16": 0x7FC00016,
    "s17": 0x7FC00017,
    "s18": 0x7FC00018,
    "s19": 0x7FC00019,
    "s20": 0x7FC0001A,
    "s21": 0x7FC0001B,
    "s22": 0x7FC0001C,
    "s23": 0x7FC0001D,
}

DEFAULT_LOOKUP = {
    index: 0xA5A50000 | (index * 0x0101) for index in range(12)
}


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def elf_sections(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize = struct.unpack_from("<H", data, 46)[0]
    e_shnum = struct.unpack_from("<H", data, 48)[0]
    e_shstrndx = struct.unpack_from("<H", data, 50)[0]
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    shstr = sections[e_shstrndx]
    shstrtab = data[shstr[4] : shstr[4] + shstr[5]]
    result: dict[str, bytes] = {}
    for section in sections:
        end = shstrtab.find(b"\x00", section[0])
        name = shstrtab[section[0] : end].decode("ascii", errors="replace")
        result[name] = data[section[4] : section[4] + section[5]]
    return result


def relocate_candidate(obj_file: Path) -> tuple[bytes, bytes]:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0010f120" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_0010f120 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    rodata_addend = None
    for rel in relocs:
        if rel.relocation_type in (1, 28, 29):
            target = None
            for address, name in STUB_NAMES.items():
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
        elif rel.relocation_type == 2:  # R_ARM_ABS32 into .rodata
            rodata_addend = struct.unpack_from("<I", code, rel.offset)[0]
            struct.pack_into("<I", code, rel.offset, SHADER_NAME_ADDR)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )

    if rodata_addend is None:
        raise RuntimeError("no read-only data relocation for the shader name")

    sections = elf_sections(obj_file)
    payload = sections.get(".rodata")
    if payload is None:
        payload = next((value for key, value in sections.items() if "rodata" in key),
                       None)
    if payload is None or rodata_addend >= len(payload):
        raise RuntimeError("could not resolve the shader-name string")
    end = payload.find(b"\x00", rodata_addend)
    if end < 0:
        raise RuntimeError("unterminated shader-name string")
    name_bytes = payload[rodata_addend:end]
    return bytes(code), name_bytes


def pin_shader_name() -> bytes:
    """Read the shader-name bytes the pinned original points at."""
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(SHADER_NAME_ADDR - 0x00100000)
        name = handle.read(64).split(b"\x00", 1)[0]
    if name + b"\x00" != SHADER_NAME:
        raise RuntimeError(f"unexpected pinned shader name: {name!r}")
    return name


def compile_candidate_baseline() -> tuple[bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_b.o"
    res = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> tuple[bytes, bytes]:
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


def read_c_string(uc, address: int, limit: int = 64) -> bytes:
    out = bytearray()
    for index in range(limit):
        byte = uc.mem_read(address + index, 1)[0]
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


def f32_bits(uc, register: int) -> int:
    return uc.reg_read(register) & 0xFFFFFFFF


def read_vec3(uc, address: int) -> tuple:
    return struct.unpack("<3I", uc.mem_read(address, 12))


class F120Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(SELF_ADDR, SELF_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        # Enable the VFP coprocessor (CP10/CP11); the pinned function pushes,
        # converts and loads single-precision registers.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], tuple(args)))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_ASD_MEMORY:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("alloc", ALLOC_RESULT))
        elif address == STUB_UI_INIT:
            self._log(address, r0)
            # The real constructor returns its argument; returning a distinct
            # tag proves the candidate forwards the call result, not its input.
            uc.reg_write(arm.UC_ARM_REG_R0, (r0 + 0x40) & 0xFFFFFFFF)
        elif address == STUB_FILE_LOAD:
            self._log(address, read_c_string(uc, r0), r2, r3)
            uc.mem_write(r1, struct.pack("<I", self.case.get("shader_size", 0x80)))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("shader_data", SHADER_DATA))
        elif address == STUB_SHADER_UPLOAD:
            self._log(address, r0, r1, r2, r3)
            uc.reg_write(arm.UC_ARM_REG_R0, 1)
        elif address == STUB_KEY_A:
            self._log(address, r0)
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case.get("key_a", {}).get(r0, 0x11110000)
            )
        elif address == STUB_KEY_B:
            self._log(address, r0)
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case.get("key_b", {}).get(r0, 0x22220000)
            )
        elif address == STUB_MATRIX:
            self._log(address, r0, f32_bits(uc, arm.UC_ARM_REG_S0),
                      f32_bits(uc, arm.UC_ARM_REG_S1),
                      f32_bits(uc, arm.UC_ARM_REG_S2),
                      f32_bits(uc, arm.UC_ARM_REG_S3),
                      f32_bits(uc, arm.UC_ARM_REG_S4),
                      f32_bits(uc, arm.UC_ARM_REG_S5))
        elif address == STUB_MATRIX_POST:
            self._log(address, r0, r1)
        elif address == STUB_CAM_INIT:
            self._log(address, r0, r1)
        elif address == STUB_CAM_ORIENT:
            self._log(address, r0, r1, r2, r3,
                      read_vec3(uc, r1), read_vec3(uc, r2), read_vec3(uc, r3))
        elif address == STUB_CAM_PROJ:
            self._log(address, r0, r1,
                      f32_bits(uc, arm.UC_ARM_REG_S0),
                      f32_bits(uc, arm.UC_ARM_REG_S1),
                      f32_bits(uc, arm.UC_ARM_REG_S2),
                      f32_bits(uc, arm.UC_ARM_REG_S3))
        elif address == STUB_OBJ_INIT:
            self._log(address, r0)
        elif address == STUB_ELEM_INIT:
            self._log(address, r0, r1)
        elif address == STUB_ELEM_LOOKUP:
            self._log(address, r0)
            uc.reg_write(
                arm.UC_ARM_REG_R0,
                self.case.get("lookup", DEFAULT_LOOKUP).get(
                    r0 & 0xFF, 0xA5A50000
                ),
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

    def run(self, code: bytes, shader_name: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(DATA_ADDR, b"\x00" * DATA_SIZE)
        self.uc.mem_write(SHADER_NAME_ADDR, shader_name + b"\x00")
        self.uc.mem_write(SELF_ADDR, b"\x5A" * SELF_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)
        for name, value in VFP_CALLEE_SAVED_START.items():
            self.uc.reg_write(VFP_CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_self = SELF_ADDR <= address < SELF_ADDR + SELF_SIZE
            if not (in_stack or in_self):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "vfp_callee_saved": {
                name: self.uc.reg_read(reg) & 0xFFFFFFFF
                for name, reg in VFP_CALLEE_SAVED.items()
            },
            "call_log": self._normalise(self.call_log),
            "self_memory": bytes(self.uc.mem_read(SELF_ADDR, SELF_SIZE)),
            "data_memory": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "vfp_callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig="
            + repr(orig["call_log"])
            + "\n    cand="
            + repr(cand["call_log"])
        )
    if orig["self_memory"] != cand["self_memory"]:
        diffs = [
            index
            for index, (left, right) in enumerate(
                zip(orig["self_memory"], cand["self_memory"])
            )
            if left != right
        ]
        problems.append(f"self memory differs at {diffs[:16]} ({len(diffs)} bytes)")
    if orig["data_memory"] != cand["data_memory"]:
        problems.append("data page was modified differently")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "alloc": ALLOC_RESULT,
        "shader_data": SHADER_DATA,
        "shader_size": 0x80,
        "key_a": {0: 0x3F800000, 2: 0x40400000},
        "key_b": {0: 0x40000000, 2: 0x40800000},
        "lookup": dict(DEFAULT_LOOKUP),
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    cases.append(base_case("baseline"))

    # --- allocation: null and non-null
    cases.append(base_case("allocation null", alloc=0))
    cases.append(base_case("allocation null, shader null", alloc=0, shader_data=0))
    cases.append(base_case("allocation at page edge", alloc=SELF_ADDR + SELF_SIZE - 0x40))

    # --- shader load result and stream size
    cases.append(base_case("shader data null", shader_data=0))
    for size in (0, 1, 0x7F, 0x80, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        cases.append(base_case(f"shader size 0x{size:08x}", shader_size=size))
    cases.append(base_case("shader null with size 0", shader_data=0, shader_size=0))
    cases.append(
        base_case("shader null with size max", shader_data=0, shader_size=0xFFFFFFFF)
    )

    # --- keyframe lookups: zero, signed boundaries and unsigned conversion
    for value in (0, 1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        cases.append(
            base_case(
                f"key_a=0x{value:08x}",
                key_a={0: value, 2: value ^ 0x55555555},
            )
        )
        cases.append(
            base_case(
                f"key_b=0x{value:08x}",
                key_b={0: value, 2: value ^ 0x0F0F0F0F},
            )
        )
    cases.append(base_case("all keys zero", key_a={0: 0, 2: 0}, key_b={0: 0, 2: 0}))
    cases.append(
        base_case(
            "all keys max",
            key_a={0: 0xFFFFFFFF, 2: 0xFFFFFFFF},
            key_b={0: 0xFFFFFFFF, 2: 0xFFFFFFFF},
        )
    )

    # --- per-index table results
    for value in (0, 0xFFFFFFFF, 0x80000000, 0x7FFFFFFF):
        cases.append(
            base_case(
                f"lookup all 0x{value:08x}",
                lookup={index: value for index in range(12)},
            )
        )
    cases.append(
        base_case(
            "lookup alternating",
            lookup={index: index * 0x11111111 for index in range(12)},
        )
    )
    cases.append(
        base_case(
            "lookup last only",
            lookup={index: 0 for index in range(11)} | {11: 0xDEADBEEF},
        )
    )

    # --- combined boundary case
    cases.append(
        base_case(
            "combined boundary",
            alloc=SELF_ADDR,
            shader_data=0,
            shader_size=0xFFFFFFFF,
            key_a={0: 0x80000000, 2: 0x7FFFFFFF},
            key_b={0: 0x7FFFFFFF, 2: 0x80000000},
            lookup={index: 0xFFFFFFFF - index for index in range(12)},
        )
    )

    return cases


def run_case_set(orig_code, cand_code, orig_name, cand_name, cases) -> int:
    passed = 0
    for case in cases:
        orig = F120Runner().run(orig_code, orig_name, case)
        cand = F120Runner().run(cand_code, cand_name, case)
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
    print("Testing engine_func_0010f120 (0x0010f120)...")
    orig_code = get_orig_bytes()
    orig_name = pin_shader_name()
    cand_code, cand_name = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        f"(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, orig_name, cand_name, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("shader_name",
         'constexpr char kShaderName[] = "DefaultTextureVS.shbin";',
         'constexpr char kShaderName[] = "DefaultTextureVS.shbiN";'),
        ("allocation_size", "constexpr u32 kAllocationSize = 0x12A48;",
         "constexpr u32 kAllocationSize = 0x12A44;"),
        ("camera_block_b", "constexpr u32 kCameraBlockB = 0x0C04;",
         "constexpr u32 kCameraBlockB = 0x0C08;"),
        ("projection_aspect", "constexpr f32 kAspect = 1.6666666269302368f;",
         "constexpr f32 kAspect = 1.6666665077209473f;"),
        ("element_flag_offset", "constexpr u32 kElementEnabledOffset = 0x18;",
         "constexpr u32 kElementEnabledOffset = 0x1C;"),
        ("element_count", "constexpr u32 kElementCount = 12;",
         "constexpr u32 kElementCount = 11;"),
    ):
        mutant_code, mutant_name = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = F120Runner().run(orig_code, orig_name, case)
            bad = F120Runner().run(mutant_code, mutant_name, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
