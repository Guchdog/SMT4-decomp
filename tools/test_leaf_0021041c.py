#!/usr/bin/env python3
"""Differential test for AsdSaveCommon_func_0021041c (0x0021041c) with Unicorn ARM."""

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
SOURCE = ROOT / "src" / "engine" / "asd_file.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_0021041c"

FUNC_ADDR = 0x0021041C
FUNC_SIZE = 204

STUB_ALLOC = 0x002C54F0
STUB_READ = 0x002F5348
STUB_COPY = 0x002BD610
STUB_FREE = 0x002C4360

STUB_NAMES = {
    STUB_ALLOC: "AsdMem_AllocAlign",
    STUB_READ: "AsdSave_Read",
    STUB_COPY: "AsdMem_CopyFrom",
    STUB_FREE: "AsdMem_Free",
}

PTR_BUF = 0x20000000
PTR_HDR = 0x20010000
PTR_PAYLOAD = 0x20020000
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
    candidate = next((val for name, val in funcs.items() if "AsdSaveCommon_func_0021041c" in name), None)
    if candidate is None:
        raise RuntimeError(f"AsdSaveCommon_func_0021041c not found in {obj_file}")

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
    obj = OUT_DIR / "asd_file.o"
    res = compile_tu_armv6k(SOURCE, obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{res.stderr}\n{res.stdout}")
    return relocate_candidate(obj)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"Mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"asd_file_mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"asd_file_mutant_{name}.o"
    mutant_src.write_text(text.replace(old, new, 1), encoding="utf-8")
    res = compile_tu_armv6k(mutant_src, mutant_obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant {name} compilation failed:\n{res.stderr}")
    return relocate_candidate(mutant_obj)


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(PTR_BUF, 0x30000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(self, code: bytes, device: int, file_id: int, payload_size: int) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(FUNC_ADDR, b"\x00" * 0x400)
        uc.mem_write(FUNC_ADDR, code)

        uc.mem_write(PTR_BUF, b"\x00" * 0x1000)
        uc.mem_write(PTR_HDR, b"\x00" * 0x100)
        uc.mem_write(PTR_PAYLOAD, b"\x00" * 0x1000)

        for stub_addr in STUB_NAMES:
            uc.mem_write(stub_addr, struct.pack("<I", 0xE12FFF1E))

        calls: list[tuple[object, ...]] = []
        bad_writes: list[int] = []

        def on_mem_invalid(uc_cb: unicorn.Uc, access: int, addr: int, size: int, val: int, _ud: object) -> bool:
            bad_writes.append(addr)
            return False

        def on_code(uc_cb: unicorn.Uc, addr: int, size: int, _ud: object) -> None:
            if addr not in STUB_NAMES:
                return
            r0 = uc_cb.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc_cb.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc_cb.reg_read(arm.UC_ARM_REG_R2)
            r3 = uc_cb.reg_read(arm.UC_ARM_REG_R3)
            sp = uc_cb.reg_read(arm.UC_ARM_REG_SP)
            if addr == STUB_ALLOC:
                s0 = struct.unpack("<I", uc_cb.mem_read(sp, 4))[0]
                calls.append(("alloc", r0, r1, r2, r3, s0))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, PTR_BUF)
            elif addr == STUB_READ:
                calls.append(("read", r0, r1, r2, r3))
                uc_cb.mem_write(r2, bytes((i & 0xFF) for i in range(r3)))
                uc_cb.reg_write(arm.UC_ARM_REG_R0, 0x0206)
            elif addr == STUB_COPY:
                calls.append(("copy", r0, r1, r2))
                uc_cb.mem_write(r1, bytes(uc_cb.mem_read(r0, r2)))
            elif addr == STUB_FREE:
                calls.append(("free", r0))

        h_code = uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
        h_mem = uc.hook_add(unicorn.UC_HOOK_MEM_WRITE_UNMAPPED | unicorn.UC_HOOK_MEM_READ_UNMAPPED, on_mem_invalid)

        uc.reg_write(arm.UC_ARM_REG_R0, device)
        uc.reg_write(arm.UC_ARM_REG_R1, file_id)
        uc.reg_write(arm.UC_ARM_REG_R2, PTR_HDR)
        uc.reg_write(arm.UC_ARM_REG_R3, PTR_PAYLOAD)
        uc.mem_write(STACK_INIT, struct.pack("<I", payload_size))
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        try:
            uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=1_000_000, count=2000)
        finally:
            uc.hook_del(h_code)
            uc.hook_del(h_mem)

        callee = {
            reg_name: uc.reg_read(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"))
            for reg_name in CALLEE_SAVED
        }
        return {
            "r0": uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": callee,
            "calls": calls,
            "hdr": bytes(uc.mem_read(PTR_HDR, 0x80)),
            "payload": bytes(uc.mem_read(PTR_PAYLOAD, payload_size)),
            "bad_writes": bad_writes,
        }


def compare(orig: dict[str, object], cand: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    if orig["r0"] != cand["r0"]:
        diffs.append(f"r0: orig={orig['r0']:#x} cand={cand['r0']:#x}")
    if orig["pc"] != cand["pc"]:
        diffs.append(f"pc: orig={orig['pc']:#x} cand={cand['pc']:#x}")
    if orig["sp"] != cand["sp"]:
        diffs.append(f"sp: orig={orig['sp']:#x} cand={cand['sp']:#x}")
    if orig["callee"] != cand["callee"]:
        diffs.append("callee-saved register mismatch")
    if orig["calls"] != cand["calls"]:
        diffs.append(f"calls mismatch (orig {orig['calls']} vs cand {cand['calls']})")
    if orig["hdr"] != cand["hdr"]:
        diffs.append("hdr mismatch")
    if orig["payload"] != cand["payload"]:
        diffs.append("payload mismatch")
    if cand["bad_writes"]:
        diffs.append(f"unexpected writes: {cand['bad_writes'][:4]}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes = compile_candidate()
    cases = [
        ("payload_0", 0, 1, 0),
        ("payload_16", 1, 2, 16),
        ("payload_256", 2, 0x55, 256),
        ("payload_1024", 3, 9, 1024),
    ]
    for label, dev, fid, psz in cases:
        orig_res = Runner().run(orig_bytes, dev, fid, psz)
        cand_res = Runner().run(cand_bytes, dev, fid, psz)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("wrong_total", "const u32 result = AsdSave_Read(device, file, buffer, total);", "const u32 result = AsdSave_Read(device, file, buffer, total + 4);"),
        ("wrong_hdr_size", "AsdMem_CopyFrom(buffer, header, 0x80);", "AsdMem_CopyFrom(buffer, header, 0x40);"),
        ("wrong_payload_off", "AsdMem_CopyFrom(buffer + 0x80, payload, payload_size);", "AsdMem_CopyFrom(buffer + 0x40, payload, payload_size);"),
        ("drop_free", "AsdMem_CopyFrom(buffer + 0x80, payload, payload_size);\n    AsdMem_Free(buffer);", "AsdMem_CopyFrom(buffer + 0x80, payload, payload_size);"),
        ("wrong_ret", "AsdMem_CopyFrom(buffer + 0x80, payload, payload_size);\n    AsdMem_Free(buffer);\n    return result;", "AsdMem_CopyFrom(buffer + 0x80, payload, payload_size);\n    AsdMem_Free(buffer);\n    return result + 1;"),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes = compile_candidate_mutant(name, old, new)
        any_diff = False
        for _label, dev, fid, psz in cases:
            if compare(Runner().run(orig_bytes, dev, fid, psz), Runner().run(mut_bytes, dev, fid, psz)):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: AsdSaveCommon_func_0021041c (0x0021041c) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
