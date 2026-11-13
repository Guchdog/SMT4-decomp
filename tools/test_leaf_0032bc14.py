#!/usr/bin/env python3
"""Differential test for engine_func_0032bc14 (0x0032bc14) using Unicorn ARM.

The routine is the engine wait/step loop over the two global objects at
0x004C3AF8 and 0x004C3B20:

  * when 0x0034F878(0x004C3AF8) is nonzero, run the four 0x0011Bxxx helpers;
  * when the context probe 0x00351028(0x004C3B20) returns zero, compare the
    64-bit time returned by 0x00351208 with the baseline at 0x0044D020+0x08
    (signed) and call one of the 0x00350EA8 / 0x0034FE60 families;
  * when 0x00350A64(0x004C3B20) is nonzero, compare the next 0x00351208 time
    with six times the baseline and run the overdue or the normal transition;
  * latch the byte at 0x0044D020, sleep through 0x00351698 and repeat until
    the overdue flag, the latched status flag, or state 1 / state 7 ends it.

Every direct callee is replaced with a deterministic stub at its original
address.  Each case runs the pinned original and the compiled candidate with an
identical fixture and compares:
  - the ordered call log (arguments and returned values),
  - return value, continuation PC and SP,
  - callee-saved integer and VFP registers,
  - the 64-bit status block, the task object, the context object and the stack
    canary.
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
FUNC_ADDR = 0x0032BC14
FUNC_SIZE = 404
TU_PATH = ROOT / "src/engine/leaf_batch41_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_0032bc14"

# ---------------------------------------------------------------------------
# Emulated address space
# ---------------------------------------------------------------------------
IMAGE_ADDR = 0x00100000
IMAGE_SIZE = 0x00500000              # 0x00100000..0x00600000 (pinned image)
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

STATUS_ADDR = 0x0044D020             # literal pool: status byte + u64 baseline
STATUS_BASELINE = STATUS_ADDR + 0x08
STATUS_WATCH = 0x40
TASK_ADDR = 0x004C3AF8               # literal pool: first-stage object
TASK_WATCH = 0x100
CONTEXT_ADDR = 0x004C3B20            # literal pool: engine task context
CONTEXT_WATCH = 0x200
OFF_STATE = 0x00C

# Direct-call stubs (original branch targets).
STUB_34F878 = 0x0034F878
STUB_11B558 = 0x0011B558
STUB_11B5E8 = 0x0011B5E8
STUB_11B6A8 = 0x0011B6A8
STUB_11B590 = 0x0011B590
STUB_351028 = 0x00351028
STUB_351208 = 0x00351208
STUB_34FE60 = 0x0034FE60
STUB_350EA8 = 0x00350EA8
STUB_350024 = 0x00350024
STUB_350A64 = 0x00350A64
STUB_34F808 = 0x0034F808
STUB_34FC14 = 0x0034FC14
STUB_34FDD8 = 0x0034FDD8
STUB_351040 = 0x00351040
STUB_34F840 = 0x0034F840
STUB_351698 = 0x00351698
STUB_350530 = 0x00350530

STUB_BY_SYMBOL = {
    "func_0034f878": STUB_34F878,
    "func_0011b558": STUB_11B558,
    "engine_func_0011b5e8": STUB_11B5E8,
    "engine_func_0011b6a8": STUB_11B6A8,
    "func_0011b590": STUB_11B590,
    "func_00351028": STUB_351028,
    "func_00351208": STUB_351208,
    "func_0034fe60": STUB_34FE60,
    "func_00350ea8": STUB_350EA8,
    "func_00350024": STUB_350024,
    "func_00350a64": STUB_350A64,
    "func_0034f808": STUB_34F808,
    "engine_func_0034fc14": STUB_34FC14,
    "engine_func_0034fdd8": STUB_34FDD8,
    "camp_func_00351040": STUB_351040,
    "func_0034f840": STUB_34F840,
    "nn_sdk_func_00351698": STUB_351698,
    "func_00350530": STUB_350530,
}

BX_LR = 0xE12FFF1E
MASK64 = (1 << 64) - 1
MAX_ITERATIONS = 32


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def u32(value):
    return value & 0xFFFFFFFF


def u64(value):
    return value & MASK64


def s64(value):
    value &= MASK64
    return value - (1 << 64) if value & (1 << 63) else value


def signed_less(a, b):
    return s64(a) < s64(b)


def high_word_is_negative(value):
    return bool((value >> 32) & 0x80000000)


def get_orig_bytes():
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def sign_extend_24(value):
    return value - 0x1000000 if value & 0x800000 else value


def compile_variant(src_file, obj_file):
    result = compile_tu_armv6k(Path(src_file), Path(obj_file), ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed for {src_file}: {result.stderr}")

    funcs = extract_elf_functions_detailed(Path(obj_file))
    entry = funcs.get("engine_func_0032bc14")
    if entry is None:
        raise RuntimeError(
            "engine_func_0032bc14 not found in object: "
            + ", ".join(sorted(funcs))
        )

    raw, relocs = entry
    code = bytearray(raw)
    for rel in relocs:
        if rel.relocation_type not in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            raise RuntimeError(f"unsupported relocation: {rel}")
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
        patched = struct.unpack_from("<I", code, rel.offset)[0]
        landed = place + 8 + (sign_extend_24(patched & 0x00FFFFFF) << 2)
        if landed != target:
            raise RuntimeError(
                f"patched call 0x{place:08x} lands on 0x{landed:08x}, "
                f"expected 0x{target:08x}"
            )
    return bytes(code)


def compile_candidate():
    return compile_variant(TU_PATH, OUT_DIR / "leaf_batch41_c.o")


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
        self.uc.mem_map(IMAGE_ADDR, IMAGE_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        self.original_image = ORIG_BIN.read_bytes()
        self.uc.mem_write(IMAGE_ADDR, self.original_image)
        self.orig_code = get_orig_bytes()

        self.call_log = []
        self.case = None
        self.sleeps = 0
        self.now_index = 0
        self._install_stubs()

    # -- stub installation ------------------------------------------------
    def _install_stubs(self):
        bx_lr = struct.pack("<I", BX_LR)
        direct = [
            (STUB_34F878, self._on_34f878),
            (STUB_11B558, self._on_void, "func_0011b558"),
            (STUB_11B5E8, self._on_11b5e8),
            (STUB_11B6A8, self._on_11b6a8),
            (STUB_11B590, self._on_void, "func_0011b590"),
            (STUB_351028, self._on_351028),
            (STUB_351208, self._on_351208),
            (STUB_34FE60, self._on_void, "func_0034fe60"),
            (STUB_350EA8, self._on_350ea8),
            (STUB_350024, self._on_350024),
            (STUB_350A64, self._on_350a64),
            (STUB_34F808, self._on_void, "func_0034f808"),
            (STUB_34FC14, self._on_34fc14),
            (STUB_34FDD8, self._on_void, "engine_func_0034fdd8"),
            (STUB_351040, self._on_void, "camp_func_00351040"),
            (STUB_34F840, self._on_void, "func_0034f840"),
            (STUB_351698, self._on_351698),
            (STUB_350530, self._on_void, "func_00350530"),
        ]
        for address, hook, *extra in direct:
            self.uc.mem_write(address, bx_lr)
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, hook, extra[0] if extra else None,
                begin=address, end=address,
            )

    # -- stub bodies ------------------------------------------------------
    def _write_u32(self, address, value):
        self.uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))

    def _write_u64(self, address, value):
        self.uc.mem_write(address, struct.pack("<Q", value & MASK64))

    def _read_u32(self, address):
        return struct.unpack("<I", self.uc.mem_read(address, 4))[0]

    def _arg(self, uc):
        return uc.reg_read(arm.UC_ARM_REG_R0)

    def _on_void(self, uc, address, size, name):
        self.call_log.append((name, self._arg(uc)))

    def _on_34f878(self, uc, address, size, user_data):
        arg = self._arg(uc)
        result = self.case["start_result"]
        self.call_log.append(("func_0034f878", arg, result))
        uc.reg_write(arm.UC_ARM_REG_R0, u32(result))

    def _on_11b5e8(self, uc, address, size, user_data):
        arg = self._arg(uc)
        self.call_log.append(("engine_func_0011b5e8", arg, 0))
        uc.reg_write(arm.UC_ARM_REG_R0, 0)

    def _on_11b6a8(self, uc, address, size, user_data):
        arg = self._arg(uc)
        self.call_log.append(("engine_func_0011b6a8", arg, 0))
        uc.reg_write(arm.UC_ARM_REG_R0, 0)

    def _on_351028(self, uc, address, size, user_data):
        arg = self._arg(uc)
        result = self.case["probe_result"]
        self.call_log.append(("func_00351028", arg, result))
        uc.reg_write(arm.UC_ARM_REG_R0, u32(result))

    def _on_351208(self, uc, address, size, user_data):
        arg = self._arg(uc)
        values = self.case["now_values"]
        value = values[min(self.now_index, len(values) - 1)]
        self.now_index += 1
        self.call_log.append(("func_00351208", arg, u64(value)))
        uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)
        uc.reg_write(arm.UC_ARM_REG_R1, (value >> 32) & 0xFFFFFFFF)

    def _on_350ea8(self, uc, address, size, user_data):
        arg = self._arg(uc)
        result = self.case["late_result"]
        self.call_log.append(("func_00350ea8", arg, result))
        uc.reg_write(arm.UC_ARM_REG_R0, u32(result))

    def _on_350024(self, uc, address, size, user_data):
        arg = self._arg(uc)
        self.call_log.append(("func_00350024", arg, 0))
        uc.reg_write(arm.UC_ARM_REG_R0, 0)

    def _on_350a64(self, uc, address, size, user_data):
        arg = self._arg(uc)
        result = self.case["advance_result"]
        self.call_log.append(("func_00350a64", arg, result))
        uc.reg_write(arm.UC_ARM_REG_R0, u32(result))

    def _on_34fc14(self, uc, address, size, user_data):
        arg = self._arg(uc)
        self.call_log.append(("engine_func_0034fc14", arg, 0))
        uc.reg_write(arm.UC_ARM_REG_R0, 0)

    def _on_351698(self, uc, address, size, user_data):
        arg = self._arg(uc)
        self.call_log.append(("nn_sdk_func_00351698", arg))
        self.sleeps += 1
        if self.sleeps > MAX_ITERATIONS:
            raise RuntimeError("0x00351698 called too often (wait loop stuck)")
        index = self.sleeps - 1
        state_script = self.case["state_after_sleep"]
        if state_script:
            self._write_u32(
                CONTEXT_ADDR + OFF_STATE,
                state_script[min(index, len(state_script) - 1)],
            )
        status_script = self.case["status_after_sleep"]
        if status_script:
            self.uc.mem_write(
                STATUS_ADDR,
                bytes([status_script[min(index, len(status_script) - 1)]]),
            )

    # -- fixtures ---------------------------------------------------------
    def _reset_fixtures(self, case):
        self.case = case
        self.sleeps = 0
        self.now_index = 0
        self.call_log = []

        status_block = bytearray(b"\xA5" * STATUS_WATCH)
        status_block[0] = case["status_initial"]
        struct.pack_into("<Q", status_block, 8, case["baseline"] & MASK64)
        self.uc.mem_write(STATUS_ADDR, bytes(status_block))

        self.uc.mem_write(TASK_ADDR, b"\xA5" * TASK_WATCH)
        self.uc.mem_write(CONTEXT_ADDR, b"\xA5" * CONTEXT_WATCH)
        self._write_u32(CONTEXT_ADDR + OFF_STATE, case["state"])

    def run(self, candidate, case):
        """candidate = None runs the pinned original."""
        uc = self.uc
        self._reset_fixtures(case)
        if candidate is None:
            uc.mem_write(FUNC_ADDR, self.orig_code)
        else:
            uc.mem_write(FUNC_ADDR, candidate)
        # Unicorn keeps translated blocks across mem_write; drop them.
        uc.ctl_flush_tb()

        sp = STACK_ADDR + STACK_SIZE - 0x100
        uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        uc.mem_write(sp, struct.pack("<I", 0x5A5A5A5A))
        uc.reg_write(arm.UC_ARM_REG_SP, sp)
        uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        # The original never reads r0; the only caller passes a frame counter.
        uc.reg_write(arm.UC_ARM_REG_R0, 0xDEADBEEF)
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
            "status": bytes(uc.mem_read(STATUS_ADDR, STATUS_WATCH)),
            "task": bytes(uc.mem_read(TASK_ADDR, TASK_WATCH)),
            "context": bytes(uc.mem_read(CONTEXT_ADDR, CONTEXT_WATCH)),
            "stack_canary": bytes(uc.mem_read(sp, 4)),
        }


# ---------------------------------------------------------------------------
# Independent expected model
# ---------------------------------------------------------------------------
def expected_case(case):
    """Return (call_log, return_value, final_state)."""
    log = []

    status = u32(case["status_initial"])
    state = u32(case["state"])
    baseline = u64(case["baseline"])
    now_values = [u64(v) for v in case["now_values"]]
    now_index = 0
    state_script = case["state_after_sleep"]
    status_script = case["status_after_sleep"]

    status_seen = False   # r4
    overdue = False       # r5
    iterations = 0

    def next_now():
        nonlocal now_index
        value = now_values[min(now_index, len(now_values) - 1)]
        now_index += 1
        return value

    for iteration in range(MAX_ITERATIONS):
        # 0x0034F878 and the four start helpers.
        start_result = case["start_result"]
        log.append(("func_0034f878", TASK_ADDR, start_result))
        if start_result != 0:
            log.append(("func_0011b558", TASK_ADDR))
            log.append(("engine_func_0011b5e8", CONTEXT_ADDR, 0))
            log.append(("engine_func_0011b6a8", CONTEXT_ADDR, 0))
            log.append(("func_0011b590", TASK_ADDR))

        # 0x00351028 clock-suspended probe and first comparison.
        probe = case["probe_result"]
        log.append(("func_00351028", CONTEXT_ADDR, probe))
        if probe == 0:
            now = next_now()
            log.append(("func_00351208", CONTEXT_ADDR, now))
            if signed_less(now, baseline):
                late = case["late_result"]
                log.append(("func_00350ea8", CONTEXT_ADDR, late))
                if late != 0:
                    log.append(("func_00350024", CONTEXT_ADDR, 0))
            else:
                log.append(("func_0034fe60", CONTEXT_ADDR))

        # 0x00350A64 overdue probe and second comparison.
        advance = case["advance_result"]
        log.append(("func_00350a64", CONTEXT_ADDR, advance))
        if advance != 0:
            now = next_now()
            log.append(("func_00351208", CONTEXT_ADDR, now))
            scaled = u64(baseline * 6)
            if signed_less(now, scaled):
                if not high_word_is_negative(now):
                    overdue = True
                    log.append(("camp_func_00351040", CONTEXT_ADDR))
                    log.append(("func_0034f840", TASK_ADDR))
            else:
                log.append(("func_0034f808", TASK_ADDR))
                log.append(("engine_func_0034fc14", CONTEXT_ADDR, 0))
                log.append(("engine_func_0034fdd8", CONTEXT_ADDR))

        # 0x0032BD44: latch the status byte, then sleep.
        if status != 0:
            status_seen = True
        log.append(("nn_sdk_func_00351698", CONTEXT_ADDR))

        if state_script:
            state = u32(state_script[min(iteration, len(state_script) - 1)])
        if status_script:
            status = u32(
                status_script[min(iteration, len(status_script) - 1)]
            )

        iterations += 1
        if overdue or status_seen or state == 7 or state == 1:
            break
    else:
        raise AssertionError("expected model wait loop did not terminate")

    if overdue:
        return log, 1, state
    log.append(("func_00350530", CONTEXT_ADDR))
    return log, 0, state


def make_case(name, **kwargs):
    case = {
        "name": name,
        "state": 1,
        "status_initial": 0,
        "baseline": 0,
        "start_result": 0,
        "probe_result": 1,
        "late_result": 0,
        "advance_result": 0,
        "now_values": (0,),
        "state_after_sleep": (),
        "status_after_sleep": (),
    }
    case.update(kwargs)
    return case


def build_cases():
    return [
        # -- loop termination and flag persistence -------------------------
        make_case("state 1 exits immediately", state=1),
        make_case("state 7 exits immediately", state=7),
        make_case("state 0, one sleep, then state 1", state=0,
                  state_after_sleep=(1,)),
        make_case("state 0, two sleeps, then state 7", state=0,
                  state_after_sleep=(0, 7)),
        make_case("state 0, three sleeps, then state 1", state=0,
                  state_after_sleep=(0, 0, 1)),
        make_case("state 0xffffffff, one sleep, then state 1", state=0xFFFFFFFF,
                  state_after_sleep=(1,)),
        make_case("state 0x80000000, one sleep, then state 7", state=0x80000000,
                  state_after_sleep=(7,)),
        make_case("status byte nonzero on the first iteration",
                  state=0, status_initial=1, state_after_sleep=(0, 1)),
        make_case("status byte 0x80 set by the sleep",
                  state=0, status_initial=0, state_after_sleep=(0, 0, 1),
                  status_after_sleep=(0x80,)),
        make_case("status byte latched on iteration 2",
                  state=0, status_initial=0, state_after_sleep=(0, 0, 1),
                  status_after_sleep=(0, 0x01)),

        # -- 0x0034F878 start path ----------------------------------------
        make_case("start path repeats over two iterations", state=0,
                  start_result=1, state_after_sleep=(0, 1)),
        make_case("start result negative (0xffffffff)", state=0,
                  start_result=0xFFFFFFFF, state_after_sleep=(1,)),
        make_case("start result zero takes no start helpers", state=0,
                  start_result=0, state_after_sleep=(1,)),

        # -- 0x00351028 / 0x00351208 first comparison ----------------------
        make_case("probe nonzero skips the clock block", state=1,
                  probe_result=1, now_values=(0,)),
        make_case("probe negative is nonzero", state=1,
                  probe_result=0xFFFFFFFF),
        make_case("now below baseline, late predicate clear", state=1,
                  probe_result=0, baseline=7, now_values=(5,),
                  late_result=0),
        make_case("now below baseline, late predicate set", state=1,
                  probe_result=0, baseline=7, now_values=(5,),
                  late_result=1),
        make_case("now equal to baseline", state=1,
                  probe_result=0, baseline=7, now_values=(7,)),
        make_case("now above baseline", state=1,
                  probe_result=0, baseline=7, now_values=(8,)),
        make_case("signed boundary: min < max baseline", state=1,
                  probe_result=0, baseline=0x7FFFFFFFFFFFFFFF,
                  now_values=(0x8000000000000000,), late_result=1),
        make_case("signed boundary: max >= min baseline", state=1,
                  probe_result=0, baseline=0x8000000000000000,
                  now_values=(0x7FFFFFFFFFFFFFFF,)),

        # -- 0x00350A64 / second comparison --------------------------------
        make_case("advance zero skips the overdue block", state=1,
                  probe_result=1, advance_result=0),
        make_case("overdue: now 5 below 6*baseline 6", state=1,
                  probe_result=1, advance_result=1, baseline=1,
                  now_values=(5,)),
        make_case("overdue skipped: negative high word", state=1,
                  probe_result=1, advance_result=1, baseline=1,
                  now_values=(0x8000000000000000,)),
        make_case("second comparison equal goes to the normal path", state=1,
                  probe_result=1, advance_result=1, baseline=1,
                  now_values=(6,)),
        make_case("second comparison above goes to the normal path", state=1,
                  probe_result=1, advance_result=1, baseline=1,
                  now_values=(7,)),
        make_case("six-times multiply wraps to zero", state=1,
                  probe_result=1, advance_result=1,
                  baseline=0x8000000000000000, now_values=(0,)),
        make_case("six-times multiply wraps negative", state=1,
                  probe_result=1, advance_result=1,
                  baseline=0xFFFFFFFFFFFFFFFF, now_values=(0xFFFFFFFFFFFFFFF9,)),
        make_case("overdue with non-negative high word 0x7fffffff", state=1,
                  probe_result=1, advance_result=1,
                  baseline=0x15555556, now_values=(0x80000000,)),
        make_case("overdue exactly at scale boundary", state=1,
                  probe_result=1, advance_result=1, baseline=2,
                  now_values=(11,)),

        # -- both blocks in one iteration ----------------------------------
        make_case("both comparisons: 0 then 5 against baseline 1",
                  state=1, probe_result=0, advance_result=1, baseline=1,
                  now_values=(0, 5), late_result=1),
        make_case("both comparisons: 1 then 6 against baseline 1",
                  state=1, probe_result=0, advance_result=1, baseline=1,
                  now_values=(1, 6)),
        make_case("both comparisons with negative now", state=1,
                  probe_result=0, advance_result=1,
                  baseline=0x7FFFFFFFFFFFFFFF,
                  now_values=(0x8000000000000000, 0xFFFFFFFFFFFFFFFF),
                  late_result=1),

        # -- return value and r5 / r4 interaction --------------------------
        make_case("overdue return 1 even if state is 1", state=1,
                  probe_result=1, advance_result=1, baseline=1,
                  now_values=(5,)),
        make_case("overdue return 1 while status stays clear", state=0,
                  probe_result=1, advance_result=1, baseline=1,
                  now_values=(5,), status_initial=0),
        make_case("status flag alone returns 0 and calls 0x00350530",
                  state=0, status_initial=0x5A, probe_result=1,
                  advance_result=0),
    ]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def check_expectations(case, result):
    log, ret, state = expected_case(case)
    assert result["call_log"] == log, (
        f"expected call log mismatch on {case['name']}:\n"
        f"  Expected: {log}\n  Actual:   {result['call_log']}"
    )
    assert result["r0"] == ret, (
        f"return mismatch on {case['name']}: "
        f"0x{result['r0']:08x} != 0x{ret:08x}"
    )
    actual_state = struct.unpack_from("<I", result["context"], OFF_STATE)[0]
    assert actual_state == state, (
        f"state mismatch on {case['name']}: "
        f"0x{actual_state:08x} != 0x{state:08x}"
    )


def main():
    print("Testing engine_func_0032bc14 (0x0032bc14)...")
    cand = compile_candidate()
    print(f"  original: {FUNC_SIZE} B, candidate: {len(cand)} B")

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
        assert res_orig["status"] == res_cand["status"], (
            f"status block memory mismatch on {case['name']}"
        )
        assert res_orig["task"] == res_cand["task"], (
            f"task object memory mismatch on {case['name']}"
        )
        assert res_orig["context"] == res_cand["context"], (
            f"context object memory mismatch on {case['name']}"
        )
        assert res_orig["stack_canary"] == res_cand["stack_canary"], (
            f"stack canary mismatch on {case['name']}"
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
            "baseline_scale",
            "constexpr u32 kBaselineScale = 6;",
            "constexpr u32 kBaselineScale = 5;",
        ),
        (
            "first_compare_unsigned",
            "static_cast<s64>(now) < static_cast<s64>(baseline)",
            "now < baseline",
        ),
        (
            "inner_high_word_inverted",
            "if (static_cast<s32>(static_cast<u32>(now >> 32)) >= 0) {",
            "if (static_cast<s32>(static_cast<u32>(now >> 32)) < 0) {",
        ),
        (
            "state_7_wrong",
            "state == 7 || state == 1",
            "state == 6 || state == 1",
        ),
        (
            "return_uses_status",
            "if (overdue) {",
            "if (status_seen) {",
        ),
        (
            "status_test_inverted",
            "if (*status_byte != 0) {",
            "if (*status_byte == 0) {",
        ),
        (
            "overdue_call_order",
            "                    overdue = true;\n"
            "                    camp_func_00351040(context);\n"
            "                    func_0034f840(task_object);",
            "                    overdue = true;\n"
            "                    func_0034f840(task_object);\n"
            "                    camp_func_00351040(context);",
        ),
        (
            "probe_inverted",
            "if (func_00351028(context) == 0) {",
            "if (func_00351028(context) != 0) {",
        ),
        (
            "baseline_offset_wrong",
            "constexpr u32 kBaselineOffset = 0x08;",
            "constexpr u32 kBaselineOffset = 0x10;",
        ),
        (
            "advance_gate_inverted",
            "if (func_00350a64(context) != 0) {",
            "if (func_00350a64(context) == 0) {",
        ),
        (
            "loop_exit_conjunction",
            "if (overdue || status_seen || state == 7 || state == 1) {",
            "if (overdue || status_seen || (state == 7 && state == 1)) {",
        ),
    ]
    for name, old, new in mutants:
        mutant = compile_mutant(name, old, new)
        detected = False
        for case in cases:
            res_orig = machine.run(None, case)
            try:
                res_mut = machine.run(mutant, case)
            except RuntimeError:
                # A mutant that never leaves the wait loop is a detected
                # difference; the iteration cap keeps the run bounded.
                detected = True
                break
            if res_orig != res_mut:
                detected = True
                break
        assert detected, f"negative control not detected: {name}"
        print(f"  [PASS] mutant detected: {name}")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
