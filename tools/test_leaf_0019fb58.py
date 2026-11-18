#!/usr/bin/env python3
"""Differential test for AsdTexTMX_func_0019fb58 (0x0019fb58) with Unicorn ARM."""

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

ORIG_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SOURCE = ROOT / "src" / "engine" / "asd_texture.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_0019fb58"

FUNC_ADDR = 0x0019FB58
FUNC_SIZE = 756

STUB_ALLOC = 0x002C4B84
STUB_FREE = 0x002C4360
STUB_WORK_ALLOC = 0x002C34A4
STUB_GPU_SUBMIT2D = 0x00349A5C

STUB_NAMES = {
    STUB_ALLOC: "AsdMem_Alloc",
    STUB_FREE: "AsdMem_Free",
    STUB_WORK_ALLOC: "AsdWork_Alloc",
    STUB_GPU_SUBMIT2D: "AsdGpu_Submit2D",
}

PTR_TEX = 0x20000000
PTR_TMX = 0x20001000
PTR_GPU_DATA = 0x20008000
PTR_HEAP_BASE = 0x20010000
STACK_BASE = 0x7F000000
STACK_SIZE = 0x10000
STACK_INIT = STACK_BASE + STACK_SIZE - 0x200
LR_SENTINEL = 0x90000000

CALLEE_SAVED = {
    "r4": 0x44444444,
    "r5": 0x55555555,
    "r6": 0x66666666,
    "r7": 0x77777777,
    "r8": 0x88888888,
    "r9": 0x99999999,
    "r10": 0xAAAAAAAA,
    "r11": 0xBBBBBBBB,
}


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def _stub_address(symbol_name: str) -> int | None:
    for addr, name in STUB_NAMES.items():
        if name in symbol_name:
            return addr
    return None


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = next((val for name, val in funcs.items() if "AsdTexTMX_func_0019fb58" in name), None)
    if candidate is None:
        raise RuntimeError(f"AsdTexTMX_func_0019fb58 not found in {obj_file}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        off = rel.offset
        sym_name = rel.symbol_name
        rtype = rel.relocation_type
        if rtype in (28, 29):
            dst = _stub_address(sym_name)
            if dst is None:
                raise RuntimeError(f"Unhandled call relocation: {sym_name}")
            pc = FUNC_ADDR + off + 8
            disp = ((dst - pc) >> 2) & 0x00FFFFFF
            insn = struct.unpack_from("<I", code, off)[0]
            struct.pack_into("<I", code, off, (insn & 0xFF000000) | disp)
        else:
            raise RuntimeError(f"Unhandled relocation type {rtype} for {sym_name}")
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj = OUT_DIR / "asd_texture.o"
    res = compile_tu_armv6k(SOURCE, obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{res.stderr}\n{res.stdout}")
    return relocate_candidate(obj)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"Mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"asd_texture_mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"asd_texture_mutant_{name}.o"
    mutant_src.write_text(text.replace(old, new, 1), encoding="utf-8")
    res = compile_tu_armv6k(mutant_src, mutant_obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant {name} compilation failed:\n{res.stderr}")
    return relocate_candidate(mutant_obj)


def build_tmx(width: int, height: int, fmt: int) -> bytes:
    hdr = bytearray(0x40)
    hdr[0x11] = 0
    struct.pack_into("<HH", hdr, 0x12, width, height)
    hdr[0x16] = fmt
    is_8bit = fmt in (0x13, 0x1B)
    pal_count = 256 if is_8bit else 16
    pal = bytearray()
    for i in range(pal_count):
        a = 0x40 if (i % 2 == 0) else 0x80
        r = (i * 7) & 0xFF
        g = (i * 13 + 3) & 0xFF
        b = (i * 29 + 5) & 0xFF
        pal.extend(struct.pack("<BBBB", b, g, r, a))
    if is_8bit:
        texels = bytes((i * 17 + 5) & 0xFF for i in range(width * height))
    else:
        nbytes = (width * height + 1) // 2 + 1
        texels = bytes((i * 0x35 + 0x12) & 0xFF for i in range(nbytes))
    return bytes(hdr) + bytes(pal) + texels


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(PTR_TEX, 0x00020000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(
        self,
        code: bytes,
        *,
        width: int,
        height: int,
        fmt: int,
        tex_kind: int,
    ) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(0x00100000, ORIG_BIN.read_bytes())
        uc.mem_write(FUNC_ADDR, code)

        uc.mem_write(PTR_TEX, b"\x00" * 0x60)
        uc.mem_write(PTR_TMX, build_tmx(width, height, fmt))

        heap = [PTR_HEAP_BASE]
        allocs: list[int] = []
        freed: list[int] = []
        work_allocs: list[tuple[int, ...]] = []
        submitted: list[tuple[int, int, bytes]] = []

        def ret_arm(val: int | None = None) -> None:
            if val is not None:
                uc.reg_write(arm.UC_ARM_REG_R0, val & 0xFFFFFFFF)
            lr = uc.reg_read(arm.UC_ARM_REG_LR)
            uc.reg_write(arm.UC_ARM_REG_PC, lr & ~1)

        def on_code(uc_inst: unicorn.Uc, address: int, _size: int, _user: object) -> None:
            r0 = uc_inst.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc_inst.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc_inst.reg_read(arm.UC_ARM_REG_R2)
            r3 = uc_inst.reg_read(arm.UC_ARM_REG_R3)
            if address == STUB_ALLOC:
                ptr = heap[0]
                heap[0] += (r3 + 15) & ~15
                uc_inst.mem_write(ptr, b"\x00" * r3)
                allocs.append(r3)
                ret_arm(ptr)
            elif address == STUB_FREE:
                freed.append(r0)
                ret_arm(None)
            elif address == STUB_WORK_ALLOC:
                sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
                a4, a5 = struct.unpack("<II", uc_inst.mem_read(sp, 8))
                work_allocs.append((r0, r1, r2, r3, a4, a5))
                ret_arm(PTR_GPU_DATA)
            elif address == STUB_GPU_SUBMIT2D:
                pix = bytes(uc_inst.mem_read(r2, r0 * r1 * 4))
                submitted.append((r0, r1, pix))
                ret_arm(None)

        hooks = [uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=a, end=a) for a in STUB_NAMES]
        uc.reg_write(arm.UC_ARM_REG_R0, PTR_TEX)
        uc.reg_write(arm.UC_ARM_REG_R1, PTR_TMX)
        uc.reg_write(arm.UC_ARM_REG_R2, 0)
        uc.reg_write(arm.UC_ARM_REG_R3, tex_kind)
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        try:
            uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=5_000_000)
        finally:
            for h in hooks:
                uc.hook_del(h)

        tex_fields = struct.unpack("<IIIIIIIIII", uc.mem_read(PTR_TEX + 4, 40))
        return {
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {r: uc.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
            "tex_fields": tex_fields,
            "allocs": allocs,
            "freed_count": len(freed),
            "work_allocs": work_allocs,
            "submitted": submitted,
        }


def compare(a: dict[str, object], b: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    for k in ("sp", "callee", "tex_fields", "allocs", "freed_count", "work_allocs", "submitted"):
        if a[k] != b[k]:
            diffs.append(f"{k}: {a[k]!r} != {b[k]!r}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes = compile_candidate()

    cases = [
        ("4bit_14_odd", {"width": 3, "height": 2, "fmt": 0x14, "tex_kind": 0x10001}),
        ("4bit_24", {"width": 4, "height": 2, "fmt": 0x24, "tex_kind": 0x10002}),
        ("4bit_2c", {"width": 2, "height": 3, "fmt": 0x2C, "tex_kind": 0x10003}),
        ("8bit_13", {"width": 5, "height": 3, "fmt": 0x13, "tex_kind": 0x10004}),
        ("8bit_1b", {"width": 4, "height": 4, "fmt": 0x1B, "tex_kind": 0x10005}),
        ("unknown_fmt", {"width": 2, "height": 2, "fmt": 0x99, "tex_kind": 0x10006}),
    ]

    for label, kw in cases:
        orig_res = Runner().run(orig_bytes, **kw)
        cand_res = Runner().run(cand_bytes, **kw)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("wrong_4bit_alpha", "alpha = alpha < 0x7Fu ? ((alpha << 1) & 0xFFu) : 0xFFu;", "alpha = alpha & 0xFFu;"),
        ("drop_8bit_swap", "u32 index = (i & 0xE7u) | ((i & 0x10u) >> 1) | ((i & 8u) << 1);", "u32 index = i;"),
        ("wrong_8bit_alpha", "a = a < 0x7Fu ? ((a << 1) & 0xFFu) : 0xFFu;", "a = a & 0xFFu;"),
        ("wrong_format2", "texture->format2 = 0x6752;", "texture->format2 = 0x6753;"),
        ("drop_submit2d", "AsdGpu_Submit2D(width, height, pixels);", ""),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes = compile_candidate_mutant(name, old, new)
        any_diff = False
        for _label, kw in cases:
            if compare(Runner().run(orig_bytes, **kw), Runner().run(mut_bytes, **kw)):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: AsdTexTMX_func_0019fb58 (0x{FUNC_ADDR:08x}) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
