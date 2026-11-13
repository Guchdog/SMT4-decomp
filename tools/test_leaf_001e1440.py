#!/usr/bin/env python3
"""Differential test for the three entry points in the 428-byte span at 0x001E1440.

The pinned original's ledger row at 0x001E1440 is 428 bytes and contains:

  * 0x001E1440 camp_func_001e1440 (372-byte body plus one pool word) -- the
    slot comparator reconstructed in ``src/engine/leaf_batch34_c.cpp``;
  * 0x001E15BC camp_func_001e15bc (16 bytes) -- 32-bit word comparator;
  * 0x001E15CC camp_func_001e15cc (32 bytes) -- s16 field comparator that
    tail-calls engine_func_002aa7f4 (0x002AA7F4).

The harness compiles the translation unit, extracts each candidate symbol,
resolves its direct-call relocations to deterministic stubs at the original
addresses, and runs the pinned original and the candidate in separate Unicorn
machines with identical fixtures.

Compared state:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log with every raw register argument (there are no stack
    arguments in these functions);
  * all observable memory outside the private stack: the 1 MiB slot-table page,
    the node page, the globals page, the input-slot page and a second table
    used by the pointer-mutation case;
  * unexpected writes outside the stack.

Coverage for camp_func_001e1440: every comparison stage and both directions,
primary and secondary 15-bit id masks (including bits 30..31), equal-value
lookup collisions, zero and non-zero lookup results, slot-index boundaries
(0x0000, 0x7FFF, 0x8000, 0xFFFF), slot-index re-read after helper calls,
work-pointer snapshot (a helper rewrites 0x0043DD68 mid-run), a shared input
slot, and a null node pointer (both sides fault after the same call prefix).

Coverage for the two tail comparators: zero/positive/negative word differences,
32-bit wrap-around, s16 boundaries, the tie path, and forwarded strcmp
arguments/results.

Negative controls mutate the primary mask, the secondary shift and the byte3
comparison order; each mutant must be detected by at least one case.
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
OUT_DIR = ROOT / "build/test_leaf_001e1440"

FUNC_ADDR = 0x001E1440
FUNC_SIZE = 428
ENTRY_15BC = 0x001E15BC
ENTRY_15CC = 0x001E15CC
OFFSET_15BC = ENTRY_15BC - FUNC_ADDR      # 0x17C
OFFSET_15CC = ENTRY_15CC - FUNC_ADDR      # 0x18C

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000
DATA_ADDR = 0x00430000
DATA_SIZE = 0x00020000
BASE_ADDR = 0x00500000
BASE_SIZE = 0x00100000
BASE2_ADDR = 0x00700000
BASE2_SIZE = 0x00010000
NODES_ADDR = 0x00800000
NODES_SIZE = 0x00010000
SLOTS_ADDR = 0x00810000
SLOTS_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100
SLOT_A_ADDR = SLOTS_ADDR + 0x100
SLOT_B_ADDR = SLOTS_ADDR + 0x200
WORK_POINTER_ADDR = 0x0043DD68
WORK_POINTER_OFFSET = WORK_POINTER_ADDR - DATA_ADDR
SLOT_TABLE_OFFSET = 0x1390
SLOT_STRIDE = 8

NODE_STRIDE = 0x94
NODE_COUNT = 32
NODE_S16_OFFSET = 0x0C

STUB_NODE = 0x002B9364
STUB_LOOKUP = 0x00288380
STUB_STRCMP = 0x002AA7F4

SYMBOL_TARGETS = {
    "camp_func_002b9364": STUB_NODE,
    "camp_func_00288380": STUB_LOOKUP,
    "engine_func_002aa7f4": STUB_STRCMP,
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


def to_s32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def to_u32(value: int) -> int:
    return value & 0xFFFFFFFF


def get_orig_block() -> bytes:
    with open(ORIG_BIN, "rb") as stream:
        stream.seek(FUNC_ADDR - 0x00100000)
        return stream.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path, name: str, entry: int) -> bytes:
    functions = extract_elf_functions_detailed(obj_file)
    if name not in functions:
        raise RuntimeError(f"{name} not found in {obj_file}: {sorted(functions)}")
    code_raw, relocs = functions[name]
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = SYMBOL_TARGETS.get(rel.symbol_name)
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        pc = entry + rel.offset + 8
        displacement = (target - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        cond = original & 0xFF000000
        struct.pack_into(
            "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
        )
    return bytes(code)


def extract_candidates(obj_file: Path) -> dict[str, bytes]:
    return {
        "camp_func_001e1440": relocate_candidate(
            obj_file, "camp_func_001e1440", FUNC_ADDR
        ),
        "camp_func_001e15bc": relocate_candidate(
            obj_file, "camp_func_001e15bc", ENTRY_15BC
        ),
        "camp_func_001e15cc": relocate_candidate(
            obj_file, "camp_func_001e15cc", ENTRY_15CC
        ),
    }


def compile_baseline() -> dict[str, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch34_c.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return extract_candidates(obj_file)


def compile_mutant(name: str, old: str, new: str) -> dict[str, bytes]:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    result = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {result.stderr}")
    return extract_candidates(obj_file)


# --------------------------------------------------------------------- fixtures
def default_node(index: int) -> tuple[int, int, int, int]:
    return (
        (index * 3) & 0xFFFF,
        (index * 5) & 0xFF,
        (index * 7) & 0xFF,
        (index * 11) & 0xFFFF,
    )


def pack_word(primary: int, secondary: int, high: int = 0) -> int:
    """Slot word whose primary field selects ``primary`` and secondary field
    selects ``secondary`` under the helpers' (value & 0xFFFF) % 32 mapping.

    Primary occupies bits 0..14, secondary bits 15..29.  Bits 30..31 are set
    from ``high`` to exercise the unused-field boundary.
    """
    word = ((secondary & 0x7FFF) << 15) | (primary & 0x7FFF)
    return to_u32(word | ((high & 3) << 30))


def primary_node(word: int) -> int:
    return (word & 0x7FFF) % NODE_COUNT


def secondary_node(word: int) -> int:
    return ((word >> 15) & 0x7FFF) % NODE_COUNT


def build_nodes(case: dict) -> bytes:
    fields = {index: default_node(index) for index in range(NODE_COUNT)}
    fields.update(case.get("nodes", {}))
    page = bytearray(NODES_SIZE)
    for index, (word0, byte2, byte3, s16) in fields.items():
        base = index * NODE_STRIDE
        struct.pack_into("<H", page, base, word0 & 0xFFFF)
        page[base + 2] = byte2 & 0xFF
        page[base + 3] = byte3 & 0xFF
        struct.pack_into("<h", page, base + NODE_S16_OFFSET, to_s16(s16))
    return bytes(page)


def to_s16(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def build_base(case: dict, key: str = "slot_words", size: int = BASE_SIZE) -> bytes:
    page = bytearray(size)
    for slot, word in case.get(key, {}).items():
        offset = SLOT_TABLE_OFFSET + slot * SLOT_STRIDE
        if offset + 4 > size:
            raise RuntimeError(f"slot 0x{slot:04x} does not fit in {size} bytes")
        struct.pack_into("<I", page, offset, word & 0xFFFFFFFF)
    return bytes(page)


def build_data(case: dict) -> bytes:
    page = bytearray(DATA_SIZE)
    struct.pack_into(
        "<I", page, WORK_POINTER_OFFSET, case.get("base_pointer", BASE_ADDR)
    )
    return bytes(page)


def build_slots(case: dict) -> bytes:
    page = bytearray(SLOTS_SIZE)
    struct.pack_into("<H", page, 0x100, case.get("slot_a", 0) & 0xFFFF)
    struct.pack_into("<H", page, 0x200, case.get("slot_b", 1) & 0xFFFF)
    if "word_a" in case:
        struct.pack_into("<I", page, 0x100, case["word_a"] & 0xFFFFFFFF)
    if "word_b" in case:
        struct.pack_into("<I", page, 0x200, case["word_b"] & 0xFFFFFFFF)
    # Tail-comparator records: 16-bit field at +0x0C plus filler bytes.
    struct.pack_into(
        "<h", page, 0x100 + NODE_S16_OFFSET, to_s16(case.get("a_s16", 0))
    )
    struct.pack_into(
        "<h", page, 0x200 + NODE_S16_OFFSET, to_s16(case.get("b_s16", 0))
    )
    page[0x100 + 0x10] = case.get("a_tag", 0x11)
    page[0x200 + 0x10] = case.get("b_tag", 0x22)
    return bytes(page)


class ComparatorRunner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(BASE_ADDR, BASE_SIZE)
        self.uc.mem_map(BASE2_ADDR, BASE2_SIZE)
        self.uc.mem_map(NODES_ADDR, NODES_SIZE)
        self.uc.mem_map(SLOTS_ADDR, SLOTS_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in SYMBOL_TARGETS.values():
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.node_calls = 0
        self.lookup_calls = 0
        self.strcmp_calls = 0
        self.case: dict = {}
        self.internal_write = False

    def _write_internal(self, address: int, data: bytes) -> None:
        self.internal_write = True
        try:
            self.uc.mem_write(address, data)
        finally:
            self.internal_write = False

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        if not self.internal_write:
            self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)

        if address == STUB_NODE:
            self.node_calls += 1
            self.call_log.append(("camp_func_002b9364", r0))

            if self.case.get("mutate_slots_on_node_call") == self.node_calls:
                self._write_internal(
                    SLOT_A_ADDR,
                    struct.pack("<H", self.case["mutate_slot_a"] & 0xFFFF),
                )
                self._write_internal(
                    SLOT_B_ADDR,
                    struct.pack("<H", self.case["mutate_slot_b"] & 0xFFFF),
                )
            if self.case.get("mutate_global_on_node_call") == self.node_calls:
                self._write_internal(
                    WORK_POINTER_ADDR,
                    struct.pack("<I", self.case.get("mutate_base_pointer", BASE2_ADDR)),
                )

            if self.case.get("null_node_call") == self.node_calls:
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
                return
            node_index = (r0 & 0xFFFF) % NODE_COUNT
            uc.reg_write(
                arm.UC_ARM_REG_R0, NODES_ADDR + node_index * NODE_STRIDE
            )
        elif address == STUB_LOOKUP:
            call_index = self.lookup_calls
            self.lookup_calls += 1
            self.call_log.append(("camp_func_00288380", r0))
            override = self.case.get("lookup_results")
            if override is not None and call_index < len(override):
                result = override[call_index] & 0xFFFF
            else:
                result = r0 % 5
            uc.reg_write(arm.UC_ARM_REG_R0, result)
        elif address == STUB_STRCMP:
            self.strcmp_calls += 1
            self.call_log.append(("engine_func_002aa7f4", r0, r1))
            uc.reg_write(
                arm.UC_ARM_REG_R0,
                self.case.get("strcmp_result", 0) & 0xFFFFFFFF,
            )
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def run(self, entry: int, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.node_calls = 0
        self.lookup_calls = 0
        self.strcmp_calls = 0
        self.case = case

        self.uc.mem_write(entry, code)
        self.uc.mem_write(DATA_ADDR, build_data(case))
        self.uc.mem_write(BASE_ADDR, build_base(case))
        self.uc.mem_write(BASE2_ADDR, build_base(case, "slot_words_b", BASE2_SIZE))
        self.uc.mem_write(NODES_ADDR, build_nodes(case))
        self.uc.mem_write(SLOTS_ADDR, build_slots(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SLOT_A_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, SLOT_B_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        fault = None
        try:
            self.uc.emu_start(entry, TRAP_ADDR, timeout=5_000_000)
        except unicorn.UcError as error:
            fault = str(error)

        unexpected_writes = []
        for address, size, _value in self.writes:
            if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE):
                unexpected_writes.append((address, size))

        result = {
            "fault": fault,
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "fixtures": {
                "base": bytes(self.uc.mem_read(BASE_ADDR, BASE_SIZE)),
                "base2": bytes(self.uc.mem_read(BASE2_ADDR, BASE2_SIZE)),
                "nodes": bytes(self.uc.mem_read(NODES_ADDR, NODES_SIZE)),
                "data": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
                "slots": bytes(self.uc.mem_read(SLOTS_ADDR, SLOTS_SIZE)),
            },
            "unexpected_writes": unexpected_writes,
        }
        return result


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    if orig["fault"] or cand["fault"]:
        if bool(orig["fault"]) != bool(cand["fault"]):
            problems.append(
                f"fault mismatch: orig={orig['fault']!r} cand={cand['fault']!r}"
            )
        if orig["call_log"] != cand["call_log"]:
            problems.append(
                "call_log (fault path):\n    orig="
                + repr(orig["call_log"])
                + "\n    cand="
                + repr(cand["call_log"])
            )
        if orig["unexpected_writes"] or cand["unexpected_writes"]:
            problems.append(
                "unexpected writes orig="
                f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
            )
        return problems

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
        if value != cand["fixtures"][key]:
            problems.append(f"fixture {key} was modified differently")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


# ----------------------------------------------------------------- reference model
def model_lookup(value: int, results, call_index: int) -> int:
    if results is not None and call_index < len(results):
        return results[call_index] & 0xFFFF
    return value % 5


def node_fields(case: dict, index: int) -> tuple[int, int, int]:
    return case.get("nodes", {}).get(index, default_node(index))[:3]


def model_main(case: dict) -> tuple[int, list]:
    slots = case.get("slot_words", {})
    slot_a = case.get("slot_a", 0)
    slot_b = case.get("slot_b", 1)
    lookup_results = case.get("lookup_results")

    call_log: list = []
    node_calls = 0
    lookup_calls = 0

    def node_calls_for(word: int) -> int:
        return word & 0x7FFF

    def secondary_calls_for(word: int) -> int:
        return (word >> 15) & 0x7FFF

    def lookup(value: int) -> int:
        nonlocal lookup_calls
        result = model_lookup(value, lookup_results, lookup_calls)
        lookup_calls += 1
        return result

    word_a = slots[slot_a]
    word_b = slots[slot_b]

    node_a = primary_node(word_a)
    node_b = primary_node(word_b)
    call_log.append(("camp_func_002b9364", node_calls_for(word_a)))
    call_log.append(("camp_func_002b9364", node_calls_for(word_b)))
    a0, a2, a3 = node_fields(case, node_a)
    b0, b2, b3 = node_fields(case, node_b)
    call_log.append(("camp_func_00288380", a0))
    call_log.append(("camp_func_00288380", b0))
    diff = lookup(a0) - lookup(b0)
    if diff != 0:
        return diff, call_log

    call_log.append(("camp_func_002b9364", node_calls_for(word_a)))
    call_log.append(("camp_func_002b9364", node_calls_for(word_b)))
    diff = a2 - b2
    if diff != 0:
        return diff, call_log
    diff = b3 - a3
    if diff != 0:
        return diff, call_log
    diff = a0 - b0
    if diff != 0:
        return diff, call_log

    # Second pass re-reads the caller's slot indices.
    if case.get("mutate_slots_on_node_call") is not None:
        slot_a = case["mutate_slot_a"]
        slot_b = case["mutate_slot_b"]
        word_a = slots.get(slot_a, 0)
        word_b = slots.get(slot_b, 0)
    node_a = secondary_node(word_a)
    node_b = secondary_node(word_b)
    call_log.append(
        ("camp_func_002b9364", secondary_calls_for(word_a))
    )
    call_log.append(
        ("camp_func_002b9364", secondary_calls_for(word_b))
    )
    a0, a2, a3 = node_fields(case, node_a)
    b0, b2, b3 = node_fields(case, node_b)
    call_log.append(("camp_func_00288380", a0))
    call_log.append(("camp_func_00288380", b0))
    diff = lookup(a0) - lookup(b0)
    if diff != 0:
        return diff, call_log

    call_log.append(
        ("camp_func_002b9364", secondary_calls_for(word_a))
    )
    call_log.append(
        ("camp_func_002b9364", secondary_calls_for(word_b))
    )
    diff = a2 - b2
    if diff != 0:
        return diff, call_log
    diff = b3 - a3
    if diff != 0:
        return diff, call_log
    return a0 - b0, call_log


def base_case(name: str, **overrides) -> dict:
    case = {"name": name, "slot_a": 0, "slot_b": 1}
    case.update(overrides)
    return case


def main_case(
    name: str,
    *,
    primary: tuple,
    secondary: tuple,
    word_a: int | None = None,
    word_b: int | None = None,
    slot_a: int = 0,
    slot_b: int = 1,
    **overrides,
) -> dict:
    if word_a is None:
        word_a = pack_word(1, 3)
    if word_b is None:
        word_b = pack_word(2, 4)
    (a0, a2, a3), (b0, b2, b3) = primary
    (c0, c2, c3), (d0, d2, d3) = secondary
    nodes = {
        primary_node(word_a): (a0, a2, a3, 0),
        primary_node(word_b): (b0, b2, b3, 0),
        secondary_node(word_a): (c0, c2, c3, 0),
        secondary_node(word_b): (d0, d2, d3, 0),
    }
    if len(nodes) != 4:
        raise RuntimeError(f"{name}: primary/secondary node collision: {sorted(nodes)}")
    case = base_case(
        name,
        slot_words={slot_a: word_a, slot_b: word_b},
        nodes=nodes,
        slot_a=slot_a,
        slot_b=slot_b,
    )
    case.update(overrides)
    return case


def make_main_cases() -> list[dict]:
    equal_fields = (0x0000, 0x00, 0x00)
    cases: list[dict] = []

    # Stage 1: lookup comparison.  Values 0 and 4 exercise both signs at the
    # modulo-5 stub's extremes; 0xFFFF and 0x0000 give a 0-vs-0 collision.
    cases.append(
        main_case(
            "primary lookup positive",
            primary=((7, 0x20, 0x30), (10, 0x20, 0x30)),
            secondary=(equal_fields, equal_fields),
        )
    )
    cases.append(
        main_case(
            "primary lookup negative",
            primary=((10, 0x20, 0x30), (7, 0x20, 0x30)),
            secondary=(equal_fields, equal_fields),
        )
    )
    cases.append(
        main_case(
            "primary lookup collision 0 vs 5",
            primary=((0xFFFF, 0x20, 0x30), (0x0005, 0x20, 0x30)),
            secondary=(equal_fields, equal_fields),
        )
    )

    # Stage 2: byte at +2.
    cases.append(
        main_case(
            "primary byte2 positive",
            primary=((10, 0x10, 0x30), (5, 0x20, 0x30)),
            secondary=(equal_fields, equal_fields),
        )
    )
    cases.append(
        main_case(
            "primary byte2 negative",
            primary=((10, 0x20, 0x30), (5, 0x10, 0x30)),
            secondary=(equal_fields, equal_fields),
        )
    )
    cases.append(
        main_case(
            "primary byte2 boundary 0xFF vs 0x00",
            primary=((10, 0xFF, 0x30), (5, 0x00, 0x30)),
            secondary=(equal_fields, equal_fields),
        )
    )

    # Stage 3: byte at +3, note the reversed operand order (b3 - a3).
    cases.append(
        main_case(
            "primary byte3 positive",
            primary=((10, 0x20, 0x10), (5, 0x20, 0x30)),
            secondary=(equal_fields, equal_fields),
        )
    )
    cases.append(
        main_case(
            "primary byte3 negative",
            primary=((10, 0x20, 0x30), (5, 0x20, 0x10)),
            secondary=(equal_fields, equal_fields),
        )
    )
    cases.append(
        main_case(
            "primary byte3 boundary 0x00 vs 0xFF",
            primary=((10, 0x20, 0x00), (5, 0x20, 0xFF)),
            secondary=(equal_fields, equal_fields),
        )
    )

    # Stage 4: u16 word at +0, a0 - b0.
    cases.append(
        main_case(
            "primary word0 positive",
            primary=((0x0001, 0x20, 0x30), (0x0006, 0x20, 0x30)),
            secondary=(equal_fields, equal_fields),
        )
    )
    cases.append(
        main_case(
            "primary word0 negative",
            primary=((0x0006, 0x20, 0x30), (0x0001, 0x20, 0x30)),
            secondary=(equal_fields, equal_fields),
        )
    )
    cases.append(
        main_case(
            "primary word0 boundary 0xFFFF vs 0x000A",
            primary=((0xFFFF, 0x20, 0x30), (0x000A, 0x20, 0x30)),
            secondary=(equal_fields, equal_fields),
        )
    )

    # Fully equal primary records, differing secondary records.
    cases.append(
        main_case(
            "secondary lookup positive",
            primary=(equal_fields, equal_fields),
            secondary=((7, 0x40, 0x50), (10, 0x40, 0x50)),
        )
    )
    cases.append(
        main_case(
            "secondary lookup negative",
            primary=(equal_fields, equal_fields),
            secondary=((10, 0x40, 0x50), (7, 0x40, 0x50)),
        )
    )
    cases.append(
        main_case(
            "secondary byte2 positive",
            primary=(equal_fields, equal_fields),
            secondary=((10, 0x40, 0x50), (5, 0x60, 0x50)),
        )
    )
    cases.append(
        main_case(
            "secondary byte2 negative",
            primary=(equal_fields, equal_fields),
            secondary=((10, 0x60, 0x50), (5, 0x40, 0x50)),
        )
    )
    cases.append(
        main_case(
            "secondary byte3 positive",
            primary=(equal_fields, equal_fields),
            secondary=((10, 0x40, 0x10), (5, 0x40, 0x30)),
        )
    )
    cases.append(
        main_case(
            "secondary byte3 negative",
            primary=(equal_fields, equal_fields),
            secondary=((10, 0x40, 0x30), (5, 0x40, 0x10)),
        )
    )
    cases.append(
        main_case(
            "secondary word0 positive",
            primary=(equal_fields, equal_fields),
            secondary=((0x0001, 0x40, 0x50), (0x0006, 0x40, 0x50)),
        )
    )
    cases.append(
        main_case(
            "secondary word0 negative",
            primary=(equal_fields, equal_fields),
            secondary=((0x0006, 0x40, 0x50), (0x0001, 0x40, 0x50)),
        )
    )

    # All comparisons equal: both passes return zero.
    cases.append(
        main_case(
            "all equal",
            primary=(equal_fields, equal_fields),
            secondary=(equal_fields, equal_fields),
        )
    )

    # Masks: bits 30..31 are unused and the primary id is exactly bits 0..14.
    # A word with all secondary bits set verifies that the primary lookup does
    # not accidentally include any bit at or above bit 15.
    cases.append(
        main_case(
            "high bits 30..31 ignored",
            primary=((0x7FFF, 0x20, 0x30), (0x000A, 0x20, 0x30)),
            secondary=(equal_fields, equal_fields),
            word_a=pack_word(1, 3, high=3),
            word_b=pack_word(2, 4, high=2),
        )
    )
    full_secondary = (0x7FFF << 15) | 0x0001
    cases.append(
        main_case(
            "primary mask excludes bits 15..29",
            primary=((7, 0x20, 0x30), (10, 0x20, 0x30)),
            secondary=(equal_fields, equal_fields),
            word_a=full_secondary,
            word_b=pack_word(2, 4),
        )
    )
    high_primary = (5 << 15) | 0x4001
    cases.append(
        main_case(
            "primary bit 14 retained",
            primary=((7, 0x20, 0x30), (10, 0x20, 0x30)),
            secondary=(equal_fields, equal_fields),
            word_a=high_primary,
            word_b=pack_word(2, 4),
        )
    )

    # Slot-index boundaries.
    for slot_a, slot_b in ((0x0000, 0x0001), (0x7FFF, 0x8000), (0xFFFF, 0x8000),
                           (0xFFFF, 0xFFFF)):
        cases.append(
            main_case(
                f"slot indices 0x{slot_a:04x}/0x{slot_b:04x}",
                primary=((7, 0x20, 0x30), (10, 0x20, 0x30)),
                secondary=(equal_fields, equal_fields),
                slot_a=slot_a,
                slot_b=slot_b,
            )
        )

    # Shared input slot: both callers point at the same u16.
    shared = main_case(
        "shared input slot",
        primary=((0x0001, 0x20, 0x30), (0x0006, 0x20, 0x30)),
        secondary=(equal_fields, equal_fields),
    )
    shared["slot_b"] = shared["slot_a"]
    cases.append(shared)

    # Lookup stub returns a constant zero for every call.
    cases.append(
        main_case(
            "lookup returns zero",
            primary=((0x0001, 0x20, 0x30), (0x0006, 0x20, 0x30)),
            secondary=(equal_fields, equal_fields),
            lookup_results=[0, 0, 0, 0],
        )
    )

    # Slot-index re-read: the first node lookup rewrites both caller slots.
    # The primary records are identical so execution reaches the second pass,
    # which must observe the rewritten slot indices.
    reread = main_case(
        "slot indices re-read after helper",
        primary=(equal_fields, equal_fields),
        secondary=((10, 0x40, 0x10), (5, 0x40, 0x30)),
        mutate_slots_on_node_call=1,
        mutate_slot_a=2,
        mutate_slot_b=3,
    )
    reread["slot_words"][2] = pack_word(5, 6)
    reread["slot_words"][3] = pack_word(6, 7)
    reread["nodes"].update(
        {
            primary_node(reread["slot_words"][2]): (0x30, 0x50, 0x60, 0),
            primary_node(reread["slot_words"][3]): (0x40, 0x50, 0x60, 0),
            secondary_node(reread["slot_words"][2]): (0x50, 0x70, 0x80, 0),
            secondary_node(reread["slot_words"][3]): (0x60, 0x70, 0x80, 0),
        }
    )
    cases.append(reread)

    # Work-pointer snapshot: a helper rewrites 0x0043DD68 during the primary
    # pass.  The original cached the old table in r4, so the second pass must
    # keep using BASE_ADDR, not BASE2_ADDR.
    snapshot = main_case(
        "work pointer snapshot",
        primary=(equal_fields, equal_fields),
        secondary=((10, 0x40, 0x10), (5, 0x40, 0x30)),
        mutate_global_on_node_call=1,
        mutate_base_pointer=BASE2_ADDR,
    )
    snapshot["slot_words_b"] = {
        snapshot["slot_a"]: pack_word(20, 21),
        snapshot["slot_b"]: pack_word(22, 23),
    }
    cases.append(snapshot)

    # Null node pointer: both sides fault on the first dereference.  The call
    # log prefix is the observable contract for this invalid input.
    cases.append(
        main_case(
            "null node pointer fault",
            primary=((7, 0x20, 0x30), (10, 0x20, 0x30)),
            secondary=(equal_fields, equal_fields),
            null_node_call=1,
        )
    )

    return cases


def make_15bc_cases() -> list[dict]:
    return [
        base_case("word compare equal", word_a=0x12345678, word_b=0x12345678),
        base_case("word compare positive", word_a=2, word_b=1),
        base_case("word compare negative", word_a=1, word_b=2),
        base_case("word compare zero vs max", word_a=0xFFFFFFFF, word_b=0),
        base_case("word compare max vs zero", word_a=0, word_b=0xFFFFFFFF),
        base_case("word compare 0x80000000", word_a=0x80000000, word_b=0),
        base_case("word compare 0x7FFFFFFF/0x80000000",
                  word_a=0x7FFFFFFF, word_b=0x80000000),
        base_case("word compare wrap pair", word_a=0x80000001, word_b=0x7FFFFFFF),
    ]


def make_15cc_cases() -> list[dict]:
    cases = [
        base_case("s16 positive", a_s16=1, b_s16=2),
        base_case("s16 negative", a_s16=2, b_s16=1),
        base_case("s16 equal delegates zero", a_s16=5, b_s16=5,
                  strcmp_result=0),
        base_case("s16 equal delegates positive", a_s16=5, b_s16=5,
                  strcmp_result=7),
        base_case("s16 equal delegates negative", a_s16=5, b_s16=5,
                  strcmp_result=to_u32(-9)),
        base_case("s16 minimum vs maximum", a_s16=-0x8000, b_s16=0x7FFF),
        base_case("s16 maximum vs minimum", a_s16=0x7FFF, b_s16=-0x8000),
        base_case("s16 -1 vs 1", a_s16=-1, b_s16=1),
        base_case("s16 0x8000 equal", a_s16=-0x8000, b_s16=-0x8000,
                  strcmp_result=1),
        base_case("s16 0x7FFF equal", a_s16=0x7FFF, b_s16=0x7FFF,
                  strcmp_result=to_u32(-1)),
    ]
    return cases


# ------------------------------------------------------------------------ tests
def run_cases(entry: int, orig_code: bytes, cand_code: bytes, cases,
              expect_model=None, fault_cases=0) -> int:
    passed = 0
    for case in cases:
        orig = ComparatorRunner().run(entry, orig_code, case)
        cand = ComparatorRunner().run(entry, cand_code, case)
        problems = compare(orig, cand)
        if expect_model is not None and not orig["fault"]:
            expected, expected_log = expect_model(case)
            if orig["ret"] != to_u32(expected):
                problems.append(
                    f"original did not exercise the model: orig={orig['ret']} "
                    f"expected={to_u32(expected)}"
                )
            if orig["call_log"] != expected_log:
                problems.append(
                    "original call log differs from model:\n    orig="
                    + repr(orig["call_log"])
                    + "\n    model="
                    + repr(expected_log)
                )
        if case.get("null_node_call") is not None:
            if not (orig["fault"] and cand["fault"]):
                problems.append("null-node case did not fault on both sides")
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        suffix = " (fault path)" if orig["fault"] else ""
        print(
            f"  [PASS] {case['name']}  ret={orig['ret']} "
            f"calls={len(orig['call_log'])}{suffix}"
        )
    return passed


def main() -> None:
    print("Testing the 0x001E1440 comparator span (428 bytes)...")
    orig_block = get_orig_block()
    if struct.unpack_from("<I", orig_block, 0x178)[0] != 0x0043DD68:
        raise RuntimeError("original pool word at 0x001E15B8 changed")
    baseline = compile_baseline()
    print(
        f"Original span {len(orig_block)} B; candidates: "
        + ", ".join(f"{name} {len(code)} B" for name, code in baseline.items())
    )

    main_cases = make_main_cases()
    passed = 0
    passed += run_cases(
        FUNC_ADDR,
        orig_block,
        baseline["camp_func_001e1440"],
        main_cases,
        expect_model=model_main,
    )

    passed += run_cases(
        ENTRY_15BC,
        orig_block[OFFSET_15BC:OFFSET_15BC + 16],
        baseline["camp_func_001e15bc"],
        make_15bc_cases(),
        expect_model=lambda case: (
            to_s32(case["word_a"] - case["word_b"]),
            [],
        ),
    )

    def model_15cc(case: dict) -> tuple[int, list]:
        a = to_s16(case.get("a_s16", 0))
        b = to_s16(case.get("b_s16", 0))
        if a != b:
            return a - b, []
        return to_s32(case.get("strcmp_result", 0)), [
            ("engine_func_002aa7f4", SLOT_A_ADDR, SLOT_B_ADDR)
        ]

    passed += run_cases(
        ENTRY_15CC,
        orig_block[OFFSET_15CC:OFFSET_15CC + 32],
        baseline["camp_func_001e15cc"],
        make_15cc_cases(),
        expect_model=model_15cc,
    )

    print("\nNegative controls:")
    for name, old, new in (
        ("primary_mask", "kCampComparatorPrimaryIdMask = 0x7FFF",
         "kCampComparatorPrimaryIdMask = 0x3FFF"),
        ("secondary_shift", "kCampComparatorSecondaryIdShift = 15",
         "kCampComparatorSecondaryIdShift = 14"),
        ("byte3_offset", "kCampComparatorNodeByte3Offset = 0x03",
         "kCampComparatorNodeByte3Offset = 0x02"),
    ):
        mutant = compile_mutant(name, old, new)
        detected = False
        for case in main_cases:
            orig = ComparatorRunner().run(
                FUNC_ADDR, orig_block, case
            )
            bad = ComparatorRunner().run(
                FUNC_ADDR, mutant["camp_func_001e1440"], case
            )
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed} differential cases PASSED.")


if __name__ == "__main__":
    main()
