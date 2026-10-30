"""Private ARM differential for the reconstructed 0x002BF9F0 helper.

Only named external leaves are stubbed. Row/sequence memory is deliberately
synthetic, bounds-valid fixture data; this is not evidence for the H1 scene
object at scene+0xD74.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.build_check import find_clang, get_armv6k_flags
from tools.semantic_experiment import arm, require_unicorn, unicorn

TEXT, INJECT, DATA, STACK = 0x00100000, 0x01000000, 0x02000000, 0x08000000
TEXT_SIZE, INJECT_SIZE, DATA_SIZE, STACK_SIZE = 0x400000, 0x10000, 0x4000, 0x2000
OBJECT, ROWS, SEQUENCE = DATA, DATA + 0x200, DATA + 0x400
SP, RETURN = STACK + 0x1000, INJECT + 0xFFF0
IMAGE = ROOT / "extracted/exefs/code.bin"
SOURCE = ROOT / "experiments/semantic_equivalence/h1_preview_helper_candidate.cpp"
HELPER, HELPER_SIZE = 0x002BF9F0, 664
HELPER_SHA = "9b4783c2ccc69b30fc99ef28b04fe5f5abbe1762f99a13551facc5cab7b8217e"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
EXTERNAL = {0x002BDAC0: "animation", 0x002C615C: "interpolation",
            0x002B1FC0: "tail_a", 0x002B1DFC: "tail_b", 0x002B1C8C: "tail_c"}
STUBS = {"camp_func_002bdac0": "animation", "ui_func_002c615c": "interpolation",
         "ui_func_002b1fc0": "tail_a", "ui_func_002b1dfc": "tail_b",
         "ui_func_002b1c8c": "tail_c"}


def h(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_image(output: Path, candidate_source: Path = SOURCE) -> tuple[bytes, dict, Path]:
    output.mkdir(parents=True, exist_ok=True)
    image = IMAGE.read_bytes()
    if h(image) != IMAGE_SHA:
        raise ValueError("pinned original image hash mismatch")
    body = image[HELPER - TEXT:HELPER - TEXT + HELPER_SIZE]
    if len(body) != HELPER_SIZE or h(body) != HELPER_SHA:
        raise ValueError("pinned helper body hash mismatch")
    generated = output / "linked_candidate.cpp"
    generated.write_text(
        '#include "' + str(candidate_source.resolve()).replace('\\', '/') + '"\n' +
        'volatile uint32_t preview_stub_sink[3]; volatile int32_t preview_interp_result;\n' +
        'extern "C" __attribute__((noinline,used)) void camp_func_002bdac0(void* o,int32_t a,int32_t f) { preview_stub_sink[0]=(uint32_t)(uintptr_t)o; preview_stub_sink[1]=(uint32_t)a; preview_stub_sink[2]=(uint32_t)f; }\n' +
        'extern "C" __attribute__((noinline,used)) int32_t ui_func_002c615c(int32_t d,uint32_t n) { preview_stub_sink[0]=(uint32_t)d; preview_stub_sink[1]=n; return preview_interp_result; }\n' +
        'extern "C" __attribute__((noinline,used)) void ui_func_002b1fc0(void* o) { preview_stub_sink[0]=(uint32_t)(uintptr_t)o; }\n' +
        'extern "C" __attribute__((noinline,used)) void ui_func_002b1dfc(void* o) { preview_stub_sink[0]=(uint32_t)(uintptr_t)o; }\n' +
        'extern "C" __attribute__((noinline,used)) void ui_func_002b1c8c(void* o) { preview_stub_sink[0]=(uint32_t)(uintptr_t)o; }\n',
        encoding="utf-8")
    clang = find_clang()
    elf = output / "linked_candidate.elf"
    cmd = [str(clang), *get_armv6k_flags(ROOT, clang), "-nostdlib", "-fuse-ld=lld",
           "-Wl,-Ttext=0x01000000", "-Wl,-e,h1_preview_helper_candidate",
           "-Wl,--build-id=none", str(generated), "-o", str(elf)]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    (output / "link-command.json").write_text(json.dumps({"argv": cmd, "exit_code": proc.returncode,
        "stdout": proc.stdout, "stderr": proc.stderr}, indent=2) + "\n", encoding="utf-8")
    if proc.returncode:
        raise RuntimeError("linked candidate build failed: " + proc.stderr)
    tools_dir = clang.parent
    objcopy = tools_dir / "llvm-objcopy.exe"
    nm = tools_dir / "llvm-nm.exe"
    if not objcopy.exists() or not nm.exists():
        raise RuntimeError("llvm-objcopy and llvm-nm are required for private linked-image extraction")
    raw = output / "candidate-text.bin"
    subprocess.run([str(objcopy), "--dump-section", f".text={raw}", str(elf)], check=True,
                   capture_output=True, text=True)
    nm_result = subprocess.run([str(nm), "-n", str(elf)], check=True, capture_output=True, text=True)
    symbols = {}
    for line in nm_result.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 3:
            symbols[fields[2]] = int(fields[0], 16)
    required = {"h1_preview_helper_candidate", *STUBS}
    if not required <= symbols.keys():
        raise RuntimeError(f"linked ELF missing symbols: {sorted(required - symbols.keys())}")
    text = raw.read_bytes()
    if len(text) > INJECT_SIZE:
        raise RuntimeError("linked candidate .text exceeds mapped injection area")
    offsets = {symbol: symbols[symbol] - INJECT for symbol in required}
    if any(offset < 0 or offset >= len(text) for offset in offsets.values()):
        raise RuntimeError("linked symbol not in extracted .text range")
    meta = {"compiler": str(clang), "argv": cmd, "elf_sha256": h(elf.read_bytes()),
            "text_sha256": h(text), "text_size": len(text), "symbols": {k: hex(v) for k,v in symbols.items() if k in required},
            "source_sha256": h(candidate_source.read_bytes()), "image_sha256": h(image), "helper_sha256": h(body)}
    return image, {"text": text, "offsets": offsets, "metadata": meta}, elf


class Machine:
    def __init__(self, image: bytes, linked: dict | None):
        require_unicorn()
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.mem_map(TEXT, TEXT_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE | unicorn.UC_PROT_EXEC)
        self.uc.mem_write(TEXT, image)
        self.uc.mem_map(INJECT, INJECT_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE | unicorn.UC_PROT_EXEC)
        if linked:
            self.uc.mem_write(INJECT, linked["text"])
        self.uc.mem_map(DATA, DATA_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.uc.mem_map(STACK, STACK_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.linked, self.calls, self.fault = linked, [], None
        self.symbol_hooks = ({INJECT + off: STUBS[name] for name, off in linked["offsets"].items() if name in STUBS}
                             if linked else {})
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._hook)

    def _hook(self, uc, pc, _size, _user):
        if pc == RETURN:
            uc.emu_stop()
            return
        if pc in EXTERNAL:
            self._external(pc, EXTERNAL[pc])
        elif pc in self.symbol_hooks:
            self._external(pc, self.symbol_hooks[pc])

    def _external(self, pc: int, name: str):
        r0 = self.uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = self.uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = self.uc.reg_read(arm.UC_ARM_REG_R2)
        args = [r0, r1, r2] if name == "animation" else ([r0, r1] if name == "interpolation" else [r0])
        ret = 0
        if name == "interpolation":
            # A deterministic synthetic leaf: return signed delta / duration,
            # with a zero-duration guard. This is not the pinned callee.
            delta = r0 if r0 < 0x80000000 else r0 - 0x100000000
            ret = int(delta / r1) & 0xFFFFFFFF if r1 else 0
        self.calls.append({"name": name, "args": [hex(x) for x in args], "return": hex(ret)})
        self.uc.reg_write(arm.UC_ARM_REG_R0, ret)
        self.uc.reg_write(arm.UC_ARM_REG_PC, self.uc.reg_read(arm.UC_ARM_REG_LR))

    def run(self, ptr: int, obj: bytes | None, rows: bytes = b"", seq: bytes = b"") -> dict:
        self.uc.mem_write(DATA, bytes([0xA5]) * 0x1000)
        if obj is not None:
            b = bytearray(obj)
            if len(b) < 0x8B: raise ValueError("fixture object too short")
            self.uc.mem_write(OBJECT, bytes(b))
        if rows: self.uc.mem_write(ROWS, rows)
        if seq: self.uc.mem_write(SEQUENCE, seq)
        self.calls, self.fault = [], None
        for i in range(13): self.uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), 0xA5A50000 | i)
        self.uc.reg_write(arm.UC_ARM_REG_R0, ptr)
        self.uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
        self.uc.reg_write(arm.UC_ARM_REG_SP, SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
        self.uc.reg_write(arm.UC_ARM_REG_FPSCR, 0x01000000)
        state0 = {f"r{i}": self.uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4, 12)}
        state0.update({"sp": SP, "fpscr": 0x01000000})
        try:
            start = (INJECT + self.linked["offsets"]["h1_preview_helper_candidate"] if self.linked else HELPER)
            self.uc.emu_start(start, 0, count=10000)
        except unicorn.UcError as e:
            self.fault = f"{self.uc.reg_read(arm.UC_ARM_REG_PC):#x}: {e}"
        regs = {f"r{i}": self.uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4, 12)}
        regs.update({"sp": self.uc.reg_read(arm.UC_ARM_REG_SP), "fpscr": self.uc.reg_read(arm.UC_ARM_REG_FPSCR)})
        memory = bytes(self.uc.mem_read(DATA, 0x1000))
        return {"fault": self.fault, "pc": hex(self.uc.reg_read(arm.UC_ARM_REG_PC)),
                "r0": self.uc.reg_read(arm.UC_ARM_REG_R0), "calls": list(self.calls),
                "state": regs, "initial_state": state0, "memory": memory.hex()}


def object_fixture(*, gate=(0, 0), already=0, row_ptr=0, progress=0, direction=0,
                   enable=0, seq_ptr=0, seq_index=0, flags=(1,1,1,1), coords=(0x1234,0x5678)) -> bytearray:
    b = bytearray([0xA5]) * 0x8B
    struct.pack_into("<i", b, 4, gate[0]); struct.pack_into("<i", b, 8, gate[1])
    struct.pack_into("<II", b, 0x0C, *coords)
    struct.pack_into("<I", b, 0x4C, row_ptr)
    struct.pack_into("<hh", b, 0x50, 0, progress)
    b[0x54] = direction; struct.pack_into("<I", b, 0x78, seq_ptr)
    struct.pack_into("<h", b, 0x7C, seq_index); b[0x84] = enable; b[0x86] = already
    b[0x87:0x8A] = bytes(flags)
    return b


def row_fixture(duration: int, mode: int, coords=(1,2,3,4)) -> bytes:
    row = bytearray(12)
    struct.pack_into("<hhhhH", row, 0, *coords, duration)
    row[10] = mode
    return bytes(row)


def sequence_fixture(first: int, next_word: int, first_frame: int = -4) -> bytes:
    seq = bytearray(0x38)
    struct.pack_into("<i", seq, 0, first); struct.pack_into("<b", seq, 4, first_frame)
    struct.pack_into("<i", seq, 0x1C, next_word); struct.pack_into("<b", seq, 0x20, 7)
    return bytes(seq)


def case(image: bytes, linked: dict, name: str, obj: bytearray | None, rows=b"", seq=b"") -> dict:
    original = Machine(image, None).run(OBJECT if obj is not None else 0, bytes(obj) if obj is not None else None, rows, seq)
    candidate = Machine(image, linked).run(OBJECT if obj is not None else 0, bytes(obj) if obj is not None else None, rows, seq)
    errors = []
    if original["fault"] or candidate["fault"]: errors.append("machine fault")
    if original["pc"] != hex(RETURN) or candidate["pc"] != hex(RETURN): errors.append("did not return to sentinel")
    for r in ("r4", "r5", "r6", "r7", "r8", "r9", "r10", "r11", "sp", "fpscr"):
        if original["state"][r] != candidate["state"][r]: errors.append(f"preserved state mismatch {r}")
    if original["r0"] != candidate["r0"]: errors.append("r0 differs")
    if original["calls"] != candidate["calls"]: errors.append("external call trace differs")
    if original["memory"] != candidate["memory"]: errors.append("synthetic memory differs")
    return {"name": name, "passed": not errors, "errors": errors, "original": original, "candidate": candidate}


def run(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    image, linked, elf = build_image(output)
    cases = [
        case(image, linked, "null early return", None),
        case(image, linked, "both negative early return", object_fixture(gate=(-1,-1))),
        case(image, linked, "second gate nonnegative continues", object_fixture(gate=(-1,0))),
        case(image, linked, "first gate zero with second gate negative continues", object_fixture(gate=(0,-1))),
        case(image, linked, "signed minimum pair early return", object_fixture(gate=(-0x80000000,-0x80000000))),
        case(image, linked, "signed minimum then maximum continues", object_fixture(gate=(-0x80000000,0x7FFFFFFF))),
        case(image, linked, "signed maximum then minimum continues without second gate", object_fixture(gate=(0x7FFFFFFF,-0x80000000))),
        case(image, linked, "already complete bypasses rows", object_fixture(already=1)),
        case(image, linked, "null row table skips animation", object_fixture(row_ptr=0)),
        case(image, linked, "endpoint row and completion tail", object_fixture(row_ptr=ROWS), row_fixture(0,0)),
        case(image, linked, "nonzero row mode bypasses sequence block", object_fixture(row_ptr=ROWS, enable=1, seq_ptr=SEQUENCE), row_fixture(0,1), sequence_fixture(0x12345678,0x23456789)),
        case(image, linked, "row mode zero direction one endpoint", object_fixture(row_ptr=ROWS, direction=1), row_fixture(0,0)),
        case(image, linked, "row mode nonzero direction one endpoint", object_fixture(row_ptr=ROWS, direction=1, enable=1, seq_ptr=SEQUENCE), row_fixture(0,1), sequence_fixture(0x12345678,0x23456789)),
        case(image, linked, "interpolation row invokes two interpolators", object_fixture(row_ptr=ROWS, progress=1, coords=(0x10000,0x20000)), row_fixture(8,0,(1,3,5,7))),
        case(image, linked, "direction one interpolation uses reversed deltas", object_fixture(row_ptr=ROWS, progress=1, direction=1, coords=(0x10000,0x20000)), row_fixture(8,0,(1,3,5,7))),
        case(image, linked, "sequence ordinary entry invokes animation helper", object_fixture(row_ptr=ROWS, enable=1, seq_ptr=SEQUENCE), row_fixture(0,0), sequence_fixture(0x12345678,0x23456789)),
        case(image, linked, "sequence enabled null pointer marks complete", object_fixture(row_ptr=ROWS, enable=1, seq_ptr=0), row_fixture(0,0)),
        case(image, linked, "current sequence end marker marks complete", object_fixture(row_ptr=ROWS, enable=1, seq_ptr=SEQUENCE), row_fixture(0,0), sequence_fixture(-1,0)),
        case(image, linked, "sequence end marker sets complete", object_fixture(row_ptr=ROWS, enable=1, seq_ptr=SEQUENCE), row_fixture(0,0), sequence_fixture(0x12345678,-1)),
        case(image, linked, "next sequence -3 marker sets complete", object_fixture(row_ptr=ROWS, enable=1, seq_ptr=SEQUENCE), row_fixture(0,0), sequence_fixture(0x12345678,-3)),
        case(image, linked, "sequence restart marker resets index", object_fixture(row_ptr=ROWS, enable=1, seq_ptr=SEQUENCE), row_fixture(0,0), sequence_fixture(0x12345678,-2)),
    ]
    # Negative control: compile a candidate with the disabled-sequence
    # completion store removed. The existing endpoint case must distinguish it.
    source_text = SOURCE.read_text(encoding="utf-8")
    disabled_store = '''} else if (row_mode == 0) {
                    // The original conditional-load chain branches to the
                    // same completion path when the sequence feature is off.
                    object[0x86] = 1;
                }'''
    if source_text.count(disabled_store) != 1:
        raise ValueError("negative-control mutation anchor is not unique")
    mutant_source = output / "negative_missing_disabled_sequence_completion.cpp"
    mutant_source.write_text(source_text.replace(disabled_store,
        "} else if (row_mode == 0) { /* negative control: omitted +0x86 store */ }"), encoding="utf-8")
    mutant_image, mutant_linked, mutant_elf = build_image(output / "negative-control", mutant_source)
    mutant_case = case(mutant_image, mutant_linked, "negative control: omitted +0x86 completion store",
                       object_fixture(row_ptr=ROWS, enable=0), row_fixture(0,0))
    negative = [{"name":"omitted_disabled_sequence_completion_store", "detected":not mutant_case["passed"],
                 "mutant_source_sha256":h(mutant_source.read_bytes()),
                 "mutant_elf_sha256":h(mutant_elf.read_bytes()),
                 "mutant_errors":mutant_case["errors"], "mutant_report_case":mutant_case}]
    report = {"task_id":"h1-preview-helper-candidate", "passed":all(c["passed"] for c in cases),
              "candidate":linked["metadata"], "linked_elf_sha256":h(elf.read_bytes()), "cases":cases,
              "case_count":len(cases), "evidence":{"compiled":"passed","arm_differential":"partial_synthetic_stubs",
              "caller":"not_run","runtime":"not_run"},
              "negative_controls":negative,
              "limitations":["All five direct callee addresses are replaced by deterministic named stubs; their original bodies and transitive effects are not compared.",
              "Synthetic byte arrays provide valid rows and sequence entries for selected indices; no allocation, constructor, H1 scene+0xD74 lifecycle, callback registration, or actual runtime bindings are established.",
              "The interpolation stub returns delta/duration and is synthetic; these comparisons establish call ABI/order and surrounding effects only for this stub contract."]}
    report_path=output/"report.json"
    report_path.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return report


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    report=run(args.output)
    print(f"helper candidate differential: {'PASS' if report['passed'] else 'FAIL'} {sum(x['passed'] for x in report['cases'])}/{report['case_count']}; report {args.output/'report.json'}")
    return 0 if report["passed"] else 1

if __name__=="__main__": raise SystemExit(main())
