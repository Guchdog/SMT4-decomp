"""Pinned original-vs-C++ differential for 0x00254CA8 with explicit service seams."""
from __future__ import annotations

import argparse
import hashlib
import copy
import json
from pathlib import Path
import random
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import unicorn
from unicorn import arm_const as arm
from tools.asm_diff import extract_elf_functions_detailed, load_function_addresses
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips, encode_ips, sha256

IMAGE = ROOT / "extracted/exefs/code.bin"
SOURCE = ROOT / "src/engine/leaf_batch45_b.cpp"
LEDGER = ROOT / "config/functions.csv"
SYMBOL = "ui_func_00254ca8"
ENTRY = 0x00254CA8
SPAN = 840
TEXT_BASE = 0x00100000
STACK = 0x0F000000
STACK_SIZE = 0x20000
SP = STACK + 0x18000
RETURN = 0x01000000
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
CALLS = {
    0x002BFFBC: "mode0_query",
    0x002B902C: "mode1_query",
    0x002C17D4: "mask_query",
    0x0027FBC8: "axis_reader",
    0x002820A4: "angle",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def bits_f32(value: int) -> float:
    return struct.unpack("<f", struct.pack("<I", value & 0xFFFFFFFF))[0]


def candidate_body(obj: Path) -> tuple[bytes, list[dict]]:
    build = compile_tu_armv6k(SOURCE, obj, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr or "affected TU compile failed")
    functions = extract_elf_functions_detailed(obj)
    if SYMBOL not in functions:
        raise RuntimeError(f"missing compiled symbol {SYMBOL}")
    body, relocs = functions[SYMBOL]
    addresses = load_function_addresses(LEDGER)
    fixed = bytearray(body)
    rows = []
    for reloc in relocs:
        if reloc.relocation_type != 28 or reloc.explicit_addend is not None:
            raise RuntimeError(f"unexpected relocation form: {reloc}")
        target = addresses.get(reloc.symbol_name)
        if target is None or target & 1 or target not in CALLS:
            raise RuntimeError(f"unresolved/non-ARM helper target {reloc.symbol_name}: {target}")
        word = struct.unpack_from("<I", fixed, reloc.offset)[0]
        if word & 0x0F000000 != 0x0B000000:
            raise RuntimeError(f"R_ARM_CALL is not BL at {reloc.offset:#x}")
        place = ENTRY + reloc.offset
        delta = target - (place + 8)
        if delta & 3 or not -(1 << 25) <= delta < (1 << 25):
            raise RuntimeError(f"BL to {target:#x} is out of range")
        struct.pack_into("<I", fixed, reloc.offset, (word & 0xFF000000) | ((delta >> 2) & 0xFFFFFF))
        rows.append({"offset": hex(reloc.offset), "target": hex(target), "symbol": reloc.symbol_name})
    if len(body) != 640 or len(rows) != 18 or len(body) > SPAN:
        raise RuntimeError(f"unexpected candidate census: body={len(body)} calls={len(rows)}")
    return bytes(fixed), rows


def make_case(name: str, id0: int, id1: int, mode: int, *,
              mode0=(), mode1=(), mask=(), availability=1,
              axis=(0.25, 0.75), angle=45.0, axis_writes=True,
              calibration=(10, 20, 30, 40, 50, 60, 70, 80)) -> dict:
    return {"name": name, "args": [id0 & 0xFFFFFFFF, id1 & 0xFFFFFFFF, mode & 0xFFFFFFFF],
            "mode0": list(mode0), "mode1": list(mode1), "mask": list(mask),
            "availability": availability, "axis": list(axis), "angle": angle,
            "axis_writes": axis_writes, "calibration": list(calibration)}


def fixtures(seed: int, samples: int) -> list[dict]:
    out = [
        make_case("mode0-ordinary", 6, 5, 0, mode0=(1, 0)),
        make_case("mode1-second-mask-short-circuit", 6, 5, 1, mode1=(1, 1), mask=(0,)),
        make_case("mode1-suppress-second-base", 6, 5, 1, mode1=(0, 1), mask=(1, 1)),
        make_case("mode1-retain-second-base", 6, 5, 1, mode1=(1, 0), mask=(1, 0)),
        make_case("mode2-both-mask", 6, 5, 2, mask=(1, 1)),
        make_case("unsupported-mode-ordinary", 6, 5, 9),
        make_case("unsupported-mode-special", 6, 15, 9, mask=(1, 0, 0, 0, 1)),
        make_case("special-availability-off", 6, 15, 0, mode0=(0, 0), availability=0, mask=(1,)),
        make_case("first-special-precedence", 14, 15, 0, mode0=(1, 0), availability=1,
                  mask=(1, 0, 0, 0, 1, 0, 0, 0), axis=(0.0, 1.0), angle=90.0),
        make_case("second-special-selector", 6, 15, 2, mask=(0, 0, 0, 0, 0, 1, 0, 0, 0),
                  axis=(1.0, 0.0), angle=180.0),
        make_case("special-12-sector", 12, 6, 2, mask=(0, 0, 1, 0, 0, 0, 1), axis=(0.5, -0.5), angle=270.0),
        make_case("special-13-sector", 6, 13, 2, mask=(0, 0, 0, 1, 0, 0, 0, 1), axis=(-1.0, 0.25), angle=359.0),
        make_case("special-first-round-no-trigger", 6, 15, 1, mode1=(0, 0), mask=(0, 0, 0, 0, 0, 0), axis=(0.0, 0.0)),
        make_case("special-second-round-no-trigger", 6, 14, 0, mode0=(0, 0), mask=(1, 0, 0, 0, 0, 0, 0, 0), axis=(0.25, 0.5)),
        make_case("special-zero-written-samples", 6, 15, 0, mode0=(0, 0), mask=(1, 0, 0, 0, 1), axis=(0.0, 0.0), angle=0.0),
        make_case("special-negative-angle-wrap", 6, 15, 0, mode0=(0, 0), mask=(1, 0, 0, 0, 1), axis=(-0.75, 0.25), angle=-15.0),
        make_case("special-no-write-reader-excluded", 6, 15, 0, mode0=(0, 0), mask=(1, 0, 0, 0, 1), axis_writes=False),
    ]
    # Signed calibration and angle boundaries for each selected sector.
    for sector_id in (14, 15, 12, 13):
        for idx, angle in enumerate((0.0, 90.0, 180.0, 359.999, 360.0)):
            triggers = {14: (1, 0, 0, 0), 15: (0, 1, 0, 0),
                        12: (0, 0, 1, 0), 13: (0, 0, 0, 1)}[sector_id]
            seq = list(triggers) + list(triggers)
            out.append(make_case(f"sector-{sector_id}-angle-{idx}", 6, sector_id, 0,
                                 mode0=(0, 0), mask=seq, axis=(0.25, 0.5), angle=angle,
                                 calibration=(-32768, 32767, -100, 100, 0, 0, 200, 400)))
    rng = random.Random(seed)
    for i in range(samples):
        id0, id1 = rng.choice((0, 1, 6, 11, 12, 13, 14, 15, 30, 31, 32)), rng.choice((0, 5, 12, 13, 14, 15, 30, 31, 32))
        mode = rng.randrange(4)
        mask = [rng.randrange(2) for _ in range(12)]
        out.append(make_case(f"seeded-{i}", id0, id1, mode,
                             mode0=(rng.randrange(2), rng.randrange(2)),
                             mode1=(rng.randrange(2), rng.randrange(2)), mask=mask,
                             availability=rng.randrange(2),
                             axis=(rng.choice((-1.0, -0.5, 0.0, 0.25, 0.5, 1.0)),
                                   rng.choice((-1.0, -0.5, 0.0, 0.25, 0.5, 1.0))),
                             angle=rng.choice((-90.0, 0.0, 45.0, 90.0, 180.0, 359.0, 360.0)),
                             calibration=tuple(rng.choice((-32768, -100, -1, 0, 1, 100, 32767)) for _ in range(8))))
    return out


def run_one(image: bytes, case: dict) -> dict:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM | unicorn.UC_MODE_LITTLE_ENDIAN)
    uc.mem_map(TEXT_BASE, (len(image) + 0xFFF) & ~0xFFF)
    uc.mem_write(TEXT_BASE, image)
    uc.mem_map(STACK, STACK_SIZE)
    uc.mem_map(RETURN, 0x1000)
    cal = bytearray(0x18)
    struct.pack_into("<8h", cal, 0, *case["calibration"])
    cal[0x10] = case["availability"] & 0xFF
    uc.mem_write(0x00465278, bytes(cal))
    returns = {"mode0_query": list(case["mode0"]),
               "mode1_query": list(case["mode1"]),
               "mask_query": list(case["mask"])}
    indices = {k: 0 for k in returns}
    trace, writes = [], []

    def hook(machine, address, _size, _user):
        if address == RETURN:
            machine.emu_stop()
            return
        if address not in CALLS:
            return
        name = CALLS[address]
        if name in returns:
            regs = (arm.UC_ARM_REG_R0,) if name != "mode0_query" else (arm.UC_ARM_REG_R0,)
            args = [machine.reg_read(r) for r in regs]
            i = indices[name]
            if "by_id" in case:
                value = case["by_id"].get(name, {}).get(str(args[0]), 0)
            else:
                value = returns[name][i] if i < len(returns[name]) else 0
            value &= 0xFFFFFFFF
            indices[name] += 1
            trace.append({"callee": name, "args": args, "result": value})
            machine.reg_write(arm.UC_ARM_REG_R0, value)
        elif name == "axis_reader":
            xptr, yptr, mode = (machine.reg_read(arm.UC_ARM_REG_R0),
                                machine.reg_read(arm.UC_ARM_REG_R1),
                                machine.reg_read(arm.UC_ARM_REG_R2))
            if case["axis_writes"]:
                machine.mem_write(xptr, struct.pack("<f", case["axis"][0]))
                machine.mem_write(yptr, struct.pack("<f", case["axis"][1]))
            base = min(xptr, yptr)
            trace.append({"callee": name, "args": ["sample_output_0", "sample_output_1", mode],
                          "raw_stack_offsets": [xptr - base, yptr - base],
                          "writes": case["axis_writes"], "values": case["axis"] if case["axis_writes"] else None,
                          "result": 1 if case["axis_writes"] else 0})
            machine.reg_write(arm.UC_ARM_REG_R0, 1 if case["axis_writes"] else 0)
        elif name == "angle":
            x = bits_f32(machine.reg_read(arm.UC_ARM_REG_S0))
            y = bits_f32(machine.reg_read(arm.UC_ARM_REG_S1))
            trace.append({"callee": name, "vfp_args": [x, y], "result": case["angle"]})
            machine.reg_write(arm.UC_ARM_REG_S0, f32_bits(case["angle"]))
        machine.reg_write(arm.UC_ARM_REG_PC, machine.reg_read(arm.UC_ARM_REG_LR))

    def mem_write(machine, _access, address, size, value, _user):
        if not (STACK <= address < STACK + STACK_SIZE):
            writes.append([address, size, value & ((1 << (size * 8)) - 1)])

    uc.hook_add(unicorn.UC_HOOK_CODE, hook)
    uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, mem_write)
    for i in range(13):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), 0xA5A50000 | i)
    uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
    uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(arm.UC_ARM_REG_FPSCR, 0)
    uc.reg_write(arm.UC_ARM_REG_D8, 0x3F123456789ABCDE)
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
    for i, value in enumerate(case["args"]):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), value)
    before = [uc.reg_read(r) for r in (arm.UC_ARM_REG_R4, arm.UC_ARM_REG_R5,
              arm.UC_ARM_REG_R6, arm.UC_ARM_REG_R7, arm.UC_ARM_REG_R8,
              arm.UC_ARM_REG_D8)]
    error = None
    try:
        uc.emu_start(ENTRY, RETURN, count=100000)
    except unicorn.UcError as exc:
        error = f"{exc}; pc={uc.reg_read(arm.UC_ARM_REG_PC):#x}"
    after = [uc.reg_read(r) for r in (arm.UC_ARM_REG_R4, arm.UC_ARM_REG_R5,
             arm.UC_ARM_REG_R6, arm.UC_ARM_REG_R7, arm.UC_ARM_REG_R8,
             arm.UC_ARM_REG_D8)]
    return {"error": error, "ret": uc.reg_read(arm.UC_ARM_REG_R0),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP), "saved_before": before,
            "saved_after": after, "fpscr": uc.reg_read(arm.UC_ARM_REG_FPSCR),
            "availability": uc.mem_read(0x00465288, 1).hex(),
            "calibration": bytes(uc.mem_read(0x00465278, 0x18)).hex(),
            "trace": trace, "writes": writes}


def run_mover(image: bytes, by_id: dict, *, axis=(0.5, -0.25), angle=45.0) -> dict:
    """Execute the original axis mover with the selected image's 0x254CA8 body."""
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM | unicorn.UC_MODE_LITTLE_ENDIAN)
    uc.mem_map(TEXT_BASE, (len(image) + 0xFFF) & ~0xFFF)
    uc.mem_write(TEXT_BASE, image)
    uc.mem_map(0x00600000, 0x10000)
    uc.mem_map(STACK, STACK_SIZE)
    uc.mem_map(RETURN, 0x1000)
    cursor = 0x00601000
    record = bytearray(0x28)
    struct.pack_into("<I", record, 0, 6)
    record[4:12] = bytes((6, 5, 32, 32, 15, 14, 32, 32))
    for off, val in ((0x10, 3), (0x14, 2), (0x18, 3), (0x1C, 3), (0x20, 0), (0x24, 0)):
        struct.pack_into("<I", record, off, val)
    uc.mem_write(cursor, bytes(record))
    cal = bytearray(0x18)
    struct.pack_into("<8h", cal, 0, 5, 20, 5, 20, 5, 20, 5, 20)
    cal[0x10] = 1
    uc.mem_write(0x00465278, bytes(cal))
    case = {"by_id": by_id, "mode0": [], "mode1": [], "mask": [],
            "availability": 1, "axis": axis, "angle": angle,
            "axis_writes": True, "calibration": (5,20,5,20,5,20,5,20)}
    indices = {"mode0_query": 0, "mode1_query": 0, "mask_query": 0}
    trace, writes = [], []

    def hook(machine, address, _size, _user):
        if address == RETURN:
            machine.emu_stop(); return
        if address == ENTRY:  # execute the selected real 0x254CA8 image body
            return
        if address not in CALLS:
            return
        name = CALLS[address]
        if name in ("mode0_query", "mode1_query", "mask_query"):
            arg = machine.reg_read(arm.UC_ARM_REG_R0)
            value = by_id.get(name, {}).get(str(arg), 0) & 0xFFFFFFFF
            indices[name] += 1
            trace.append({"callee": name, "args": [arg], "result": value})
            machine.reg_write(arm.UC_ARM_REG_R0, value)
        elif name == "axis_reader":
            xptr, yptr, mode = (machine.reg_read(arm.UC_ARM_REG_R0), machine.reg_read(arm.UC_ARM_REG_R1), machine.reg_read(arm.UC_ARM_REG_R2))
            machine.mem_write(xptr, struct.pack("<f", axis[0])); machine.mem_write(yptr, struct.pack("<f", axis[1]))
            trace.append({"callee": name, "args": ["sample_output_0", "sample_output_1", mode], "values": axis})
            machine.reg_write(arm.UC_ARM_REG_R0, 1)
        elif name == "angle":
            x = bits_f32(machine.reg_read(arm.UC_ARM_REG_S0)); y = bits_f32(machine.reg_read(arm.UC_ARM_REG_S1))
            trace.append({"callee": name, "vfp_args": [x, y], "result": angle})
            machine.reg_write(arm.UC_ARM_REG_S0, f32_bits(angle))
        machine.reg_write(arm.UC_ARM_REG_PC, machine.reg_read(arm.UC_ARM_REG_LR))

    def mem_write(machine, _access, address, size, value, _user):
        if not (STACK <= address < STACK + STACK_SIZE):
            writes.append([address, size, value & ((1 << (size * 8)) - 1)])

    uc.hook_add(unicorn.UC_HOOK_CODE, hook)
    uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, mem_write)
    for i in range(13): uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), 0x12340000 | i)
    uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10); uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(arm.UC_ARM_REG_FPSCR, 0); uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, RETURN); uc.reg_write(arm.UC_ARM_REG_R0, cursor)
    error = None
    try:
        uc.emu_start(0x001FF3C4, RETURN, count=500000)
    except unicorn.UcError as exc:
        error = f"{exc}; pc={uc.reg_read(arm.UC_ARM_REG_PC):#x}"
    return {"error": error, "ret": uc.reg_read(arm.UC_ARM_REG_R0),
            "cursor": bytes(uc.mem_read(cursor, 0x28)).hex(), "trace": trace,
            "writes": writes, "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "saved": [uc.reg_read(r) for r in (arm.UC_ARM_REG_R4, arm.UC_ARM_REG_R5,
                      arm.UC_ARM_REG_R6, arm.UC_ARM_REG_R7, arm.UC_ARM_REG_R8,
                      arm.UC_ARM_REG_R9, arm.UC_ARM_REG_R10, arm.UC_ARM_REG_R11,
                      arm.UC_ARM_REG_D8)]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=20261112)
    ap.add_argument("--samples", type=int, default=80)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    if any((args.output / name).exists() for name in ("report.json", "candidate.o", "code.production.bin", "code.production.ips")):
        raise FileExistsError(f"output artifacts already exist under {args.output}")
    image = IMAGE.read_bytes()
    if sha(image) != IMAGE_SHA:
        raise RuntimeError("pinned original image hash mismatch")
    obj = args.output / "candidate.o"
    body, relocs = candidate_body(obj)
    offset = ENTRY - TEXT_BASE
    patched = bytearray(image)
    patched[offset:offset + len(body)] = body
    if patched[offset + len(body):offset + SPAN] != image[offset + len(body):offset + SPAN]:
        raise RuntimeError("slot suffix changed")
    patch = encode_ips([(offset, body)], len(image))
    if apply_ips(image, patch) != bytes(patched):
        raise RuntimeError("slot IPS roundtrip failed")
    rows, bad = [], []
    excluded_no_write = None
    for case in fixtures(args.seed, args.samples):
        a, b = run_one(image, case), run_one(bytes(patched), case)
        comparable = case["axis_writes"]
        a_compare, b_compare = copy.deepcopy(a), copy.deepcopy(b)
        # FPSCR condition/status flags are caller-saved in the raw ABI. Preserve
        # and report them, but do not treat their value after return as contract.
        a_compare.pop("fpscr", None); b_compare.pop("fpscr", None)
        # The two local output slots may be laid out in opposite order. Compare
        # semantic output roles and values, while retaining raw stack offsets.
        for result in (a_compare, b_compare):
            for call in result["trace"]:
                if call["callee"] == "axis_reader":
                    call.pop("raw_stack_offsets", None)
        equal = a_compare == b_compare
        row = {"name": case["name"], "pass": equal if comparable else None,
               "fpscr_equal": a["fpscr"] == b["fpscr"],
               "excluded_no_write_domain": not comparable,
               "original": a, "candidate": b}
        rows.append(row)
        if comparable and not equal:
            bad.append(case["name"])
        if not comparable:
            excluded_no_write = {"name": case["name"], "original_return": a["ret"],
                                 "candidate_return": b["ret"], "original_error": a["error"],
                                 "candidate_error": b["error"], "equal_incidentally": equal}
    # Wrong first helper target must change the trace/result.
    bad_image = bytearray(patched)
    first = relocs[0]
    place = ENTRY + int(first["offset"], 16)
    word = struct.unpack_from("<I", bad_image, place - TEXT_BASE)[0]
    wrong = 0x002B902C if first["target"] != hex(0x002B902C) else 0x002BFFBC
    delta = wrong - (place + 8)
    struct.pack_into("<I", bad_image, place - TEXT_BASE,
                     (word & 0xFF000000) | ((delta >> 2) & 0xFFFFFF))
    control_case = next(c for c in fixtures(args.seed, 0) if c["name"] == "mode0-ordinary")
    neg = run_one(image, control_case) != run_one(bytes(bad_image), control_case)
    caller_compositions = []
    mover_cases = [
        ("h2-initialized-idle", {"mode0_query": {}, "mode1_query": {}, "mask_query": {}}),
        ("h2-initialized-primary-6-with-15-axis", {
            "mode0_query": {"6": 1}, "mode1_query": {"6": 0},
            "mask_query": {"15": 1}}),
        ("h2-initialized-primary-6-with-14-axis", {
            "mode0_query": {"6": 1}, "mode1_query": {"6": 0},
            "mask_query": {"14": 1}}),
    ]
    for label, returns_by_id in mover_cases:
        a = run_mover(image, returns_by_id)
        b = run_mover(bytes(patched), returns_by_id)
        caller_compositions.append({"name": label, "pass": a == b,
                                    "original": a, "candidate": b})
    report = {"target": hex(ENTRY), "source_sha256": sha(SOURCE.read_bytes()),
              "image_sha256": sha(image), "candidate_body_sha256": sha(body),
              "candidate_body_bytes": len(body), "object_sha256": sha(obj.read_bytes()),
              "slot_ips_sha256": sha(patch), "relocations": relocs,
              "seed": args.seed, "samples": args.samples,
              "direct_cases": len(rows), "comparable_cases": sum(r["pass"] is not None for r in rows),
              "fpscr_difference_cases": sum(not r["fpscr_equal"] for r in rows if r["pass"] is not None),
              "passed": len(rows) - len(bad) - (1 if excluded_no_write else 0),
              "failures": bad, "no_write_excluded_case": excluded_no_write,
              "wrong_helper_target_control_detected": neg,
              "h2_original_mover_compositions": caller_compositions, "cases": rows}
    (args.output / "code.production.bin").write_bytes(patched)
    (args.output / "code.production.ips").write_bytes(patch)
    rp = args.output / "report.json"
    rp.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("target", "candidate_body_bytes", "direct_cases", "comparable_cases", "failures", "no_write_excluded_case", "wrong_helper_target_control_detected", "h2_original_mover_compositions")}, indent=2))
    return 1 if bad or not neg or any(not row["pass"] for row in caller_compositions) else 0


if __name__ == "__main__":
    raise SystemExit(main())
