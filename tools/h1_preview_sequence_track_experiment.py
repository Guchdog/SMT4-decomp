#!/usr/bin/env python3
"""Private original-vs-C++ ARM differential for 0x002B1C8C."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.build_check import find_clang, get_armv6k_flags
from tools.semantic_experiment import arm, require_unicorn, unicorn

TEXT, INJECT, DATA, STACK = 0x00100000, 0x01000000, 0x01E00000, 0x08000000
TEXT_SIZE, INJECT_SIZE, DATA_SIZE, STACK_SIZE = 0x00400000, 0x10000, 0x00400000, 0x2000
OBJECT, TABLE = DATA + 0x1000, DATA + 0x4000
DESCRIPTOR, LOOKUP, SEQUENCE = DATA + 0x8000, DATA + 0x9000, DATA + 0xA000
SP, RETURN = STACK + 0x1000, INJECT + 0xFFF0
ENTRY, SIZE = 0x002B1C8C, 368
IMAGE = ROOT / "extracted/exefs/code.bin"
SOURCE = ROOT / "experiments/semantic_equivalence/h1_preview_sequence_track_candidate.cpp"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
BODY_SHA = "8097eb2315dd6b7f6dd72be434ee38223841c6470bfa3b923b362900572ba092"
U32 = 0xFFFFFFFF


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_linked(output: Path, source: Path = SOURCE) -> tuple[bytes, dict, Path]:
    output.mkdir(parents=True, exist_ok=True)
    image = IMAGE.read_bytes()
    if sha(image) != IMAGE_SHA:
        raise ValueError("pinned code.bin hash mismatch")
    body = image[ENTRY - TEXT:ENTRY - TEXT + SIZE]
    if len(body) != SIZE or sha(body) != BODY_SHA:
        raise ValueError("pinned 0x002B1C8C body identity mismatch")
    clang = find_clang()
    elf = output / "candidate.elf"
    argv = [str(clang), *get_armv6k_flags(ROOT, clang), "-nostdlib", "-fuse-ld=lld",
            f"-Wl,-Ttext={INJECT:#x}", "-Wl,-e,h1_preview_sequence_track_candidate",
            "-Wl,--build-id=none", str(source.resolve()), "-o", str(elf)]
    proc = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
    (output / "link-command.json").write_text(json.dumps({"argv": argv,
        "exit_code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr},
        indent=2) + "\n", encoding="utf-8")
    if proc.returncode:
        raise RuntimeError("candidate link failed: " + proc.stderr)
    objcopy, nm = clang.parent / "llvm-objcopy.exe", clang.parent / "llvm-nm.exe"
    raw = output / "candidate-text.bin"
    subprocess.run([str(objcopy), "--dump-section", f".text={raw}", str(elf)],
                   check=True, capture_output=True, text=True)
    nmr = subprocess.run([str(nm), "-n", str(elf)], check=True,
                         capture_output=True, text=True)
    symbols = {}
    for line in nmr.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 3:
            symbols[fields[2]] = int(fields[0], 16)
    name = "h1_preview_sequence_track_candidate"
    text = raw.read_bytes()
    if name not in symbols or not 0 <= symbols[name] - INJECT < len(text) <= INJECT_SIZE:
        raise RuntimeError("linked candidate entry outside mapped .text")
    meta = {"compiler": str(clang), "argv": argv, "elf_sha256": sha(elf.read_bytes()),
            "text_sha256": sha(text), "text_size": len(text), "entry": hex(symbols[name]),
            "source_sha256": sha(source.read_bytes()), "image_sha256": sha(image),
            "body_sha256": sha(body)}
    return image, {"text": text, "entry": symbols[name], "metadata": meta}, elf


class Machine:
    def __init__(self, image: bytes, linked: dict | None):
        require_unicorn()
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.mem_map(TEXT, TEXT_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
        self.uc.mem_write(TEXT, image)
        self.uc.mem_map(INJECT, INJECT_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
        if linked:
            self.uc.mem_write(INJECT, linked["text"])
        self.uc.mem_map(DATA, DATA_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.uc.mem_map(STACK, STACK_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.linked = linked
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._hook)

    def _hook(self, uc, pc, _size, _user):
        if pc == RETURN:
            uc.emu_stop()

    def run(self, object_bytes: bytes, writes: list[tuple[int, bytes]]) -> dict:
        uc = self.uc
        uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
        for i in range(13):
            uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), 0xA5000000 | i)
        uc.reg_write(arm.UC_ARM_REG_R0, OBJECT)
        uc.reg_write(arm.UC_ARM_REG_SP, SP)
        uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
        uc.mem_write(DATA, bytes([0xA5]) * DATA_SIZE)
        uc.mem_write(STACK, bytes([0x5A]) * STACK_SIZE)
        uc.mem_write(OBJECT, object_bytes)
        for address, payload in writes:
            uc.mem_write(address, payload)
        fault = None
        try:
            uc.emu_start(self.linked["entry"] if self.linked else ENTRY, 0, count=500)
        except unicorn.UcError as exc:
            fault = f"{exc} at pc={uc.reg_read(arm.UC_ARM_REG_PC):#x}"
        state = {f"r{i}": uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}"))
                 for i in range(4, 12)}
        state["sp"] = uc.reg_read(arm.UC_ARM_REG_SP)
        data = bytes(uc.mem_read(DATA, DATA_SIZE))
        stack = bytes(uc.mem_read(SP, STACK + STACK_SIZE - SP))
        return {"fault": fault, "pc": hex(uc.reg_read(arm.UC_ARM_REG_PC)),
                "r0": uc.reg_read(arm.UC_ARM_REG_R0), "state": state,
                "data_sha256": sha(data), "object": data[OBJECT-DATA:OBJECT-DATA+0x8B].hex(),
                "data": data, "caller_stack": stack}


def u16(value: int) -> bytes:
    return struct.pack("<H", value & 0xFFFF)


def s16(value: int) -> bytes:
    return struct.pack("<h", value)


def u32(value: int) -> bytes:
    return struct.pack("<I", value & U32)


def row(track: int, duration: int) -> bytes:
    return s16(track) + u16(duration)


def descriptor(entries: list[int], *, byte_length: int | None = None,
               pointer: int = LOOKUP) -> list[tuple[int, bytes]]:
    size = bytearray(0x1C)
    struct.pack_into("<H", size, 6, len(entries) * 4 if byte_length is None else byte_length)
    struct.pack_into("<I", size, 0x18, pointer)
    return [(DESCRIPTOR, bytes(size)),
            (pointer, b"".join(row(v, 0x7777) for v in entries))]


def sequence(words: list[int], pointer: int = SEQUENCE) -> list[tuple[int, bytes]]:
    data = bytearray(max(0x20, 8 + 28 * len(words)))
    for i, value in enumerate(words):
        struct.pack_into("<I", data, 8 + 28 * i, value & U32)
    return [(pointer, bytes(data))]


def fixture(name: str, *, rows: list[tuple[int, int]] | None = None,
            table: int = TABLE, row_index: int = 0, progress: int = 0,
            sequence_ptr: int = SEQUENCE, sequence_index: int = 0,
            sequence_enabled: int = 0, complete: int = 0,
            lookup: list[int] | None = None, lookup_length: int | None = None,
            extra_writes: list[tuple[int, bytes]] | None = None) -> tuple[str, bytes, list[tuple[int, bytes]]]:
    rows = rows if rows is not None else [(10, 4), (20, 4), (-1, 0)]
    lookup = lookup if lookup is not None else [30, -1, 40]
    obj = bytearray([0xCC]) * 0x8B
    struct.pack_into("<i", obj, 4, 0x12345678)
    struct.pack_into("<i", obj, 8, 0x23456789)
    struct.pack_into("<I", obj, 0x48, DESCRIPTOR)
    struct.pack_into("<I", obj, 0x70, table)
    struct.pack_into("<h", obj, 0x74, row_index)
    struct.pack_into("<h", obj, 0x76, progress)
    struct.pack_into("<I", obj, 0x78, sequence_ptr)
    struct.pack_into("<h", obj, 0x82, sequence_index)
    obj[0x84] = sequence_enabled
    obj[0x89] = complete
    obj[0x8A] = 0x5A
    writes = [(TABLE, b"".join(row(a, b) for a, b in rows))]
    writes += descriptor(lookup, byte_length=lookup_length)
    writes += sequence([0, -1])
    if extra_writes:
        writes += extra_writes
    return name, bytes(obj), writes


def fixtures() -> list[tuple[str, bytes, list[tuple[int, bytes]]]]:
    result = []
    add = result.append
    add(fixture("early completion gate", complete=1))
    add(fixture("null current track handle", table=0))
    add(fixture("duration greater than progress increments", progress=3))
    add(fixture("duration equals progress advances row", progress=4))
    add(fixture("negative progress compares signed against duration", progress=-1))
    add(fixture("next ordinary track writes return object plus four", rows=[(10, 1), (20, 2)], progress=1))
    add(fixture("next row minus two restarts at first track", rows=[(10, 1), (-2, 2)], progress=1))
    add(fixture("next row minus three is ordinary track value", rows=[(10, 1), (-3, 2)], progress=1))
    add(fixture("next row minus one with sequence disabled completes", rows=[(10, 1), (-1, 2)], progress=1))
    add(fixture("next row minus one with enabled null sequence completes", rows=[(10, 1), (-1, 2)], progress=1, sequence_enabled=1, sequence_ptr=0))
    add(fixture("current sequence minus one completes", rows=[(10, 1), (-1, 2)], progress=1, sequence_enabled=1, sequence_ptr=SEQUENCE, sequence_index=0, extra_writes=sequence([-1, 0])))
    add(fixture("next sequence minus one completes", rows=[(10, 1), (-1, 2)], progress=1, sequence_enabled=1, extra_writes=sequence([0, -1])))
    add(fixture("next sequence minus three completes", rows=[(10, 1), (-1, 2)], progress=1, sequence_enabled=1, extra_writes=sequence([0, -3])))
    add(fixture("next sequence minus two is an unmatched lookup ID", rows=[(10, 1), (-1, 2)], progress=1, sequence_enabled=1, extra_writes=sequence([0, -2])))
    add(fixture("sequence target zero selects first lookup entry", rows=[(10, 1), (-1, 2)], progress=1, sequence_enabled=1, lookup=[30, -1, 40], extra_writes=sequence([0, 0])))
    add(fixture("sequence target one selects after one sentinel", rows=[(10, 1), (-1, 2)], progress=1, sequence_enabled=1, lookup=[-1, 40, 50], extra_writes=sequence([0, 1])))
    add(fixture("sequence target ordinal not present clears handle", rows=[(10, 1), (-1, 2)], progress=1, sequence_enabled=1, lookup=[-1, 40], extra_writes=sequence([0, 3])))
    add(fixture("zero lookup count clears handle", rows=[(10, 1), (-1, 2)], progress=1, sequence_enabled=1, lookup=[], lookup_length=3, extra_writes=sequence([0, 0])))
    add(fixture("lookup byte length floors to record count", rows=[(10, 1), (-1, 2)], progress=1, sequence_enabled=1, lookup=[40], lookup_length=7, extra_writes=sequence([0, 0])))
    add(fixture("negative row index selects preceding valid entry", rows=[(10, 1), (20, 4), (30, 2)], table=TABLE + 4, row_index=-1, progress=1))
    add(fixture("minimum signed row index with mapped preceding storage", rows=[(10, 4), (20, 2)], table=TABLE + 0x20000, row_index=-0x8000, progress=0))
    add(fixture("negative sequence index selects preceding entry", rows=[(10, 1), (-1, 2)], progress=1, sequence_enabled=1, sequence_index=-1, extra_writes=sequence([0, 0], SEQUENCE - 28)))
    wrap_seq = DATA + 0x200000
    wrap_current = wrap_seq + 28 * 0x7FFF + 8
    wrap_next = wrap_seq + 28 * -0x8000 + 8
    add(fixture("sequence index maximum wraps to signed minimum", rows=[(10, 1), (-1, 2)], progress=1, sequence_enabled=1, sequence_index=0x7FFF, sequence_ptr=wrap_seq, extra_writes=[(wrap_current, u32(0)), (wrap_next, u32(0))]))
    add(fixture("duration offset mutation control", rows=[(7, 1), (20, 2)], progress=2))
    return result


def run_case(image: bytes, linked: dict, name: str, obj: bytes,
             writes: list[tuple[int, bytes]]) -> dict:
    original = Machine(image, None).run(obj, writes)
    candidate = Machine(image, linked).run(obj, writes)
    errors = []
    if original["fault"] or candidate["fault"]:
        errors.append("machine fault")
    if original["pc"] != hex(RETURN) or candidate["pc"] != hex(RETURN):
        errors.append("did not return to LR sentinel")
    if original["r0"] != candidate["r0"]:
        errors.append("r0 differs")
    if original["state"] != candidate["state"]:
        errors.append("callee-saved registers or SP differ")
    if original["data_sha256"] != candidate["data_sha256"]:
        errors.append("mapped object/lookup/sequence memory differs")
    if original["caller_stack"] != candidate["caller_stack"]:
        errors.append("caller-owned stack differs")
    def compact(run: dict) -> dict:
        return {k: run[k] for k in ("fault", "pc", "r0", "state", "data_sha256", "object")}
    return {"name": name, "passed": not errors, "errors": errors,
            "original": compact(original), "candidate": compact(candidate)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="new private output directory")
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.mkdir(parents=True, exist_ok=False)
    image, linked, elf = build_linked(output / "build")
    cases = [run_case(image, linked, name, obj, writes)
             for name, obj, writes in fixtures()]

    control_source = output / "negative_wrong_duration_offset.cpp"
    source_text = SOURCE.read_text(encoding="utf-8")
    anchor = "read_u16(at(current_entry_address) + 2)"
    if source_text.count(anchor) != 1:
        raise ValueError("mutation anchor is not unique")
    control_source.write_text(source_text.replace(anchor,
        "read_u16(at(current_entry_address) + 0)"), encoding="utf-8")
    _, mutant, mutant_elf = build_linked(output / "negative-control", control_source)
    control_fixture = next(x for x in fixtures() if x[0] == "duration offset mutation control")
    control_case = run_case(image, mutant, control_fixture[0], control_fixture[1], control_fixture[2])
    control = {"name": "duration_read_at_offset_zero_instead_of_two",
               "detected": not control_case["passed"], "errors": control_case["errors"],
               "mutant_source_sha256": sha(control_source.read_bytes()),
               "mutant_elf_sha256": sha(mutant_elf.read_bytes()), "case": control_case}
    compilation = json.loads((output / "build/link-command.json").read_text(encoding="utf-8"))
    report = {"schema_version": 1, "task_id": "h1-preview-sequence-track-candidate",
        "passed": all(c["passed"] for c in cases) and control["detected"],
        "entry": hex(ENTRY), "size": SIZE, "exit": hex(ENTRY + SIZE),
        "identity": linked["metadata"], "linked_elf_sha256": sha(elf.read_bytes()),
        "compile_exit": compilation["exit_code"], "compile_argv": compilation["argv"],
        "cases": cases, "case_count": len(cases), "negative_control": control,
        "evidence": {"compiled": "passed", "arm_differential": "partial_synthetic_valid_memory",
                     "caller": "partial_static_0x002BF9F0", "runtime": "not_run"},
        "limits": ["Finite synthetic valid, non-aliasing object/descriptor/lookup/sequence memory only.",
                   "Original pointer and signed-index arithmetic is unchecked; invalid pointers and out-of-range addresses are not defined by this evidence.",
                   "The direct H1 call at 0x002BFC48 is static only; no caller-level comparison or live object lifecycle was exercised.",
                   "No external calls occur in the pinned 0x002B1C8C body; local lookup behavior is implemented directly."]}
    report_path = output / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "case_count": len(cases),
                      "negative_control_detected": control["detected"],
                      "report": str(report_path)}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
