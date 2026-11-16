#!/usr/bin/env python3
"""Differential test for ui_func_001084f0 (0x001084f0) using Unicorn ARM.

Compiles src/engine/leaf_batch34_c.cpp, extracts the ui_func_001084f0 body,
resolves its five direct-call relocations to deterministic stubs at the pinned
addresses, and runs the original span from extracted/exefs/code.bin against the
candidate in separate Unicorn machines with identical fixtures.

The function is the "HDRCL" capture-completion callback (companion to
0x00108300):

    scene = 0x002C0AC8(handle);
    scene->+0xE96 = 0;
    if (0x002C00E8(0) != 0) return 0;
    if (!scene->+0xE8C || !scene->+0xE8D || !scene->+0xFDC ||
         scene->+0xFD8) return 0;
    0x002C3BA8(*(void**)0x0044EA00);
    scene->+0xFDC->+0x14 = scene->+0xFDC->+0x18 = 0x200;
    scene->+0xE94 = (u8)0x002BFCB4(0, scene->+0xFDC);
    mode = 0x002C00E8(0);
    count = scene->+0xE90;
    if (mode == 0 && count > 1) count -= 1;        // clamped at 1
    trim either 0xFDC/0xFE4/0xFE8 (via 0x002BFC88, halving +0x14/+0x18)
    or 0xFDC against itself count times;
    scene->+0xE96 = 1; scene->+0xE95 = 0; return 0;

Compared outputs: return r0, continuation PC, final SP, callee-saved r4-r11,
the ordered call log (helper identity plus every register argument; none of the
helpers takes a stack argument), the multiset of every emulated non-stack write
(address, size, value), and the complete contents of every fixture page: the
low page (used by the null-lookup scene), the 0x0044EA00 GPU-state slot page,
the FrameTex scene page, the three capture-texture pages and the GPU-state
object page.

Coverage: the first 0x002C00E8 gate (zero and non-zero, including signed
extremes), every guard independently and in combination; null and non-null
scene lookups (including a fully populated scene at address 0); signed count
values around every bound; both +0xFE0 strategies with zero, one, two and many
iterations (covering all three chain bodies); the count decrement/clamp; signed
width/height boundaries (proving `asr #1`); all 0x002BFCB4 byte results and
0x002C00E8 signed results; GPU-state slot values 0/0xDEADBEEF/real pointer;
aliasing and null texture pointers; and stubs that mutate the scene/textures
between calls to prove pointers and fields are reloaded exactly where the
original reloads them.

Negative controls mutate the mode gate, the success flag, a helper argument,
the +0xFE0 strategy, the arithmetic shift and the trim argument; each must be
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
SOURCE = ROOT / "src/engine/leaf_batch34_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_001084f0"

FUNC_ADDR = 0x001084F0
FUNC_SIZE = 520

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers the function at 0x1084f0 and every stub
LOW_ADDR = 0x00000000
LOW_SIZE = 0x00010000
GPU_SLOT_ADDR = 0x00440000
GPU_SLOT_SIZE = 0x00010000
SCENE_ADDR = 0x00710000
SCENE_SIZE = 0x00010000
TEX_A_ADDR = 0x00720000
TEX_B_ADDR = 0x00730000
TEX_C_ADDR = 0x00740000
TEX_SIZE = 0x00010000
GPU_ADDR = 0x00750000
GPU_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

LOW_TEX_A = 0x00008000
LOW_TEX_B = 0x00009000
LOW_TEX_C = 0x0000A000

GPU_STATE_SLOT = 0x0044EA00

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_LOOKUP = 0x002C0AC8
STUB_BEGIN_PASS = 0x002C3BA8
STUB_TRIM = 0x002BFCB4
STUB_MODE = 0x002C00E8
STUB_BLIT = 0x002BFC88

STUB_NAMES = {
    STUB_LOOKUP: "ui_func_002c0ac8",
    STUB_BEGIN_PASS: "ui_func_002c3ba8",
    STUB_TRIM: "func_002bfcb4",
    STUB_MODE: "func_002c00e8",
    STUB_BLIT: "func_002bfc88",
}

# None of the five callees is passed an architected stack argument.  The runner
# still reads and logs stack words when an entry is non-zero so a future ABI
# change cannot silently lose an argument.
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

# Per-texture +0x14/+0x18 defaults; captured scenes can reuse the same object.
DEFAULT_TEXTURES = {
    TEX_A_ADDR: (0x1F0, 0x110),
    TEX_B_ADDR: (0x100, 0x80),
    TEX_C_ADDR: (0x40, 0x20),
}
DEFAULT_LOW_TEXTURES = {
    LOW_TEX_A: (0x1F0, 0x110),
    LOW_TEX_B: (0x100, 0x80),
    LOW_TEX_C: (0x40, 0x20),
}


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def _symbol_address(symbol_name: str) -> int | None:
    for address in STUB_NAMES:
        if f"{address:08x}" in symbol_name:
            return address
    return None


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "001084f0" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"ui_func_001084f0 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        target = _symbol_address(rel.symbol_name)
        if rel.relocation_type in (1, 28, 29) and target is not None:
            pc = FUNC_ADDR + rel.offset + 8
            displacement = (target - pc) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
            )
        elif rel.relocation_type == 2:
            raise RuntimeError(
                f"unexpected data relocation {rel.symbol_name} at "
                f"+0x{rel.offset:x}"
            )
        else:
            raise RuntimeError(
                f"unresolved call relocation: {rel.symbol_name} "
                f"(type {rel.relocation_type})"
            )
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch34_c.o"
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
def build_tex(width: int, height: int) -> bytes:
    page = bytearray(TEX_SIZE)
    for offset in range(0, TEX_SIZE, 4):
        struct.pack_into("<I", page, offset, 0xC0DE0000 | (offset >> 2))
    struct.pack_into("<I", page, 0x14, width & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x18, height & 0xFFFFFFFF)
    page[0x10] = 0x11
    page[0x1C] = 0x22
    return bytes(page)


def build_scene(case: dict) -> bytes:
    page = bytearray(SCENE_SIZE)
    for offset in range(0, SCENE_SIZE, 4):
        struct.pack_into("<I", page, offset, 0x5CE00000 | (offset >> 2))

    page[0xE8C] = case.get("e8c", 1) & 0xFF
    page[0xE8D] = case.get("e8d", 1) & 0xFF
    struct.pack_into("<i", page, 0xE90, case.get("e90", 2))
    page[0xE94] = case.get("e94", 0xA4) & 0xFF
    page[0xE95] = case.get("e95", 0x55) & 0xFF
    page[0xE96] = case.get("e96", 0x66) & 0xFF
    page[0xFD8] = case.get("fd8", 0) & 0xFF
    struct.pack_into("<I", page, 0xFDC, case.get("fdc", TEX_A_ADDR))
    page[0xFE0] = case.get("fe0", 0) & 0xFF
    struct.pack_into("<I", page, 0xFE4, case.get("fe4", TEX_B_ADDR))
    struct.pack_into("<I", page, 0xFE8, case.get("fe8", TEX_C_ADDR))
    return bytes(page)


def build_low_page(case: dict) -> bytes:
    if not case.get("low_scene", False):
        return b"\x00" * LOW_SIZE

    page = bytearray(build_scene(case))
    textures = case.get("textures", DEFAULT_LOW_TEXTURES)
    # The low page is 0x10000 bytes and also holds the scene at 0; each fake
    # texture only needs its +0x14/+0x18 words plus a little marker data.
    for address in (LOW_TEX_A, LOW_TEX_B, LOW_TEX_C):
        payload = build_tex(*textures.get(address, (0, 0)))
        page[address:address + 0x200] = payload[:0x200]
    return bytes(page)


def build_gpu_slot(case: dict) -> bytes:
    page = bytearray(GPU_SLOT_SIZE)
    value = case.get("gpu_slot_value", GPU_ADDR)
    struct.pack_into("<I", page, GPU_STATE_SLOT - GPU_SLOT_ADDR, value)
    return bytes(page)


def build_gpu() -> bytes:
    return b"\x77" * GPU_SIZE


def build_texture_pages(case: dict) -> dict[int, bytes]:
    textures = dict(DEFAULT_TEXTURES)
    textures.update(case.get("textures", {}))
    pages = {}
    for address in (TEX_A_ADDR, TEX_B_ADDR, TEX_C_ADDR):
        pages[address] = build_tex(*textures.get(address, (0, 0)))
    return pages


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(LOW_ADDR, LOW_SIZE)
        self.uc.mem_map(GPU_SLOT_ADDR, GPU_SLOT_SIZE)
        self.uc.mem_map(SCENE_ADDR, SCENE_SIZE)
        self.uc.mem_map(TEX_A_ADDR, TEX_SIZE)
        self.uc.mem_map(TEX_B_ADDR, TEX_SIZE)
        self.uc.mem_map(TEX_C_ADDR, TEX_SIZE)
        self.uc.mem_map(GPU_ADDR, GPU_SIZE)
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
        self.case: dict = {}
        self.mode_calls = 0

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        return struct.unpack(f"<{count}I", self.uc.mem_read(sp, 4 * count))

    def _log(self, address: int, *args) -> None:
        self.call_log.append(
            (STUB_NAMES[address], args + self._stack_words(STACK_ARGS[address]))
        )

    def _scene_base(self) -> int:
        return self.case.get("scene_base", SCENE_ADDR)

    def _write_word_if_mapped(self, address: int, value: int) -> None:
        try:
            self.uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))
        except unicorn.UcError:
            pass

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)

        if address == STUB_LOOKUP:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["lookup"])
        elif address == STUB_BEGIN_PASS:
            self._log(address, r0)
        elif address == STUB_TRIM:
            self._log(address, r0, r1)
            override = self.case.get("trim_writes_count")
            if override is not None:
                self._write_word_if_mapped(self._scene_base() + 0xE90, override)
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case.get("trim_ret", 0) & 0xFFFFFFFF
            )
        elif address == STUB_MODE:
            self._log(address, r0)
            returns = self.case.get("mode_rets", (0, 0))
            index = self.mode_calls
            self.mode_calls += 1
            value = returns[index] if index < len(returns) else returns[-1]
            override = self.case.get("mode_writes_count")
            if override is not None:
                self._write_word_if_mapped(self._scene_base() + 0xE90, override)
            uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)
        elif address == STUB_BLIT:
            self._log(address, r0, r1)
            if self.case.get("blit_bump_src", False) and r0 != 0:
                try:
                    width = struct.unpack("<i", uc.mem_read(r0 + 0x14, 4))[0]
                    height = struct.unpack("<i", uc.mem_read(r0 + 0x18, 4))[0]
                    self._write_word_if_mapped(r0 + 0x14, width + 1)
                    self._write_word_if_mapped(r0 + 0x18, height + 2)
                except unicorn.UcError:
                    pass
            if self.case.get("blit_negate_src", False) and r0 != 0:
                # Force odd negative dimensions so `asr #1` and `/ 2` differ.
                try:
                    width = struct.unpack("<i", uc.mem_read(r0 + 0x14, 4))[0]
                    height = struct.unpack("<i", uc.mem_read(r0 + 0x18, 4))[0]
                    self._write_word_if_mapped(r0 + 0x14, -(abs(width) | 1))
                    self._write_word_if_mapped(r0 + 0x18, -(abs(height) | 1))
                except unicorn.UcError:
                    pass
            if self.case.get("blit_swap_aux", False):
                base = self._scene_base()
                try:
                    fe4 = struct.unpack("<I", uc.mem_read(base + 0xFE4, 4))[0]
                    fe8 = struct.unpack("<I", uc.mem_read(base + 0xFE8, 4))[0]
                    self._write_word_if_mapped(base + 0xFE4, fe8)
                    self._write_word_if_mapped(base + 0xFE8, fe4)
                except unicorn.UcError:
                    pass
            if self.case.get("blit_bump_count", False):
                base = self._scene_base()
                try:
                    count = struct.unpack("<i", uc.mem_read(base + 0xE90, 4))[0]
                    self._write_word_if_mapped(base + 0xE90, count + 1)
                except unicorn.UcError:
                    pass
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def _fixture_pages(self, case: dict) -> list[tuple[int, int, bytes]]:
        pages = [
            (LOW_ADDR, LOW_SIZE, build_low_page(case)),
            (GPU_SLOT_ADDR, GPU_SLOT_SIZE, build_gpu_slot(case)),
            (SCENE_ADDR, SCENE_SIZE, build_scene(case)),
            (GPU_ADDR, GPU_SIZE, build_gpu()),
        ]
        for address, payload in build_texture_pages(case).items():
            pages.append((address, TEX_SIZE, payload))
        return pages

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case
        self.mode_calls = 0

        self.uc.mem_write(FUNC_ADDR, code)
        pages = self._fixture_pages(case)
        for address, size, payload in pages:
            self.uc.mem_write(address, payload)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, case.get("handle", 0x0050006A))
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

        memory = {
            f"0x{address:08x}": bytes(self.uc.mem_read(address, size))
            for address, size, _payload in pages
        }

        # Writes outside the private stack must land in one of the fixture pages.
        # Register-save slots below the entry SP are scratch and differ by frame
        # layout, so only non-stack writes enter the compared write multiset.
        unexpected_writes = []
        observable_writes = []
        for address, size, value in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_fixture = any(
                base <= address < base + page_size
                for base, page_size, _payload in pages
            )
            if not in_stack:
                observable_writes.append((address, size, value))
            if not in_stack and not in_fixture:
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "writes": sorted(observable_writes),
            "memory": memory,
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
    if orig["writes"] != cand["writes"]:
        problems.append(
            "write set:\n    orig="
            + repr(orig["writes"])
            + "\n    cand="
            + repr(cand["writes"])
        )
    for key, value in orig["memory"].items():
        if value != cand["memory"][key]:
            first = next(
                index for index, (a, b) in enumerate(zip(value, cand["memory"][key]))
                if a != b
            )
            problems.append(
                f"memory {key} differs first at +0x{first:x}: "
                f"orig=0x{value[first]:02x} cand=0x{cand['memory'][key][first]:02x}"
            )
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "handle": 0x0050006A,
        "lookup": SCENE_ADDR,
        "scene_base": SCENE_ADDR,
        "gpu_slot_value": GPU_ADDR,
        "e8c": 1,
        "e8d": 1,
        "e90": 2,
        "e94": 0xA4,
        "e95": 0x55,
        "e96": 0x66,
        "fd8": 0,
        "fdc": TEX_A_ADDR,
        "fe0": 0,
        "fe4": TEX_B_ADDR,
        "fe8": TEX_C_ADDR,
        "textures": {},
        "trim_ret": 0,
        "mode_rets": (0, 0),
    }
    case.update(overrides)
    return case


def low_scene_case(name: str, **overrides) -> dict:
    case = base_case(
        name,
        lookup=0,
        scene_base=0,
        low_scene=True,
        fdc=LOW_TEX_A,
        fe4=LOW_TEX_B,
        fe8=LOW_TEX_C,
        textures=dict(DEFAULT_LOW_TEXTURES),
    )
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- lookup result: null with an empty low page, null with a complete
    #     scene at address 0, and a normal scene pointer.
    cases.append(base_case("lookup null, low page zero", lookup=0, scene_base=0))
    for count in (-2, -1, 0, 1, 2, 3, 4):
        for fe0 in (0, 1):
            cases.append(low_scene_case(
                f"lookup null, scene at 0, count {count}, fe0 {fe0}",
                e90=count, fe0=fe0,
            ))

    # --- first 0x002C00E8 call gates the whole callback.
    for mode_first in (0, 1, 0x7F, 0xFF, -1, 0x7FFFFFFF, -0x80000000):
        cases.append(base_case(
            f"first mode 0x{mode_first & 0xFFFFFFFF:08x}", mode_rets=(mode_first, 0)
        ))
    cases.append(base_case(
        "first mode nonzero with all other gates open",
        mode_rets=(1, 0), e8c=0xFF, e8d=0xFF, e90=4, fe0=1,
    ))

    # --- each guard independently and combined.
    for name, override in (
        ("e8c zero", {"e8c": 0}),
        ("e8c 0x80", {"e8c": 0x80}),
        ("e8c 0xFF", {"e8c": 0xFF}),
        ("e8d zero", {"e8d": 0}),
        ("e8d 0x80", {"e8d": 0x80}),
        ("e8d 0xFF", {"e8d": 0xFF}),
        ("fd8 one", {"fd8": 1}),
        ("fd8 0x80", {"fd8": 0x80}),
        ("fd8 0xFF", {"fd8": 0xFF}),
        ("fdc null", {"fdc": 0}),
        ("first two gates zero", {"e8c": 0, "e8d": 0}),
        ("all gates zero", {"e8c": 0, "e8d": 0, "fd8": 1, "fdc": 0}),
    ):
        cases.append(base_case(name, **override))

    # --- both trim strategies across all loop shapes.
    for fe0 in (0, 1):
        for count in (-3, -2, -1, 0, 1, 2, 3, 4, 7):
            cases.append(base_case(
                f"fe0 {fe0} count {count}", fe0=fe0, e90=count
            ))
    # Second 0x002C00E8 result controls the decrement; signed extremes.
    for count in (0, 1, 2, 3, 4):
        for mode_second in (0, 1, 0xFF, -1, 0x7FFFFFFF, -0x80000000):
            cases.append(base_case(
                f"second mode 0x{mode_second & 0xFFFFFFFF:08x} count {count}",
                e90=count, mode_rets=(0, mode_second),
            ))
    # A positive 0x7FFFFFFF count would require that many loop iterations in
    # both implementations; only the negative signed boundary is executable.
    # It distinguishes the signed `blt/ble` bounds from unsigned ones.
    cases.append(base_case("count boundary 0x80000000", e90=-0x80000000))
    cases.append(base_case("count boundary 0x80000000 fe0 1",
                           e90=-0x80000000, fe0=1))

    # --- signed width/height boundaries; the original uses `asr #1`.
    for width, height in (
        (0, 0), (1, 1), (-1, -1), (-3, 5), (3, -5),
        (0x7FFFFFFF, 0x80000000), (0x80000000, 0x7FFFFFFF),
        (0xFFFFFFFE, 0xFFFFFFFD),
    ):
        for fe0 in (0, 1):
            cases.append(base_case(
                f"dims {width}/{height} fe0 {fe0}",
                fe0=fe0, e90=3,
                textures={TEX_A_ADDR: (width, height),
                          TEX_B_ADDR: (width, height),
                          TEX_C_ADDR: (width, height)},
            ))

    # --- 0x002BFCB4 byte result is stored at +0xE94.
    for trim_ret in (0, 1, 0x7F, 0x80, 0xFF, 0x12345678, -1):
        cases.append(base_case(
            f"trim result 0x{trim_ret & 0xFFFFFFFF:08x}", trim_ret=trim_ret
        ))

    # --- helper order: the count is loaded after the second 0x002C00E8 and
    #     before the loop, and the +0xE94 store precedes that call.
    for override in (0, 1, 3, 5, -1):
        cases.append(base_case(
            f"mode helper rewrites count to {override}",
            mode_writes_count=override, mode_rets=(0, 0), e90=2,
        ))
        cases.append(base_case(
            f"trim helper rewrites count to {override}",
            trim_writes_count=override, mode_rets=(0, 0), e90=2,
        ))

    # --- stubs mutate textures/scene between calls: pointers and fields must
    #     be reloaded after every helper, exactly like the original.
    for fe0 in (0, 1):
        cases.append(base_case(
            f"blit bumps source fields fe0 {fe0}", fe0=fe0, e90=4,
            blit_bump_src=True,
        ))
        cases.append(base_case(
            f"blit swaps aux pointers fe0 {fe0}", fe0=fe0, e90=4,
            blit_swap_aux=True,
        ))
        cases.append(base_case(
            f"blit bumps scene count fe0 {fe0}", fe0=fe0, e90=4,
            blit_bump_count=True,
        ))
        cases.append(base_case(
            f"blit bumps, swaps and bumps count fe0 {fe0}", fe0=fe0, e90=5,
            blit_bump_src=True, blit_swap_aux=True, blit_bump_count=True,
        ))
        # The real callers only ever feed 0x200 down the chain, so the source
        # stub must inject an odd negative width/height to exercise `asr #1`
        # (arithmetic, rounds towards -inf) instead of `/ 2`.
        for count in (2, 3, 4, 7):
            cases.append(base_case(
                f"blit negates source fe0 {fe0} count {count}",
                fe0=fe0, e90=count, blit_negate_src=True,
            ))

    # --- texture aliasing and null auxiliary pointers.
    for name, fdc, fe4, fe8 in (
        ("fe4 aliases fdc", TEX_A_ADDR, TEX_A_ADDR, TEX_C_ADDR),
        ("fe8 aliases fdc", TEX_A_ADDR, TEX_B_ADDR, TEX_A_ADDR),
        ("fe4 aliases fe8", TEX_A_ADDR, TEX_B_ADDR, TEX_B_ADDR),
        ("fe4 null", TEX_A_ADDR, 0, TEX_C_ADDR),
        ("fe8 null", TEX_A_ADDR, TEX_B_ADDR, 0),
        ("both aux null", TEX_A_ADDR, 0, 0),
    ):
        cases.append(base_case(name, fdc=fdc, fe4=fe4, fe8=fe8,
                               fe0=1, e90=3))
        cases.append(base_case(name + ", fe0 0", fdc=fdc, fe4=fe4, fe8=fe8,
                               fe0=0, e90=3))

    # --- initial flag bytes are overwritten on every path.
    for e95 in (0, 0xFF):
        for e96 in (0, 0xFF):
            cases.append(base_case(
                f"flags e95 0x{e95:02x} e96 0x{e96:02x}", e95=e95, e96=e96
            ))

    # --- GPU-state slot values: null, opaque and the real object pointer.
    for value in (0, 0xDEADBEEF, GPU_ADDR):
        cases.append(base_case(
            f"gpu slot 0x{value:08x}", gpu_slot_value=value
        ))

    # --- packed handle is forwarded untouched to 0x002C0AC8.
    for handle in (0, 0x000FFFFF, 0xFFFFFFFF, 0x7FFFFFFF, 0x80000000):
        cases.append(base_case(f"handle 0x{handle:08x}", handle=handle))

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = Runner().run(orig_code, case)
        cand = Runner().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  "
              f"({len(orig['call_log'])} calls, {len(orig['writes'])} writes)")
    return passed


def main() -> None:
    print("Testing ui_func_001084f0 (0x001084f0)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B.")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("mode_gate", "if (CaptureMode(0) != 0) {",
         "if (CaptureMode(0) == 0) {"),
        ("success_flag", "scene->field_e96 = 1;",
         "scene->field_e96 = 2;"),
        ("second_mode_argument",
         "const s32 mode = CaptureMode(0);             // 0x0010858C..0x00108594",
         "const s32 mode = CaptureMode(1);             // 0x0010858C..0x00108594"),
        ("fe0_strategy",
         "if (scene->field_fe0 != 0) {                 // 0x001085B4..0x001085BC",
         "if (scene->field_fe0 == 0) {                 // 0x001085B4..0x001085BC"),
        ("half_shift",
         "// `asr #1` on a signed 32-bit word.\n"
         "inline s32 Half(s32 value) noexcept {\n"
         "    return value >> 1;\n"
         "}\n"
         "\n"
         "}  // namespace ui_1084f0",
         "// `asr #1` on a signed 32-bit word.\n"
         "inline s32 Half(s32 value) noexcept {\n"
         "    return value / 2;\n"
         "}\n"
         "\n"
         "}  // namespace ui_1084f0"),
        ("trim_argument",
         "static_cast<u8>(TrimCapture(0, scene->field_fdc));  "
         "// 0x0010857C..0x00108588",
         "static_cast<u8>(TrimCapture(1, scene->field_fdc));  "
         "// 0x0010857C..0x00108588"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, case)
            bad = Runner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
