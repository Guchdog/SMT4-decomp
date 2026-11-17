#!/usr/bin/env python3
"""Offline ARM/Thumb differential for the 0x002b5c2c halfword counter."""
from __future__ import annotations

import argparse
import capstone
import hashlib
import json
from pathlib import Path
import random
import struct
import sys

from unicorn import (
    UC_ARCH_ARM, UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE,
    UC_MEM_READ, UC_MODE_ARM, Uc,
)
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ADDRESS = 0x002B5C2C
SPAN = 20
TEXT = 0x00100000
TEXT_MAP_SIZE = 0x00400000
DATA = 0x02000000
DATA_SIZE = 0x1000
STACK = 0x08000000
STACK_SIZE = 0x2000
SP = STACK + 0x1000
INJECT = 0x01000000
RETURN = 0x01001000

CALLERS = {
    0x0021F504: "engine_func_0021f480",
    0x0023495C: "engine_func_0023494c",
    0x002A8868: "ui_func_002a882c",
    0x002ADADC: "ui_func_002ada98",
    0x002BB930: "engine_func_002bb8e4",
    0x002E0E0C: "engine_func_002e0dd0",
    0x003104A8: "engine_func_00310448",
    0x003529F0: "ui_func_00352974",
    0x00352B80: "ui_func_00352b30",
    0x00356028: "engine_func_00355fe0",
    0x0035C340: "ui_func_0035c32c",
    0x0038C7C8: "script_vm_func_0038c43c",
    0x0038C840: "script_vm_func_0038c43c",
    0x0038DA94: "script_vm_func_0038d7b0",
    0x0038DB04: "script_vm_func_0038d7b0",
}


def verify_reference(image: bytes) -> dict:
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    image_hash = hashlib.sha256(image).hexdigest()
    if image_hash != game["code_sha256"] or len(image) != game["code_bin_size"]:
        raise ValueError("code.bin does not match the pinned game revision")
    offset = ADDRESS - TEXT
    raw = image[offset:offset + SPAN]
    expected = bytes.fromhex("002101e0491c801c0288002afa d108007047ffff".replace(" ", ""))
    if raw != expected:
        raise ValueError(f"reference bytes changed: {raw.hex()}")

    direct = []
    for off in range(0, len(image) - 3, 4):
        word = struct.unpack_from("<I", image, off)[0]
        site = TEXT + off
        cond = word >> 28
        target = None
        kind = None
        if cond != 0xF and ((word >> 24) & 0xF) == 0xB:
            imm = word & 0xFFFFFF
            if imm & (1 << 23):
                imm -= 1 << 24
            target = site + 8 + (imm << 2)
            kind = "bl"
        elif cond == 0xF and ((word >> 25) & 7) == 5:
            imm = word & 0xFFFFFF
            if imm & (1 << 23):
                imm -= 1 << 24
            target = (site + 8 + (imm << 2) + (((word >> 24) & 1) << 1)) & ~1
            kind = "blx"
        if target == ADDRESS:
            direct.append({"site": site, "kind": kind})
    direct_sites = [item["site"] for item in direct]
    if direct_sites != sorted(CALLERS):
        raise ValueError(f"direct caller set changed: {[hex(site) for site in direct_sites]}")
    pointer_sites = [TEXT + off for off in range(0, len(image) - 3, 4)
                     if struct.unpack_from("<I", image, off)[0] in (ADDRESS, ADDRESS | 1)]

    with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
        import csv
        rows = list(csv.DictReader(stream))
    function_row = next((row for row in rows if int(row["address"], 16) == ADDRESS), None)
    if (function_row is None or int(function_row["size"]) != SPAN or
            function_row["name"] != "ui_func_002b5c2c"):
        raise ValueError(f"function ledger identity changed: {function_row}")
    owners = {}
    for site in direct_sites:
        row = next((item for item in rows
                    if int(item["address"], 16) <= site <
                    int(item["address"], 16) + int(item["size"])), None)
        if row is None or row["name"] != CALLERS[site]:
            raise ValueError(f"caller owner mismatch at {site:#x}: {row}")
        owners[f"0x{site:08x}"] = row["name"]

    return {
        "image_sha256": image_hash,
        "address": f"0x{ADDRESS:08x}",
        "span_size": SPAN,
        "mode": "Thumb, established by byte decoding and ARM BLX call sites",
        "entry_bytes": raw.hex(),
        "return": "bx lr at 0x002b5c3c; 0xffff halfword tail data/padding",
        "direct_callers": [{**item, "owner": owners[f"0x{item['site']:08x}"]}
                           for item in direct],
        "aligned_pointer_sites": [f"0x{site:08x}" for site in pointer_sites],
        "scan_limit": "Aligned ARM BL/BLX immediate words and aligned exact pointer words only; indirect, unaligned, relocated or computed references can be missed.",
    }


def thumb_instructions(code: bytes):
    dis = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    dis.detail = True
    items = list(dis.disasm(code, 0))
    if not items or sum(item.size for item in items) != len(code):
        raise ValueError("candidate is not completely decodable as Thumb")
    if items[-1].mnemonic != "bx" or items[-1].op_str != "lr":
        raise ValueError("candidate must end in Thumb bx lr")
    if any(item.group(capstone.CS_GRP_CALL) for item in items):
        raise ValueError("candidate must be relocation-free and call-free")
    return items


def compile_candidate(output: Path) -> tuple[bytes, Path]:
    source = ROOT / "experiments/semantic_equivalence/h18_002b5c2c_candidate.cpp"
    obj = output / "h18_002b5c2c_candidate.o"
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "ARMv6K compile failed")
    symbols = extract_elf_functions_detailed(obj)
    if "candidate_002b5c2c" not in symbols:
        raise ValueError("candidate symbol missing from object")
    code, relocations = symbols["candidate_002b5c2c"]
    if relocations:
        raise ValueError(f"candidate has relocations: {relocations}")
    thumb_instructions(code)
    return code, obj


def new_machine(image: bytes, pointer: int, words: list[int], body: bytes | None):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(TEXT, TEXT_MAP_SIZE)
    uc.mem_write(TEXT, image)
    uc.mem_map(DATA, DATA_SIZE)
    uc.mem_map(STACK, STACK_SIZE)
    uc.mem_map(INJECT, 0x2000)
    payload = struct.pack("<" + "H" * (len(words) + 1), *words, 0)
    uc.mem_write(pointer, payload)
    if body is not None:
        uc.mem_write(INJECT, body)
    return uc, payload


def execute_function(image: bytes, body: bytes | None, words: list[int],
                     pointer=DATA + 0x100, initial_nzcv=0xF0000000) -> dict:
    uc, payload = new_machine(image, pointer, words, body)
    uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10 | (initial_nzcv & 0xF0000000))
    initial = [((0x12340000 + index * 0x01010101) & 0xFFFFFFFF) for index in range(13)]
    for index, value in enumerate(initial):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_R{index}"), value)
    uc.reg_write(arm.UC_ARM_REG_R0, pointer)
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
    reads: set[int] = set()
    writes: set[int] = set()
    stopped = False

    def code_hook(machine, address, _size, _):
        nonlocal stopped
        if address == RETURN:
            stopped = True
            machine.emu_stop()

    def memory_hook(_machine, access, address, size, _value, _):
        target = reads if access == UC_MEM_READ else writes
        target.update(range(address, address + size))

    uc.hook_add(UC_HOOK_CODE, code_hook)
    uc.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, memory_hook)
    start = INJECT if body is not None else ADDRESS
    uc.emu_start(start | 1, 0, count=512)
    cpsr = uc.reg_read(arm.UC_ARM_REG_CPSR)
    return {
        "stopped": stopped,
        "r0": uc.reg_read(arm.UC_ARM_REG_R0),
        "pc": uc.reg_read(arm.UC_ARM_REG_PC),
        "lr": uc.reg_read(arm.UC_ARM_REG_LR),
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        "preserved": tuple(uc.reg_read(getattr(arm, f"UC_ARM_REG_R{index}"))
                           for index in range(4, 12)),
        "nzcv": cpsr & 0xF0000000,
        "thumb_state": bool(cpsr & 0x20),
        "reads": reads,
        "writes": writes,
        "payload": payload,
        "memory": bytes(uc.mem_read(pointer, len(payload))),
    }


def encode_blx(site: int, target: int) -> bytes:
    displacement = target - (site + 8)
    if target & 1 or displacement & 1 or not -(1 << 25) <= displacement < (1 << 25):
        raise ValueError("BLX target is unaligned or out of range")
    imm24 = (displacement >> 2) & 0xFFFFFF
    h = (displacement >> 1) & 1
    return struct.pack("<I", 0xFA000000 | (h << 24) | imm24)


def execute_caller_window(image: bytes, body: bytes | None, site: int, stop: int,
                          pointer: int, words: list[int], preloaded_r0: bool = False) -> dict:
    uc, payload = new_machine(image, pointer, words, body)
    if body is not None:
        uc.mem_write(site, encode_blx(site, INJECT))
    uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10 | 0xA0000000)
    for index in range(13):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_R{index}"), 0x76540000 + index)
    # The 0x002e0dd0 callsite is preceded by MOV r0,r6. The (count+1)*2
    # callsite has MOV r0,r4 and the input pointer is already in r4.
    if site == 0x002E0E0C:
        uc.reg_write(arm.UC_ARM_REG_R6, pointer)
        uc.reg_write(arm.UC_ARM_REG_R0, pointer)
    elif site == 0x002A8868:
        uc.reg_write(arm.UC_ARM_REG_R0, pointer)
        uc.reg_write(arm.UC_ARM_REG_R4, pointer)
        uc.reg_write(arm.UC_ARM_REG_R6, 0x12345678)
    else:
        raise ValueError(f"unsupported caller window {site:#x}")
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
    stopped = False

    def code_hook(machine, address, _size, _):
        nonlocal stopped
        if address == stop:
            stopped = True
            machine.emu_stop()

    uc.hook_add(UC_HOOK_CODE, code_hook)
    try:
        uc.emu_start(site, 0, count=512)
    except Exception as error:
        raise RuntimeError(
            f"caller window {site:#x}->{stop:#x} faulted at "
            f"PC={uc.reg_read(arm.UC_ARM_REG_PC):#x}, "
            f"LR={uc.reg_read(arm.UC_ARM_REG_LR):#x}, "
            f"r0={uc.reg_read(arm.UC_ARM_REG_R0):#x}: {error}"
        ) from error
    return {
        "stopped": stopped,
        "pc": uc.reg_read(arm.UC_ARM_REG_PC),
        "r0": uc.reg_read(arm.UC_ARM_REG_R0),
        "r3": uc.reg_read(arm.UC_ARM_REG_R3),
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        "length_slot": struct.unpack("<I", uc.mem_read(SP + 8, 4))[0],
        "thumb_state": bool(uc.reg_read(arm.UC_ARM_REG_CPSR) & 0x20),
        "nzcv": uc.reg_read(arm.UC_ARM_REG_CPSR) & 0xF0000000,
        "payload": payload,
    }


def make_cases(seed: int, samples: int) -> list[list[int]]:
    rng = random.Random(seed ^ ADDRESS)
    cases = [[], [1], [0xFFFF], [0x8000], [0x1234, 0xABCD, 0x0101, 0x7FFF]]
    for _ in range(samples):
        length = rng.randint(1, 64)
        cases.append([rng.randrange(1, 0x10000) for _ in range(length)])
    return cases


def compare_run(original: dict, candidate: dict, count: int, pointer: int) -> str | None:
    if not original["stopped"] or not candidate["stopped"]:
        return "execution did not reach ARM continuation"
    if original["r0"] != count or candidate["r0"] != count:
        return f"wrong count: original={original['r0']}, candidate={candidate['r0']}, expected={count}"
    expected_reads = set(range(pointer, pointer + 2 * (count + 1)))
    for label, run in (("original", original), ("candidate", candidate)):
        if run["reads"] != expected_reads:
            return f"{label} read footprint differs from all nonzero halfwords plus terminator"
        if run["writes"]:
            return f"{label} wrote memory"
        if run["sp"] != SP or run["lr"] != RETURN:
            return f"{label} changed SP/LR"
        if run["thumb_state"]:
            return f"{label} failed Thumb-to-ARM return interworking"
        if run["memory"] != run["payload"]:
            return f"{label} changed input memory"
    if original["preserved"] != candidate["preserved"]:
        return "callee-saved registers differ"
    if original["pc"] != candidate["pc"]:
        return "continuation PC differs"
    if original["nzcv"] != candidate["nzcv"]:
        return "NZCV differs"
    return None


def negative_controls(image: bytes) -> list[dict]:
    raw = bytes.fromhex("002101e0491c801c0288002afad108007047ffff")
    if len(raw) != SPAN:
        raise AssertionError("reference control template length changed")
    controls = {
        "byte_step": (raw[:6] + struct.pack("<H", 0x1C40) + raw[8:], [0x0101, 0x0202]),
        "inclusive_terminator": (raw[:14] + struct.pack("<H", 0x1C48) + raw[16:], [0x1234]),
        "wrong_count": (raw[:14] + struct.pack("<H", 0x0048) + raw[16:], [1, 2, 3]),
    }
    output = []
    for name, (mutated, words) in controls.items():
        baseline = execute_function(image, None, words)
        mutant = execute_function(image, mutated, words)
        issue = compare_run(baseline, mutant, len(words), DATA + 0x100)
        output.append({"name": name, "detected": issue is not None, "reason": issue})
    return output


def run(code_path: Path, output: Path, seed: int, samples: int = 128) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    image = Path(code_path).read_bytes()
    evidence = verify_reference(image)
    body, obj = compile_candidate(output)
    case_reports = []
    for index, words in enumerate(make_cases(seed, samples)):
        pointer = DATA + 0x100
        initial_nzcv = ((index * 7 + seed) & 0xF) << 28
        original = execute_function(image, None, words, pointer, initial_nzcv)
        candidate = execute_function(image, body, words, pointer, initial_nzcv)
        reason = compare_run(original, candidate, len(words), pointer)
        case_reports.append({"index": index, "length": len(words), "passed": reason is None,
                             "reason": reason})
        if reason:
            break

    controls = negative_controls(image)
    if not all(item["detected"] for item in controls):
        raise AssertionError(f"negative control escaped: {controls}")

    caller_cases = [[], [0x2345], [0x8000, 0xFFFF]]
    caller_windows = []
    for site, stop, kind in ((0x002E0E0C, 0x002E0E14, "count_times_2"),
                             (0x002A8868, 0x002A887C, "count_plus_terminator_times_2")):
        for words in caller_cases:
            original = execute_caller_window(image, None, site, stop, DATA + 0x100, words)
            candidate = execute_caller_window(image, body, site, stop, DATA + 0x100, words)
            expected = len(words) * 2 if kind == "count_times_2" else (len(words) + 1) * 2
            actual = original["r3"] if kind == "count_times_2" else original["length_slot"]
            issue = None
            if not original["stopped"] or not candidate["stopped"]:
                issue = "caller window did not reach continuation"
            elif actual != expected:
                issue = f"original caller composition produced {actual}, expected {expected}"
            elif (candidate["r3"] if kind == "count_times_2" else candidate["length_slot"]) != expected:
                issue = "candidate caller-composed length differs"
            elif original["pc"] != candidate["pc"] or original["thumb_state"] or candidate["thumb_state"]:
                issue = "caller continuation/interworking state differs"
            elif original["nzcv"] != candidate["nzcv"]:
                issue = "caller-window flags differ"
            caller_windows.append({"site": f"0x{site:08x}", "kind": kind,
                                  "count": len(words), "expected": expected,
                                  "passed": issue is None, "reason": issue})

    report = {
        "passed": all(item["passed"] for item in case_reports) and
                  all(item["passed"] for item in caller_windows) and
                  all(item["detected"] for item in controls),
        "seed": seed,
        "cases": len(case_reports),
        "candidate_bytes": body.hex(),
        "candidate_object_sha256": hashlib.sha256(obj.read_bytes()).hexdigest(),
        "candidate_thumb_instructions": [
            {"address": item.address, "mnemonic": item.mnemonic, "op_str": item.op_str}
            for item in thumb_instructions(body)
        ],
        "reference": evidence,
        "caller_windows": caller_windows,
        "negative_controls": controls,
        "case_results": case_reports,
        "limits": [
            "Seeded domain uses aligned readable zero-terminated uint16_t sequences with lengths at most 64; unterminated/out-of-range pointers are not tested.",
            "Caller composition executes selected BLX-to-Thumb and post-call length instructions, not full callers or downstream helper behavior.",
            "A bounded offline ARM11 Unicorn comparison is not whole-game/runtime equivalence.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--seed", type=int, default=20261116)
    parser.add_argument("--samples", type=int, default=128)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.samples < 0:
        parser.error("--samples must be nonnegative")
    report = run(args.code, args.output, args.seed, args.samples)
    print(json.dumps({key: report[key] for key in ("passed", "seed", "cases", "candidate_bytes", "caller_windows", "negative_controls")}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
