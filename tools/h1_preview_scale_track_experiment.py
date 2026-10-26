#!/usr/bin/env python3
"""Private pinned-ARM differential for the self-contained 0x002B1FC0 helper."""
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

TEXT, INJECT, DATA, STACK = 0x00100000, 0x01000000, 0x02000000, 0x08000000
TEXT_SIZE, INJECT_SIZE, DATA_SIZE, STACK_SIZE = 0x400000, 0x10000, 0x10000, 0x2000
OBJECT, ROWS, SEQUENCE = DATA, DATA + 0x1000, DATA + 0x4000
SP, RETURN = STACK + 0x1000, INJECT + 0xFFF0
ENTRY, SIZE = 0x002B1FC0, 444
IMAGE = ROOT / "extracted/exefs/code.bin"
SOURCE = ROOT / "experiments/semantic_equivalence/h1_preview_scale_track_candidate.cpp"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
BODY_SHA = "9d9948ecc56a1a6dd32012eacce76ce8cffdf3902632f8efc85245d9dd1f5811"
U32 = 0xFFFFFFFF
DREGS = tuple(getattr(arm, f"UC_ARM_REG_D{i}") for i in range(8, 16))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_linked(output: Path, source: Path = SOURCE) -> tuple[bytes, dict, Path]:
    output.mkdir(parents=True, exist_ok=True)
    image = IMAGE.read_bytes()
    if sha(image) != IMAGE_SHA:
        raise ValueError("pinned code.bin hash mismatch")
    body = image[ENTRY - TEXT:ENTRY - TEXT + SIZE]
    if len(body) != SIZE or sha(body) != BODY_SHA:
        raise ValueError("pinned 0x002B1FC0 body identity mismatch")
    clang = find_clang()
    elf = output / "candidate.elf"
    cmd = [str(clang), *get_armv6k_flags(ROOT, clang), "-nostdlib", "-fuse-ld=lld",
           f"-Wl,-Ttext={INJECT:#x}", "-Wl,-e,h1_preview_scale_track_candidate",
           "-Wl,--build-id=none", str(source.resolve()), "-o", str(elf)]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    (output / "link-command.json").write_text(json.dumps({"argv": cmd, "exit_code": proc.returncode,
        "stdout": proc.stdout, "stderr": proc.stderr}, indent=2) + "\n", encoding="utf-8")
    if proc.returncode:
        raise RuntimeError("candidate link failed: " + proc.stderr)
    tool_dir = clang.parent
    objcopy, nm = tool_dir / "llvm-objcopy.exe", tool_dir / "llvm-nm.exe"
    if not objcopy.is_file() or not nm.is_file():
        raise RuntimeError("llvm-objcopy and llvm-nm are required")
    raw = output / "candidate-text.bin"
    subprocess.run([str(objcopy), "--dump-section", f".text={raw}", str(elf)], check=True,
                   capture_output=True, text=True)
    nm_result = subprocess.run([str(nm), "-n", str(elf)], check=True,
                               capture_output=True, text=True)
    symbols = {}
    for line in nm_result.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 3:
            symbols[fields[2]] = int(fields[0], 16)
    symbol = "h1_preview_scale_track_candidate"
    if symbol not in symbols:
        raise RuntimeError("linked ELF lacks candidate entry")
    text = raw.read_bytes()
    offset = symbols[symbol] - INJECT
    if not 0 <= offset < len(text) <= INJECT_SIZE:
        raise RuntimeError("candidate entry outside mapped .text")
    meta = {"compiler": str(clang), "argv": cmd, "elf_sha256": sha(elf.read_bytes()),
            "text_sha256": sha(text), "text_size": len(text), "entry": hex(symbols[symbol]),
            "source_sha256": sha(source.read_bytes()), "image_sha256": sha(image),
            "body_sha256": sha(body)}
    return image, {"text": text, "entry": INJECT + offset, "metadata": meta}, elf


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

    def run(self, object_bytes: bytes, row_bytes: bytes = b"", sequence_bytes: bytes = b"") -> dict:
        uc = self.uc
        uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
        for i in range(13):
            uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), 0xA5000000 | i)
        for i, reg in enumerate(DREGS):
            uc.reg_write(reg, 0xD800000000000000 | (0x01010101 * (i + 1)))
        uc.reg_write(arm.UC_ARM_REG_R0, OBJECT)
        uc.reg_write(arm.UC_ARM_REG_SP, SP)
        uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
        # ARM11 VFP instructions trap as undefined unless the FPEXC enable bit
        # is set, even in this isolated user-mode execution harness.
        uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        uc.reg_write(arm.UC_ARM_REG_FPSCR, 0x01000000)
        uc.mem_write(DATA, bytes([0xA5]) * DATA_SIZE)
        uc.mem_write(STACK, bytes([0x5A]) * STACK_SIZE)
        if len(object_bytes) < 0x8B:
            raise ValueError("object fixture too short")
        uc.mem_write(OBJECT, object_bytes)
        if row_bytes:
            uc.mem_write(ROWS, row_bytes)
        if sequence_bytes:
            uc.mem_write(SEQUENCE, sequence_bytes)
        fault = None
        try:
            uc.emu_start(self.linked["entry"] if self.linked else ENTRY, 0, count=500)
        except unicorn.UcError as exc:
            fault = f"{exc} at pc={uc.reg_read(arm.UC_ARM_REG_PC):#x}"
        preserved = {f"r{i}": uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}"))
                     for i in range(4, 12)}
        preserved["sp"] = uc.reg_read(arm.UC_ARM_REG_SP)
        preserved["fpscr"] = uc.reg_read(arm.UC_ARM_REG_FPSCR)
        preserved.update({f"d{i+8}": uc.reg_read(reg) for i, reg in enumerate(DREGS)})
        return {"fault": fault, "pc": hex(uc.reg_read(arm.UC_ARM_REG_PC)),
                "r0": uc.reg_read(arm.UC_ARM_REG_R0), "state": preserved,
                "data": bytes(uc.mem_read(DATA, DATA_SIZE)),
                # Candidate compiler spills below entry SP; caller-owned stack
                # is the unchanged live region at and above the entry SP.
                "caller_stack": bytes(uc.mem_read(SP, STACK + STACK_SIZE - SP))}


def put_u32(buffer: bytearray, offset: int, value: int):
    struct.pack_into("<I", buffer, offset, value & U32)


def put_s16(buffer: bytearray, offset: int, value: int):
    struct.pack_into("<h", buffer, offset, value)


def object_fixture(*, table=ROWS, row_index=0, progress=0, direction=0,
                   sequence=0, sequence_index=0, sequence_enabled=0,
                   complete=0, scale=0.75, complete_other=0x5A) -> bytearray:
    obj = bytearray([0xCC]) * 0x8B
    put_u32(obj, 0x20, struct.unpack("<I", struct.pack("<f", scale))[0])
    put_u32(obj, 0x58, table)
    put_s16(obj, 0x5C, row_index)
    put_s16(obj, 0x5E, progress)
    obj[0x60] = direction & 0xFF
    put_u32(obj, 0x78, sequence)
    put_s16(obj, 0x7E, sequence_index)
    obj[0x84] = sequence_enabled & 0xFF
    obj[0x87] = complete & 0xFF
    obj[0x8A] = complete_other & 0xFF
    return obj


def row_entry(first: float, second: float, duration: int, row_mode: int) -> bytes:
    row = bytearray(12)
    struct.pack_into("<ffH", row, 0, first, second, duration & 0xFFFF)
    row[0x0A] = row_mode & 0xFF
    return bytes(row)


def sequence_entries(first_word: int, next_word: int, *,
                     first_direction: int = 0, next_direction: int = 0) -> bytes:
    sequence = bytearray([0xA5]) * 0x38
    put_u32(sequence, 0x0C, first_word)
    sequence[0x10] = first_direction & 0xFF
    put_u32(sequence, 0x1C + 0x0C, next_word)
    sequence[0x1C + 0x10] = next_direction & 0xFF
    return bytes(sequence)


def run_case(image: bytes, linked: dict, name: str, obj: bytes,
             rows: bytes = b"", sequence: bytes = b"") -> dict:
    original = Machine(image, None).run(obj, rows, sequence)
    candidate = Machine(image, linked).run(obj, rows, sequence)
    errors = []
    if original["fault"] or candidate["fault"]:
        errors.append("machine fault")
    if original["pc"] != hex(RETURN) or candidate["pc"] != hex(RETURN):
        errors.append("did not return to LR sentinel")
    if original["r0"] != candidate["r0"]:
        errors.append("r0 differs")
    if original["state"] != candidate["state"]:
        errors.append("callee-saved/FPSCR state differs")
    if original["data"] != candidate["data"]:
        errors.append("synthetic object/table/sequence memory differs")
    if original["caller_stack"] != candidate["caller_stack"]:
        errors.append("caller-owned stack differs")
    return {"name": name, "passed": not errors, "errors": errors,
            "original": {"fault": original["fault"], "pc": original["pc"],
                         "r0": hex(original["r0"]), "state": original["state"],
                         "object": original["data"][:0x8B].hex()},
            "candidate": {"fault": candidate["fault"], "pc": candidate["pc"],
                          "r0": hex(candidate["r0"]), "state": candidate["state"],
                          "object": candidate["data"][:0x8B].hex()}}


def fixtures():
    base0 = row_entry(1.25, -2.5, 8, 1)
    base1 = row_entry(-3.0, 5.5, 8, 1)
    rows_two = base0 + base1
    yield ("gate byte already complete", object_fixture(complete=1), rows_two, b"")
    yield ("null scale-track table returns", object_fixture(table=0), b"", b"")
    yield ("endpoint mode nonzero direction zero", object_fixture(progress=8), row_entry(1.25, -2.5, 8, 1), b"")
    yield ("endpoint mode nonzero direction nonzero", object_fixture(progress=9, direction=1), row_entry(1.25, -2.5, 8, 1), b"")
    yield ("endpoint row-mode zero selects opposite endpoint", object_fixture(progress=8), row_entry(1.25, -2.5, 8, 0), b"")
    yield ("endpoint row-mode zero direction nonzero selects opposite endpoint", object_fixture(progress=8, direction=1), row_entry(1.25, -2.5, 8, 0), b"")
    yield ("interpolation direction zero duration eight", object_fixture(progress=1, direction=0), row_entry(-3.5, 7.25, 8, 1), b"")
    yield ("interpolation direction nonzero duration eight", object_fixture(progress=1, direction=1), row_entry(-3.5, 7.25, 8, 1), b"")
    yield ("progress signed minimum with zero duration", object_fixture(progress=-0x8000), row_entry(1.0, 0.0, 0, 1), b"")
    yield ("negative progress with zero duration exercises VFP divide by zero", object_fixture(progress=-1), row_entry(1.0, 0.0, 0, 1), b"")
    yield ("progress maximum increments with halfword wrap", object_fixture(progress=0x7FFF), row_entry(-1.0, 1.0, 0xFFFF, 1), b"")
    yield ("duration one progress zero interpolation", object_fixture(progress=0), row_entry(0.125, 1.125, 1, 1), b"")
    yield ("zero sequence feature sets completion", object_fixture(progress=8, sequence_enabled=0), row_entry(2.0, 4.0, 8, 0), b"")
    yield ("enabled null sequence sets completion", object_fixture(progress=8, sequence_enabled=1, sequence=0), row_entry(2.0, 4.0, 8, 0), b"")
    yield ("current sequence end marker sets completion", object_fixture(progress=8, sequence=SEQUENCE, sequence_enabled=1), row_entry(2.0, 4.0, 8, 0), sequence_entries(-1, 1))
    yield ("next sequence minus one marker sets completion", object_fixture(progress=8, sequence=SEQUENCE, sequence_enabled=1), row_entry(2.0, 4.0, 8, 0), sequence_entries(0, -1))
    yield ("next sequence minus three marker sets completion", object_fixture(progress=8, sequence=SEQUENCE, sequence_enabled=1), row_entry(2.0, 4.0, 8, 0), sequence_entries(0, -3))
    sequence_rows = row_entry(2.0, 4.0, 8, 0) + row_entry(-1.0, 9.0, 8, 1)
    yield ("next sequence minus two restarts at first entry", object_fixture(progress=8, sequence=SEQUENCE, sequence_enabled=1), sequence_rows, sequence_entries(1, -2, first_direction=-1))
    yield ("ordinary sequence entry selects row and signed direction", object_fixture(progress=8, sequence=SEQUENCE, sequence_enabled=1, complete_other=1), sequence_rows, sequence_entries(0, 1, next_direction=-1))
    yield ("negative row index selects preceding valid row", object_fixture(table=ROWS + 12, row_index=-1, progress=8), rows_two, b"")
    yield ("signed halfword progress and max duration interpolate", object_fixture(progress=-1), row_entry(0.0, 1.0, 0xFFFF, 1), b"")
    yield ("finite extreme values preserve VFP operation order", object_fixture(progress=1, direction=1, scale=-3.0e38), row_entry(3.0e38, -3.0e38, 2, 1), b"")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="new private output directory")
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.mkdir(parents=True, exist_ok=False)

    image, linked, elf = build_linked(output / "build")
    results = [run_case(image, linked, name, bytes(obj), rows, sequence)
               for name, obj, rows, sequence in fixtures()]

    control_source = output / "negative_omit_sequence_scale_clear.cpp"
    text = SOURCE.read_text(encoding="utf-8")
    anchor = "    write_u8(object + 0x8A, 0);\n"
    if text.count(anchor) != 1:
        raise ValueError("negative-control anchor is not unique")
    control_source.write_text(text.replace(anchor,
        "    // negative control: omit original +0x8A clear\n"), encoding="utf-8")
    mutant_image, mutant_linked, mutant_elf = build_linked(output / "negative-control", control_source)
    control_case = run_case(mutant_image, mutant_linked,
        "negative control omits selected-sequence +0x8A clear",
        bytes(object_fixture(progress=8, sequence=SEQUENCE, sequence_enabled=1, complete_other=1)),
        row_entry(2.0, 4.0, 8, 0) + row_entry(-1.0, 9.0, 8, 1),
        sequence_entries(0, 1, next_direction=1))
    control = {"name": "missing_selected_sequence_scale_clear", "detected": not control_case["passed"],
               "errors": control_case["errors"], "mutant_source_sha256": sha(control_source.read_bytes()),
               "mutant_elf_sha256": sha(mutant_elf.read_bytes()), "case": control_case}

    compilation = json.loads((output / "build/link-command.json").read_text(encoding="utf-8"))
    report = {
        "schema_version": 1,
        "task_id": "h1-preview-scale-track-candidate",
        "passed": all(case["passed"] for case in results) and control["detected"],
        "entry": hex(ENTRY), "size": SIZE, "exit": hex(ENTRY + SIZE),
        "identity": linked["metadata"], "linked_elf_sha256": sha(elf.read_bytes()),
        "compile_exit": compilation["exit_code"], "compile_argv": compilation["argv"],
        "cases": results, "case_count": len(results), "negative_control": control,
        "evidence": {"compiled": "passed", "arm_differential": "partial_valid_synthetic_track_memory",
                     "caller": "partial_static_0x002BF9F0", "runtime": "not_run"},
        "limits": [
            "Finite synthetic valid-memory fixtures; no captured H1 track object or runtime scene was exercised.",
            "Table and sequence indices/pointers are unchecked in the original; only bounded valid storage is tested.",
            "Overlapping object/table/sequence memory, MMIO, concurrent mutation, invalid addresses, and arbitrary index wrap domains remain unvalidated.",
            "No external functions occur in the pinned 0x002B1FC0 body; the candidate implements its own sequence/endpoint/interpolation logic.",
            "The helper is statically called at 0x002BFC30 with object r4; the encompassing preview helper's own external dependencies/runtime binding remain separate unknowns."
        ]
    }
    report_path = output / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "case_count": len(results),
                      "negative_control_detected": control["detected"],
                      "report": str(report_path)}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
