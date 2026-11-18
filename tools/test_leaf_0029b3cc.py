#!/usr/bin/env python3
"""Differential test for Unite_Init (0x0029b3cc) with Unicorn ARM."""

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
SOURCE = ROOT / "src" / "camp" / "unite.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_0029b3cc"

FUNC_ADDR = 0x0029B3CC
FUNC_SIZE = 1676

STUB_ZERO = 0x002C4B30
STUB_ALLOC = 0x002C54F0
STUB_GET_DEMON = 0x002B9364
STUB_GET_CAT = 0x0026A904
STUB_GET_INFO = 0x002840B8
STUB_CHK_AFF = 0x002992D8
STUB_QSORT = 0x002B7F0A  # Thumb
STUB_GET_EXTRA = 0x00205404
STUB_GET_EXTRA_INFO = 0x0029EC14
STUB_2AE3F0 = 0x002AE3F0
STUB_26A86C = 0x0026A86C
STUB_1DF7D0 = 0x001DF7D0
STUB_1CFED0 = 0x001CFED0
STUB_1D00F8 = 0x001D00F8
STUB_MEMCPY = 0x002C5FF4
STUB_FREE = 0x002C4360
STUB_MEMCLR4 = 0x003F0300

STUB_NAMES = {
    STUB_ZERO: "AsdMem_Zero",
    STUB_ALLOC: "engine_func_002c54f0",
    STUB_GET_DEMON: "func_002b9364",
    STUB_GET_CAT: "func_0026a904",
    STUB_GET_INFO: "func_002840b8",
    STUB_CHK_AFF: "func_002992d8",
    STUB_QSORT: "func_002b7f0a",
    STUB_GET_EXTRA: "func_00205404",
    STUB_GET_EXTRA_INFO: "func_0029ec14",
    STUB_2AE3F0: "func_002ae3f0",
    STUB_26A86C: "func_0026a86c",
    STUB_1DF7D0: "func_001df7d0",
    STUB_1CFED0: "func_001cfed0",
    STUB_1D00F8: "func_001d00f8",
    STUB_MEMCPY: "engine_func_002c5ff4",
    STUB_FREE: "AsdMem_Free",
    STUB_MEMCLR4: "__aeabi_memclr4",
}

PTR_RODATA = 0x00500000
PTR_SKILLS = 0x20000000
PTR_ENTRY = 0x20001000
PTR_IDP = 0x20002000
PTR_DEMON = 0x20003000
PTR_INFO_BASE = 0x20004000
PTR_EXTRA_INFO = 0x20006000
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


def _get_symbol_offset(obj_file: Path, substr: str) -> int:
    data = obj_file.read_bytes()
    e_shoff, = struct.unpack_from("<I", data, 0x20)
    e_shentsize, e_shnum, _e_shstrndx = struct.unpack_from("<HHH", data, 0x2E)
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    for sh in sections:
        if sh[1] == 2:
            str_sec = sections[sh[6]]
            strtab = data[str_sec[4] : str_sec[4] + str_sec[5]]
            sym_off, sym_size, entsize = sh[4], sh[5], sh[9] or 16
            for pos in range(sym_off, sym_off + sym_size, entsize):
                st_name, st_value, _st_size, _st_info, _st_other, _st_shndx = struct.unpack_from("<IIIBBH", data, pos)
                end = strtab.find(b"\x00", st_name)
                name = strtab[st_name:end].decode("utf-8", errors="replace")
                if substr in name:
                    return st_value
    return 0


def _extract_rodata(obj_file: Path) -> bytes:
    data = obj_file.read_bytes()
    e_shoff, = struct.unpack_from("<I", data, 0x20)
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 0x2E)
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    shstr_off, shstr_size = sections[e_shstrndx][4], sections[e_shstrndx][5]
    shstr = data[shstr_off : shstr_off + shstr_size]
    for sh in sections:
        end = shstr.find(b"\x00", sh[0])
        name = shstr[sh[0] : end].decode("utf-8", errors="replace")
        if name == ".rodata":
            return data[sh[4] : sh[4] + sh[5]]
    return b""


def relocate_candidate(obj_file: Path) -> tuple[bytes, bytes]:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = next((val for name, val in funcs.items() if "Unite_Init" in name), None)
    if candidate is None:
        raise RuntimeError(f"Unite_Init not found in {obj_file}")
    sym_offset = _get_symbol_offset(obj_file, "Unite_Init")

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
            if dst == STUB_QSORT and rtype == 28:
                struct.pack_into("<I", code, off, 0xFA000000 | disp)
            else:
                struct.pack_into("<I", code, off, (insn & 0xFF000000) | disp)
        elif rtype == 2 and sym_name == "":
            addend = struct.unpack_from("<I", code, off)[0]
            target = (FUNC_ADDR + (addend - sym_offset)) if addend >= sym_offset else (PTR_RODATA + addend)
            struct.pack_into("<I", code, off, target)
        else:
            raise RuntimeError(f"Unhandled relocation type {rtype} for {sym_name}")
    return bytes(code), _extract_rodata(obj_file)


def compile_candidate() -> tuple[bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj = OUT_DIR / "unite.o"
    res = compile_tu_armv6k(SOURCE, obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{res.stderr}\n{res.stdout}")
    return relocate_candidate(obj)


def compile_candidate_mutant(name: str, old: str, new: str) -> tuple[bytes, bytes]:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"Mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"unite_mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"unite_mutant_{name}.o"
    mutant_src.write_text(text.replace(old, new, 1), encoding="utf-8")
    res = compile_tu_armv6k(mutant_src, mutant_obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant {name} compilation failed:\n{res.stderr}")
    return relocate_candidate(mutant_obj)


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(PTR_RODATA, 0x1000)
        self.uc.mem_map(PTR_SKILLS, 0x30000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(
        self,
        code: bytes,
        rodata: bytes,
        skills: list[int],
        use_entry: bool,
        use_idp: bool,
        demon_skills: list[int],
        innate_skills: list[int],
        skill_flags: dict[int, int],
        aff_ok: bool,
        extra_skills: list[int],
        promote_ok: bool,
    ) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(FUNC_ADDR, b"\x00" * 0x1000)
        uc.mem_write(FUNC_ADDR, code)
        uc.mem_write(PTR_RODATA, b"\x00" * 0x1000)
        if rodata:
            uc.mem_write(PTR_RODATA, rodata)

        uc.mem_write(PTR_SKILLS, b"\x00" * 0x100)
        if skills:
            uc.mem_write(PTR_SKILLS, struct.pack(f"<{len(skills)}H", *skills))

        uc.mem_write(PTR_ENTRY, struct.pack("<II", (0x123 << 17), 0x45))
        uc.mem_write(PTR_IDP, struct.pack("<H", 0x77))

        uc.mem_write(PTR_DEMON, b"\x00" * 0x100)
        for idx, dsk in enumerate(demon_skills[:8]):
            uc.mem_write(PTR_DEMON + 0x3C + idx * 2, struct.pack("<H", dsk))
        for idx, isk in enumerate(innate_skills[:8]):
            uc.mem_write(PTR_DEMON + 0x4E + idx * 4, struct.pack("<H", isk))
        for off_aff in range(0x6C, 0x90, 2):
            uc.mem_write(PTR_DEMON + off_aff, struct.pack("<H", 3 << 10))

        for stub_addr in STUB_NAMES:
            if stub_addr == STUB_QSORT:
                uc.mem_write(stub_addr, struct.pack("<HH", 0x4770, 0x46C0))
            else:
                uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))

        heap_idx = 0
        f1d00f8_calls = 0
        calls: list[tuple[object, ...]] = []
        bad_writes: list[int] = []

        def on_mem_invalid(uc_cb: unicorn.Uc, access: int, addr: int, size: int, val: int, _ud: object) -> bool:
            bad_writes.append(addr)
            return False

        def on_code(uc_cb: unicorn.Uc, addr: int, size: int, _ud: object) -> None:
            nonlocal heap_idx, f1d00f8_calls
            if addr not in STUB_NAMES:
                return
            r0 = uc_cb.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc_cb.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc_cb.reg_read(arm.UC_ARM_REG_R2)
            r3 = uc_cb.reg_read(arm.UC_ARM_REG_R3)
            sp = uc_cb.reg_read(arm.UC_ARM_REG_SP)
            if addr == STUB_ZERO:
                uc_cb.mem_write(r0, b"\x00" * r1)
            elif addr == STUB_MEMCLR4:
                uc_cb.mem_write(r0, b"\x00" * r1)
            elif addr == STUB_ALLOC:
                s0 = struct.unpack("<I", uc_cb.mem_read(sp, 4))[0]
                calls.append(("alloc", r0, r1, r2, r3, s0))
                ptr = PTR_HEAP_BASE + heap_idx * 0x100
                heap_idx += 1
                uc_cb.mem_write(ptr, b"\x00" * 0x100)
                uc_cb.reg_write(arm.UC_ARM_REG_R0, ptr)
            elif addr == STUB_GET_DEMON:
                calls.append(("get_demon", r0))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, PTR_DEMON)
            elif addr == STUB_GET_CAT:
                uc_cb.reg_write(arm.UC_ARM_REG_R0, (r0 % 6) + 1)
            elif addr == STUB_GET_INFO:
                if r0 in skill_flags:
                    iptr = PTR_INFO_BASE + (r0 & 0xFF) * 0x40
                    uc_cb.mem_write(iptr, b"\x00" * 0x40)
                    uc_cb.mem_write(iptr + 0x38, struct.pack("<I", skill_flags[r0]))
                    uc_cb.reg_write(arm.UC_ARM_REG_R0, iptr)
                else:
                    uc_cb.reg_write(arm.UC_ARM_REG_R0, 0)
            elif addr == STUB_CHK_AFF:
                calls.append(("chk_aff", r0, r1))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, 1 if aff_ok else 0)
            elif addr == STUB_QSORT:
                calls.append(("qsort", r0, r1, r2, r3))
                if r1 > 0:
                    arr = list(struct.unpack(f"<{r1}H", uc_cb.mem_read(r0, r1 * 2)))
                    arr.sort()
                    uc_cb.mem_write(r0, struct.pack(f"<{r1}H", *arr))
            elif addr == STUB_GET_EXTRA:
                calls.append(("get_extra", r0, r1, r2, r3))
                if r0 != 0 and extra_skills:
                    uc_cb.mem_write(r0, struct.pack(f"<{len(extra_skills)}H", *extra_skills))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, len(extra_skills))
            elif addr == STUB_GET_EXTRA_INFO:
                uc_cb.mem_write(PTR_EXTRA_INFO, struct.pack("<BBBB", 0, 0, (r0 % 5) + 1, 0))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, PTR_EXTRA_INFO)
            elif addr == STUB_2AE3F0:
                uc_cb.reg_write(arm.UC_ARM_REG_R0, 1 if promote_ok else 0)
            elif addr == STUB_26A86C:
                uc_cb.reg_write(arm.UC_ARM_REG_R0, 1 if promote_ok else 0)
            elif addr in (STUB_1DF7D0, STUB_1CFED0, STUB_1D00F8):
                ctx_words = struct.unpack("<12I", uc_cb.mem_read(r0, 48))
                ctx_tail = struct.unpack("<7I", uc_cb.mem_read(r0 + 0x30, 28))
                calls.append((STUB_NAMES[addr], ctx_words[0], ctx_words[2], ctx_words[4], ctx_words[6], ctx_words[8], ctx_words[10], ctx_words[11] & 0xFF, ctx_tail))
                if addr == STUB_1D00F8:
                    f1d00f8_calls += 1
                    uc_cb.reg_write(arm.UC_ARM_REG_R0, 1 if f1d00f8_calls == 2 else 0)
            elif addr == STUB_MEMCPY:
                calls.append(("memcpy", r0, r1, r2))
                uc_cb.mem_write(r0, bytes(uc_cb.mem_read(r1, r2)))
            elif addr == STUB_FREE:
                calls.append(("free", r0))

        h_code = uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
        h_mem = uc.hook_add(unicorn.UC_HOOK_MEM_WRITE_UNMAPPED | unicorn.UC_HOOK_MEM_READ_UNMAPPED, on_mem_invalid)

        uc.reg_write(arm.UC_ARM_REG_R0, PTR_SKILLS)
        uc.reg_write(arm.UC_ARM_REG_R1, len(skills))
        uc.reg_write(arm.UC_ARM_REG_R2, PTR_ENTRY if use_entry else 0)
        uc.reg_write(arm.UC_ARM_REG_R3, PTR_IDP if use_idp else 0)
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        try:
            uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=1_000_000, count=20000)
        finally:
            uc.hook_del(h_code)
            uc.hook_del(h_mem)

        callee = {
            reg_name: uc.reg_read(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"))
            for reg_name in CALLEE_SAVED
        }
        return {
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": callee,
            "calls": calls,
            "skills_out": bytes(uc.mem_read(PTR_SKILLS, max(2, len(skills) * 2))),
            "bad_writes": bad_writes,
        }


def compare(orig: dict[str, object], cand: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    if orig["pc"] != cand["pc"]:
        diffs.append(f"pc: orig={orig['pc']:#x} cand={cand['pc']:#x}")
    if orig["sp"] != cand["sp"]:
        diffs.append(f"sp: orig={orig['sp']:#x} cand={cand['sp']:#x}")
    if orig["callee"] != cand["callee"]:
        diffs.append("callee-saved register mismatch")
    if orig["calls"] != cand["calls"]:
        diffs.append(f"calls mismatch (orig {len(orig['calls'])} vs cand {len(cand['calls'])})")
    if orig["skills_out"] != cand["skills_out"]:
        diffs.append("skills_out mismatch")
    if cand["bad_writes"]:
        diffs.append(f"unexpected writes: {cand['bad_writes'][:4]}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes, cand_rodata = compile_candidate()
    # flag encoding: ((flags << 21) >> 27) == 5 -> bits [10:6] = 5 -> 5 << 6 = 0x140
    # ((flags << 12) >> 28) == sub -> bits [19:16] = sub -> sub << 16
    def mk_flag(sub: int, slot: int = 1) -> int:
        return (5 << 6) | (sub << 16) | (slot << 11)

    cases = [
        ("empty_null", [], False, False, [5, 0, 0, 0, 0, 0, 0, 0], [], {}, True, [], False),
        (
            "entry_promote",
            [10, 20, 30, 40, 50],
            True,
            False,
            [6, 12, 0, 0, 0, 0, 0, 0],
            [10],
            {20: mk_flag(1), 30: mk_flag(5), 40: mk_flag(6), 50: mk_flag(2)},
            False,
            [100, 101],
            True,
        ),
        (
            "idp_aff_ok",
            [20, 30, 40, 50],
            False,
            True,
            [12, 18, 24, 0, 0, 0, 0, 0],
            [99],
            {20: mk_flag(3), 30: mk_flag(4), 40: mk_flag(5)},
            True,
            [102],
            False,
        ),
    ]
    for label, sk, ue, ui, dsk, isk, sf, aok, ex, pok in cases:
        orig_res = Runner().run(orig_bytes, b"", sk, ue, ui, dsk, isk, sf, aok, ex, pok)
        cand_res = Runner().run(cand_bytes, cand_rodata, sk, ue, ui, dsk, isk, sf, aok, ex, pok)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("wrong_best_aff", "if (ctx.best_affinity == 6)", "if (ctx.best_affinity == 5)"),
        ("wrong_sub_1_map", "mapped = 5;", "mapped = 2;"),
        ("drop_promote", "ctx.arr3[ctx.count3++] = sk;\n                ctx.arr1[i] = 0;", "// dropped"),
        ("drop_while_loop", "while (func_001d00f8(&ctx) != 0) {", "if (false) {"),
        ("drop_memcpy", "engine_func_002c5ff4(skills, ctx.arr3, buf_bytes);", "// dropped"),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes, mut_rodata = compile_candidate_mutant(name, old, new)
        any_diff = False
        for _label, sk, ue, ui, dsk, isk, sf, aok, ex, pok in cases:
            if compare(
                Runner().run(orig_bytes, b"", sk, ue, ui, dsk, isk, sf, aok, ex, pok),
                Runner().run(mut_bytes, mut_rodata, sk, ue, ui, dsk, isk, sf, aok, ex, pok),
            ):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: Unite_Init (0x0029b3cc) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
