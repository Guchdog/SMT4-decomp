#!/usr/bin/env python3
"""Differential test for ui_func_00121b80 (0x00121b80) using Unicorn ARM.

Compiles src/engine/leaf_batch34_c.cpp, extracts the ui_func_00121b80 body,
resolves its two direct calls to deterministic stubs placed at the original
target addresses, and runs the pinned original (extracted/exefs/code.bin)
against the candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and the callee-saved r4-r11;
  * the ordered call log with every register argument (and the architected
    stack arguments, of which there are none) of both helpers;
  * the info page (the +0x04/+0x08 store performed by the 0x00131414 stub) and
    the whole 16 KiB resource page, so every rebasing store, the conditional
    +0x14/+0x18/+0x0C/+0x10 guards and the header re-tag are pinned;
  * every emulated write outside the private stack, bucketed by page.

Coverage:
  * the "already parsed" guard with 1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF and
    a CFNT resource (the guard runs before the magic check);
  * the already-rebased 'CFNU' search: empty table, FINF at the first and last
    index, no FINF at all, count 1 and 0xFFFF, a large chunk offset, a
    zero-size chunk and a multi-entry walk with mixed sizes;
  * the 'CFNT' header check (0x0012AA74): rejected magic, 0xFEFF marker,
    version high/middle/low byte boundaries, file size 0x23/0x24 and chunk
    count below the required two, plus a forced success/failure result so both
    sides of the caller branch are reachable independently of the fixture;
  * every accepted chunk tag (FINF with all, some and none of its optional
    pointers, CWDH, CMAP, TGLP, GLGR), several FINF chunks (the last one wins),
    unknown tags in both signed groups and one past each known tag, an unknown
    tag before and after a FINF (the earlier rebasing stores must survive), and
    chunk_offset == 0;
  * loop bounds: count equal to, one below and one above the number of planted
    entries, a zero size that reprocesses the same chunk, and the signed `bgt`
    exit for a huge count;
  * the final attach call and both return values, including the path that
    re-tags the header yet returns 0 because no FINF chunk was seen.

Negative controls mutate the magic/tag constants, the rebasing offsets, the
optional-pointer guards, the attach argument order, the header check argument,
the re-tag value and the CFNU empty-table guard; each mutant must be detected.
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
SOURCE = ROOT / "src/engine/leaf_batch34_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_00121b80"

FUNC_ADDR = 0x00121B80
FUNC_SIZE = 472

# Free address for the relocated candidate; the body is position independent
# apart from its two direct calls.
CAND_ADDR = 0x00200000

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000          # original, candidate and both stub targets
STUB_CHECK = 0x0012AA74         # ui_func_0012aa74
STUB_ATTACH = 0x00131414        # ui_func_00131414

INFO_ADDR = 0x00710000
INFO_SIZE = 0x00001000
RES_ADDR = 0x00720000
RES_SIZE = 0x00004000

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_NAMES = {
    STUB_CHECK: "ui_func_0012aa74",
    STUB_ATTACH: "ui_func_00131414",
}
STACK_ARGS = {STUB_CHECK: 0, STUB_ATTACH: 0}

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

MAGIC_CFNT = 0x544E4643
MAGIC_CFNU = 0x554E4643
TAG_FINF = 0x464E4946
TAG_CWDH = 0x48445743
TAG_CMAP = 0x50414D43
TAG_TGLP = 0x504C4754
TAG_GLGR = 0x52474C47


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "00121b80" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"ui_func_00121b80 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    seen = set()
    for rel in relocs:
        if rel.relocation_type not in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = None
        for address, name in STUB_NAMES.items():
            if name in rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        seen.add(target)
        pc = CAND_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        cond = original & 0xFF000000
        struct.pack_into("<I", code, rel.offset, cond | (displacement & 0x00FFFFFF))
    if seen != set(STUB_NAMES):
        raise RuntimeError(f"missing call relocations: found {sorted(seen)}")
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch34_c.o"
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


# --------------------------------------------------------------------- fixtures
def pattern(size: int, salt: int) -> bytes:
    return bytes(((index * 7 + salt) & 0xFF) for index in range(size))


def chunk(tag: int, offset: int, size: int = 0x20, words: dict | None = None) -> dict:
    return {"tag": tag & 0xFFFFFFFF, "offset": offset, "size": size & 0xFFFFFFFF,
            "words": words or {}}


def finf(offset: int, size: int = 0x20, p0: int = 0x100, p1: int = 0x200,
         p2: int = 0x300) -> dict:
    return chunk(TAG_FINF, offset, size, {0x10: p0, 0x14: p1, 0x18: p2})


def cwdh(offset: int, size: int = 0x20, p: int = 0x400) -> dict:
    return chunk(TAG_CWDH, offset, size, {0x0C: p})


def cmap(offset: int, size: int = 0x20, p: int = 0x500) -> dict:
    return chunk(TAG_CMAP, offset, size, {0x10: p})


def tglp(offset: int, size: int = 0x20, p: int = 0x600) -> dict:
    return chunk(TAG_TGLP, offset, size, {0x1C: p})


def glgr(offset: int, size: int = 0x20) -> dict:
    return chunk(TAG_GLGR, offset, size)


def build_info(case: dict) -> bytes:
    page = bytearray(pattern(INFO_SIZE, 0x41))
    struct.pack_into("<I", page, 0x00, case["info_type"] & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x04, case["info_data"] & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x08, case["info_chunk"] & 0xFFFFFFFF)
    return bytes(page)


def build_resource(case: dict) -> bytes:
    page = bytearray(pattern(RES_SIZE, 0x5B))
    struct.pack_into("<I", page, 0x00, case["magic"] & 0xFFFFFFFF)
    struct.pack_into("<H", page, 0x04, case["marker"] & 0xFFFF)
    struct.pack_into("<H", page, 0x06, case["chunk_offset"] & 0xFFFF)
    struct.pack_into("<I", page, 0x08, case["version"] & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x0C, case["file_size"] & 0xFFFFFFFF)
    struct.pack_into("<H", page, 0x10, case["chunk_count"] & 0xFFFF)
    for entry in case["chunks"]:
        off = entry["offset"]
        struct.pack_into("<I", page, off + 0x00, entry["tag"])
        struct.pack_into("<I", page, off + 0x04, entry["size"])
        for field_offset, value in entry["words"].items():
            struct.pack_into("<I", page, off + field_offset, value & 0xFFFFFFFF)
    return bytes(page)


def model_check(uc, pointer: int, tag: int, version: int, words: int) -> int:
    """Python model of 0x0012AA74, used by the stub for both machines."""
    magic = struct.unpack("<I", uc.mem_read(pointer, 4))[0]
    marker = struct.unpack("<H", uc.mem_read(pointer + 4, 2))[0]
    field_version = struct.unpack("<I", uc.mem_read(pointer + 8, 4))[0]
    file_size = struct.unpack("<I", uc.mem_read(pointer + 0x0C, 4))[0]
    count = struct.unpack("<H", uc.mem_read(pointer + 0x10, 2))[0]
    if magic != tag:
        return 0
    if marker != 0xFEFF:
        return 0
    if (version >> 24) != (field_version >> 24):
        return 0
    if ((version >> 16) & 0xFF) < ((field_version >> 16) & 0xFF):
        return 0
    if (version & 0xFF) > (field_version & 0xFF):
        return 0
    if file_size < 0x14 + words * 8:
        return 0
    if count < words:
        return 0
    return 1


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(INFO_ADDR, INFO_SIZE)
        self.uc.mem_map(RES_ADDR, RES_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

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
    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        raw = self.uc.mem_read(sp, 4 * count)
        return struct.unpack(f"<{count}I", raw)

    def _log(self, address: int, *args) -> None:
        self.call_log.append(
            (STUB_NAMES[address], args + self._stack_words(STACK_ARGS[address]))
        )

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_CHECK:
            self._log(address, r0, r1, r2, r3)
            forced = self.case.get("force_check")
            if forced is None:
                result = model_check(uc, r0, r1, r2, r3)
            else:
                result = forced & 0xFFFFFFFF
            uc.reg_write(arm.UC_ARM_REG_R0, result)
        elif address == STUB_ATTACH:
            self._log(address, r0, r1, r2)
            uc.mem_write(r0 + 4, struct.pack("<I", r1))
            uc.mem_write(r0 + 8, struct.pack("<I", r2))
            uc.reg_write(arm.UC_ARM_REG_R0, r0 + 4)  # 0x00131414 returns p + 4
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

    def run(self, code: bytes, case: dict, addr: int = FUNC_ADDR) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case

        self.uc.mem_write(addr, code)
        self.uc.mem_write(INFO_ADDR, build_info(case))
        self.uc.mem_write(RES_ADDR, build_resource(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, INFO_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, RES_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0xCCCCCCCC)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0xDDDDDDDD)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(addr, TRAP_ADDR, timeout=5_000_000, count=1_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        regions = sorted(
            {
                self._region(address)
                for address, _size in self.writes
                if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
            }
        )

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self._normalise(self.call_log),
            "write_regions": regions,
            "fixtures": {
                "info": bytes(self.uc.mem_read(INFO_ADDR, INFO_SIZE)),
                "resource": bytes(self.uc.mem_read(RES_ADDR, RES_SIZE)),
            },
        }

    @staticmethod
    def _region(address: int) -> str:
        if INFO_ADDR <= address < INFO_ADDR + INFO_SIZE:
            return "info"
        if RES_ADDR <= address < RES_ADDR + RES_SIZE:
            return "resource"
        if STACK_ADDR <= address < STACK_ADDR + STACK_SIZE:
            return "stack"
        return "unmapped"


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "write_regions", "call_log"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            for index, (left, right) in enumerate(zip(value, cand["fixtures"][key])):
                if left != right:
                    problems.append(
                        f"fixture {key} first differs at +0x{index:04x}: "
                        f"orig=0x{left:02x} cand=0x{right:02x}"
                    )
                    break
            else:
                problems.append(f"fixture {key} length differs")
    return problems


def res_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "magic": MAGIC_CFNU,
        "marker": 0xFEFF,
        "chunk_offset": 0x20,
        "version": 0x03000000,
        "file_size": 0x4000,
        "chunk_count": 0,
        "chunks": (),
        "force_check": None,
        "info_type": 0x00421D58,
        "info_data": 0,
        "info_chunk": 0xDEADBEEF,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- guard: a non-zero info+0x04 returns before the magic is even read
    for info_data in (1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        cases.append(res_case(f"already parsed info+04=0x{info_data:08x}",
                              info_data=info_data, chunk_count=2,
                              chunks=(finf(0x20), glgr(0x40))))
    cases.append(res_case("already parsed, CFNT resource", info_data=7,
                          magic=MAGIC_CFNT, chunk_count=2,
                          chunks=(finf(0x20), glgr(0x40))))

    # --- already-rebased 'CFNU' search
    cases.append(res_case("CFNU empty table", chunk_count=0))
    cases.append(res_case("CFNU count 0 with FINF planted", chunk_count=0,
                          chunks=(finf(0x20),)))
    cases.append(res_case("CFNU count 1 FINF first", chunk_count=1,
                          chunks=(finf(0x20),)))
    cases.append(res_case("CFNU FINF at index 0 of 2", chunk_count=2,
                          chunks=(finf(0x20), cmap(0x40))))
    cases.append(res_case("CFNU FINF at index 1 of 2", chunk_count=2,
                          chunks=(glgr(0x20), finf(0x40))))
    cases.append(res_case("CFNU no FINF", chunk_count=2,
                          chunks=(cmap(0x20), cwdh(0x40))))
    cases.append(res_case("CFNU count 0xFFFF FINF first", chunk_count=0xFFFF,
                          chunks=(finf(0x20),)))
    cases.append(res_case("CFNU large chunk offset", chunk_count=1,
                          chunk_offset=0x100, chunks=(finf(0x100),)))
    cases.append(res_case("CFNU zero-size FINF", chunk_count=2,
                          chunks=(finf(0x20, size=0), glgr(0x40))))
    cases.append(res_case("CFNU walk with mixed sizes", chunk_count=3,
                          chunks=(glgr(0x20, size=0x30), cmap(0x50, size=0x10),
                                  finf(0x60))))
    cases.append(res_case("CFNU offset points into resource", chunk_count=1,
                          chunk_offset=0x1000, chunks=(finf(0x1000),)))

    # --- the 'CFNT' header check (0x0012AA74)
    cases.append(res_case("CFNT faithful minimal", magic=MAGIC_CFNT,
                          chunk_count=2, chunks=(finf(0x20), cmap(0x40))))
    cases.append(res_case("CFNT rejected magic", magic=0x58585858,
                          chunk_count=2, chunks=(finf(0x20), cmap(0x40))))
    cases.append(res_case("CFNT rejected marker 0xFEFE", magic=MAGIC_CFNT,
                          marker=0xFEFE, chunk_count=2,
                          chunks=(finf(0x20), cmap(0x40))))
    cases.append(res_case("CFNT rejected version high byte 0x04",
                          magic=MAGIC_CFNT, version=0x04000000, chunk_count=2,
                          chunks=(finf(0x20), cmap(0x40))))
    cases.append(res_case("CFNT rejected version high byte 0x02",
                          magic=MAGIC_CFNT, version=0x02000000, chunk_count=2,
                          chunks=(finf(0x20), cmap(0x40))))
    cases.append(res_case("CFNT rejected version middle byte 0x01",
                          magic=MAGIC_CFNT, version=0x03010000, chunk_count=2,
                          chunks=(finf(0x20), cmap(0x40))))
    cases.append(res_case("CFNT accepted version low byte 0xFF",
                          magic=MAGIC_CFNT, version=0x030000FF, chunk_count=2,
                          chunks=(finf(0x20), cmap(0x40))))
    cases.append(res_case("CFNT accepted version low byte 0x01",
                          magic=MAGIC_CFNT, version=0x03000001, chunk_count=2,
                          chunks=(finf(0x20), cmap(0x40))))
    cases.append(res_case("CFNT rejected file size 0x23", magic=MAGIC_CFNT,
                          file_size=0x23, chunk_count=2,
                          chunks=(finf(0x20), cmap(0x40))))
    cases.append(res_case("CFNT accepted file size 0x24", magic=MAGIC_CFNT,
                          file_size=0x24, chunk_count=2,
                          chunks=(finf(0x20), cmap(0x40))))
    cases.append(res_case("CFNT rejected chunk count 1", magic=MAGIC_CFNT,
                          chunk_count=1, chunks=(finf(0x20),)))
    cases.append(res_case("CFNT forced check failure", magic=MAGIC_CFNT,
                          force_check=0, chunk_count=2,
                          chunks=(finf(0x20), cmap(0x40))))
    cases.append(res_case("CFNT forced check success, empty table",
                          magic=MAGIC_CFNT, force_check=1, chunk_count=0))
    cases.append(res_case("CFNT forced check success, count 0xFFFF",
                          magic=MAGIC_CFNT, force_check=1, chunk_count=0xFFFF,
                          chunks=(finf(0x20),)))

    # --- every accepted chunk tag, and the optional-pointer guards
    cases.append(res_case("CFNT all chunk tags", magic=MAGIC_CFNT,
                          force_check=1, chunk_count=5,
                          chunks=(finf(0x20), cwdh(0x40), cmap(0x60),
                                  tglp(0x80), glgr(0xA0))))
    cases.append(res_case("CFNT FINF optional pointers zero", magic=MAGIC_CFNT,
                          force_check=1, chunk_count=2,
                          chunks=(finf(0x20, p1=0, p2=0), glgr(0x40))))
    cases.append(res_case("CFNT FINF first pointer zero", magic=MAGIC_CFNT,
                          force_check=1, chunk_count=2,
                          chunks=(finf(0x20, p0=0), glgr(0x40))))
    cases.append(res_case("CFNT CWDH pointer zero", magic=MAGIC_CFNT,
                          force_check=1, chunk_count=2,
                          chunks=(cwdh(0x20, p=0), finf(0x40))))
    cases.append(res_case("CFNT CMAP pointer zero", magic=MAGIC_CFNT,
                          force_check=1, chunk_count=2,
                          chunks=(cmap(0x20, p=0), finf(0x40))))
    cases.append(res_case("CFNT TGLP pointer zero", magic=MAGIC_CFNT,
                          force_check=1, chunk_count=2,
                          chunks=(tglp(0x20, p=0), finf(0x40))))
    cases.append(res_case("CFNT two FINF chunks", magic=MAGIC_CFNT,
                          force_check=1, chunk_count=2,
                          chunks=(finf(0x20, p0=0x111, p1=0x222, p2=0x333),
                                  finf(0x40, p0=0x444, p1=0x555, p2=0x666))))
    cases.append(res_case("CFNT GLGR then FINF", magic=MAGIC_CFNT,
                          force_check=1, chunk_count=2,
                          chunks=(glgr(0x20), finf(0x40))))

    # --- unknown tags: both signed groups and one past each known tag
    cases.append(res_case("CFNT unknown tag before FINF", magic=MAGIC_CFNT,
                          force_check=1, chunk_count=2,
                          chunks=(chunk(0x11223344, 0x20), finf(0x40))))
    cases.append(res_case("CFNT unknown tag after FINF", magic=MAGIC_CFNT,
                          force_check=1, chunk_count=2,
                          chunks=(finf(0x20), chunk(0x11223344, 0x40))))
    for tag, label in (
        (TAG_CMAP + 1, "one past CMAP"),
        (TAG_TGLP + 1, "one past TGLP"),
        (TAG_GLGR + 1, "one past GLGR"),
        (TAG_FINF + 1, "one past FINF"),
        (TAG_CWDH + 1, "one past CWDH"),
        (0x80000000, "0x80000000 signed lower group"),
        (0x7FFFFFFF, "0x7FFFFFFF signed upper group"),
        (0x00000000, "zero tag"),
    ):
        cases.append(res_case(f"CFNT unknown {label}", magic=MAGIC_CFNT,
                              force_check=1, chunk_count=2,
                              chunks=(chunk(tag, 0x20), finf(0x40))))
    cases.append(res_case("CFNT unknown tag at chunk_offset 0",
                          magic=MAGIC_CFNT, force_check=1, chunk_count=2,
                          chunk_offset=0, chunks=()))
    cases.append(res_case("CFNT no FINF, all known tags", magic=MAGIC_CFNT,
                          force_check=1, chunk_count=4,
                          chunks=(cmap(0x20), cwdh(0x40), tglp(0x60),
                                  glgr(0x80))))

    # --- loop bounds: count versus the number of planted entries
    cases.append(res_case("CFNT count 2 with FINF only at index 2",
                          magic=MAGIC_CFNT, force_check=1, chunk_count=2,
                          chunks=(glgr(0x20), glgr(0x40), finf(0x60))))
    cases.append(res_case("CFNT count 3 with FINF at index 2",
                          magic=MAGIC_CFNT, force_check=1, chunk_count=3,
                          chunks=(glgr(0x20), glgr(0x40), finf(0x60))))
    cases.append(res_case("CFNT count 4 with FINF at index 3",
                          magic=MAGIC_CFNT, force_check=1, chunk_count=4,
                          chunks=(glgr(0x20), glgr(0x40), glgr(0x60),
                                  finf(0x80))))
    cases.append(res_case("CFNU count 2 with FINF only at index 2",
                          chunk_count=2,
                          chunks=(glgr(0x20), glgr(0x40), finf(0x60))))
    cases.append(res_case("CFNT zero-size FINF repeats", magic=MAGIC_CFNT,
                          force_check=1, chunk_count=2,
                          chunks=(finf(0x20, size=0), glgr(0x40))))
    cases.append(res_case("CFNT zero-size CMAP repeats", magic=MAGIC_CFNT,
                          force_check=1, chunk_count=3,
                          chunks=(cmap(0x20, size=0), glgr(0x40))))
    cases.append(res_case("CFNT zero-size TGLP repeats", magic=MAGIC_CFNT,
                          force_check=1, chunk_count=2,
                          chunks=(tglp(0x20, size=0), finf(0x40))))
    cases.append(res_case("CFNT zero-size CWDH repeats", magic=MAGIC_CFNT,
                          force_check=1, chunk_count=2,
                          chunks=(cwdh(0x20, size=0), finf(0x40))))

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = Runner().run(orig_code, case, FUNC_ADDR)
        cand = Runner().run(cand_code, case, CAND_ADDR)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  (ret={orig['ret']}, "
              f"{len(orig['call_log'])} calls, writes={orig['write_regions']})")
    return passed


def main() -> None:
    print("Testing ui_func_00121b80 (0x00121b80)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
          f"(two call relocations resolved).")
    if len(orig_code) != FUNC_SIZE:
        raise SystemExit("short read of the original function")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("cfnu_magic", "kMagicCfnu = 0x554E4643;", "kMagicCfnu = 0x554E4642;"),
        ("cfnt_magic", "kMagicCfnt = 0x544E4643;", "kMagicCfnt = 0x544E4642;"),
        ("finf_tag", "kChunkFinf = 0x464E4946;", "kChunkFinf = 0x464E4947;"),
        ("cmap_tag", "kChunkCmap = 0x50414D43;", "kChunkCmap = 0x50414D44;"),
        ("glgr_tag", "kChunkGlgr = 0x52474C47;", "kChunkGlgr = 0x52474C48;"),
        ("finf_pointer1_offset",
         "constexpr u32 kWordFinfPointer1 = 0x14 / 4;",
         "constexpr u32 kWordFinfPointer1 = 0x18 / 4;"),
        ("cwdh_pointer_offset",
         "constexpr u32 kWordCwdhPointer = 0x0C / 4;",
         "constexpr u32 kWordCwdhPointer = 0x10 / 4;"),
        ("tglp_pointer_offset",
         "constexpr u32 kWordTglpPointer = 0x1C / 4;",
         "constexpr u32 kWordTglpPointer = 0x18 / 4;"),
        ("header_chunk_words",
         "constexpr u32 kHeaderChunkWords = 2;",
         "constexpr u32 kHeaderChunkWords = 3;"),
        ("finf_second_guard",
         "if (chunk[kWordFinfPointer1] != 0) {",
         "if (chunk[kWordFinfPointer1] != 0) {\n                        chunk[kWordFinfPointer1] += 1;"),
        ("attach_arg_order",
         "        info, base, static_cast<u32>(reinterpret_cast<std::uintptr_t>(found)));",
         "        info, static_cast<u32>(reinterpret_cast<std::uintptr_t>(found)), base);"),
        ("retag_value",
         "        header->magic = kMagicCfnu;\n    }",
         "        header->magic = kMagicCfnt;\n    }"),
        ("cfnu_empty_guard",
         "        if (static_cast<s32>(count) <= 0) {\n            return 0;",
         "        if (static_cast<s32>(count) < 0) {\n            return 0;"),
        ("loop_exit",
         "                if (!(static_cast<s32>(count) > static_cast<s32>(index))) {\n                    break;",
         "                if (!(static_cast<s32>(count) >= static_cast<s32>(index))) {\n                    break;"),
        ("finf_found_pointer",
         "                    found = cursor + sizeof(FontChunk);\n                } else if (tag == kChunkCwdh) {",
         "                    found = cursor;\n                } else if (tag == kChunkCwdh) {"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, case, FUNC_ADDR)
            try:
                bad = Runner().run(mutant_code, case, CAND_ADDR)
            except RuntimeError:
                # A mutant that faults diverges just as clearly as a mutant
                # that writes or returns differently.
                detected = True
                break
            if compare(orig, bad):
                detected = True
                break
        if not detected:
            raise SystemExit(f"negative control failed: {name} was not detected")
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
