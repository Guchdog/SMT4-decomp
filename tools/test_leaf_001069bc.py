#!/usr/bin/env python3
"""Differential test for engine_func_001069bc (0x001069bc) using Unicorn ARM.

The original function is straight-line: it constructs the projection block,
queries two screen dimensions, stores six floats at camera+0x4A0, writes five
scalar fields around camera+0x508, builds a 3x4 basis matrix from p0, calls the
camera basis helper, sets the clip range, and registers the camera globally.

Every direct call is replaced with a deterministic stub so the original and the
compiled C++ candidate can be compared on call order/arguments, the 0x30-byte
matrix handed to the basis helper, return/PC/SP, callee-saved registers, and the
object memory they write.
"""

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
FUNC_ADDR = 0x001069BC
FUNC_SIZE = 400

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers 0x00100000..0x00300000 (all stub addresses)
OBJ_ADDR = 0x00500000
OBJ_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

STUB_INIT = 0x002C2210        # engine_func_002c2210(camera, mode)
STUB_SCREEN_A = 0x002C17AC    # engine_func_002c17ac(index)
STUB_SCREEN_B = 0x002C1784    # engine_func_002c1784(index)
STUB_SIX_FLOATS = 0x0011CFFC  # func_0011cffc(camera, s0..s5)
STUB_BASIS = 0x0011CFA4       # func_0011cfa4(camera, mtx34)
STUB_CLIP = 0x002C1774        # ui_func_002c1774(camera, s0, s1)
STUB_REGISTER = 0x002C1740    # battle_func_002c1740(camera)

STUB_BY_SYMBOL = {
    "engine_func_002c2210": STUB_INIT,
    "engine_func_002c17ac": STUB_SCREEN_A,
    "engine_func_002c1784": STUB_SCREEN_B,
    "func_0011cffc": STUB_SIX_FLOATS,
    "func_0011cfa4": STUB_BASIS,
    "ui_func_002c1774": STUB_CLIP,
    "battle_func_002c1740": STUB_REGISTER,
}


def f2b(value):
    return struct.unpack("<I", struct.pack("<f", value))[0]


def b2f(bits):
    return struct.unpack("<f", struct.pack("<I", bits))[0]


def get_orig_bytes():
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def get_symbol_offset(obj_file, sym_name):
    data = Path(obj_file).read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize = struct.unpack_from("<H", data, 46)[0]
    e_shnum = struct.unpack_from("<H", data, 48)[0]
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    symtab = [s for s in sections if s[1] == 2][0]
    for i in range(symtab[5] // 16):
        st_name, st_val, st_size, st_info, st_other, st_shndx = struct.unpack_from(
            "<IIIBBH", data, symtab[4] + i * 16
        )
        name = data[sections[symtab[6]][4] + st_name:].split(b"\x00")[0]
        if name.decode("ascii", errors="replace") == sym_name:
            return st_val
    return 0


def compile_candidate_from(src_file, obj_file):
    res = compile_tu_armv6k(src_file, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")

    funcs = extract_elf_functions_detailed(obj_file)
    entry = funcs.get("engine_func_001069bc")
    if entry is None:
        raise RuntimeError(
            "engine_func_001069bc not found in object: " + ", ".join(sorted(funcs))
        )

    code = bytearray(entry[0])
    relocs = entry[1]
    func_sym_offset = get_symbol_offset(obj_file, "engine_func_001069bc")
    errors = []
    for rel in relocs:
        if rel.relocation_type not in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            errors.append(f"unexpected relocation {rel.relocation_type} {rel.symbol_name}")
            continue
        target = STUB_BY_SYMBOL.get(rel.symbol_name)
        if target is None:
            errors.append(f"no stub for {rel.symbol_name}")
            continue
        pc = FUNC_ADDR + rel.offset + 8
        disp = (target - pc) >> 2
        orig_inst = struct.unpack_from("<I", code, rel.offset)[0]
        cond = orig_inst & 0xFF000000
        struct.pack_into("<I", code, rel.offset, cond | (disp & 0x00FFFFFF))
    if errors:
        raise RuntimeError("; ".join(errors))
    if func_sym_offset == 0:
        raise RuntimeError("missing symbol offset for engine_func_001069bc")

    return bytes(code)


def compile_candidate():
    out_dir = ROOT / "build/test_leaf_001069bc"
    out_dir.mkdir(parents=True, exist_ok=True)
    return compile_candidate_from(
        ROOT / "src/engine/leaf_batch28_a.cpp",
        out_dir / "engine" / "leaf_batch28_a.o",
    )


def compile_mutant(name, old, new):
    out_dir = ROOT / "build/test_leaf_001069bc"
    out_dir.mkdir(parents=True, exist_ok=True)
    source = ROOT / "src/engine/leaf_batch28_a.cpp"
    text = source.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = out_dir / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    return compile_candidate_from(mutant_src, out_dir / f"mutant_{name}.o")


class Runner:
    def __init__(self):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(OBJ_ADDR, OBJ_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        self.call_log = []
        self.screen_a = 640
        self.screen_b = 480

        bx_lr = struct.pack("<I", 0xE12FFF1E)
        stubs = [
            (STUB_INIT, self._on_init),
            (STUB_SCREEN_A, self._on_screen_a),
            (STUB_SCREEN_B, self._on_screen_b),
            (STUB_SIX_FLOATS, self._on_six_floats),
            (STUB_BASIS, self._on_basis),
            (STUB_CLIP, self._on_clip),
            (STUB_REGISTER, self._on_register),
        ]
        for address, hook in stubs:
            self.uc.mem_write(address, bx_lr)
            self.uc.hook_add(unicorn.UC_HOOK_CODE, hook, begin=address, end=address)

        # Enable the VFP coprocessor (CP10/CP11) and the floating-point unit.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.reg_write(arm.UC_ARM_REG_FPSCR, 0)

    def _f32_reg(self, reg):
        return self.uc.reg_read(reg)

    def _on_init(self, uc, address, size, user_data):
        self.call_log.append(
            ("engine_func_002c2210", uc.reg_read(arm.UC_ARM_REG_R0),
             uc.reg_read(arm.UC_ARM_REG_R1))
        )

    def _on_screen_a(self, uc, address, size, user_data):
        self.call_log.append(("engine_func_002c17ac", uc.reg_read(arm.UC_ARM_REG_R0)))
        uc.reg_write(arm.UC_ARM_REG_R0, self.screen_a)

    def _on_screen_b(self, uc, address, size, user_data):
        self.call_log.append(("engine_func_002c1784", uc.reg_read(arm.UC_ARM_REG_R0)))
        uc.reg_write(arm.UC_ARM_REG_R0, self.screen_b)

    def _on_six_floats(self, uc, address, size, user_data):
        args = [uc.reg_read(arm.UC_ARM_REG_S0 + i) for i in range(6)]
        self.call_log.append(
            ("func_0011cffc", uc.reg_read(arm.UC_ARM_REG_R0), *args)
        )

    def _on_basis(self, uc, address, size, user_data):
        camera = uc.reg_read(arm.UC_ARM_REG_R0)
        matrix_ptr = uc.reg_read(arm.UC_ARM_REG_R1)
        matrix = bytes(uc.mem_read(matrix_ptr, 0x30))
        self.call_log.append(("func_0011cfa4", camera, matrix.hex()))

    def _on_clip(self, uc, address, size, user_data):
        args = [uc.reg_read(arm.UC_ARM_REG_S0 + i) for i in range(2)]
        self.call_log.append(("ui_func_002c1774", uc.reg_read(arm.UC_ARM_REG_R0), *args))

    def _on_register(self, uc, address, size, user_data):
        self.call_log.append(("battle_func_002c1740", uc.reg_read(arm.UC_ARM_REG_R0)))

    def run(self, code_bytes, screen_a, screen_b, p0, p1, p2, p3):
        self.call_log = []
        self.screen_a = screen_a
        self.screen_b = screen_b

        self.uc.mem_write(FUNC_ADDR, code_bytes)
        # Unicorn caches translated blocks; overwriting code at the same
        # addresses requires an explicit flush between original/mutant runs.
        self.uc.ctl_remove_cache(FUNC_ADDR, FUNC_ADDR + 0x1000)
        self.uc.mem_write(OBJ_ADDR, b"\x5a" * OBJ_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        sp = STACK_ADDR + STACK_SIZE - 0x100
        self.uc.reg_write(arm.UC_ARM_REG_SP, sp)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, OBJ_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_S0, p0)
        self.uc.reg_write(arm.UC_ARM_REG_S1, p1)
        self.uc.reg_write(arm.UC_ARM_REG_S2, p2)
        self.uc.reg_write(arm.UC_ARM_REG_S3, p3)

        # Callee-saved sentinels: the ABI requires them to survive the call.
        for index, reg in enumerate(
            [
                arm.UC_ARM_REG_R4, arm.UC_ARM_REG_R5, arm.UC_ARM_REG_R6,
                arm.UC_ARM_REG_R7, arm.UC_ARM_REG_R8, arm.UC_ARM_REG_R9,
                arm.UC_ARM_REG_R10, arm.UC_ARM_REG_R11,
            ]
        ):
            self.uc.reg_write(reg, 0x11110000 + index * 0x11)
        for index in range(16, 32):
            self.uc.reg_write(
                getattr(arm, f"UC_ARM_REG_S{index}"), 0x3F000000 + index
            )

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5000000)
        except unicorn.UcError as exc:
            raise RuntimeError(
                f"Crash at PC=0x{self.uc.reg_read(arm.UC_ARM_REG_PC):08x}: {exc}"
            )

        return {
            "call_log": list(self.call_log),
            "object": bytes(self.uc.mem_read(OBJ_ADDR, 0x600)),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "r0": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "r1": self.uc.reg_read(arm.UC_ARM_REG_R1),
            "callee_saved": [
                self.uc.reg_read(reg)
                for reg in [
                    arm.UC_ARM_REG_R4, arm.UC_ARM_REG_R5, arm.UC_ARM_REG_R6,
                    arm.UC_ARM_REG_R7, arm.UC_ARM_REG_R8, arm.UC_ARM_REG_R9,
                    arm.UC_ARM_REG_R10, arm.UC_ARM_REG_R11,
                ]
            ],
            "callee_saved_vfp": [
                self.uc.reg_read(getattr(arm, f"UC_ARM_REG_S{i}"))
                for i in range(16, 32)
            ],
        }


def main():
    print("Testing engine_func_001069bc (0x001069bc)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()

    runner = Runner()

    cases = [
        {
            "name": "boot call (0.25, 0.2, 1.0, 1.0), 640x480",
            "screen_a": 640, "screen_b": 480,
            "p0": f2b(0.25), "p1": f2b(0.2), "p2": f2b(1.0), "p3": f2b(1.0),
        },
        {
            "name": "negative p0 (-0.25), negative p1, 1920x1080",
            "screen_a": 1920, "screen_b": 1080,
            "p0": f2b(-0.25), "p1": f2b(-1.5), "p2": f2b(2.5), "p3": f2b(100.0),
        },
        {
            "name": "zero screen dimensions, small p0 (0.001), far=0",
            "screen_a": 0, "screen_b": 0,
            "p0": f2b(0.001), "p1": f2b(1.0), "p2": f2b(-1.0), "p3": f2b(0.0),
        },
        {
            "name": "unsigned screen boundary (0x80000000 / 0xFFFFFFFF)",
            "screen_a": 0x80000000, "screen_b": 0xFFFFFFFF,
            "p0": f2b(100.0), "p1": f2b(3.5), "p2": 0x7FC00001, "p3": f2b(1.0e-3),
        },
        {
            "name": "unit p0, zero p1/p2, 4000x3000",
            "screen_a": 4000, "screen_b": 3000,
            "p0": f2b(1.0), "p1": f2b(0.0), "p2": f2b(0.0), "p3": f2b(30.0),
        },
        {
            "name": "large p0 (4096.0), negative zero p3",
            "screen_a": 1, "screen_b": 0x7FFFFFFF,
            "p0": f2b(4096.0), "p1": f2b(1.0e-30), "p2": f2b(-1.0e30),
            "p3": 0x80000000,
        },
    ]

    passed = 0
    for case in cases:
        res_orig = runner.run(
            orig_code, case["screen_a"], case["screen_b"],
            case["p0"], case["p1"], case["p2"], case["p3"],
        )
        res_cand = runner.run(
            cand_code, case["screen_a"], case["screen_b"],
            case["p0"], case["p1"], case["p2"], case["p3"],
        )

        assert res_orig["call_log"] == res_cand["call_log"], (
            f"Call log mismatch on {case['name']}:\n"
            f"  Orig: {res_orig['call_log']}\n  Cand: {res_cand['call_log']}"
        )
        assert res_orig["object"] == res_cand["object"], (
            f"Object memory mismatch on {case['name']}"
        )
        assert res_orig["sp"] == res_cand["sp"], (
            f"SP mismatch on {case['name']}: {res_orig['sp']:#x} vs {res_cand['sp']:#x}"
        )
        assert res_orig["pc"] == res_cand["pc"] == TRAP_ADDR, (
            f"PC mismatch on {case['name']}: {res_orig['pc']:#x} vs {res_cand['pc']:#x}"
        )
        assert res_orig["callee_saved"] == res_cand["callee_saved"], (
            f"callee-saved register mismatch on {case['name']}"
        )
        assert res_orig["callee_saved_vfp"] == res_cand["callee_saved_vfp"], (
            f"callee-saved VFP register mismatch on {case['name']}"
        )

        # The entry SP is restored; check both runs agree with it.
        entry_sp = STACK_ADDR + STACK_SIZE - 0x100
        assert res_orig["sp"] == entry_sp, f"stack not restored on {case['name']}"

        passed += 1
        print(f"  [PASS] {case['name']}")

    print("\nNegative controls:")
    mutants = [
        (
            "signed screen conversion",
            "static_cast<f32>(engine_func_002c17ac(0))",
            "static_cast<f32>(static_cast<s32>(engine_func_002c17ac(0)))",
        ),
        (
            "swapped clip arguments",
            "ui_func_002c1774(camera, p0, p3);",
            "ui_func_002c1774(camera, p3, p0);",
        ),
        (
            "basis translation sign",
            "0.0f, 0.0f, axis, -(p0 * axis),",
            "0.0f, 0.0f, axis, p0 * axis,",
        ),
    ]
    for name, old, new in mutants:
        mutant_code = compile_mutant(name.replace(" ", "_"), old, new)
        detected = False
        for case in cases:
            res_orig = runner.run(
                orig_code, case["screen_a"], case["screen_b"],
                case["p0"], case["p1"], case["p2"], case["p3"],
            )
            res_mut = runner.run(
                mutant_code, case["screen_a"], case["screen_b"],
                case["p0"], case["p1"], case["p2"], case["p3"],
            )
            if res_orig != res_mut:
                detected = True
                break
        assert detected, f"negative control not detected: {name}"
        print(f"  [PASS] mutant detected: {name}")

    print(f"\nAll {passed}/{len(cases)} differential test cases PASSED!")


if __name__ == "__main__":
    main()
