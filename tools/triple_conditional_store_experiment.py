#!/usr/bin/env python3
"""Differential-test the guarded three-word STM helper at 0x0034F978."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import capstone
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang
from tools.semantic_experiment import (
    DATA, DATA_SIZE, STACK_SIZE, TEXT, Case, Runner, difference,
    validate_local_blob,
)
from tools.semantic_experiment_support import load_pinned_reference

ADDRESS = 0x0034F978
FUNCTION_SIZE = 24
CALLER = 0x0034F284
CALLER_CONTINUATIONS = {"zero": 0x0034F304, "nonzero": 0x0034F290}
EXPECTED_BYTES = bytes.fromhex(
    "00 00 51 e3 04 00 80 12 00 00 a0 03 0e 00 80 18 "
    "01 00 a0 13 1e ff 2f e1"
)
EXPECTED_INSTRUCTIONS = (
    ("cmp", "r1, #0"),
    ("addne", "r0, r0, #4"),
    ("moveq", "r0, #0"),
    ("stmne", "r0, {r1, r2, r3}"),
    ("movne", "r0, #1"),
    ("bx", "lr"),
)
EXPECTED_CALLER = (
    ("push", "{r3, r4, r5, lr}"),
    ("mov", "r4, r0"),
    ("bl", "#0x34f978"),
    ("cmp", "r0, #0"),
    ("beq", "#0x34f304"),
)
U32_MASK = 0xFFFFFFFF


def _decode(image: bytes, address: int, size: int):
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    start = address - TEXT
    decoded = list(decoder.disasm(image[start:start + size], address))
    return tuple((item.mnemonic.lower(), item.op_str.lower()) for item in decoded), sum(
        item.size for item in decoded
    )


def _decode_candidate(code: bytes):
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoded = list(decoder.disasm(code, 0))
    if sum(item.size for item in decoded) != len(code):
        raise ValueError("Compiled candidate has undecoded bytes")
    return tuple((item.mnemonic.lower(), item.op_str.lower()) for item in decoded), len(code)


def _direct_callers(image: bytes) -> tuple[int, ...]:
    found = []
    for index in range(len(image) // 4):
        word = struct.unpack_from("<I", image, index * 4)[0]
        if (word & 0x0F000000) != 0x0B000000 or (word >> 28) == 0xF:
            continue
        displacement = (word & 0x00FFFFFF) << 2
        if displacement & (1 << 25):
            displacement -= 1 << 26
        site = TEXT + index * 4
        if ((site + 8 + displacement) & U32_MASK) == ADDRESS:
            found.append(site)
    return tuple(found)


def verify_reference(image: bytes, game_info: dict, ledger: list[dict]) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if digest != game_info["code_sha256"]:
        raise ValueError("code.bin SHA-256 does not match the pinned game revision")
    row = next((item for item in ledger
                if int(item["address"], 16) == ADDRESS), None)
    if row is None or row["status"].strip() != "matching" or int(row["size"]) != FUNCTION_SIZE:
        raise ValueError("Missing matching 24-byte ledger row for 0x0034F978")
    begin = ADDRESS - TEXT
    body = image[begin:begin + FUNCTION_SIZE]
    if body != EXPECTED_BYTES:
        raise ValueError("Exact original bytes changed at 0x0034F978")
    instructions, size = _decode(image, ADDRESS, FUNCTION_SIZE)
    if instructions != EXPECTED_INSTRUCTIONS or size != FUNCTION_SIZE:
        raise ValueError(f"Original instruction sequence changed: {instructions}")

    callers = _direct_callers(image)
    if callers != (CALLER,):
        raise ValueError(f"Direct BL caller set changed: {callers}")
    caller_insns, caller_size = _decode(image, CALLER - 8, 20)
    if caller_insns != EXPECTED_CALLER or caller_size != 20:
        raise ValueError(f"Caller return-consumption window changed: {caller_insns}")
    return {
        "address": hex(ADDRESS), "size": FUNCTION_SIZE,
        "ledger_status": row["status"].strip(), "ledger_name": row["name"],
        "function_bytes_hex": body.hex(),
        "function_sha256": hashlib.sha256(body).hexdigest(),
        "instructions": [f"{mnemonic} {operands}" for mnemonic, operands in instructions],
        "direct_callers": [hex(site) for site in callers],
        "caller_window": [f"{mnemonic} {operands}" for mnemonic, operands in caller_insns],
        "caller_window_sha256": hashlib.sha256(
            image[CALLER - 8 - TEXT:CALLER - 8 - TEXT + 20]).hexdigest(),
    }


def _case(seed: int, label: str, *, base: int = DATA + 0x200,
          first: int, second: int, third: int, nzcv: int | None = None) -> Case:
    salt = sum((index + 1) * ord(char) for index, char in enumerate(label))
    rng = random.Random(seed ^ ADDRESS ^ salt)
    data = bytearray(rng.randbytes(DATA_SIZE))
    if DATA <= base and base + 16 <= DATA + DATA_SIZE:
        struct.pack_into("<III", data, base - DATA + 4,
                         0xDEADBEEF, 0xA55AA55A, 0xC001D00D)
    regs = [rng.getrandbits(32) for _ in range(13)]
    regs[0], regs[1], regs[2], regs[3] = (
        base & U32_MASK, first & U32_MASK, second & U32_MASK, third & U32_MASK
    )
    return Case(label, tuple(regs), bytes(data), rng.randbytes(STACK_SIZE),
                (rng.getrandbits(4) if nzcv is None else nzcv) << 28)


def make_cases(samples: int, seed: int):
    destination = DATA + 0x204
    boundary = (
        (0, 0, 0, "zero-all-zero"),
        (0, U32_MASK, 0x80000000, "zero-guard-no-write"),
        (1, 2, 3, "nonzero-small-ordered"),
        (0x11223344, 0x55667788, 0x99AABBCC, "three-distinct-patterns"),
        (0x80000000, U32_MASK, 0x7FFFFFFF, "unsigned-boundaries"),
        (destination, destination + 4, destination + 8, "pointer-shaped-alias-values"),
        (DATA + 0x204, DATA + 0x208, DATA + 0x20C, "values-equal-destination-slots"),
        (U32_MASK, 0, U32_MASK, "nonzero-guard-zero-payloads"),
    )
    for index, (first, second, third, label) in enumerate(boundary):
        yield _case(seed + index, label, first=first, second=second, third=third,
                    nzcv=index & 0xF)
    rng = random.Random(seed ^ ADDRESS)
    for index in range(samples):
        first = 0 if index % 2 == 0 else rng.choice((1, U32_MASK, rng.getrandbits(32)))
        yield _case(seed + 100 + index, f"random-{index}", first=first,
                    second=rng.getrandbits(32), third=rng.getrandbits(32),
                    nzcv=rng.getrandbits(4))


def _caller_case(seed: int, label: str, first: int, second: int, third: int) -> Case:
    case = _case(seed, label, first=first, second=second, third=third)
    registers = list(case.registers)
    # The caller stores through r4 only after the consumed return check. Inject
    # a mapped object value so the tested window stays within ordinary RAM.
    registers[4] = DATA + 0x180
    return Case(label, tuple(registers), case.data, case.stack, case.nzcv)


def _fault_observation(runner: Runner, case: Case) -> dict:
    result = runner.run(case)
    return {
        "faulted": result.fault is not None,
        "fault": result.fault,
        "stopped": result.stopped,
        "write_bytes": sorted(hex(address) for address in result.writes),
        "changed_tail_hex": result.data[-16:].hex(),
        "reads": sorted(hex(address) for address in result.reads),
        "pc": hex(result.pc),
        "r0": hex(result.result),
    }


def _compile_symbols(source: Path, object_path: Path) -> dict[str, bytes]:
    """Compile and validate leaf blobs, including local conditional BX LR."""
    build = compile_tu_armv6k(source, object_path, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr or "ARMv6K candidate compilation failed")
    compiled = {}
    for symbol, (code, relocations) in extract_elf_functions_detailed(object_path).items():
        if relocations:
            raise ValueError(f"Unsupported relocation in {symbol}: {relocations}")
        try:
            validate_local_blob(code)
        except ValueError as error:
            raise ValueError(f"Invalid local candidate {symbol}: {error}") from error
        compiled[symbol] = code
    return compiled


def run(code_path: Path, output: Path, samples: int = 64,
        seed: int = 20261024) -> dict:
    if samples < 0:
        raise ValueError("samples must be non-negative")
    pinned = load_pinned_reference(
        code_path, ROOT / "config/game_info.json", ROOT / "config/functions.csv"
    )
    image, game_info, ledger = pinned.image, pinned.game_info, pinned.ledger
    reference = verify_reference(image, game_info, ledger)
    output.mkdir(parents=True, exist_ok=True)
    source = ROOT / "experiments/semantic_equivalence/triple_conditional_store_candidates.cpp"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    compiled = _compile_symbols(source, output / "triple_conditional_store_candidates.o")
    required = {"candidate_0034f978", "negative_wrong_guard", "negative_wrong_offset",
                "negative_reversed_words", "negative_unconditional_store",
                "negative_two_word_store"}
    missing = required - compiled.keys()
    if missing:
        raise ValueError(f"Missing compiled symbols: {sorted(missing)}")
    original = Runner(image, ADDRESS)
    candidate_code = compiled["candidate_0034f978"]
    candidate_instructions, _ = _decode_candidate(candidate_code)
    rebuilt = Runner(image, ADDRESS, candidate_code,
                     replacement_validator=validate_local_blob)

    comparisons = []
    nzcv_matches = 0
    for case in make_cases(samples, seed):
        original_result = original.run(case)
        rebuilt_result = rebuilt.run(case)
        reason = difference(original_result, rebuilt_result, returns_value=True,
                            compare_flags=False)
        nzcv_matches += original_result.nzcv == rebuilt_result.nzcv
        comparisons.append({"case": case.label, "passed": reason is None,
                             "failure": reason,
                             "original_nzcv": hex(original_result.nzcv),
                             "candidate_nzcv": hex(rebuilt_result.nzcv),
                             "nzcv_equal": original_result.nzcv == rebuilt_result.nzcv,
                             "read_bytes": len(original_result.reads),
                             "write_bytes": len(original_result.writes)})
        if reason:
            break

    controls = (
        ("negative_wrong_guard", 0, 0x11223344, 0xAABBCCDD, "zero-guard-no-write"),
        ("negative_wrong_offset", 0x11223344, 0x55667788, 0x99AABBCC,
         "three-distinct-patterns"),
        ("negative_reversed_words", 0x11223344, 0x55667788, 0x99AABBCC,
         "three-distinct-patterns"),
        ("negative_unconditional_store", 0, U32_MASK, 0x80000000,
         "zero-guard-no-write"),
        ("negative_two_word_store", 0x11223344, 0x55667788, 0x99AABBCC,
         "three-distinct-patterns"),
    )
    negative_controls = []
    for symbol, first, second, third, label in controls:
        case = next(item for item in make_cases(0, seed) if item.label == label)
        bad = Runner(image, ADDRESS, compiled[symbol],
                     replacement_validator=validate_local_blob)
        reason = difference(original.run(case), bad.run(case), returns_value=True,
                            compare_flags=False)
        negative_controls.append({"name": symbol, "detected": reason is not None,
                                  "reason": reason})

    # Run the pinned BL and its return-value branch. The caller's CMP replaces
    # callee NZCV before BEQ, so it must not depend on the helper's flags.
    caller_windows = []
    for index, (label, first, second, third) in enumerate((
        ("zero-guard-taken", 0, 0x11223344, 0x55667788),
        ("nonzero-guard-fallthrough", 0x13579BDF, 0x2468ACE0, 0xFDB97531),
    )):
        case = _caller_case(seed + index, label, first, second, third)
        expected_stop = CALLER_CONTINUATIONS["zero" if first == 0 else "nonzero"]
        a = Runner(image, ADDRESS)
        b = Runner(image, ADDRESS, candidate_code,
                   replacement_validator=validate_local_blob)
        original_result = a.run(case, start=CALLER, stops=(expected_stop,))
        candidate_result = b.run(case, start=CALLER, stops=(expected_stop,))
        reason = difference(original_result, candidate_result, returns_value=True,
                            caller_window=True, compare_flags=True)
        caller_windows.append({"case": label, "stop": hex(expected_stop),
                               "passed": reason is None, "failure": reason,
                               "original_nzcv": hex(original_result.nzcv),
                               "candidate_nzcv": hex(candidate_result.nzcv)})

    # Probe a page-boundary write with only the first two words mapped. This
    # detects whether distinct C++ volatile STRs leave a partial footprint
    # unlike the original STM; any mismatch is reported and excluded from the
    # in-bounds equivalence claim.
    fault_case = _case(seed, "fault-third-word-unmapped",
                       base=DATA + DATA_SIZE - 12, first=0x11223344,
                       second=0x55667788, third=0x99AABBCC, nzcv=0)
    fault_original = Runner(image, ADDRESS)
    fault_candidate = Runner(image, ADDRESS, candidate_code,
                             replacement_validator=validate_local_blob)
    fault_a = _fault_observation(fault_original, fault_case)
    fault_b = _fault_observation(fault_candidate, fault_case)
    fault_footprint_equal = (
        fault_a["faulted"] == fault_b["faulted"]
        and fault_a["write_bytes"] == fault_b["write_bytes"]
        and fault_a["changed_tail_hex"] == fault_b["changed_tail_hex"]
        and fault_a["reads"] == fault_b["reads"]
    )

    if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("Candidate source changed during experiment")
    compiler = subprocess.run([str(find_clang()), "--version"], capture_output=True,
                              text=True, check=True)
    passed = (all(item["passed"] for item in comparisons)
              and all(item["detected"] for item in negative_controls)
              and all(item["passed"] for item in caller_windows))
    report = {
        "schema": 1, "passed": passed,
        "scope": "0x0034F978 conditional three-word store; aligned, in-bounds ordinary RAM",
        "reference_sha256": hashlib.sha256(image).hexdigest(),
        "reference": reference,
        "source_sha256": source_hash,
        "object_sha256": hashlib.sha256((output / "triple_conditional_store_candidates.o").read_bytes()).hexdigest(),
        "candidate_bytes": len(candidate_code),
        "candidate_instructions": [f"{mnemonic} {operands}"
                                    for mnemonic, operands in candidate_instructions],
        "store_strategy": "three separately emitted conditional STR instructions",
        "compiler": compiler.stdout.splitlines()[0],
        "seed": seed, "random_cases": samples,
        "functional_cases": len(comparisons), "functional_comparisons": comparisons,
        "nzcv": {"equal_cases": nzcv_matches, "total_cases": len(comparisons),
                 "callee_flags_are_not_part_of_the_AAPCS_return_contract": True,
                 "caller_cmp_overwrites_flags_before_beq": True},
        "verified_callers": {hex(CALLER): {
            "instructions": [f"{mnemonic} {operands}" for mnemonic, operands in EXPECTED_CALLER],
            "meaning": "Caller saves its frame, preserves r1-r3 through BL, then consumes r0 with CMP/BEQ; it does not consume callee NZCV."}},
        "caller_windows": caller_windows,
        "negative_controls": negative_controls,
        "fault_probe": {"original": fault_a, "candidate": fault_b,
                        "footprint_equal": fault_footprint_equal,
                        "equivalence_claimed": False,
                        "scope_note": "The fault probe is diagnostic only and is excluded from pass/fail for the in-bounds RAM contract."},
        "limitations": [
            "Differential evidence is bounded testing, not a formal equivalence proof or gameplay trace",
            "The one direct caller is manually pinned at its BL and immediate CMP/BEQ consumer; argument setup before BL is not executed",
            "Caller window uses injected register values and synthetic mapped RAM, not live allocator/global state",
            "Only aligned, in-bounds ordinary RAM is in the positive equivalence claim; MMIO, concurrency and unaligned access are excluded",
            "Candidate emits separate volatile stores; STM multi-register atomicity, precise exception behavior and partial-fault ordering are not claimed even when this diagnostic footprint happens to match",
            "NZCV is observed and reported but is not an AAPCS return-value contract; caller comparison overwrites it before use",
            "No production source, ledger, game image, emulator, patch or save data is changed",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Triple conditional-store experiment {'PASS' if passed else 'FAIL'}; report: {output / 'report.json'}", flush=True)
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/semantic-equivalence/triple-conditional-store-seed20261024")
    parser.add_argument("--samples", type=int, default=64)
    parser.add_argument("--seed", type=int, default=20261024)
    args = parser.parse_args()
    try:
        result = run(args.code, args.output, args.samples, args.seed)
    except (RuntimeError, ValueError, OSError) as error:
        parser.exit(2, f"Experiment error: {error}\n")
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
