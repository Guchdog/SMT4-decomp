#!/usr/bin/env python3
"""Bounded differential ARM experiment; never changes the matching ledger/image.

This tests selected ordinary-memory leaf functions, not arbitrary C++ equivalence
or a complete 3DS. Reports and compiled artifacts belong in ignored build/.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, replace
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import capstone
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang

try:
    import unicorn
    from unicorn import arm_const as arm
except ImportError:
    unicorn = None
    arm = None

TEXT = 0x00100000
DATA = 0x02000000
DATA_SIZE = 0x1000
STACK = 0x08000000
STACK_SIZE = 0x2000
SP = STACK + 0x1000
INJECT = 0x01000000
RETURN = INJECT + 0x1000
U32_MASK = 0xFFFFFFFF


@dataclass(frozen=True)
class Candidate:
    address: int
    name: str
    returns_value: bool = True

    @property
    def symbol(self):
        return f"candidate_{self.address:08x}"


CANDIDATES = (
    Candidate(0x00128F34, "relative_pointer"),
    Candidate(0x002AE464, "unsigned_threshold"),
    Candidate(0x00394614, "byte_equality"),
    Candidate(0x0038143C, "halfword_cursor"),
    Candidate(0x00381450, "byte_cursor"),
    Candidate(0x003D7228, "three_word_copy"),
    Candidate(0x0037C46C, "state_flags"),
)


@dataclass(frozen=True)
class Case:
    label: str
    registers: tuple[int, ...]
    data: bytes
    stack: bytes
    nzcv: int


@dataclass
class Execution:
    stopped: bool
    fault: str | None
    result: int
    pc: int
    nzcv: int
    preserved: tuple[int, ...]
    expected_preserved: tuple[int, ...]
    data: bytes
    live_stack: bytes
    reads: frozenset[int]
    writes: frozenset[int]


def require_unicorn():
    if unicorn is None:
        raise RuntimeError("Install the optional experiment dependencies: pip install -r requirements-experiment.txt")


def arm_branch(source: int, destination: int) -> bytes:
    displacement = destination - source - 8
    if displacement % 4 or not -(1 << 25) <= displacement < (1 << 25):
        raise ValueError("ARM branch target is unaligned or out of range")
    return struct.pack("<I", 0xEA000000 | ((displacement >> 2) & 0xFFFFFF))


def validate_leaf(code: bytes):
    """Fail closed: this pilot cannot relocate calls, literals or PC-relative data."""
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    cs.detail = True
    instructions = list(cs.disasm(code, 0))
    if sum(i.size for i in instructions) != len(code) or not instructions:
        raise ValueError("Incomplete ARM disassembly")
    if instructions[-1].mnemonic != "bx" or instructions[-1].op_str != "lr":
        raise ValueError("Pilot requires a final bx lr")
    for instruction in instructions[:-1]:
        if instruction.group(capstone.CS_GRP_JUMP) or instruction.group(capstone.CS_GRP_CALL) or "pc" in instruction.op_str:
            raise ValueError("Pilot does not relocate branches or PC-relative operands")
        if instruction.mnemonic.startswith(("svc", "swi", "v")):
            raise ValueError("Pilot excludes OS and floating-point instructions")


class Runner:
    """Execute original image or an in-memory entry trampoline to compiled C++."""

    def __init__(self, image: bytes, entry: int, replacement: bytes | None = None):
        require_unicorn()
        self.entry = entry
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.mem_map(TEXT, 0x400000, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
        self.uc.mem_write(TEXT, image)
        self.uc.mem_map(INJECT, 0x2000, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
        self.uc.mem_map(DATA, DATA_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.uc.mem_map(STACK, STACK_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        if replacement is not None:
            validate_leaf(replacement)
            if len(replacement) > 0x1000:
                raise ValueError("Replacement exceeds reserved code page")
            self.uc.mem_write(INJECT, replacement)
            self.uc.mem_write(entry, arm_branch(entry, INJECT))
        self.reads: set[int] = set()
        self.writes: set[int] = set()
        self.stops: tuple[int, ...] = ()
        self.stopped = False
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._instruction)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_READ | unicorn.UC_HOOK_MEM_WRITE, self._memory)
        self.reg_ids = tuple(getattr(arm, f"UC_ARM_REG_R{i}") for i in range(13))
        self.d_ids = tuple(getattr(arm, f"UC_ARM_REG_D{i}") for i in range(8, 16))

    def _instruction(self, uc, address, size, _):
        if address in self.stops:
            self.stopped = True
            uc.emu_stop()

    def _memory(self, uc, access, address, size, value, _):
        # Compare observable memory footprints, not scratch space below caller SP.
        target = self.writes if access == unicorn.UC_MEM_WRITE else self.reads
        for byte in range(address, address + size):
            if DATA <= byte < DATA + DATA_SIZE or SP <= byte < STACK + STACK_SIZE:
                target.add(byte)

    def run(self, case: Case, *, start: int | None = None,
            stops: tuple[int, ...] = (RETURN,), budget: int = 128) -> Execution:
        uc = self.uc
        uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10 | case.nzcv)
        for reg_id, value in zip(self.reg_ids, case.registers):
            uc.reg_write(reg_id, value)
        expected_d = tuple(((case.registers[4] << 32) | case.registers[5]) ^ i for i in range(8))
        for reg_id, value in zip(self.d_ids, expected_d):
            uc.reg_write(reg_id, value)
        uc.reg_write(arm.UC_ARM_REG_SP, SP)
        uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
        uc.mem_write(DATA, case.data)
        uc.mem_write(STACK, case.stack)
        self.reads.clear()
        self.writes.clear()
        self.stopped = False
        self.stops = stops
        fault = None
        try:
            uc.emu_start(self.entry if start is None else start, 0, count=budget)
        except unicorn.UcError as error:
            fault = str(error)
        preserved = tuple(uc.reg_read(r) for r in self.reg_ids[4:12])
        preserved += (uc.reg_read(arm.UC_ARM_REG_SP),)
        preserved += tuple(uc.reg_read(r) for r in self.d_ids)
        return Execution(
            self.stopped, fault, uc.reg_read(arm.UC_ARM_REG_R0),
            uc.reg_read(arm.UC_ARM_REG_PC), uc.reg_read(arm.UC_ARM_REG_CPSR) & 0xF0000000,
            preserved, case.registers[4:12] + (SP,) + expected_d,
            bytes(uc.mem_read(DATA, DATA_SIZE)), bytes(uc.mem_read(SP, STACK_SIZE // 2)),
            frozenset(self.reads), frozenset(self.writes),
        )


def difference(original: Execution, rebuilt: Execution, *, returns_value=True,
               caller_window=False) -> str | None:
    for label, result in (("original", original), ("rebuilt", rebuilt)):
        if result.fault:
            return f"{label} fault: {result.fault}"
        if not result.stopped:
            return f"{label} instruction budget exhausted / no expected return"
        if result.preserved != result.expected_preserved:
            return f"{label} violates callee-saved register/SP contract"
    if returns_value and original.result != rebuilt.result:
        return "return value differs"
    if original.pc != rebuilt.pc:
        return "caller continuation differs"
    if caller_window and original.nzcv != rebuilt.nzcv:
        return "caller condition flags differ"
    if original.data != rebuilt.data:
        return "data memory differs"
    if original.live_stack != rebuilt.live_stack:
        return "caller stack memory differs"
    if original.reads != rebuilt.reads:
        return "observable read footprint differs"
    if original.writes != rebuilt.writes:
        return "observable write footprint differs"
    return None


def cases(candidate: Candidate, samples: int, seed: int):
    """Generate boundary cases plus seeded random valid ordinary-memory inputs."""
    rng = random.Random(seed ^ candidate.address)
    boundaries = [0, 1, 399, 400, 401, 0x7FFF, 0x8000, 0xFFFF,
                  0x7FFFFFFF, 0x80000000, U32_MASK]
    edge_count = 256 if candidate.name == "byte_equality" else len(boundaries)
    for index in range(edge_count + samples):
        regs = [rng.getrandbits(32) for _ in range(13)]
        memory = bytearray(rng.randbytes(DATA_SIZE))
        stack = rng.randbytes(STACK_SIZE)
        value = boundaries[index] if index < len(boundaries) else rng.getrandbits(32)
        label = f"case-{index}"
        regs[0] = DATA + 0x100 + (index % 8) * 4
        if candidate.name == "unsigned_threshold":
            regs[0] = value
        elif candidate.name == "byte_equality":
            memory[regs[0] - DATA] = index if index < 256 else value & 0xFF
        elif candidate.name == "relative_pointer":
            offset = value % 0x700
            struct.pack_into("<I", memory, regs[0] - DATA + 0x18, offset)
        elif candidate.name in ("byte_cursor", "halfword_cursor"):
            cell = DATA + 0x40 + (index % 8) * 4
            source = DATA + 0x200 + (index % 512) * 2
            if candidate.name == "byte_cursor" and index < 4:
                # unsigned char may inspect pointer representation; valid alias case.
                source = cell + index
                label += "-cursor-alias"
            struct.pack_into("<I", memory, cell - DATA, source)
            if source >= DATA + 0x200:
                struct.pack_into("<H", memory, source - DATA, value & 0xFFFF)
            regs[0] = cell
        elif candidate.name == "state_flags":
            struct.pack_into("<H", memory, regs[0] - DATA + 0x20, value & 0xFFFF)
        elif candidate.name == "three_word_copy":
            struct.pack_into("<III", memory, regs[0] - DATA + 12,
                             value, value ^ U32_MASK, (value + 1) & U32_MASK)
        else:
            raise ValueError(candidate.name)
        yield Case(label, tuple(regs), bytes(memory), stack, rng.getrandbits(4) << 28)


def compare_cases(original: Runner, rebuilt: Runner, inputs, **kwargs):
    count = 0
    for case in inputs:
        reason = difference(original.run(case), rebuilt.run(case), **kwargs)
        if reason:
            return {"passed": False, "cases": count + 1, "counterexample": case.label,
                    "arguments": [f"0x{x:08x}" for x in case.registers[:4]], "reason": reason}
        count += 1
    return {"passed": True, "cases": count}


def patch_image(image: bytes, compiled: dict, game: dict):
    """Install entry branches in a copy, placing relocation-free code in padding.

    The image's declared text byte count is not enlarged. Testing that a real
    loader preserves/maps these existing text pages remains a separate step.
    """
    text = game["segments"]["text"]
    text_base = int(text["vaddr"], 16)
    text_offset = int(text["file_offset"], 16)
    cave_offset = text_offset + int(text["size"], 16)
    padding_end = text_offset + int(text["aligned_size"], 16)
    cave_offset = (cave_offset + 3) & ~3
    if text_base != TEXT or not 0 <= text_offset <= cave_offset <= padding_end <= len(image):
        raise ValueError("Invalid text mapping/padding bounds")
    if any(image[cave_offset:padding_end]):
        raise ValueError("Text padding is not entirely zero; no automatic cave patch allowed")
    patched = bytearray(image)
    records = []
    manifest = []
    for candidate in CANDIDATES:
        code = compiled[candidate.symbol]
        validate_leaf(code)
        if cave_offset + len(code) > padding_end:
            raise ValueError("Experimental replacements exceed existing text page padding")
        entry_offset = text_offset + candidate.address - text_base
        if not text_offset <= entry_offset <= text_offset + int(text["size"], 16) - 4:
            raise ValueError("Entry point is outside the original text range")
        destination = text_base + cave_offset - text_offset
        branch = arm_branch(candidate.address, destination)
        for offset, payload in ((entry_offset, branch), (cave_offset, code)):
            patched[offset:offset + len(payload)] = payload
            records.append((offset, payload))
        manifest.append({"entry": hex(candidate.address), "replacement": hex(destination),
                         "file_offset": cave_offset, "compiled_bytes": len(code)})
        cave_offset += len(code)
        cave_offset = (cave_offset + 3) & ~3
    # IPS records contain generated branches and generated C++ machine code only.
    ips = bytearray(b"PATCH")
    for offset, payload in sorted(records):
        if offset >= 0x1000000 or not 0 < len(payload) < 0x10000:
            raise ValueError("IPS record cannot represent this patch")
        ips += offset.to_bytes(3, "big") + len(payload).to_bytes(2, "big") + payload
    ips += b"EOF"
    return bytes(patched), bytes(ips), manifest


def caller_windows(image, patched_image, samples, seed):
    # Real, unchanged instructions before and after BL; no game boot is implied.
    windows = (
        (0x002AE464, 0x001B0370, 0x001B0374, (0x001B0384, 0x001B0394)),
        (0x00394614, 0x001B4DBC, 0x001B4DC0, (0x001B4DD0, 0x001B4DF4)),
    )
    results = []
    for address, start, callsite, stops in windows:
        # Check that this really is an unconditional BL to the selected original.
        word = struct.unpack_from("<I", image, callsite - TEXT)[0]
        imm = word & 0xFFFFFF
        if imm & 0x800000:
            imm -= 1 << 24
        if word >> 24 != 0xEB or callsite + 8 + imm * 4 != address:
            raise ValueError("Reference caller no longer matches the recorded image")
        candidate = next(c for c in CANDIDATES if c.address == address)
        original, patched = Runner(image, address), Runner(patched_image, address)
        count = 0
        continuations: set[int] = set()
        result = {"callsite": hex(callsite), "callee": hex(address), "passed": True}
        for case in cases(candidate, min(samples, 256), seed):
            regs, stack = list(case.registers), bytearray(case.stack)
            if address == 0x002AE464:
                regs[5] = regs[0]  # Original caller executes mov r0,r5 before BL.
            else:
                stack[SP - STACK] = case.data[regs[0] - DATA]
            case = replace(case, registers=tuple(regs), stack=bytes(stack))
            a = original.run(case, start=start, stops=stops)
            b = patched.run(case, start=start, stops=stops)
            reason = difference(a, b, caller_window=True)
            count += 1
            continuations.add(a.pc)
            if reason:
                result.update(passed=False, reason=reason, counterexample=case.label)
                break
        result.update(cases=count, continuations=[hex(p) for p in sorted(continuations)])
        if len(continuations) != 2:
            result.update(passed=False, reason="Both caller branch outcomes were not exercised")
        results.append(result)
    return results


def experiment(code_path: Path, output: Path, samples=4096, seed=20261024):
    experiment_start = time.perf_counter()
    require_unicorn()
    if samples < 0:
        raise ValueError("samples must be nonnegative")
    output.mkdir(parents=True, exist_ok=True)
    image = code_path.read_bytes()
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(image).hexdigest()
    if len(image) != game["code_bin_size"] or digest != game["code_sha256"]:
        raise ValueError("Private code.bin does not match the configured US revision")
    source = ROOT / "experiments/semantic_equivalence/candidates.cpp"
    source_digest = hashlib.sha256(source.read_bytes()).hexdigest()
    obj = output / "candidates.o"
    start = time.perf_counter()
    build = compile_tu_armv6k(source, obj, ROOT)
    compile_seconds = time.perf_counter() - start
    if build.returncode:
        raise RuntimeError(build.stderr)
    functions = extract_elf_functions_detailed(obj)
    compiled = {}
    for symbol, (code, relocations) in functions.items():
        if relocations:
            raise ValueError(f"Unsupported relocation in {symbol}: {relocations}")
        validate_leaf(code)
        compiled[symbol] = code
    patched_image, ips, patches = patch_image(image, compiled, game)
    with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
        ledger = {int(r["address"], 16): r for r in csv.DictReader(stream)}
    results = []
    for candidate in CANDIDATES:
        address = candidate.address
        size = int(ledger[address]["size"])
        original_code = image[address - TEXT:address - TEXT + size]
        validate_leaf(original_code)
        replacement = compiled[candidate.symbol]
        original = Runner(image, address)
        rebuilt = Runner(patched_image, address)
        start = time.perf_counter()
        comparison = compare_cases(original, rebuilt, cases(candidate, samples, seed),
                                   returns_value=candidate.returns_value)
        results.append({"address": hex(address), "name": candidate.name,
                        "original_bytes": size, "rebuilt_bytes": len(replacement),
                        "byte_identical": original_code == replacement,
                        "seconds": round(time.perf_counter() - start, 6), **comparison})
        print(json.dumps(results[-1]), flush=True)
    controls = []
    for address, symbol, expected_reason in (
        (0x002AE464, "wrong_threshold", "return value differs"),
        (0x00394614, "wrong_byte", "return value differs"),
        (0x00381450, "wrong_cursor", "data memory differs"),
        (0x00381450, "wrong_cursor_order", "return value differs"),
        (0x0037C46C, "wrong_state", "data memory differs"),
        (0x002AE464, "wrong_abi", "rebuilt violates callee-saved register/SP contract"),
    ):
        candidate = next(c for c in CANDIDATES if c.address == address)
        outcome = compare_cases(Runner(image, address), Runner(image, address, compiled[symbol]),
                                cases(candidate, 0, seed), returns_value=candidate.returns_value)
        controls.append({"name": symbol, "expected_reason": expected_reason,
                         "detected": outcome.get("reason") == expected_reason, **outcome})
    integration = caller_windows(image, patched_image, samples, seed)
    if hashlib.sha256(source.read_bytes()).hexdigest() != source_digest:
        raise RuntimeError("Candidate source changed during the experiment; rerun from stable inputs")
    compiler = subprocess.run([str(find_clang()), "--version"], capture_output=True, text=True, check=True)
    passed = (all(r["passed"] for r in results) and all(r["detected"] for r in controls)
              and all(r["passed"] for r in integration))
    report = {
        "schema": 1, "passed": passed,
        "scope": "Seven ARM leaf functions and two original caller windows; not a full game boot",
        "reference_sha256": digest,
        "patched_sha256": hashlib.sha256(patched_image).hexdigest(),
        "ips_sha256": hashlib.sha256(ips).hexdigest(),
        "image_bytes": len(patched_image),
        "patches": patches,
        "source_sha256": source_digest,
        "object_sha256": hashlib.sha256(obj.read_bytes()).hexdigest(),
        "baseline_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                          capture_output=True, text=True, check=True).stdout.strip(),
        "compiler": compiler.stdout.splitlines()[0], "unicorn": unicorn.__version__,
        "cpu": "ARM11 MPCore", "seed": seed, "random_cases_per_function": samples,
        "compile_seconds": round(compile_seconds, 6),
        "total_seconds": round(time.perf_counter() - experiment_start, 6),
        "functions": results, "negative_controls": controls, "caller_windows": integration,
        "limitations": [
            "Tested inputs are not a formal equivalence proof or captured gameplay traces",
            "Ordinary RAM only: no MMIO, concurrent observers, timing, exceptions or OS services",
            "No floating-point, external calls, relocations or PC-relative replacements",
            "Internal caller-saved registers/flags and scratch stack contents may differ",
            "Preserved r4-r11, SP, d8-d15; compared r0 for every pilot function, caller flags/continuation, RAM and access footprints",
            "Patched image uses zero text-page padding; real 3DS loader behavior and full game boot are untested",
            "Source/ledger/private original remain unchanged; experimental functions do not count as exact matching",
        ],
    }
    if passed:
        (output / "code.experimental.bin").write_bytes(patched_image)
        (output / "code.ips").write_bytes(ips)
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Experiment {'PASS' if passed else 'FAIL'}; report: {output / 'report.json'}", flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path, default=ROOT / "build/semantic-equivalence")
    parser.add_argument("--samples", type=int, default=4096)
    parser.add_argument("--seed", type=int, default=20261024)
    args = parser.parse_args()
    try:
        result = experiment(args.code, args.output, args.samples, args.seed)
    except (RuntimeError, ValueError, OSError) as error:
        parser.exit(2, f"Experiment error: {error}\n")
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
