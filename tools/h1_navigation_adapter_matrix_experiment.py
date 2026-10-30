"""Exhaustive private caller-window matrix for the H1 navigation adapter."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools import h1_navigation_adapter_experiment as base
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang, get_armv6k_flags

IMAGE = ROOT / "extracted/exefs/code.bin"
ADAPTER_SOURCE = ROOT / "experiments/semantic_equivalence/h1_navigation_adapter_candidate.cpp"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
ADAPTER_SHA = "95bba0be4c59445eca0ca72c16c4b486c0737befd49ab0e60716a2c112d818ad"
TRIGGER_IDS = base.TRIGGER_IDS
MASK_BIT_FOR_TRIGGER = {logical_id: index for index, logical_id in enumerate(TRIGGER_IDS)}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_metadata(output: Path, object_path: Path) -> dict:
    clang = find_clang()
    argv = [str(clang), *get_armv6k_flags(ROOT, clang), "-MD", "-MF",
            str(object_path.with_suffix(object_path.suffix + ".d")), "-MT", "object",
            "-c", str(ADAPTER_SOURCE.resolve()), "-o", str(object_path.resolve())]
    return {"argv": argv, "exit_code": 0, "source_sha256": sha(ADAPTER_SOURCE.read_bytes()),
            "object_sha256": sha(object_path.read_bytes()), "object_path": str(object_path)}


def run_machine(machine: base.AdapterMachine, cursor: int, cached: int, ready=(1, 1),
                responses=None, *, adapter_patched=False, blend=1.5) -> dict:
    initial = machine.initialize(cursor, cached, ready, responses, blend=blend)
    machine.stop_addresses = (base.GATE_EXIT, base.TOUCH_STOP)
    try:
        machine.uc.emu_start(base.CALLBACK_START, 0, count=5000)
        fault = None
    except machine.unicorn.UcError as error:
        fault = str(error)
    work = bytes(machine.uc.mem_read(base.WORK, base.WORK_SIZE))
    mutated_work = bytes(machine.uc.mem_read(base.MUTATED_WORK, base.WORK_SIZE))
    return {"fault": fault, "mode": "adapter" if adapter_patched else "original",
            "stop": machine.uc.reg_read(machine.arm.UC_ARM_REG_PC),
            "state": machine.snapshot(), "mailbox": base.read_u32(machine.uc, base.MAILBOX),
            "work_hex": work.hex(), "mutated_work_hex": mutated_work.hex(),
            "initial_work_hex": initial["work"].hex(),
            "initial_mutated_work_hex": initial["mutated_work"].hex(),
            "work_sha256": sha(work), "mutated_work_sha256": sha(mutated_work),
            "slot": hex(base.read_u32(machine.uc, base.WORK_SLOT)),
            "ready_calls": list(machine.ready_calls), "trigger_calls": list(machine.trigger_calls),
            "event_calls": list(machine.event_calls), "timeline": list(machine.timeline),
            "hook_error": machine.hook_error}


def patch_inline_window(machine: base.AdapterMachine):
    code = bytearray(machine.uc.mem_read(base.TEXT, 0x400000))
    struct.pack_into("<I", code, base.CALLBACK_START - base.TEXT,
                     base.branch_word(base.CALLBACK_START, base.INJECT))
    machine.uc.mem_write(base.TEXT, bytes(code))


def compact_observations(run: dict) -> dict:
    return {
        "readiness": [{"entry": item["entry"], "result": item["result"]}
                      for item in run["ready_calls"]],
        "triggers": [{"logical_id": item["logical_id"],
                      "arguments": [hex(item["r0"])], "result": item["result"]}
                     for item in run["trigger_calls"]],
        "events": [{"arguments": [hex(item["event_id"])],
                    "selection_seen": item["work_selection"],
                    "cached_seen": item["work_cached"]}
                   for item in run["event_calls"]],
    }


def compare_row(original: dict, candidate: dict, label: str, ready, *, cursor: int | None = None,
                cached: int | None = None, mask: int | None = None) -> dict:
    comparison = base.compare(original, candidate, label, ready)
    original_work = bytes.fromhex(original["work_hex"])
    candidate_work = bytes.fromhex(candidate["work_hex"])
    original_post = {"selection": struct.unpack_from("<I", original_work, 8)[0],
                     "cached": struct.unpack_from("<I", original_work, 12)[0]}
    candidate_post = {"selection": struct.unpack_from("<I", candidate_work, 8)[0],
                      "cached": struct.unpack_from("<I", candidate_work, 12)[0]}
    row = {
        "case": label, "passed": comparison["passed"],
        "input": {"cursor": cursor, "cached": cached,
                  "ready": list(ready), "mask": mask,
                  "responses": ({key: int(bool(mask & (1 << bit)))
                                 for key, bit in MASK_BIT_FOR_TRIGGER.items()} if mask is not None else {})},
        "stop": {"expected": comparison["expected_stop"],
                 "original": comparison["original_stop"], "adapter": comparison["adapter_stop"]},
        "faults": {"original": original["fault"], "adapter": candidate["fault"]},
        "selection_cache": {"original_after": original_post, "adapter_after": candidate_post},
        "registers_match": comparison["registers_match"],
        "sp_aligned": comparison["sp_aligned"],
        "live_registers": {key: comparison[key] for key in
                            ("original_r4", "adapter_r4", "original_r8", "adapter_r8",
                             "original_s17", "adapter_s17", "original_r6", "adapter_r6")},
        "memory_match": comparison["memory_match"],
        "work_sha256": {"original": original["work_sha256"], "adapter": candidate["work_sha256"]},
        "slot": {"original": original["slot"], "adapter": candidate["slot"]},
        "mailbox": candidate["mailbox"],
        # Store the actual ordered original observations once; the paired
        # adapter trace is compared in-process and its equality is recorded.
        "ordered_observations": compact_observations(original),
        "ordered_observations_match": compact_observations(original) == compact_observations(candidate),
        "helper_order_match": comparison["helper_order_match"],
        "event_observation_match": comparison["event_observation_match"],
        "changed_work_offsets": comparison["changed_offsets"],
    }
    if not row["passed"]:
        row["mismatch_summary"] = {
            "work_differs": not comparison["memory_match"],
            "register_differs": not comparison["registers_match"],
            "call_order_differs": not comparison["helper_order_match"],
            "event_differs": not comparison["event_observation_match"],
            "r4_differs": comparison["original_r4"] != comparison["adapter_r4"],
            "r8_differs": comparison["original_r8"] != comparison["adapter_r8"],
            "s17_differs": comparison["original_s17"] != comparison["adapter_s17"],
        }
    return row


def compile_wrong_normalizer(output: Path) -> tuple[bytes, dict]:
    output.mkdir(parents=True, exist_ok=True)
    source_text = ADAPTER_SOURCE.read_text(encoding="utf-8")
    anchor = "return adjusted - multiple;"
    if source_text.count(anchor) != 1:
        raise ValueError("normalizer negative-control anchor is not unique")
    mutant = output / "navigation_adapter_wrong_signed_modulo.cpp"
    mutant.write_text(source_text.replace(anchor,
        "return static_cast<u32>(static_cast<s32>(provisional) % 4);"), encoding="utf-8")
    obj = output / "navigation_adapter_wrong_signed_modulo.o"
    build = compile_tu_armv6k(mutant, obj, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr or "normalizer mutant compilation failed")
    funcs = extract_elf_functions_detailed(obj)
    symbol = "h1_navigation_adapter_candidate"
    if symbol not in funcs:
        raise ValueError("mutated object is missing adapter entry")
    code, relocations = funcs[symbol]
    if relocations:
        raise ValueError(f"unsupported mutant adapter relocations: {relocations}")
    validation = base.validate_blob(code, symbol, base.INJECT)
    clang = find_clang()
    argv = [str(clang), *get_armv6k_flags(ROOT, clang), "-MD", "-MF",
            str(obj.with_suffix(obj.suffix + ".d")), "-MT", "object", "-c",
            str(mutant.resolve()), "-o", str(obj.resolve())]
    return code, {"source_path": str(mutant), "source_sha256": sha(mutant.read_bytes()),
                  "object_path": str(obj), "object_sha256": sha(obj.read_bytes()),
                  "candidate_sha256": sha(code), "compile_argv": argv,
                  "compile_exit_code": build.returncode, "symbol_validation": validation}


def run(output: Path) -> dict:
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"run output is not fresh: {output}")
    output.mkdir(parents=True, exist_ok=True)
    image = IMAGE.read_bytes()
    if sha(image) != IMAGE_SHA:
        raise ValueError("pinned reference image hash mismatch")
    if sha(ADAPTER_SOURCE.read_bytes()) != ADAPTER_SHA:
        raise ValueError("navigation adapter candidate changed from frozen input")
    reference = base.verify_image(image)
    blobs, build = base.compile_adapter(output / "build")
    clang = find_clang()
    source_object = Path(build["object_path"])
    build["compile"] = compile_metadata(output, source_object)
    build["compile"]["stdout"] = build["compiler_stdout"]
    build["compile"]["stderr"] = build["compiler_stderr"]

    original_machine = base.AdapterMachine(image, blobs, "good")
    adapter_machine = base.AdapterMachine(image, blobs, "good")
    patch_inline_window(adapter_machine)

    gate_rows = []
    for label, ready in (("script_not_ready", (0, 1)),
                         ("preview_not_ready", (1, 0))):
        original = run_machine(original_machine, 1, 0, ready, {}, adapter_patched=False)
        candidate = run_machine(adapter_machine, 1, 0, ready, {}, adapter_patched=True)
        gate_rows.append(compare_row(original, candidate, label, ready, cursor=1, cached=0))

    matrix = []
    key_original = None
    for cursor in range(4):
        for cached in range(4):
            for mask in range(16):
                responses = {logical_id: int(bool(mask & (1 << bit)))
                             for logical_id, bit in MASK_BIT_FOR_TRIGGER.items()}
                original = run_machine(original_machine, cursor, cached, (1, 1), responses)
                candidate = run_machine(adapter_machine, cursor, cached, (1, 1), responses,
                                        adapter_patched=True)
                label = f"cursor{cursor}-cache{cached}-mask{mask:02x}"
                row = compare_row(original, candidate, label, (1, 1),
                                  cursor=cursor, cached=cached, mask=mask)
                matrix.append(row)
                if cursor == 0 and cached == 0 and mask == 1:
                    key_original = original

    if key_original is None:
        raise RuntimeError("matrix did not create wrong-normalizer control fixture")
    mutant_code, mutant_meta = compile_wrong_normalizer(output / "negative-control")
    mutant_machine = base.AdapterMachine(image, blobs, "good")
    mutant_machine.uc.mem_write(base.CANDIDATE_ADDRESS, mutant_code)
    patch_inline_window(mutant_machine)
    mutated = run_machine(mutant_machine, 0, 0, (1, 1), {5: 1}, adapter_patched=True)
    control = compare_row(key_original, mutated, "negative_wrong_signed_modulo_cursor0_mask01",
                          (1, 1), cursor=0, cached=0, mask=1)
    control_result = {
        "name": "wrong_raw_signed_remainder_for_minus_one",
        "mutant": mutant_meta,
        "detected": not control["passed"],
        "expected_original_selection": 3,
        "mutant_selection": control["selection_cache"]["adapter_after"]["selection"],
        "mismatch": control,
    }
    first_mismatch = next((row for row in [*gate_rows, *matrix] if not row["passed"]), None)
    report = {
        "task_id": "h1-navigation-adapter-matrix",
        "reference": reference,
        "candidate": build,
        "matrix_definition": {
            "logical_trigger_ids_in_bit_order": list(TRIGGER_IDS),
            "logical_masks": 16,
            "cursor_domain": [0, 1, 2, 3], "cached_domain": [0, 1, 2, 3],
            "matrix_case_count": len(matrix), "expected_matrix_case_count": 256,
            "gate_false_case_count": len(gate_rows),
        },
        "passed": len(matrix) == 256 and all(r["passed"] for r in matrix + gate_rows)
                  and control_result["detected"],
        "matrix_passed": sum(bool(r["passed"]) for r in matrix),
        "gate_false_passed": sum(bool(r["passed"]) for r in gate_rows),
        "gate_false_cases": gate_rows,
        "matrix_cases": matrix,
        "negative_control": control_result,
        "first_mismatch": first_mismatch,
        "evidence": {"compiled": "passed", "arm_differential": "partial",
                     "caller": "partial", "runtime": "not_run"},
        "limitations": [
            "Original execution starts at the pinned inline-window entry 0x001E9D08 with a synthetic active callback frame; adapter execution branches from that same entry into the private naked shim. The full function prologue and common epilogue are excluded.",
            "Readiness, trigger, and event entry hooks return configured values. Event queue work, physical device/input internals, and other trigger responses are not executed.",
            "The success path continues through original ARM to the first touch-pointer reload stop at 0x001E9E50; failure stops at 0x001EA62C. Physical touch handling and later callback work are excluded.",
            "Cursor/cache values are 0..3 and work/global storage is synthetic. The matrix does not establish production shim placement/linking, real runtime pointers, whole callback behavior, renderer state, or H1/game runtime equivalence."
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.output)
    print(f"navigation adapter matrix: {'PASS' if report['passed'] else 'FAIL'} "
          f"matrix={report['matrix_passed']}/256 gates={report['gate_false_passed']}/2 "
          f"negative-control={'detected' if report['negative_control']['detected'] else 'missed'}; "
          f"report={args.output/'report.json'}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
