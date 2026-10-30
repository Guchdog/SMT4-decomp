"""Private pinned-ARM comparison for the 0x002B1DFC translation-track update."""
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

from tools.build_check import find_clang, get_armv6k_flags  # noqa: E402
from tools.semantic_experiment import arm, require_unicorn, unicorn  # noqa: E402

TEXT, INJECT, DATA, STACK = 0x00100000, 0x01000000, 0x02000000, 0x08000000
TEXT_SIZE, INJECT_SIZE, DATA_SIZE, STACK_SIZE = 0x400000, 0x10000, 0x8000, 0x2000
OBJECT, ROWS, SEQUENCE = DATA, DATA + 0x1000, DATA + 0x4000
SP, RETURN = STACK + 0x1000, INJECT + 0xFFF0
ENTRY, SIZE = 0x002B1DFC, 452
IMAGE = ROOT / "extracted/exefs/code.bin"
SOURCE = ROOT / "experiments/semantic_equivalence/h1_preview_translation_track_candidate.cpp"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
BODY_SHA = "092706575055bba00e8aab90e9ef2a45c2761fb7d12fa0f0b54dbecd35b7439a"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_linked(output: Path, source: Path = SOURCE) -> tuple[bytes, dict, Path]:
    output.mkdir(parents=True, exist_ok=True)
    image = IMAGE.read_bytes()
    if sha(image) != IMAGE_SHA:
        raise ValueError("pinned code.bin hash mismatch")
    body = image[ENTRY - TEXT:ENTRY - TEXT + SIZE]
    if len(body) != SIZE or sha(body) != BODY_SHA:
        raise ValueError("pinned 0x002B1DFC body identity mismatch")
    clang = find_clang()
    elf = output / "candidate.elf"
    cmd = [str(clang), *get_armv6k_flags(ROOT, clang), "-nostdlib", "-fuse-ld=lld",
           f"-Wl,-Ttext={INJECT:#x}", "-Wl,-e,h1_preview_translation_track_candidate",
           "-Wl,--build-id=none", str(source.resolve()), "-o", str(elf)]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    (output / "link-command.json").write_text(json.dumps({"argv": cmd, "exit_code": proc.returncode,
        "stdout": proc.stdout, "stderr": proc.stderr}, indent=2) + "\n", encoding="utf-8")
    if proc.returncode:
        raise RuntimeError("candidate link failed: " + proc.stderr)
    objcopy = clang.parent / "llvm-objcopy.exe"
    nm = clang.parent / "llvm-nm.exe"
    if not objcopy.is_file() or not nm.is_file():
        raise RuntimeError("llvm-objcopy and llvm-nm are required")
    raw = output / "candidate-text.bin"
    subprocess.run([str(objcopy), "--dump-section", f".text={raw}", str(elf)], check=True,
                   capture_output=True, text=True)
    symbols = subprocess.run([str(nm), "-n", str(elf)], check=True,
                             capture_output=True, text=True).stdout
    addresses = {fields[2]: int(fields[0], 16) for line in symbols.splitlines()
                 if len(fields := line.split()) >= 3}
    symbol = "h1_preview_translation_track_candidate"
    if symbol not in addresses:
        raise RuntimeError("candidate entry is absent from linked ELF")
    text = raw.read_bytes()
    offset = addresses[symbol] - INJECT
    if not 0 <= offset < len(text) <= INJECT_SIZE:
        raise RuntimeError("candidate entry outside extracted .text")
    meta = {"compiler": str(clang), "argv": cmd, "elf_sha256": sha(elf.read_bytes()),
            "text_sha256": sha(text), "text_size": len(text), "entry": hex(addresses[symbol]),
            "source_sha256": sha(source.read_bytes()), "image_sha256": sha(image),
            "function_sha256": sha(body)}
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
        self.fault = None

    def _hook(self, uc, pc, _size, _user):
        if pc == RETURN:
            uc.emu_stop()

    def run(self, object_bytes: bytes, rows: bytes, sequence: bytes = b"") -> dict:
        self.uc.mem_write(DATA, bytes([0xA5]) * DATA_SIZE)
        self.uc.mem_write(STACK, bytes([0x5A]) * STACK_SIZE)
        if len(object_bytes) < 0x8B:
            raise ValueError("track fixture too short")
        self.uc.mem_write(OBJECT, object_bytes)
        if rows:
            self.uc.mem_write(ROWS, rows)
        if sequence:
            self.uc.mem_write(SEQUENCE, sequence)
        for i in range(13):
            self.uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), 0xA5A50000 | i)
        self.uc.reg_write(arm.UC_ARM_REG_R0, OBJECT)
        self.uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
        self.uc.reg_write(arm.UC_ARM_REG_SP, SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.reg_write(arm.UC_ARM_REG_FPSCR, 0x01000000)
        for i in range(8, 16):
            self.uc.reg_write(getattr(arm, f"UC_ARM_REG_D{i}"), 0x1111222233334400 + i)
        self.fault = None
        try:
            start = self.linked["entry"] if self.linked else ENTRY
            self.uc.emu_start(start, 0, count=4096)
        except unicorn.UcError as exc:
            self.fault = f"{exc} at pc={self.uc.reg_read(arm.UC_ARM_REG_PC):#x}"
        preserved = {f"r{i}": self.uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}"))
                     for i in range(4, 12)}
        preserved["sp"] = self.uc.reg_read(arm.UC_ARM_REG_SP)
        preserved_d = [self.uc.reg_read(getattr(arm, f"UC_ARM_REG_D{i}")) for i in range(8, 16)]
        return {"fault": self.fault, "pc": hex(self.uc.reg_read(arm.UC_ARM_REG_PC)),
                "r0": self.uc.reg_read(arm.UC_ARM_REG_R0), "preserved": preserved,
                "preserved_d8_d15": preserved_d,
                "fpscr": self.uc.reg_read(arm.UC_ARM_REG_FPSCR),
                "vfp_scratch_s0_s3": [self.uc.reg_read(getattr(arm, f"UC_ARM_REG_S{i}")) for i in range(4)],
                "data": bytes(self.uc.mem_read(DATA, DATA_SIZE)).hex(),
                "caller_stack": bytes(self.uc.mem_read(SP, STACK + STACK_SIZE - SP)).hex()}


def put_u32(buf: bytearray, offset: int, value: int):
    struct.pack_into("<I", buf, offset, value & 0xFFFFFFFF)


def float_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def track_fixture(*, table=ROWS, animation=0, progress=0, direction=0,
                  completed=0, sequence=0, sequence_index=0, enabled=0,
                  current=10.0, neighbor1=20.0, neighbor2=30.0,
                  change_flag=1) -> bytearray:
    b = bytearray([0xCC]) * 0x8B
    put_u32(b, 0x24, float_bits(current))
    put_u32(b, 0x28, float_bits(neighbor1))
    put_u32(b, 0x2C, float_bits(neighbor2))
    put_u32(b, 0x64, table)
    struct.pack_into("<hhb", b, 0x68, animation, progress, direction)
    put_u32(b, 0x78, sequence)
    struct.pack_into("<h", b, 0x80, sequence_index)
    b[0x84] = enabled & 0xFF
    b[0x88] = completed & 0xFF
    b[0x8A] = change_flag & 0xFF
    return b


def row_bytes(*rows: tuple[float, float, int, int]) -> bytes:
    return b"".join(struct.pack("<ffHBx", a, b, d, mode & 0xFF) for a, b, d, mode in rows)


def sequence_bytes(*entries: tuple[int, int]) -> bytes:
    # Each entry's animation/sentinel word and signed direction byte live at
    # the sequence base offsets +0x14 and +0x18, with 0x1C-byte stride.
    out = bytearray(0x14 + 0x1C * len(entries))
    for index, (word, direction) in enumerate(entries):
        struct.pack_into("<I", out, 0x14 + 0x1C * index, word & 0xFFFFFFFF)
        struct.pack_into("<b", out, 0x18 + 0x1C * index, direction)
    return bytes(out)


def run_case(image: bytes, linked: dict, name: str, obj: bytearray,
             rows: bytes, seq: bytes = b"") -> dict:
    original_machine = Machine(image, None)
    candidate_machine = Machine(image, linked)
    if read_ptr(obj, 0x78) == SEQUENCE and not seq:
        raise ValueError(f"case {name} points at an absent sequence")
    original = original_machine.run(bytes(obj), rows, seq)
    candidate = candidate_machine.run(bytes(obj), rows, seq)
    errors = []
    if original["fault"] or candidate["fault"]:
        errors.append("machine fault")
    if original["pc"] != hex(RETURN) or candidate["pc"] != hex(RETURN):
        errors.append("did not return to LR sentinel")
    if original["r0"] != candidate["r0"]:
        errors.append("r0 differs")
    if original["preserved"] != candidate["preserved"]:
        errors.append("callee-saved GPR or SP differs")
    if original["preserved_d8_d15"] != candidate["preserved_d8_d15"]:
        errors.append("callee-saved VFP d8-d15 differs")
    if original["fpscr"] != candidate["fpscr"]:
        errors.append("FPSCR differs")
    if original["data"] != candidate["data"]:
        errors.append("object/table/sequence memory differs")
    if original["caller_stack"] != candidate["caller_stack"]:
        errors.append("caller-owned stack differs")
    return {"name": name, "passed": not errors, "errors": errors,
            "original": original, "candidate": candidate}


def read_ptr(obj: bytearray, offset: int) -> int:
    return struct.unpack_from("<I", obj, offset)[0]


def run(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    image, linked, elf = build_linked(output)
    table = row_bytes((1.0, 5.0, 8, 0), (11.0, 13.0, 8, 1),
                      (-3.0, 7.0, 8, 0))
    tests = [
        ("disabled completion gate returns unchanged", track_fixture(completed=1), table, b""),
        ("null translation table returns unchanged", track_fixture(table=0), table, b""),
        ("mode zero direction zero endpoint", track_fixture(progress=8, direction=0),
         row_bytes((1.0, 5.0, 0, 0))),
        ("mode zero direction one endpoint", track_fixture(progress=8, direction=1),
         row_bytes((1.0, 5.0, 0, 0))),
        ("mode nonzero direction zero endpoint", track_fixture(progress=8, direction=0),
         row_bytes((1.0, 5.0, 0, 1))),
        ("mode nonzero direction one endpoint", track_fixture(progress=8, direction=1),
         row_bytes((1.0, 5.0, 0, 1))),
        ("interpolation direction zero", track_fixture(progress=1, direction=0,
            current=10.0), row_bytes((1.0, 5.0, 8, 0))),
        ("interpolation direction one reversed delta", track_fixture(progress=1, direction=1,
            current=10.0), row_bytes((1.0, 5.0, 8, 0))),
        ("duration one above progress interpolates", track_fixture(progress=7, direction=0,
            current=10.0), row_bytes((1.0, 5.0, 8, 0))),
        ("duration equals progress selects endpoint", track_fixture(progress=8, direction=0),
            row_bytes((1.0, 5.0, 8, 1))),
        ("sequence disabled marks complete", track_fixture(progress=8,
            enabled=0), row_bytes((1.0, 5.0, 8, 0))),
        ("sequence enabled null pointer marks complete", track_fixture(progress=8,
            enabled=1, sequence=0), row_bytes((1.0, 5.0, 8, 0))),
        ("sequence current minus one sentinel", track_fixture(progress=8,
            enabled=1, sequence=SEQUENCE), row_bytes((1.0, 5.0, 8, 0)),
         sequence_bytes((-1, 0), (1, 1))),
        ("sequence next minus one sentinel", track_fixture(progress=8,
            enabled=1, sequence=SEQUENCE), row_bytes((1.0, 5.0, 8, 0)),
         sequence_bytes((0, 0), (-1, 1))),
        ("sequence next minus three sentinel", track_fixture(progress=8,
            enabled=1, sequence=SEQUENCE), row_bytes((1.0, 5.0, 8, 0)),
         sequence_bytes((0, 0), (-3, 1))),
        ("sequence next minus two restarts index", track_fixture(progress=8,
            enabled=1, sequence=SEQUENCE, sequence_index=1), table,
         sequence_bytes((2, 0), (1, -1), (-2, 1))),
        ("sequence ordinary next updates index and animation", track_fixture(progress=8,
            enabled=1, sequence=SEQUENCE), table,
         sequence_bytes((0, 0), (1, -1))),
    ]
    cases = [run_case(image, linked, name, obj, rows, seq) for name, obj, rows, *rest in tests
             for seq in (rest[0] if rest else b"",)]

    # Wrong-offset mutation: send the common-tail neighbor copy to +0x30.
    text = SOURCE.read_text(encoding="utf-8")
    anchor = "    write_u32(object + 0x2C, current_value);\n"
    if text.count(anchor) != 1:
        raise ValueError("negative-control common-tail anchor is not unique")
    mutant_source = output / "negative_wrong_neighbor_offset.cpp"
    mutant_source.write_text(text.replace(anchor,
        "    write_u32(object + 0x30, current_value); // deliberate wrong offset\n"), encoding="utf-8")
    mutant_image, mutant_linked, mutant_elf = build_linked(output / "negative-control", mutant_source)
    neg_obj = track_fixture(progress=8, direction=0)
    neg_rows = row_bytes((1.0, 5.0, 8, 1))
    negative = run_case(mutant_image, mutant_linked, "negative wrong +0x30 neighbor offset",
                        neg_obj, neg_rows)
    control = {"name": "wrong_common_tail_neighbor_offset", "detected": not negative["passed"],
               "errors": negative["errors"], "mutant_source_sha256": sha(mutant_source.read_bytes()),
               "mutant_elf_sha256": sha(mutant_elf.read_bytes()), "case": negative}
    report = {
        "task_id": "h1-preview-translation-track-candidate",
        "passed": all(c["passed"] for c in cases) and control["detected"],
        "entry": hex(ENTRY), "size": SIZE, "exit_exclusive": hex(ENTRY + SIZE),
        "identity": linked["metadata"], "linked_elf_sha256": sha(elf.read_bytes()),
        "cases": cases, "case_count": len(cases), "negative_controls": [control],
        "first_mismatch": next(({"case": c["name"], "errors": c["errors"]}
                                 for c in cases if not c["passed"]), None),
        "evidence": {"compiled": "passed", "arm_differential": "partial_bounded_local_body",
                     "caller": "partial_static_h1_preview_helper", "runtime": "not_run"},
        "limits": [
            "The helper is tested against valid synthetic object, translation-row, and sequence storage only; invalid indices/pointers and aliasing are unsupported.",
            "The candidate body has no external callees; its VFP work is directly compared to the pinned body, but the containing helper/caller lifecycle and live object binding are not tested.",
            "VFP s0-s3 are recorded as caller-saved diagnostics, not required to match; final FPSCR, object float bits, preserved d8-d15, callee-saved GPRs, SP, caller-owned stack, and full data mapping are compared.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.output)
    print(f"translation-track differential: {'PASS' if report['passed'] else 'FAIL'} "
          f"{sum(c['passed'] for c in report['cases'])}/{report['case_count']}; "
          f"negative control={'detected' if report['negative_controls'][0]['detected'] else 'missed'}; "
          f"report {args.output / 'report.json'}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
