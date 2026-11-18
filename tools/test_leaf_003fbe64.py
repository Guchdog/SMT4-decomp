#!/usr/bin/env python3
"""Differential test for func_003fbe64 (0x003FBE64) using Unicorn ARM."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
SRC_CPP = ROOT / "src/engine/leaf_batch45_a.cpp"
FUNC_ADDR = 0x003FBE64
FUNC_SIZE = 920
FUNC_NAME = "func_003fbe64"

STUB_BASE = 0x00110000
RODATA_BASE = 0x00120000
MEM_BASE = 0x20000000
MEM_SIZE = 0x00020000
SELF_ADDR = 0x20000000
ALLOC_ADDR = 0x20001000
OLD_DATA_ADDR = 0x20002000
NEW_BUF1_ADDR = 0x20003000
NEW_BUF2_ADDR = 0x20004000
ITEM_ADDR = 0x20005000
HEAD_ADDR = 0x20006000
OWNER_ADDR = 0x20007000
STACK_TOP = 0x2001E000
TRAP_ADDR = 0x001F0000

STUB_ALLOC0 = STUB_BASE + 0x00
STUB_FREE = STUB_BASE + 0x04
STUB_ALLOC2 = STUB_BASE + 0x08
STUB_OWNER_REL = STUB_BASE + 0x0C

CALLEES = {
    0x0022C968: ("func_0022c968", 3),
    0x0022C198: ("func_0022c198", 2),
}

STUB_ADDRS = {addr: STUB_BASE + 0x40 + idx * 4 for idx, addr in enumerate(sorted(CALLEES))}
ADDR_BY_STUB = {v: k for k, v in STUB_ADDRS.items()}
NAME_TO_STUB = {CALLEES[k][0]: v for k, v in STUB_ADDRS.items()}


def patch_orig_code(raw: bytes) -> bytearray:
    code = bytearray(raw)
    for off in range(0, len(code), 4):
        insn = struct.unpack_from("<I", code, off)[0]
        cond = (insn >> 28) & 0xF
        op = (insn >> 24) & 0xF
        if cond != 0xF and op in (0xA, 0xB):
            imm24 = insn & 0x00FFFFFF
            if imm24 & 0x00800000:
                imm24 -= 0x01000000
            pc = FUNC_ADDR + off
            target = pc + 8 + (imm24 << 2)
            if target in STUB_ADDRS:
                new_imm = ((STUB_ADDRS[target] - (pc + 8)) >> 2) & 0x00FFFFFF
                struct.pack_into("<I", code, off, (insn & 0xFF000000) | new_imm)
    return code


def patch_cand_elf(obj_path: Path) -> tuple[bytearray, list[tuple[int, bytes]]]:
    elf = obj_path.read_bytes()
    e_shoff = struct.unpack_from("<I", elf, 0x20)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", elf, 0x2E)
    sections = [struct.unpack_from("<10I", elf, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr_off = sections[e_shstrndx][4]

    def sec_name(idx: int) -> str:
        n_off = shstr_off + sections[idx][0]
        return elf[n_off : elf.find(b"\x00", n_off)].decode("ascii", errors="replace")

    symtab = next(sh for sh in sections if sh[1] == 2)
    strtab = sections[symtab[6]]
    str_off = strtab[4]

    def sym_info(sym_idx: int) -> tuple[str, int, int]:
        s_off = symtab[4] + sym_idx * 16
        st_name, st_value, _, _, _, st_shndx = struct.unpack_from("<IIIBBH", elf, s_off)
        end = elf.find(b"\x00", str_off + st_name)
        return elf[str_off + st_name : end].decode("ascii", errors="replace"), st_value, st_shndx

    func_val = func_size = func_shndx = None
    for idx in range(symtab[5] // 16):
        name, val, shndx = sym_info(idx)
        if name == FUNC_NAME:
            func_val = val
            func_size = struct.unpack_from("<I", elf, symtab[4] + idx * 16 + 8)[0]
            func_shndx = shndx
            break
    assert func_val is not None and func_size is not None and func_shndx is not None

    text_sh = sections[func_shndx]
    code = bytearray(elf[text_sh[4] + func_val : text_sh[4] + func_val + func_size])

    rodata_blob = bytearray()
    rodata_map: dict[int, int] = {}
    for idx, sh in enumerate(sections):
        if sec_name(idx).startswith(".rodata"):
            rodata_map[idx] = RODATA_BASE + len(rodata_blob)
            rodata_blob.extend(elf[sh[4] : sh[4] + sh[5]])
            while len(rodata_blob) % 4 != 0:
                rodata_blob.append(0)

    for sh in sections:
        if sh[1] == 9 and sh[7] == func_shndx:
            for pos in range(sh[4], sh[4] + sh[5], 8):
                r_off, r_info = struct.unpack_from("<II", elf, pos)
                if not (func_val <= r_off < func_val + func_size):
                    continue
                c_off = r_off - func_val
                r_type = r_info & 0xFF
                s_name, _, s_shndx = sym_info(r_info >> 8)
                if r_type in (28, 29):
                    insn = struct.unpack_from("<I", code, c_off)[0]
                    cond = (insn >> 28) & 0xF
                    op = (insn >> 24) & 0xF
                    link = op == 0xB
                    target = NAME_TO_STUB[s_name]
                    pc = FUNC_ADDR + c_off
                    imm24 = ((target - (pc + 8)) >> 2) & 0x00FFFFFF
                    struct.pack_into("<I", code, c_off, (cond << 28) | ((0xB if link else 0xA) << 24) | imm24)
                elif r_type == 2:
                    addend = struct.unpack_from("<I", code, c_off)[0]
                    if s_shndx == func_shndx:
                        struct.pack_into("<I", code, c_off, (FUNC_ADDR - func_val) + addend)
                    elif s_shndx in rodata_map:
                        struct.pack_into("<I", code, c_off, rodata_map[s_shndx] + addend)
                    else:
                        raise RuntimeError(f"Unexpected R_ARM_ABS32 section {s_shndx} ({s_name})")
                else:
                    raise RuntimeError(f"Unsupported reloc {r_type} for {s_name}")
    rodata_blobs = [(RODATA_BASE, bytes(rodata_blob))] if rodata_blob else []
    return code, rodata_blobs


class Runner:
    def __init__(self, code: bytes, rodata_blobs: list[tuple[int, bytes]] | None = None):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(MEM_BASE, MEM_SIZE)
        self.uc.mem_write(FUNC_ADDR, bytes(code))
        if rodata_blobs:
            for addr, blob in rodata_blobs:
                self.uc.mem_write(addr, blob)
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE7FFDEFE))

    def run(
        self,
        cap: int,
        size: int,
        cap1_ret: int,
        alloc0_ok: bool = True,
        alloc2_ok: bool = True,
        fallback_ok: bool = True,
        linked_elem: bool = True,
    ) -> dict:
        self.uc.mem_write(SELF_ADDR, struct.pack("<IIII", ALLOC_ADDR, OLD_DATA_ADDR, cap, size))
        # Allocator vtable at ALLOC_ADDR + 0x40
        alloc_buf = bytearray(0x60)
        struct.pack_into("<I", alloc_buf, 0x00, ALLOC_ADDR + 0x40)
        struct.pack_into("<I", alloc_buf, 0x40, STUB_ALLOC0)
        struct.pack_into("<I", alloc_buf, 0x44, STUB_FREE)
        struct.pack_into("<I", alloc_buf, 0x48, STUB_ALLOC2)
        self.uc.mem_write(ALLOC_ADDR, bytes(alloc_buf))

        # Owner vtable at OWNER_ADDR + 0x40
        owner_buf = bytearray(0x60)
        struct.pack_into("<I", owner_buf, 0x00, OWNER_ADDR + 0x40)
        struct.pack_into("<I", owner_buf, 0x44, STUB_OWNER_REL)
        self.uc.mem_write(OWNER_ADDR, bytes(owner_buf))

        # Old data elements
        old_buf = bytearray(0x100)
        for i in range(size):
            off = i * 0x10
            elem_addr = OLD_DATA_ADDR + off
            prev_p = HEAD_ADDR if linked_elem else 0
            next_p = HEAD_ADDR
            struct.pack_into("<IIII", old_buf, off, OWNER_ADDR, 0x100 + i, prev_p, next_p)
        self.uc.mem_write(OLD_DATA_ADDR, bytes(old_buf))
        self.uc.mem_write(NEW_BUF1_ADDR, b"\x00" * 0x100)
        self.uc.mem_write(NEW_BUF2_ADDR, b"\x00" * 0x100)

        # Item and head
        self.uc.mem_write(ITEM_ADDR, struct.pack("<IIII", OWNER_ADDR, 0x999, 0, HEAD_ADDR))
        self.uc.mem_write(HEAD_ADDR, struct.pack("<IIII", 0, 0, ITEM_ADDR, 0))

        trace: list[tuple] = []
        alloc_calls = 0

        def on_code(uc: unicorn.Uc, addr: int, size_insn: int, user_data: object) -> None:
            nonlocal alloc_calls
            if addr == TRAP_ADDR:
                uc.emu_stop()
                return
            if addr == STUB_ALLOC0:
                alloc_calls += 1
                sz = uc.reg_read(arm.UC_ARM_REG_R1)
                trace.append(("alloc0", uc.reg_read(arm.UC_ARM_REG_R0), sz))
                if alloc_calls == 1:
                    uc.reg_write(arm.UC_ARM_REG_R0, NEW_BUF1_ADDR if alloc0_ok else 0)
                else:
                    uc.reg_write(arm.UC_ARM_REG_R0, NEW_BUF2_ADDR if fallback_ok else 0)
                uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))
                return
            if addr == STUB_ALLOC2:
                trace.append((
                    "alloc2",
                    uc.reg_read(arm.UC_ARM_REG_R0),
                    uc.reg_read(arm.UC_ARM_REG_R1),
                    uc.reg_read(arm.UC_ARM_REG_R2),
                ))
                uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))
                return
            if addr == STUB_FREE:
                trace.append(("free", uc.reg_read(arm.UC_ARM_REG_R0), uc.reg_read(arm.UC_ARM_REG_R1)))
                uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))
                return
            if addr == STUB_OWNER_REL:
                trace.append(("owner_rel", uc.reg_read(arm.UC_ARM_REG_R0), uc.reg_read(arm.UC_ARM_REG_R1)))
                uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))
                return
            if addr not in ADDR_BY_STUB:
                return
            target = ADDR_BY_STUB[addr]
            name, nargs = CALLEES[target]
            regs = (arm.UC_ARM_REG_R0, arm.UC_ARM_REG_R1, arm.UC_ARM_REG_R2)
            args = tuple(uc.reg_read(regs[i]) for i in range(nargs))
            trace.append((name, args))
            if name == "func_0022c198":
                uc.reg_write(arm.UC_ARM_REG_R0, cap1_ret)
            uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))

        hook = self.uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
        try:
            self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
            self.uc.reg_write(arm.UC_ARM_REG_R1, ITEM_ADDR)
            self.uc.reg_write(arm.UC_ARM_REG_R2, OLD_DATA_ADDR + size * 0x10)
            self.uc.reg_write(arm.UC_ARM_REG_SP, STACK_TOP)
            self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=100000)
        finally:
            self.uc.hook_del(hook)

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "self": bytes(self.uc.mem_read(SELF_ADDR, 16)),
            "old_data": bytes(self.uc.mem_read(OLD_DATA_ADDR, 0x40)),
            "new_buf1": bytes(self.uc.mem_read(NEW_BUF1_ADDR, 0x40)),
            "new_buf2": bytes(self.uc.mem_read(NEW_BUF2_ADDR, 0x40)),
            "item": bytes(self.uc.mem_read(ITEM_ADDR, 16)),
            "head": bytes(self.uc.mem_read(HEAD_ADDR, 16)),
            "trace": trace,
        }


def build_cases() -> list[tuple[str, dict]]:
    return [
        ("in_place_has_cap", {"cap": 4, "size": 2, "cap1_ret": 4}),
        ("grow_cap1_alloc0_linked", {"cap": 2, "size": 2, "cap1_ret": 4, "alloc0_ok": True, "linked_elem": True}),
        ("grow_cap1_alloc0_unlinked", {"cap": 2, "size": 2, "cap1_ret": 4, "alloc0_ok": True, "linked_elem": False}),
        ("grow_cap1_alloc2_fallback", {"cap": 2, "size": 2, "cap1_ret": 4, "alloc0_ok": False, "alloc2_ok": True}),
        ("grow_fallback_new_size", {"cap": 2, "size": 2, "cap1_ret": 8, "alloc0_ok": False, "alloc2_ok": False, "fallback_ok": True}),
        ("grow_all_oom", {"cap": 2, "size": 2, "cap1_ret": 8, "alloc0_ok": False, "alloc2_ok": False, "fallback_ok": False}),
    ]


def run_suite(orig_code: bytes, cand_code: bytes, rodata_blobs: list[tuple[int, bytes]]) -> list[str]:
    failures: list[str] = []
    for name, kwargs in build_cases():
        orig = Runner(orig_code).run(**kwargs)
        cand = Runner(cand_code, rodata_blobs).run(**kwargs)
        if orig != cand:
            failures.append(f"{name}: orig_ret={orig['ret']} cand_ret={cand['ret']}")
    return failures


def run_negative_controls(orig_code: bytes, cpp_text: str, work_dir: Path) -> None:
    mutations = [
        ("wrong_tag_const", "0x0040FF98u", "0x0040FF9Cu"),
        ("wrong_size_inc", "self->size = new_size;", "self->size = size;"),
        ("wrong_oom_ret", "reinterpret_cast<FreeFn>(vtbl[1])(alloc, nullptr);\n                    return 0u;", "reinterpret_cast<FreeFn>(vtbl[1])(alloc, nullptr);\n                    return 1u;"),
        ("wrong_shift_bytes", "const u32 bytes = count << 4;", "const u32 bytes = count << 3;"),
        ("wrong_release_slot", "reinterpret_cast<ReleaseFn>(vtbl[1])(p->f0, p->f4);", "reinterpret_cast<ReleaseFn>(vtbl[0])(p->f0, p->f4);"),
    ]
    for mut_name, old, new in mutations:
        assert old in cpp_text, f"mutation anchor missing: {mut_name}"
        mut_cpp = work_dir / f"mut_{mut_name}.cpp"
        mut_obj = work_dir / f"mut_{mut_name}.o"
        mut_cpp.write_text(cpp_text.replace(old, new, 1), encoding="utf-8")
        compile_tu_armv6k(mut_cpp, mut_obj, ROOT)
        cand_code, rodata_blobs = patch_cand_elf(mut_obj)
        try:
            failures = run_suite(orig_code, cand_code, rodata_blobs)
        except unicorn.UcError as exc:
            failures = [f"uc_error: {exc}"]
        assert failures, f"negative control {mut_name} unexpectedly passed!"


def main() -> int:
    work_dir = ROOT / "build" / "test_leaf_003fbe64"
    work_dir.mkdir(parents=True, exist_ok=True)

    raw = ORIG_BIN.read_bytes()[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    orig_code = patch_orig_code(raw)

    obj_path = work_dir / "leaf_batch45_a.o"
    compile_tu_armv6k(SRC_CPP, obj_path, ROOT)
    cand_code, rodata_blobs = patch_cand_elf(obj_path)

    failures = run_suite(orig_code, cand_code, rodata_blobs)
    if failures:
        for f in failures[:5]:
            print("FAIL:", f)
        return 1

    run_negative_controls(orig_code, SRC_CPP.read_text(encoding="utf-8"), work_dir)
    cases = build_cases()
    print(f"ALL PASS: {len(cases)} cases + 5 negative controls (cand_size={len(cand_code)}B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
