#!/usr/bin/env python3
"""Build and offline-validate an IPS for the two production script getters.

This stages code.bin/IPS artifacts only. It never launches an emulator.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import struct
import sys
from pathlib import Path

import capstone

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.h18_script_word_getters_production import (
    CALLER_PAIRS, EXPECTED_BYTE_OFFSETS, HALFWORDS, _case, _ordinary_ram_difference,
    _run_full, compile_production_symbols, verify_reference,
)
from tools.semantic_experiment import DATA, TEXT, Runner
SEEDS = (7, 20261024)
SAMPLES = 64
U32_MASK = 0xFFFFFFFF


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _encode_ips(records: list[tuple[int, bytes]], image_size: int) -> bytes:
    out = bytearray(b"PATCH")
    previous_end = -1
    for offset, payload in sorted(records):
        if offset < 0 or offset >= 0x1000000 or not payload or len(payload) >= 0x10000:
            raise ValueError("invalid IPS record bounds")
        if offset < previous_end or offset + len(payload) > image_size:
            raise ValueError("overlapping or out-of-image IPS record")
        out.extend(offset.to_bytes(3, "big"))
        out.extend(len(payload).to_bytes(2, "big"))
        out.extend(payload)
        previous_end = offset + len(payload)
    out.extend(b"EOF")
    return bytes(out)


def _apply_ips(image: bytes, patch: bytes) -> bytes:
    if not patch.startswith(b"PATCH"):
        raise ValueError("bad IPS signature")
    out = bytearray(image)
    cursor = 5
    while True:
        if cursor + 3 > len(patch):
            raise ValueError("truncated IPS")
        if patch[cursor:cursor + 3] == b"EOF":
            if cursor + 3 != len(patch):
                raise ValueError("unexpected IPS trailing bytes")
            return bytes(out)
        offset = int.from_bytes(patch[cursor:cursor + 3], "big")
        cursor += 3
        if cursor + 2 > len(patch):
            raise ValueError("missing IPS record length")
        length = int.from_bytes(patch[cursor:cursor + 2], "big")
        cursor += 2
        if length == 0:
            raise ValueError("RLE records are not emitted by this task")
        if cursor + length > len(patch) or offset + length > len(out):
            raise ValueError("truncated/out-of-image IPS payload")
        out[offset:offset + length] = patch[cursor:cursor + length]
        cursor += length


def _decode_arm_leaf(code: bytes, address: int) -> list[dict]:
    if len(code) > 12 or len(code) % 4:
        raise ValueError(f"ARM body at {address:#x} does not fit its 12-byte slot")
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoder.detail = True
    instructions = list(decoder.disasm(code, address))
    if not instructions or sum(i.size for i in instructions) != len(code):
        raise ValueError(f"incomplete ARM disassembly at {address:#x}")
    if instructions[-1].mnemonic != "bx" or instructions[-1].op_str != "lr":
        raise ValueError(f"ARM body at {address:#x} must return through bx lr")
    if any(i.group(capstone.CS_GRP_CALL) for i in instructions):
        raise ValueError("replacement leaf unexpectedly contains a call")
    return [{"address": hex(i.address), "mnemonic": i.mnemonic, "operands": i.op_str}
            for i in instructions]


def _check_callsite(image: bytes, site: int, target: int) -> None:
    word = struct.unpack_from("<I", image, site - TEXT)[0]
    if word >> 24 != 0xEB:
        raise ValueError(f"expected ARM BL at {site:#x}, got {word:#010x}")
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm -= 1 << 24
    actual = site + 8 + imm * 4
    if actual != target or actual & 3:
        raise ValueError(f"BL at {site:#x} targets {actual:#x}, expected ARM entry {target:#x}")


def _make_cases(address: int, seed: int, samples: int):
    for index, value in enumerate(HALFWORDS):
        yield _case(address, seed, index, value)
    for index in range(samples):
        value = random.Random(seed ^ address ^ index).getrandbits(16)
        yield _case(address, seed, len(HALFWORDS) + index, value)


def _direct_diff(original_image: bytes, patched_image: bytes, address: int,
                 seed: int, samples: int) -> dict:
    results = []
    for case in _make_cases(address, seed, samples):
        original, original_state = _run_full(Runner(original_image, address), case)
        patched, patched_state = _run_full(Runner(patched_image, address), case)
        reason = _ordinary_ram_difference(original, patched, original_state, patched_state)
        results.append({"case": case.label, "passed": reason is None, "reason": reason})
        if reason:
            break
    return {"address": hex(address), "cases": len(results),
            "passed": all(x["passed"] for x in results), "results": results}


def _caller_diff(original_image: bytes, patched_image: bytes, seed: int) -> list[dict]:
    output = []
    for index, window in enumerate(CALLER_PAIRS):
        address = 0x002345FC
        case = _case(address, seed, 100 + index, 0x005E)
        regs = list(case.registers)
        regs[window["base_reg"]] = DATA + 0x100
        data = bytearray(case.data)
        field_base = DATA + 0x100 + 0x28
        struct.pack_into("<H", data, field_base - DATA + 0x48, 0x00D3)
        struct.pack_into("<H", data, field_base - DATA + 0x4A, 0x005E)
        case = case.__class__(case.label, tuple(regs), bytes(data), case.stack, case.nzcv)
        start = window["halfword_call"] - 4
        stop = window["stop"]
        _check_callsite(original_image, window["halfword_call"], 0x002345FC)
        _check_callsite(original_image, window["byte_call"], 0x002345F0)
        a, as_ = _run_full(Runner(original_image, 0x002345FC), case,
                           start=start, stops=(stop,))
        b, bs = _run_full(Runner(patched_image, 0x002345FC), case,
                           start=start, stops=(stop,))
        reason = _ordinary_ram_difference(a, b, as_, bs, returns_value=False,
                                          caller_window=True)
        expected = (0xD3, 0x5E)
        actual = (bs["r0_r12"][2], bs["r0_r12"][3])
        if reason is None and actual != expected:
            reason = f"caller did not consume expected (r2,r3): {actual!r}"
        output.append({"caller": window["caller"],
                       "call_sites": [hex(window["halfword_call"]), hex(window["byte_call"])],
                       "start": hex(start), "stop": hex(stop), "passed": reason is None,
                       "reason": reason, "cases": 1,
                       "expected_consumed_r2_r3": [hex(v) for v in expected],
                       "candidate_consumed_r2_r3": [hex(v) for v in actual],
                       "original_reads": sorted(hex(v) for v in a.reads),
                       "patched_reads": sorted(hex(v) for v in b.reads)})
    return output


def _negative_controls(original_image: bytes, patched_image: bytes, seed: int,
                       compiled: dict[int, bytes]) -> list[dict]:
    # The sibling getter is a wrong-offset replacement for f0. A direct LDRH
    # without the low-byte mask is the omitted-mask mutant. Both mutate an
    # actual patched-image entry and execute through the pinned entry address.
    controls = []
    case = _case(0x002345F0, seed, 0, 0x80FF)
    mutants = (
        ("wrong_offset", compiled[0x002345FC]),
        ("omitted_mask", bytes.fromhex("b804d0e11eff2fe1")),
    )
    for name, code in mutants:
        mutant_image = bytearray(patched_image)
        offset = 0x002345F0 - TEXT
        mutant_image[offset:offset + len(code)] = code
        a, as_ = _run_full(Runner(original_image, 0x002345F0), case)
        b, bs = _run_full(Runner(bytes(mutant_image), 0x002345F0), case)
        reason = _ordinary_ram_difference(a, b, as_, bs)
        controls.append({"name": name, "detected": reason is not None, "reason": reason})
    return controls


def stage(code_path: Path, output: Path, samples: int = SAMPLES) -> dict:
    if samples < 0:
        raise ValueError("samples must be nonnegative")
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(f"output must be fresh: {output}")
    output.mkdir(parents=True)
    source_path = ROOT / "src/engine/leaf_matching.cpp"
    source_hash_before = sha256(source_path.read_bytes())
    original = Path(code_path).read_bytes()
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    ref_hash = sha256(original)
    if len(original) != game["code_bin_size"] or ref_hash != game["code_sha256"]:
        raise ValueError("original code.bin does not match configured pinned revision")
    if int(game["segments"]["text"]["vaddr"], 16) != TEXT or int(
            game["segments"]["text"]["file_offset"], 16) != 0:
        raise ValueError("unexpected text address/file-offset mapping")
    references = verify_reference(code_path, ROOT / "config/game_info.json",
                                  ROOT / "config/functions.csv")
    if references["interior_branch_refs"]:
        raise ValueError(f"direct branches target inside getter spans: {references['interior_branch_refs']}")
    for entry, details in references["external_references"].items():
        if len(details["branches"]) != 16 or details["pointer_words"]:
            raise ValueError(f"unexpected caller/pointer inventory at {entry}: {details}")

    compile_dir = output / "compile"
    compile_dir.mkdir()
    compiled, source_hash, object_hash = compile_production_symbols(compile_dir)
    if source_hash != source_hash_before:
        raise RuntimeError("production source changed during compilation")
    code_records = {}
    disassemblies = {}
    patched = bytearray(original)
    for address, slot_size in ((0x002345F0, 12), (0x002345FC, 12)):
        code = compiled[address]
        disassemblies[hex(address)] = _decode_arm_leaf(code, address)
        if len(code) != 8:
            raise ValueError(f"expected compact 8-byte getter at {address:#x}, got {len(code)}")
        start = address - TEXT
        end = start + slot_size
        if end > len(original):
            raise ValueError("getter slot is outside code.bin")
        if patched[start + len(code):end] != original[start + len(code):end]:
            raise ValueError("tail window changed before patching")
        patched[start:start + len(code)] = code
        code_records[hex(address)] = {"file_offset": hex(start), "slot_size": slot_size,
                                      "compiled_size": len(code), "bytes_hex": code.hex(),
                                      "retained_tail_hex": original[start + len(code):end].hex()}
    final_image = bytes(patched)
    records = []
    for address in (0x002345F0, 0x002345FC):
        start = address - TEXT
        records.append((start, final_image[start:start + 8]))
    ips = _encode_ips(records, len(original))
    if _apply_ips(original, ips) != final_image:
        raise ValueError("IPS round trip did not reproduce the patched code image")
    stage_dir = output / "stage"
    stage_dir.mkdir()
    final_path = stage_dir / "getters-patched.code.bin"
    ips_path = stage_dir / "getters-patched.code.ips"
    final_path.write_bytes(final_image)
    ips_path.write_bytes(ips)

    per_seed = []
    for seed in SEEDS:
        funcs = [_direct_diff(original, final_image, address, seed, samples)
                 for address in (0x002345F0, 0x002345FC)]
        callers = _caller_diff(original, final_image, seed)
        controls = _negative_controls(original, final_image, seed, compiled)
        report = {"seed": seed, "reference_sha256": ref_hash,
                  "patched_image_sha256": sha256(final_image), "ips_sha256": sha256(ips),
                  "production_source_sha256": source_hash, "production_object_sha256": object_hash,
                  "functions": funcs, "caller_windows": callers, "negative_controls": controls,
                  "passed": all(x["passed"] for x in funcs)
                            and all(x["passed"] for x in callers)
                            and all(x["detected"] for x in controls),
                  "limits": ["Aligned, side-effect-free ordinary RAM only; original LDRH reads two bytes while production candidate LDRB reads one.",
                             "Each of four representative caller windows executes one paired use and stops before the next external helper; full callers and unobserved pointer shapes are not covered.",
                             "Offline ARM11 Unicorn evidence only; no Azahar launch or in-game runtime scenario."]}
        seed_dir = output / f"seed-{seed}"
        seed_dir.mkdir()
        (seed_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        per_seed.append(report)
    if sha256(source_path.read_bytes()) != source_hash:
        raise RuntimeError("production source changed during staged validation")

    manifest = {"schema": 1, "addresses": code_records, "arm_disassembly": disassemblies,
                "original_path": str(Path(code_path).resolve()), "original_sha256": ref_hash,
                "patched_image_path": str(final_path.resolve()), "patched_image_sha256": sha256(final_image),
                "ips_path": str(ips_path.resolve()), "ips_sha256": sha256(ips),
                "ips_records": [{"file_offset": hex(o), "length": len(b), "bytes_hex": b.hex()}
                                for o, b in records],
                "ips_round_trip": True, "direct_branch_inventory": references["external_references"],
                "interior_branch_refs": references["interior_branch_refs"],
                "pointer_words": {k: v["pointer_words"] for k, v in references["external_references"].items()},
                "source_sha256": source_hash, "object_sha256": object_hash,
                "seed_reports": [{"path": str((output / f"seed-{r['seed']}" / "report.json").resolve()),
                                  "sha256": sha256((output / f"seed-{r['seed']}" / "report.json").read_bytes()),
                                  "passed": r["passed"]} for r in per_seed],
                "passed": all(r["passed"] for r in per_seed),
                "emulator_launched": False}
    manifest_path = stage_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path, required=True,
                        help="must be a fresh output directory under the assigned run")
    parser.add_argument("--samples", type=int, default=SAMPLES)
    args = parser.parse_args()
    report = stage(args.code, args.output, args.samples)
    print(json.dumps({"passed": report["passed"], "patched_image": report["patched_image_path"],
                      "ips": report["ips_path"], "manifest": str(Path(args.output) / "stage/manifest.json")}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
