#!/usr/bin/env python3
"""Differential test for func_002712d4 (0x002712D4) using Unicorn ARM.

Compiles ``src/engine/leaf_batch45_a.cpp``, extracts the ``func_002712d4`` body,
resolves its direct calls to deterministic stubs at the original addresses, and
runs the pinned original (``extracted/exefs/code.bin``) against the candidate in
separate Unicorn machines with identical fixtures.

The routine selects one row of the 0x00447E58 placement table, publishes an
origin/probe pair into 0x0049F91C, samples four 90-degree-snapped headings
around the row heading, and keeps the probe whose segment result is closest.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11 and s16-s31;
  * the ordered call log with every register/HFA argument and the stack words of
    each helper (stack pointers are normalised to ``<stack>``);
  * the Vec3 payloads read through the 0x00266E88 pointers;
  * the full manager, owner, runtime-state, camera-object and pointer-slot pages;
  * every write outside the private stack.

Coverage: null and non-null link word; initial segment rejection; a rejected
sample at each of the four loop positions; positive, negative, zero and
wrapped heading values; signed zero deltas; improving and non-improving
distance sequences; row indices 0, 1, 0x3F and the 32-bit wrap index; an owner
object distinct from the manager; and distinct camera-eye quadrants.

Negative controls recompile mutated source (probe distance, origin lift, link
offset, owner flag offset, state target offset, degree scale, sample count,
step-sign comparison, row X offset, camera-eye offset, index offset); each must
be detected.
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
SOURCE = ROOT / "src/engine/leaf_batch45_a.cpp"
OUT_DIR = ROOT / "build/test_leaf_002712d4"

FUNC_ADDR = 0x002712D4
FUNC_SIZE = 632

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers the function and every stub below 0x3F0000

MANAGER_LO_ADDR = 0x00700000
MANAGER_LO_SIZE = 0x00010000
MANAGER_ADDR = 0x00710000
MANAGER_SIZE = 0x00010000
OWNER_ADDR = 0x00720000
OWNER_SIZE = 0x00010000
STATE_ADDR = 0x0049F000  # page containing g_MapRuntimeState (0x0049F91C)
STATE_SIZE = 0x00001000
CAMERA_ADDR = 0x00740000
CAMERA_SIZE = 0x00010000
ABS_ADDR = 0x00447000  # 0x004474F4 camera slot and 0x00447E58 owner slot
ABS_SIZE = 0x00020000

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_266E88 = 0x00266E88
STUB_282588 = 0x00282588
STUB_282600 = 0x00282600
STUB_28277C = 0x0028277C
STUB_287D54 = 0x00287D54
STUB_287D74 = 0x00287D74
STUB_287E4C = 0x00287E4C

STUB_NAMES = {
    STUB_266E88: "script_vm_func_00266e88",
    STUB_282588: "script_vm_func_00282588",
    STUB_282600: "script_vm_func_00282600",
    STUB_28277C: "script_vm_func_0028277c",
    STUB_287D54: "engine_func_00287d54",
    STUB_287D74: "script_vm_func_00287d74",
    STUB_287E4C: "script_vm_func_00287e4c",
}

CAMERA_SLOT = 0x004474F4
OWNER_SLOT = 0x00447E58

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
VFP_REGS = {
    "s16": arm.UC_ARM_REG_S16,
    "s17": arm.UC_ARM_REG_S17,
    "s18": arm.UC_ARM_REG_S18,
    "s19": arm.UC_ARM_REG_S19,
    "s20": arm.UC_ARM_REG_S20,
    "s21": arm.UC_ARM_REG_S21,
    "s22": arm.UC_ARM_REG_S22,
    "s23": arm.UC_ARM_REG_S23,
    "s24": arm.UC_ARM_REG_S24,
    "s25": arm.UC_ARM_REG_S25,
    "s26": arm.UC_ARM_REG_S26,
    "s27": arm.UC_ARM_REG_S27,
    "s28": arm.UC_ARM_REG_S28,
    "s29": arm.UC_ARM_REG_S29,
    "s30": arm.UC_ARM_REG_S30,
    "s31": arm.UC_ARM_REG_S31,
}
VFP_START = {
    "s16": 0x3F800000,  # 1.0f
    "s17": 0x40000000,  # 2.0f
    "s18": 0x40400000,  # 3.0f
    "s19": 0x40800000,  # 4.0f
    "s20": 0x40A00000,  # 5.0f
    "s21": 0x40C00000,  # 6.0f
    "s22": 0x40E00000,  # 7.0f
    "s23": 0x41000000,  # 8.0f
    "s24": 0x41100000,  # 9.0f
    "s25": 0x41200000,  # 10.0f
    "s26": 0x41300000,  # 11.0f
    "s27": 0x41400000,  # 12.0f
    "s28": 0x41500000,  # 13.0f
    "s29": 0x41600000,  # 14.0f
    "s30": 0x41700000,  # 15.0f
    "s31": 0x41800000,  # 16.0f
}


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


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


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "002712d4" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"func_002712d4 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
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
        cond = original & 0xFF000000
        struct.pack_into(
            "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
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


# --------------------------------------------------------------------- stubs
SNAP_GUARD = 4096


def snap_degrees(value: float) -> float:
    x = f32(value)
    guard = 0
    while x >= 360.0 and guard < SNAP_GUARD:
        x = f32(x - 360.0)
        guard += 1
    while x < 0.0 and guard < SNAP_GUARD:
        x = f32(x + 360.0)
        guard += 1
    quotient = int(f32(f32(x + 45.0) / 90.0))
    return f32(float(quotient) * 90.0)


def wrap_degrees(value: float) -> float:
    x = f32(value)
    turns = math.floor(x / 360.0)
    return f32(x - 360.0 * float(turns))


def delta_degrees(base: float, angle: float) -> float:
    a = wrap_degrees(base)
    b = wrap_degrees(angle)
    diff = f32(a - b)
    if diff > 180.0 or diff < -180.0:
        if a < b:
            a = f32(a + 360.0)
        else:
            b = f32(b + 360.0)
    return f32(b - a)


def angle_degrees(from_xyz, to_xyz) -> float:
    dx = f32(to_xyz[0] - from_xyz[0])
    dz = f32(to_xyz[2] - from_xyz[2])
    radians = math.atan2(dx, dz)
    degrees = f32(radians * f32(57.3248405456543))
    if degrees < 0.0:
        degrees = f32(degrees + 360.0)
    if f32_bits(degrees) > f32_bits(360.0):
        degrees = f32(degrees - 360.0)
    return degrees


def distance_xyz(a_xyz, b_xyz) -> float:
    dx = f32(b_xyz[0] - a_xyz[0])
    dy = f32(b_xyz[1] - a_xyz[1])
    dz = f32(b_xyz[2] - a_xyz[2])
    sq = f32(dx * dx)
    sq = f32(sq + f32(dy * dy))
    sq = f32(sq + f32(dz * dz))
    return f32(math.sqrt(sq))


def read_vec3(uc, address: int) -> tuple[float, float, float]:
    raw = uc.mem_read(address, 12)
    return struct.unpack("<fff", raw)


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        for address, size in (
            (CODE_ADDR, CODE_SIZE),
            (MANAGER_LO_ADDR, MANAGER_LO_SIZE),
            (MANAGER_ADDR, MANAGER_SIZE),
            (OWNER_ADDR, OWNER_SIZE),
            (STATE_ADDR, STATE_SIZE),
            (CAMERA_ADDR, CAMERA_SIZE),
            (ABS_ADDR, ABS_SIZE),
            (STACK_ADDR, STACK_SIZE),
            (TRAP_ADDR, 0x1000),
        ):
            self.uc.mem_map(address, size)

        bx_lr_arm = struct.pack("<I", 0xE12FFF1E)
        for address in STUB_NAMES:
            self.uc.mem_write(address, bx_lr_arm)
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}
        self.ray_index = 0
        self.distance_index = 0

    # ------------------------------------------------------------------ stubs
    def _normalise_address(self, value: int) -> object:
        if STACK_ADDR <= value < STACK_ADDR + STACK_SIZE:
            return "<stack>"
        return value

    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], args))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        s0 = uc.reg_read(arm.UC_ARM_REG_S0)
        s1 = uc.reg_read(arm.UC_ARM_REG_S1)
        s2 = uc.reg_read(arm.UC_ARM_REG_S2)
        s3 = uc.reg_read(arm.UC_ARM_REG_S3)
        s4 = uc.reg_read(arm.UC_ARM_REG_S4)
        s5 = uc.reg_read(arm.UC_ARM_REG_S5)

        if address == STUB_266E88:
            first = read_vec3(uc, r0)
            second = read_vec3(uc, r1)
            out = self._normalise_address(r2)
            self._log(address, out, first, second)
            results = self.case.get("ray_results", ())
            result = (
                results[self.ray_index]
                if self.ray_index < len(results)
                else self.case.get("ray_result", 0)
            )
            self.ray_index += 1
            # The real helper fills its output structure; mirror that the
            # candidate passes a writable pointer.
            uc.mem_write(
                r2,
                struct.pack(
                    "<IIII", 0x51A70000 | self.ray_index, r1, r0, 0xA5A5A5A5
                ),
            )
            uc.reg_write(arm.UC_ARM_REG_R0, result & 0xFFFFFFFF)
        elif address == STUB_282588:
            self._log(address, f32_bits(s0))
            uc.reg_write(arm.UC_ARM_REG_S0, f32_bits(snap_degrees(s0)))
            uc.reg_write(arm.UC_ARM_REG_R0, 0x28258800)
        elif address == STUB_28277C:
            self._log(address, f32_bits(s0))
            uc.reg_write(arm.UC_ARM_REG_S0, f32_bits(f32(math.sin(s0))))
            uc.reg_write(arm.UC_ARM_REG_R0, 0x28277C00)
        elif address == STUB_282600:
            self._log(address, f32_bits(s0))
            uc.reg_write(arm.UC_ARM_REG_S0, f32_bits(f32(math.cos(s0))))
            uc.reg_write(arm.UC_ARM_REG_R0, 0x28260000)
        elif address == STUB_287D54:
            a_xyz = (s0, s1, s2)
            b_xyz = (s3, s4, s5)
            self._log(address, f32_bits(s0), f32_bits(s1), f32_bits(s2),
                      f32_bits(s3), f32_bits(s4), f32_bits(s5))
            values = self.case.get("distance_results", ())
            result = (
                values[self.distance_index]
                if self.distance_index < len(values)
                else distance_xyz(a_xyz, b_xyz)
            )
            self.distance_index += 1
            uc.reg_write(arm.UC_ARM_REG_S0, f32_bits(result))
            uc.reg_write(arm.UC_ARM_REG_R0, 0x287D5400)
        elif address == STUB_287D74:
            self._log(address, f32_bits(s0), f32_bits(s1))
            uc.reg_write(
                arm.UC_ARM_REG_S0, f32_bits(delta_degrees(s0, s1))
            )
            uc.reg_write(arm.UC_ARM_REG_R0, 0x287D7400)
        elif address == STUB_287E4C:
            from_xyz = (s0, s1, s2)
            to_xyz = (s3, s4, s5)
            self._log(address, f32_bits(s0), f32_bits(s1), f32_bits(s2),
                      f32_bits(s3), f32_bits(s4), f32_bits(s5))
            uc.reg_write(
                arm.UC_ARM_REG_S0, f32_bits(angle_degrees(from_xyz, to_xyz))
            )
            uc.reg_write(arm.UC_ARM_REG_R0, 0x287E4C00)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case
        self.ray_index = 0
        self.distance_index = 0

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(ABS_ADDR, case["abs_page"])
        self.uc.mem_write(MANAGER_LO_ADDR, case["manager_lo"])
        self.uc.mem_write(MANAGER_ADDR, case["manager"])
        self.uc.mem_write(OWNER_ADDR, case["owner"])
        self.uc.mem_write(STATE_ADDR, case["state"])
        self.uc.mem_write(CAMERA_ADDR, case["camera"])
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, case["value"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case["owner_slot"])
        self.uc.reg_write(arm.UC_ARM_REG_R2, MANAGER_ADDR)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)
        for name, bits in VFP_START.items():
            self.uc.reg_write(VFP_REGS[name], bits)

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
            "callee_saved_vfp": {
                name: self.uc.reg_read(reg) for name, reg in VFP_REGS.items()
            },
            "call_log": self.call_log,
            "fixtures": {
                "manager_lo": bytes(
                    self.uc.mem_read(MANAGER_LO_ADDR, MANAGER_LO_SIZE)
                ),
                "manager": bytes(self.uc.mem_read(MANAGER_ADDR, MANAGER_SIZE)),
                "owner": bytes(self.uc.mem_read(OWNER_ADDR, OWNER_SIZE)),
                "state": bytes(self.uc.mem_read(STATE_ADDR, STATE_SIZE)),
                "camera": bytes(self.uc.mem_read(CAMERA_ADDR, CAMERA_SIZE)),
                "abs": bytes(self.uc.mem_read(ABS_ADDR, ABS_SIZE)),
            },
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "callee_saved_vfp"):
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
            differing = [
                index
                for index, (left, right) in enumerate(
                    zip(value, cand["fixtures"][key])
                )
                if left != right
            ]
            problems.append(
                f"fixture {key} differs at offsets "
                f"{[hex(i) for i in differing[:16]]}"
            )
    if orig["unexpected_writes"] != cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


# ------------------------------------------------------------------ fixtures
PATTERN = bytes((index * 37 + 11) & 0xFF for index in range(0x10000))


def patterned(size: int, seed: int = 0) -> bytearray:
    return bytearray(
        (PATTERN[index % len(PATTERN)] + seed) & 0xFF for index in range(size)
    )


def build_case(name: str, **kwargs) -> dict:
    index = kwargs.get("index", 0)
    row_offset = (index * 0x38) & 0xFFFFFFFF
    row_addr = (MANAGER_ADDR + row_offset) & 0xFFFFFFFF

    # The manager and its preceding page are one contiguous region so that the
    # 32-bit wrap index 0xFFFFFFFF can reach row-56 without leaving the map.
    region = patterned(MANAGER_LO_SIZE + MANAGER_SIZE)
    row_region = (row_addr - MANAGER_LO_ADDR) & 0x1FFFF

    def put8(offset: int, value: int) -> None:
        region[row_region + offset] = value & 0xFF

    def put32(offset: int, value) -> None:
        struct.pack_into(
            "<I", region, row_region + offset, value & 0xFFFFFFFF
        )

    # Row fields first: for index 0x3F the link word at row+0x38 is the header
    # selector itself, so the header write below is what leaves it set.
    put8(0x0C, kwargs.get("row_active", 0xA1))
    put8(0x0E, kwargs.get("row_value", 0xB2))
    put32(0x1C, f32_bits(f32(kwargs.get("row_x", 12.5))))
    put32(0x20, f32_bits(f32(kwargs.get("row_y", -3.25))))
    put32(0x24, f32_bits(f32(kwargs.get("row_z", 47.75))))
    put32(0x28, f32_bits(f32(kwargs.get("heading", 0.0))))
    put32(0x38, kwargs.get("link", 0x12345678))

    # Distinct sentinels in the header bytes this routine may touch.
    header = MANAGER_LO_SIZE
    region[header + 0xE0C] = kwargs.get("header_c", 0x11)
    struct.pack_into("<I", region, header + 0xE10, index)
    region[header + 0xE3C] = kwargs.get("manager_flag", 0x22)
    manager_lo = bytes(region[:MANAGER_LO_SIZE])
    manager = bytes(region[MANAGER_LO_SIZE:])

    owner = patterned(OWNER_SIZE)
    owner[0xE3C] = kwargs.get("owner_flag", 0x33)

    state = patterned(STATE_SIZE, seed=7)
    camera = patterned(CAMERA_SIZE, seed=13)
    struct.pack_into(
        "<fff",
        camera,
        0x4C,
        f32(kwargs.get("eye_x", 500.0)),
        f32(kwargs.get("eye_y", 40.0)),
        f32(kwargs.get("eye_z", 10.0)),
    )

    abs_page = patterned(ABS_SIZE, seed=29)
    struct.pack_into("<I", abs_page, CAMERA_SLOT - ABS_ADDR, CAMERA_ADDR)
    owner_slot = kwargs.get("owner_slot", OWNER_SLOT)
    owner_pointer = kwargs.get("owner_pointer", OWNER_ADDR)
    struct.pack_into(
        "<I", abs_page, owner_slot - ABS_ADDR, owner_pointer
    )

    return {
        "name": name,
        "value": kwargs.get("value", 0x5A),
        "index": index,
        "owner_slot": owner_slot,
        "manager": manager,
        "manager_lo": manager_lo,
        "owner": bytes(owner),
        "state": bytes(state),
        "camera": bytes(camera),
        "abs_page": bytes(abs_page),
        "ray_results": kwargs.get("ray_results", ()),
        "ray_result": kwargs.get("ray_result", 0),
        "distance_results": kwargs.get("distance_results", ()),
    }


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- link word gate: no segment, no distance, no angle helpers.
    cases.append(build_case("link word zero", link=0, row_x=3.0, row_y=4.0,
                            row_z=5.0, heading=0.0))

    # --- initial segment rejection.
    cases.append(build_case("initial segment rejected", link=1,
                            ray_results=(-1,)))

    # --- sample rejection at each loop position.
    for reject_at in range(4):
        results = tuple(-1 if index == reject_at else index + 1
                        for index in range(4))
        cases.append(
            build_case(f"sample {reject_at} rejected", link=1,
                       ray_results=results, heading=0.0,
                       eye_x=100.0, eye_z=200.0)
        )

    # --- all samples accepted, realistic distances.
    for heading, eye in (
        (0.0, (500.0, 40.0, 10.0)),
        (0.0, (-500.0, 40.0, 10.0)),
        (45.0, (10.0, 40.0, 900.0)),
        (89.9, (-800.0, 40.0, -800.0)),
        (135.0, (0.0, 40.0, 0.0)),
        (180.0, (250.0, 40.0, -250.0)),
        (269.0, (-250.0, 40.0, 250.0)),
        (359.0, (5.0, -40.0, 5.0)),
        (360.0, (700.0, 40.0, 700.0)),
        (-45.0, (12.5, 40.0, 47.75)),
        (-90.5, (-12.5, 40.0, -47.75)),
        (450.0, (900.0, 40.0, -100.0)),
        (0.0, (12.5, 40.0, 47.75)),  # delta exactly zero
    ):
        cases.append(
            build_case(f"heading {heading} eye {eye}", link=1,
                       heading=heading, eye_x=eye[0], eye_y=eye[1],
                       eye_z=eye[2])
        )

    # --- improving and non-improving distance sequences (double call check).
    cases.append(
        build_case("distances strictly decreasing", link=1, heading=30.0,
                   eye_x=12.5, eye_z=47.75,
                   distance_results=(1000.0, 900.0, 800.0, 700.0, 600.0,
                                     500.0, 400.0, 300.0))
    )
    cases.append(
        build_case("distances strictly increasing", link=1, heading=30.0,
                   eye_x=12.5, eye_z=47.75,
                   distance_results=(1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0,
                                     8.0))
    )
    cases.append(
        build_case("first sample improves only", link=1, heading=30.0,
                   eye_x=12.5, eye_z=47.75,
                   distance_results=(100.0, 50.0, 75.0, 80.0, 90.0, 95.0))
    )
    cases.append(
        build_case("last sample improves", link=1, heading=30.0,
                   eye_x=12.5, eye_z=47.75,
                   distance_results=(100.0, 100.0, 100.0, 100.0, 100.0, 1.0))
    )
    cases.append(
        build_case("equal distances do not improve", link=1, heading=30.0,
                   eye_x=12.5, eye_z=47.75,
                   distance_results=(5.0, 5.0, 5.0, 5.0, 5.0, 5.0))
    )

    # --- row index selection and 32-bit wrap.
    for index in (0, 1, 0x3F, 0xFFFFFFFF):
        cases.append(
            build_case(f"index 0x{index:08x}", index=index, link=1,
                       heading=0.0, eye_x=100.0, eye_z=30.0)
        )

    # --- payload byte values and owner flag aliasing.
    for value in (0x00, 0x01, 0x7F, 0x80, 0xFF):
        cases.append(
            build_case(f"value 0x{value:02x}", value=value, link=1,
                       heading=0.0, eye_x=100.0, eye_z=30.0)
        )
    cases.append(
        build_case("owner distinct from manager", link=1, heading=0.0,
                   owner_pointer=OWNER_ADDR + 0x100, eye_x=100.0, eye_z=30.0)
    )
    cases.append(
        build_case("owner aliases manager", link=1, heading=0.0,
                   owner_pointer=MANAGER_ADDR, eye_x=100.0, eye_z=30.0)
    )
    cases.append(
        build_case("alternate owner slot pointer", link=1, heading=0.0,
                   owner_slot=OWNER_SLOT + 8, owner_pointer=OWNER_ADDR + 0x40,
                   eye_x=100.0, eye_z=30.0)
    )

    # --- coordinate and heading boundaries.
    for x, y, z in (
        (0.0, 0.0, 0.0),
        (-10000.0, 5000.0, -7000.0),
        (1e6, -1e6, 1e6),
        (-0.0, -0.0, -0.0),
    ):
        cases.append(
            build_case(f"position {x}/{y}/{z}", link=1, heading=0.0,
                       row_x=x, row_y=y, row_z=z, eye_x=100.0, eye_z=30.0)
        )
    for heading in (-360.0, -180.0, -90.0, -0.5, 0.5, 90.0, 179.5, 180.5,
                    270.0, 359.5, 720.0):
        cases.append(
            build_case(f"sweep heading {heading}", link=1, heading=heading,
                       eye_x=100.0, eye_z=30.0)
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
    print("Testing func_002712d4 (0x002712d4)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
          "(relocations resolved).")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("probe_distance", "constexpr f32 kProbeDistance = 400.0f;",
         "constexpr f32 kProbeDistance = 399.0f;"),
        ("origin_lift", "constexpr f32 kOriginLift = 100.0f;",
         "constexpr f32 kOriginLift = 99.0f;"),
        ("link_offset", "constexpr u32 kRowLinkOffset = 0x38;",
         "constexpr u32 kRowLinkOffset = 0x34;"),
        ("owner_flag_offset", "constexpr u32 kOwnerFlagOffset = 0xE3C;",
         "constexpr u32 kOwnerFlagOffset = 0xE38;"),
        ("state_target_offset", "constexpr u32 kStateTargetOffset = 0xEC;",
         "constexpr u32 kStateTargetOffset = 0xE8;"),
        ("degree_scale", "constexpr f32 kDegToRadians = 0.017453292f;",
         "constexpr f32 kDegToRadians = 0.017453291f;"),
        ("sample_count", "constexpr u32 kSampleCount = 4;",
         "constexpr u32 kSampleCount = 3;"),
        ("step_sign", "angular_delta < 0.0f ? -kStepDegrees : kStepDegrees;",
         "angular_delta <= 0.0f ? -kStepDegrees : kStepDegrees;"),
        ("row_x_offset", "constexpr u32 kRowXOffset = 0x1C;",
         "constexpr u32 kRowXOffset = 0x20;"),
        ("camera_eye_offset", "constexpr u32 kCameraEyeOffset = 0x4C;",
         "constexpr u32 kCameraEyeOffset = 0x50;"),
        ("index_offset", "constexpr u32 kTableIndexOffset = 0xE10;",
         "constexpr u32 kTableIndexOffset = 0xE0C;"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, case)
            try:
                bad = Runner().run(mutant_code, case)
            except RuntimeError:
                # A mutant that faults the emulator has certainly diverged.
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
