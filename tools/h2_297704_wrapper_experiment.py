#!/usr/bin/env python3
"""Pinned ARM differential for ScriptVm_LoadTable wrapper 0x00297704."""
from __future__ import annotations

import argparse
import csv
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
SOURCE = ROOT / "src/engine/leaf_batch18_b.cpp"
ADDRESS, SPAN, CODE_BASE = 0x00297704, 32, 0x00100000
CODE_SIZE = 0x00378000
LOADER, BLOCK, STACK, STACK_SIZE, RETURN = 0x002AE6C8, 0x00500000, 0x00600000, 0x10000, 0x00700000
CALLER_START, CALLER_STOP = 0x002F4DC8, 0x002F4DEC
SYMBOL = "script_vm_func_00297704"
CALLEE = [(f"r{i}", getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4, 12)]
VFP_CALLEE = [(f"d{i}", getattr(arm, f"UC_ARM_REG_D{i}")) for i in range(8, 16)]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ledger_addresses() -> dict[str, int]:
    rows: dict[str, set[int]] = {}
    with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("name") and row.get("address"):
                rows.setdefault(row["name"].strip(), set()).add(int(row["address"], 16))
    return {name: next(iter(values)) for name, values in rows.items() if len(values) == 1}


def compile_body(out: Path) -> tuple[bytes, list, list[str], Path]:
    out.mkdir(parents=True, exist_ok=True)
    obj = out / "leaf_batch18_b.o"
    result = compile_tu_armv6k(SOURCE, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "candidate TU compilation failed")
    entry = extract_elf_functions_detailed(obj).get(SYMBOL)
    if entry is None:
        raise ValueError(f"candidate symbol {SYMBOL!r} not found")
    body, relocs = entry
    if not body or len(body) > SPAN or len(body) % 4 or len(relocs) != 1:
        raise ValueError(f"candidate does not fit its slot with one helper call: {len(body)} / {relocs}")
    return body, list(relocs), list(result.args), obj


def resolve(body: bytes, relocs: list, original: bytes) -> tuple[bytes, list[dict]]:
    fixed = bytearray(body)
    addresses = ledger_addresses()
    report = []
    for r in relocs:
        target = addresses.get(r.symbol_name)
        if (target != LOADER or target & 3 or r.relocation_type != 28
                or r.explicit_addend is not None or r.offset % 4):
            raise ValueError(f"unexpected loader relocation: {r}, target={target}")
        word = struct.unpack_from("<I", fixed, r.offset)[0]
        if word & 0xFF000000 != 0xEB000000:
            raise ValueError(f"relocation is not ARM BL: {word:#x}")
        delta = target - (ADDRESS + r.offset + 8)
        if delta & 3 or not -(1 << 25) <= delta < (1 << 25):
            raise ValueError("loader ARM BL out of range")
        struct.pack_into("<I", fixed, r.offset,
                         (word & 0xFF000000) | ((delta >> 2) & 0xFFFFFF))
        target_word = struct.unpack_from("<I", original, target - CODE_BASE)[0]
        if target_word in (0, 0xFFFFFFFF):
            raise ValueError("loader target is not pinned ARM code")
        report.append({"offset": r.offset, "symbol": r.symbol_name,
                       "target": f"0x{target:08X}", "bit0": target & 1,
                       "entry_word": f"0x{target_word:08X}"})
    return bytes(fixed), report


def stage(original: bytes, body: bytes) -> tuple[bytes, bytes]:
    off = ADDRESS - CODE_BASE
    fill = struct.pack("<I", 0xE320F000)
    payload = body + fill * ((SPAN - len(body)) // 4)
    image = bytearray(original)
    image[off:off + SPAN] = payload
    staged = bytes(image)
    ips = encode_ips([(off, payload)], len(original))
    if apply_ips(original, ips) != staged:
        raise AssertionError("IPS replay differs")
    if original[:off] != staged[:off] or original[off + SPAN:] != staged[off + SPAN:]:
        raise AssertionError("staging changed bytes outside the wrapper slot")
    return staged, ips


def run(image: bytes, values: dict, seed: int, *, caller: bool = False) -> dict:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM | unicorn.UC_MODE_LITTLE_ENDIAN)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_write(CODE_BASE, image)
    uc.mem_map(BLOCK, 0x1000)
    uc.mem_map(STACK, STACK_SIZE)
    uc.mem_map(RETURN, 0x1000)
    raw = bytes((seed * 17 + i * 29 + 0x45) & 0xFF for i in range(0x1000))
    uc.mem_write(BLOCK, raw)
    if not caller and values.get("name_text"):
        uc.mem_write(values["name"], values["name_text"].encode("ascii") + b"\0")
    entry_sp = STACK + STACK_SIZE // 2
    uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
    uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(arm.UC_ARM_REG_FPSCR, 0)
    uc.reg_write(arm.UC_ARM_REG_SP, entry_sp)
    uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
    for i, (_, reg) in enumerate(CALLEE):
        uc.reg_write(reg, 0xA5000000 | (i * 0x01010101 + seed))
    for i, (_, reg) in enumerate(VFP_CALLEE):
        uc.reg_write(reg, 0x1122334455667700 + i + seed * 8)
    uc.mem_write(entry_sp, struct.pack("<2I", *values.get("incoming_stack", (0xDEADBEEF, 0x76543210))))
    if caller:
        work = BLOCK + 0x100
        uc.reg_write(arm.UC_ARM_REG_R4, work)
        uc.reg_write(arm.UC_ARM_REG_R5, 0)
        begin, until = CALLER_START, CALLER_STOP
    else:
        uc.reg_write(arm.UC_ARM_REG_R0, values["name"])
        uc.reg_write(arm.UC_ARM_REG_R1, values["out"])
        uc.reg_write(arm.UC_ARM_REG_R2, values["flags"])
        uc.reg_write(arm.UC_ARM_REG_R3, values["ignored_r3"])
        begin, until = ADDRESS, RETURN

    calls = []

    def at_loader(machine, address, _size, _data):
        if address != LOADER:
            return
        sp = machine.reg_read(arm.UC_ARM_REG_SP)
        name_ptr = machine.reg_read(arm.UC_ARM_REG_R0)
        name = bytearray()
        for k in range(96):
            byte = machine.mem_read(name_ptr + k, 1)[0]
            if not byte:
                break
            name.append(byte)
        calls.append({"r0": name_ptr, "name": name.decode("ascii", errors="replace"),
                      "r1": machine.reg_read(arm.UC_ARM_REG_R1),
                      "r2": machine.reg_read(arm.UC_ARM_REG_R2),
                      "r3": machine.reg_read(arm.UC_ARM_REG_R3),
                      "stack": struct.unpack("<2I", machine.mem_read(sp, 8)),
                      "sp_mod8": sp & 7})
        machine.reg_write(arm.UC_ARM_REG_R0, 0xC0DE0000 + len(calls))
        machine.reg_write(arm.UC_ARM_REG_PC, machine.reg_read(arm.UC_ARM_REG_LR))

    uc.hook_add(unicorn.UC_HOOK_CODE, at_loader)
    fault = None
    try:
        uc.emu_start(begin, until, count=100000)
    except unicorn.UcError as exc:
        fault = str(exc)
    return {"fault": fault, "calls": calls,
            "return": uc.reg_read(arm.UC_ARM_REG_R0), "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "entry_sp": entry_sp, "callee": tuple(uc.reg_read(r) for _, r in CALLEE),
            "vfp_callee": tuple(uc.reg_read(r) for _, r in VFP_CALLEE),
            "out_memory": bytes(uc.mem_read(BLOCK + 0x300, 0x20)),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC)}


def compare(a: dict, b: dict) -> str | None:
    for key in ("fault", "calls", "return", "sp", "callee", "vfp_callee", "out_memory"):
        if a[key] != b[key]:
            return f"{key} differs"
    if b["fault"] is not None:
        return "candidate faulted"
    if b["sp"] != b["entry_sp"]:
        return "candidate SP differs from entry"
    if any(call["sp_mod8"] for call in b["calls"]):
        return "candidate loader call SP is not 8-byte aligned"
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261102)
    parser.add_argument("--random-cases", type=int, default=32)
    args = parser.parse_args()
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    original = IMAGE.read_bytes()
    if sha(original) != IMAGE_SHA:
        raise ValueError("pinned code.bin SHA-256 mismatch")
    body, relocs, command, obj = compile_body(out / "compile")
    linked, branch = resolve(body, relocs, original)
    staged, ips = stage(original, linked)
    (out / "candidate.ips").write_bytes(ips)
    (out / "candidate.bin").write_bytes(staged)

    rng = random.Random(args.seed)
    values = [{"name": BLOCK + 0x20, "name_text": "camp/config.bf",
               "out": BLOCK + 0x300, "flags": 0,
               "ignored_r3": 0, "incoming_stack": (0xABCDEF01, 0xFEDCBA98)},
              {"name": BLOCK + 0x40, "out": BLOCK + 0x340, "flags": 0xFFFFFFFF,
               "name_text": "camp/config.mbm", "ignored_r3": 0x87654321,
               "incoming_stack": (1, 2)}]
    for _ in range(args.random_cases):
        values.append({"name": BLOCK + 0x20, "name_text": "camp/config.bf",
                       "out": BLOCK + 0x300,
                       "flags": rng.getrandbits(32), "ignored_r3": rng.getrandbits(32),
                       "incoming_stack": (rng.getrandbits(32), rng.getrandbits(32))})
    direct, failures = [], []
    for i, case in enumerate(values):
        uc_case = dict(case)
        ref = run(original, uc_case, args.seed + i)
        got = run(staged, uc_case, args.seed + i)
        mismatch = compare(ref, got)
        row = {"index": i, "status": mismatch or "pass", "case": case,
               "trace": got["calls"]}
        direct.append(row)
        if mismatch:
            failures.append(row)

    caller_ref = run(original, {}, args.seed + 0xCAFE, caller=True)
    caller_got = run(staged, {}, args.seed + 0xCAFE, caller=True)
    caller_mismatch = compare(caller_ref, caller_got)
    if caller_mismatch:
        failures.append({"caller": caller_mismatch})

    # Mutate `mov r12,#4` to `mov r12,#8` so the downstream size word is wrong.
    mutant = bytearray(linked)
    mov4 = next((i for i in range(0, len(body), 4)
                 if struct.unpack_from("<I", body, i)[0] == 0xE3A0C004), None)
    if mov4 is None:
        raise AssertionError("candidate size argument instruction was not found")
    struct.pack_into("<I", mutant, mov4, 0xE3A0C008)
    mutant_image, _ = stage(original, bytes(mutant))
    control_ref = run(original, values[0], args.seed + 99)
    control_mutant = run(mutant_image, values[0], args.seed + 99)
    control_difference = compare(control_ref, control_mutant)
    if control_difference is None:
        raise AssertionError("wrong-size negative control was not detected")

    report = {
        "target": "0x00297704", "original_image_sha256": sha(original),
        "original_span_sha256": sha(original[ADDRESS-CODE_BASE:ADDRESS-CODE_BASE+SPAN]),
        "candidate_source_sha256": sha(SOURCE.read_bytes()),
        "candidate_object_sha256": sha(obj.read_bytes()),
        "candidate_body_sha256": sha(body), "candidate_body_size": len(body),
        "slot_size": SPAN, "resolved_branch": branch,
        "compiler_command": command, "seed": args.seed,
        "case_count": len(direct), "direct_cases": direct,
        "caller_slice": {"start": f"0x{CALLER_START:08X}",
                         "stop": f"0x{CALLER_STOP:08X}",
                         "status": caller_mismatch or "pass",
                         "traces": caller_got["calls"]},
        "negative_control": {"change": "loader size 4 to 8",
                              "difference_detected": control_difference},
        "failures": failures, "status": "passed" if not failures else "failed",
        "domain": "ordinary mapped name and output memory; downstream loader is an entry-hook seam returning a controlled raw value; asynchronous completion and real resource behavior are not tested",
    }
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"candidate={len(body)}/{SPAN} bytes; direct={len(direct)}; caller={caller_mismatch or 'pass'}; failures={len(failures)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
