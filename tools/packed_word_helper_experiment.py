#!/usr/bin/env python3
"""Differentially test three identical packed-word register-level helpers.

The source-level AAPCS signature is only a harness model. Static direct-BL
search found no callsites; three code.bin words point at these helpers from
data tables, whose dispatch and semantic role remain unresolved.
"""
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

from tools.semantic_experiment import (  # noqa: E402
    DATA, DATA_SIZE, STACK, STACK_SIZE, SP, TEXT, U32_MASK, Case, Runner,
    difference,
)
from tools.semantic_experiment_support import (  # noqa: E402
    compile_candidate_symbols, load_pinned_reference,
)

FUNCTIONS = {
    0x003F8808: "candidate_003f8808",
    0x003F88E4: "candidate_003f88e4",
    0x003F89CC: "candidate_003f89cc",
}
SIZE = 44
WORDS = (0xE59D0000, 0xE1A02F02, 0xE1A0CC00, 0xE18C3683, 0xE1832422,
         0xE3A00000, 0xE1A03000, 0xE3822602, 0xE1800001, 0xE1821003,
         0xE12FFF1E)
DATA_POINTER_SLOTS = {
    0x004212DC: 0x003F8808,
    0x0042137C: 0x003F88E4,
    0x00421394: 0x003F89CC,
}
NEGATIVES = ("wrong_stack_shift", "wrong_r2_lane", "wrong_r1_return", "wrong_constant")


def _direct_bl_targets(image: bytes, text_size: int) -> dict[int, list[int]]:
    refs = {address: [] for address in FUNCTIONS}
    for offset in range(0, min(text_size, len(image)) - 3, 4):
        word = struct.unpack_from("<I", image, offset)[0]
        if word >> 24 != 0xEB:
            continue
        imm = word & 0xFFFFFF
        if imm & 0x800000:
            imm -= 1 << 24
        target = (TEXT + offset + 8 + (imm << 2)) & U32_MASK
        if target in refs:
            refs[target].append(TEXT + offset)
    return refs


def verify_reference(reference) -> dict:
    by_address = {int(row["address"], 16): row for row in reference.ledger}
    text_size = int(reference.game_info["segments"]["text"]["size"], 16)
    refs = _direct_bl_targets(reference.image, text_size)
    funcs, pointer_slots = {}, {}
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    for address, symbol in FUNCTIONS.items():
        row = by_address.get(address)
        if row is None or row["status"] != "matching" or int(row["size"]) != SIZE:
            raise ValueError(f"Ledger entry changed at {address:#010x}")
        code = reference.image[address - TEXT:address - TEXT + SIZE]
        actual_words = struct.unpack("<11I", code)
        if actual_words != WORDS:
            raise ValueError(f"Instruction words changed at {address:#010x}")
        instructions = list(decoder.disasm(code, address))
        if sum(item.size for item in instructions) != SIZE:
            raise ValueError(f"Instruction decode incomplete at {address:#010x}")
        funcs[hex(address)] = {
            "ledger_name": row["name"], "size": SIZE,
            "sha256": hashlib.sha256(code).hexdigest(),
            "instruction_words": [f"0x{word:08x}" for word in actual_words],
            "decoded": [f"{item.mnemonic} {item.op_str}".strip() for item in instructions],
            "direct_arm_bl_sites": [hex(site) for site in refs[address]],
            "direct_arm_bl_search_scope": f"all 4-byte-aligned words in pinned text segment ({text_size:#x} bytes), ARM BL encoding only",
        }
    for slot, target in DATA_POINTER_SLOTS.items():
        offset = slot - TEXT
        if offset < 0 or offset + 4 > len(reference.image):
            raise ValueError(f"Function-pointer data slot outside code.bin: {slot:#010x}")
        actual = struct.unpack_from("<I", reference.image, offset)[0]
        if actual != target:
            raise ValueError(f"Function-pointer table word changed at {slot:#010x}")
        pointer_slots[hex(slot)] = hex(actual)
    return {
        "code_sha256": reference.game_info["code_sha256"],
        "functions": funcs,
        "observed_data_pointer_slots": pointer_slots,
        "caller_evidence": {
            "observation": "No direct ARM BL instruction in the aligned-word scan targets any of the three leaves.",
            "inference": "The pinned data words are function-pointer-like values at these addresses.",
            "unknown": "Dispatch logic, caller register setup, source-level parameter types, and high-level meaning are not established.",
            "scope_limit": "The scan does not cover Thumb BL, computed/interworking calls, or mistaken code/data decoding; no caller contract is claimed.",
        },
    }


def _store_u32(buffer: bytearray, offset: int, value: int):
    buffer[offset:offset + 4] = (value & U32_MASK).to_bytes(4, "little")


def make_cases(address: int, seed: int, samples: int):
    """Systematic one-hot/overlap edges plus seeded full-word patterns."""
    if samples < 0:
        raise ValueError("samples must be non-negative")
    rng = random.Random(seed ^ address)
    # r1, r2, r3, and the fifth word exercise each input lane's bit boundaries.
    sources = (0, 1, 2, 0x7FFFFFFF, 0x80000000, U32_MASK)
    vectors = [(x, y, z, w) for x in sources for y in sources
               for z in sources for w in sources]
    # One-hot patterns expose shifts crossing bit 21/22/23/24/31 and wrap loss.
    for bit in range(32):
        vectors.extend(((rng.getrandbits(32), 1 << bit, 1 << bit, 1 << bit),))
    # Interaction patterns intentionally overlap OR contributions.
    vectors.extend((
        (0, 0, 1 << 9, 0), (0, 0, 1 << 10, 0),
        (0, 0, 1 << 19, 0), (0, 0, 1 << 18, 0),
        (0, 0, 0x000003FF, 0x000001FF),
        (0, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF),
        (0xAAAAAAAA, 0x55555555, 0xAAAAAAAA, 0x55555555),
    ))
    for index in range(samples):
        vectors.append(tuple(rng.getrandbits(32) for _ in range(4)))
    for index, (low_r1, source_r2, source_r3, stack_word) in enumerate(vectors):
        regs = [rng.getrandbits(32) for _ in range(13)]
        # Input r0 is purposefully varied and must be ignored by the observed code.
        regs[0], regs[1], regs[2], regs[3] = rng.getrandbits(32), low_r1, source_r2, source_r3
        memory = bytearray(rng.randbytes(DATA_SIZE))
        stack = bytearray(rng.randbytes(STACK_SIZE))
        stack_offset = SP - STACK
        _store_u32(stack, stack_offset, stack_word)
        yield Case(f"packed-{index}", tuple(regs), bytes(memory), bytes(stack),
                   rng.getrandbits(4) << 28)


def _result_pair(runner: Runner, execution) -> tuple[int, int]:
    from unicorn import arm_const as arm
    return execution.result, runner.uc.reg_read(arm.UC_ARM_REG_R1)


def _fault_at_invalid_stack(runner: Runner, case: Case, entry: int) -> tuple[bool, frozenset[int], frozenset[int]]:
    """Move SP to a crossing boundary before instruction 1 and observe fault/read/write."""
    from unicorn import arm_const as arm
    bad_sp = STACK + STACK_SIZE - 2

    def set_bad_sp(uc, address, size, _):
        if address == entry:
            uc.reg_write(arm.UC_ARM_REG_SP, bad_sp)

    import unicorn
    runner.uc.hook_add(unicorn.UC_HOOK_CODE, set_bad_sp)
    result = runner.run(case)
    return result.fault is not None, result.reads, result.writes


def run(code_path: Path, output: Path, seed: int, samples: int) -> dict:
    if samples < 0:
        raise ValueError("samples must be non-negative")
    output.mkdir(parents=True, exist_ok=True)
    reference = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                      ROOT / "config/functions.csv")
    evidence = verify_reference(reference)
    source = ROOT / "experiments/semantic_equivalence/packed_word_helper_candidates.cpp"
    symbols = list(FUNCTIONS.values()) + list(NEGATIVES)
    compiled = compile_candidate_symbols(source, output / "packed_word_helpers.o", ROOT, symbols)
    function_results, negative_results = [], []
    for address, symbol in FUNCTIONS.items():
        original, candidate = Runner(reference.image, address), Runner(reference.image, address,
                                                                       compiled[symbol])
        count, failure = 0, None
        for case in make_cases(address, seed, samples):
            old, new = original.run(case), candidate.run(case)
            reason = difference(old, new, returns_value=False)
            if not reason and _result_pair(original, old) != _result_pair(candidate, new):
                reason = "r0/r1 return pair differs"
            if not reason and old.nzcv != new.nzcv:
                reason = "NZCV differs (tested as an observational extension, not caller ABI evidence)"
            stack_bytes = frozenset(range(SP, SP + 4))
            if not reason and (old.reads != stack_bytes or new.reads != stack_bytes):
                reason = "expected exactly one 32-bit read from [sp]"
            if not reason and (old.writes or new.writes):
                reason = "unexpected memory write"
            count += 1
            if reason:
                failure = {"case": case.label, "reason": reason}
                break
        function_results.append({"address": hex(address), "candidate": symbol,
                                 "candidate_bytes": len(compiled[symbol]),
                                 "cases": count, "passed": failure is None,
                                 "failure": failure})

        for wrong in NEGATIVES:
            bad = Runner(reference.image, address, compiled[wrong])
            detected, witness = False, None
            for case in make_cases(address, seed, 0):
                old, new = original.run(case), bad.run(case)
                if (_result_pair(original, old) != _result_pair(bad, new)
                        or old.reads != new.reads or old.writes != new.writes):
                    detected, witness = True, case.label
                    break
            negative_results.append({"address": hex(address), "control": wrong,
                                     "detected": detected, "witness": witness})

    fault_results = []
    for address, symbol in FUNCTIONS.items():
        case = next(make_cases(address, seed, 0))
        old_fault = _fault_at_invalid_stack(Runner(reference.image, address), case, address)
        new_fault = _fault_at_invalid_stack(Runner(reference.image, address,
                                                    compiled[symbol]), case, address)
        fault_results.append({"address": hex(address), "invalid_sp": hex(STACK + STACK_SIZE - 2),
                              "original_faulted": old_fault[0], "candidate_faulted": new_fault[0],
                              "original_reads": sorted(hex(x) for x in old_fault[1]),
                              "candidate_reads": sorted(hex(x) for x in new_fault[1]),
                              "passed": old_fault[0] and new_fault[0]
                                        and old_fault[1] == new_fault[1]
                                        and old_fault[2] == new_fault[2]})
    report = {
        "experiment": "packed_word_helper_register_contract",
        "seed": seed, "random_samples_per_function": samples,
        "reference": evidence, "functions": function_results,
        "negative_controls": negative_results, "fault_footprint": fault_results,
        "passed": all(row["passed"] for row in function_results)
                  and all(row["detected"] for row in negative_results)
                  and all(row["passed"] for row in fault_results),
        "observed_register_contract": {
            "inputs": "r1, r2, r3, and a 32-bit word loaded from [sp]; incoming r0 is overwritten before use",
            "outputs": "r0 receives incoming r1; r1 receives the assembled 32-bit word",
            "assembly_expression": "r0_out=r1_in; r1_out=(stack_word<<24)|(r3_in<<13)|((r2_in<<30)>>8)|0x00200000, all operations 32-bit",
            "memory": "one 32-bit read at [sp], no writes in valid mapped-stack cases",
            "source_abi": "not established: no direct ARM BL sites were found; pointer-like data words exist, but their dispatch is unresolved",
        },
        "limitations": [
            "The AAPCS C++ signature is a test harness model, not a proven game source signature.",
            "No direct caller setup/consumption path is claimed; ARM-aligned direct BL scan is bounded and does not cover Thumb/interworking/computed dispatch.",
            "Only mapped ordinary RAM is used for broad data patterns; the boundary-fault probe tests that both versions fault when [sp] crosses the mapped stack edge.",
            "Randomized and directed testing is bounded evidence, not a formal equivalence proof or game boot.",
            "No production source, ledger, README, MODLOG, or emulator files are modified.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/semantic-equivalence/packed-word-helpers")
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument("--samples", type=int, default=128)
    args = parser.parse_args()
    report = run(args.code, args.output, args.seed, args.samples)
    print(json.dumps({"passed": report["passed"], "functions": report["functions"],
                      "negative_controls": report["negative_controls"],
                      "fault_footprint": report["fault_footprint"]}, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
