"""Private pinned-ARM differential for interior animation row setter 0x002BDAC0."""
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
TEXT_SIZE, INJECT_SIZE, DATA_SIZE, STACK_SIZE = 0x400000, 0x10000, 0x4000, 0x2000
OBJECT, ROWS = DATA, DATA + 0x200
SP, RETURN = STACK + 0x1000, INJECT + 0xFFF0
ENTRY, SIZE = 0x002BDAC0, 108
IMAGE = ROOT / "extracted/exefs/code.bin"
SOURCE = ROOT / "experiments/semantic_equivalence/h1_animation_row_setter_candidate.cpp"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
BODY_SHA = "e9c60d31db041884aa6fe44db47bcabc849bf08464d1465a68cad24c4b1f152a"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_linked(output: Path, source: Path = SOURCE) -> tuple[bytes, dict, Path]:
    output.mkdir(parents=True, exist_ok=True)
    image = IMAGE.read_bytes()
    if sha(image) != IMAGE_SHA:
        raise ValueError("pinned code.bin hash mismatch")
    body = image[ENTRY - TEXT:ENTRY - TEXT + SIZE]
    if len(body) != SIZE or sha(body) != BODY_SHA:
        raise ValueError("pinned 0x002BDAC0 body identity mismatch")
    clang = find_clang()
    elf = output / "candidate.elf"
    cmd = [str(clang), *get_armv6k_flags(ROOT, clang), "-nostdlib", "-fuse-ld=lld",
           f"-Wl,-Ttext={INJECT:#x}", "-Wl,-e,h1_animation_row_setter_candidate",
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
    nm_result = subprocess.run([str(nm), "-n", str(elf)], check=True, capture_output=True, text=True)
    symbols = {}
    for line in nm_result.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 3:
            symbols[fields[2]] = int(fields[0], 16)
    symbol = "h1_animation_row_setter_candidate"
    if symbol not in symbols:
        raise RuntimeError("candidate entry is absent from linked ELF")
    text = raw.read_bytes()
    offset = symbols[symbol] - INJECT
    if not 0 <= offset < len(text) <= INJECT_SIZE:
        raise RuntimeError("candidate entry outside extracted .text")
    meta = {"compiler": str(clang), "argv": cmd, "elf_sha256": sha(elf.read_bytes()),
            "text_sha256": sha(text), "text_size": len(text), "entry": hex(symbols[symbol]),
            "source_sha256": sha(source.read_bytes()), "image_sha256": sha(image),
            "helper_sha256": sha(body)}
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

    def run(self, ptr: int, object_bytes: bytes | None, row_bytes: bytes = b"",
            *, row_index: int = 0, mode: int = 0) -> dict:
        self.uc.mem_write(DATA, bytes([0xA5]) * DATA_SIZE)
        self.uc.mem_write(STACK, bytes([0x5A]) * STACK_SIZE)
        if object_bytes is not None:
            if len(object_bytes) < 0x8B:
                raise ValueError("object fixture too short")
            self.uc.mem_write(OBJECT, object_bytes)
        if row_bytes:
            self.uc.mem_write(ROWS, row_bytes)
        for i in range(13):
            self.uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), 0xA5A50000 | i)
        self.uc.reg_write(arm.UC_ARM_REG_R0, ptr)
        self.uc.reg_write(arm.UC_ARM_REG_R1, row_index & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R2, mode & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
        self.uc.reg_write(arm.UC_ARM_REG_SP, SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
        self.fault = None
        try:
            start = self.linked["entry"] if self.linked else ENTRY
            self.uc.emu_start(start, 0, count=256)
        except unicorn.UcError as exc:
            self.fault = f"{exc} at pc={self.uc.reg_read(arm.UC_ARM_REG_PC):#x}"
        preserved = {f"r{i}": self.uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4, 12)}
        preserved["sp"] = self.uc.reg_read(arm.UC_ARM_REG_SP)
        return {"fault": self.fault, "pc": hex(self.uc.reg_read(arm.UC_ARM_REG_PC)),
                "r0": self.uc.reg_read(arm.UC_ARM_REG_R0), "preserved": preserved,
                "data": bytes(self.uc.mem_read(DATA, DATA_SIZE)).hex(),
                # Ignore temporary bytes below entry SP; callees may spill
                # there while preserving SP. Compare only caller-owned space.
                "caller_stack": bytes(self.uc.mem_read(SP, STACK + STACK_SIZE - SP)).hex()}


def put_i32(buf: bytearray, offset: int, value: int):
    struct.pack_into("<i", buf, offset, value)


def put_u32(buf: bytearray, offset: int, value: int):
    struct.pack_into("<I", buf, offset, value & 0xFFFFFFFF)


def object_fixture(table=ROWS, *, initial=(0x12345678, 0x87654321),
                   old_index=9, old_progress=0x1234, old_mode=0x7F,
                   old_complete=1, old_result=1) -> bytes:
    b = bytearray([0xCC]) * 0x8B
    put_u32(b, 0x0C, initial[0]); put_u32(b, 0x10, initial[1])
    put_u32(b, 0x4C, table)
    struct.pack_into("<H", b, 0x50, old_index & 0xFFFF)
    struct.pack_into("<H", b, 0x52, old_progress & 0xFFFF)
    b[0x54] = old_mode & 0xFF
    b[0x86] = old_complete & 0xFF
    b[0x8A] = old_result & 0xFF
    return bytes(b)


def row_fixture(x0: int, y0: int, x1: int, y1: int) -> bytes:
    return struct.pack("<hhhh", x0, y0, x1, y1)


def compare_case(image: bytes, linked: dict, name: str, obj: bytes | None,
                 rows: bytes = b"", row_index: int = 0, mode: int = 0,
                 expected_fault: bool = False, mutant: bool = False) -> dict:
    original = Machine(image, None).run(OBJECT if obj is not None else 0, obj, rows,
                                        row_index=row_index, mode=mode)
    candidate = Machine(image, linked).run(OBJECT if obj is not None else 0, obj, rows,
                                           row_index=row_index, mode=mode)
    errors = []
    if expected_fault:
        if original["fault"] is None or candidate["fault"] is None:
            errors.append("expected both invalid-null-pointer executions to fault")
        return {"name": name, "passed": not errors, "errors": errors,
                "expected_fault": True, "original": original, "candidate": candidate}
    if original["fault"] or candidate["fault"]:
        errors.append("machine fault")
    if original["pc"] != hex(RETURN) or candidate["pc"] != hex(RETURN):
        errors.append("did not return to LR sentinel")
    if original["r0"] != candidate["r0"]:
        errors.append("r0 differs")
    if original["preserved"] != candidate["preserved"]:
        errors.append("callee-saved registers or SP differ")
    if original["data"] != candidate["data"]:
        errors.append("synthetic memory differs")
    if original["caller_stack"] != candidate["caller_stack"]:
        errors.append("caller-owned stack differs")
    return {"name": name, "passed": not errors, "errors": errors,
            "row_index_argument": row_index, "mode_argument": mode,
            "original": original, "candidate": candidate}


def run(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    image, linked, elf = build_linked(output)
    rows0 = row_fixture(-2, 3, -4, 5)
    cases = [
        compare_case(image, linked, "null object faults at first table load", None,
                     expected_fault=True),
        compare_case(image, linked, "nonnull object with null table returns unchanged",
                     object_fixture(table=0), rows0),
        compare_case(image, linked, "mode zero selects row offsets 0 and 2",
                     object_fixture(), rows0, row_index=0, mode=0),
        compare_case(image, linked, "mode nonzero selects row offsets 4 and 6",
                     object_fixture(), rows0, row_index=0, mode=1),
        compare_case(image, linked, "nonzero full mode with zero low byte still selects second pair",
                     object_fixture(), rows0, row_index=0, mode=0x100),
        compare_case(image, linked, "row index one uses 12-byte table stride",
                     object_fixture(), rows0 + row_fixture(11, -12, 13, -14), row_index=1),
        compare_case(image, linked, "negative row index selects preceding row by wrapped address",
                     object_fixture(table=ROWS + 12), rows0, row_index=-1),
        compare_case(image, linked, "signed coordinate minimum and maximum mode zero",
                     object_fixture(), row_fixture(-32768, 32767, 32767, -32768)),
        compare_case(image, linked, "signed coordinate maximum and minimum mode nonzero",
                     object_fixture(), row_fixture(32767, -32768, -32768, 32767), mode=1),
    ]

    # Compile a deliberate mutant omitting the +0x86 clear. Seed it nonzero so
    # the same valid-table call must distinguish it by object memory.
    source_text = SOURCE.read_text(encoding="utf-8")
    anchor = "    object[0x86] = 0;\n"
    if source_text.count(anchor) != 1:
        raise ValueError("negative-control mutation anchor is not unique")
    mutant_source = output / "negative_missing_complete_clear.cpp"
    mutant_source.write_text(source_text.replace(anchor,
        "    // negative control omits the original +0x86 clear\n"), encoding="utf-8")
    mutant_image, mutant_linked, mutant_elf = build_linked(output / "negative-control", mutant_source)
    negative = compare_case(mutant_image, mutant_linked,
                            "negative control omits +0x86 clear",
                            object_fixture(old_complete=1), rows0, mutant=True)
    control = {"name": "missing_0x86_clear", "detected": not negative["passed"],
               "errors": negative["errors"], "mutant_source_sha256": sha(mutant_source.read_bytes()),
               "mutant_elf_sha256": sha(mutant_elf.read_bytes()), "case": negative}
    report = {
        "task_id": "h1-animation-row-setter-candidate",
        "passed": all(c["passed"] for c in cases) and control["detected"],
        "entry": hex(ENTRY), "size": SIZE, "exit": hex(ENTRY + SIZE),
        "identity": linked["metadata"], "linked_elf_sha256": sha(elf.read_bytes()),
        "cases": cases, "case_count": len(cases), "negative_controls": [control],
        "first_mismatch": next(({"case": c["name"], "errors": c["errors"]}
                                 for c in cases if not c["passed"]), None),
        "evidence": {"compiled": "passed", "arm_differential": "partial_valid_table_fixtures",
                     "caller": "partial_static_h1_helper_call", "runtime": "not_run"},
        "limitations": [
            "The original entry dereferences object+0x4C without a null-object check; the null-object fixture records that both Unicorn executions fault, but invalid-null-pointer behavior is outside the C++ contract.",
            "The null-table early return is validated only with a valid object pointer.",
            "Row/table storage is valid and non-aliasing in normal passing fixtures. Overlapping table/object storage, unmapped row addresses, and invalid pointers are unsupported.",
            "Caller evidence is static: 0x002BF9F0 calls this helper at 0x002BFB48 and 0x002BFB78 with object, animation word, and signed frame byte. No real caller/runtime scenario was run.",
        ],
    }
    report_path = output / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.output)
    print(f"row setter differential: {'PASS' if report['passed'] else 'FAIL'} "
          f"{sum(c['passed'] for c in report['cases'])}/{report['case_count']}; "
          f"negative control={'detected' if report['negative_controls'][0]['detected'] else 'missed'}; "
          f"report {args.output / 'report.json'}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
