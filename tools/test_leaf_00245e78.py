#!/usr/bin/env python3
"""Differential test for ui_func_00245e78 (0x00245e78) with Unicorn ARM."""

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
SOURCE = ROOT / "src" / "engine" / "leaf_batch45_b.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_00245e78"

FUNC_ADDR = 0x00245E78
FUNC_SIZE = 452

STUB_293C98 = 0x00293C98
STUB_282B94 = 0x00282B94
STUB_2BE7FC = 0x002BE7FC
STUB_23EC3C = 0x0023EC3C

STUB_NAMES = {
    STUB_293C98: "ui_func_00293c98",
    STUB_282B94: "ui_func_00282b94",
    STUB_2BE7FC: "ui_func_002be7fc",
    STUB_23EC3C: "script_vm_func_0023ec3c",
}

RODATA_BASE = 0x18000000
PTR_P = 0x20000000
PTR_ROW1 = 0x20001000
PTR_ROW2 = 0x20002000
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


def _layout_rodata(obj_file: Path) -> tuple[bytes, dict[int, int]]:
    data = obj_file.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 46)
    raw_secs = [struct.unpack_from("<10I", data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr_off = raw_secs[e_shstrndx][4]
    names = [data[shstr_off + s[0] : data.index(b"\x00", shstr_off + s[0])].decode("ascii", errors="replace") for s in raw_secs]

    image = bytearray()
    sec_addr: dict[int, int] = {}
    for i, s in enumerate(raw_secs):
        if s[1] == 1 and (s[2] & 2) and not names[i].startswith(".text"):
            align = max(s[8], 1)
            while len(image) % align:
                image.append(0)
            sec_addr[i] = RODATA_BASE + len(image)
            image.extend(data[s[4] : s[4] + s[5]])

    for i, s in enumerate(raw_secs):
        if s[1] == 9 and s[7] in sec_addr:
            target_off = sec_addr[s[7]] - RODATA_BASE
            symtab = raw_secs[s[6]]
            for k in range(s[5] // 8):
                r_off, r_info = struct.unpack_from("<II", data, s[4] + k * 8)
                sym_idx, r_type = r_info >> 8, r_info & 0xFF
                if r_type == 2:
                    st_shndx = struct.unpack_from("<H", data, symtab[4] + sym_idx * 16 + 14)[0]
                    if st_shndx in sec_addr:
                        val = struct.unpack_from("<I", image, target_off + r_off)[0]
                        struct.pack_into("<I", image, target_off + r_off, sec_addr[st_shndx] + val)

    return bytes(image), sec_addr


def relocate_candidate(obj_file: Path) -> tuple[bytes, bytes]:
    rodata, sec_addr = _layout_rodata(obj_file)
    data = obj_file.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 46)
    raw_secs = [struct.unpack_from("<10I", data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr_off = raw_secs[e_shstrndx][4]
    names = [data[shstr_off + s[0] : data.index(b"\x00", shstr_off + s[0])].decode("ascii", errors="replace") for s in raw_secs]
    tidx = next(i for i, n in enumerate(names) if n.startswith(".text"))
    rel_sec = next(s for s in raw_secs if s[1] == 9 and s[7] == tidx)
    symtab = raw_secs[rel_sec[6]]
    strtab = raw_secs[symtab[6]]
    fn_off = 0
    for k in range(symtab[5] // 16):
        st_name, st_val, _sz, _inf, _oth, st_sh = struct.unpack_from("<IIIBBH", data, symtab[4] + k * 16)
        if st_sh == tidx:
            nm = data[strtab[4] + st_name : data.index(b"\x00", strtab[4] + st_name)].decode("ascii", errors="replace")
            if "ui_func_00245e78" in nm:
                fn_off = st_val
                break
    rel_sym_shndx = {
        struct.unpack_from("<I", data, rel_sec[4] + k * 8)[0] - fn_off: struct.unpack_from("<H", data, symtab[4] + (struct.unpack_from("<I", data, rel_sec[4] + k * 8 + 4)[0] >> 8) * 16 + 14)[0]
        for k in range(rel_sec[5] // 8)
    }

    funcs = extract_elf_functions_detailed(obj_file)
    candidate = next((val for name, val in funcs.items() if "ui_func_00245e78" in name), None)
    if candidate is None:
        raise RuntimeError(f"ui_func_00245e78 not found in {obj_file}")

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
        elif rtype == 2:
            shndx = rel_sym_shndx[off]
            if shndx in sec_addr:
                addend = struct.unpack_from("<I", code, off)[0]
                struct.pack_into("<I", code, off, sec_addr[shndx] + addend)
            else:
                raise RuntimeError(f"Unhandled ABS32 relocation: {sym_name}")
        else:
            raise RuntimeError(f"Unhandled relocation type {rtype} for {sym_name}")
    return bytes(code), rodata


def compile_candidate() -> tuple[bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj = OUT_DIR / "leaf_batch45_b.o"
    res = compile_tu_armv6k(SOURCE, obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{res.stderr}\n{res.stdout}")
    return relocate_candidate(obj)


def compile_candidate_mutant(name: str, old: str, new: str) -> tuple[bytes, bytes]:
    text = SOURCE.read_text(encoding="utf-8")
    fs = text.index("extern \"C\" u32 ui_func_00245e78(")
    fe = text.index("\n}\n", fs) + 3
    body = text[fs:fe]
    if body.count(old) != 1:
        raise RuntimeError(f"Mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"leaf_batch45_b_mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"leaf_batch45_b_mutant_{name}.o"
    mutant_src.write_text(text[:fs] + body.replace(old, new, 1) + text[fe:], encoding="utf-8")
    res = compile_tu_armv6k(mutant_src, mutant_obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant {name} compilation failed:\n{res.stderr}")
    return relocate_candidate(mutant_obj)


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(RODATA_BASE, 0x00010000)
        self.uc.mem_map(PTR_P, 0x00010000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(
        self,
        code: bytes,
        rodata: bytes,
        *,
        kind: int,
        stat: int,
        row2_ok: bool,
        bonus: int,
        roll: int,
    ) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(0x00100000, ORIG_BIN.read_bytes())
        uc.mem_write(FUNC_ADDR, code)
        if rodata:
            uc.mem_write(RODATA_BASE, rodata)

        uc.mem_write(PTR_ROW1, b"\x00" * 0x200)
        uc.mem_write(PTR_ROW1 + 0x1C4, struct.pack("<h", stat))
        uc.mem_write(PTR_ROW2, b"\x00" * 0x100)
        for slot in (0x16, 0x17, 0x18, 0x19):
            uc.mem_write(PTR_ROW2 + 0x72 + slot * 2, struct.pack("<h", bonus))

        calls: list[tuple[str, tuple[object, ...]]] = []
        row_seq = [0]

        def ret_arm(val: int | None = None) -> None:
            if val is not None:
                uc.reg_write(arm.UC_ARM_REG_R0, val & 0xFFFFFFFF)
            lr = uc.reg_read(arm.UC_ARM_REG_LR)
            cpsr = uc.reg_read(arm.UC_ARM_REG_CPSR)
            uc.reg_write(arm.UC_ARM_REG_CPSR, cpsr & ~0x20)
            uc.reg_write(arm.UC_ARM_REG_PC, lr & ~1)

        def on_code(uc_inst: unicorn.Uc, address: int, _size: int, _user: object) -> None:
            r0 = uc_inst.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc_inst.reg_read(arm.UC_ARM_REG_R1)
            if address == STUB_293C98:
                calls.append(("293c98", ()))
                ret_arm(PTR_P)
            elif address == STUB_282B94:
                calls.append(("282b94", (r0, r1)))
                idx = row_seq[0]
                row_seq[0] += 1
                ret_arm(PTR_ROW1 if idx == 0 else (PTR_ROW2 if row2_ok else 0))
            elif address == STUB_2BE7FC:
                fmt = bytes(uc_inst.mem_read(r1, 8)).split(b"\x00", 1)[0]
                calls.append(("2be7fc", (fmt,)))
                ret_arm(len(fmt))
            elif address == STUB_23EC3C:
                calls.append(("23ec3c", (r0,)))
                ret_arm(roll)

        hooks = [uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=a, end=a) for a in STUB_NAMES]
        uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        uc.reg_write(arm.UC_ARM_REG_R0, 5)
        uc.reg_write(arm.UC_ARM_REG_R1, kind)
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        try:
            uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=5_000_000)
        finally:
            for h in hooks:
                uc.hook_del(h)

        return {
            "ret": uc.reg_read(arm.UC_ARM_REG_R0),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {r: uc.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
            "calls": calls,
        }


def compare(a: dict[str, object], b: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    for k in ("ret", "sp", "callee", "calls"):
        if a[k] != b[k]:
            diffs.append(f"{k}: {a[k]!r} != {b[k]!r}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes, cand_rodata = compile_candidate()

    cases = [
        ("invalid_kind", {"kind": 4, "stat": 10, "row2_ok": True, "bonus": 0, "roll": 0}),
        ("k3_pass", {"kind": 3, "stat": 100, "row2_ok": True, "bonus": 1, "roll": 29}),
        ("k3_fail", {"kind": 3, "stat": 100, "row2_ok": True, "bonus": 1, "roll": 30}),
        ("k6_clamp80", {"kind": 6, "stat": 400, "row2_ok": False, "bonus": 0, "roll": 80}),
        ("k6_base_edge", {"kind": 6, "stat": 0, "row2_ok": False, "bonus": 0, "roll": 25}),
        ("k7_hit", {"kind": 7, "stat": 50, "row2_ok": True, "bonus": 1, "roll": 64}),
        ("k8_miss", {"kind": 8, "stat": 0, "row2_ok": True, "bonus": 0, "roll": 20}),
    ]

    for label, kw in cases:
        orig_res = Runner().run(orig_bytes, b"", **kw)
        cand_res = Runner().run(cand_bytes, cand_rodata, **kw)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("wrong_k6_base", "base = 25.0f;", "base = 26.0f;"),
        ("drop_clamp", "if (rate > 80.0f) {\n        rate = 80.0f;\n    }", ""),
        ("wrong_bonus_mult", "rate += static_cast<f32>(bonus) * 20.0f;", "rate += static_cast<f32>(bonus) * 10.0f;"),
        ("wrong_k7_fmt", 'fmt = "\\x90\\x87\\x96\\xb0";', 'fmt = "\\x8d\\xac\\x97\\x90";'),
        ("flip_roll_cmp", "return (static_cast<f32>(roll) >= rate) ? 0u : 1u;", "return (static_cast<f32>(roll) > rate) ? 0u : 1u;"),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes, mut_rodata = compile_candidate_mutant(name, old, new)
        any_diff = False
        for _label, kw in cases:
            if compare(Runner().run(orig_bytes, b"", **kw), Runner().run(mut_bytes, mut_rodata, **kw)):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: ui_func_00245e78 (0x{FUNC_ADDR:08x}) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
