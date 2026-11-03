#!/usr/bin/env python3
"""Pinned ARM differential for H2 cursor-axis initializer 0x00296F18."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import struct
from pathlib import Path
import sys

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips, encode_ips

IMAGE = ROOT / "extracted/exefs/code.bin"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
SOURCE = ROOT / "src/engine/leaf_batch11_b.cpp"
ADDRESS, SPAN, CODE_BASE = 0x00296F18, 72, 0x00100000
CODE_SIZE = 0x00378000
BLOCK, STACK, STACK_SIZE, RETURN = 0x00500000, 0x00600000, 0x10000, 0x00700000
H2_SETUP = 0x0029FAE8
H2_CALLS = (0x0029FB6C, 0x0029FBC4, 0x0029FC28, 0x0029FC44)
CALLEE = [(f"r{i}", getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4, 12)]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compact_result(value: dict) -> dict:
    return {key: (sha(item) if key == "block" else item)
            for key, item in value.items()}


def compile_body(source: Path, out: Path, symbol: str = "ui_func_00296f18") -> tuple[bytes, list[str], Path]:
    out.mkdir(parents=True, exist_ok=True)
    obj = out / "leaf_batch11_b.o"
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "candidate TU compilation failed")
    body, relocations = extract_elf_functions_detailed(obj)[symbol]
    if len(body) > SPAN or len(body) % 4 or relocations:
        raise ValueError(f"candidate invalid size/relocations: {len(body)} bytes, {relocations}")
    return body, list(result.args), obj


def stage(original: bytes, body: bytes) -> tuple[bytes, bytes]:
    fill = struct.pack("<I", 0xE320F000)
    payload = body + fill * ((SPAN - len(body)) // 4)
    off = ADDRESS - CODE_BASE
    staged = bytearray(original)
    staged[off:off + SPAN] = payload
    staged = bytes(staged)
    ips = encode_ips([(off, payload)], len(original))
    if apply_ips(original, ips) != staged:
        raise AssertionError("slot IPS roundtrip failed")
    if original[:off] != staged[:off] or original[off + SPAN:] != staged[off + SPAN:]:
        raise AssertionError("candidate changed bytes outside the 72-byte slot")
    return staged, ips


def arm_bl_target(image: bytes, pc: int) -> int:
    instruction = struct.unpack_from("<I", image, pc - CODE_BASE)[0]
    if instruction & 0xFF000000 != 0xEB000000:
        raise ValueError(f"expected unconditional ARM BL at {pc:#x}, got {instruction:#010x}")
    immediate = instruction & 0x00FFFFFF
    displacement = (immediate << 2) - (1 << 26) if immediate & 0x00800000 else immediate << 2
    return pc + 8 + displacement


def execute(image: bytes, start: int, metadata: int, seed: int,
            block_arg: int = BLOCK) -> dict:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM | unicorn.UC_MODE_LITTLE_ENDIAN)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_write(CODE_BASE, image)
    uc.mem_map(BLOCK, 0x1000)
    uc.mem_map(STACK, STACK_SIZE)
    uc.mem_map(RETURN, 0x1000)
    initial = bytes((seed * 23 + i * 37) & 0xFF for i in range(0x40))
    uc.mem_write(BLOCK, initial)
    writes = []

    def on_write(_uc, _access, address, size, value, _data):
        writes.append((address, size, value & 0xFFFFFFFF))

    uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_write)
    preserved = {name: (0xA5000000 + i * 0x01010101) & 0xFFFFFFFF
                 for i, (name, _) in enumerate(CALLEE)}
    for name, reg in CALLEE:
        uc.reg_write(reg, preserved[name])
    uc.reg_write(arm.UC_ARM_REG_R0, block_arg)
    uc.reg_write(arm.UC_ARM_REG_R1, start & 0xFFFFFFFF)
    uc.reg_write(arm.UC_ARM_REG_R2, metadata & 0xFFFFFFFF)
    uc.reg_write(arm.UC_ARM_REG_R3, (0xC3000000 ^ seed) & 0xFFFFFFFF)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK + STACK_SIZE // 2)
    uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
    entry_sp = uc.reg_read(arm.UC_ARM_REG_SP)
    fault = None
    try:
        uc.emu_start(ADDRESS, RETURN, count=1000)
    except unicorn.UcError as exc:
        fault = str(exc)
    return {"fault": fault, "return": uc.reg_read(arm.UC_ARM_REG_R0),
            "block": bytes(uc.mem_read(BLOCK, 0x40)), "writes": tuple(writes),
            "callee_saved": tuple(uc.reg_read(reg) for _, reg in CALLEE),
            "expected_callee_saved": tuple(preserved[name] for name, _ in CALLEE),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP), "entry_sp": entry_sp,
            "pc": uc.reg_read(arm.UC_ARM_REG_PC)}


def compare(ref: dict, got: dict, *, require_success: bool = True) -> str | None:
    for field in ("fault", "return", "block", "writes", "callee_saved", "sp"):
        if ref[field] != got[field]:
            return f"{field} differs"
    if got["callee_saved"] != got["expected_callee_saved"] or got["sp"] != got["entry_sp"]:
        return "candidate ABI preservation differs"
    if require_success and got["fault"] is not None:
        return "candidate faulted"
    return None


def execute_h2_setup(image: bytes, seed: int) -> dict:
    """Run actual 0x0029FAE8 with the pinned TitleConfig setup arguments."""
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM | unicorn.UC_MODE_LITTLE_ENDIAN)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_write(CODE_BASE, image)
    uc.mem_map(BLOCK, 0x2000)
    uc.mem_map(STACK, STACK_SIZE)
    uc.mem_map(RETURN, 0x1000)
    uc.mem_write(BLOCK, bytes((seed * 19 + i * 29) & 0xFF for i in range(0x2000)))
    writes, helper_calls = [], []

    def on_write(_uc, _access, address, size, value, _data):
        writes.append((address, size, value & 0xFFFFFFFF))

    def on_code(_uc, address, _size, _data):
        if address == ADDRESS:
            helper_calls.append({
                "site": _uc.reg_read(arm.UC_ARM_REG_LR) - 4,
                "block": _uc.reg_read(arm.UC_ARM_REG_R0),
                "start": _uc.reg_read(arm.UC_ARM_REG_R1),
                "metadata": _uc.reg_read(arm.UC_ARM_REG_R2),
            })

    uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_write)
    uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
    sp = STACK + STACK_SIZE // 2
    uc.reg_write(arm.UC_ARM_REG_SP, sp)
    uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
    uc.reg_write(arm.UC_ARM_REG_R0, BLOCK)
    uc.reg_write(arm.UC_ARM_REG_R1, 3)
    uc.reg_write(arm.UC_ARM_REG_R2, 3)
    uc.reg_write(arm.UC_ARM_REG_R3, 1)
    uc.mem_write(sp, struct.pack("<II", 0, 1))
    saved = {name: (0xD4000000 + i * 0x01020305) & 0xFFFFFFFF
             for i, (name, _) in enumerate(CALLEE)}
    for name, reg in CALLEE:
        uc.reg_write(reg, saved[name])
    fault = None
    try:
        uc.emu_start(H2_SETUP, RETURN, count=100000)
    except unicorn.UcError as exc:
        fault = str(exc)
    return {"fault": fault, "return": uc.reg_read(arm.UC_ARM_REG_R0),
            "block": bytes(uc.mem_read(BLOCK, 0x2000)), "writes": tuple(writes),
            "helper_calls": tuple(helper_calls), "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "entry_sp": sp,
            "callee_saved": tuple(uc.reg_read(reg) for _, reg in CALLEE),
            "expected_callee_saved": tuple(saved[name] for name, _ in CALLEE)}


def run(out: Path, seed: int) -> dict:
    out.mkdir(parents=True, exist_ok=False)
    original = IMAGE.read_bytes()
    if sha(original) != IMAGE_SHA:
        raise ValueError("pinned original code image hash mismatch")
    body, compiler_args, obj = compile_body(SOURCE, out / "compile")
    static_targets = {hex(pc): hex(arm_bl_target(original, pc)) for pc in H2_CALLS}
    if ADDRESS & 1 or any(int(target, 16) != ADDRESS for target in static_targets.values()):
        raise ValueError("candidate ARM entry or pinned H2 BL targets failed interworking audit")
    if any(arg.lower() == "-mthumb" for arg in compiler_args):
        raise ValueError("candidate was compiled for Thumb state")
    staged, ips = stage(original, body)
    (out / "staged-image.bin").write_bytes(staged)
    (out / "slot-only.ips").write_bytes(ips)
    cases = [(start, metadata, seed + i) for i, (start, metadata) in enumerate(
        (pair for start in (-(1 << 31), -2, -1, 0, 1, 2, (1 << 31) - 1)
         for pair in ((start, 0), (start, 1), (start, 0x80000000), (start, 0xFFFFFFFF))))]
    rng = random.Random(seed ^ 0x296F18)
    cases.extend((rng.randint(-(1 << 31), (1 << 31) - 1), rng.getrandbits(32), rng.getrandbits(32))
                 for _ in range(32))
    # This is the recovered H2 axis-0 argument pair observed from cursor setup.
    cases.append((3, 3, seed ^ 0xA11))
    rows, mismatches = [], []
    for i, (start, metadata, case_seed) in enumerate(cases):
        ref = execute(original, start, metadata, case_seed)
        got = execute(staged, start, metadata, case_seed)
        error = compare(ref, got)
        rows.append({"index": i, "start": start, "metadata": metadata,
                     "result": "passed" if error is None else "failed", "mismatch": error,
                     "writes": len(got["writes"])})
        if error:
            mismatches.append({"case": rows[-1], "original": ref, "candidate": got})
            break
    # Both implementations must fault at the same first store for a block whose
    # metadata word lies just beyond the mapped RAM boundary.
    fault_ref = execute(original, 0, 0x12345678, seed ^ 0xF017, BLOCK + 0xFF0)
    fault_got = execute(staged, 0, 0x12345678, seed ^ 0xF017, BLOCK + 0xFF0)
    fault_error = compare(fault_ref, fault_got, require_success=False)
    if fault_error is None and fault_ref["fault"] is None:
        fault_error = "boundary fault control unexpectedly completed"
    if fault_error:
        mismatches.append({"kind": "mapped-boundary fault", "error": fault_error,
                           "original": compact_result(fault_ref),
                           "candidate": compact_result(fault_got)})
    base_setup = execute_h2_setup(original, seed ^ 0xFAE8)
    staged_setup = execute_h2_setup(staged, seed ^ 0xFAE8)
    setup_error = compare(base_setup, staged_setup)
    expected_calls = (
        {"site": 0x0029FBC4, "block": BLOCK, "start": 3, "metadata": 3},
        {"site": 0x0029FC44, "block": BLOCK + 0x28, "start": 1, "metadata": 1},
    )
    expected_axes = (
        (6, 0x20200506, 0x20200E0F, 0, 3, 1, 3, 3, 0, 0),
        (6, 0x20200403, 0x20200D0C, 0, 1, 1, 1, 1, 0, 0),
    )
    observed_axes = tuple(struct.unpack_from("<10I", base_setup["block"], offset)
                          for offset in (0, 0x28))
    if base_setup["helper_calls"] != expected_calls:
        setup_error = "actual H2 setup helper callsites or raw arguments differ from pinned contract"
    if staged_setup["helper_calls"] != expected_calls:
        setup_error = "candidate H2 setup helper callsites or raw arguments differ from pinned contract"
    if observed_axes != expected_axes:
        setup_error = "actual H2 setup final axis records differ from pinned field contract"
    if base_setup["fault"] or staged_setup["fault"]:
        setup_error = f"H2 setup faulted: original={base_setup['fault']} candidate={staged_setup['fault']}"
    if setup_error:
        mismatches.append({"kind": "actual H2 setup caller", "error": setup_error,
                           "original": compact_result(base_setup),
                           "candidate": compact_result(staged_setup)})
    mutants = []
    source_text = SOURCE.read_text(encoding="utf-8")
    controls = [
        ("negative_clamp", "start <= 0 ? 0 : start", "start < 0 ? 1 : start", -1, 3),
        ("metadata_offset", "words[7] =", "words[6] =", 1, 0x12345678),
        ("layout_flags", "words[5] = 2;", "words[5] = 3;", 3, 3),
    ]
    for name, before, after, start, metadata in controls:
        if source_text.count(before) != 1:
            raise ValueError(f"nonunique mutant anchor: {name}")
        mutant_src = out / f"mutant-{name}.cpp"
        mutant_src.write_text(source_text.replace(before, after, 1), encoding="utf-8")
        mutant_body, _, _ = compile_body(mutant_src, out / f"mutant-{name}-build")
        mutant_image, _ = stage(original, mutant_body)
        ref = execute(original, start, metadata, 0x5150 + len(mutants))
        got = execute(mutant_image, start, metadata, 0x5150 + len(mutants))
        detected = compare(ref, got) is not None
        mutants.append({"name": name, "detected": detected})
        if not detected:
            raise AssertionError(f"negative control not detected: {name}")
    caller_obj = out / "affected-tus" / "leaf_batch40_a.o"
    caller_obj.parent.mkdir(parents=True, exist_ok=True)
    caller_build = compile_tu_armv6k(ROOT / "src/engine/leaf_batch40_a.cpp", caller_obj, ROOT)
    if caller_build.returncode:
        raise RuntimeError(caller_build.stderr or "H2 caller translation unit compilation failed")
    # Record final artifacts, compiler identity and directed/seeded results.
    report = {"schema_version": 1, "function": hex(ADDRESS), "span": SPAN,
              "image_sha256": sha(original), "source_sha256": sha(SOURCE.read_bytes()),
              "object_sha256": sha(obj.read_bytes()), "body_sha256": sha(body),
              "body_bytes": len(body), "relocations": [], "compiler_args": compiler_args,
              "affected_tus": [{"path": "src/engine/leaf_batch11_b.cpp", "compiled": True,
                                "compiler_args": compiler_args},
                               {"path": "src/engine/leaf_batch40_a.cpp", "compiled": True,
                                "compiler_args": list(caller_build.args),
                                "object_sha256": sha(caller_obj.read_bytes())}],
              "staged_image_sha256": sha(staged), "ips_sha256": sha(ips),
              "changed_bytes_within_slot": True, "cases": len(rows), "seed": seed,
              "directed_starts": [-(1 << 31), -2, -1, 0, 1, 2, (1 << 31) - 1],
              "metadata_patterns": ["0", "1", "0x80000000", "0xFFFFFFFF"],
              "seeded_cases": 32, "h2_axis0_argument_case": {"start": 3, "metadata": 3},
              "rows": rows, "mismatches": mismatches, "negative_controls": mutants,
              "fault_control": {"block_offset": "0xFF0", "original_fault": fault_ref["fault"],
                                "candidate_fault": fault_got["fault"],
                                "matched": fault_error is None},
              "h2_setup_call_sites": [hex(x) for x in H2_CALLS],
              "arm_interworking": {"candidate_entry": hex(ADDRESS), "candidate_entry_bit0": ADDRESS & 1,
                                   "static_call_targets": static_targets,
                                   "candidate_compiled_thumb": False, "passed": True},
              "h2_setup_call_sites_observed": [hex(x["site"]) for x in base_setup["helper_calls"]],
              "h2_setup_helper_arguments_observed": [
                  {**x, "site": hex(x["site"]), "block": hex(x["block"])}
                  for x in base_setup["helper_calls"]],
              "h2_setup_final_axis_words": [list(x) for x in observed_axes],
              "h2_setup_composition": "actual original 0x0029FAE8 entry; two dynamically reached calls among four static 0x00296F18 callsites; base compared against one-slot staged image",
              "all_passed": not mismatches, "caller": "actual TitleConfig cursor setup entry executed in both profiles; sibling setup helpers remain original",
              "limits": ["valid mapped writable ordinary RAM only", "other cursor setup helpers/lifecycle and runtime are unverified"]}
    path = out / "report.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_passed": report["all_passed"], "body_bytes": len(body),
                      "cases": len(rows), "mutants": mutants,
                      "report": str(path), "sha256": sha(path.read_bytes())}, indent=2))
    if mismatches:
        return report
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261121)
    args = parser.parse_args()
    report = run(args.out.resolve(), args.seed)
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
