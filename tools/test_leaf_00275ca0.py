#!/usr/bin/env python3
"""Differential test for script_vm_func_00275ca0 (0x00275ca0) using Unicorn ARM.

The routine reads ``work = *(void**)0x004474D8`` and synchronises the two model
slots at ``work+0x0C`` and ``work+0x10`` with the byte flag at ``work+0x0A``.
A model's bit-1 flag (+0x00) is the hidden bit; ``backend->visual_node->visible``
(+0x2C -> +0x1F6) mirrors it.  Every transition calls 0x0029BDB4 and then
0x0028C8D0 with ``(backend, 1.0f)`` when showing or ``(backend, 0.0f)`` when
hiding; a model already in the requested state is skipped.

The runner compiles ``src/engine/leaf_batch41_c.cpp``, extracts
``script_vm_func_00275ca0``, resolves its three R_ARM_CALL and one R_ARM_JUMP24
relocations to deterministic stubs at the original targets, and runs the pinned
original (``extracted/exefs/code.bin``) against the candidate in separate
Unicorn machines with identical fixtures.

Compared per case:
  * continuation PC, final SP, callee-saved r4-r11 and s16-s31;
  * the ordered call log with the exact backend pointer and the raw s0 bits;
  * every emulated write outside the private stack;
  * the full contents of the global slot page, both work objects, all model,
    backend and visual-node pages (against an independent expected model).

Coverage:
  * bit-1 set/clear with active = 0, 1, 2, 0x80 and 0xFF;
  * model slots null / non-null in every combination, in both halves;
  * flags values 0, 1, 2, 3, 0xFFFFFFFD, 0xFFFFFFFF, 0x40000002, 0x80000000;
  * initial visible bytes 0x00, 0x01, 0x7F, 0x5A and 0xFF;
  * helper rewrites of the chain between calls: clearing model B, replacing
    model A, replacing model A's backend and replacing the work pointer itself;
  * an idempotent no-op path for each model/half (no store, no call).

Negative controls recompile mutated source (hidden mask, both volume literals,
active polarity, clear/set direction, visible value/offset, active field offset,
backend field offset and the second-half helper slot); every mutant must be
detected.

``r0`` at return is deliberately not compared: the routine is ``void`` and all
four static callers overwrite r0 immediately, so the original's residual r0 is
not part of the contract.  It is still recorded in the result for diagnostics.
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
OUT_DIR = ROOT / "build/test_leaf_00275ca0"

FUNC_NAME = "script_vm_func_00275ca0"
FUNC_ADDR = 0x00275CA0
FUNC_SIZE = 408

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000          # target plus both direct-call stubs
GLOBAL_ADDR = 0x00447000
GLOBAL_SIZE = 0x00001000
GLOBAL_SLOT = 0x004474D8
GLOBAL_PTR_OFFSET = GLOBAL_SLOT - GLOBAL_ADDR

STUB_29BDB4 = 0x0029BDB4
STUB_28C8D0 = 0x0028C8D0
STUB_BY_SYMBOL = {
    "ui_func_0029bdb4": STUB_29BDB4,
    "script_vm_func_0028c8d0": STUB_28C8D0,
}

ROOT_ADDR = 0x00500000
ROOT2_ADDR = 0x00501000
MODEL_A_ADDR = 0x00510000
MODEL_A2_ADDR = 0x00511000
MODEL_B_ADDR = 0x00520000
MODEL_B2_ADDR = 0x00521000
BACKEND_A_ADDR = 0x00530000
BACKEND_A2_ADDR = 0x00531000
BACKEND_B_ADDR = 0x00540000
BACKEND_B2_ADDR = 0x00541000
VISUAL_A_ADDR = 0x00550000
VISUAL_A2_ADDR = 0x00551000
VISUAL_B_ADDR = 0x00560000
VISUAL_B2_ADDR = 0x00561000
PAGE_SIZE = 0x00001000

DATA_PAGES = {
    ROOT_ADDR: 0x5A,
    ROOT2_ADDR: 0x5A,
    MODEL_A_ADDR: 0xC3,
    MODEL_A2_ADDR: 0xC3,
    MODEL_B_ADDR: 0xC3,
    MODEL_B2_ADDR: 0xC3,
    BACKEND_A_ADDR: 0xD4,
    BACKEND_A2_ADDR: 0xD4,
    BACKEND_B_ADDR: 0xD4,
    BACKEND_B2_ADDR: 0xD4,
    VISUAL_A_ADDR: 0xE5,
    VISUAL_A2_ADDR: 0xE5,
    VISUAL_B_ADDR: 0xE5,
    VISUAL_B2_ADDR: 0xE5,
}

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

VISIBLE_OFFSET = 0x1F6
MODEL_BACKEND_OFFSET = 0x08
BACKEND_VISUAL_OFFSET = 0x2C
ROOT_ACTIVE_OFFSET = 0x0A
ROOT_MODEL_A_OFFSET = 0x0C
ROOT_MODEL_B_OFFSET = 0x10
HIDDEN_FLAG = 2

VISIBLE_BITS = 0x3F800000
HIDDEN_BITS = 0x00000000

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

# Rewrite kinds performed by the first helper callback (see the stub below).
REWRITES = (
    None,
    "clear_model_b",
    "model_a_to_a2",
    "backend_a_to_a2",
    "root_to_root2",
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
def model(addr, visual_addr, flags, backend):
    return {
        "addr": addr,
        "visual": visual_addr,
        "backend": backend,
        "flags": flags & 0xFFFFFFFF,
    }


def make_state(case: dict) -> dict:
    root = {
        "addr": ROOT_ADDR,
        "active": case["active"] & 0xFF,
        "model_a": model(MODEL_A_ADDR, VISUAL_A_ADDR, case["flags_a"],
                         BACKEND_A_ADDR)
        if case["model_a"] else None,
        "model_b": model(MODEL_B_ADDR, VISUAL_B_ADDR, case["flags_b"],
                         BACKEND_B_ADDR)
        if case["model_b"] else None,
    }
    root2 = {
        "addr": ROOT2_ADDR,
        "active": case.get("root2_active", 1) & 0xFF,
        "model_a": model(MODEL_A2_ADDR, VISUAL_A2_ADDR,
                         case.get("root2_flags_a", 0), BACKEND_A2_ADDR),
        "model_b": model(MODEL_B2_ADDR, VISUAL_B2_ADDR,
                         case.get("root2_flags_b", 2), BACKEND_B2_ADDR),
    }
    return {
        "root": root,
        "root2": root2,
        "visible": {
            VISUAL_A_ADDR: case["visible_a"] & 0xFF,
            VISUAL_A2_ADDR: case.get("visible_a2", 0x6B) & 0xFF,
            VISUAL_B_ADDR: case["visible_b"] & 0xFF,
            VISUAL_B2_ADDR: case.get("visible_b2", 0x7C) & 0xFF,
        },
        "rewrite": case.get("rewrite"),
    }


def build_pages(state: dict) -> dict:
    pages = {
        address: bytearray([fill]) * PAGE_SIZE
        for address, fill in DATA_PAGES.items()
    }

    for key in ("root", "root2"):
        work = state[key]
        page = pages[work["addr"]]
        page[ROOT_ACTIVE_OFFSET] = work["active"]
        struct.pack_into(
            "<I", page, ROOT_MODEL_A_OFFSET,
            work["model_a"]["addr"] if work["model_a"] else 0,
        )
        struct.pack_into(
            "<I", page, ROOT_MODEL_B_OFFSET,
            work["model_b"]["addr"] if work["model_b"] else 0,
        )

    for key in ("root", "root2"):
        work = state[key]
        for slot in ("model_a", "model_b"):
            m = work[slot]
            if m is None:
                continue
            page = pages[m["addr"]]
            struct.pack_into("<I", page, 0, m["flags"])
            struct.pack_into("<I", page, MODEL_BACKEND_OFFSET, m["backend"])

    for backend_addr, visual_addr in (
        (BACKEND_A_ADDR, VISUAL_A_ADDR),
        (BACKEND_A2_ADDR, VISUAL_A2_ADDR),
        (BACKEND_B_ADDR, VISUAL_B_ADDR),
        (BACKEND_B2_ADDR, VISUAL_B2_ADDR),
    ):
        struct.pack_into(
            "<I", pages[backend_addr], BACKEND_VISUAL_OFFSET, visual_addr
        )

    for visual_addr, value in state["visible"].items():
        pages[visual_addr][VISIBLE_OFFSET] = value

    return pages


def build_global(root_addr: int) -> bytes:
    page = bytearray(b"\x77" * GLOBAL_SIZE)
    struct.pack_into("<I", page, GLOBAL_PTR_OFFSET, root_addr)
    return bytes(page)


# ---------------------------------------------------------------------------
# Independent expected model
# ---------------------------------------------------------------------------
def volume_bits(volume: float) -> int:
    return struct.unpack("<I", struct.pack("<f", volume))[0]


def apply_rewrite(state: dict) -> list:
    """Apply the case's single stub rewrite and return its memory stores."""
    kind = state["rewrite"]
    if kind is None:
        return []
    root = state["root"]
    if kind == "clear_model_b":
        root["model_b"] = None
        return [(root["addr"] + ROOT_MODEL_B_OFFSET, 4, 0)]
    if kind == "model_a_to_a2":
        root["model_a"] = state["root2"]["model_a"]
        return [(root["addr"] + ROOT_MODEL_A_OFFSET, 4, MODEL_A2_ADDR)]
    if kind == "backend_a_to_a2":
        root["model_a"]["backend"] = BACKEND_A2_ADDR
        return [(MODEL_A_ADDR + MODEL_BACKEND_OFFSET, 4, BACKEND_A2_ADDR)]
    if kind == "root_to_root2":
        state["root"] = state["root2"]
        return [(GLOBAL_SLOT, 4, ROOT2_ADDR)]
    raise AssertionError(f"unknown rewrite {kind!r}")


def expected_run(case: dict) -> tuple:
    """Return (call log, ordered stores).  Mirrors the recovered ARM contract."""
    state = make_state(case)
    log: list = []
    stores: list = []
    helper_calls = 0

    def call_helper(name: str, slot: str, volume: float) -> None:
        nonlocal helper_calls
        root = state["root"]
        m = root[slot]
        backend = m["backend"]
        log.append((name, backend, volume_bits(volume)))
        if helper_calls == 0:
            stores.extend(apply_rewrite(state))
        helper_calls += 1

    for slot in ("model_a", "model_b"):
        root = state["root"]
        m = root[slot]
        if m is None:
            continue
        flags = m["flags"]
        if root["active"] != 0:
            if (flags & HIDDEN_FLAG) == 0:
                continue
            new_flags = flags & ~HIDDEN_FLAG
            m["flags"] = new_flags
            stores.append((m["addr"], 4, new_flags))
            stores.append((m["visual"] + VISIBLE_OFFSET, 1, 1))
            call_helper("ui_func_0029bdb4", slot, 1.0)
            call_helper("script_vm_func_0028c8d0", slot, 1.0)
        else:
            if (flags & HIDDEN_FLAG) != 0:
                continue
            new_flags = flags | HIDDEN_FLAG
            m["flags"] = new_flags
            stores.append((m["addr"], 4, new_flags))
            stores.append((m["visual"] + VISIBLE_OFFSET, 1, 0))
            call_helper("ui_func_0029bdb4", slot, 0.0)
            call_helper("script_vm_func_0028c8d0", slot, 0.0)

    return log, stores


def apply_stores(pages: dict, stores: list) -> None:
    for address, size, value in stores:
        if address == GLOBAL_SLOT and size == 4:
            # Tracked separately by expected_global().
            continue
        page_addr = address & ~(PAGE_SIZE - 1)
        offset = address - page_addr
        if page_addr not in pages:
            raise AssertionError(f"store outside mapped pages: 0x{address:x}")
        if offset + size > PAGE_SIZE:
            raise AssertionError(f"store crosses page: 0x{address:x}")
        struct.pack_into(
            {1: "<B", 4: "<I"}[size], pages[page_addr], offset,
            value & ((1 << (8 * size)) - 1),
        )


# ---------------------------------------------------------------------------
# Candidate preparation
# ---------------------------------------------------------------------------
def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def sign_extend_24(value: int) -> int:
    return value - 0x1000000 if value & 0x800000 else value


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    entry = funcs.get(FUNC_NAME)
    if entry is None:
        raise RuntimeError(
            f"{FUNC_NAME} not found in {obj_file}: {sorted(funcs)}"
        )

    raw, relocs = entry
    code = bytearray(raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            target = STUB_BY_SYMBOL.get(rel.symbol_name)
            if target is None:
                raise RuntimeError(f"unexpected call relocation: {rel}")
            instruction = struct.unpack_from("<I", code, rel.offset)[0]
            addend = sign_extend_24(instruction & 0x00FFFFFF) << 2
            place = FUNC_ADDR + rel.offset
            displacement = (target + addend - place) >> 2
            struct.pack_into(
                "<I", code, rel.offset,
                (instruction & 0xFF000000) | (displacement & 0x00FFFFFF),
            )
        else:
            raise RuntimeError(f"unsupported relocation: {rel}")
    return bytes(code)


def compile_variant(src_file: Path, obj_file: Path) -> bytes:
    result = compile_tu_armv6k(src_file, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed for {src_file}: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return compile_variant(SOURCE, OUT_DIR / "leaf_batch41_c.o")


def compile_mutant(name: str, old: str, new: str, count: int = 1) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != count:
        raise RuntimeError(
            f"mutation anchor {old!r} occurs {text.count(old)} times, "
            f"expected {count}"
        )
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    return compile_variant(mutant_src, OUT_DIR / f"mutant_{name}.o")


# ---------------------------------------------------------------------------
# Machine
# ---------------------------------------------------------------------------
class Machine:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        # The original prologue uses VFP (vpush {d8}); enable CP10/CP11.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        for address, size in (
            (CODE_ADDR, CODE_SIZE),
            (GLOBAL_ADDR, GLOBAL_SIZE),
            (STACK_ADDR, STACK_SIZE),
            (TRAP_ADDR, 0x1000),
        ):
            self.uc.mem_map(address, size)
        for address in DATA_PAGES:
            self.uc.mem_map(address, PAGE_SIZE)

        self.orig_code = get_orig_bytes()
        self.call_log: list = []
        self.writes: list = []
        self.helper_calls = 0
        self.case: dict = {}

        bx_lr = struct.pack("<I", 0xE12FFF1E)
        for address, hook in (
            (STUB_29BDB4, self._on_29bdb4),
            (STUB_28C8D0, self._on_28c8d0),
        ):
            self.uc.mem_write(address, bx_lr)
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, hook, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

    # -- stubs ------------------------------------------------------------
    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value & ((1 << (8 * size)) - 1)))

    def _helper(self, name: str) -> None:
        backend = self.uc.reg_read(arm.UC_ARM_REG_R0)
        bits = self.uc.reg_read(arm.UC_ARM_REG_S0)
        self.call_log.append((name, backend, bits))

        if self.helper_calls == 0:
            kind = self.case.get("rewrite")
            if kind == "clear_model_b":
                self.uc.mem_write(ROOT_ADDR + ROOT_MODEL_B_OFFSET,
                                  struct.pack("<I", 0))
            elif kind == "model_a_to_a2":
                self.uc.mem_write(ROOT_ADDR + ROOT_MODEL_A_OFFSET,
                                  struct.pack("<I", MODEL_A2_ADDR))
            elif kind == "backend_a_to_a2":
                self.uc.mem_write(MODEL_A_ADDR + MODEL_BACKEND_OFFSET,
                                  struct.pack("<I", BACKEND_A2_ADDR))
            elif kind == "root_to_root2":
                self.uc.mem_write(GLOBAL_SLOT, struct.pack("<I", ROOT2_ADDR))
            elif kind is not None:
                raise AssertionError(f"unknown rewrite {kind!r}")
        self.helper_calls += 1

    def _on_29bdb4(self, uc, address, size, user_data) -> None:
        self._helper("ui_func_0029bdb4")

    def _on_28c8d0(self, uc, address, size, user_data) -> None:
        self._helper("script_vm_func_0028c8d0")

    # -- execution --------------------------------------------------------
    def run(self, candidate: bytes | None, case: dict) -> dict:
        uc = self.uc
        self.case = case
        self.call_log = []
        self.helper_calls = 0

        state = make_state(case)
        pages = build_pages(state)

        uc.mem_write(FUNC_ADDR, self.orig_code if candidate is None else candidate)
        uc.mem_write(GLOBAL_ADDR, build_global(ROOT_ADDR))
        for address, page in pages.items():
            uc.mem_write(address, bytes(page))
        uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []
        # Unicorn caches translated blocks; drop them after every mem_write.
        uc.ctl_flush_tb()

        uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R0, 0x11111111)
        uc.reg_write(arm.UC_ARM_REG_R1, 0x22222222)
        uc.reg_write(arm.UC_ARM_REG_R2, 0x33333333)
        uc.reg_write(arm.UC_ARM_REG_R3, 0x44444444)
        for name, register in CALLEE_SAVED.items():
            uc.reg_write(register, CALLEE_SAVED_START[name])
        for index in range(16, 32):
            uc.reg_write(getattr(arm, f"UC_ARM_REG_S{index}"),
                         0x3F000000 + index)

        try:
            uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except unicorn.UcError as error:
            pc = uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        return {
            "call_log": list(self.call_log),
            "ret": uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: uc.reg_read(register)
                for name, register in CALLEE_SAVED.items()
            },
            "callee_saved_vfp": [
                uc.reg_read(getattr(arm, f"UC_ARM_REG_S{index}"))
                for index in range(16, 32)
            ],
            "writes": [
                write for write in self.writes
                if not STACK_ADDR <= write[0] < STACK_ADDR + STACK_SIZE
            ],
            "global": bytes(uc.mem_read(GLOBAL_ADDR, GLOBAL_SIZE)),
            "pages": {
                address: bytes(uc.mem_read(address, PAGE_SIZE))
                for address in DATA_PAGES
            },
        }


# ---------------------------------------------------------------------------
# Case table
# ---------------------------------------------------------------------------
def make_case(name: str, active: int, model_a: bool = True,
              model_b: bool = True, flags_a: int = 0, flags_b: int = 0,
              visible_a: int = 0x5A, visible_b: int = 0x5A,
              rewrite: str | None = None, **extra) -> dict:
    case = {
        "name": name,
        "active": active,
        "model_a": model_a,
        "model_b": model_b,
        "flags_a": flags_a,
        "flags_b": flags_b,
        "visible_a": visible_a,
        "visible_b": visible_b,
        "rewrite": rewrite,
    }
    case.update(extra)
    return case


def build_cases() -> list[dict]:
    cases = [
        # -- model presence ------------------------------------------------
        make_case("both models null, active 1", 1, False, False),
        make_case("both models null, active 0", 0, False, False),
        make_case("A null, B null flags, active 0", 0, False, True),
        make_case("A present, B null, active 1", 1, True, False),
        make_case("A null, B present, active 1", 1, False, True),

        # -- first half: show / hide / no-op ------------------------------
        make_case("A hidden -> show", 1, True, False, flags_a=2),
        make_case("A visible -> no-op (active)", 1, True, False, flags_a=0),
        make_case("A hidden -> no-op (inactive)", 0, True, False, flags_a=2),
        make_case("A visible -> hide", 0, True, False, flags_a=0),
        make_case("A bit0 only -> no-op (active)", 1, True, False, flags_a=1),
        make_case("A bit0 only -> hide (inactive)", 0, True, False, flags_a=1),

        # -- second half ---------------------------------------------------
        make_case("B hidden -> show", 1, False, True, flags_b=2),
        make_case("B visible -> no-op (active)", 1, False, True, flags_b=0),
        make_case("B visible -> hide", 0, False, True, flags_b=0),
        make_case("B hidden -> no-op (inactive)", 0, False, True, flags_b=2),

        # -- both halves ---------------------------------------------------
        make_case("both hidden -> show both", 1, flags_a=2, flags_b=2),
        make_case("both visible -> hide both", 0, flags_a=0, flags_b=0),
        make_case("both visible -> no-op", 1, flags_a=0, flags_b=0),
        make_case("both hidden -> no-op", 0, flags_a=2, flags_b=2),
        make_case("A hidden/B visible, active -> show A only", 1,
                  flags_a=2, flags_b=0),
        make_case("A visible/B hidden, active -> show B only", 1,
                  flags_a=0, flags_b=2),
        make_case("A visible/B hidden, inactive -> hide A only", 0,
                  flags_a=0, flags_b=2),
        make_case("A hidden/B visible, inactive -> hide B only", 0,
                  flags_a=2, flags_b=0),

        # -- active byte values --------------------------------------------
        make_case("active 2 -> show", 2, flags_a=2, flags_b=2),
        make_case("active 0x80 -> show", 0x80, flags_a=2, flags_b=2),
        make_case("active 0xFF -> show", 0xFF, flags_a=2, flags_b=2),
        make_case("active 0x00 -> hide", 0x00, flags_a=0, flags_b=0),

        # -- flags boundaries ----------------------------------------------
        make_case("flags 0xFFFFFFFD -> hide", 0, flags_a=0xFFFFFFFD,
                  flags_b=0xFFFFFFFD),
        make_case("flags 0xFFFFFFFF -> show", 1, flags_a=0xFFFFFFFF,
                  flags_b=0xFFFFFFFF),
        make_case("flags 0x40000002 -> show", 1, flags_a=0x40000002,
                  flags_b=0x40000002),
        make_case("flags 0x80000000 -> hide", 0, flags_a=0x80000000,
                  flags_b=0x80000000),
        make_case("flags 3 -> show, keeps bit 0", 1, flags_a=3, flags_b=3),
        make_case("flags 1 -> no-op", 1, flags_a=1, flags_b=1),

        # -- initial visible byte values -----------------------------------
        make_case("visible 0x00 -> show writes 1", 1, flags_a=2, flags_b=2,
                  visible_a=0x00, visible_b=0x00),
        make_case("visible 0xFF -> hide writes 0", 0, flags_a=0, flags_b=0,
                  visible_a=0xFF, visible_b=0xFF),
        make_case("visible 0x7F -> show writes 1", 1, flags_a=2, flags_b=2,
                  visible_a=0x7F, visible_b=0x7F),
        make_case("visible 0x01 -> hide writes 0", 0, flags_a=0, flags_b=0,
                  visible_a=0x01, visible_b=0x01),

        # -- helper rewrites between calls ---------------------------------
        make_case("helper clears model B", 1, flags_a=2, flags_b=2,
                  rewrite="clear_model_b"),
        make_case("helper replaces model A", 1, flags_a=2, model_b=False,
                  rewrite="model_a_to_a2"),
        make_case("helper replaces A backend", 1, flags_a=2, model_b=False,
                  rewrite="backend_a_to_a2"),
        make_case("helper replaces work pointer", 1, flags_a=2, model_b=False,
                  rewrite="root_to_root2"),
        make_case("helper replaces work pointer, root2 hides B", 1,
                  flags_a=2, model_b=False, rewrite="root_to_root2",
                  root2_active=0, root2_flags_b=2),
        make_case("helper replaces work pointer, root2 B already visible", 1,
                  flags_a=2, model_b=False, rewrite="root_to_root2",
                  root2_active=1, root2_flags_b=0),
    ]
    return cases


def expected_pages(case: dict) -> dict:
    state = make_state(case)
    initial = build_pages(state)
    _, stores = expected_run(case)
    apply_stores(initial, stores)
    return initial


def expected_global(case: dict) -> bytes:
    _, stores = expected_run(case)
    root_addr = ROOT_ADDR
    for address, size, value in stores:
        if address == GLOBAL_SLOT and size == 4:
            root_addr = value
    return build_global(root_addr)


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------
def check_expected(case: dict, result: dict) -> None:
    log, _ = expected_run(case)
    assert result["call_log"] == log, (
        f"expected call log mismatch on {case['name']}:\n"
        f"  Expected: {log}\n  Actual:   {result['call_log']}"
    )
    assert result["global"] == expected_global(case), (
        f"global slot mismatch on {case['name']}"
    )
    wanted = expected_pages(case)
    for address, page in wanted.items():
        assert result["pages"][address] == bytes(page), (
            f"page 0x{address:08x} mismatch on {case['name']}"
        )


def compare(orig: dict, cand: dict, name: str) -> None:
    for key in ("pc", "sp", "callee_saved", "callee_saved_vfp",
                "call_log", "writes", "global", "pages"):
        assert orig[key] == cand[key], (
            f"{key} mismatch on {name}:\n"
            f"  Orig: {orig[key]!r}\n  Cand: {cand[key]!r}"
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def safe_run(machine: Machine, candidate: bytes, case: dict):
    try:
        return machine.run(candidate, case)
    except RuntimeError as error:
        return ("crash", str(error))


def main() -> None:
    print("Testing script_vm_func_00275ca0 (0x00275ca0)...")
    candidate = compile_candidate()
    print(f"  original: {FUNC_SIZE} B, candidate: {len(candidate)} B")

    cases = build_cases()
    machine = Machine()
    passed = 0
    for case in cases:
        res_orig = machine.run(None, case)
        res_cand = machine.run(candidate, case)
        compare(res_orig, res_cand, case["name"])
        check_expected(case, res_orig)
        check_expected(case, res_cand)
        assert res_orig["pc"] == TRAP_ADDR, (
            f"original did not stop at trap on {case['name']}"
        )
        assert res_cand["pc"] == TRAP_ADDR, (
            f"candidate did not stop at trap on {case['name']}"
        )
        assert res_orig["sp"] == res_cand["sp"] == ENTRY_SP, (
            f"SP mismatch on {case['name']}"
        )
        passed += 1
        print(f"  [PASS] {case['name']}  "
              f"({len(res_orig['call_log'])} helper calls)")

    print("\nNegative controls:")
    mutants = [
        (
            "hidden_flag_mask",
            "constexpr u32 kHiddenFlag = 2;",
            "constexpr u32 kHiddenFlag = 4;",
            1,
        ),
        (
            "shown_volume",
            "constexpr float kShownVolume = 1.0f;",
            "constexpr float kShownVolume = 2.0f;",
            1,
        ),
        (
            "hidden_volume",
            "constexpr float kHiddenVolume = 0.0f;",
            "constexpr float kHiddenVolume = 0.5f;",
            1,
        ),
        (
            "active_polarity",
            "if (active != 0) {",
            "if (active == 0) {",
            2,
        ),
        (
            "set_instead_of_clear",
            "model->flags = flags & ~kHiddenFlag;",
            "model->flags = flags | kHiddenFlag;",
            2,
        ),
        (
            "visible_value",
            "visible_1f6 = 1;",
            "visible_1f6 = 2;",
            2,
        ),
        (
            "visible_offset",
            "constexpr u32 kVisualNodeVisibleOffset = 0x1F6;",
            "constexpr u32 kVisualNodeVisibleOffset = 0x1F7;",
            1,
        ),
        (
            "active_field_offset",
            "u8 pad_000[kActiveOffset];",
            "u8 pad_000[kActiveOffset + 1];",
            1,
        ),
        (
            "backend_field_offset",
            "u8 pad_004[4];",
            "u8 pad_004[5];",
            1,
        ),
        (
            "second_half_helper_slot",
            "script_vm_func_0028c8d0(current_work()->model_10->backend,",
            "script_vm_func_0028c8d0(current_work()->model_0c->backend,",
            2,
        ),
    ]
    for name, old, new, count in mutants:
        mutant = compile_mutant(name, old, new, count)
        detected = False
        for case in cases:
            baseline = machine.run(None, case)
            mutated = safe_run(machine, mutant, case)
            if baseline != mutated:
                detected = True
                break
        assert detected, f"negative control not detected: {name}"
        print(f"  [PASS] mutant detected: {name}")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
