#!/usr/bin/env python3
"""Differential test for engine_func_0019de18 (0x0019DE18) using Unicorn ARM.

The candidate body is compiled from ``src/engine/leaf_batch28_a.cpp`` and run
against the pinned original in separate ARM machines with identical fixtures.
The single direct helper (0x002AF604, the ``+0x0C`` chain search) and the two
allocator vtable slots (``[ctx][2]`` allocate, ``[ctx][3]`` release) are
replaced by deterministic hooks that record every argument, so the growth
boundaries can be driven exactly.

Coverage:
  * loop gate: count 0, 1, 5, -1 and 0x80000000 (signed), and a 3rd array slot
    that must not be read when the count is 2;
  * membership: empty chain, element == chain head, element found at depth 1
    and depth 3, element absent, and an element whose own link is already set;
  * append: free capacity above the used count, exactly-used and
    capacity == used + 1, the empty-vector grow, the grow with a copy of
    1/3 words, maximum 30-bit capacity, the unreachable ``capacity * 2``
    overflow guard, and a negative used count (begin > end) that only the
    signed ``bgt`` treats as "room available";
  * grow refusals: capacity tag 0, 0x80000000, 0xC0000000 and a null allocator
    context (append dropped silently, no calls, no writes);
  * duplicate elements with a null and a non-null owner word;
  * ordered call log with all register arguments;
  * return r0, PC, SP, LR, callee-saved r4-r11, the source/list/element/pool/
    vtable/context pages and every non-stack written byte;
  * fault parity when the allocator returns null (the original then stores the
    element through the low address 4).

Negative controls mutate the growable tag, the capacity mask, the element link
offset and the ``capacity > used`` comparison; each mutant must be detected.
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
SOURCE = ROOT / "src/engine/leaf_batch28_a.cpp"
OUT_DIR = ROOT / "build/test_leaf_0019de18"

FUNC_ADDR = 0x0019DE18
FUNC_SIZE = 420
FUNC_SYMBOL = "engine_func_0019de18"

HELPER_ADDR = 0x002AF604   # engine_func_002af604, chain search
ALLOC_STUB = 0x002F0000    # concept-only stub for vtable slot [2]
RELEASE_STUB = 0x002F0100  # concept-only stub for vtable slot [3]

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000
SCRATCH_ADDR = 0x0019D000  # rebuilt with the candidate body before every run
SCRATCH_SIZE = 0x00001000

SOURCE_ADDR = 0x00600000
SOURCE_SIZE = 0x00001000
LIST_ADDR = 0x00610000
LIST_SIZE = 0x00001000
ELEM_ADDR = 0x00620000
ELEM_SIZE = 0x00001000
POOL_ADDR = 0x00630000
POOL_SIZE = 0x00001000
VTABLE_ADDR = 0x00640000
VTABLE_SIZE = 0x00001000
CTX_ADDR = 0x00650000
CTX_SIZE = 0x00001000

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

ITEM_ARRAY_OFF = 0x100
ELEM_SLOT_BASE = 0x100
ELEM_SLOT_STRIDE = 0x40
ELEM_SLOT_COUNT = 8
OWNER_DEFAULT = ELEM_ADDR + 0x3F0
OLD_BASE = POOL_ADDR + 0x800

CAPACITY_MASK = 0x3FFFFFFF
CAPACITY_TAGS = 0xC0000000
GROWABLE_TAG = 0x40000000
GROW_ALIGN = 0x20

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

PAGES = ("source", "list", "elements", "pool", "vtable", "ctx")


def elem(slot: int) -> int:
    return ELEM_ADDR + ELEM_SLOT_BASE + slot * ELEM_SLOT_STRIDE


def pattern(size: int, seed: int = 11) -> bytes:
    return bytes(((i * 37 + seed) & 0xFF) for i in range(size))


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if FUNC_SYMBOL in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"{FUNC_SYMBOL} not found in {obj_file}: {sorted(funcs)}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    seen_helper = False
    for rel in relocs:
        if rel.relocation_type not in (1, 28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        if "002af604" not in rel.symbol_name:
            raise RuntimeError(f"unexpected call relocation: {rel.symbol_name}")
        seen_helper = True
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (HELPER_ADDR - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        condition = original & 0xFF000000
        struct.pack_into(
            "<I", code, rel.offset, condition | (displacement & 0x00FFFFFF)
        )
    if not seen_helper:
        raise RuntimeError("candidate does not call 0x002AF604")
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch28_a.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    result = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"mutant compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


# --------------------------------------------------------------------- fixtures
def case(name: str, **overrides) -> dict:
    value = {
        "name": name,
        "count": 0,
        "items": None,
        "items_ptr": SOURCE_ADDR + ITEM_ARRAY_OFF,
        "head": 0,
        "owner": OWNER_DEFAULT,
        "links": {},
        "ctx": CTX_ADDR,
        "capacity": GROWABLE_TAG,
        "old_words": [],
        "begin": None,
        "end": None,
        "alloc_null": False,
    }
    value.update(overrides)
    if value["items"] is None:
        count = value["count"]
        value["items"] = list(range(count)) if 0 < count <= 8 else []
    return value


def build_source(entry: dict) -> bytes:
    page = bytearray(pattern(SOURCE_SIZE, seed=31))
    struct.pack_into("<I", page, 0x24, entry["items_ptr"] & 0xFFFFFFFF)
    struct.pack_into("<i", page, 0x28, entry["count"])
    for index, item in enumerate(entry["items"]):
        address = item[1] if isinstance(item, tuple) else elem(item)
        struct.pack_into("<I", page, ITEM_ARRAY_OFF + 4 * index,
                         address & 0xFFFFFFFF)
    return bytes(page)


def build_list(entry: dict) -> bytes:
    page = bytearray(pattern(LIST_SIZE, seed=41))
    begin = entry["begin"]
    end = entry["end"]
    if begin is None and end is None:
        begin = OLD_BASE if entry["old_words"] else 0
        end = OLD_BASE + 4 * len(entry["old_words"]) if entry["old_words"] else 0
    struct.pack_into("<I", page, 0x0C, entry["head"] & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x10, entry["owner"] & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x14, entry["ctx"] & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x18, begin & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x1C, end & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x20, entry["capacity"] & 0xFFFFFFFF)
    return bytes(page)


def build_elements(entry: dict) -> bytes:
    page = bytearray(pattern(ELEM_SIZE, seed=53))
    for slot in range(ELEM_SLOT_COUNT):
        base = ELEM_SLOT_BASE + slot * ELEM_SLOT_STRIDE
        struct.pack_into("<I", page, base + 0x0C,
                         entry["links"].get(slot, 0) & 0xFFFFFFFF)
    return bytes(page)


def build_pool(entry: dict) -> bytes:
    page = bytearray(pattern(POOL_SIZE, seed=67))
    for index, word in enumerate(entry["old_words"]):
        struct.pack_into("<I", page, 0x800 + 4 * index, word & 0xFFFFFFFF)
    return bytes(page)


def build_vtable() -> bytes:
    page = bytearray(pattern(VTABLE_SIZE, seed=79))
    struct.pack_into("<4I", page, 0, 0x11111111, 0x22222222,
                     ALLOC_STUB, RELEASE_STUB)
    return bytes(page)


def build_ctx() -> bytes:
    page = bytearray(pattern(CTX_SIZE, seed=97))
    struct.pack_into("<I", page, 0, VTABLE_ADDR)
    return bytes(page)


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)

        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(SOURCE_ADDR, SOURCE_SIZE)
        self.uc.mem_map(LIST_ADDR, LIST_SIZE)
        self.uc.mem_map(ELEM_ADDR, ELEM_SIZE)
        self.uc.mem_map(POOL_ADDR, POOL_SIZE)
        self.uc.mem_map(VTABLE_ADDR, VTABLE_SIZE)
        self.uc.mem_map(CTX_ADDR, CTX_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in (HELPER_ADDR, ALLOC_STUB, RELEASE_STUB):
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_helper,
                         begin=HELPER_ADDR, end=HELPER_ADDR)
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_alloc,
                         begin=ALLOC_STUB, end=ALLOC_STUB)
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_release,
                         begin=RELEASE_STUB, end=RELEASE_STUB)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.alloc_index = 0
        self.alloc_null = False

    # ------------------------------------------------------------------ stubs
    def _read_u32(self, address: int) -> int:
        return struct.unpack("<I", self.uc.mem_read(address, 4))[0]

    def _on_helper(self, uc, address, size, user_data) -> None:
        node = uc.reg_read(arm.UC_ARM_REG_R0)
        key = uc.reg_read(arm.UC_ARM_REG_R1)
        self.call_log.append(("engine_func_002af604", node, key))
        current = node
        result = 0
        for _ in range(16):
            current = self._read_u32(current + 0x0C)
            if current == 0:
                result = 0
                break
            if current == key:
                result = 1
                break
        else:  # pragma: no cover - fixtures never build a cycle
            raise AssertionError("membership chain did not terminate")
        uc.reg_write(arm.UC_ARM_REG_R0, result)

    def _on_alloc(self, uc, address, size, user_data) -> None:
        ctx = uc.reg_read(arm.UC_ARM_REG_R0)
        requested = uc.reg_read(arm.UC_ARM_REG_R1)
        alignment = uc.reg_read(arm.UC_ARM_REG_R2)
        self.call_log.append(("allocate", ctx, requested, alignment, self.alloc_index))
        if self.alloc_null:
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        else:
            uc.reg_write(arm.UC_ARM_REG_R0, POOL_ADDR + 0x200 * self.alloc_index)
        self.alloc_index += 1

    def _on_release(self, uc, address, size, user_data) -> None:
        ctx = uc.reg_read(arm.UC_ARM_REG_R0)
        block = uc.reg_read(arm.UC_ARM_REG_R1)
        self.call_log.append(("release", ctx, block))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, entry: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.alloc_index = 0
        self.alloc_null = entry["alloc_null"]

        self.uc.mem_write(SCRATCH_ADDR, b"\x00" * SCRATCH_SIZE)
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(SOURCE_ADDR, build_source(entry))
        self.uc.mem_write(LIST_ADDR, build_list(entry))
        self.uc.mem_write(ELEM_ADDR, build_elements(entry))
        self.uc.mem_write(POOL_ADDR, build_pool(entry))
        self.uc.mem_write(VTABLE_ADDR, build_vtable())
        self.uc.mem_write(CTX_ADDR, build_ctx())
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        self.writes = []
        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SOURCE_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, LIST_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0xA5A5A5A5)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x5A5A5A5A)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        fault = None
        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except unicorn.UcError as error:
            fault = str(error)

        write_bytes = set()
        for address, size, _value in self.writes:
            if STACK_ADDR <= address < STACK_ADDR + STACK_SIZE:
                continue
            write_bytes.update(range(address, address + size))

        return {
            "fault": fault,
            "r0": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "lr": self.uc.reg_read(arm.UC_ARM_REG_LR),
            "callee_saved": {
                name: self.uc.reg_read(reg)
                for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "source": bytes(self.uc.mem_read(SOURCE_ADDR, SOURCE_SIZE)),
            "list": bytes(self.uc.mem_read(LIST_ADDR, LIST_SIZE)),
            "elements": bytes(self.uc.mem_read(ELEM_ADDR, ELEM_SIZE)),
            "pool": bytes(self.uc.mem_read(POOL_ADDR, POOL_SIZE)),
            "vtable": bytes(self.uc.mem_read(VTABLE_ADDR, VTABLE_SIZE)),
            "ctx": bytes(self.uc.mem_read(CTX_ADDR, CTX_SIZE)),
            "write_bytes": write_bytes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    if (orig["fault"] is None) != (cand["fault"] is None):
        return [f"fault: orig={orig['fault']!r} cand={cand['fault']!r}"]
    if orig["fault"] is not None:
        keys = ["call_log", "write_bytes"] + list(PAGES)
    else:
        # LR is caller-saved here: the original's epilogue restores PC from the
        # stack and leaves LR holding the last helper return address, so only
        # the defined results are compared.
        keys = ["r0", "pc", "sp", "callee_saved", "call_log",
                "write_bytes"] + list(PAGES)
    for key in keys:
        if orig[key] == cand[key]:
            continue
        if key in PAGES:
            left = orig[key]
            right = cand[key]
            diff = [i for i, (a, b) in enumerate(zip(left, right)) if a != b]
            problems.append(f"{key} differs at {len(diff)} bytes, first {diff[:12]}")
        elif key == "write_bytes":
            problems.append(
                f"write_bytes differ: only_orig={sorted(orig[key] - cand[key])[:16]} "
                f"only_cand={sorted(cand[key] - orig[key])[:16]}"
            )
        else:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    return problems


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- loop gate: signed count, no item array dereference -----------------
    cases.append(case("count 0 leaves everything untouched", count=0,
                      items_ptr=0))
    cases.append(case("count -1 skips the loop", count=-1, items_ptr=0))
    cases.append(case("count 0x80000000 skips the loop", count=-0x80000000,
                      items_ptr=0))
    cases.append(case("count 1 processes exactly one item", count=1, items=[0]))
    cases.append(case("count 2 ignores the third array slot", count=2,
                      items=[0, 1, ("raw", 0xDEAD0000)],
                      capacity=GROWABLE_TAG | 4, old_words=[elem(6)]))
    cases.append(case("count 5 processes five items", count=5, items=[0, 1, 2, 3, 4]))

    # --- membership chain ---------------------------------------------------
    cases.append(case("chain head equals the item", count=1, items=[0],
                      head=elem(0)))
    cases.append(case("item found at chain depth 1", count=1, items=[2],
                      head=elem(1), links={1: elem(2), 2: 0}))
    cases.append(case("item found at chain depth 3", count=1, items=[4],
                      head=elem(1),
                      links={1: elem(2), 2: elem(3), 3: elem(4)}))
    cases.append(case("chain of one null link, item absent", count=1, items=[2],
                      head=elem(1), links={1: 0}))
    cases.append(case("item absent from a two-node chain", count=1, items=[0],
                      head=elem(1), links={1: elem(2), 2: 0},
                      capacity=GROWABLE_TAG | 2))
    cases.append(case("item link set although absent from the chain",
                      count=1, items=[2], head=elem(1),
                      links={1: elem(3), 3: 0, 2: 0xDEADBEEF}))

    # --- item link gate -----------------------------------------------------
    cases.append(case("empty chain, item link already set", count=1, items=[0],
                      links={0: elem(7)}))
    cases.append(case("empty chain, item link set to the owner word",
                      count=1, items=[1], links={1: OWNER_DEFAULT}))

    # --- append with room ---------------------------------------------------
    cases.append(case("room in an empty vector writes end only", count=1,
                      items=[0], capacity=GROWABLE_TAG | 5))
    cases.append(case("room with one stored element", count=1, items=[0],
                      capacity=2, old_words=[elem(6)]))
    cases.append(case("maximum 30-bit capacity is room", count=1, items=[0],
                      capacity=GROWABLE_TAG | CAPACITY_MASK))
    cases.append(case("capacity 0x20000000 tag 0x40000000 is room", count=1,
                      items=[0], capacity=0x60000000))
    cases.append(case("negative used count is treated as room", count=1,
                      items=[0], capacity=0,
                      begin=OLD_BASE + 0x100, end=OLD_BASE + 0x80))

    # --- growth -------------------------------------------------------------
    cases.append(case("grow from empty", count=1, items=[0],
                      capacity=GROWABLE_TAG))
    cases.append(case("capacity == used grows after copying one word",
                      count=1, items=[0], capacity=GROWABLE_TAG | 1,
                      old_words=[elem(6)]))
    cases.append(case("grow from a three-word block", count=1, items=[0],
                      capacity=GROWABLE_TAG | 3,
                      old_words=[elem(4), elem(5), elem(6)]))
    cases.append(case("capacity == used + 1 does not grow", count=1, items=[0],
                      capacity=GROWABLE_TAG | 4,
                      old_words=[elem(4), elem(5), elem(6)]))
    cases.append(case("grow keeps the tag bits of the capacity word", count=1,
                      items=[0], capacity=GROWABLE_TAG | 1,
                      old_words=[elem(6)]))
    cases.append(case("two consecutive growths", count=2, items=[0, 1],
                      capacity=GROWABLE_TAG))

    # --- grow refusals ------------------------------------------------------
    cases.append(case("full vector, capacity tag 0 refuses", count=1, items=[0],
                      capacity=0))
    cases.append(case("full vector with data, tag 0 refuses", count=1,
                      items=[0], capacity=1, old_words=[elem(6)]))
    cases.append(case("full vector, tag 0x80000000 refuses", count=1, items=[0],
                      capacity=0x80000000))
    cases.append(case("full vector, tag 0xC0000000 refuses", count=1, items=[0],
                      capacity=0xC0000000))
    cases.append(case("full vector, null allocator context refuses", count=1,
                      items=[0], capacity=0, ctx=0))

    # --- duplicate items / owner word --------------------------------------
    cases.append(case("duplicate item with a null owner appends twice",
                      count=2, items=[0, 0], owner=0, capacity=GROWABLE_TAG))
    cases.append(case("duplicate item with an owner appends once",
                      count=2, items=[0, 0], capacity=GROWABLE_TAG))
    cases.append(case("room path appends two items into a real block",
                      count=2, items=[0, 1], capacity=4,
                      old_words=[elem(6)]))

    # --- mixed ordered sequence --------------------------------------------
    cases.append(case("mixed skip, grow and room sequence", count=5,
                      items=[0, 1, 2, 3, 4],
                      head=elem(5), links={5: elem(1), 1: 0, 3: 0x12345678},
                      capacity=GROWABLE_TAG | 2,
                      old_words=[elem(6), elem(7)]))

    # --- null allocation ----------------------------------------------------
    cases.append(case("null allocation from an empty vector leaves end at 4",
                      count=1, items=[0], capacity=GROWABLE_TAG,
                      alloc_null=True))
    cases.append(case("null allocation while copying faults on address 4",
                      count=1, items=[0], capacity=GROWABLE_TAG | 2,
                      old_words=[elem(6), elem(7)], alloc_null=True))

    return cases


def run_case_set(orig_code: bytes, cand_code: bytes, cases: list[dict]) -> int:
    passed = 0
    for entry in cases:
        orig = Runner().run(orig_code, entry)
        cand = Runner().run(cand_code, entry)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {entry['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {entry['name']}  ({len(orig['call_log'])} calls)"
              + ("  [faulted]" if orig["fault"] else ""))
    return passed


def check_expectations(orig_code: bytes, cases: list[dict]) -> None:
    """Guard the fixtures: confirm the intended paths really execute."""
    by_name = {entry["name"]: entry for entry in cases}
    runner = Runner()

    def run(name: str) -> dict:
        return runner.run(orig_code, by_name[name])

    grow = run("grow from empty")
    assert any(call[0] == "allocate" for call in grow["call_log"]), grow["call_log"]

    copied = run("grow from a three-word block")
    assert [call[0] for call in copied["call_log"]] == [
        "allocate", "release"], copied["call_log"]

    no_grow = run("capacity == used + 1 does not grow")
    assert no_grow["call_log"] == [], no_grow["call_log"]

    depth = run("item found at chain depth 3")
    assert depth["call_log"] == [("engine_func_002af604",
                                 elem(1), elem(4))], depth["call_log"]

    refused = run("full vector, capacity tag 0 refuses")
    assert refused["call_log"] == [], refused["call_log"]

    negative = run("negative used count is treated as room")
    assert negative["call_log"] == [], negative["call_log"]

    doubled = run("two consecutive growths")
    assert [call[0] for call in doubled["call_log"]] == [
        "allocate", "allocate", "release"], doubled["call_log"]

    null_alloc = run("null allocation from an empty vector leaves end at 4")
    assert null_alloc["fault"] is None
    assert [call[0] for call in null_alloc["call_log"]] == ["allocate"], (
        null_alloc["call_log"])

    null_copy = run("null allocation while copying faults on address 4")
    assert null_copy["fault"] is not None
    assert [call[0] for call in null_copy["call_log"]] == ["allocate"], (
        null_copy["call_log"])
    print("  [PASS] fixture expectations (grow, copy, refusal, chain, fault)")


def main() -> None:
    print("Testing engine_func_0019de18 (0x0019DE18)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
          "(call relocation resolved to 0x002AF604).")

    cases = make_cases()
    check_expectations(orig_code, cases)
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    controls = (
        ("growable_tag", "constexpr u32 kGrowableTag   = 0x40000000u;",
         "constexpr u32 kGrowableTag   = 0x80000000u;"),
        ("capacity_mask", "constexpr u32 kCapacityMask  = 0x3fffffffu;",
         "constexpr u32 kCapacityMask  = 0x1fffffffu;"),
        ("element_link_offset",
         "struct CollectedElement {\n    u8 unknown_00[0x0c];",
         "struct CollectedElement {\n    u8 unknown_00[0x10];"),
        ("room_compare", "if (static_cast<s32>(capacity) > used) {",
         "if (static_cast<s32>(capacity) >= used) {"),
    )
    for name, old, new in controls:
        mutant = compile_candidate_mutant(name, old, new)
        detected = False
        for entry in cases:
            orig = Runner().run(orig_code, entry)
            bad = Runner().run(mutant, entry)
            if compare(orig, bad):
                detected = True
                break
        if not detected:
            raise SystemExit(f"negative control failed: {name} was not detected")
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
