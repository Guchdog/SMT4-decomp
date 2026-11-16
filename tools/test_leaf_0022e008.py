#!/usr/bin/env python3
"""Differential test for camp_func_0022e008 (0x0022e008) using Unicorn ARM emulation.

Compiles src/engine/leaf_batch45_a.cpp, extracts the camp_func_0022e008 body,
resolves every direct call to a deterministic stub address, and runs the pinned
original (extracted/exefs/code.bin) against the candidate in separate Unicorn
machines with identical fixtures.  Compared outputs:

  * return value, continuation PC, final SP, callee-saved r4-r11
  * ordered call log (helper name + meaningful arguments; stack pointers are
    normalised relative to the scratch buffer base)
  * full camp-work memory image and the 0x610-byte stack scratch record

Covers: empty-list tail call, 0x29e398 == 0 early return, mode 0 with both dirty
flag values, mode 1 with sub-mode 0 and 1, the 0x2a8a08 list loop with zero /
matching / non-matching / negative slot entries, plus negative controls that
must be detected (wrong selection store and wrong notification argument).
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
FUNC_ADDR = 0x0022e008
FUNC_SIZE = 572

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00100000
WORK_ADDR = 0x00500000
WORK_SIZE = 0x00010000
TABLE_ADDR = 0x00600000
TABLE_SIZE = 0x00040000
INFO_ADDR = 0x00700000
INFO_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Original direct-call target addresses.  Stubs are placed at the exact same
# addresses so both the original bytes and the relocated candidate resolve to
# the same deterministic handlers.
STUB_2337A0 = 0x002337A0
STUB_29E398 = 0x0029E398
STUB_29DB40 = 0x0029DB40
STUB_29D924 = 0x0029D924
STUB_22D33C = 0x0022D33C
STUB_2A8A08 = 0x002A8A08
STUB_2B9364 = 0x002B9364
STUB_2BCF58 = 0x002BCF58
STUB_2C4B30 = 0x002C4B30
STUB_24BE90 = 0x0024BE90
STUB_29C950 = 0x0029C950
STUB_29C784 = 0x0029C784
STUB_29C768 = 0x0029C768
STUB_258C58 = 0x00258C58
STUB_29E260 = 0x0029E260

STUB_NAMES = {
    STUB_2337A0: "shop_func_002337a0",
    STUB_29E398: "script_vm_func_0029e398",
    STUB_29DB40: "camp_func_0029db40",
    STUB_29D924: "camp_func_0029d924",
    STUB_22D33C: "camp_func_0022d33c",
    STUB_2A8A08: "camp_func_002a8a08",
    STUB_2B9364: "camp_func_002b9364",
    STUB_2BCF58: "ui_func_002bcf58",
    STUB_2C4B30: "engine_func_002c4b30",
    STUB_24BE90: "camp_func_0024be90",
    STUB_29C950: "script_vm_func_0029c950",
    STUB_29C784: "script_vm_func_0029c784",
    STUB_29C768: "script_vm_func_0029c768",
    STUB_258C58: "ui_func_00258c58",
    STUB_29E260: "camp_func_0029e260",
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
CALLEE_SAVED_REGS = {
    "r4": arm.UC_ARM_REG_R4,
    "r5": arm.UC_ARM_REG_R5,
    "r6": arm.UC_ARM_REG_R6,
    "r7": arm.UC_ARM_REG_R7,
    "r8": arm.UC_ARM_REG_R8,
    "r9": arm.UC_ARM_REG_R9,
    "r10": arm.UC_ARM_REG_R10,
    "r11": arm.UC_ARM_REG_R11,
}


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def compile_candidate() -> bytes:
    out_dir = ROOT / "build/test_leaf_0022e008"
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_file = out_dir / "leaf_batch45_a.o"
    src_file = ROOT / "src/engine/leaf_batch45_a.cpp"
    res = compile_tu_armv6k(src_file, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")

    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0022e008" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"camp_func_0022e008 not found in {obj_file}: {sorted(funcs)}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (1, 28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} for {rel.symbol_name}"
            )
        target = None
        for address, name in STUB_NAMES.items():
            if f"{address:08x}" in rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        cond = original & 0xFF000000
        struct.pack_into("<I", code, rel.offset, cond | (displacement & 0x00FFFFFF))
    return bytes(code)


def build_table(case: dict) -> bytes:
    buf = bytearray((i * 73 + 0x5A) & 0xFF for i in range(TABLE_SIZE))
    count = case.get("table_count", 0)
    buf[0x910B] = count & 0xFF
    for i, slot in enumerate(case.get("table_slots", [])):
        buf[0x90F0 + i] = slot & 0xFF
    for slot, ident in case.get("table_ids", {}).items():
        struct.pack_into("<H", buf, slot * 0x604 + 0xD6, ident & 0xFFFF)
    return bytes(buf)


def build_info(case: dict) -> bytes:
    buf = bytearray((i * 29 + 0x33) & 0xFF for i in range(INFO_SIZE))
    struct.pack_into("<H", buf, 0x38, case.get("info_bits", 0x0F2) & 0xFFFF)
    return bytes(buf)


def build_work(case: dict) -> bytes:
    work = bytearray(WORK_SIZE)
    struct.pack_into("<H", work, 0x5A8, case.get("a8", 1) & 0xFFFF)
    work[0x5A4] = case.get("a4", 0) & 0xFF
    work[0x5A5] = case.get("a5", 0) & 0xFF
    work[0x5A7] = case.get("a7", 0) & 0xFF
    struct.pack_into("<H", work, 0xA5B2, case.get("selected", 0) & 0xFFFF)
    index = case.get("entry_index", 2)
    struct.pack_into(
        "<H", work, 0x5A8 + index * 0x20 + 4, case.get("entry_id", 0) & 0xFFFF
    )
    return bytes(work)


class CampRunner:
    """One Unicorn machine with stubs at the original call-target addresses."""

    def __init__(self):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(WORK_ADDR, WORK_SIZE)
        self.uc.mem_map(TABLE_ADDR, TABLE_SIZE)
        self.uc.mem_map(INFO_ADDR, INFO_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        # bx lr stubs at every direct-call target.
        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))
            self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address)

        # Track emulated writes so stray memory effects are visible.
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log = []
        self.writes = []
        self.buf_dest = None
        self.fixture = {}

    def _log(self, address, *args):
        self.call_log.append((STUB_NAMES[address], args))

    def _on_write(self, uc, access, address, size, value, user_data):
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address, size, user_data):
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)

        if address == STUB_2337A0:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self.fixture["entry_index"])
        elif address == STUB_29E398:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self.fixture["e398"])
        elif address == STUB_29DB40:
            self._log(address, r0)
        elif address == STUB_29D924:
            self._log(address, r0)
        elif address == STUB_22D33C:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self.fixture["d33c"])
        elif address == STUB_2A8A08:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, TABLE_ADDR)
        elif address == STUB_2B9364:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, INFO_ADDR)
        elif address == STUB_2BCF58:
            self._log(address, r0, r1, r2)
            if self.buf_dest is None:
                self.buf_dest = r0
            if r2:
                if r1 == 0:
                    data = b"\x00" * r2
                else:
                    data = bytes(uc.mem_read(r1, r2))
                uc.mem_write(r0, data)
        elif address == STUB_2C4B30:
            self._log(address, r0, r1)
            if r1:
                uc.mem_write(r0, b"\x00" * r1)
        elif address == STUB_24BE90:
            self._log(address, r0, r1)
            byte_addr = r0 + (r1 >> 3) + 0x4C
            mask = 1 << (r1 & 7)
            old = uc.mem_read(byte_addr, 1)[0]
            uc.mem_write(byte_addr, bytes((old | mask,)))
        elif address == STUB_29C950:
            self._log(address, r0)
        elif address == STUB_29C784:
            self._log(address, r0, r1)
        elif address == STUB_29C768:
            self._log(address, r0)
        elif address == STUB_258C58:
            self._log(address, r0)
        elif address == STUB_29E260:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self.fixture["e260"])
        else:
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    @staticmethod
    def _normalise(log, buf_dest):
        normalised = []
        for name, args in log:
            out = []
            for arg in args:
                if buf_dest is not None and STACK_ADDR <= arg < STACK_ADDR + STACK_SIZE:
                    out.append(("stack", arg - buf_dest))
                else:
                    out.append(arg)
            normalised.append((name, tuple(out)))
        return normalised

    def run(self, code: bytes, case: dict):
        self.call_log = []
        self.writes = []
        self.buf_dest = None
        self.fixture = {
            "entry_index": case.get("entry_index", 2),
            "e398": case.get("e398", 1),
            "d33c": case.get("d33c", 0xD33C),
            "e260": case.get("e260", 0xE260),
        }

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(WORK_ADDR, build_work(case))
        self.uc.mem_write(TABLE_ADDR, build_table(case))
        self.uc.mem_write(INFO_ADDR, build_info(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, WORK_ADDR)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED_REGS[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5000000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        scratch = None
        if self.buf_dest is not None:
            scratch = bytes(self.uc.mem_read(self.buf_dest, 0x610))

        unexpected_writes = []
        for address, size, _value in self.writes:
            in_work = WORK_ADDR <= address < WORK_ADDR + WORK_SIZE
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            if not in_work and not in_stack:
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED_REGS.items()
            },
            "call_log": self._normalise(self.call_log, self.buf_dest),
            "work": bytes(self.uc.mem_read(WORK_ADDR, WORK_SIZE)),
            "scratch": scratch,
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict):
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "call_log", "work"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["scratch"] != cand["scratch"]:
        problems.append("scratch record differs")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            f"unexpected writes orig={orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def make_cases():
    cases = []

    # 1. Empty list: immediate tail call with a zero argument.
    cases.append(
        {
            "name": "empty list -> camp_func_0029e260(0)",
            "a8": 0,
        }
    )

    # 2. Non-empty list but the entry predicate rejects it.
    cases.append(
        {
            "name": "0x29e398 == 0 early return",
            "a8": 1,
            "entry_id": 0x1234,
            "e398": 0,
        }
    )

    # 3. Mode 0, selection already current -> no calls past the predicate.
    cases.append(
        {
            "name": "mode 0, same id -> return selected",
            "a8": 1,
            "a4": 0,
            "entry_id": 0x2222,
            "selected": 0x2222,
            "e398": 1,
        }
    )

    # 4/5. Mode 0, selection changes, with both dirty-flag values.  The mode 0
    # path never consults 0xA7, but exercising both proves that.
    for a7 in (0, 1):
        cases.append(
            {
                "name": f"mode 0, new id, dirty={a7}",
                "a8": 1,
                "a4": 0,
                "a7": a7,
                "entry_id": 0x3344,
                "selected": 0x1111,
                "e398": 1,
            }
        )

    # 6. Mode 1, sub-mode 0, clean + same id -> early return.
    cases.append(
        {
            "name": "mode 1, sub-mode 0, clean, same id",
            "a8": 1,
            "a4": 1,
            "a5": 0,
            "a7": 0,
            "entry_id": 0x4455,
            "selected": 0x4455,
            "e398": 1,
        }
    )

    # 7. Mode 1, sub-mode 0, clean + new id -> no animation callback.
    cases.append(
        {
            "name": "mode 1, sub-mode 0, clean, new id",
            "a8": 1,
            "a4": 1,
            "a5": 0,
            "a7": 0,
            "entry_id": 0x5566,
            "selected": 0x1111,
            "e398": 1,
        }
    )

    # 8. Mode 1, sub-mode 0, dirty -> animation callback with argument 0.
    cases.append(
        {
            "name": "mode 1, sub-mode 0, dirty, new id",
            "a8": 1,
            "a4": 1,
            "a5": 0,
            "a7": 1,
            "entry_id": 0x5566,
            "selected": 0x1111,
            "e398": 1,
        }
    )

    # 9/10. Mode 1, sub-mode 1, zero-entry 0x2a8a08 list, both dirty values.
    for a7 in (0, 1):
        cases.append(
            {
                "name": f"mode 1, sub-mode 1, zero list entries, dirty={a7}",
                "a8": 1,
                "a4": 1,
                "a5": 1,
                "a7": a7,
                "entry_id": 0x6677,
                "selected": 0x1111,
                "e398": 1,
                "table_count": 0,
            }
        )

    # 11. Matching list entry (slot 2) -> the copy source is that record.
    cases.append(
        {
            "name": "mode 1, sub-mode 1, matching slot 2",
            "a8": 1,
            "a4": 1,
            "a5": 1,
            "a7": 1,
            "entry_id": 0x7788,
            "selected": 0x1111,
            "e398": 1,
            "table_count": 1,
            "table_slots": [2],
            "table_ids": {2: 0x7788},
        }
    )

    # 12. No matching entry: record_base tracks the last valid slot (1).
    cases.append(
        {
            "name": "mode 1, sub-mode 1, no matching slot",
            "a8": 1,
            "a4": 1,
            "a5": 1,
            "a7": 0,
            "entry_id": 0x7788,
            "selected": 0x1111,
            "e398": 1,
            "table_count": 1,
            "table_slots": [1],
            "table_ids": {1: 0x9999},
        }
    )

    # 13. Two valid slots with the match on the second one.
    cases.append(
        {
            "name": "mode 1, sub-mode 1, match on second slot",
            "a8": 1,
            "a4": 1,
            "a5": 1,
            "a7": 1,
            "entry_id": 0x8899,
            "selected": 0x1111,
            "e398": 1,
            "table_count": 2,
            "table_slots": [1, 3],
            "table_ids": {1: 0xAAAA, 3: 0x8899},
        }
    )

    # 14. Negative slot bytes are skipped; the last valid slot still loses.
    cases.append(
        {
            "name": "mode 1, sub-mode 1, negative slot skipped",
            "a8": 1,
            "a4": 1,
            "a5": 1,
            "a7": 0,
            "entry_id": 0x8899,
            "selected": 0x1111,
            "e398": 1,
            "table_count": 2,
            "table_slots": [-1, 2],
            "table_ids": {2: 0xBBBB},
        }
    )

    return cases


def mutate_wrong_store(code: bytes) -> bytes:
    """Change the shared selection store to write a different register."""
    mutated = bytearray(code)
    patched = 0
    for offset in range(0, len(mutated) - 3, 4):
        inst = struct.unpack_from("<I", mutated, offset)[0]
        # STRH r11, [r10, #0] -- the selection store at each return site.
        if (inst & 0x0FF0FFFF) == 0x01C0B0B0:
            new_inst = (inst & ~0xF000) | (0xA << 12)  # store r10 instead of r11
            struct.pack_into("<I", mutated, offset, new_inst)
            patched += 1
    if patched == 0:
        raise RuntimeError("negative control: no STRH #0 instruction found")
    return bytes(mutated)


def mutate_wrong_argument(relocated_code: bytes) -> bytes | None:
    """Change the camp_func_0029d924 argument from 1 to 2 when locatable."""
    mutated = bytearray(relocated_code)
    patched = 0
    for offset in range(0, len(mutated) - 7, 4):
        # mov r0, #1 immediately followed by the relocated bl 29d924.
        inst = struct.unpack_from("<I", mutated, offset)[0]
        nxt = struct.unpack_from("<I", mutated, offset + 4)[0]
        if (inst & 0x0FFFFFFF) == 0x03A00001 and (nxt & 0x0F000000) == 0x0B000000:
            target = FUNC_ADDR + (offset + 4) + 8 + ((nxt & 0x00FFFFFF) << 2)
            if target == STUB_29D924:
                struct.pack_into("<I", mutated, offset, 0xE3A00002)
                patched += 1
    if patched == 0:
        return None
    return bytes(mutated)


def main():
    print("Testing camp_func_0022e008 (0x0022e008)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B (relocations resolved).")

    cases = make_cases()

    passed = 0
    for case in cases:
        # A fresh machine per side avoids reuse of translated blocks.
        orig = CampRunner().run(orig_code, case)
        cand = CampRunner().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")

    # Negative controls: both mutants must be rejected by the same comparison.
    print("\nNegative controls:")

    bad_store = mutate_wrong_store(cand_code)
    detected_store = False
    for case in cases:
        orig = CampRunner().run(orig_code, case)
        mutant = CampRunner().run(bad_store, case)
        if compare(orig, mutant):
            detected_store = True
            break
    assert detected_store, "negative control failed: wrong selection store was not detected"
    print("  [PASS] wrong selection store is detected")

    bad_arg = mutate_wrong_argument(cand_code)
    if bad_arg is None:
        print("  [SKIP] wrong-argument mutant pattern not present")
    else:
        detected_arg = False
        for case in cases:
            orig = CampRunner().run(orig_code, case)
            mutant = CampRunner().run(bad_arg, case)
            if compare(orig, mutant):
                detected_arg = True
                break
        assert detected_arg, "negative control failed: wrong 0x29d924 argument was not detected"
        print("  [PASS] wrong camp_func_0029d924 argument is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
