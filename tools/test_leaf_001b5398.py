#!/usr/bin/env python3
"""Differential test for script_vm_func_001b5398 (0x001b5398) using Unicorn ARM.

Compiles src/engine/leaf_batch34_c.cpp, extracts the reconstructed
script_vm_func_001b5398 body, resolves its direct calls to deterministic stubs,
and runs the pinned original (extracted/exefs/code.bin) against the candidate in
separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and the callee-saved r4-r11;
  * the ordered call log with every register argument and the full text written
    through the 0x002BF86C copy stub;
  * the manager block, the global manager pointer cell, every fixture node block
    (the routine writes status/state/counters and unlinks removed nodes) and the
    stub string page;
  * any CPU write outside the private stack, manager, node, global-cell and
    string regions.

Coverage: null manager, null head, single and chained removals (head, middle
with previous and next, tail), removal followed by processing, all four
non-negative status forms including 0x0000 and 0x7FFF and 16-bit wrap, signed
state 0/1/other, both readiness gates, kinds 0/1/2/other, both text sources,
the (flags +0x10 | flags +0x14) zero test, signed +0x29C boundaries, the
16-bit truncation of +0x08, sign-extended +0x298 and +0xDE ids.  Negative
controls mutate the frame size, the text-select bit, the manager pointer
address and the status preload; each mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_001b5398"

FUNC_ADDR = 0x001B5398
FUNC_SIZE = 600

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers the function and every stub below 0x2C4360
GLOBAL_ADDR = 0x00430000  # holds the 0x00435D78 manager pointer cell
GLOBAL_SIZE = 0x00020000
MANAGER_ADDR = 0x00710000
MANAGER_SIZE = 0x00001000
NODE_ADDR = 0x00720000
NODE_SIZE = 0x00030000
STR_ADDR = 0x00760000
STR_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

GLOBAL_CELL = 0x00435D78
LABEL_ADDR = STR_ADDR + 0x100
TEXT_BUCKET_BASE = STR_ADDR + 0x1000
TEXT_BUCKET_STRIDE = 0x40
TEXT_BUCKET_MASK = 0x1FF

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100
NODE_STRIDE = 0x400
NODE_BLOCK = 0x400

# Original direct-call targets.  Stubs are placed at the same addresses so that
# both the original bytes and the relocated candidate resolve to them.
STUB_2C0AC8 = 0x002C0AC8
STUB_2B6E44 = 0x002B6E44
STUB_295E74 = 0x00295E74
STUB_2C4B30 = 0x002C4B30
STUB_2BD3EC = 0x002BD3EC
STUB_2BD25C = 0x002BD25C
STUB_2BF86C = 0x002BF86C
STUB_295904 = 0x00295904
STUB_27EA24 = 0x0027EA24
STUB_27E9E4 = 0x0027E9E4
STUB_212024 = 0x00212024
STUB_2C4360 = 0x002C4360

STUB_NAMES = {
    STUB_2C0AC8: "ui_func_002c0ac8",
    STUB_2B6E44: "script_vm_func_002b6e44",
    STUB_295E74: "script_vm_func_00295e74",
    STUB_2C4B30: "engine_func_002c4b30",
    STUB_2BD3EC: "script_vm_func_002bd3ec",
    STUB_2BD25C: "script_vm_func_002bd25c",
    STUB_2BF86C: "engine_func_002bf86c",
    STUB_295904: "script_vm_func_00295904",
    STUB_27EA24: "script_vm_func_0027ea24",
    STUB_27E9E4: "script_vm_func_0027e9e4",
    STUB_212024: "camp_func_00212024",
    STUB_2C4360: "engine_func_002c4360",
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


# --------------------------------------------------------------------- helpers
def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    functions = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in functions.items():
        if "001b5398" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"script_vm_func_001b5398 not found in {obj_file}: {sorted(functions)}"
        )

    code_raw, relocations = candidate
    code = bytearray(code_raw)
    for rel in relocations:
        if rel.relocation_type != 28:  # R_ARM_CALL
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = None
        for address in STUB_NAMES:
            if f"{address:08x}" in rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        if (target - pc) & 3:
            raise RuntimeError(f"unaligned call target 0x{target:08x}")
        original = struct.unpack_from("<I", code, rel.offset)[0]
        cond = original & 0xFF000000
        struct.pack_into(
            "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
        )
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch34_c.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_source = OUT_DIR / f"mutant_{name}.cpp"
    mutant_source.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    result = compile_tu_armv6k(mutant_source, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def read_c_string(uc, address: int, limit: int = 128) -> bytes:
    out = bytearray()
    for index in range(limit):
        byte = uc.mem_read(address + index, 1)[0]
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


def s16_bytes(value: int) -> bytes:
    return struct.pack("<H", value & 0xFFFF)


def u32_bytes(value: int) -> bytes:
    return struct.pack("<I", value & 0xFFFFFFFF)


# --------------------------------------------------------------------- fixtures
DEFAULT_NODE = {
    "kind": 0,
    "state": 0,
    "id": 0x1234,
    "low": 0x00005678,
    "word": 0x9ABCDEF0,
    "flags10": 0,
    "flags14": 0,
    "index": 0x0055,
    "byte": 0x42,
    "slot": 0,
    "counter": 0x1234,
    "status": 0,
}


def node(**overrides) -> dict:
    value = dict(DEFAULT_NODE)
    value.update(overrides)
    return value


def make_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "manager_null": False,
        "nodes": [],
        "order": None,
        "count": None,
        "ready": 0,
        "selection": 0,
        "scene_ret": 0,
        "label": "LABEL",
        "arg0": 0xDEADBEEF,
    }
    case.update(overrides)
    return case


def build_node_block(spec: dict) -> bytes:
    block = bytearray(b"\xA5" * NODE_BLOCK)
    block[0:2] = s16_bytes(spec["kind"])
    block[2:4] = s16_bytes(spec["state"])
    block[4:6] = struct.pack("<H", spec["id"] & 0xFFFF)
    block[8:12] = u32_bytes(spec["low"])
    block[0x0C:0x10] = u32_bytes(spec["word"])
    block[0x10:0x14] = u32_bytes(spec["flags10"])
    block[0x14:0x18] = u32_bytes(spec["flags14"])
    block[0xDE:0xE0] = struct.pack("<H", spec["index"] & 0xFFFF)
    block[0x298] = spec["byte"] & 0xFF
    block[0x29C:0x2A0] = u32_bytes(spec["slot"])
    block[0x2A0:0x2A2] = struct.pack("<H", spec["counter"] & 0xFFFF)
    block[0x2A2:0x2A4] = s16_bytes(spec["status"])
    # next/prev are filled by build_fixture once the order is known.
    return bytes(block)


def build_fixture(case: dict) -> dict:
    specs = case["nodes"]
    addrs = [NODE_ADDR + index * NODE_STRIDE for index in range(len(specs))]
    order = case["order"]
    if order is None:
        order = list(range(len(specs)))
    if sorted(order) != list(range(len(specs))):
        raise RuntimeError(f"invalid order {order} for {len(specs)} nodes")

    blocks = []
    for index, spec in enumerate(specs):
        block = bytearray(build_node_block(spec))
        position = order.index(index)
        previous = addrs[order[position - 1]] if position > 0 else 0
        following = addrs[order[position + 1]] if position + 1 < len(order) else 0
        block[0x2A4:0x2A8] = u32_bytes(following)
        block[0x2A8:0x2AC] = u32_bytes(previous)
        blocks.append((addrs[index], bytes(block)))

    head = addrs[order[0]] if order else 0
    tail = addrs[order[-1]] if order else 0
    count = case["count"] if case["count"] is not None else len(order)
    manager = struct.pack("<III", head, tail, count & 0xFFFFFFFF)
    global_value = 0 if case["manager_null"] else MANAGER_ADDR

    return {
        "manager": manager,
        "global": global_value,
        "label": case["label"].encode("ascii"),
        "blocks": blocks,
        "addrs": addrs,
    }


# ------------------------------------------------------------------------ runner
class BtlHelpRunner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(GLOBAL_ADDR, GLOBAL_SIZE)
        self.uc.mem_map(MANAGER_ADDR, MANAGER_SIZE)
        self.uc.mem_map(NODE_ADDR, NODE_SIZE)
        self.uc.mem_map(STR_ADDR, STR_SIZE)
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
        self.stack_buffers: set = set()
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    @staticmethod
    def _norm(value: int):
        if STACK_ADDR <= value < STACK_ADDR + STACK_SIZE:
            return "<stack>"
        return value

    def _note_buffer(self, value: int) -> None:
        if STACK_ADDR <= value < STACK_ADDR + STACK_SIZE:
            self.stack_buffers.add(value)

    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], tuple(args)))

    def _text_for(self, ident: int) -> int:
        address = (
            TEXT_BUCKET_BASE
            + (ident & TEXT_BUCKET_MASK) * TEXT_BUCKET_STRIDE
        )
        text = f"T{ident & 0xFFFF}".encode("ascii")
        self.uc.mem_write(address, text + b"\x00")
        return address

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_2C0AC8:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["scene_ret"] & 0xFFFFFFFF)
        elif address == STUB_2B6E44:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, 1 if self.case["ready"] else 0)
        elif address == STUB_295E74:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, 1 if self.case["selection"] else 0)
        elif address == STUB_2C4B30:
            self._log(address, self._norm(r0), r1)
            self._note_buffer(r0)
            uc.mem_write(r0, b"\x00" * min(r1, 0x400))
        elif address == STUB_2BD3EC:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, LABEL_ADDR)
        elif address == STUB_2BD25C:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self._text_for(r0))
        elif address == STUB_2BF86C:
            source = read_c_string(uc, r1)
            self._log(address, self._norm(r0), source)
            self._note_buffer(r0)
            uc.mem_write(r0, source + b"\x00")
        elif address == STUB_295904:
            text = read_c_string(uc, r1)
            self._log(address, r0, text, self._norm(r1))
            self._note_buffer(r1)
        elif address == STUB_27EA24:
            self._log(address, r0, r1)
        elif address == STUB_27E9E4:
            self._log(address, r0, r1)
        elif address == STUB_212024:
            self._log(address, r0)
        elif address == STUB_2C4360:
            self._log(address, r0)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def _allowed_write(self, address: int, size: int, blocks) -> bool:
        if STACK_ADDR <= address < STACK_ADDR + STACK_SIZE:
            return True
        if STR_ADDR <= address < STR_ADDR + STR_SIZE:
            return True
        if GLOBAL_CELL <= address < GLOBAL_CELL + 4:
            return True
        if MANAGER_ADDR <= address < MANAGER_ADDR + 0x40:
            return True
        for block_address in blocks:
            if block_address <= address < block_address + NODE_BLOCK:
                return True
        return False

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.stack_buffers = set()
        self.case = case

        fixture = build_fixture(case)

        self.uc.mem_write(GLOBAL_ADDR, b"\x00" * GLOBAL_SIZE)
        self.uc.mem_write(MANAGER_ADDR, b"\x00" * MANAGER_SIZE)
        self.uc.mem_write(NODE_ADDR, b"\x00" * NODE_SIZE)
        self.uc.mem_write(STR_ADDR, b"\x00" * STR_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.uc.mem_write(FUNC_ADDR, b"\x00" * max(FUNC_SIZE, len(code)))
        self.uc.mem_write(FUNC_ADDR, code)

        self.uc.mem_write(GLOBAL_CELL, u32_bytes(fixture["global"]))
        self.uc.mem_write(MANAGER_ADDR, fixture["manager"])
        self.uc.mem_write(LABEL_ADDR, fixture["label"] + b"\x00")
        for block_address, block in fixture["blocks"]:
            self.uc.mem_write(block_address, block)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, case["arg0"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        if len(self.stack_buffers) > 1:
            raise RuntimeError(
                "the routine used more than one stack buffer: "
                f"{sorted(hex(value) for value in self.stack_buffers)}"
            )

        unexpected_writes = []
        for address, size, _value in self.writes:
            if not self._allowed_write(address, size, fixture["addrs"]):
                unexpected_writes.append((address, size))

        fixtures = {
            "global": bytes(self.uc.mem_read(GLOBAL_CELL, 4)),
            "manager": bytes(self.uc.mem_read(MANAGER_ADDR, 0x40)),
            "label": bytes(self.uc.mem_read(LABEL_ADDR, 0x40)),
            "text": bytes(
                self.uc.mem_read(TEXT_BUCKET_BASE, TEXT_BUCKET_STRIDE * 0x200)
            ),
        }
        for index, block_address in enumerate(fixture["addrs"]):
            fixtures[f"node{index}"] = bytes(
                self.uc.mem_read(block_address, NODE_BLOCK)
            )

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "fixtures": fixtures,
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
    for key, value in orig["fixtures"].items():
        if key not in cand["fixtures"] or value != cand["fixtures"][key]:
            problems.append(f"fixture {key} differs")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


# ------------------------------------------------------------------------- cases
def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- manager / list shape
    cases.append(make_case("null manager pointer", manager_null=True))
    cases.append(make_case("null head", nodes=[], order=[]))

    # --- removals (signed status < 0)
    cases.append(make_case("single removed node clears head and tail",
                           nodes=[node(status=-1)], order=[0]))
    cases.append(make_case("removal chain to empty list",
                           nodes=[node(status=-1), node(status=-2),
                                  node(status=-32768)],
                           order=[0, 1, 2]))
    cases.append(make_case("remove head then process state 2",
                           nodes=[node(status=-1),
                                  node(state=2, status=5, counter=9)],
                           order=[0, 1]))
    cases.append(make_case("remove middle with previous and next",
                           nodes=[node(status=-1), node(status=-1),
                                  node(state=2, status=5, counter=9)],
                           order=[0, 1, 2]))
    cases.append(make_case("remove non-head with previous only",
                           nodes=[node(status=-1), node(status=-1)],
                           order=[0, 1]))

    # --- state 0 readiness gates
    cases.append(make_case("state 0 ready gate preloads status",
                           nodes=[node(state=0, status=3, counter=0xFFFF)],
                           order=[0], ready=1))
    cases.append(make_case("state 0 selection gate preloads status",
                           nodes=[node(state=0, status=3, counter=0)],
                           order=[0], selection=1))
    cases.append(make_case("state 0 both gates zero processes kind 0",
                           nodes=[node(state=0, status=0, counter=0xFFFF,
                                       kind=0, low=0xFFFF1234, word=0xFFFFFFFF,
                                       byte=0x80, slot=-1)],
                           order=[0]))

    # --- kind 1 text selection
    cases.append(make_case("kind 1 zero flags uses script tail only",
                           nodes=[node(state=0, kind=1, flags10=0, flags14=0,
                                       slot=0, counter=1)],
                           order=[0]))
    cases.append(make_case("kind 1 negative slot uses script tail only",
                           nodes=[node(state=0, kind=1, flags10=2, flags14=0,
                                       slot=-1, counter=1)],
                           order=[0]))
    cases.append(make_case("kind 1 label path slot 0",
                           nodes=[node(state=0, kind=1, flags10=2, flags14=0,
                                       slot=0, index=0, byte=0x7F)],
                           order=[0], label="ACTIVE-LABEL"))
    cases.append(make_case("kind 1 id path slot 5",
                           nodes=[node(state=0, kind=1, flags10=1,
                                       flags14=0x80000000, slot=5, index=0)],
                           order=[0]))
    cases.append(make_case("kind 1 id path maximum slot and index",
                           nodes=[node(state=0, kind=1, flags10=0, flags14=1,
                                       slot=0x7FFFFFFF, index=0xFFFF,
                                       byte=0x80)],
                           order=[0]))
    cases.append(make_case("kind 1 minimum signed slot skipped",
                           nodes=[node(state=0, kind=1, flags10=2,
                                       flags14=0x80000000, slot=-0x80000000)],
                           order=[0]))

    # --- kind 2
    cases.append(make_case("kind 2 zero flags uses camp tail only",
                           nodes=[node(state=0, kind=2, flags10=0, flags14=0,
                                       id=0, counter=2)],
                           order=[0]))
    cases.append(make_case("kind 2 negative slot uses camp tail only",
                           nodes=[node(state=0, kind=2, flags10=2, flags14=0,
                                       slot=-1, id=0xFFFF)],
                           order=[0]))
    cases.append(make_case("kind 2 label path slot 0",
                           nodes=[node(state=0, kind=2, flags10=2, flags14=0,
                                       slot=0, id=1)],
                           order=[0], label="LABEL-2"))
    cases.append(make_case("kind 2 id path slot 1",
                           nodes=[node(state=0, kind=2, flags10=0, flags14=1,
                                       slot=1, id=0xABCD, index=0x1234)],
                           order=[0]))
    cases.append(make_case("kind 2 maximum slot",
                           nodes=[node(state=0, kind=2, flags10=0,
                                       flags14=0x80000000, slot=0x7FFFFFFF,
                                       index=0x8000, id=0x8000)],
                           order=[0]))

    # --- other kinds / states
    cases.append(make_case("other kind skips tail calls",
                           nodes=[node(state=0, kind=3, flags10=2, slot=0)],
                           order=[0]))
    cases.append(make_case("negative kind skips tail calls",
                           nodes=[node(state=0, kind=-1, flags10=2, slot=0)],
                           order=[0]))
    cases.append(make_case("state 1 ready preloads status",
                           nodes=[node(state=1, status=0, counter=0)],
                           order=[0], ready=1))
    cases.append(make_case("state 1 not ready decrements status",
                           nodes=[node(state=1, status=3, counter=0)],
                           order=[0], ready=0))
    cases.append(make_case("state 1 not ready wraps status",
                           nodes=[node(state=1, status=0, counter=0xFFFE)],
                           order=[0]))
    cases.append(make_case("state 1 ready wraps counter",
                           nodes=[node(state=1, status=0x7FFF,
                                       counter=0xFFFF)],
                           order=[0], ready=1))
    cases.append(make_case("state 2 does no work",
                           nodes=[node(state=2, status=1, counter=0)],
                           order=[0]))
    cases.append(make_case("state -1 is an other state",
                           nodes=[node(state=-1, status=0, counter=1)],
                           order=[0]))
    cases.append(make_case("state 0x7FFF is an other state",
                           nodes=[node(state=0x7FFF, status=5, counter=1)],
                           order=[0]))
    cases.append(make_case("state -32768 is an other state",
                           nodes=[node(state=-32768, status=5, counter=1)],
                           order=[0]))

    # --- 16-bit boundaries and forwarding widths
    cases.append(make_case("status 0x7FFF decrements to 0x7FFE",
                           nodes=[node(state=2, status=0x7FFF,
                                       counter=0xFFFF)],
                           order=[0]))
    cases.append(make_case("status zero wraps to 0xFFFF",
                           nodes=[node(state=2, status=0, counter=0)],
                           order=[0]))
    cases.append(make_case("low word truncated to 16 bits",
                           nodes=[node(state=0, kind=0, low=0xFFFFABCD,
                                       word=0x00000000, counter=0x0001)],
                           order=[0]))
    cases.append(make_case("sign extended byte and 16-bit id",
                           nodes=[node(state=0, kind=0, byte=0x7F, id=0xFFFF,
                                       low=0, word=0xFFFFFFFF)],
                           order=[0]))
    cases.append(make_case("nonzero scene lookup result is ignored",
                           nodes=[node(state=0, kind=0)], order=[0],
                           ready=1, scene_ret=0x12345678,
                           arg0=0xFFFFFFFF))
    cases.append(make_case("zero handle and zero frame",
                           nodes=[node(state=0, kind=0, byte=-128)],
                           order=[0], arg0=0))

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = BtlHelpRunner().run(orig_code, case)
        cand = BtlHelpRunner().run(cand_code, case)
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
    print("Testing script_vm_func_001b5398 (0x001b5398)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B.")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("frame_zero_size", "constexpr u32 kFrameZeroSize = 0x60;",
         "constexpr u32 kFrameZeroSize = 0x5F;"),
        ("text_path_bit", "constexpr u32 kTextPathBit = 2;",
         "constexpr u32 kTextPathBit = 4;"),
        ("manager_pointer_address",
         "constexpr u32 kManagerPointerAddress = 0x00435D78;",
         "constexpr u32 kManagerPointerAddress = 0x00435D7C;"),
        ("status_preload", "constexpr s16 kStatusPreload = 1;",
         "constexpr s16 kStatusPreload = 2;"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = BtlHelpRunner().run(orig_code, case)
            bad = BtlHelpRunner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
