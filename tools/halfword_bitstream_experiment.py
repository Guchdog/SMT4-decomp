#!/usr/bin/env python3
"""Test halfword bit-refill value semantics and gate the private ABI contract.

The C++ symbols are ordinary AAPCS semantic models. They are deliberately not
treated as direct replacements: the original receives its stream/count/value
in r1/r2/r3, returns the updated accumulator in r3, advances r1, adds 16 to
r2, and clobbers callee-saved r9/r10. Reports stay in ignored build/.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import random
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import capstone
from unicorn import arm_const as arm

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.semantic_experiment import DATA, DATA_SIZE, STACK_SIZE, TEXT, Case, Runner
from tools.semantic_experiment_support import load_pinned_reference

EXPECTED_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
WORDS = (0xE0D1A0B2, 0xE2822010, 0xE2629010, 0xE183391A, 0xE1A0F00E)
FUNCTIONS = {
    0x0016E468: "candidate_0016e468",
    0x00174A68: "candidate_00174a68",
    0x0017B068: "candidate_0017b068",
}
DIRECT_CALLS_PER_FUNCTION = 33
MASK32 = 0xFFFFFFFF
PROBE_PREFIXES = (0x00000000, 0x80000000, 0xA5000000, 0xFFFFFF00)


def _ledger() -> list[dict[str, str]]:
    with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _direct_bl_sites(image: bytes, target: int) -> list[int]:
    found = []
    for offset in range(0, len(image) - 3, 4):
        word = struct.unpack_from("<I", image, offset)[0]
        if word & 0x0F000000 != 0x0B000000:
            continue
        displacement = word & 0x00FFFFFF
        if displacement & 0x00800000:
            displacement -= 0x01000000
        if (TEXT + offset + 8 + (displacement << 2)) & MASK32 == target:
            found.append(TEXT + offset)
    return found


def verify_reference(image: bytes, ledger: list[dict[str, str]]) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"Unexpected code.bin SHA-256: {digest}")
    by_address = {int(row["address"], 16): row for row in ledger}
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoder.detail = True
    records = {}
    for address in FUNCTIONS:
        row = by_address.get(address)
        if row is None or int(row["size"]) != 20 or row["status"] != "matching":
            raise ValueError(f"Ledger entry changed at {address:#010x}")
        raw = image[address - TEXT:address - TEXT + 20]
        words = struct.unpack("<5I", raw)
        if words != WORDS:
            raise ValueError(f"Instruction words changed at {address:#010x}: {words}")
        decoded = [(item.mnemonic, item.op_str) for item in decoder.disasm(raw, address)]
        expected = [
            ("ldrh", "sl, [r1], #2"),
            ("add", "r2, r2, #0x10"),
            ("rsb", "sb, r2, #0x10"),
            ("orr", "r3, r3, sl, lsl sb"),
            ("mov", "pc, lr"),
        ]
        if decoded != expected:
            raise ValueError(f"Instruction contract changed at {address:#010x}: {decoded}")
        callers = _direct_bl_sites(image, address)
        if len(callers) != DIRECT_CALLS_PER_FUNCTION:
            raise ValueError(
                f"Expected {DIRECT_CALLS_PER_FUNCTION} direct BL sites at {address:#010x}, "
                f"found {len(callers)}"
            )
        caller_evidence = []
        operand_classes: dict[str, int] = {}
        for site in callers:
            context = list(decoder.disasm(image[site - TEXT - 12:site - TEXT + 4], site - 12))
            branch = next((item for item in context if item.address == site), None)
            if branch is None or branch.id != capstone.arm.ARM_INS_BL or branch.cc != capstone.arm.ARM_CC_LT:
                raise ValueError(f"Caller at {site:#010x} is not the pinned BLT form")
            flag_setter = next((item for item in reversed(context[:-1]) if item.update_flags), None)
            if flag_setter is None or flag_setter.mnemonic != "subs" or not flag_setter.op_str.startswith("r2, r2, "):
                raise ValueError(f"Caller at {site:#010x} no longer gates BLT with SUBS r2")
            operand = flag_setter.op_str.rsplit(", ", 1)[1]
            operand_class = "immediate" if operand.startswith("#") else operand
            operand_classes[operand_class] = operand_classes.get(operand_class, 0) + 1
            caller_evidence.append({
                "site": f"0x{site:08x}",
                "condition": "LT",
                "subtract": flag_setter.op_str,
                "flags_preserved_between_sub_and_call": all(
                    not item.update_flags for item in context
                    if flag_setter.address < item.address < branch.address
                ),
                "window": [f"{item.mnemonic} {item.op_str}" for item in context],
            })
        records[f"0x{address:08x}"] = {
            "name": row["name"],
            "size": int(row["size"]),
            "bytes_hex": raw.hex(),
            "bytes_sha256": hashlib.sha256(raw).hexdigest(),
            "instruction_words": [f"0x{word:08x}" for word in words],
            "direct_call_count": len(callers),
            "direct_call_sites": [f"0x{site:08x}" for site in callers],
            "caller_subtract_operand_classes": operand_classes,
            "caller_windows": caller_evidence,
        }
    return {"code_sha256": digest, "functions": records}


def _registers(runner: Runner) -> dict[str, int]:
    uc = runner.uc
    ids = [getattr(arm, f"UC_ARM_REG_R{i}") for i in range(13)]
    values = {f"r{i}": uc.reg_read(reg_id) for i, reg_id in enumerate(ids)}
    values["sp"] = uc.reg_read(arm.UC_ARM_REG_SP)
    values["lr"] = uc.reg_read(arm.UC_ARM_REG_LR)
    values["nzcv"] = uc.reg_read(arm.UC_ARM_REG_CPSR) & 0xF0000000
    return values


def make_cases(seed: int):
    """Cover all 256 effective register-shift residues and high-word aliases."""
    rng = random.Random(seed ^ 0x16E468)
    words = (0x0001, 0x8001, 0xA55A, 0xFFFF)
    for prefix_index, prefix in enumerate(PROBE_PREFIXES):
        for residue in range(256):
            count = (prefix | residue) & MASK32
            data = bytearray(rng.randbytes(DATA_SIZE))
            pointer = 0x200 + ((residue + prefix_index) % 16) * 4
            word = words[(residue + prefix_index) % len(words)]
            struct.pack_into("<H", data, pointer, word)
            regs = [rng.getrandbits(32) for _ in range(13)]
            regs[0] = rng.getrandbits(32)  # ordinary C++ model's unused r0 arg
            regs[1] = DATA + pointer
            regs[2] = count
            regs[3] = 0  # make every OR-in contribution visible
            yield Case(f"prefix-{prefix_index}-residue-{residue:02x}", tuple(regs),
                       bytes(data), rng.randbytes(STACK_SIZE),
                       rng.getrandbits(4) << 28)


def _expected_model(stream_word: int, count: int, accumulator: int) -> int:
    amount = (-count) & 0xFF
    if amount == 0:
        shifted = stream_word
    elif amount < 32:
        shifted = (stream_word << amount) & MASK32
    else:
        shifted = 0
    return accumulator | shifted


def run(code_path: Path, output: Path, seed: int) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    pinned = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                   ROOT / "config/functions.csv")
    reference = verify_reference(pinned.image, pinned.ledger)
    source = ROOT / "experiments/semantic_equivalence/halfword_bitstream_candidates.cpp"
    obj = output / "halfword_bitstream_candidates.o"
    build = compile_tu_armv6k(source, obj, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr or "ARMv6K candidate compilation failed")
    compiled = {}
    for symbol, (code, relocations) in extract_elf_functions_detailed(obj).items():
        if relocations:
            raise ValueError(f"Unsupported relocation in {symbol}: {relocations}")
        compiled[symbol] = code
    required = set(FUNCTIONS.values())
    required |= {f"wrong_{kind}_{address:08x}"
                 for address in FUNCTIONS for kind in ("sign", "width")}
    if not required <= compiled.keys():
        raise ValueError(f"Missing candidate symbols: {sorted(required - compiled.keys())}")

    functions = []
    negative_controls = []
    for address, symbol in FUNCTIONS.items():
        original = Runner(pinned.image, address)
        candidate = Runner(pinned.image, address, compiled[symbol])
        controls = {
            kind: Runner(pinned.image, address,
                         compiled[f"wrong_{kind}_{address:08x}"])
            for kind in ("sign", "width")
        }
        totals = {"value_matches": 0, "expected_reads": 0, "no_writes": 0,
                  "original_flags_unchanged": 0, "candidate_aapcs_preserved": 0}
        replacement_state_mismatches = {key: 0 for key in ("r1", "r2", "r3", "r9", "r10", "nzcv")}
        failure = None
        count = 0
        control_detected = {"sign": False, "width": False}
        for case in make_cases(seed):
            old = original.run(case)
            new = candidate.run(case)
            old_state, new_state = _registers(original), _registers(candidate)
            pointer = case.registers[1]
            low = pointer - DATA
            word = struct.unpack_from("<H", case.data, low)[0]
            expected_r3 = _expected_model(word, case.registers[2], case.registers[3])
            expected_reads = frozenset((pointer, pointer + 1))
            value_ok = old_state["r3"] == expected_r3 == new_state["r0"]
            reads_ok = old.reads == expected_reads and new.reads == expected_reads
            writes_ok = not old.writes and not new.writes
            flags_ok = old_state["nzcv"] == case.nzcv
            preserved_ok = new.preserved == new.expected_preserved
            totals["value_matches"] += value_ok
            totals["expected_reads"] += reads_ok
            totals["no_writes"] += writes_ok
            totals["original_flags_unchanged"] += flags_ok
            totals["candidate_aapcs_preserved"] += preserved_ok
            for key in replacement_state_mismatches:
                if old_state[key] != new_state[key]:
                    replacement_state_mismatches[key] += 1
            count += 1
            if not all((old.stopped, new.stopped, value_ok, reads_ok, writes_ok,
                        flags_ok, preserved_ok)):
                failure = {
                    "case": case.label,
                    "old_stopped": old.stopped,
                    "candidate_stopped": new.stopped,
                    "value_ok": value_ok,
                    "reads_ok": reads_ok,
                    "writes_ok": writes_ok,
                    "original_flags_unchanged": flags_ok,
                    "candidate_aapcs_preserved": preserved_ok,
                }
                break

            # Keep negative controls focused and deterministic.
            if case.label in ("prefix-0-residue-01", "prefix-0-residue-de"):
                kind = "sign" if case.label.endswith("01") else "width"
                controls[kind].run(case)
                wrong = _registers(controls[kind])["r0"]
                control_detected[kind] = wrong != old_state["r3"]

        functions.append({
            "address": f"0x{address:08x}", "candidate": symbol,
            "tested_cases": count, "effective_shift_residues": 256,
            "high_word_prefixes": [f"0x{x:08x}" for x in PROBE_PREFIXES],
            "counts": totals, "replacement_state_mismatch_cases": replacement_state_mismatches,
            "value_and_footprint_passed": failure is None,
            "failure": failure,
        })
        for kind in ("sign", "width"):
            negative_controls.append({"address": f"0x{address:08x}", "control": kind,
                                      "detected": control_detected[kind]})

    caller_windows = []
    # One caller-proven initial refill per copy: the caller sets r2=0, subtracts
    # one, and conditionally invokes the helper with r2=-1.
    for address, caller in ((0x0016E468, 0x0016DB04),
                            (0x00174A68, 0x00174104),
                            (0x0017B068, 0x0017A704)):
        spec = FUNCTIONS[address]
        old_runner = Runner(pinned.image, address)
        new_runner = Runner(pinned.image, address, compiled[spec])
        regs = [0xABCD0000 + i for i in range(13)]
        regs[1] = DATA + 0x200
        regs[2] = 0
        regs[3] = 0x13579BDF
        data = bytearray(DATA_SIZE)
        struct.pack_into("<H", data, 0x200, 0xA55A)
        case = Case(f"root-initial-refill-{caller:08x}", tuple(regs), bytes(data),
                    bytes(STACK_SIZE), 0)
        old = old_runner.run(case, start=caller - 4, stops=(caller + 4,), budget=8)
        new = new_runner.run(case, start=caller - 4, stops=(caller + 4,), budget=128)
        old_state, new_state = _registers(old_runner), _registers(new_runner)
        caller_windows.append({
            "callsite": f"0x{caller:08x}",
            "caller_proven_input_r2": "0x00000000 before subs r2,#1; -1 at helper entry",
            "original_stopped_after_call": old.stopped,
            "candidate_stopped_after_call": new.stopped,
            "original_r3": f"0x{old_state['r3']:08x}",
            "candidate_r3": f"0x{new_state['r3']:08x}",
            "candidate_return_r0": f"0x{new_state['r0']:08x}",
            "original_r1": f"0x{old_state['r1']:08x}",
            "candidate_r1": f"0x{new_state['r1']:08x}",
            "original_r2": f"0x{old_state['r2']:08x}",
            "candidate_r2": f"0x{new_state['r2']:08x}",
            "direct_replacement_state_matches": old_state == new_state,
            "interpretation": "value-only C++ model is not wired to the private register ABI",
        })

    report = {
        "experiment": "halfword_bitstream_refill_semantics_and_abi_gate",
        "seed": seed,
        "reference": reference,
        "input_contract": {
            "caller_proven_numeric_r2_range": {
                "established_range": None,
                "known_exact_case": "three root initial-refill sites enter with r2=-1",
                "reason": "other direct callers subtract dynamic r6/r5 values or multiple prior bit counts; local caller windows do not bound the incoming reservoir state",
            },
            "direct_arm_blt_callers": sum(v["direct_call_count"] for v in reference["functions"].values()),
            "dynamic_call_patterns": "LDRB/table-derived r6, masked halfword fields in r5/r6, and immediate decrements; exact validated parser-state range remains unknown",
        },
        "machine_semantics": {
            "r1_after": "(r1_before + 2) mod 2^32",
            "r2_after": "(r2_before + 16) mod 2^32",
            "r9_sb_after": "(-r2_before) mod 2^32",
            "r10_sl_after": "zero-extended halfword read from [r1_before]",
            "r3_after": "r3_before OR LSL-register(halfword, r9_after)",
            "lsl_register_rule": "shift amount is r9[7:0]; 0 preserves the halfword, 1..31 shifts left, 32..255 yields zero",
            "flags": "unchanged (none of the five instructions sets flags)",
            "memory": "one LDRH halfword read at r1; no writes; no stack activity",
            "tested_stream_pointer_alignment_bytes": 2,
        },
        "abi_gate": {
            "direct_normal_cpp_replacement_compatible": False,
            "reason": [
                "original private convention takes the stream pointer/count/accumulator in r1/r2/r3, leaves accumulator in r3 and returns via mov pc,lr; ordinary AAPCS C++ returns scalar values in r0",
                "original overwrites r9/sb and r10/sl, which ordinary AAPCS C++ must preserve",
                "caller evidence proves one exact initial count case and shows selected preservation/dead-path patterns, but not liveness for every direct call path or a numeric range for all count states",
            ],
            "candidate_cpp_is_value_model_only": True,
            "assembly_or_explicit_adapter_required_for_machine_replacement": True,
        },
        "functions": functions,
        "negative_controls": negative_controls,
        "caller_window_probes": caller_windows,
        "semantic_value_and_read_footprint_passed": all(
            item["value_and_footprint_passed"] for item in functions
        ),
        "direct_replacement_compatible": False,
        "passed": all(item["value_and_footprint_passed"] for item in functions)
                  and all(item["detected"] for item in negative_controls),
        "limitations": [
            "This validates the scalar value equation and halfword read footprint; it is not an ABI-compatible replacement experiment.",
            "Each seed exhausts all 256 architecturally effective shift residues and repeats each residue with four high-word prefixes. The formula shows higher bits cannot affect the register shift amount, but this is not an enumeration of 2^32 distinct r2 words.",
            "Three direct caller sites prove r2=-1 for their first refill only. The remaining 96 caller paths have been xref-pinned, but their cross-path bit-count ranges and complete r9/r10 liveness are not proven here.",
            "No production ledger, patch, README, MODLOG, or emulator state is changed.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=Path("extracted/exefs/code.bin"))
    parser.add_argument("--output", type=Path,
                        default=Path("build/semantic-equivalence/halfword-bitstream-seed20261024"))
    parser.add_argument("--seed", type=int, default=20261024)
    args = parser.parse_args()
    report = run(args.code, args.output, args.seed)
    print(json.dumps({"passed": report["passed"], "functions": report["functions"],
                      "negative_controls": report["negative_controls"],
                      "caller_window_probes": report["caller_window_probes"]}, indent=2))


if __name__ == "__main__":
    main()
