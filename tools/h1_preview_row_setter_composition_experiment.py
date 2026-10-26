"""Private caller-level ARM differential for preview helper plus row setter."""
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
TEXT_SIZE, INJECT_SIZE, DATA_SIZE, STACK_SIZE = 0x00400000, 0x00010000, 0x00004000, 0x00002000
OBJECT, ROWS, SEQUENCE = DATA, DATA + 0x200, DATA + 0x800
SP, RETURN = STACK + 0x1000, INJECT + 0xFFF0
HELPER, HELPER_SIZE = 0x002BF9F0, 664
SETTER = 0x002BDAC0
IMAGE = ROOT / "extracted/exefs/code.bin"
HELPER_SOURCE = ROOT / "experiments/semantic_equivalence/h1_preview_helper_candidate.cpp"
SETTER_SOURCE = ROOT / "experiments/semantic_equivalence/h1_animation_row_setter_candidate.cpp"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
HELPER_SHA = "9b4783c2ccc69b30fc99ef28b04fe5f5abbe1762f99a13551facc5cab7b8217e"
SETTER_SHA = "e9c60d31db041884aa6fe44db47bcabc849bf08464d1465a68cad24c4b1f152a"
STUBS = {
    "ui_func_002c615c": "interpolation",
    "ui_func_002b1fc0": "tail_a",
    "ui_func_002b1dfc": "translation_track",
    "ui_func_002b1c8c": "tail_c",
}
ORIGINAL_STUBS = {
    0x002C615C: "interpolation",
    0x002B1FC0: "tail_a",
    0x002B1DFC: "translation_track",
    0x002B1C8C: "tail_c",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_object(clang: Path, source: Path, output: Path, root: Path) -> dict:
    obj = output / (source.stem + ".o")
    argv = [str(clang), *get_armv6k_flags(root, clang), "-c", str(source), "-o", str(obj)]
    proc = subprocess.run(argv, cwd=root, capture_output=True, text=True)
    if proc.returncode:
        raise RuntimeError(f"compile failed for {source}: {proc.stderr}")
    return {"argv": argv, "exit_code": proc.returncode, "object": obj,
            "object_sha256": sha(obj.read_bytes()), "source_sha256": sha(source.read_bytes())}


def build_linked(output: Path, setter_source: Path = SETTER_SOURCE) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    clang = find_clang()
    adapter = output / "composition_adapter.cpp"
    adapter.write_text(r'''#include <stdint.h>
extern "C" void h1_animation_row_setter_candidate(void*, int32_t, int32_t);
extern "C" __attribute__((noinline, used)) void camp_func_002bdac0(
    void* object, int32_t animation, int32_t frame) {
    h1_animation_row_setter_candidate(object, animation, frame);
}
extern "C" __attribute__((noinline, used)) int32_t ui_func_002c615c(int32_t, uint32_t) { return 0; }
extern "C" __attribute__((noinline, used)) void ui_func_002b1fc0(void*) {}
extern "C" __attribute__((noinline, used)) void ui_func_002b1dfc(void*) {}
extern "C" __attribute__((noinline, used)) void ui_func_002b1c8c(void*) {}
''', encoding="utf-8")
    objects = [compile_object(clang, source, output, ROOT)
               for source in (HELPER_SOURCE, setter_source, adapter)]
    elf = output / "composed_candidate.elf"
    link_argv = [str(clang), *get_armv6k_flags(ROOT, clang), "-nostdlib", "-fuse-ld=lld",
                 f"-Wl,-Ttext={INJECT:#x}", "-Wl,-e,h1_preview_helper_candidate",
                 "-Wl,--build-id=none", "-Wl,--no-undefined",
                 *(str(item["object"]) for item in objects), "-o", str(elf)]
    link = subprocess.run(link_argv, cwd=ROOT, capture_output=True, text=True)
    (output / "link-command.json").write_text(json.dumps({
        "argv": link_argv, "exit_code": link.returncode, "stdout": link.stdout,
        "stderr": link.stderr,
    }, indent=2) + "\n", encoding="utf-8")
    if link.returncode:
        raise RuntimeError(f"composed candidate link failed: {link.stderr}")
    objcopy, nm = clang.parent / "llvm-objcopy.exe", clang.parent / "llvm-nm.exe"
    if not objcopy.is_file() or not nm.is_file():
        raise RuntimeError("llvm-objcopy and llvm-nm are required")
    raw = output / "candidate-text.bin"
    subprocess.run([str(objcopy), "--dump-section", f".text={raw}", str(elf)],
                   check=True, capture_output=True, text=True)
    nm_result = subprocess.run([str(nm), "-n", str(elf)], check=True,
                               capture_output=True, text=True)
    symbols = {}
    for line in nm_result.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 3:
            symbols[fields[2]] = int(fields[0], 16)
    required = {"h1_preview_helper_candidate", "h1_animation_row_setter_candidate",
                "camp_func_002bdac0", *STUBS.keys()}
    missing = sorted(required - symbols.keys())
    if missing:
        raise RuntimeError(f"composition ELF missing symbols: {missing}")
    text = raw.read_bytes()
    if len(text) > INJECT_SIZE:
        raise RuntimeError("composed .text exceeds private mapping")
    undefined = subprocess.run([str(nm), "-u", str(elf)], check=True,
                               capture_output=True, text=True).stdout.splitlines()
    if any(line.strip() for line in undefined):
        raise RuntimeError(f"composed ELF has undefined symbols: {undefined}")
    return {
        "text": text,
        "symbols": {name: symbols[name] for name in required},
        "elf": elf,
        "metadata": {
            "compiler": str(clang), "link_argv": link_argv,
            "elf_sha256": sha(elf.read_bytes()), "text_sha256": sha(text),
            "text_size": len(text), "image_sha256": sha(IMAGE.read_bytes()),
            "helper_source_sha256": sha(HELPER_SOURCE.read_bytes()),
            "setter_source_sha256": sha(setter_source.read_bytes()),
            "adapter_source_sha256": sha(adapter.read_bytes()),
            "helper_body_sha256": sha(IMAGE.read_bytes()[HELPER - TEXT:HELPER - TEXT + HELPER_SIZE]),
            "setter_body_sha256": sha(IMAGE.read_bytes()[SETTER - TEXT:SETTER - TEXT + 108]),
            "object_builds": [{"source_sha256": item["source_sha256"],
                               "object_sha256": item["object_sha256"],
                               "compile_exit_code": item["exit_code"],
                               "compile_argv": item["argv"]} for item in objects],
            "link_exit_code": link.returncode,
            "link_stdout": link.stdout,
            "link_stderr": link.stderr,
            "undefined_symbols": [],
            "symbols": {name: hex(symbols[name]) for name in required},
        },
    }


def signed32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


class Machine:
    def __init__(self, image: bytes, linked: dict | None):
        require_unicorn()
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.mem_map(TEXT, TEXT_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
        self.uc.mem_write(TEXT, image)
        self.uc.mem_map(INJECT, INJECT_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE | unicorn.UC_PROT_EXEC)
        if linked:
            self.uc.mem_write(INJECT, linked["text"])
        self.uc.mem_map(DATA, DATA_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.uc.mem_map(STACK, STACK_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.linked = linked
        self.stub_symbols = ({linked["symbols"][name]: label for name, label in STUBS.items()}
                             if linked else {})
        self.setter_adapter = linked["symbols"]["camp_func_002bdac0"] if linked else None
        self.stub_calls: list[dict] = []
        self.setter_calls: list[dict] = []
        self.fault: str | None = None
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._hook)

    def _registers(self) -> tuple[int, int, int]:
        return tuple(self.uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(3))

    def _record_setter(self, pc: int):
        r0, r1, r2 = self._registers()
        self.setter_calls.append({"pc": hex(pc), "args": [hex(r0), hex(r1), hex(r2)]})

    def _stub(self, pc: int, name: str):
        r0, r1, r2 = self._registers()
        args = [r0, r1] if name == "interpolation" else [r0]
        self.stub_calls.append({"name": name, "pc": hex(pc),
                                "args": [hex(value) for value in args], "return": "0x0"})
        self.uc.reg_write(arm.UC_ARM_REG_R0, 0)
        self.uc.reg_write(arm.UC_ARM_REG_PC, self.uc.reg_read(arm.UC_ARM_REG_LR))

    def _hook(self, uc, pc, _size, _user):
        if pc == RETURN:
            uc.emu_stop()
            return
        if self.linked is None:
            if pc == SETTER:
                self._record_setter(pc)
            elif pc in ORIGINAL_STUBS:
                self._stub(pc, ORIGINAL_STUBS[pc])
            return
        if pc == self.setter_adapter:
            self._record_setter(pc)
        elif pc in self.stub_symbols:
            self._stub(pc, self.stub_symbols[pc])

    def run(self, obj: bytes, rows: bytes, sequence: bytes) -> dict:
        self.uc.mem_write(DATA, bytes([0xA5]) * DATA_SIZE)
        self.uc.mem_write(STACK, bytes([0x5A]) * STACK_SIZE)
        self.uc.mem_write(OBJECT, obj)
        if rows:
            self.uc.mem_write(ROWS, rows)
        if sequence:
            self.uc.mem_write(SEQUENCE, sequence)
        for i in range(13):
            self.uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), 0xA5A50000 | i)
        self.uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
        self.uc.reg_write(arm.UC_ARM_REG_R0, OBJECT)
        self.uc.reg_write(arm.UC_ARM_REG_SP, SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
        self.uc.reg_write(arm.UC_ARM_REG_FPSCR, 0x01000000)
        for i in range(8, 16):
            self.uc.reg_write(getattr(arm, f"UC_ARM_REG_D{i}"), 0x1111222233334400 + i)
        before = {f"r{i}": self.uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4, 12)}
        before["sp"] = SP
        d_before = [self.uc.reg_read(getattr(arm, f"UC_ARM_REG_D{i}")) for i in range(8, 16)]
        self.stub_calls, self.setter_calls, self.fault = [], [], None
        try:
            start = (HELPER if self.linked is None
                     else self.linked["symbols"]["h1_preview_helper_candidate"])
            self.uc.emu_start(start, 0, count=20000)
        except unicorn.UcError as exc:
            self.fault = f"{exc} at pc={self.uc.reg_read(arm.UC_ARM_REG_PC):#x}"
        after = {f"r{i}": self.uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4, 12)}
        after["sp"] = self.uc.reg_read(arm.UC_ARM_REG_SP)
        d_after = [self.uc.reg_read(getattr(arm, f"UC_ARM_REG_D{i}")) for i in range(8, 16)]
        return {
            "fault": self.fault, "pc": hex(self.uc.reg_read(arm.UC_ARM_REG_PC)),
            "r0": hex(self.uc.reg_read(arm.UC_ARM_REG_R0)),
            "preserved_before": before, "preserved_after": after,
            "d8_d15_before": d_before, "d8_d15_after": d_after,
            "fpscr": self.uc.reg_read(arm.UC_ARM_REG_FPSCR),
            "data": bytes(self.uc.mem_read(DATA, DATA_SIZE)).hex(),
            "caller_stack": bytes(self.uc.mem_read(SP, STACK + STACK_SIZE - SP)).hex(),
            "stub_calls": list(self.stub_calls), "setter_calls": list(self.setter_calls),
        }


def put_u32(buf: bytearray, offset: int, value: int):
    struct.pack_into("<I", buf, offset, value & 0xFFFFFFFF)


def object_fixture(*, gate=(0, 0), table_ptr=ROWS, row_index=0, progress=0, direction=0,
                   enable=0, sequence_ptr=0, sequence_index=0,
                   flags=(1, 1, 1, 1), coords=(0x1234, 0x5678)) -> bytearray:
    b = bytearray([0xCC]) * 0x8B
    struct.pack_into("<i", b, 4, gate[0])
    struct.pack_into("<i", b, 8, gate[1])
    put_u32(b, 0x0C, coords[0])
    put_u32(b, 0x10, coords[1])
    put_u32(b, 0x4C, table_ptr)
    struct.pack_into("<hh", b, 0x50, row_index, progress)
    b[0x54] = direction & 0xFF
    put_u32(b, 0x78, sequence_ptr)
    struct.pack_into("<h", b, 0x7C, sequence_index)
    b[0x84] = enable & 0xFF
    b[0x86] = 0
    b[0x87:0x8B] = bytes(value & 0xFF for value in flags)
    return b


def row_fixture(*rows: tuple[int, int, int, int, int, int]) -> bytes:
    out = bytearray()
    for x0, y0, x1, y1, duration, mode in rows:
        out.extend(struct.pack("<hhhhHBB", x0, y0, x1, y1, duration, mode & 0xFF, 0))
    return bytes(out)


def sequence_fixture(*entries: tuple[int, int]) -> bytes:
    out = bytearray(0x1C * len(entries))
    for i, (animation_word, frame) in enumerate(entries):
        struct.pack_into("<I", out, 0x1C * i, animation_word & 0xFFFFFFFF)
        struct.pack_into("<b", out, 0x1C * i + 4, frame)
    return bytes(out)


def compare_case(image: bytes, linked: dict, name: str, obj: bytearray,
                 rows: bytes, sequence: bytes) -> dict:
    original = Machine(image, None).run(bytes(obj), rows, sequence)
    candidate = Machine(image, linked).run(bytes(obj), rows, sequence)
    errors = []
    if original["fault"] or candidate["fault"]:
        errors.append("machine fault")
    if original["pc"] != hex(RETURN) or candidate["pc"] != hex(RETURN):
        errors.append("did not return to LR sentinel")
    if original["r0"] != candidate["r0"]:
        errors.append("r0 differs")
    if original["preserved_after"] != original["preserved_before"]:
        errors.append("original callee-saved state/SP changed")
    if candidate["preserved_after"] != candidate["preserved_before"]:
        errors.append("candidate callee-saved state/SP changed")
    if original["preserved_after"] != candidate["preserved_after"]:
        errors.append("callee-saved state/SP differs")
    if original["d8_d15_after"] != original["d8_d15_before"]:
        errors.append("original d8-d15 changed")
    if candidate["d8_d15_after"] != candidate["d8_d15_before"]:
        errors.append("candidate d8-d15 changed")
    if original["d8_d15_after"] != candidate["d8_d15_after"]:
        errors.append("d8-d15 differs")
    if original["data"] != candidate["data"]:
        errors.append("object/table/sequence memory differs")
    if original["caller_stack"] != candidate["caller_stack"]:
        errors.append("caller-owned stack differs")
    # The original PC is the pinned entry while the candidate PC is the
    # adapter symbol; compare the semantic boundary (ordered arguments), not
    # those necessarily different code addresses.
    norm_setter = lambda calls: [call["args"] for call in calls]
    norm_stubs = lambda calls: [{k: v for k, v in call.items() if k != "pc"}
                                for call in calls]
    if norm_setter(original["setter_calls"]) != norm_setter(candidate["setter_calls"]):
        errors.append("setter call arguments/order differ")
    if norm_stubs(original["stub_calls"]) != norm_stubs(candidate["stub_calls"]):
        errors.append("named stub call trace differs")
    return {"name": name, "passed": not errors, "errors": errors,
            "original": original, "candidate": candidate}


def run(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    image = IMAGE.read_bytes()
    if sha(image) != IMAGE_SHA:
        raise ValueError("pinned image hash mismatch")
    if sha(image[HELPER - TEXT:HELPER - TEXT + HELPER_SIZE]) != HELPER_SHA:
        raise ValueError("pinned helper body hash mismatch")
    if sha(image[SETTER - TEXT:SETTER - TEXT + 108]) != SETTER_SHA:
        raise ValueError("pinned setter body hash mismatch")
    linked = build_linked(output / "candidate-build")
    endpoint_rows = row_fixture((1, 2, 3, 4, 0, 0), (10, 20, 30, 40, 8, 1),
                                (-2, 3, -4, 5, 0, 0))
    interpolation_rows = row_fixture((1, 2, 3, 4, 8, 0), (10, 20, 30, 40, 8, 1),
                                      (-2, 3, -4, 5, 8, 0))
    cases = [
        compare_case(image, linked, "valid null table returns without setter",
                     object_fixture(table_ptr=0), b"", b""),
        compare_case(image, linked, "endpoint disabled sequence skips setter",
                     object_fixture(enable=0, progress=0), endpoint_rows, sequence_fixture((2, 0), (3, 1))),
        compare_case(image, linked, "endpoint restart marker calls pinned setter site one",
                     object_fixture(enable=1, sequence_ptr=SEQUENCE), endpoint_rows,
                     sequence_fixture((2, 0), (-2, 0))),
        compare_case(image, linked, "endpoint ordinary next calls pinned setter site two",
                     object_fixture(enable=1, sequence_ptr=SEQUENCE), endpoint_rows,
                     sequence_fixture((1, 0), (2, 1))),
        compare_case(image, linked, "interpolation direction zero calls both interpolator stubs",
                     object_fixture(progress=1, direction=0), interpolation_rows, b""),
        compare_case(image, linked, "interpolation direction one calls both interpolator stubs",
                     object_fixture(progress=1, direction=1), interpolation_rows, b""),
        compare_case(image, linked, "endpoint nonzero row mode bypasses enabled sequence",
                     object_fixture(enable=1, sequence_ptr=SEQUENCE),
                     row_fixture((1, 2, 3, 4, 0, 1)), sequence_fixture((1, 0), (2, 1))),
        compare_case(image, linked, "enabled null sequence completes without setter",
                     object_fixture(enable=1, sequence_ptr=0), endpoint_rows, b""),
    ]
    # The setter must replace the current animation row index. Omitting this
    # meaningful effect leaves the old index in object+0x50 after a sequence.
    setter_text = SETTER_SOURCE.read_text(encoding="utf-8")
    anchor = "write_u16(object + 0x50, static_cast<uint16_t>(row_index));"
    if setter_text.count(anchor) != 1:
        raise ValueError("setter negative-control mutation anchor is not unique")
    mutant_source = output / "negative_missing_animation_index_store.cpp"
    mutant_source.write_text(setter_text.replace(anchor,
        "/* negative control omits the +0x50 animation index store */"), encoding="utf-8")
    mutant_linked = build_linked(output / "negative-control", mutant_source)
    mutant_case = compare_case(image, mutant_linked,
        "negative control omits setter +0x50 animation index store",
        object_fixture(enable=1, sequence_ptr=SEQUENCE), endpoint_rows,
        sequence_fixture((1, 0), (2, 1)))
    negative = {"name": "missing_setter_animation_index_store",
                "detected": not mutant_case["passed"], "errors": mutant_case["errors"],
                "mutant_setter_source_sha256": sha(mutant_source.read_bytes()),
                "mutant_elf_sha256": sha(mutant_linked["elf"].read_bytes()),
                "case": mutant_case}
    report = {
        "task_id": "h1-preview-row-setter-composition",
        "passed": all(case["passed"] for case in cases) and negative["detected"],
        "image_sha256": sha(image),
        "original_helper": {"entry": hex(HELPER), "size": HELPER_SIZE, "sha256": HELPER_SHA},
        "original_setter": {"entry": hex(SETTER), "size": 108, "sha256": SETTER_SHA},
        "candidate": linked["metadata"],
        "cases": cases, "case_count": len(cases), "negative_control": negative,
        "first_mismatch": next(({"case": case["name"], "errors": case["errors"]}
                                 for case in cases if not case["passed"]), None),
        "stub_contracts": {
            "interpolation": "returns zero; receives the helper's fixed-point delta and duration; real divide body not included",
            "tail_a_0x002b1fc0": "no-op, return zero",
            "translation_track_0x002b1dfc": "no-op, return zero",
            "tail_c_0x002b1c8c": "no-op, return zero",
        },
        "evidence": {"compiled": "passed", "arm_differential": "partial_composite_stubbed_callees",
                     "caller": "partial_static_helper_and_setter_calls", "runtime": "not_run"},
        "limitations": [
            "Original side executes pinned 0x002BF9F0 and actual code.bin 0x002BDAC0. Candidate side uses the unchanged helper candidate plus compiled setter candidate through the composition adapter.",
            "Only the row setter is real on both sides. The other four direct callees remain named stubs: interpolation returns zero and three tail helpers are no-ops; their effects and transitive behavior are unknown.",
            "Fixtures use valid, non-aliasing synthetic object, row and sequence storage. Actual H1 object construction/lifecycle, runtime bindings, invalid pointers/indices, aliasing, callback timing, and game runtime are unsupported.",
            "The comparison checks final full data mapping, return r0, setter/stub call arguments/order, callee-saved GPR/VFP state, SP and caller-owned stack. It does not compare all caller-saved scratch registers/flags or read/write access multiplicity/order.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.output)
    passed = sum(case["passed"] for case in report["cases"])
    print(f"preview/setter composition: {'PASS' if report['passed'] else 'FAIL'} "
          f"{passed}/{report['case_count']}; setter control="
          f"{'detected' if report['negative_control']['detected'] else 'missed'}; "
          f"report={args.output/'report.json'}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
