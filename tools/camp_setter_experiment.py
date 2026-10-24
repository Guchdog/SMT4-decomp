#!/usr/bin/env python3
"""Differentially test two bounded CAMP byte/halfword setter leaves."""
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
from tools.build_check import find_clang
from tools.semantic_experiment import DATA, DATA_SIZE, STACK_SIZE, TEXT, Case, Runner, difference
from tools.semantic_experiment_support import (
    compile_candidate_symbols,
    load_pinned_reference,
)

FUNCTIONS = {
    0x003C8FC8: {"byte_offset": 0x136, "halfword_offsets": (0x138, 0x13A)},
    0x003C9314: {"byte_offset": 0x13C, "halfword_offsets": (0x13E, 0x140)},
}
# Manually checked direct ARM BL sites in Unite_DrawAndCalc (0x001de238,
# 5020 bytes). The scan in the review scaffold missed these, so this experiment
# pins the exact callsites itself and does not treat scan absence as evidence.
CALLERS = {
    0x003C8FC8: (0x001DE340, 0x001DE51C),
    0x003C9314: (0x001DE364, 0x001DE530),
}
CALLER_FUNCTION = (0x001DE238, 5020, "Unite_DrawAndCalc")
U32_MASK = 0xFFFFFFFF
BASE_OFFSETS = (0x100, 0x280, 0x500)
HALFWORD_BOUNDARIES = (0, 1, 0x7FFF, 0x8000, 0xFFFF, 0x1234, 0xABCD)


def _decode(image: bytes, address: int, size: int):
    offset = address - TEXT
    if offset < 0 or offset + size > len(image):
        raise ValueError(f"instruction range outside image at {address:#010x}")
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoded = list(decoder.disasm(image[offset:offset + size], address))
    if sum(item.size for item in decoded) != size:
        raise ValueError(f"incomplete ARM decode at {address:#010x}")
    return tuple((item.mnemonic.lower(), item.op_str.lower()) for item in decoded)


def _direct_callers(image: bytes, targets: set[int]) -> dict[int, tuple[int, ...]]:
    found = {target: [] for target in targets}
    for index in range(len(image) // 4):
        word = struct.unpack_from("<I", image, index * 4)[0]
        if (word & 0x0F000000) != 0x0B000000 or (word >> 28) == 0xF:
            continue
        displacement = (word & 0x00FFFFFF) << 2
        if displacement & (1 << 25):
            displacement -= 1 << 26
        site = TEXT + index * 4
        target = (site + 8 + displacement) & U32_MASK
        if target in found:
            found[target].append(site)
    return {address: tuple(sites) for address, sites in found.items()}


def verify_reference(image: bytes, game_info: dict, ledger: list[dict]) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if digest != game_info["code_sha256"]:
        raise ValueError("code.bin SHA-256 does not match configured game revision")
    by_address = {int(row["address"], 16): row for row in ledger}
    function_evidence = {}
    for address, spec in FUNCTIONS.items():
        row = by_address.get(address)
        if row is None or row["status"].strip() != "matching" or int(row["size"]) != 20:
            raise ValueError(f"Missing matching 20-byte ledger row at {address:#010x}")
        byte, (half0, half1) = spec["byte_offset"], spec["halfword_offsets"]
        expected = (
            ("add", "ip, r0, #0x100"),
            ("strb", f"r1, [r0, #0x{byte:x}]"),
            ("strh", f"r2, [ip, #0x{half0 - 0x100:x}]"),
            ("strh", f"r3, [ip, #0x{half1 - 0x100:x}]"),
            ("bx", "lr"),
        )
        actual = _decode(image, address, 20)
        if actual != expected:
            raise ValueError(f"Instruction drift at {address:#010x}: {actual}")
        function_evidence[hex(address)] = {
            "name": row["name"], "category": row["category"], "size": 20,
            "sha256": hashlib.sha256(image[address - TEXT:address - TEXT + 20]).hexdigest(),
            "instructions": [f"{mnemonic} {operands}" for mnemonic, operands in actual],
            "bounded_effects": [
                {"width_bits": 8, "offset": hex(byte), "value_register": "r1 low 8 bits", "order": 1},
                {"width_bits": 16, "offset": hex(half0), "value_register": "r2 low 16 bits", "order": 2},
                {"width_bits": 16, "offset": hex(half1), "value_register": "r3 low 16 bits", "order": 3},
            ],
            "observed_return": "r0 unchanged; no explicit return-value construction",
        }

    caller_set = _direct_callers(image, set(FUNCTIONS))
    caller_evidence = {}
    caller_start, caller_size, caller_name = CALLER_FUNCTION
    caller_row = by_address.get(caller_start)
    if (caller_row is None or int(caller_row["size"]) != caller_size
            or caller_row["name"] != caller_name):
        raise ValueError("Pinned caller function ledger row changed")
    for address, sites in CALLERS.items():
        if caller_set[address] != sites:
            raise ValueError(f"Direct caller set changed at {address:#010x}: {caller_set[address]}")
        for site in sites:
            expected = (("bl", f"#0x{address:x}"),)
            if _decode(image, site, 4) != expected:
                raise ValueError(f"Pinned caller BL changed at {site:#010x}")
            # Pin adjacent instructions so manual inspection evidence remains
            # reviewable; they are not executed before the bounded call window.
            caller_evidence[hex(site)] = {
                "callee": hex(address), "function": caller_name,
                "function_address": hex(caller_start),
                "preceding_4_instructions": [
                    f"{mnemonic} {operands}" for mnemonic, operands in _decode(image, site - 16, 16)
                ],
                "following_4_instructions": [
                    f"{mnemonic} {operands}" for mnemonic, operands in _decode(image, site + 4, 16)
                ],
                "execution_scope": "BL through return to BL+4; preceding setup is inspected but not executed",
            }
    return {
        "code_sha256": digest, "functions": function_evidence,
        "caller_function": {"address": hex(caller_start), "size": caller_size,
                            "name": caller_name},
        "direct_callers": {hex(address): [hex(site) for site in sites]
                           for address, sites in caller_set.items()},
        "caller_windows": caller_evidence,
    }


def _make_case(address: int, seed: int, label: str, index: int,
               byte_value: int, half0: int, half1: int) -> Case:
    rng = random.Random(seed ^ address ^ sum((i + 1) * ord(c) for i, c in enumerate(label)))
    data = bytearray(rng.randbytes(DATA_SIZE))
    base = DATA + BASE_OFFSETS[index % len(BASE_OFFSETS)]
    registers = [rng.getrandbits(32) for _ in range(13)]
    registers[0] = base
    registers[1] = byte_value & U32_MASK
    registers[2] = half0 & U32_MASK
    registers[3] = half1 & U32_MASK
    return Case(label, tuple(registers), bytes(data), rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)


def make_cases(address: int, samples: int, seed: int):
    # Exhaust every low-byte input. Sweep halfword edge patterns independently
    # and pair every edge with a different second halfword to catch swaps.
    index = 0
    for value in range(256):
        half0 = HALFWORD_BOUNDARIES[value % len(HALFWORD_BOUNDARIES)]
        half1 = HALFWORD_BOUNDARIES[(value * 3 + 1) % len(HALFWORD_BOUNDARIES)]
        yield _make_case(address, seed, f"byte-{value:02x}", index, value, half0, half1)
        index += 1
    for j, half0 in enumerate(HALFWORD_BOUNDARIES):
        for half1 in HALFWORD_BOUNDARIES:
            yield _make_case(address, seed, f"halfword-{j}-{half1:04x}", index,
                             (j * 43 + half1) & 0xFF, half0, half1)
            index += 1
    rng = random.Random(seed ^ address ^ 0xCA6F)
    for j in range(samples):
        yield _make_case(address, seed, f"random-{j}", index,
                         rng.getrandbits(32), rng.getrandbits(32), rng.getrandbits(32))
        index += 1


def _caller_case(address: int, seed: int, site: int) -> Case:
    rng = random.Random(seed ^ site)
    return _make_case(address, seed, f"caller-{site:08x}", site,
                      rng.getrandbits(32), rng.getrandbits(32), rng.getrandbits(32))


def _assert_candidate_order(code: bytes, address: int, spec: dict) -> list[str]:
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoded = list(decoder.disasm(code, address))
    if not decoded or decoded[-1].mnemonic != "bx" or decoded[-1].op_str != "lr":
        raise ValueError(f"candidate {address:#010x} does not return with bx lr")
    stores = [item for item in decoded if item.mnemonic.startswith("str")]
    if len(stores) != 3 or [item.mnemonic for item in stores] != ["strb", "strh", "strh"]:
        raise ValueError(f"candidate {address:#010x} changed store widths/order")
    # Clang may form temporary base registers, so effective-address details are
    # checked by differential execution; this independently pins width/order.
    return [f"{item.mnemonic} {item.op_str}".strip() for item in decoded]


def run(code_path: Path, output: Path, samples: int = 128,
        seed: int = 20261024) -> dict:
    if samples < 0:
        raise ValueError("samples must be non-negative")
    reference_input = load_pinned_reference(
        code_path, ROOT / "config/game_info.json", ROOT / "config/functions.csv"
    )
    image, game_info, ledger = (reference_input.image, reference_input.game_info,
                                reference_input.ledger)
    reference = verify_reference(image, game_info, ledger)
    output.mkdir(parents=True, exist_ok=False)
    source_path = ROOT / "experiments/semantic_equivalence/camp_setter_candidates.cpp"
    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    required = {f"candidate_{address:08x}" for address in FUNCTIONS}
    required |= {"negative_camp_wrong_byte_offset", "negative_camp_swapped_halfwords"}
    compiled = compile_candidate_symbols(
        source_path, output / "camp_setter_candidates.o", ROOT, required
    )

    function_results = []
    for address, spec in FUNCTIONS.items():
        symbol = f"candidate_{address:08x}"
        candidate_code = compiled[symbol]
        candidate_disassembly = _assert_candidate_order(candidate_code, address, spec)
        original, candidate = Runner(image, address), Runner(image, address, candidate_code)
        count = 0
        failure = None
        for case in make_cases(address, samples, seed):
            reason = difference(original.run(case), candidate.run(case),
                                returns_value=True, compare_flags=True)
            count += 1
            if reason:
                failure = {"case": case.label, "reason": reason}
                break
        function_results.append({
            "address": hex(address), "original_bytes": 20,
            "candidate_bytes": len(candidate_code), "candidate_instructions": candidate_disassembly,
            "cases": count, "passed": failure is None, "failure": failure,
        })

    caller_results = []
    for address, sites in CALLERS.items():
        symbol = f"candidate_{address:08x}"
        for site in sites:
            original = Runner(image, address)
            candidate = Runner(image, address, compiled[symbol])
            case = _caller_case(address, seed, site)
            stop = site + 4
            baseline = original.run(case, start=site, stops=(stop,), budget=16)
            rebuilt = candidate.run(case, start=site, stops=(stop,), budget=16)
            reason = difference(baseline, rebuilt, returns_value=False,
                                caller_window=True, compare_flags=True)
            caller_results.append({"callee": hex(address), "callsite": hex(site),
                                   "stop": hex(stop), "cases": 1,
                                   "passed": reason is None, "reason": reason})

    negative_controls = []
    control_cases = (
        (0x003C8FC8, "negative_camp_wrong_byte_offset"),
        (0x003C8FC8, "negative_camp_swapped_halfwords"),
    )
    for address, symbol in control_cases:
        case = _make_case(address, seed, f"negative-{symbol}", 0x70,
                          0xA5, 0x1234, 0xFEDC)
        outcome = difference(Runner(image, address).run(case),
                             Runner(image, address, compiled[symbol]).run(case),
                             returns_value=True, compare_flags=True)
        negative_controls.append({"name": symbol, "address": hex(address),
                                  "detected": outcome is not None, "reason": outcome})

    if hashlib.sha256(source_path.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("Candidate source changed during experiment")
    compiler = subprocess.run([str(find_clang()), "--version"], capture_output=True,
                              text=True, check=True)
    passed = (all(result["passed"] for result in function_results)
              and all(result["passed"] for result in caller_results)
              and all(result["detected"] for result in negative_controls))
    report = {
        "schema": 1, "experiment": "two_camp_fixed_byte_halfword_setters",
        "passed": passed,
        "scope": "Two isolated CAMP leaves and four manually pinned BL-through-return windows",
        "reference": reference, "source_sha256": source_hash,
        "compiler": compiler.stdout.splitlines()[0], "unicorn": __import__("unicorn").__version__,
        "seed": seed, "random_samples_per_function": samples,
        "function_comparisons": sum(result["cases"] for result in function_results),
        "caller_comparisons": sum(result["cases"] for result in caller_results),
        "functions": function_results, "caller_results": caller_results,
        "negative_controls": negative_controls,
        "limitations": [
            "Evidence proves only the three ordered writes at the pinned offsets and unchanged r0 at return; it does not prove CAMP field names, higher-level meaning, or interchangeable contracts.",
            "Function cases use aligned bases in ordinary RAM; unaligned halfword behavior, MMIO, concurrent observers, exceptions, and partial faults are untested.",
            "Caller windows begin at the pinned BL and end at BL+4; argument setup is manually inspected and pinned but not executed by this harness.",
            "Two seeds and these directed/random cases are bounded differential evidence, not formal or whole-game equivalence.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=128)
    parser.add_argument("--seed", type=int, default=20261024)
    args = parser.parse_args()
    try:
        report = run(args.code, args.output, args.samples, args.seed)
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(2, f"Experiment error: {error}\n")
    print(json.dumps({"passed": report["passed"],
                      "function_comparisons": report["function_comparisons"],
                      "caller_comparisons": report["caller_comparisons"],
                      "negative_controls": report["negative_controls"]}, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
