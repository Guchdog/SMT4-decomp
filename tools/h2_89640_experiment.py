"""Offline differential for the H2 nested-callback global getter at 0x00289640."""
from __future__ import annotations

import hashlib
import json
import random
import struct
import sys
from pathlib import Path

import unicorn
from unicorn import Uc, UcError, UC_ARCH_ARM, UC_MODE_ARM
from unicorn.arm_const import *

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.semantic_experiment import arm_branch

IMAGE_PATH = ROOT / "extracted/exefs/code.bin"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
SOURCE = ROOT / "src/engine/leaf_batch21_b.cpp"
ENTRY = 0x00289640
CALLER = 0x00221168
SPAN = 20
TEXT = 0x00100000
GLOBAL_SLOT = 0x0044DEB8
DATA = 0x00800000
STACK = 0x00810000
STOP = 0x00820000
U32 = 0xFFFFFFFF


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def word(data: bytes, offset: int = 0) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def arm_bl_target(instruction: int, site: int) -> int | None:
    if instruction & 0xFF000000 != 0xEB000000:
        return None
    displacement = (instruction & 0x00FFFFFF) << 2
    if displacement & 0x02000000:
        displacement -= 0x04000000
    return site + 8 + displacement


def compile_production(out: Path) -> bytes:
    out.mkdir(parents=True, exist_ok=True)
    obj = out / "leaf_batch21_b.o"
    result = compile_tu_armv6k(SOURCE, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr)
    functions = extract_elf_functions_detailed(obj)
    body, relocs = functions["engine_func_00289640"]
    if len(body) != SPAN or relocs:
        raise AssertionError(f"unexpected getter body: {len(body)} bytes, relocations={relocs}")
    return body


def staged(image: bytes, body: bytes) -> bytes:
    offset = ENTRY - TEXT
    if len(body) != SPAN or offset < 0 or offset + SPAN > len(image):
        raise AssertionError("invalid production slot")
    mutable = bytearray(image)
    mutable[offset:offset + SPAN] = body
    return bytes(mutable)


class Machine:
    def __init__(self, image: bytes, state_address: int, state_value: int,
                 r0: int, callback: bool = False):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        self.uc.mem_map(TEXT, (len(image) + 0xFFF) & ~0xFFF)
        self.uc.mem_write(TEXT, image)
        self.uc.mem_map(DATA, 0x10000)
        self.uc.mem_map(STACK, 0x10000)
        self.state_address = state_address
        self.uc.mem_write(GLOBAL_SLOT, struct.pack("<I", state_address))
        self.uc.mem_write(state_address + 0xD0, struct.pack("<I", state_value & U32))
        if callback:
            object1, object2 = DATA + 0x3000, DATA + 0x5000
            self.uc.mem_write(0x0043E18C, struct.pack("<I", object1))
            self.uc.mem_write(0x0043E190, struct.pack("<I", object2))
            self.uc.mem_write(object1 + 8, b"\x00")
            self.uc.mem_write(object2 + 8, b"\x00")
        self.uc.reg_write(UC_ARM_REG_SP, STACK + 0x8000)
        self.uc.reg_write(UC_ARM_REG_LR, STOP)
        self.uc.reg_write(UC_ARM_REG_R0, r0 & U32)
        for i, reg in enumerate((UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6,
                                 UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9,
                                 UC_ARM_REG_R10, UC_ARM_REG_R11)):
            self.uc.reg_write(reg, 0xA4000000 + i * 0x10101)
        self.reads: list[tuple[int, int]] = []
        self.writes: list[tuple[int, int, int]] = []
        self.calls: list[tuple[int, tuple[int, ...]]] = []
        self.callback = callback
        self.uc.hook_add(unicorn.UC_HOOK_MEM_READ, self._read)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._write)
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._code)

    def _read(self, uc, access, address, size, value, _):
        if address in (GLOBAL_SLOT, self.uc.reg_read(UC_ARM_REG_R0)) or address >= DATA:
            if address == GLOBAL_SLOT or DATA <= address < DATA + 0x10000:
                self.reads.append((address, size))

    def _write(self, uc, access, address, size, value, _):
        self.writes.append((address, size, value & U32))

    def _code(self, uc, address, size, _):
        if address == ENTRY:
            self.calls.append((address, tuple(uc.reg_read(r) for r in
                (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3))))
        if not self.callback:
            return
        stubs = {0x0028686C: 0xACCE5501, 0x00296F60: 0xBEEF0020,
                 0x00286928: 0x13572468}
        if address in stubs:
            args = tuple(uc.reg_read(r) for r in
                         (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3))
            if address == 0x00286928:
                sp = uc.reg_read(UC_ARM_REG_SP)
                args += (word(uc.mem_read(sp, 4)), word(uc.mem_read(sp + 4, 4)))
            self.calls.append((address, args))
            uc.reg_write(UC_ARM_REG_R0, stubs[address])
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    def run(self, entry: int) -> dict:
        fault = None
        try:
            self.uc.emu_start(entry, STOP, count=5000)
        except UcError as exc:
            fault = type(exc).__name__
        regs = (UC_ARM_REG_R0, UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6,
                UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10,
                UC_ARM_REG_R11, UC_ARM_REG_SP, UC_ARM_REG_LR)
        return {
            "fault": fault,
            "registers": [self.uc.reg_read(r) for r in regs],
            "reads": self.reads,
            "writes": self.writes,
            "calls": self.calls,
            "global": bytes(self.uc.mem_read(GLOBAL_SLOT, 4)).hex(),
            "state_value": bytes(self.uc.mem_read(self.state_address + 0xD0, 4)).hex(),
        }


def execute(image: bytes, body: bytes | None, state: int, value: int,
            r0: int, callback: bool = False) -> dict:
    if body is not None:
        image = staged(image, body)
    machine = Machine(image, state, value, r0, callback)
    return machine.run(CALLER if callback else ENTRY)


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "build/agent-work/H2-semantic/h2-callback-getter-00289640-convert/run001/checks/direct")
    parser.add_argument("--seed", type=int, default=20261108)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    image = IMAGE_PATH.read_bytes()
    if sha(image) != IMAGE_SHA:
        raise AssertionError("pinned original image hash changed")
    body = compile_production(args.out / "compile")
    offset = ENTRY - TEXT
    original_slot = image[offset:offset + SPAN]
    caller_targets = []
    for site in range(CALLER, CALLER + 148, 4):
        target = arm_bl_target(word(image, site - TEXT), site)
        if target == ENTRY:
            caller_targets.append(site)
    if ENTRY & 1 or len(caller_targets) != 2 or word(body, 12) != 0xE12FFF1E:
        raise AssertionError(f"ARM entry/return/caller audit failed: {caller_targets}")
    staged_image = staged(image, body)
    changed_offsets = [i for i, (old, new) in enumerate(zip(image, staged_image)) if old != new]
    if changed_offsets and (min(changed_offsets) < offset or max(changed_offsets) >= offset + SPAN):
        raise AssertionError("staging changed bytes outside the 20-byte getter slot")
    rng = random.Random(args.seed)
    values = [0, 1, 2, 0xFF, 0x100, 0x7FFFFFFF, 0x80000000, U32]
    direct = []
    for index, value in enumerate(values + [rng.getrandbits(32) for _ in range(32)]):
        state = DATA + 0x1000 + index * 0x100
        ignored_r0 = rng.getrandbits(32)
        left = execute(image, None, state, value, ignored_r0)
        right = execute(image, body, state, value, ignored_r0)
        direct.append({"index": index, "value": value, "matched": left == right,
                       "original": left, "candidate": right})
    caller = []
    for index, value in enumerate((0, 1, 0x80000000, U32, rng.getrandbits(32))):
        state = DATA + 0x8000 + index * 0x100
        ignored_r0 = rng.getrandbits(32)
        left = execute(image, None, state, value, ignored_r0, callback=True)
        right = execute(image, body, state, value, ignored_r0, callback=True)
        caller.append({"index": index, "value": value, "matched": left == right,
                       "original": left, "candidate": right})
    for row in caller:
        events = row["candidate"]["calls"]
        if sum(address == ENTRY for address, _ in events) != 2:
            raise AssertionError("original callback did not call the getter twice")
        if sum(address == 0x00286928 for address, _ in events) != 1:
            raise AssertionError("original callback did not reach the controlled final helper")
    # A one-word offset mutation must change the result when the adjacent word differs.
    mutant = bytearray(body)
    instruction = word(mutant, 8)
    struct.pack_into("<I", mutant, 8, (instruction & 0xFFFFFFF0) | 0xD4)
    state = DATA + 0xE000
    left = execute(image, body, state, 0x11112222, 0xFFFFFFFF)
    right = execute(image, bytes(mutant), state, 0x11112222, 0xFFFFFFFF)
    mutation_detected = left["registers"][0] != right["registers"][0]
    report = {
        "schema_version": 1, "seed": args.seed, "image_sha256": sha(image),
        "source_sha256": sha(SOURCE.read_bytes()), "candidate_body_sha256": sha(body),
        "original_slot_sha256": sha(original_slot), "candidate_bytes_equal": body == original_slot,
        "changed_offsets": [hex(i + TEXT) for i in changed_offsets],
        "arm_entry_even": (ENTRY & 1) == 0, "arm_return_bx_lr": hex(word(body, 12)),
        "original_callback_bl_sites": [hex(site) for site in caller_targets],
        "direct_cases": len(direct), "direct_passed": sum(x["matched"] for x in direct),
        "caller_cases": len(caller), "caller_passed": sum(x["matched"] for x in caller),
        "mutation_detected": mutation_detected, "direct": direct, "caller": caller,
    }
    report_path = args.out / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in (
        "candidate_bytes_equal", "direct_cases", "direct_passed", "caller_cases",
        "caller_passed", "mutation_detected")}, indent=2))
    if report["direct_passed"] != len(direct) or report["caller_passed"] != len(caller) or not mutation_detected:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
