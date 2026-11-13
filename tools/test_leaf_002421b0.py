#!/usr/bin/env python3
"""Differential test for ui_func_002421b0 (0x002421b0) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the ui_func_002421b0 body,
resolves its direct calls to deterministic stubs and runs the pinned original
(extracted/exefs/code.bin) against the candidate in separate identical machines.

Compared outputs:
  * return r0, continuation PC, final SP and every callee-saved register r4-r11;
  * the ordered call log with every live register argument plus the architected
    stack word of 0x002DE2A4 (the f32 bit pattern at [sp]);
  * the 0xC8-byte text buffer written through 0x00323660 (content, not address);
  * every "GENERAL %d" destination buffer written through 0x002BE7FC;
  * the full contents of the global UI block page and of each fixture object
    page, plus the absence of writes outside the private stack and the fixture
    pages.

Coverage: both top-level modes (owner word set / cleared), every dispatch state
(0, 1, 2, other, 0xFFFFFFFF), kind code 8 versus every other kind, the node
selection equal / different / null, signed value boundaries (incl. 0x80000000
whose negation is itself), the "GENERAL %d" loop off and its full 0..21 range
with the bit-3 flag, flag values with and without bit 3, the reload of the
global words after helper calls (poll repoints +0x40, kind repoints +0x40, loop
writes +0x3C) and the freshly created object stamps.

Negative controls mutate the loop bound, the selected status word, the kind-8
comparison and the value negation; each mutant must diverge on some case.

A benign codegen difference is expected and not compared: the original re-clears
the already-null owner word at +0x3C with a redundant store, while the compiler
elides that self-store in the candidate (same resulting memory).
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
SOURCE = ROOT / "src/engine/leaf_batch41_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_002421b0"

FUNC_ADDR = 0x002421B0
FUNC_SIZE = 436

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers the function and every stub below 0x3F0000

# Global UI context block at 0x0044EA80 (only this page is meaningful).
GLOB_ADDR = 0x0044EA80
GLOB_PAGE = 0x0044E000
GLOB_PAGE_SIZE = 0x00002000

OWNER_ADDR = 0x00700000
OBJ_ADDR = 0x00710000
COPY_ADDR = 0x00720000
NEW_ADDR = 0x00730000
CONTAINER_ADDR = 0x00740000
RODATA_ADDR = 0x00750000
NODE_ADDR = 0x00760000
OTHER_NODE_ADDR = 0x00790000
BLOB_ADDR = 0x00770000
PAGE_SIZE = 0x00010000

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100
TEXT_SIZE = 0xC8

# Original direct-call targets.  Stubs live at the original addresses so the
# pinned bytes and the relocated candidate resolve to the same handlers.
STUB_2F8270 = 0x002F8270
STUB_323660 = 0x00323660
STUB_318DF8 = 0x00318DF8
STUB_2473AC = 0x002473AC
STUB_24736C = 0x0024736C
STUB_30ED58 = 0x0030ED58
STUB_2BE7FC = 0x002BE7FC
STUB_2DE2A4 = 0x002DE2A4
STUB_246A4C = 0x00246A4C
STUB_242964 = 0x00242964
STUB_25C888 = 0x0025C888
STUB_25CC14 = 0x0025CC14

# 0x2BE7FC is Thumb code in the pinned binary (the original reaches it with
# `blx`); a real linker turns the candidate's R_ARM_CALL into BLX as well.
THUMB_STUBS = {STUB_2BE7FC}

STUB_NAMES = {
    STUB_2F8270: "func_002f8270",
    STUB_323660: "func_00323660",
    STUB_318DF8: "func_00318df8",
    STUB_2473AC: "func_002473ac",
    STUB_24736C: "func_0024736c",
    STUB_30ED58: "func_0030ed58",
    STUB_2BE7FC: "ui_func_002be7fc",
    STUB_2DE2A4: "func_002de2a4",
    STUB_246A4C: "func_00246a4c",
    STUB_242964: "func_00242964",
    STUB_25C888: "func_0025c888",
    STUB_25CC14: "func_0025cc14",
}

# Number of architected stack words each helper receives.
STACK_ARGS = {
    STUB_2DE2A4: 1,  # f32 bit pattern read with `vldr s16, [sp, #0x28]`
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

FIXTURE_PAGES = {
    "glob": (GLOB_PAGE, GLOB_PAGE_SIZE),
    "owner": (OWNER_ADDR, PAGE_SIZE),
    "obj": (OBJ_ADDR, PAGE_SIZE),
    "copy": (COPY_ADDR, PAGE_SIZE),
    "new": (NEW_ADDR, PAGE_SIZE),
    "container": (CONTAINER_ADDR, PAGE_SIZE),
    "node": (NODE_ADDR, PAGE_SIZE),
    "other_node": (OTHER_NODE_ADDR, PAGE_SIZE),
    "blob": (BLOB_ADDR, PAGE_SIZE),
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
        if "002421b0" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"ui_func_002421b0 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (1, 28, 29):
            target = None
            for address in STUB_NAMES:
                if f"{address:08x}" in rel.symbol_name:
                    target = address
                    break
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
            offset = target - (FUNC_ADDR + rel.offset + 8)
            if target in THUMB_STUBS:
                # BLX (immediate): cond=1111 101H, H = bit 1 of the offset.
                if offset & 3:
                    raise RuntimeError(f"unaligned Thumb call target 0x{target:08x}")
                instruction = (
                    0xFA000000
                    | ((offset >> 2) & 0x00FFFFFF)
                    | ((offset & 2) << 23)
                )
                struct.pack_into("<I", code, rel.offset, instruction)
            else:
                original = struct.unpack_from("<I", code, rel.offset)[0]
                cond = original & 0xFF000000
                struct.pack_into(
                    "<I", code, rel.offset, cond | ((offset >> 2) & 0x00FFFFFF)
                )
        elif rel.relocation_type == 2:  # R_ARM_ABS32 into the format string
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            struct.pack_into("<I", code, rel.offset, RODATA_ADDR + addend)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name!r}"
            )

    rodata = elf_sections(obj_file).get(".rodata.str1.1", b"")
    if b"GENERAL %d\x00" not in rodata:
        raise RuntimeError("could not locate the 'GENERAL %d' format string")
    return bytes(code), rodata


def compile_candidate_baseline() -> tuple[bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch41_c.o"
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


# --------------------------------------------------------------------- fixtures
def read_c_string(uc, address: int, limit: int = 64) -> bytes:
    out = bytearray()
    for index in range(limit):
        byte = uc.mem_read(address + index, 1)[0]
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


def build_glob(case: dict) -> bytes:
    page = bytearray(GLOB_PAGE_SIZE)
    for offset in range(0, len(page), 4):
        struct.pack_into("<I", page, offset, 0xA5A5A5A5)
    base = GLOB_ADDR - GLOB_PAGE
    struct.pack_into("<I", page, base + 0x14, CONTAINER_ADDR)
    struct.pack_into("<I", page, base + 0x1C, BLOB_ADDR)
    struct.pack_into("<I", page, base + 0x24, NODE_ADDR)
    if case["owner"]:
        struct.pack_into("<I", page, base + 0x3C, OWNER_ADDR)
        struct.pack_into("<I", page, base + 0x40, OBJ_ADDR)
    else:
        struct.pack_into("<I", page, base + 0x3C, 0)
        # Sentinel proves the create path never dereferences the stale object.
        struct.pack_into("<I", page, base + 0x40, 0x11111111)
    return bytes(page)


def build_page(fill: int) -> bytes:
    page = bytearray(PAGE_SIZE)
    for offset in range(0, len(page), 4):
        struct.pack_into("<I", page, offset, fill)
    return bytes(page)


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(GLOB_PAGE, GLOB_PAGE_SIZE)
        for address, size in FIXTURE_PAGES.values():
            if address == GLOB_PAGE:
                continue
            self.uc.mem_map(address, size)
        self.uc.mem_map(RODATA_ADDR, PAGE_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            if address in THUMB_STUBS:
                self.uc.mem_write(address, struct.pack("<H", 0x4770))  # thumb bx lr
            else:
                self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.text_ptrs: list = []
        self.format_ptrs: list = []
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
            (STUB_NAMES[address], args + self._stack_words(STACK_ARGS.get(address, 0)))
        )

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _repoint_object(self, address: int) -> None:
        uc = self.uc
        uc.mem_write(GLOB_ADDR + 0x40, struct.pack("<I", address))
        uc.mem_write(address + 8, struct.pack("<I", self.case["state"] & 0xFFFFFFFF))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_2F8270:
            self._log(address, r0)
            uc.mem_write(r0 + 8, struct.pack("<I", self.case["state"] & 0xFFFFFFFF))
            if self.case["repoint_on_poll"]:
                self._repoint_object(COPY_ADDR)
        elif address == STUB_323660:
            self._log(address, r0, r1)
            payload = bytes((index * 7 + 3) & 0xFF for index in range(TEXT_SIZE))
            uc.mem_write(r1, payload)
            self.text_ptrs.append(r1)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["kind"] & 0xFFFFFFFF)
            if self.case["repoint_on_kind"]:
                self._repoint_object(COPY_ADDR)
        elif address == STUB_318DF8:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["value"] & 0xFFFFFFFF)
        elif address == STUB_2473AC:
            self._log(address, r0)
        elif address == STUB_24736C:
            self._log(address, r0)
        elif address == STUB_30ED58:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, NEW_ADDR)
        elif address == STUB_2BE7FC:
            fmt = read_c_string(uc, r1)
            self._log(address, fmt, r2)
            if fmt == b"GENERAL %d":
                payload = f"GENERAL {r2}".encode("ascii")
            else:
                payload = fmt
            uc.mem_write(r0, payload + b"\x00")
            self.format_ptrs.append(r0)
            uc.reg_write(arm.UC_ARM_REG_R0, len(payload))
        elif address == STUB_2DE2A4:
            name = read_c_string(uc, r1)
            self._log(address, r0, name, r2, r3)
            if self.case["loop_slot_write"] is not None:
                uc.mem_write(
                    GLOB_ADDR + 0x3C,
                    struct.pack("<I", self.case["loop_slot_write"] & 0xFFFFFFFF),
                )
        elif address == STUB_246A4C:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["selected"] & 0xFFFFFFFF)
        elif address == STUB_242964:
            self._log(address, r0, r1)
        elif address == STUB_25C888:
            self._log(address, r0, r1, r2)
        elif address == STUB_25CC14:
            value = struct.unpack("<I", uc.mem_read(r1, 4))[0]
            self._log(address, r0, value, r2, r3)
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

    def run(self, code: bytes, rodata: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.text_ptrs = []
        self.format_ptrs = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(GLOB_PAGE, build_glob(case))
        for name, (address, size) in FIXTURE_PAGES.items():
            if name == "glob":
                continue
            fill = 0xC0C0C0C0 if name == "owner" else 0xB0B0B0B0
            self.uc.mem_write(address, build_page(fill))
        self.uc.mem_write(OBJ_ADDR + 8, struct.pack("<I", 0xDEADBEEF))
        self.uc.mem_write(COPY_ADDR + 8, struct.pack("<I", 0x99999999))
        self.uc.mem_write(RODATA_ADDR, rodata)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, case["flags"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x12121212)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x23232323)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x34343434)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        text_dumps = [bytes(self.uc.mem_read(ptr, TEXT_SIZE)) for ptr in self.text_ptrs]
        format_dumps = [
            bytes(self.uc.mem_read(ptr, 0x20)) for ptr in self.format_ptrs
        ]

        unexpected_writes = []
        allowed_ranges = [(GLOB_PAGE, GLOB_PAGE + GLOB_PAGE_SIZE)]
        for address, size in FIXTURE_PAGES.values():
            allowed_ranges.append((address, address + size))
        allowed_ranges.append((STACK_ADDR, STACK_ADDR + STACK_SIZE))
        for address, size, _value in self.writes:
            if not any(start <= address < end for start, end in allowed_ranges):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self._normalise(self.call_log),
            "text_dumps": text_dumps,
            "format_dumps": format_dumps,
            "fixtures": {
                name: bytes(self.uc.mem_read(address, size))
                for name, (address, size) in FIXTURE_PAGES.items()
            },
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig="
            + repr(orig["call_log"])
            + "\n    cand="
            + repr(cand["call_log"])
        )
    if orig["text_dumps"] != cand["text_dumps"]:
        problems.append(
            f"text buffer mismatch: {len(orig['text_dumps'])} vs "
            f"{len(cand['text_dumps'])} dumps"
        )
    if orig["format_dumps"] != cand["format_dumps"]:
        problems.append(
            "format buffer mismatch:\n    orig="
            + repr(orig["format_dumps"][:4])
            + "\n    cand="
            + repr(cand["format_dumps"][:4])
        )
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            problems.append(f"fixture {key} was modified differently")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "flags": 0,
        "owner": True,
        "state": 0,
        "kind": 0,
        "value": 0,
        "selected": NODE_ADDR,
        "repoint_on_poll": False,
        "repoint_on_kind": False,
        "loop_slot_write": None,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- active mode: dispatch state sweep (kind 0 keeps the create-only path
    # out of the picture).  state 1 exercises the destroy and commit paths.
    for state in (0, 1, 2, 3, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        cases.append(base_case(f"active state 0x{state:08x}", state=state))
        cases.append(
            base_case(
                f"active state 0x{state:08x} kind 8", state=state, kind=8, value=-1
            )
        )

    # --- kind boundary around the 8 comparison (state 1 only)
    for kind in (0, 7, 8, 9, 0xFFFFFFFF):
        cases.append(
            base_case(f"active kind 0x{kind:08x}", state=1, kind=kind, value=1)
        )

    # --- node selection in the non-8 branch
    for selected in (NODE_ADDR, OTHER_NODE_ADDR, 0):
        cases.append(
            base_case(
                f"active kind 7 selected 0x{selected:08x}",
                state=1,
                kind=7,
                value=-1,
                selected=selected,
            )
        )

    # --- signed value boundaries (negated with 32-bit unsigned arithmetic)
    for value in (0, 1, -1, -2, 0x7FFFFFFF, -0x80000000):
        cases.append(
            base_case(f"active value {value}", state=1, kind=7, value=value)
        )
        cases.append(
            base_case(f"active kind 8 value {value}", state=1, kind=8, value=value)
        )

    # --- create mode: bit 3 of the flags argument gates the generic-name loop
    for flags in (0, 1, 4, 7, 8, 9, 0x0C, 0xFFFFFFFF):
        cases.append(
            base_case(f"create flags 0x{flags:08x}", owner=False, flags=flags)
        )

    # --- global reloads: helper repoints the active object / the loop writes
    # the owner word that is re-read for every registration and for creation.
    cases.append(
        base_case(
            "active poll repoints object",
            state=1,
            kind=8,
            value=-1,
            repoint_on_poll=True,
        )
    )
    cases.append(
        base_case(
            "active kind repoints object",
            state=1,
            kind=7,
            value=-1,
            repoint_on_kind=True,
        )
    )
    cases.append(
        base_case(
            "create loop writes owner word",
            owner=False,
            flags=8,
            loop_slot_write=0x12345678,
        )
    )
    return cases


def run_case_set(orig_code, cand_code, rodata, cases) -> int:
    passed = 0
    for case in cases:
        orig = Runner().run(orig_code, rodata, case)
        cand = Runner().run(cand_code, rodata, case)
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
    print("Testing ui_func_002421b0 (0x002421b0)...")
    orig_code = get_orig_bytes()
    cand_code, cand_rodata = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B, "
        f"rodata {len(cand_rodata)} B (relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cand_rodata, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("loop_bound", "kGenericEntryCount = 0x16;", "kGenericEntryCount = 0x15;"),
        (
            "selected_status",
            "kStatusSelected = 0x00400002;",
            "kStatusSelected = 0x00400003;",
        ),
        ("kind_compare", "if (kind == 8) {", "if (kind == 9) {"),
        (
            "value_negation",
            "0u - static_cast<u32>(value)",
            "static_cast<u32>(value)",
        ),
    ):
        mutant_code, mutant_rodata = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, mutant_rodata, case)
            bad = Runner().run(mutant_code, mutant_rodata, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
