#!/usr/bin/env python3
"""Differentially test two pinned load-and-store callback helpers."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import sys

import capstone

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.semantic_experiment import (
    DATA, DATA_SIZE, STACK_SIZE, TEXT, U32_MASK, Case, Runner,
)
from tools.semantic_experiment_support import (
    compile_candidate_symbols, load_pinned_reference,
)

FUNCTIONS = {
    0x003E89D8: {
        "symbol": "candidate_003e89d8",
        "words": (0xE5922000, 0xE2811004, 0xE3A00001, 0xE8810005, 0xE12FFF1E),
    },
    0x003E8A68: {
        "symbol": "candidate_003e8a68",
        "words": (0xE5922000, 0xE2811004, 0xE3A00001, 0xE8810005, 0xE12FFF1E),
    },
}
DIRECT_CALLERS = {0x003E89D8: (), 0x003E8A68: ()}
FAULT_LABELS = ("fault-unmapped-source", "fault-unmapped-first-store",
                "fault-partial-second-store")


def _direct_bl_callers(image: bytes, targets: set[int]) -> dict[int, tuple[int, ...]]:
    found = {address: [] for address in targets}
    for offset in range(0, len(image) - 3, 4):
        word = struct.unpack_from("<I", image, offset)[0]
        if word & 0x0F000000 != 0x0B000000 or word >> 28 == 0xF:
            continue
        displacement = (word & 0x00FFFFFF) << 2
        if displacement & (1 << 25):
            displacement -= 1 << 26
        site = TEXT + offset
        target = (site + 8 + displacement) & U32_MASK
        if target in found:
            found[target].append(site)
    return {address: tuple(sites) for address, sites in found.items()}


def verify_reference(reference) -> dict:
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    ledger = {int(row["address"], 16): row for row in reference.ledger}
    callers = _direct_bl_callers(reference.image, set(FUNCTIONS))
    funcs = {}
    for address, spec in FUNCTIONS.items():
        row = ledger.get(address)
        if row is None or row["status"] != "matching" or int(row["size"]) != 20:
            raise ValueError(f"Pinned ledger entry changed at {address:#010x}")
        if callers[address] != DIRECT_CALLERS[address]:
            raise ValueError(
                f"Direct BL caller set changed at {address:#010x}: {callers[address]}"
            )
        code = reference.image[address - TEXT:address - TEXT + 20]
        words = struct.unpack("<5I", code)
        if words != spec["words"]:
            raise ValueError(f"Instruction words changed at {address:#010x}: {words!r}")
        decoded = list(decoder.disasm(code, address))
        actual = tuple((item.mnemonic.lower(), item.op_str.lower()) for item in decoded)
        expected = (("ldr", "r2, [r2]"), ("add", "r1, r1, #4"),
                    ("mov", "r0, #1"), ("stm", "r1, {r0, r2}"),
                    ("bx", "lr"))
        if actual != expected or sum(i.size for i in decoded) != 20:
            raise ValueError(f"Disassembly changed at {address:#010x}: {actual!r}")
        funcs[hex(address)] = {
            "ledger_name": row["name"], "ledger_status": row["status"],
            "size": 20, "instructions": [f"{m} {o}" for m, o in actual],
            "instruction_words": [f"0x{word:08x}" for word in words],
            "function_sha256": hashlib.sha256(code).hexdigest(),
            "verified_observable_contract": {
                "source": "read u32 at input r2, then r2 contains the loaded value",
                "destination": "advance input r1 by 4 bytes",
                "stores_in_register_order": [
                    "write 1 at advanced r1 (original r1 + 4)",
                    "write loaded u32 at advanced r1 + 4 (original r1 + 8)",
                ],
                "return_r0": 1,
                "condition_flags_modified": False,
            },
            "direct_bl_callers": [],
        }
    return {"code_sha256": reference.game_info["code_sha256"],
            "functions": funcs,
            "caller_review": (
                "No direct ARM BL callers were found for these addresses. "
                "Indirect callback/table references were not resolved, so no caller "
                "window is claimed or executed."
            )}


def _put_u32(memory: bytearray, address: int, value: int) -> None:
    struct.pack_into("<I", memory, address - DATA, value & U32_MASK)


def _case(address: int, seed: int, label: str, destination: int,
          source: int, loaded: int, nzcv: int | None = None) -> Case:
    rng = random.Random(seed ^ address ^ sum(map(ord, label)))
    memory = bytearray(rng.randbytes(DATA_SIZE))
    if DATA <= source <= DATA + DATA_SIZE - 4:
        _put_u32(memory, source, loaded)
    regs = [rng.getrandbits(32) for _ in range(13)]
    regs[1] = destination
    regs[2] = source
    return Case(label, tuple(regs), bytes(memory), rng.randbytes(STACK_SIZE),
                ((rng.getrandbits(4) << 28) if nzcv is None else nzcv))


def make_cases(address: int, seed: int, samples: int):
    if samples < 0:
        raise ValueError("samples must be non-negative")
    base = DATA + 0x100
    source = DATA + 0x300
    for index, value in enumerate((0, 1, 0x7FFFFFFF, 0x80000000, U32_MASK)):
        yield _case(address, seed, f"boundary-{index}-{value:08x}", base, source,
                    value, (index & 0xF) << 28)
    # Aliasing confirms the source load occurs before either destination store.
    yield _case(address, seed, "source-aliases-first-store", base, base + 4,
                0xA5A55A5A)
    yield _case(address, seed, "source-aliases-second-store", base, base + 8,
                0x5A5AA5A5)
    # The original single STM may commit its first word before faulting on the
    # second. Preserve these as explicit fault cases, not successful samples.
    yield _case(address, seed, FAULT_LABELS[0], base, DATA + DATA_SIZE,
                0x12345678)
    yield _case(address, seed, FAULT_LABELS[1], DATA + DATA_SIZE - 4,
                source, 0x23456789)
    yield _case(address, seed, FAULT_LABELS[2], DATA + DATA_SIZE - 8,
                source, 0x3456789A)
    rng = random.Random(seed ^ address)
    for index in range(samples):
        destination = DATA + 0x80 + 4 * rng.randrange((DATA_SIZE - 0x100) // 4)
        source_address = DATA + 4 * rng.randrange(DATA_SIZE // 4)
        value = rng.getrandbits(32)
        yield _case(address, seed + index + 1, f"random-{index}-{value:08x}",
                    destination, source_address, value)


def _full_registers(runner: Runner) -> tuple[int, ...]:
    from unicorn import arm_const as arm

    ids = [getattr(arm, f"UC_ARM_REG_R{index}") for index in range(13)]
    ids.extend((arm.UC_ARM_REG_SP, arm.UC_ARM_REG_LR, arm.UC_ARM_REG_CPSR,
                arm.UC_ARM_REG_PC))
    return tuple(runner.uc.reg_read(reg) for reg in ids)


def _compare(old, new, old_runner: Runner, new_runner: Runner) -> str | None:
    # Compare full GPR/SPSR-visible state plus memory and access footprints,
    # including when both sides raise the same class of unmapped-access fault.
    if bool(old.fault) != bool(new.fault):
        return "fault behavior differs"
    if old.fault and new.fault and old.fault != new.fault:
        return f"fault differs: original={old.fault}; candidate={new.fault}"
    if old.data != new.data:
        return "data memory differs"
    if old.live_stack != new.live_stack:
        return "live stack differs"
    if old.reads != new.reads:
        return "observable read footprint differs"
    if old.writes != new.writes:
        return "observable write footprint differs"
    old_state, new_state = _full_registers(old_runner), _full_registers(new_runner)
    # A fault necessarily points at different code locations after replacing
    # the function; keep that as explicit evidence but compare all other state.
    if old.fault and new.fault:
        if old_state[:-1] != new_state[:-1]:
            return "full register/CPSR state differs at matching fault class"
    elif old_state != new_state:
        return "full register/CPSR/PC state differs"
    return None


def _expected_footprints(case: Case) -> tuple[frozenset[int], frozenset[int]]:
    reads = frozenset(range(case.registers[2], case.registers[2] + 4))
    destination = (case.registers[1] + 4) & U32_MASK
    writes = frozenset(range(destination, destination + 8))
    return reads, writes


def run(code_path: Path, output: Path, seed: int, samples: int) -> dict:
    if samples < 0:
        raise ValueError("samples must be non-negative")
    output.mkdir(parents=True, exist_ok=True)
    reference = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                     ROOT / "config/functions.csv")
    evidence = verify_reference(reference)
    source_path = ROOT / "experiments/semantic_equivalence/callback_state_candidates.cpp"
    symbols = [spec["symbol"] for spec in FUNCTIONS.values()]
    controls = ["wrong_destination_offset", "wrong_store_order",
                "wrong_second_value", "wrong_return_value"]
    compiled = compile_candidate_symbols(source_path, output / "callback_state.o",
                                         ROOT, symbols + controls)
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    compiled_instructions = {
        symbol: [f"{insn.mnemonic} {insn.op_str}" for insn in decoder.disasm(code, 0)]
        for symbol, code in compiled.items() if symbol in symbols
    }
    functions, negatives = [], []
    for address, spec in FUNCTIONS.items():
        original = Runner(reference.image, address)
        candidate = Runner(reference.image, address, compiled[spec["symbol"]])
        cases = list(make_cases(address, seed, samples))
        count, failure, fault_evidence = 0, None, []
        partial_fault = None
        for case in cases:
            old = original.run(case)
            new = candidate.run(case)
            reason = _compare(old, new, original, candidate)
            if old.fault or new.fault:
                fault_evidence.append({
                    "case": case.label, "original_fault": old.fault,
                    "candidate_fault": new.fault,
                    "original_fault_pc": hex(old.pc), "candidate_fault_pc": hex(new.pc),
                    "same_partial_memory_and_footprints": reason is None,
                    "reason": reason,
                })
            if not reason and not old.fault:
                expected_reads, expected_writes = _expected_footprints(case)
                if old.reads != expected_reads or old.writes != expected_writes:
                    reason = "unexpected ordinary-memory access footprint"
            if case.label == FAULT_LABELS[2]:
                partial_fault = {
                    "original_fault": old.fault, "candidate_fault": new.fault,
                    "original_first_word": struct.unpack_from(
                        "<I", old.data, DATA_SIZE - 4)[0],
                    "candidate_first_word": struct.unpack_from(
                        "<I", new.data, DATA_SIZE - 4)[0],
                    "passed": reason is None,
                    "reason": reason,
                    "interpretation": (
                        "Checks whether the first STM word remains committed when its "
                        "second word faults; not a real-device/MMIO atomicity guarantee."
                    ),
                }
            count += 1
            if reason:
                failure = {"case": case.label, "reason": reason}
                break
        functions.append({"address": hex(address), "candidate": spec["symbol"],
                          "candidate_bytes": len(compiled[spec["symbol"]]),
                          "cases": count, "passed": failure is None,
                          "failure": failure, "fault_cases": fault_evidence,
                          "partial_second_store_fault": partial_fault})

        normal = next(case for case in cases if case.label == "boundary-4-ffffffff")
        partial = next(case for case in cases if case.label == FAULT_LABELS[2])
        for control in controls:
            wrong = Runner(reference.image, address, compiled[control])
            probe = partial if control == "wrong_store_order" else normal
            old = original.run(probe)
            new = wrong.run(probe)
            reason = _compare(old, new, original, wrong)
            memory_effect_detected = old.data != new.data or old.writes != new.writes
            negatives.append({"address": hex(address), "control": control,
                              "probe": probe.label, "detected": reason is not None,
                              "memory_effect_detected": memory_effect_detected,
                              "reason": reason})

    report = {
        "experiment": "callback_load_and_ordered_pair_store",
        "seed": seed, "random_samples_per_function": samples,
        "reference": evidence, "compiled_candidate_instructions": compiled_instructions,
        "functions": functions,
        "negative_controls": negatives,
        "caller_windows": [],
        "passed": all(row["passed"] for row in functions)
                  and all(row["detected"] for row in negatives)
                  and all(row["memory_effect_detected"] for row in negatives
                          if row["control"] == "wrong_store_order"),
        "limitations": [
            "Inputs are synthetic aligned ordinary-memory pointers inside Unicorn DATA RAM; no 3DS process or hardware MMIO is modeled.",
            "Direct ARM BL scan found no callers. Indirect callback/table references are unresolved, so there is no manually validated caller window in this report.",
            "The original uses one ARM STM instruction; C++ volatile stores are ordered but may compile to separate stores. Fault-edge comparison covers the tested unmapped second word only and does not establish atomicity under all abort/device conditions.",
            "This is bounded isolated ARM execution evidence, not production integration or whole-game equivalence.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n",
                                         encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=Path("extracted/exefs/code.bin"))
    parser.add_argument("--output", type=Path,
                        default=Path("build/semantic-equivalence/callback-state-seed20261024"))
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument("--samples", type=int, default=128)
    args = parser.parse_args()
    report = run(args.code, args.output, args.seed, args.samples)
    print(json.dumps({"passed": report["passed"], "functions": report["functions"],
                      "negative_controls": report["negative_controls"]}, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
