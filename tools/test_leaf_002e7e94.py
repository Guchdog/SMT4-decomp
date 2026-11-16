#!/usr/bin/env python3
"""Differential test for engine_func_002e7e94 (0x002e7e94).

`effParts` child-node destroy: the node is detached from a doubly linked child
list, remaining flagged members are either destroyed recursively (flag 0x1) or
re-parented through 0x0025C888 (low flag bits 0x2 with +0x94 == the node's
particle), then the particle is released and the node is freed.

This runner compiles src/engine/leaf_batch45_a.cpp, extracts that one function,
relocates its self-recursion and its two direct calls, and executes the pinned
original (extracted/exefs/code.bin) and the candidate in separate Unicorn ARM
machines with identical fixtures.

Compared:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log: (kind, arguments) for 0x002C4360, 0x0025C888 and the
    0x00464110 entry hook at +0x10, including the type index;
  * the full manager/node/particle/context/block page, the 0x00464110 table
    page and the capture page;
  * any emulated write outside the stack or the fixture page.

Coverage: manager list empty, single node, chains of two to six; target at the
head, tail, middle and outside the list; node flags 0, 1, 2, 3, 0xFFFFFFF2,
0xFFFFFFFC; particle with no resources, only the instance, only each owned
block, both blocks, and every block pointer null; type indices 0, 1, 7 and 34
(table stride); alias members sharing / not sharing the particle, with flag 0,
1 and 3; one to three bound members with matching / non-matching +0x94, flag 3
and 0xFFFFFFF2, both with and without a preceding alias recursion; manager
count 0, 1 and 0xFFFFFFFF; members carrying distinct sentinels in their own
+0x80/+0x88/+0x8C header words (the routine must only use the manager's).

Negative controls mutate the flag constants, the count step, the tail link
store, the freed block offset and the re-parent anchor; each mutant must be
detected.
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
SOURCE = ROOT / "src/engine/leaf_batch45_a.cpp"
OUT_DIR = ROOT / "build/test_leaf_002e7e94"

FUNC_ADDR = 0x002E7E94
FUNC_SIZE = 604

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers the function and every stub below 0x3F0000

HOOK_BASE = 0x00310000  # 35 destroy + 35 create stubs, 0x10 apart
HOOK_CREATE_BIAS = 0x800
TABLE_ADDR = 0x00464000  # contains the 0x00464110 type table
TABLE_SIZE = 0x00001000
PAGE_ADDR = 0x00700000  # manager, nodes, particles, contexts and blocks
PAGE_SIZE = 0x00010000
CAPTURE_ADDR = 0x00720000
CAPTURE_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

TYPE_TABLE_BASE = 0x00464110
TYPE_STRIDE = 0x44
TYPE_COUNT = 35

# Original direct-call targets; stubs live at the same addresses so the original
# bytes and the relocated candidate reach the same code.
STUB_2C4360 = 0x002C4360
STUB_25C888 = 0x0025C888

STUB_NAMES = {
    STUB_2C4360: "engine_func_002c4360",
    STUB_25C888: "engine_func_0025c888",
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

# Fixture layout inside the private page.
MANAGER = PAGE_ADDR + 0x0100
NODE_BASE = PAGE_ADDR + 0x1000
NODE_STRIDE = 0x100
PARTICLE_BASE = PAGE_ADDR + 0x3000
PARTICLE_STRIDE = 0x40
CONTEXT_BASE = PAGE_ADDR + 0x5000
CONTEXT_STRIDE = 0x40
BLOCK_BASE = PAGE_ADDR + 0x7000
BLOCK_STRIDE = 0x40
SLOT_COUNT = 8

# Hard fixture bound: every list has at most this many members, so a runaway
# recursion is reported instead of emulated forever.
MAX_STUB_CALLS = 96


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "002e7e94" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"engine_func_002e7e94 not found in {obj_file}: {sorted(funcs)}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        if "002e7e94" in rel.symbol_name:
            target = FUNC_ADDR
        else:
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


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
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
def node_addr(index: int) -> int:
    return NODE_BASE + index * NODE_STRIDE


def particle_addr(index: int) -> int:
    return PARTICLE_BASE + index * PARTICLE_STRIDE


def context_addr(index: int) -> int:
    return CONTEXT_BASE + index * CONTEXT_STRIDE


def block_addr(index: int) -> int:
    return BLOCK_BASE + index * BLOCK_STRIDE


def resolve_pointer(spec, case) -> int:
    if spec is None:
        return 0
    if isinstance(spec, int):
        return spec
    kind, _, number = spec.partition(":")
    if kind == "particle":
        return particle_addr(int(number))
    if kind == "context":
        return context_addr(int(number))
    if kind == "block":
        return block_addr(int(number))
    if kind == "target":
        return node_particle(case, case["target"])
    raise RuntimeError(f"unknown pointer spec {spec!r}")


def node_particle(case, index: int) -> int:
    spec = case["nodes"][index]["particle"]
    return 0 if spec is None else resolve_pointer(spec, case)


def build_page(case: dict) -> bytes:
    page = bytearray(PAGE_SIZE)
    nodes = case["nodes"]
    order = case["order"]
    target = case["target"]

    if target >= len(nodes):
        raise RuntimeError("target node index out of range")
    if len(order) > 8:
        raise RuntimeError("fixture exceeds the bounded list length")

    manager = MANAGER - PAGE_ADDR
    struct.pack_into("<I", page, manager + 0x80, case.get("count", 1) & 0xFFFFFFFF)
    has_list = bool(order)
    struct.pack_into("<I", page, manager + 0x8C, node_addr(order[0]) if has_list else 0)
    struct.pack_into("<I", page, manager + 0x88, node_addr(order[-1]) if has_list else 0)

    for index, node in enumerate(nodes):
        base = (NODE_BASE - PAGE_ADDR) + index * NODE_STRIDE
        # A member's own list header must survive untouched.
        struct.pack_into("<I", page, base + 0x80, 0xDEAD0080 | index)
        struct.pack_into("<I", page, base + 0x88, 0xDEAD0088 | index)
        struct.pack_into("<I", page, base + 0x8C, 0xDEAD008C | index)
        struct.pack_into("<I", page, base + 0x90, node_particle(case, index))
        struct.pack_into(
            "<I", page, base + 0x94, resolve_pointer(node["field_94"], case)
        )
        struct.pack_into("<I", page, base + 0x98, node["flags"] & 0xFFFFFFFF)
        page[base + 0x9C : base + 0xAC] = bytes([0xA0 | index] * 0x10)
        # Links are only written for members; detached nodes keep 0/0.
        if index in order:
            position = order.index(index)
            prev = node_addr(order[position - 1]) if position > 0 else 0
            nxt = (
                node_addr(order[position + 1])
                if position + 1 < len(order)
                else 0
            )
            struct.pack_into("<I", page, base + 0xAC, nxt)
            struct.pack_into("<I", page, base + 0xB0, prev)

    for index, particle in enumerate(case["particles"]):
        base = (PARTICLE_BASE - PAGE_ADDR) + index * PARTICLE_STRIDE
        struct.pack_into("<H", page, base + 0x04, particle.get("type", 0) & 0xFFFF)
        struct.pack_into(
            "<I", page, base + 0x08, resolve_pointer(particle.get("instance"), case)
        )
        struct.pack_into("<H", page, base + 0x0C, particle.get("field_0c", 0x0C0C))
        struct.pack_into("<I", page, base + 0x10, particle.get("data_0", 0) & 0xFFFFFFFF)
        struct.pack_into("<I", page, base + 0x14, particle.get("size_0", 0) & 0xFFFFFFFF)
        struct.pack_into(
            "<I", page, base + 0x18, resolve_pointer(particle.get("alloc_0"), case)
        )
        struct.pack_into("<H", page, base + 0x1C, particle.get("field_1c", 0x1C1C))
        struct.pack_into("<I", page, base + 0x20, particle.get("data_1", 0) & 0xFFFFFFFF)
        struct.pack_into("<I", page, base + 0x24, particle.get("size_1", 0) & 0xFFFFFFFF)
        struct.pack_into(
            "<I", page, base + 0x28, resolve_pointer(particle.get("alloc_1"), case)
        )

    # Context and block targets carry distinct sentinels: a wrong pointer shows
    # up in the call log and, if written, in the page comparison.
    for index in range(SLOT_COUNT):
        struct.pack_into("<I", page, (CONTEXT_BASE - PAGE_ADDR) + index * CONTEXT_STRIDE,
                         0xC07E0000 | index)
        struct.pack_into("<I", page, (BLOCK_BASE - PAGE_ADDR) + index * BLOCK_STRIDE,
                         0xB10C0000 | index)
    return bytes(page)


def build_table() -> bytes:
    page = bytearray(TABLE_SIZE)
    for type_index in range(TYPE_COUNT):
        entry = TYPE_TABLE_BASE - TABLE_ADDR + type_index * TYPE_STRIDE
        struct.pack_into("<I", page, entry + 0x10,
                         HOOK_BASE + type_index * 0x10)
        struct.pack_into("<I", page, entry + 0x14,
                         HOOK_BASE + HOOK_CREATE_BIAS + type_index * 0x10)
    return bytes(page)


class DestroyRunner:
    """One Unicorn ARM machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(TABLE_ADDR, TABLE_SIZE)
        self.uc.mem_map(PAGE_ADDR, PAGE_SIZE)
        self.uc.mem_map(CAPTURE_ADDR, CAPTURE_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        bx_lr = struct.pack("<I", 0xE12FFF1E)
        for address in STUB_NAMES:
            self.uc.mem_write(address, bx_lr)
        for type_index in range(TYPE_COUNT):
            self.uc.mem_write(HOOK_BASE + type_index * 0x10, bx_lr)
            self.uc.mem_write(HOOK_BASE + HOOK_CREATE_BIAS + type_index * 0x10, bx_lr)

        self.uc.hook_add(
            unicorn.UC_HOOK_CODE, self._on_helper, begin=STUB_2C4360, end=STUB_2C4360
        )
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE, self._on_helper, begin=STUB_25C888, end=STUB_25C888
        )
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE,
            self._on_hook,
            begin=HOOK_BASE,
            end=HOOK_BASE + HOOK_CREATE_BIAS + TYPE_COUNT * 0x10,
        )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []

    def _log(self, *entry) -> None:
        if len(self.call_log) >= MAX_STUB_CALLS:
            raise RuntimeError(f"fixture recursion bound exceeded: {self.call_log[-4:]}")
        self.call_log.append(entry)

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_helper(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        # 0x2C4360 takes one architected argument; r1/r2 are incidental.
        if address == STUB_2C4360:
            self._log(STUB_NAMES[address], r0)
        else:
            self._log(STUB_NAMES[address], r0, r1, r2)
        if address == STUB_2C4360:
            # Deterministic block-release status: both machines must match.
            uc.reg_write(arm.UC_ARM_REG_R0, 0xF4EE0000 | ((r0 >> 4) & 0xFFFF))
        else:
            # Documented effect of 0x0025C888 that the caller's rescan depends
            # on: the re-parented child records the anchor's particle at +0x94
            # (`ldr r0,[r5,#0x90]` then `str r0,[r6,#0x94]`, 0x0025C94C..
            # 0x0025C950).  The rest of that helper's relinking is out of scope.
            if r1 != 0 and PAGE_ADDR <= r1 < PAGE_ADDR + PAGE_SIZE:
                anchor_particle = 0
                if r2 != 0:
                    anchor_particle = struct.unpack(
                        "<I", uc.mem_read(r2 + 0x90, 4)
                    )[0]
                uc.mem_write(r1 + 0x94, struct.pack("<I", anchor_particle))
            uc.reg_write(arm.UC_ARM_REG_R0, 0x5E7A0000 | (r1 & 0xFFFF))

    def _on_hook(self, uc, address: int, size: int, user_data) -> None:
        offset = address - HOOK_BASE
        if offset >= HOOK_CREATE_BIAS:
            kind = "create_instance"
            type_index = (offset - HOOK_CREATE_BIAS) // 0x10
        else:
            kind = "destroy_instance"
            type_index = offset // 0x10
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        # The only architected argument is r0 (particle->instance); r1 holds the
        # resolved hook pointer and r2 the table address in the original.
        self._log(kind, type_index, r0)
        uc.reg_write(arm.UC_ARM_REG_R0, 0xD3570000 | type_index)

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(TABLE_ADDR, build_table())
        self.uc.mem_write(PAGE_ADDR, build_page(case))
        self.uc.mem_write(CAPTURE_ADDR, b"\x00" * CAPTURE_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, MANAGER)
        self.uc.reg_write(arm.UC_ARM_REG_R1, node_addr(case["target"]))
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
        for address, size, _value in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_page = PAGE_ADDR <= address < PAGE_ADDR + PAGE_SIZE
            if not (in_stack or in_page):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "fixtures": {
                "page": bytes(self.uc.mem_read(PAGE_ADDR, PAGE_SIZE)),
                "table": bytes(self.uc.mem_read(TABLE_ADDR, TABLE_SIZE)),
                "capture": bytes(self.uc.mem_read(CAPTURE_ADDR, CAPTURE_SIZE)),
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
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            problems.append(f"fixture {key} was modified differently")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


# ----------------------------------------------------------------------- cases
def nd(flags=0, particle="particle:0", field_94=None):
    return {"flags": flags, "particle": particle, "field_94": field_94}


def pt(type=0, instance=None, alloc_0=None, alloc_1=None, **fields):
    particle = {
        "type": type,
        "instance": instance,
        "alloc_0": alloc_0,
        "alloc_1": alloc_1,
        "data_0": fields.get("data_0", 0x11111111),
        "size_0": fields.get("size_0", 0x00000022),
        "data_1": fields.get("data_1", 0x33333333),
        "size_1": fields.get("size_1", 0x00000044),
        "field_0c": fields.get("field_0c", 0x0C0C),
        "field_1c": fields.get("field_1c", 0x1C1C),
    }
    return particle


def make_case(name, nodes, order, target, particles, count=1):
    return {
        "name": name,
        "nodes": nodes,
        "order": order,
        "target": target,
        "particles": particles,
        "count": count,
    }


def make_cases() -> list[dict]:
    cases: list[dict] = []
    idle = pt()
    busy = pt(instance="context:0", alloc_0="block:0", alloc_1="block:1")

    # --- particle resource combinations / flag early-outs
    cases.append(make_case("single idle node", [nd()], [0], 0, [idle]))
    cases.append(
        make_case("single node, instance only",
                  [nd()], [0], 0, [pt(instance="context:0")])
    )
    cases.append(
        make_case("single node, primary block only",
                  [nd()], [0], 0, [pt(alloc_0="block:0")])
    )
    cases.append(
        make_case("single node, secondary block only",
                  [nd()], [0], 0, [pt(alloc_1="block:1")])
    )
    cases.append(make_case("single node, all resources", [nd()], [0], 0, [busy]))
    for type_index in (1, 7, 34):
        cases.append(
            make_case(f"type index {type_index}",
                      [nd()], [0], 0,
                      [pt(type=type_index, instance="context:0",
                          alloc_0="block:0", alloc_1="block:1")])
        )

    # --- node flag early-outs
    cases.append(
        make_case("flag 1 alias with null particle",
                  [nd(flags=1, particle=None)], [0], 0, [])
    )
    cases.append(
        make_case("flag 1 alias with resources",
                  [nd(flags=1)], [0], 0, [busy])
    )
    cases.append(
        make_case("flag 2 node with resources", [nd(flags=2)], [0], 0, [busy])
    )
    cases.append(
        make_case("flag 3 node with null particle",
                  [nd(flags=3, particle=None)], [0], 0, [])
    )
    cases.append(
        make_case("flag 0xFFFFFFFC node", [nd(flags=0xFFFFFFFC)], [0], 0, [busy])
    )
    cases.append(
        make_case("flag 0x00000001 node", [nd(flags=1)], [0], 0, [])
    )

    # --- manager count boundaries
    for count in (0, 0xFFFFFFFF, 0x00000007):
        cases.append(
            make_case(f"manager count 0x{count:08x}",
                      [nd()], [0], 0, [busy], count=count)
        )

    # --- list shapes: head / middle / tail / single-node chain
    cases.append(make_case("head detach", [nd(), nd()], [0, 1], 0, [busy, idle]))
    cases.append(make_case("tail detach", [nd(), nd()], [0, 1], 1, [busy, idle]))
    cases.append(
        make_case("middle detach", [nd(), nd(), nd()], [0, 1, 2], 1,
                  [busy, idle, idle])
    )
    cases.append(
        make_case("detached target outside list",
                  [nd(), nd(), nd()], [0, 1], 2, [busy, idle, idle])
    )
    cases.append(
        make_case("empty list, detached target",
                  [nd()], [], 0, [busy])
    )
    cases.append(
        make_case("six node chain, target in middle",
                  [nd(), nd(), nd(), nd(), nd(), nd()],
                  [0, 1, 2, 3, 4, 5], 2,
                  [idle, idle, busy, idle, idle, idle])
    )

    # --- alias recursion (flag 0x1, same particle)
    cases.append(
        make_case("one alias behind target",
                  [nd(), nd(flags=1)], [0, 1], 0, [busy])
    )
    cases.append(
        make_case("two aliases",
                  [nd(), nd(flags=1), nd(flags=1)], [0, 1, 2], 0, [busy])
    )
    cases.append(
        make_case("alias before target",
                  [nd(flags=1), nd()], [0, 1], 1, [busy])
    )
    cases.append(
        make_case("alias not sharing the particle",
                  [nd(), nd(flags=1, particle="particle:1")], [0, 1], 0,
                  [busy, pt(instance="context:1")])
    )
    cases.append(
        make_case("same particle but flag 0 member",
                  [nd(), nd(flags=0)], [0, 1], 0, [busy])
    )
    cases.append(
        make_case("alias with flag 3",
                  [nd(), nd(flags=3)], [0, 1], 0, [busy])
    )
    cases.append(
        make_case("three aliases in a five node chain",
                  [nd(), nd(flags=1), nd(), nd(flags=1), nd(flags=1)],
                  [0, 1, 2, 3, 4], 0, [busy])
    )

    # --- bound members (low bits 0x2 and +0x94 == target particle).
    # A bound member carries its own particle: the re-parent helper rewrites
    # its +0x94 to the anchor's particle, and a member that also carried the
    # destroyed particle would make the original's rescan loop forever.
    cases.append(
        make_case("one bound member",
                  [nd(), nd(flags=2, particle="particle:1", field_94="target")],
                  [0, 1], 0, [busy, pt(instance="context:1")])
    )
    cases.append(
        make_case("two bound members",
                  [nd(), nd(flags=2, particle="particle:1", field_94="target"),
                   nd(flags=2, particle="particle:2", field_94="target")],
                  [0, 1, 2], 0,
                  [busy, pt(instance="context:1"), pt(instance="context:2")])
    )
    cases.append(
        make_case("three bound members",
                  [nd(), nd(flags=2, particle="particle:1", field_94="target"),
                   nd(flags=2, particle="particle:2", field_94="target"),
                   nd(flags=2, particle="particle:3", field_94="target")],
                  [0, 1, 2, 3], 0,
                  [busy, pt(instance="context:1"), pt(instance="context:2"),
                   pt(instance="context:3")])
    )
    cases.append(
        make_case("bound member with wrong +0x94",
                  [nd(), nd(flags=2, particle="particle:1",
                            field_94="particle:2")],
                  [0, 1], 0, [busy, idle, idle])
    )
    cases.append(
        make_case("bound member with flag 3",
                  [nd(), nd(flags=3, particle="particle:1", field_94="target")],
                  [0, 1], 0, [busy, idle])
    )
    cases.append(
        make_case("bound member with flag 0xFFFFFFF2",
                  [nd(), nd(flags=0xFFFFFFF2, particle="particle:1",
                            field_94="target")],
                  [0, 1], 0, [busy, idle])
    )
    cases.append(
        make_case("bound member with flag 6 (bit 2 must be ignored)",
                  [nd(), nd(flags=6, particle="particle:1", field_94="target")],
                  [0, 1], 0, [busy, idle])
    )
    cases.append(
        make_case("bound member with flag 0x0A (bits 2..3 ignored)",
                  [nd(), nd(flags=0x0A, particle="particle:1",
                            field_94="target")],
                  [0, 1], 0, [busy, idle])
    )
    cases.append(
        make_case("bound member under a flag 2 target",
                  [nd(flags=2), nd(flags=2, particle="particle:1",
                                   field_94="target")],
                  [0, 1], 0, [busy, idle])
    )
    cases.append(
        make_case("bound member is the head",
                  [nd(), nd(flags=2, particle="particle:1", field_94="target")],
                  [1, 0], 0, [busy, idle])
    )

    # --- combined alias recursion + re-parenting order
    cases.append(
        make_case("alias then two bound members",
                  [nd(), nd(flags=1),
                   nd(flags=2, particle="particle:1", field_94="target"),
                   nd(flags=2, particle="particle:2", field_94="target")],
                  [0, 1, 2, 3], 0, [busy, idle, idle, idle])
    )
    cases.append(
        make_case("two aliases then one bound member",
                  [nd(), nd(flags=1), nd(flags=1),
                   nd(flags=2, particle="particle:1", field_94="target")],
                  [0, 1, 2, 3], 0, [busy, idle, idle, idle])
    )
    cases.append(
        make_case("bound member keeps its own particle",
                  [nd(), nd(flags=2, particle="particle:1", field_94="target")],
                  [0, 1], 0, [busy, busy])
    )
    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = DestroyRunner().run(orig_code, case)
        cand = DestroyRunner().run(cand_code, case)
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
    print("Testing engine_func_002e7e94 (0x002e7e94)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(self-recursion and both direct calls relocated)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("alias_flag", "constexpr u32 kFlagAlias = 0x00000001u;",
         "constexpr u32 kFlagAlias = 0x00000004u;"),
        ("bound_mask", "constexpr u32 kFlagMask = 0x00000003u;",
         "constexpr u32 kFlagMask = 0x00000007u;"),
        ("count_step", "manager->count = manager->count - 1;",
         "manager->count = manager->count - 2;"),
        ("tail_store", "manager->last = node->prev;",
         "manager->first = node->prev;"),
        ("alloc_0_offset", "engine_func_002c4360(particle->alloc_0);",
         "engine_func_002c4360(particle->alloc_1);"),
        ("reparent_anchor", "engine_func_0025c888(manager, member, anchor);",
         "engine_func_0025c888(manager, member, member);"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = DestroyRunner().run(orig_code, case)
            try:
                bad = DestroyRunner().run(mutant_code, case)
            except RuntimeError as error:
                # A fault is a divergence too (the original completes).
                detected = True
                print(f"    ({error})")
                break
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
