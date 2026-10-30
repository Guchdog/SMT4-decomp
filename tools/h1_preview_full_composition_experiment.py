"""Private all-real-callee ARM composition differential for H1 preview helper."""
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
TEXT_SIZE, INJECT_SIZE, DATA_SIZE, STACK_SIZE = 0x00400000, 0x00010000, 0x00020000, 0x00002000
OBJECT, HELPER_ROWS = DATA, DATA + 0x1000
SCALE_ROWS, TRANSLATION_ROWS, SELECTOR_ROWS = DATA + 0x3000, DATA + 0x5000, DATA + 0x7000
HELPER_SEQUENCE, SCALE_SEQUENCE, TRANSLATION_SEQUENCE = DATA + 0x9000, DATA + 0xA000, DATA + 0xB000
SELECTOR_SEQUENCE, DESCRIPTOR, LOOKUP = DATA + 0xC000, DATA + 0xE000, DATA + 0xE100
SP, RETURN = STACK + 0x1000, INJECT + 0xFFF0
IMAGE = ROOT / "extracted/exefs/code.bin"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
COMPONENTS = {
    "helper": (0x002BF9F0, 664, "9b4783c2ccc69b30fc99ef28b04fe5f5abbe1762f99a13551facc5cab7b8217e"),
    "setter": (0x002BDAC0, 108, "e9c60d31db041884aa6fe44db47bcabc849bf08464d1465a68cad24c4b1f152a"),
    "divide": (0x002C615C, 556, "3d7cdf38585407be142951c950b3c44d2ba4d5d860470166cc4d5e4b3a2705b9"),
    "scale": (0x002B1FC0, 444, "9d9948ecc56a1a6dd32012eacce76ce8cffdf3902632f8efc85245d9dd1f5811"),
    "translation": (0x002B1DFC, 452, "092706575055bba00e8aab90e9ef2a45c2761fb7d12fa0f0b54dbecd35b7439a"),
    "selector": (0x002B1C8C, 368, "8097eb2315dd6b7f6dd72be434ee38223841c6470bfa3b923b362900572ba092"),
}
SOURCES = {
    "helper": ROOT / "experiments/semantic_equivalence/h1_preview_helper_candidate.cpp",
    "setter": ROOT / "experiments/semantic_equivalence/h1_animation_row_setter_candidate.cpp",
    "divide": ROOT / "experiments/semantic_equivalence/h1_interpolation_divide_candidate.cpp",
    "scale": ROOT / "experiments/semantic_equivalence/h1_preview_scale_track_candidate.cpp",
    "translation": ROOT / "experiments/semantic_equivalence/h1_preview_translation_track_candidate.cpp",
    "selector": ROOT / "experiments/semantic_equivalence/h1_preview_sequence_track_candidate.cpp",
}
WRAPPERS = {
    "camp_func_002bdac0": "setter",
    "ui_func_002c615c": "divide",
    "ui_func_002b1fc0": "scale",
    "ui_func_002b1dfc": "translation",
    "ui_func_002b1c8c": "selector",
}
ORIGINAL_ENTRY = {COMPONENTS[name][0]: name for name in WRAPPERS.values()}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_object(clang: Path, source: Path, out: Path) -> dict:
    obj = out / f"{source.stem}.o"
    argv = [str(clang), *get_armv6k_flags(ROOT, clang), "-c", str(source), "-o", str(obj)]
    proc = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
    if proc.returncode:
        raise RuntimeError(f"compile failed for {source}: {proc.stderr}")
    return {"source": str(source), "source_sha256": sha(source.read_bytes()),
            "object": str(obj), "object_sha256": sha(obj.read_bytes()),
            "argv": argv, "exit_code": proc.returncode}


def build_candidate(out: Path, sources: dict[str, Path] = SOURCES) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    clang = find_clang()
    adapter = out / "full_composition_adapter.cpp"
    adapter.write_text(r'''#include <stdint.h>
extern "C" void h1_animation_row_setter_candidate(void*, int32_t, int32_t);
extern "C" int32_t candidate_002c615c(int32_t, int32_t);
extern "C" void* h1_preview_scale_track_candidate(void*);
extern "C" void h1_preview_translation_track_candidate(void*);
extern "C" void* h1_preview_sequence_track_candidate(void*);
extern "C" __attribute__((noinline,used)) void camp_func_002bdac0(void* o,int32_t a,int32_t f) {
  h1_animation_row_setter_candidate(o,a,f);
}
extern "C" __attribute__((noinline,used)) int32_t ui_func_002c615c(int32_t n,uint32_t d) {
  return candidate_002c615c(n,static_cast<int32_t>(d));
}
extern "C" __attribute__((noinline,used)) void ui_func_002b1fc0(void* o) {
  (void)h1_preview_scale_track_candidate(o);
}
extern "C" __attribute__((noinline,used)) void ui_func_002b1dfc(void* o) {
  h1_preview_translation_track_candidate(o);
}
extern "C" __attribute__((noinline,used)) void ui_func_002b1c8c(void* o) {
  (void)h1_preview_sequence_track_candidate(o);
}
''', encoding="utf-8")
    object_builds = [compile_object(clang, sources[name], out)
                     for name in ("helper", "setter", "divide", "scale", "translation", "selector")]
    object_builds.append(compile_object(clang, adapter, out))
    elf = out / "composed_candidate.elf"
    argv = [str(clang), *get_armv6k_flags(ROOT, clang), "-nostdlib", "-fuse-ld=lld",
            f"-Wl,-Ttext={INJECT:#x}", "-Wl,-e,h1_preview_helper_candidate",
            "-Wl,--build-id=none", "-Wl,--no-undefined",
            *(item["object"] for item in object_builds), "-o", str(elf)]
    proc = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
    command_record = {"argv": argv, "exit_code": proc.returncode,
                      "stdout": proc.stdout, "stderr": proc.stderr}
    (out / "link-command.json").write_text(json.dumps(command_record, indent=2) + "\n", encoding="utf-8")
    if proc.returncode:
        raise RuntimeError("composed candidate link failed: " + proc.stderr)
    objcopy, nm = clang.parent / "llvm-objcopy.exe", clang.parent / "llvm-nm.exe"
    if not objcopy.is_file() or not nm.is_file():
        raise RuntimeError("llvm-objcopy and llvm-nm are required")
    raw = out / "candidate-text.bin"
    subprocess.run([str(objcopy), "--dump-section", f".text={raw}", str(elf)],
                   check=True, capture_output=True, text=True)
    nm_out = subprocess.run([str(nm), "-n", str(elf)], check=True,
                            capture_output=True, text=True).stdout
    symbols = {}
    for line in nm_out.splitlines():
        fields = line.split()
        if len(fields) >= 3:
            symbols[fields[2]] = int(fields[0], 16)
    wanted = {"h1_preview_helper_candidate", "h1_animation_row_setter_candidate",
              "candidate_002c615c", "candidate_002c615c_divmod",
              "h1_preview_scale_track_candidate", "h1_preview_translation_track_candidate",
              "h1_preview_sequence_track_candidate", *WRAPPERS.keys()}
    if wanted - symbols.keys():
        raise RuntimeError(f"missing linked symbols: {sorted(wanted - symbols.keys())}")
    undefined = subprocess.run([str(nm), "-u", str(elf)], check=True,
                               capture_output=True, text=True).stdout.splitlines()
    if any(line.strip() for line in undefined):
        raise RuntimeError(f"unresolved linked symbols: {undefined}")
    text = raw.read_bytes()
    if len(text) > INJECT_SIZE:
        raise RuntimeError("candidate text exceeds injection map")
    return {
        "text": text,
        "symbols": {name: symbols[name] for name in wanted},
        "elf": elf,
        "meta": {"compiler": str(clang), "link_argv": argv, "link_exit_code": proc.returncode,
                 "elf_sha256": sha(elf.read_bytes()), "text_sha256": sha(text), "text_size": len(text),
                 "undefined_symbols": [], "object_builds": object_builds,
                 "adapter_sha256": sha(adapter.read_bytes()),
                 "sources": {name: {"path": str(path), "sha256": sha(path.read_bytes())}
                             for name, path in sources.items()},
                 "symbols": {name: hex(symbols[name]) for name in wanted}},
    }


def regread(uc, reg: str) -> int:
    return uc.reg_read(getattr(arm, f"UC_ARM_REG_{reg}"))


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
        self.candidate_wrappers = ({linked["symbols"][name]: target for name, target in WRAPPERS.items()}
                                   if linked else {})
        self.calls: list[dict] = []
        self.fault: str | None = None
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._hook)

    def _hook(self, uc, pc, _size, _user):
        if pc == RETURN:
            uc.emu_stop()
            return
        if self.linked is None:
            name = ORIGINAL_ENTRY.get(pc)
            if name:
                self._record(name, pc)
        elif pc in self.candidate_wrappers:
            self._record(self.candidate_wrappers[pc], pc)

    def _record(self, name: str, pc: int):
        args = [regread(self.uc, "R0")]
        if name in ("setter", "divide"):
            args.append(regread(self.uc, "R1"))
        if name == "setter":
            args.append(regread(self.uc, "R2"))
        self.calls.append({"name": name, "pc": hex(pc), "args": [hex(x) for x in args]})

    def run(self, data: bytes, entry_ptr: int = OBJECT) -> dict:
        if len(data) != DATA_SIZE:
            raise ValueError("fixture must initialize the complete defined data map")
        self.uc.mem_write(DATA, data)
        self.uc.mem_write(STACK, bytes([0x5A]) * STACK_SIZE)
        for i in range(13):
            self.uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), 0xA5A50000 | i)
        self.uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
        self.uc.reg_write(arm.UC_ARM_REG_R0, entry_ptr)
        self.uc.reg_write(arm.UC_ARM_REG_SP, SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
        # ARM11 user-mode VFP requires the coprocessor permission and FPEXC
        # enable used by the independently reviewed track runners.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.reg_write(arm.UC_ARM_REG_FPSCR, 0x01000000)
        for i in range(8, 16):
            self.uc.reg_write(getattr(arm, f"UC_ARM_REG_D{i}"), 0x1111222233334400 + i)
        before = {f"r{i}": regread(self.uc, f"R{i}") for i in range(4, 12)}
        before["sp"] = SP
        d_before = [regread(self.uc, f"D{i}") for i in range(8, 16)]
        self.calls, self.fault = [], None
        try:
            start = COMPONENTS["helper"][0] if self.linked is None else self.linked["symbols"]["h1_preview_helper_candidate"]
            self.uc.emu_start(start, 0, count=100000)
        except unicorn.UcError as exc:
            self.fault = f"{exc} at pc={regread(self.uc, 'PC'):#x}"
        after = {f"r{i}": regread(self.uc, f"R{i}") for i in range(4, 12)}
        after["sp"] = regread(self.uc, "SP")
        d_after = [regread(self.uc, f"D{i}") for i in range(8, 16)]
        data_after = bytes(self.uc.mem_read(DATA, DATA_SIZE))
        stack_after = bytes(self.uc.mem_read(SP, STACK + STACK_SIZE - SP))
        return {
            "fault": self.fault, "pc": hex(regread(self.uc, "PC")),
            "r0": hex(regread(self.uc, "R0")), "r1": hex(regread(self.uc, "R1")),
            "preserved_before": before, "preserved_after": after,
            "d8_d15_before": d_before, "d8_d15_after": d_after,
            "fpscr": regread(self.uc, "FPSCR"),
            "data_sha256": sha(data_after), "data_size": len(data_after),
            "object_after_hex": data_after[:0x100].hex(),
            "_data_snapshot": data_after,
            "stack_sha256": sha(stack_after), "caller_stack_size": len(stack_after),
            "caller_stack_hex": stack_after.hex(), "calls": list(self.calls),
        }


def set_u8(b: bytearray, off: int, value: int):
    b[off] = value & 0xFF


def set_u16(b: bytearray, off: int, value: int):
    struct.pack_into("<H", b, off, value & 0xFFFF)


def set_u32(b: bytearray, off: int, value: int):
    struct.pack_into("<I", b, off, value & 0xFFFFFFFF)


def fixture(*, gate=(0, 0), helper_table=HELPER_ROWS, helper_row=0, progress=0,
            direction=0, enable=0, helper_sequence=0, helper_index=0,
            scale_gate=1, translation_gate=1, selector_gate=1,
            scale_table=0, translation_table=0, selector_table=0,
            scale_index=0, scale_progress=0, scale_direction=0,
            translation_index=0, translation_progress=0, translation_direction=0,
            selector_index=0, selector_progress=0, helper_complete=0) -> bytearray:
    b = bytearray([0xCC]) * DATA_SIZE
    ob = memoryview(b)[0:0x100]
    struct.pack_into("<ii", ob, 4, gate[0], gate[1])
    set_u32(b, 0x0C, 0x12345678); set_u32(b, 0x10, 0x87654321)
    set_u32(b, 0x4C, helper_table)
    set_u16(b, 0x50, helper_row); set_u16(b, 0x52, progress); set_u8(b, 0x54, direction)
    set_u32(b, 0x58, scale_table); set_u16(b, 0x5C, scale_index)
    set_u16(b, 0x5E, scale_progress); set_u8(b, 0x60, scale_direction)
    set_u32(b, 0x64, translation_table); set_u16(b, 0x68, translation_index)
    set_u16(b, 0x6A, translation_progress); set_u8(b, 0x6C, translation_direction)
    set_u32(b, 0x70, selector_table); set_u16(b, 0x74, selector_index)
    set_u16(b, 0x76, selector_progress)
    set_u32(b, 0x78, helper_sequence); set_u16(b, 0x7C, helper_index)
    set_u16(b, 0x7E, selector_index); set_u16(b, 0x80, translation_index)
    set_u16(b, 0x82, selector_index)
    set_u8(b, 0x84, enable); set_u8(b, 0x86, helper_complete)
    set_u8(b, 0x87, scale_gate); set_u8(b, 0x88, translation_gate)
    set_u8(b, 0x89, selector_gate); set_u8(b, 0x8A, 0)
    set_u32(b, 0x48, DESCRIPTOR)
    return b


def rows_i16(rows: list[tuple[int, int, int, int, int, int]]) -> bytes:
    return b"".join(struct.pack("<hhhhHBB", *r[:5], r[5] & 0xFF, 0) for r in rows)


def rows_f32(rows: list[tuple[float, float, int, int]]) -> bytes:
    return b"".join(struct.pack("<ffHBB", *r[:3], r[3] & 0xFF, 0) for r in rows)


def put_blob(b: bytearray, address: int, payload: bytes):
    offset = address - DATA
    b[offset:offset + len(payload)] = payload


def helper_sequence(entries: list[tuple[int, int]]) -> bytes:
    data = bytearray(0x1C * len(entries))
    for i, (word, frame) in enumerate(entries):
        struct.pack_into("<I", data, i * 0x1C, word & 0xFFFFFFFF)
        struct.pack_into("<b", data, i * 0x1C + 4, frame)
    return bytes(data)


def selector_sequence(entries: list[int]) -> bytes:
    # Pinned 0x002B1C8C loads each selector word from
    # sequence + 8 + 28 * index (0x2B1D34-0x2B1D40).
    data = bytearray(8 + 0x1C * len(entries))
    for i, word in enumerate(entries):
        struct.pack_into("<i", data, 8 + 0x1C * i, word)
    return bytes(data)


def set_selector_descriptor(b: bytearray, ids: list[int]):
    lookup = b"".join(struct.pack("<hH", value, 0) for value in ids)
    set_u16(b, DESCRIPTOR - DATA + 6, len(lookup))
    set_u32(b, DESCRIPTOR - DATA + 0x18, LOOKUP)
    put_blob(b, LOOKUP, lookup)


def case_data(name: str, obj: bytearray, helper_rows: list[tuple[int, int, int, int, int, int]] | None = None,
              helper_seq: list[tuple[int, int]] | None = None,
              scale_rows: list[tuple[float, float, int, int]] | None = None,
              translation_rows: list[tuple[float, float, int, int]] | None = None,
              selector_rows: list[tuple[int, int]] | None = None,
              selector_seq_words: list[int] | None = None,
              lookup_ids: list[int] | None = None, entry_ptr: int = OBJECT) -> dict:
    data = obj
    if helper_rows is not None: put_blob(data, HELPER_ROWS, rows_i16(helper_rows))
    if helper_seq is not None: put_blob(data, HELPER_SEQUENCE, helper_sequence(helper_seq))
    if scale_rows is not None: put_blob(data, SCALE_ROWS, rows_f32(scale_rows))
    if translation_rows is not None: put_blob(data, TRANSLATION_ROWS, rows_f32(translation_rows))
    if selector_rows is not None:
        put_blob(data, SELECTOR_ROWS, b"".join(struct.pack("<hH", *r) for r in selector_rows))
    if selector_seq_words is not None: put_blob(data, SELECTOR_SEQUENCE, selector_sequence(selector_seq_words))
    if lookup_ids is not None: set_selector_descriptor(data, lookup_ids)
    return {"name": name, "data": bytes(data), "entry_ptr": entry_ptr}


def call_names(calls: list[dict]) -> list[tuple]:
    return [(c["name"], tuple(c["args"])) for c in calls]


def compare(image: bytes, linked: dict, fixture_case: dict, linked_mutant: dict | None = None) -> dict:
    original = Machine(image, None).run(fixture_case["data"], fixture_case["entry_ptr"])
    candidate = Machine(image, linked_mutant or linked).run(fixture_case["data"], fixture_case["entry_ptr"])
    errors = []
    if original["fault"] or candidate["fault"]: errors.append("execution fault")
    if original["pc"] != hex(RETURN) or candidate["pc"] != hex(RETURN): errors.append("did not return to sentinel")
    for reg in ("r0",):
        if original[reg] != candidate[reg]: errors.append(f"{reg} differs")
    if original["preserved_after"] != original["preserved_before"]: errors.append("original callee-saved state changed")
    if candidate["preserved_after"] != candidate["preserved_before"]: errors.append("candidate callee-saved state changed")
    if original["preserved_after"] != candidate["preserved_after"]: errors.append("callee-saved state/SP differs")
    if original["d8_d15_after"] != original["d8_d15_before"]: errors.append("original d8-d15 changed")
    if candidate["d8_d15_after"] != candidate["d8_d15_before"]: errors.append("candidate d8-d15 changed")
    if original["d8_d15_after"] != candidate["d8_d15_after"]: errors.append("d8-d15 differs")
    if original["fpscr"] != candidate["fpscr"]: errors.append("FPSCR differs")
    original_snapshot = original.pop("_data_snapshot")
    candidate_snapshot = candidate.pop("_data_snapshot")
    if original_snapshot != candidate_snapshot: errors.append("full mapped data differs")
    if original["caller_stack_hex"] != candidate["caller_stack_hex"]: errors.append("caller-owned stack differs")
    if call_names(original["calls"]) != call_names(candidate["calls"]): errors.append("direct callee call trace differs")
    # Find a concrete first memory mismatch using rerun snapshots only when the
    # digest differs, preserving compact successful cases in the report.
    first_memory = None
    if original_snapshot != candidate_snapshot:
        off = next(i for i, (a, b) in enumerate(zip(original_snapshot, candidate_snapshot)) if a != b)
        first_memory = {"address": hex(DATA + off), "offset": off,
                        "original": original_snapshot[off], "candidate": candidate_snapshot[off],
                        "different_byte_count": sum(a != b for a, b in zip(original_snapshot, candidate_snapshot))}
    return {"name": fixture_case["name"], "passed": not errors, "errors": errors,
            "first_memory_mismatch": first_memory,
            "original": original, "candidate": candidate}


def run(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    image = IMAGE.read_bytes()
    if sha(image) != IMAGE_SHA: raise ValueError("pinned code.bin identity mismatch")
    original_components = {}
    for name, (address, size, expected) in COMPONENTS.items():
        body = image[address - TEXT:address - TEXT + size]
        if len(body) != size or sha(body) != expected:
            raise ValueError(f"pinned {name} body identity mismatch")
        original_components[name] = {"entry": hex(address), "size": size, "sha256": expected}
    linked = build_candidate(output / "candidate-build")
    helper_rows = [(1, 2, 3, 4, 0, 0), (10, 20, 30, 40, 8, 1), (-2, 3, -4, 5, 0, 0)]
    scale_rows = [(1.0, 5.0, 8, 0), (3.0, 7.0, 0, 1)]
    translation_rows = [(2.0, 6.0, 8, 0), (4.0, 8.0, 0, 1)]
    cases = []
    cases.append(case_data("null helper pointer early return", fixture(), entry_ptr=0))
    cases.append(case_data("helper both signed gates negative early return",
                           fixture(gate=(-1, -1))))
    cases.append(case_data("common tail invokes three real track dependencies on gated track objects",
                           fixture(gate=(0, 0), helper_table=0, scale_table=0,
                                   translation_table=0, selector_table=0)))
    cases.append(case_data("helper endpoint with disabled sequence and all tracks gated",
                           fixture(helper_table=HELPER_ROWS, enable=0), helper_rows))
    cases.append(case_data("helper restart marker invokes real setter and three real common-tail dependencies",
                           fixture(helper_table=HELPER_ROWS, enable=1, helper_sequence=HELPER_SEQUENCE),
                           helper_rows, [(2, 0), (-2, 0)]))
    cases.append(case_data("helper ordinary next invokes real setter",
                           fixture(helper_table=HELPER_ROWS, enable=1, helper_sequence=HELPER_SEQUENCE),
                           helper_rows, [(1, 0), (2, 1)]))
    cases.append(case_data("helper interpolation direction zero uses real divide candidate",
                           fixture(helper_table=HELPER_ROWS, progress=1, direction=0),
                           [(1, 2, 3, 4, 8, 0)]))
    cases.append(case_data("helper interpolation direction one uses real divide candidate",
                           fixture(helper_table=HELPER_ROWS, progress=1, direction=1),
                           [(1, 2, 3, 4, 8, 0)]))
    cases.append(case_data("helper sequence current end sentinel",
                           fixture(helper_table=HELPER_ROWS, enable=1, helper_sequence=HELPER_SEQUENCE),
                           helper_rows, [(-1, 0)]))
    cases.append(case_data("helper sequence next completion sentinel -3",
                           fixture(helper_table=HELPER_ROWS, enable=1, helper_sequence=HELPER_SEQUENCE),
                           helper_rows, [(1, 0), (-3, 0)]))
    cases.append(case_data("scale track endpoint real dependency body",
                           fixture(helper_table=0, scale_gate=0, scale_table=SCALE_ROWS,
                                   translation_gate=1, selector_gate=1),
                           scale_rows=scale_rows))
    cases.append(case_data("scale track interpolation real dependency body",
                           fixture(helper_table=0, scale_gate=0, scale_table=SCALE_ROWS,
                                   scale_progress=1, translation_gate=1, selector_gate=1),
                           scale_rows=scale_rows))
    cases.append(case_data("translation track endpoint real dependency body",
                           fixture(helper_table=0, scale_gate=1, translation_gate=0,
                                   translation_table=TRANSLATION_ROWS, selector_gate=1),
                           translation_rows=translation_rows))
    cases.append(case_data("translation track interpolation real dependency body",
                           fixture(helper_table=0, scale_gate=1, translation_gate=0,
                                   translation_table=TRANSLATION_ROWS, translation_progress=1,
                                   selector_gate=1), translation_rows=translation_rows))
    cases.append(case_data("selector track ordinary row transition real dependency body",
                           fixture(helper_table=0, scale_gate=1, translation_gate=1,
                                   selector_gate=0, selector_table=SELECTOR_ROWS),
                           selector_rows=[(7, 0), (3, 0)]))
    cases.append(case_data("selector track sequence selection updates lookup track",
                           fixture(helper_table=0, scale_gate=1, translation_gate=1,
                                   selector_gate=0, selector_table=SELECTOR_ROWS,
                                   helper_sequence=SELECTOR_SEQUENCE, enable=1),
                           selector_rows=[(7, 0), (-1, 0)], selector_seq_words=[0, 1],
                           lookup_ids=[-1, 42]))
    cases.append(case_data("selector track next -3 sequence completion sentinel",
                           fixture(helper_table=0, scale_gate=1, translation_gate=1,
                                   selector_gate=0, selector_table=SELECTOR_ROWS,
                                   helper_sequence=SELECTOR_SEQUENCE, enable=1),
                           selector_rows=[(7, 0), (-1, 0)], selector_seq_words=[0, -3],
                           lookup_ids=[42]))
    results = [compare(image, linked, c) for c in cases]

    # Sensitivity control: omit the meaningful setter +0x50 animation-index
    # store in a private source copy and link the other five candidates intact.
    setter_text = SOURCES["setter"].read_text(encoding="utf-8")
    setter_anchor = "write_u16(object + 0x50, static_cast<uint16_t>(row_index));"
    if setter_text.count(setter_anchor) != 1:
        raise ValueError("setter negative-control mutation anchor is not unique")
    mutant_dir = output / "negative-control"
    mutant_dir.mkdir(parents=True, exist_ok=True)
    mutant_setter = mutant_dir / "setter_missing_animation_store.cpp"
    mutant_setter.write_text(setter_text.replace(setter_anchor,
        "/* negative control omits the +0x50 animation-index store */"), encoding="utf-8")
    mutant_sources = dict(SOURCES)
    mutant_sources["setter"] = mutant_setter
    mutant_linked = build_candidate(mutant_dir / "candidate-build", mutant_sources)
    ordinary_case = next(c for c in cases if c["name"] == "helper ordinary next invokes real setter")
    negative_result = compare(image, linked, ordinary_case, linked_mutant=mutant_linked)
    negative = {"name": "setter_missing_0x50_animation_index_store",
                "detected": not negative_result["passed"], "errors": negative_result["errors"],
                "mutant_source_sha256": sha(mutant_setter.read_bytes()),
                "mutant_elf_sha256": sha(mutant_linked["elf"].read_bytes()),
                "case": negative_result}
    report = {
        "task_id": "h1-preview-full-composition", "passed": all(c["passed"] for c in results) and negative["detected"],
        "reference_image_sha256": sha(image), "original_components": original_components,
        "candidate": linked["meta"], "cases": results, "case_count": len(results),
        "negative_control": negative,
        "first_mismatch": next(({"case": c["name"], "errors": c["errors"],
                                 "first_memory_mismatch": c["first_memory_mismatch"]}
                                for c in results if not c["passed"]), None),
        "projection": ["fault/termination PC", "r0 return", "r4-r11 and SP preservation/equality",
                       "d8-d15 preservation/equality", "FPSCR", "full mapped data SHA-256",
                       "final object bytes", "caller-owned stack bytes", "ordered direct callee names and argument registers"],
        "evidence": {"compiled": "passed", "arm_differential": "partial_synthetic_valid_composition",
                     "caller": "partial_static_call_graph", "runtime": "not_run"},
        "limitations": [
            "All six candidate C++ entrypoints are linked without external stubs. The original side executes the six pinned bodies. No candidate function body was altered; only the private setter mutant used for the negative control.",
            "Inputs are finite synthetic valid, non-aliasing ordinary-memory objects, tables, descriptors, lookups, and sequences. The combined object fields are independently arranged for the covered branches; no constructor/allocation or real H1 asset/runtime binding is established.",
            "The projection checks memory digest for the entire 0x20000-byte synthetic data map, object bytes, r0, callee-saved registers, SP, d8-d15, FPSCR, caller-owned stack, direct call order/arguments, and termination/fault status. Caller-saved scratch GPRs and flags are diagnostic/uncompared; memory access multiplicity/order and below-SP temporary stack residue are not compared.",
            "The divide wrapper receives the helper's positive u16 duration domain. Divide-by-zero helper failure path and arbitrary invalid pointers/indices, overlapping storage, lifecycle, concurrency, MMIO, and game runtime are outside this composition evidence."
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.output)
    passed = sum(c["passed"] for c in report["cases"])
    print(f"full preview composition: {'PASS' if report['passed'] else 'FAIL'} "
          f"{passed}/{report['case_count']}; dependency control="
          f"{'detected' if report['negative_control']['detected'] else 'missed'}; report={args.output/'report.json'}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
