#!/usr/bin/env python3
"""Differential test for script_vm_func_00296a18 (0x00296a18) with Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the script_vm_func_00296a18
body, resolves its fifteen direct calls to deterministic stubs placed at the
pinned target addresses, and runs the pinned original
(extracted/exefs/code.bin) against the candidate in separate Unicorn machines
with identical fixtures.

Compared outputs:
  * return r0, continuation PC (0x90000000), final SP, callee-saved r4-r11;
  * the ordered call log with every architected register argument (all helpers
    are register-only; the pin consumes no stack arguments, so every logged
    stack tuple is empty);
  * the complete 64 KiB work object (ctx+0x0000..+0xFFFF), the manager limit
    page and the resource-slot page, byte for byte;
  * any emulated write outside the fixture pages and the private stack.

Coverage: every mapped state id (0x01, 0x0A, 0x0B, 0x0D..0x12) plus unmapped,
zero, active-state, advance-state, negative and bit-31 state values; the signed
callback count -0x8000, -1, 0, 1, 3, 5, 0x100 and 0x7FFF with callback scripts
that leave, increase, decrease, zero and negate the re-read halfword; the
0x0014 teardown with result 0, result above/equal/below the unsigned limit and
all sign boundaries; state mutations performed by 0x0029F10C and 0x002B8B78
before the post-helper re-read; resource-slot mutation during the advance call.
Negative controls mutate the state mapping, a cleared-field offset, the active
state, the advance selector, the finish request, the transition mask, the loop
comparison and the unsigned limit comparison.
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
OUT_DIR = ROOT / "build/test_leaf_00296a18"

FUNC_ADDR = 0x00296A18
FUNC_SIZE = 448

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers the function and every stub below 0x2F0000
CTX_ADDR = 0x00500000
CTX_SIZE = 0x00010000
LIMIT_ADDR = 0x00510000
LIMIT_SIZE = 0x00001000
SLOT_ADDR = 0x00520000
SLOT_SIZE = 0x00001000
RODATA_ADDR = 0x00700000
RODATA_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Original direct-call targets; stubs are placed at the same addresses so both
# the pinned bytes and the relocated candidate resolve to them.
STUB_2B9008 = 0x002B9008
STUB_29F10C = 0x0029F10C
STUB_2B8B78 = 0x002B8B78
STUB_29A3C4 = 0x0029A3C4
STUB_292F44 = 0x00292F44
STUB_29E260 = 0x0029E260
STUB_29EB14 = 0x0029EB14
STUB_29C768 = 0x0029C768
STUB_292EB0 = 0x00292EB0
STUB_292E94 = 0x00292E94
STUB_2A8A08 = 0x002A8A08
STUB_2954B8 = 0x002954B8
STUB_2971E4 = 0x002971E4
STUB_2B85BC = 0x002B85BC

THUMB_STUBS: set[int] = set()

STUB_NAMES = {
    STUB_2B9008: "camp_func_002b9008",
    STUB_29F10C: "camp_func_0029f10c",
    STUB_2B8B78: "script_vm_func_002b8b78",
    STUB_29A3C4: "script_vm_func_0029a3c4",
    STUB_292F44: "func_00292f44",
    STUB_29E260: "camp_func_0029e260",
    STUB_29EB14: "ui_func_0029eb14",
    STUB_29C768: "script_vm_func_0029c768",
    STUB_292EB0: "script_vm_func_00292eb0",
    STUB_292E94: "script_vm_func_00292e94",
    STUB_2A8A08: "camp_func_002a8a08",
    STUB_2954B8: "script_vm_func_002954b8",
    STUB_2971E4: "script_vm_func_002971e4",
    STUB_2B85BC: "ui_func_002b85bc",
}

# Number of architected stack words each helper receives.  The pinned bodies of
# all fifteen targets are register-only; this table makes the claim explicit.
STACK_ARGS = {address: 0 for address in STUB_NAMES}

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
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + index * e_shentsize)
        for index in range(e_shnum)
    ]
    shstr = sections[e_shstrndx]
    shstrtab = data[shstr[4] : shstr[4] + shstr[5]]
    result: dict[str, bytes] = {}
    for section in sections:
        end = shstrtab.find(b"\x00", section[0])
        name = shstrtab[section[0] : end].decode("ascii", errors="replace")
        result[name] = data[section[4] : section[4] + section[5]]
    return result


def _stub_address(symbol_name: str) -> int | None:
    for address in STUB_NAMES:
        if f"{address:08x}" in symbol_name:
            return address
    return None


def relocate_candidate(obj_file: Path) -> tuple[bytes, bytes]:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "00296a18" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"script_vm_func_00296a18 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            target = _stub_address(rel.symbol_name)
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
            pc = FUNC_ADDR + rel.offset + 8
            displacement = (target - pc) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
            )
        elif rel.relocation_type == 2:  # R_ARM_ABS32 into the switch table
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            struct.pack_into("<I", code, rel.offset, RODATA_ADDR + addend)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name!r}"
            )

    rodata = elf_sections(obj_file).get(".rodata", b"")
    if not rodata:
        raise RuntimeError("candidate .rodata is missing the state transition table")
    return bytes(code), rodata


def compile_candidate() -> tuple[bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch41_c.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> tuple[bytes, bytes]:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    result = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def build_ctx(case: dict) -> bytes:
    page = bytearray(b"\xA5" * CTX_SIZE)
    struct.pack_into("<I", page, 0x352C, case["state"] & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x3530, case.get("previous", 0x11111111))
    struct.pack_into("<I", page, 0x3534, 0x22222222)
    struct.pack_into("<I", page, 0x3538, 0x33333333)
    struct.pack_into("<I", page, 0x353C, 0x44444444)
    struct.pack_into("<I", page, 0x3540, 0x55555555)
    struct.pack_into("<I", page, 0x3544, 0x66666666)
    struct.pack_into("<I", page, 0x3568, case.get("slot", SLOT_ADDR + 0x40) & 0xFFFFFFFF)
    struct.pack_into("<h", page, 0x357C, case.get("count", 0))
    return bytes(page)


def build_limit(case: dict) -> bytes:
    page = bytearray(b"\x5A" * LIMIT_SIZE)
    struct.pack_into("<I", page, 0, case.get("limit", 0) & 0xFFFFFFFF)
    return bytes(page)


def build_slot(case: dict) -> bytes:
    page = bytearray(b"\x6B" * SLOT_SIZE)
    struct.pack_into("<I", page, 0x40, 0x51525354)
    return bytes(page)


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(CTX_ADDR, CTX_SIZE)
        self.uc.mem_map(LIMIT_ADDR, LIMIT_SIZE)
        self.uc.mem_map(SLOT_ADDR, SLOT_SIZE)
        self.uc.mem_map(RODATA_ADDR, RODATA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            if address in THUMB_STUBS:
                self.uc.mem_write(address, struct.pack("<H", 0x4770))
            else:
                self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}
        self.count_index = 0
        self.b8b78_calls = 0

    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        return struct.unpack(f"<{count}I", self.uc.mem_read(sp, 4 * count))

    def _log(self, address: int, *args) -> None:
        self.call_log.append(
            (STUB_NAMES[address], args + self._stack_words(STACK_ARGS[address]))
        )

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def _write_ctx(self, offset: int, value: int, width: int = 4) -> None:
        if width == 4:
            self.uc.mem_write(CTX_ADDR + offset, struct.pack("<I", value & 0xFFFFFFFF))
        elif width == 2:
            self.uc.mem_write(CTX_ADDR + offset, struct.pack("<H", value & 0xFFFF))
        else:
            self.uc.mem_write(CTX_ADDR + offset, struct.pack("<B", value & 0xFF))

    def _read_ctx_word(self, offset: int) -> int:
        return struct.unpack("<I", self.uc.mem_read(CTX_ADDR + offset, 4))[0]

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)

        if address == STUB_2B9008:
            self._log(address, r0)
            script = self.case.get("count_script", ())
            if self.count_index < len(script):
                self._write_ctx(0x357C, script[self.count_index], width=2)
                self.count_index += 1
        elif address == STUB_29F10C:
            self._log(address, r0, r1)
            target = self.case.get("f10c_state_after")
            if target is not None:
                self._write_ctx(0x352C, target)
        elif address == STUB_2B8B78:
            self._log(address, r0)
            self.b8b78_calls += 1
            match = self.case.get("b8b78_state_when")
            if self.case.get("b8b78_state_after") is not None and (
                match is None or r0 == match
            ):
                self._write_ctx(0x352C, self.case["b8b78_state_after"])
                self.case["b8b78_state_after"] = None
            if self.case.get("b8b78_slot_after") is not None and r0 == 0x90:
                self._write_ctx(0x3568, self.case["b8b78_slot_after"])
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("b8b78_ret", 0x0B8B78))
        elif address in (
            STUB_29A3C4,
            STUB_292F44,
            STUB_29E260,
            STUB_29EB14,
            STUB_29C768,
            STUB_2954B8,
        ):
            self._log(address, r0)
            if address == STUB_29C768:
                # The pinned body stores r0's low byte and leaves r0 unchanged.
                uc.reg_write(arm.UC_ARM_REG_R0, r0)
        elif address == STUB_292EB0:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("service_ret", 0x292EB0))
        elif address == STUB_292E94:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("value_ret", 0))
        elif address == STUB_2A8A08:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, LIMIT_ADDR)
        elif address == STUB_2971E4:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("advance_ret", 0x2971E4))
        elif address == STUB_2B85BC:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("finish_ret", 0x2B85BC))
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def run(self, code: bytes, rodata: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.count_index = 0
        self.b8b78_calls = 0
        self.case = dict(case)

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(CTX_ADDR, build_ctx(case))
        self.uc.mem_write(LIMIT_ADDR, build_limit(case))
        self.uc.mem_write(SLOT_ADDR, build_slot(case))
        self.uc.mem_write(RODATA_ADDR, rodata)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, CTX_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case["state"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_ctx = CTX_ADDR <= address < CTX_ADDR + CTX_SIZE
            in_limit = LIMIT_ADDR <= address < LIMIT_ADDR + LIMIT_SIZE
            in_slot = SLOT_ADDR <= address < SLOT_ADDR + SLOT_SIZE
            if not (in_stack or in_ctx or in_limit or in_slot):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "ctx": bytes(self.uc.mem_read(CTX_ADDR, CTX_SIZE)),
            "limit": bytes(self.uc.mem_read(LIMIT_ADDR, LIMIT_SIZE)),
            "slot": bytes(self.uc.mem_read(SLOT_ADDR, SLOT_SIZE)),
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    for key in ("call_log", "ctx", "limit", "slot", "unexpected_writes"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "state": 0,
        "count": 0,
        "slot": SLOT_ADDR + 0x40,
        "limit": 0,
        "value_ret": 0,
        "service_ret": 0x292EB0,
        "advance_ret": 0x2971E4,
        "finish_ret": 0x2B85BC,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- state mapping: every mapped id, plus unmapped/zero/negative values.
    for state in (
        0x00,
        0x01,
        0x02,
        0x09,
        0x0A,
        0x0B,
        0x0C,
        0x0D,
        0x0E,
        0x0F,
        0x10,
        0x11,
        0x12,
        0x13,
        0x14,
        0x15,
        0x16,
        0xFFFFFFFF,
        0x80000000,
        0x7FFFFFFF,
    ):
        cases.append(base_case(f"state 0x{state:08x}", state=state, count=0))
        # Exercise the map with a non-zero drain too, but keep it short.
        cases.append(
            base_case(f"state 0x{state:08x} count 3", state=state, count=3)
        )

    # --- signed callback-count boundaries and callback-driven re-reads.
    for count in (-0x8000, -1, 0, 1, 3, 5, 0x100, 0x7FFF):
        cases.append(base_case(f"count {count}", state=0, count=count))
    for name, initial, script in (
        ("decreasing", 5, [3, 2, 1, 0]),
        ("increasing", 1, [4, 0]),
        ("negated", 2, [-1]),
        ("pinned high", 3, [3, 3, 3, 0]),
        ("zeroed first", 4, [0]),
        ("signed max then zero", 0x7FFF, [0]),
        ("signed min", -0x8000, [5]),
    ):
        cases.append(
            base_case(
                f"callback {name}",
                state=0,
                count=initial,
                count_script=script,
            )
        )

    # --- active state 0x14 teardown: zero, limit boundaries, signed boundaries.
    for value, limit, label in (
        (0, 0, "zero"),
        (0, 0xFFFFFFFF, "zero with limit"),
        (1, 0, "above zero limit"),
        (1, 1, "equal limit"),
        (1, 2, "below limit"),
        (0xFFFFFFFF, 0xFFFFFFFF, "max equal max"),
        (0xFFFFFFFF, 0xFFFFFFFE, "max above"),
        (0x80000000, 0x7FFFFFFF, "negative above positive"),
        (0x7FFFFFFF, 0x80000000, "positive below negative"),
        (0x100, 0x0FF, "just above"),
        (0x100, 0x100, "just equal"),
        (0x100, 0x101, "just below"),
    ):
        cases.append(
            base_case(
                f"state 0x14 value {label}",
                state=0x14,
                value_ret=value,
                limit=limit,
            )
        )

    # --- the teardown service result is forwarded to 0x00292E94.
    for service in (0, 1, 0x12345678, 0xFFFFFFFF):
        cases.append(
            base_case(
                f"service result 0x{service:08x}",
                state=0x14,
                service_ret=service,
                value_ret=1,
                limit=1,
            )
        )

    # --- state re-read after the mapped helpers.
    cases.append(
        base_case(
            "mapped helper rewrites state",
            state=0x01,
            b8b78_state_after=0x99,
            count=1,
        )
    )
    cases.append(
        base_case(
            "mapped helper enters active state",
            state=0x01,
            b8b78_state_after=0x14,
            value_ret=1,
            limit=1,
            count=1,
        )
    )
    cases.append(
        base_case(
            "message helper rewrites state",
            state=0x0E,
            f10c_state_after=0x14,
            value_ret=1,
            limit=1,
            count=0,
        )
    )
    cases.append(
        base_case(
            "message helper returns to ordinary state",
            state=0x12,
            f10c_state_after=0x05,
            count=2,
        )
    )

    # --- advance path: slot is re-read after the 0x90 transition request.
    cases.append(
        base_case(
            "advance slot mutation",
            state=0x14,
            value_ret=1,
            limit=1,
            b8b78_slot_after=SLOT_ADDR + 0x80,
            slot=SLOT_ADDR + 0x40,
        )
    )
    for slot in (0, 0xFFFFFFFF, SLOT_ADDR + 0x80):
        cases.append(
            base_case(
                f"advance slot 0x{slot & 0xFFFFFFFF:08x}",
                state=0x14,
                value_ret=0x20,
                limit=0x20,
                slot=slot,
            )
        )

    # --- distinct return values prove each tail result is forwarded.
    cases.append(
        base_case(
            "advance return forwarded",
            state=0x14,
            value_ret=1,
            limit=1,
            advance_ret=0xA5A50001,
        )
    )
    cases.append(
        base_case(
            "finish return forwarded",
            state=0x14,
            value_ret=1,
            limit=0,
            finish_ret=0xA5A50002,
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
    print("Testing script_vm_func_00296a18 (0x00296a18)...")
    orig_code = get_orig_bytes()
    cand_code, cand_rodata = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B, "
        f"rodata {len(cand_rodata)} B (relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cand_rodata, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("state_0e_mapping", "constexpr u32 kState0EId = 0xDF;",
         "constexpr u32 kState0EId = 0xDE;"),
        ("cleared_word_a_offset", "constexpr u32 kClearedWordAOffset = 0x3534;",
         "constexpr u32 kClearedWordAOffset = 0x3538;"),
        ("active_state", "constexpr u32 kActiveState = 0x14;",
         "constexpr u32 kActiveState = 0x15;"),
        ("advance_selector", "constexpr u32 kAdvanceSelector = 5;",
         "constexpr u32 kAdvanceSelector = 6;"),
        ("finish_state", "constexpr u32 kFinishState = 3;",
         "constexpr u32 kFinishState = 4;"),
        ("transition_mask", "script_vm_func_002b8b78(transition & 0xFFu);",
         "script_vm_func_002b8b78(transition & 0x0Fu);"),
        ("loop_comparison",
         "            ++index;\n"
         "        } while (count > index);\n"
         "    }\n"
         "    *reinterpret_cast<volatile s16*>(ctx + kCallbackCountOffset) = 0;",
         "            ++index;\n"
         "        } while (count >= index);\n"
         "    }\n"
         "    *reinterpret_cast<volatile s16*>(ctx + kCallbackCountOffset) = 0;"),
        ("limit_comparison",
         "if (value == 0 || value > *camp_func_002a8a08(value)) {",
         "if (value == 0 || value >= *camp_func_002a8a08(value)) {"),
    ):
        mutant_code, mutant_rodata = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, cand_rodata, case)
            bad = Runner().run(mutant_code, mutant_rodata, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
