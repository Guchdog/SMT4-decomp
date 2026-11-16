#!/usr/bin/env python3
"""Differential test for script_vm_func_003359f4 (0x003359f4) using Unicorn ARM.

The routine is a game-over state-machine step.  It compares a selector word at
object+0x08 against a static table (0x00439a70), runs up to four selector-specific
helpers, and, when the selector is above the table limit, loads the
gameover/level-event file pair, increments a saturating byte counter at
+0x24B29 of the work block returned by 0x002c0b94, and tail-calls 0x0023f2f0.

Every direct call is replaced with a deterministic stub that logs its arguments
(including stack arguments).  Each case runs the pinned original and the
compiled candidate with identical fixtures and compares:
  - the ordered call log,
  - return value, continuation PC and SP,
  - callee-saved integer and VFP registers,
  - the object block, the counter window, the selector table and the hook
    global.

The fixtures also cover helper side effects (rewriting the selector or the flag
word) so that the original's reloads are observable.
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
FUNC_ADDR = 0x003359F4
FUNC_SIZE = 400
TU_PATH = ROOT / "src/engine/leaf_batch44_b.cpp"
OUT_DIR = ROOT / "build/test_leaf_003359f4"

# ---------------------------------------------------------------------------
# Emulated address space
# ---------------------------------------------------------------------------
IMAGE_ADDR = 0x00100000
IMAGE_MAP_SIZE = 0x00500000          # 0x00100000..0x00600000
LOW_ADDR = 0x00000000
LOW_SIZE = 0x00030000                # null work pointer -> counter at 0x24B29
RODATA_ADDR = 0x00600000
RODATA_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

SELF_ADDR = 0x00450000
COUNTER_BASE = 0x00440000
COUNTER_OFFSET = 0x24B29
TABLE_ADDR = 0x00439A70
HOOK_ADDR = 0x00439CA8

SELF_WATCH = 0x40
COUNTER_WATCH = 0x100             # centered on the counter byte
TABLE_WATCH = 0x24

# Direct-call stubs (original branch targets).
STUB_282A90 = 0x00282A90
STUB_267F68 = 0x00267F68
STUB_23F3D8 = 0x0023F3D8
STUB_29C660 = 0x0029C660
STUB_297704 = 0x00297704
STUB_2C0B94 = 0x002C0B94
STUB_23F2F0 = 0x0023F2F0

STUB_BY_SYMBOL = {
    "battle_func_00282a90": STUB_282A90,
    "battle_func_00267f68": STUB_267F68,
    "battle_func_0023f3d8": STUB_23F3D8,
    "script_vm_func_0029c660": STUB_29C660,
    "script_vm_func_00297704": STUB_297704,
    "ui_func_002c0b94": STUB_2C0B94,
    "battle_func_0023f2f0": STUB_23F2F0,
}
ABS32_TARGETS = {
    "g_BtlGameOverSelectors": TABLE_ADDR,
    "g_BtlGameOverHookTarget": HOOK_ADDR,
}

BX_LR = 0xE12FFF1E

# Selector table contents read from the pinned image (0x00439a70).
EXPECTED_TABLE = (20, 110, 1, 86, 18, 0xFFFFFFFF, 22, 5, 120)
TABLE_SELECTOR_00 = 20
TABLE_SELECTOR_04 = 110
TABLE_SLOT_VALUE_08 = 1
TABLE_SELECTOR_0C = 86
TABLE_SLOT_VALUE_10 = 18
TABLE_SELECTOR_14 = 0xFFFFFFFF
TABLE_MESSAGE_ID_18 = 22
TABLE_MESSAGE_ARG_1C = 5
TABLE_SELECTOR_LIMIT_20 = 120

GAMEOVER_BF = b"battle/gameover/gameover.bf"
LEVEL_EVENT_BF = b"battle/gameover/level_event.bf"
GAMEOVER_MBM = b"battle/gameover/gameover.mbm"
LEVEL_EVENT_MBM = b"battle/gameover/level_event.mbm"


# ---------------------------------------------------------------------------
# Candidate preparation
# ---------------------------------------------------------------------------
def get_orig_bytes():
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def image_bytes():
    return ORIG_BIN.read_bytes()


def table_bytes():
    image = image_bytes()
    offset = TABLE_ADDR - IMAGE_ADDR
    return image[offset:offset + TABLE_WATCH]


def sign_extend_24(value):
    return value - 0x1000000 if value & 0x800000 else value


def read_object_section(obj_file, wanted):
    """Return the bytes of the first section whose name starts with `wanted`."""
    data = Path(obj_file).read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize = struct.unpack_from("<H", data, 46)[0]
    e_shnum = struct.unpack_from("<H", data, 48)[0]
    e_shstrndx = struct.unpack_from("<H", data, 50)[0]
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    shstrtab = sections[e_shstrndx]
    shstr = data[shstrtab[4]:shstrtab[4] + shstrtab[5]]
    for section in sections:
        name = shstr[section[0]:].split(b"\x00")[0].decode("ascii", "replace")
        if name.startswith(wanted):
            return data[section[4]:section[4] + section[5]]
    raise RuntimeError(f"section {wanted!r} not found in {obj_file}")


def compile_variant(src_file, obj_file):
    result = compile_tu_armv6k(Path(src_file), Path(obj_file), ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed for {src_file}: {result.stderr}")

    funcs = extract_elf_functions_detailed(Path(obj_file))
    entry = funcs.get("script_vm_func_003359f4")
    if entry is None:
        raise RuntimeError(
            "script_vm_func_003359f4 not found in object: "
            + ", ".join(sorted(funcs))
        )

    raw, relocs = entry
    code = bytearray(raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            target = STUB_BY_SYMBOL.get(rel.symbol_name)
            if target is None:
                raise RuntimeError(f"unexpected call relocation: {rel}")
            inst = struct.unpack_from("<I", code, rel.offset)[0]
            addend = sign_extend_24(inst & 0x00FFFFFF) << 2
            place = FUNC_ADDR + rel.offset
            disp = (target + addend - place) >> 2
            struct.pack_into(
                "<I", code, rel.offset, (inst & 0xFF000000) | (disp & 0x00FFFFFF)
            )
        elif rel.relocation_type == 2:  # R_ARM_ABS32
            literal = struct.unpack_from("<I", code, rel.offset)[0]
            if rel.symbol_name in ABS32_TARGETS:
                if literal != 0:
                    raise RuntimeError(f"unexpected addend in {rel}")
                value = ABS32_TARGETS[rel.symbol_name]
            elif rel.symbol_name == "":
                # Section-relative .rodata literal; the addend is the section
                # offset of the string.
                if literal >= RODATA_SIZE:
                    raise RuntimeError(f"rodata addend out of range: {rel}")
                value = RODATA_ADDR + literal
            else:
                raise RuntimeError(f"unexpected abs32 relocation: {rel}")
            struct.pack_into("<I", code, rel.offset, value)
        else:
            raise RuntimeError(f"unsupported relocation: {rel}")

    return bytes(code), read_object_section(obj_file, ".rodata")


def compile_candidate():
    return compile_variant(TU_PATH, OUT_DIR / "leaf_batch44_b.o")


def compile_mutant(name, old, new):
    text = TU_PATH.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    return compile_variant(mutant_src, OUT_DIR / f"mutant_{name}.o")


# ---------------------------------------------------------------------------
# Machine
# ---------------------------------------------------------------------------
class Machine:
    def __init__(self):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(IMAGE_ADDR, IMAGE_MAP_SIZE)
        self.uc.mem_map(LOW_ADDR, LOW_SIZE)
        self.uc.mem_map(RODATA_ADDR, RODATA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        # Original image: text, rodata and data (including the selector table).
        self.original_image = image_bytes()
        self.uc.mem_write(IMAGE_ADDR, self.original_image)
        self.table = table_bytes()
        self.orig_code = get_orig_bytes()

        self.call_log = []
        self.case = None
        self._install_stubs()

    def _install_stubs(self):
        bx_lr = struct.pack("<I", BX_LR)
        stubs = [
            (STUB_282A90, self._on_282a90),
            (STUB_267F68, self._on_267f68),
            (STUB_23F3D8, self._on_23f3d8),
            (STUB_29C660, self._on_29c660),
            (STUB_297704, self._on_297704),
            (STUB_2C0B94, self._on_2c0b94),
            (STUB_23F2F0, self._on_23f2f0),
        ]
        for address, hook in stubs:
            self.uc.mem_write(address, bx_lr)
            self.uc.hook_add(unicorn.UC_HOOK_CODE, hook, begin=address, end=address)

    # -- stub bodies ------------------------------------------------------
    def _read_stack(self, count):
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        raw = self.uc.mem_read(sp, count * 4)
        return struct.unpack("<%dI" % count, raw)

    def _read_cstring(self, address):
        try:
            raw = self.uc.mem_read(address, 128)
        except Exception:
            return b""
        end = raw.find(b"\x00")
        return bytes(raw[:end] if end != -1 else raw)

    def _on_282a90(self, uc, address, size, user_data):
        args = [uc.reg_read(arm.UC_ARM_REG_R0 + i) for i in range(4)]
        stack = list(self._read_stack(4))
        self.call_log.append(("battle_func_00282a90", *args, *stack))
        mutate = self.case.get("mutate_selector_after_282a90")
        if mutate is not None:
            self._write_u32(SELF_ADDR + 0x08, mutate)

    def _on_267f68(self, uc, address, size, user_data):
        self.call_log.append(
            ("battle_func_00267f68", uc.reg_read(arm.UC_ARM_REG_R0))
        )

    def _on_23f3d8(self, uc, address, size, user_data):
        args = [uc.reg_read(arm.UC_ARM_REG_R0 + i) for i in range(4)]
        stack = list(self._read_stack(5))
        self.call_log.append(("battle_func_0023f3d8", *args, *stack))

    def _on_29c660(self, uc, address, size, user_data):
        args = [uc.reg_read(arm.UC_ARM_REG_R0 + i) for i in range(3)]
        self.call_log.append(("script_vm_func_0029c660", *args))

    def _on_297704(self, uc, address, size, user_data):
        name = self._read_cstring(uc.reg_read(arm.UC_ARM_REG_R0))
        dest = uc.reg_read(arm.UC_ARM_REG_R1)
        flags = uc.reg_read(arm.UC_ARM_REG_R2)
        self.call_log.append(("script_vm_func_00297704", name, dest, flags))
        if dest == SELF_ADDR + 0x0C:
            new_flags = self.case.get("flags_after_first_load")
            if new_flags is not None:
                self._write_u32(SELF_ADDR + 0x04, new_flags)

    def _on_2c0b94(self, uc, address, size, user_data):
        self.call_log.append(("ui_func_002c0b94",))
        uc.reg_write(arm.UC_ARM_REG_R0, self.case["counter_base"])

    def _on_23f2f0(self, uc, address, size, user_data):
        work = uc.reg_read(arm.UC_ARM_REG_R0)
        state = self._read_u32(SELF_ADDR + 0x00)
        self.call_log.append(("battle_func_0023f2f0", work, state))
        uc.reg_write(arm.UC_ARM_REG_R0, self.case["tail_return"])

    # -- helpers ----------------------------------------------------------
    def _write_u32(self, address, value):
        self.uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))

    def _read_u32(self, address):
        return struct.unpack("<I", self.uc.mem_read(address, 4))[0]

    def _counter_address(self, case):
        return (case["counter_base"] + COUNTER_OFFSET) & 0xFFFFFFFF

    def _reset_fixtures(self, case):
        self.uc.mem_write(SELF_ADDR, b"\x5A" * SELF_WATCH)
        self._write_u32(SELF_ADDR + 0x00, case["initial_state"])
        self._write_u32(SELF_ADDR + 0x04, case["flags"])
        self._write_u32(SELF_ADDR + 0x08, case["selector"])
        self._write_u32(SELF_ADDR + 0x0C, 0x0C0C0C0C)
        self._write_u32(SELF_ADDR + 0x10, 0x10101010)
        self._write_u32(SELF_ADDR + 0x14, 0x14141414)

        self.uc.mem_write(TABLE_ADDR, self.table)
        self._write_u32(HOOK_ADDR, case["hook_target"])

        counter_addr = self._counter_address(case)
        window = (counter_addr - 0x80) & 0xFFFFFFFF
        self.uc.mem_write(window, b"\xCC" * COUNTER_WATCH)
        self.uc.mem_write(counter_addr, bytes([case["counter"]]))

    def run(self, candidate, case):
        """candidate = None runs the pinned original."""
        uc = self.uc
        self.case = case
        self.call_log = []

        self._reset_fixtures(case)
        if candidate is None:
            uc.mem_write(FUNC_ADDR, self.orig_code)
        else:
            code, rodata = candidate
            uc.mem_write(RODATA_ADDR, rodata)
            uc.mem_write(FUNC_ADDR, code)
        # Unicorn keeps translated blocks across mem_write; drop them.
        uc.ctl_flush_tb()

        sp = STACK_ADDR + STACK_SIZE - 0x100
        uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        uc.reg_write(arm.UC_ARM_REG_SP, sp)
        uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for index, reg in enumerate(
            [
                arm.UC_ARM_REG_R4, arm.UC_ARM_REG_R5, arm.UC_ARM_REG_R6,
                arm.UC_ARM_REG_R7, arm.UC_ARM_REG_R8, arm.UC_ARM_REG_R9,
                arm.UC_ARM_REG_R10, arm.UC_ARM_REG_R11,
            ]
        ):
            uc.reg_write(reg, 0x11110000 + index * 0x11)
        for index in range(16, 32):
            uc.reg_write(getattr(arm, f"UC_ARM_REG_S{index}"), 0x3F000000 + index)

        try:
            uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5000000)
        except unicorn.UcError as exc:
            raise RuntimeError(
                f"Crash at PC=0x{uc.reg_read(arm.UC_ARM_REG_PC):08x}: {exc}"
            ) from exc

        counter_addr = self._counter_address(case)
        window = (counter_addr - 0x80) & 0xFFFFFFFF
        return {
            "call_log": list(self.call_log),
            "r0": uc.reg_read(arm.UC_ARM_REG_R0),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "callee_saved": [
                uc.reg_read(reg)
                for reg in [
                    arm.UC_ARM_REG_R4, arm.UC_ARM_REG_R5, arm.UC_ARM_REG_R6,
                    arm.UC_ARM_REG_R7, arm.UC_ARM_REG_R8, arm.UC_ARM_REG_R9,
                    arm.UC_ARM_REG_R10, arm.UC_ARM_REG_R11,
                ]
            ],
            "callee_saved_vfp": [
                uc.reg_read(getattr(arm, f"UC_ARM_REG_S{i}"))
                for i in range(16, 32)
            ],
            "self": bytes(uc.mem_read(SELF_ADDR, SELF_WATCH)),
            "counter_window": bytes(uc.mem_read(window, COUNTER_WATCH)),
            "table": bytes(uc.mem_read(TABLE_ADDR, TABLE_WATCH)),
            "hook": self._read_u32(HOOK_ADDR),
        }


# ---------------------------------------------------------------------------
# Independent expected model
# ---------------------------------------------------------------------------
def expected_case(case):
    """Return (call_log, return_value, final_state, final_counter)."""
    selector = case["selector"]
    flags = case["flags"]
    counter = case["counter"]
    log = []

    if selector == TABLE_SELECTOR_00:
        log.append(
            ("battle_func_00282a90", 0, 0, 0, 0, 8, 0, 11, 0)
        )
        log.append(("battle_func_00267f68", case["hook_target"]))
        if case.get("mutate_selector_after_282a90") is not None:
            selector = case["mutate_selector_after_282a90"]

    if selector == TABLE_SELECTOR_14:
        log.append(
            ("battle_func_0023f3d8", 0, 0, TABLE_MESSAGE_ID_18, 0x10,
             0, TABLE_MESSAGE_ARG_1C, 0, 2, 0xFFFFFFFF)
        )

    if selector == TABLE_SELECTOR_04:
        log.append(
            ("script_vm_func_0029c660", 0, TABLE_SLOT_VALUE_08, 0xFF)
        )

    if selector == TABLE_SELECTOR_0C:
        log.append(
            ("script_vm_func_0029c660", 1, TABLE_SLOT_VALUE_10, 0xFF)
        )

    if selector <= TABLE_SELECTOR_LIMIT_20:
        return log, 0, case["initial_state"], counter

    log.append(
        ("script_vm_func_00297704",
         LEVEL_EVENT_BF if (flags & 1) else GAMEOVER_BF,
         SELF_ADDR + 0x0C, 0)
    )
    second_flags = case.get("flags_after_first_load")
    if second_flags is None:
        second_flags = flags
    log.append(
        ("script_vm_func_00297704",
         LEVEL_EVENT_MBM if (second_flags & 1) else GAMEOVER_MBM,
         SELF_ADDR + 0x14, 0)
    )
    log.append(("ui_func_002c0b94",))
    if counter < 0xFF:
        counter += 1
    log.append(("battle_func_0023f2f0", SELF_ADDR, 4))
    return log, case["tail_return"], 4, counter


def make_case(name, selector, **kwargs):
    case = {
        "name": name,
        "selector": selector & 0xFFFFFFFF,
        "flags": 0,
        "initial_state": 0x12345678,
        "hook_target": 0x00470000,
        "counter_base": COUNTER_BASE,
        "counter": 0x10,
        "tail_return": 0,
        "mutate_selector_after_282a90": None,
        "flags_after_first_load": None,
    }
    case.update(kwargs)
    return case


def build_cases():
    return [
        make_case(
            "selector 20, null hook target",
            TABLE_SELECTOR_00,
            hook_target=0,
        ),
        make_case(
            "selector 20, non-null hook target",
            TABLE_SELECTOR_00,
            hook_target=0x00470000,
            flags=0xFFFFFFFF,
        ),
        make_case(
            "selector 0xffffffff -> message + transition (flags 0)",
            TABLE_SELECTOR_14,
            flags=0,
            counter=0,
        ),
        make_case(
            "selector 0xffffffff -> gameover pair (flags 1), counter 0xfe",
            TABLE_SELECTOR_14,
            flags=1,
            counter=0xFE,
            tail_return=2,
        ),
        make_case(
            "selector 0xffffffff, saturated counter 0xff",
            TABLE_SELECTOR_14,
            flags=0xFFFFFFFF,
            counter=0xFF,
            tail_return=0xFFFFFFFF,
        ),
        make_case(
            "selector 110 -> script slot 0",
            TABLE_SELECTOR_04,
            flags=1,
        ),
        make_case(
            "selector 86 -> script slot 1",
            TABLE_SELECTOR_0C,
            flags=0,
        ),
        make_case("selector 0 -> early return", 0),
        make_case("selector 19 just below 20 -> early return", 19),
        make_case(
            "selector 120 at limit -> early return",
            TABLE_SELECTOR_LIMIT_20,
        ),
        make_case(
            "selector 121 just above limit -> transition",
            TABLE_SELECTOR_LIMIT_20 + 1,
            flags=0,
            counter=0,
        ),
        make_case(
            "selector 0x80000000 unsigned above limit -> transition",
            0x80000000,
            flags=1,
            counter=0x7F,
            tail_return=1,
        ),
        make_case(
            "selector 0x7fffffff -> transition",
            0x7FFFFFFF,
            flags=0xFFFFFFFE,
            counter=0x80,
        ),
        make_case(
            "helper rewrites selector 20 -> 110",
            TABLE_SELECTOR_00,
            mutate_selector_after_282a90=TABLE_SELECTOR_04,
        ),
        make_case(
            "helper rewrites selector 20 -> 0xffffffff (message + transition)",
            TABLE_SELECTOR_00,
            mutate_selector_after_282a90=0xFFFFFFFF,
            counter=0x01,
            tail_return=0,
        ),
        make_case(
            "flags re-read: 0 -> 1 between the two loads",
            TABLE_SELECTOR_LIMIT_20 + 1,
            flags=0,
            flags_after_first_load=1,
        ),
        make_case(
            "flags re-read: 1 -> 0 between the two loads",
            TABLE_SELECTOR_LIMIT_20 + 1,
            flags=1,
            flags_after_first_load=0,
        ),
        make_case(
            "null helper result: counter base 0",
            121,
            counter_base=0,
            counter=0x41,
        ),
        make_case(
            "null helper result, saturated counter",
            121,
            counter_base=0,
            counter=0xFF,
        ),
    ]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def check_expectations(case, result):
    log, ret, state, counter = expected_case(case)
    assert result["call_log"] == log, (
        f"expected call log mismatch on {case['name']}:\n"
        f"  Expected: {log}\n  Actual:   {result['call_log']}"
    )
    assert result["r0"] == ret, (
        f"return mismatch on {case['name']}: "
        f"0x{result['r0']:08x} != 0x{ret:08x}"
    )
    actual_state = struct.unpack_from("<I", result["self"], 0x00)[0]
    assert actual_state == state, (
        f"state mismatch on {case['name']}: "
        f"0x{actual_state:08x} != 0x{state:08x}"
    )
    counter_addr = (case["counter_base"] + COUNTER_OFFSET) & 0xFFFFFFFF
    window = (counter_addr - 0x80) & 0xFFFFFFFF
    actual_counter = result["counter_window"][counter_addr - window]
    assert actual_counter == counter, (
        f"counter mismatch on {case['name']}: "
        f"0x{actual_counter:02x} != 0x{counter:02x}"
    )


def main():
    print("Testing script_vm_func_003359f4 (0x003359f4)...")
    assert table_bytes() == struct.pack("<9I", *EXPECTED_TABLE), (
        "selector table 0x00439a70 does not match the recorded values: "
        + table_bytes().hex()
    )
    cand = compile_candidate()
    print(f"  original: {FUNC_SIZE} B, candidate: {len(cand[0])} B")

    machine = Machine()
    cases = build_cases()
    entry_sp = STACK_ADDR + STACK_SIZE - 0x100

    passed = 0
    for case in cases:
        res_orig = machine.run(None, case)
        res_cand = machine.run(cand, case)

        assert res_orig["call_log"] == res_cand["call_log"], (
            f"call log mismatch on {case['name']}:\n"
            f"  Orig: {res_orig['call_log']}\n  Cand: {res_cand['call_log']}"
        )
        assert res_orig["r0"] == res_cand["r0"], (
            f"return mismatch on {case['name']}: "
            f"0x{res_orig['r0']:08x} != 0x{res_cand['r0']:08x}"
        )
        assert res_orig["self"] == res_cand["self"], (
            f"object memory mismatch on {case['name']}"
        )
        assert res_orig["counter_window"] == res_cand["counter_window"], (
            f"counter window mismatch on {case['name']}"
        )
        assert res_orig["table"] == res_cand["table"], (
            f"selector table mismatch on {case['name']}"
        )
        assert res_orig["hook"] == res_cand["hook"], (
            f"hook global mismatch on {case['name']}"
        )
        assert res_orig["sp"] == res_cand["sp"] == entry_sp, (
            f"SP mismatch on {case['name']}: "
            f"0x{res_orig['sp']:08x} / 0x{res_cand['sp']:08x}"
        )
        assert res_orig["pc"] == res_cand["pc"] == TRAP_ADDR, (
            f"PC mismatch on {case['name']}: "
            f"0x{res_orig['pc']:08x} / 0x{res_cand['pc']:08x}"
        )
        assert res_orig["callee_saved"] == res_cand["callee_saved"], (
            f"callee-saved register mismatch on {case['name']}"
        )
        assert res_orig["callee_saved_vfp"] == res_cand["callee_saved_vfp"], (
            f"callee-saved VFP register mismatch on {case['name']}"
        )
        check_expectations(case, res_cand)

        passed += 1
        print(f"  [PASS] {case['name']}")

    print("\nNegative controls:")
    mutants = [
        (
            "threshold_lt_instead_of_le",
            "if (work->selector_08 <= g_BtlGameOverSelectors.selector_limit_20) {",
            "if (work->selector_08 < g_BtlGameOverSelectors.selector_limit_20) {",
        ),
        (
            "second_load_ignores_flags",
            "    if ((work->flags_04 & 1u) == 0) {\n"
            "        script_vm_func_00297704(\n"
            "            \"battle/gameover/gameover.mbm\"",
            "    if ((work->flags_04 & 1u) != 0) {\n"
            "        script_vm_func_00297704(\n"
            "            \"battle/gameover/gameover.mbm\"",
        ),
        (
            "counter_not_saturating",
            "if (value < 0xffu) {",
            "if (value <= 0xffu) {",
        ),
        (
            "message_id_wrong",
            "0, 0, g_BtlGameOverSelectors.message_id_18, 0x10,",
            "0, 0, g_BtlGameOverSelectors.message_id_18, 0x11,",
        ),
        (
            "script_slot_value_wrong",
            "1, g_BtlGameOverSelectors.script_slot_value_10, 0xff);",
            "1, 0xff, g_BtlGameOverSelectors.script_slot_value_10);",
        ),
    ]
    for name, old, new in mutants:
        mutant = compile_mutant(name, old, new)
        detected = False
        for case in cases:
            res_orig = machine.run(None, case)
            res_mut = machine.run(mutant, case)
            if res_orig != res_mut:
                detected = True
                break
        assert detected, f"negative control not detected: {name}"
        print(f"  [PASS] mutant detected: {name}")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
