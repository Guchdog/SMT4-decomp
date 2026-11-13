#!/usr/bin/env python3
"""Differential test for script_vm_func_00191b64 (0x00191b64) using Unicorn ARM.

The pinned original is straight-line.  It calls the interaction-table getter
(0x002b66ec) ten times: for each of five halfword fields it
  (a) reads the signed table value at table+0x12+2*i, differences it against
      the signed value of the selected 0x3600-table entry at entry+0x6a+2*i,
      and adds the difference to a signed sum, then
  (b) calls the getter again and copies the unsigned entry value over the
      table value.
The getter result is used after every call, the selected index at
context+0xcf78 is re-read after every call, and the signed sum is finally
added (32-bit wrap) to the accumulator at context+0xcfcc.

The getter is replaced by a deterministic stub that returns scripted table
addresses, can rewrite the selected index and entry fields between calls, and
logs every call.  Original and candidate are compared on the ordered call log,
continuation PC/SP, callee-saved registers, and every mapped byte of the
context and table regions.  A null getter result is covered separately: both
bodies must fault on the first dereference without writing observable memory.
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
FUNC_ADDR = 0x00191B64
FUNC_SIZE = 400
FUNC_SYMBOL = "script_vm_func_00191b64"

HELPER_ADDR = 0x002B66EC
HELPER_SYMBOL = "script_vm_func_002b66ec"

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers 0x00100000..0x00300000
CTX_ADDR = 0x00500000
CTX_SIZE = 0x00020000
TABLE_ADDR = 0x00700000
TABLE_SIZE = 0x00010000
WRAP_ADDR = 0x20500000
WRAP_SIZE = 0x00020000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

CTX_INDEX = 0xCF78      # 0xCC00 + 0x378
CTX_ACC = 0xCFCC        # 0xCC00 + 0x3CC
ENTRY_BASE = 0x3600
ENTRY_STRIDE = 0x620    # ((index * 49) << 5)
TABLE_FIELD_BASE = 0x12
ENTRY_FIELD_BASE = 0x6A
FIELD_COUNT = 5

TABLE_BUFFER_STRIDE = 0x40


def h16(value):
    return value & 0xFFFF


def entry_addr(index):
    offset = (index * ENTRY_STRIDE) & 0xFFFFFFFF
    return (CTX_ADDR + ENTRY_BASE + offset) & 0xFFFFFFFF


def get_orig_bytes():
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def compile_candidate_from(src_file, obj_file):
    res = compile_tu_armv6k(src_file, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")

    funcs = extract_elf_functions_detailed(obj_file)
    entry = funcs.get(FUNC_SYMBOL)
    if entry is None:
        raise RuntimeError(
            f"{FUNC_SYMBOL} not found in object: " + ", ".join(sorted(funcs))
        )

    code = bytearray(entry[0])
    errors = []
    call_count = 0
    for rel in entry[1]:
        if rel.relocation_type not in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            errors.append(f"unexpected relocation {rel.relocation_type} {rel.symbol_name}")
            continue
        if rel.symbol_name != HELPER_SYMBOL:
            errors.append(f"unexpected call target {rel.symbol_name}")
            continue
        pc = FUNC_ADDR + rel.offset + 8
        disp = (HELPER_ADDR - pc) >> 2
        orig_inst = struct.unpack_from("<I", code, rel.offset)[0]
        cond = orig_inst & 0xFF000000
        struct.pack_into("<I", code, rel.offset, cond | (disp & 0x00FFFFFF))
        call_count += 1
    if errors:
        raise RuntimeError("; ".join(errors))
    if call_count != 10:
        raise RuntimeError(f"expected 10 getter calls, found {call_count}")
    return bytes(code)


def compile_candidate():
    out_dir = ROOT / "build/test_leaf_00191b64"
    out_dir.mkdir(parents=True, exist_ok=True)
    return compile_candidate_from(
        ROOT / "src/engine/leaf_batch28_a.cpp",
        out_dir / "engine" / "leaf_batch28_a.o",
    )


def compile_mutant(name, replacements):
    out_dir = ROOT / "build/test_leaf_00191b64"
    out_dir.mkdir(parents=True, exist_ok=True)
    source = ROOT / "src/engine/leaf_batch28_a.cpp"
    text = source.read_text(encoding="utf-8")
    for old, new in replacements:
        count = text.count(old)
        if count == 0:
            raise RuntimeError(f"mutation anchor {old!r} not found")
        text = text.replace(old, new)
    mutant_src = out_dir / f"mutant_{name}.cpp"
    mutant_src.write_text(text, encoding="utf-8")
    return compile_candidate_from(mutant_src, out_dir / f"mutant_{name}.o")


def default_tables(base):
    """Ten distinct table buffers, each with five distinct field values."""
    tables = []
    for buffer_index in range(10):
        tables.append([
            h16(base + buffer_index * 0x31 + field * 0x111)
            for field in range(FIELD_COUNT)
        ])
    return tables


class Runner:
    def __init__(self):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(CTX_ADDR, CTX_SIZE)
        self.uc.mem_map(TABLE_ADDR, TABLE_SIZE)
        self.uc.mem_map(WRAP_ADDR, WRAP_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        self.call_log = []
        self.call_count = 0
        self.script = {}
        self.table_mode = "rotate"
        self.null_at = None

        self.uc.mem_write(HELPER_ADDR, struct.pack("<I", 0xE12FFF1E))  # bx lr
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE, self._on_helper, begin=HELPER_ADDR, end=HELPER_ADDR
        )

    def _read_index(self):
        return struct.unpack("<I", self.uc.mem_read(CTX_ADDR + CTX_INDEX, 4))[0]

    def _write_index(self, index):
        self.uc.mem_write(CTX_ADDR + CTX_INDEX, struct.pack("<I", index & 0xFFFFFFFF))

    def _on_helper(self, uc, address, size, user_data):
        ordinal = self.call_count
        self.call_count += 1
        action = self.script.get(ordinal, {})

        # A scripted index rewrite models the getter mutating the writable
        # index between calls; the body must re-read it after every call.
        if "index" in action:
            self._write_index(action["index"])

        if "entry_fields" in action:
            index = self._read_index()
            base = entry_addr(index)
            for offset, value in action["entry_fields"].items():
                uc.mem_write(base + offset, struct.pack("<H", h16(value)))

        if self.null_at == ordinal:
            returned = 0
        elif self.table_mode == "table":
            returned = action.get("table", TABLE_ADDR)
        elif self.table_mode == "same":
            returned = TABLE_ADDR
        else:
            returned = TABLE_ADDR + ordinal * TABLE_BUFFER_STRIDE

        self.call_log.append((HELPER_SYMBOL, ordinal, returned))
        uc.reg_write(arm.UC_ARM_REG_R0, returned)

    def _prepare(self, case):
        self.uc.mem_write(CTX_ADDR, b"\x5a" * CTX_SIZE)
        self.uc.mem_write(TABLE_ADDR, b"\xa5" * TABLE_SIZE)
        self.uc.mem_write(WRAP_ADDR, b"\xc3" * WRAP_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        self._write_index(case["index"])
        self.uc.mem_write(
            CTX_ADDR + CTX_ACC, struct.pack("<I", case["accumulator"] & 0xFFFFFFFF)
        )

        for index, values in case.get("entries", {}).items():
            base = entry_addr(index)
            for field, value in enumerate(values):
                self.uc.mem_write(
                    base + ENTRY_FIELD_BASE + field * 2,
                    struct.pack("<H", h16(value)),
                )

        for buffer_index, values in enumerate(case.get("tables", [])):
            base = TABLE_ADDR + buffer_index * TABLE_BUFFER_STRIDE
            for field, value in enumerate(values):
                self.uc.mem_write(
                    base + TABLE_FIELD_BASE + field * 2,
                    struct.pack("<H", h16(value)),
                )

    def run(self, code_bytes, case):
        self.call_log = []
        self.call_count = 0
        self.script = case.get("script", {})
        self.table_mode = case.get("table_mode", "rotate")
        self.null_at = case.get("null_at")

        self._prepare(case)

        self.uc.mem_write(FUNC_ADDR, code_bytes)
        # Unicorn caches translated blocks; the original and candidate bodies
        # live at the same address, so the cache must be flushed every run.
        self.uc.ctl_remove_cache(FUNC_ADDR, FUNC_ADDR + 0x1000)

        sp = STACK_ADDR + STACK_SIZE - 0x100
        self.uc.reg_write(arm.UC_ARM_REG_SP, sp)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, CTX_ADDR)

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

        fault = None
        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5000000)
        except unicorn.UcError as exc:
            fault = getattr(exc, "errno", None)

        return {
            "call_log": list(self.call_log),
            "fault": fault,
            "context": bytes(self.uc.mem_read(CTX_ADDR, CTX_SIZE)),
            "table": bytes(self.uc.mem_read(TABLE_ADDR, TABLE_SIZE)),
            "wrap": bytes(self.uc.mem_read(WRAP_ADDR, WRAP_SIZE)),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "r0": self.uc.reg_read(arm.UC_ARM_REG_R0),
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


def make_cases():
    cases = []

    cases.append({
        "name": "index 0, per-call table buffers, positive fields",
        "index": 0,
        "accumulator": 0x00000000,
        "tables": default_tables(0x120),
        "entries": {0: [1, 2, 3, 4, 5]},
    })

    cases.append({
        "name": "index 3, signed high-bit fields (0x8000/0x7FFF/0xFFFF)",
        "index": 3,
        "accumulator": 0x12345678,
        "tables": [[0x8000, 0xFFFF, 0x7FFF, 0x0000, 0xFFFF]] + default_tables(0x220)[1:],
        "entries": {3: [0x7FFF, 0x8000, 0x0001, 0xFFFF, 0x0000]},
    })

    entries = {
        0: [10, 20, 30, 40, 50],
        1: [11, 21, 31, 41, 51],
        4: [14, 24, 34, 44, 54],
        7: [17, 27, 37, 47, 57],
    }
    cases.append({
        "name": "index re-read: script rewrites index after calls 2 and 6",
        "index": 0,
        "accumulator": 0xFFFFFFFF,
        "tables": default_tables(0x320),
        "entries": entries,
        "script": {
            2: {"index": 1},
            6: {"index": 4},
        },
    })

    cases.append({
        "name": "entry fields re-read: mutations during read and copy calls",
        "index": 2,
        "accumulator": 0x00000007,
        "tables": default_tables(0x420),
        "entries": {2: [100, 200, 300, 400, 500]},
        "script": {
            0: {"entry_fields": {0x6E: 0x7777}},
            2: {"entry_fields": {0x6C: 0x1234}},
            3: {"entry_fields": {0x72: 0x8001}},
            9: {"entry_fields": {0x70: 0xFFFF}},
        },
    })

    cases.append({
        "name": "accumulator positive wrap (0xFFFFFFF0 + 5*0x7FFF)",
        "index": 1,
        "accumulator": 0xFFFFFFF0,
        "tables": [[0x7FFF] * 5 for _ in range(10)],
        "entries": {1: [0, 0, 0, 0, 0]},
    })

    cases.append({
        "name": "accumulator negative wrap (0x00000005 + 5*(-0xFFFF))",
        "index": 1,
        "accumulator": 0x00000005,
        "tables": [[0x8000] * 5 for _ in range(10)],
        "entries": {1: [0x7FFF] * 5},
    })

    cases.append({
        "name": "index 0x01000000: 32-bit stride multiply wraps to 0x20503600",
        "index": 0x01000000,
        "accumulator": 0xFFFFFFFF,
        "table_mode": "same",
        "tables": [[0x1111, 0x2222, 0x3333, 0x4444, 0x5555]],
        "entries": {0x01000000: [0x6666, 0x7777, 0x8888, 0x9999, 0xAAAA]},
    })

    cases.append({
        "name": "same table buffer returned by all ten calls (index 1)",
        "index": 1,
        "accumulator": 0x80000000,
        "table_mode": "same",
        "tables": [[0x0102, 0x0304, 0x0506, 0x0708, 0x090A]],
        "entries": {1: [0x1111, 0x2222, 0x3333, 0x4444, 0x5555]},
    })

    cases.append({
        "name": "null getter result: both bodies fault before any store",
        "index": 0,
        "accumulator": 0xDEADBEEF,
        "tables": default_tables(0x520),
        "entries": {0: [1, 2, 3, 4, 5]},
        "null_at": 0,
    })

    return cases


def comparable(result):
    """Observable result fields used by the semantic comparison.

    r0 and other call-clobbered registers are deliberately excluded.
    """
    return (
        result["call_log"],
        result["context"],
        result["table"],
        result["wrap"],
        result["pc"],
        result["sp"],
        result["callee_saved"],
        result["callee_saved_vfp"],
    )


def compare_full(name, res_orig, res_cand):
    assert res_orig["call_log"] == res_cand["call_log"], (
        f"Call log mismatch on {name}:\n"
        f"  Orig: {res_orig['call_log']}\n  Cand: {res_cand['call_log']}"
    )
    assert res_orig["context"] == res_cand["context"], (
        f"Context memory mismatch on {name}"
    )
    assert res_orig["table"] == res_cand["table"], (
        f"Table memory mismatch on {name}"
    )
    assert res_orig["wrap"] == res_cand["wrap"], (
        f"Wrap-region memory mismatch on {name}"
    )
    assert res_orig["pc"] == res_cand["pc"] == TRAP_ADDR, (
        f"PC mismatch on {name}: {res_orig['pc']:#x} vs {res_cand['pc']:#x}"
    )
    assert res_orig["sp"] == res_cand["sp"], (
        f"SP mismatch on {name}: {res_orig['sp']:#x} vs {res_cand['sp']:#x}"
    )
    assert res_orig["sp"] == STACK_ADDR + STACK_SIZE - 0x100, (
        f"stack not restored on {name}"
    )
    assert res_orig["callee_saved"] == res_cand["callee_saved"], (
        f"callee-saved register mismatch on {name}"
    )
    assert res_orig["callee_saved_vfp"] == res_cand["callee_saved_vfp"], (
        f"callee-saved VFP register mismatch on {name}"
    )


def main():
    print("Testing script_vm_func_00191b64 (0x00191b64)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    runner = Runner()
    cases = make_cases()

    passed = 0
    for case in cases:
        res_orig = runner.run(orig_code, case)
        res_cand = runner.run(cand_code, case)
        name = case["name"]

        if case.get("null_at") is not None:
            assert res_orig["fault"] is not None, f"original did not fault on {name}"
            assert res_cand["fault"] is not None, f"candidate did not fault on {name}"
            assert res_orig["fault"] == res_cand["fault"], (
                f"fault kind mismatch on {name}: "
                f"{res_orig['fault']} vs {res_cand['fault']}"
            )
            # Both bodies must fault on the first null dereference, before any
            # table or accumulator store; fault PC/SP are prologue-dependent
            # and are deliberately not compared for the fault case.
            assert res_orig["call_log"] == res_cand["call_log"], (
                f"fault call log mismatch on {name}"
            )
            assert res_orig["context"] == res_cand["context"], (
                f"fault context memory mismatch on {name}"
            )
            assert res_orig["table"] == res_cand["table"], (
                f"fault table memory mismatch on {name}"
            )
            assert res_orig["wrap"] == res_cand["wrap"], (
                f"fault wrap-region memory mismatch on {name}"
            )
            assert struct.unpack(
                "<I", res_cand["context"][CTX_ACC:CTX_ACC + 4]
            )[0] == case["accumulator"], (
                f"accumulator changed before the fault on {name}"
            )
            passed += 1
            print(f"  [PASS] {name} (fault parity, errno {res_orig['fault']})")
            continue

        compare_full(name, res_orig, res_cand)
        passed += 1
        print(f"  [PASS] {name}")

    print("\nNegative controls:")
    mutants = [
        (
            "unsigned table field in the difference",
            [(
                "        const s32 tableValue =\n"
                "            *reinterpret_cast<const s16*>(tableForRead + tableOffset);",
                "        const s32 tableValue =\n"
                "            *reinterpret_cast<const u16*>(tableForRead + tableOffset);",
            )],
        ),
        (
            "entry field base shifted by two bytes",
            [("constexpr u32 kEntryFieldBase   = 0x6a;",
              "constexpr u32 kEntryFieldBase   = 0x6c;")],
        ),
        (
            "difference sign flipped",
            [("        sum += tableValue - entryValue;",
              "        sum += entryValue - tableValue;")],
        ),
        (
            "copy reads the table instead of the entry",
            [("            *reinterpret_cast<const u16*>(selectedEntry(base) + entryOffset);",
              "            *reinterpret_cast<const u16*>(tableForWrite + tableOffset);")],
        ),
        (
            "entry stride off by one element unit",
            [("constexpr u32 kEntryStride      = 0x620;",
              "constexpr u32 kEntryStride      = 0x610;")],
        ),
        (
            "16-bit index read instead of the 32-bit field",
            [("    const u32 index = *reinterpret_cast<const u32*>(context + kSelectedIndex);",
              "    const u32 index = *reinterpret_cast<const u16*>(context + kSelectedIndex);")],
        ),
        (
            "accumulator offset shifted by one word",
            [("constexpr u32 kAccumulator      = 0xcfcc;",
              "constexpr u32 kAccumulator      = 0xcfc8;")],
        ),
        (
            "selected index read once, not after every call",
            [
                (
                    "inline u8* selectedEntry(u8* context) {\n"
                    "    const u32 index = *reinterpret_cast<const u32*>(context + kSelectedIndex);\n"
                    "    return context + kEntryArrayOffset + index * kEntryStride;\n"
                    "}",
                    "inline u8* selectedEntry(u8* context, u32 index) {\n"
                    "    return context + kEntryArrayOffset + index * kEntryStride;\n"
                    "}",
                ),
                (
                    "    u8* const base = static_cast<u8*>(context);\n"
                    "    s32 sum = 0;",
                    "    u8* const base = static_cast<u8*>(context);\n"
                    "    const u32 cachedIndex =\n"
                    "        *reinterpret_cast<const u32*>(base + kSelectedIndex);\n"
                    "    s32 sum = 0;",
                ),
                ("selectedEntry(base)", "selectedEntry(base, cachedIndex)"),
            ],
        ),
    ]
    for name, replacements in mutants:
        mutant_code = compile_mutant(name.replace(" ", "_"), replacements)
        detected = False
        for case in cases:
            if case.get("null_at") is not None:
                continue
            res_orig = runner.run(orig_code, case)
            res_mut = runner.run(mutant_code, case)
            if comparable(res_orig) != comparable(res_mut):
                detected = True
                break
        assert detected, f"negative control not detected: {name}"
        print(f"  [PASS] mutant detected: {name}")

    print(f"\nAll {passed}/{len(cases)} differential test cases PASSED!")


if __name__ == "__main__":
    main()
