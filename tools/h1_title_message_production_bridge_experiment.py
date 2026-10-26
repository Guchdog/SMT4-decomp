"""Compile the production H1 title-message TU and compare it with pinned ARM."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import re
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_check import find_clang, get_armv6k_flags
from tools.inspect_assets import parse_tbb_header
from tools.semantic_experiment import arm, require_unicorn, unicorn

TEXT, TEXT_SIZE = 0x00100000, 0x00400000
INJECT, INJECT_SIZE = 0x01000000, 0x00010000
DATA, DATA_SIZE = 0x02000000, 0x00020000
STACK, STACK_SIZE = 0x08000000, 0x00002000
WORK_OFF, MANAGER_OFF, INPUT_OFF, ASSET_OFF = 0x2000, 0x1000, 0x8000, 0x100
WORK_SIZE, RETURN, SP = 0x564, INJECT + 0xFFF0, STACK + 0x1000
MANAGER_GLOBAL = 0x0043DA28
HELPER = 0x0029F10C
ASSET_PATH = ROOT / "build/semantic-equivalence/real-assets/romfs/title/TitleTable.tbb"
IMAGE_PATH = ROOT / "extracted/exefs/code.bin"
SOURCE = ROOT / "src/camp/title_message.cpp"
SOURCE_HEADER = ROOT / "src/camp/title_message.h"
UI_SOURCE = ROOT / "src/ui/ui_runtime2.cpp"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
ASSET_SHA = "edd6bc1de5388e5689f797861ae6947c7c339f9b6bdb63d6c35951d72020fa41"
EXPECTED = (
    "Start a new game from the beginning.",
    "Load a saved game and continue playing.",
    "Configure audio settings.",
    "Download additional content.",
)
STRIDE, FIELD = 0x56, 0x16


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha(path.read_bytes())


def build_candidate(out: Path) -> dict:
    build = out / "candidate-build"
    build.mkdir(parents=True, exist_ok=False)
    clang = find_clang()
    flags = get_armv6k_flags(ROOT, clang)
    support = build / "bridge_test_support.cpp"
    support.write_text(
        '#include "camp/unite.h"\n'
        'namespace smt4::camp {\n'
        '__attribute__((section(".title_manager"))) '
        'ButtonHelpManager g_ButtonHelpManager = {};\n'
        '}\n', encoding="utf-8")
    source_obj, support_obj = build / "title_message.o", build / "bridge_test_support.o"
    commands = []
    for src, obj in ((SOURCE, source_obj), (support, support_obj)):
        argv = [str(clang), *flags, "-c", str(src), "-o", str(obj)]
        cp = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
        commands.append({"argv": argv, "exit_code": cp.returncode,
                         "stdout": cp.stdout, "stderr": cp.stderr})
        if cp.returncode:
            raise RuntimeError(f"compile failed for {src}: {cp.stderr}")
    elf = build / "title_message_production_tu.elf"
    link_argv = [str(clang), *flags, "-nostdlib", "-fuse-ld=lld",
                 f"-Wl,-Ttext={INJECT:#x}",
                 f"-Wl,--section-start=.title_manager={DATA + MANAGER_OFF:#x}",
                 "-Wl,-e,H1_SetTitleHelpMessage", "-Wl,--build-id=none",
                 "-Wl,--no-undefined", str(source_obj), str(support_obj), "-o", str(elf)]
    lp = subprocess.run(link_argv, cwd=ROOT, capture_output=True, text=True)
    commands.append({"argv": link_argv, "exit_code": lp.returncode,
                     "stdout": lp.stdout, "stderr": lp.stderr})
    if lp.returncode:
        raise RuntimeError(f"candidate link failed: {lp.stderr}")

    clang_dir = clang.parent
    objcopy, nm = clang_dir / "llvm-objcopy.exe", clang_dir / "llvm-nm.exe"
    if not objcopy.is_file() or not nm.is_file():
        raise RuntimeError("llvm-objcopy and llvm-nm are required")
    text_path = build / "candidate-text.bin"
    subprocess.run([str(objcopy), "--dump-section", f".text={text_path}", str(elf)],
                   check=True, capture_output=True, text=True)
    nm_result = subprocess.run([str(nm), "-n", str(elf)], check=True,
                               capture_output=True, text=True)
    symbols = {}
    for line in nm_result.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 3:
            symbols[fields[2]] = int(fields[0], 16)
    if "H1_SetTitleHelpMessage" not in symbols:
        raise RuntimeError("linked production TU does not expose H1_SetTitleHelpMessage")
    manager_symbol = next((name for name, address in symbols.items()
                           if "g_ButtonHelpManager" in name and address == DATA + MANAGER_OFF), None)
    if manager_symbol is None:
        raise RuntimeError("typed ButtonHelp manager is not linked at the isolated test address")
    undefined = subprocess.run([str(nm), "-u", str(elf)], check=True,
                               capture_output=True, text=True).stdout.splitlines()
    if any(line.strip() for line in undefined):
        raise RuntimeError(f"candidate has unresolved symbols: {undefined}")
    text = text_path.read_bytes()
    if len(text) > INJECT_SIZE:
        raise RuntimeError("production TU text exceeds isolated injection mapping")
    return {"text": text, "entry": symbols["H1_SetTitleHelpMessage"],
            "manager": symbols[manager_symbol], "elf": elf, "object": source_obj,
            "support_object": support_obj, "text_path": text_path,
            "build_dir": build,
            "meta": {"compiler": str(clang), "commands": commands,
                     "source_sha256": file_sha(SOURCE), "header_sha256": file_sha(SOURCE_HEADER),
                     "object_sha256": file_sha(source_obj), "support_object_sha256": file_sha(support_obj),
                     "elf_sha256": file_sha(elf), "text_sha256": file_sha(text_path),
                     "text_size": len(text), "entry": hex(symbols["H1_SetTitleHelpMessage"]),
                     "manager_symbol": manager_symbol, "manager_address": hex(symbols[manager_symbol]),
                     "defined_symbols": sorted(symbols),
                     "undefined_symbols": []}}


def asset_cases(raw: bytes) -> tuple[list[dict], dict]:
    if len(raw) != 880 or sha(raw) != ASSET_SHA:
        raise ValueError("TitleTable.tbb does not match the frozen 880-byte input")
    parsed = parse_tbb_header(raw)
    table = parsed["tables"][0]
    payload_file = table["offset"] + 0x10
    cases, rows = [], []
    for index, expected in enumerate(EXPECTED):
        file_offset = payload_file + FIELD + index * STRIDE
        row_end = payload_file + (index + 1) * STRIDE
        nul = raw.find(b"\0", file_offset, row_end)
        if nul < 0:
            raise ValueError(f"TBB row {index} does not terminate within its slot")
        text = raw[file_offset:nul]
        if text.decode("ascii") != expected or len(text) > 64:
            raise ValueError(f"unexpected or out-of-domain H1 row {index}")
        data = blank_data()
        data[ASSET_OFF:ASSET_OFF + len(raw)] = raw
        message = DATA + ASSET_OFF + file_offset
        cases.append({"name": f"asset-row-{index}", "data": bytes(data),
                      "message": message, "color": 0x323232FF,
                      "text": expected, "input_length": len(text),
                      "file_offset": file_offset, "selection": index})
        rows.append({"selection": index, "file_offset": file_offset,
                     "nul_file_offset": nul, "length": len(text),
                     "text": expected, "mapped_pointer": hex(message)})
    return cases, {"sha256": sha(raw), "size": len(raw),
                   "payload_file_offset": payload_file, "rows": rows}


def blank_data() -> bytearray:
    return bytearray([0xA7]) * DATA_SIZE


def synthetic_case(name: str, message: bytes, color: int = 0x323232FF) -> dict:
    data = blank_data()
    data[INPUT_OFF:INPUT_OFF + 128] = b"Q" * 128
    if len(message) > 128:
        raise ValueError("synthetic message fixture must fit its readable 128-byte span")
    data[INPUT_OFF:INPUT_OFF + len(message)] = message
    return {"name": name, "data": bytes(data), "message": DATA + INPUT_OFF,
            "color": color, "text": None, "input_length": len(message)}


def fixtures(raw: bytes) -> tuple[list[dict], list[dict], dict]:
    rows, asset_info = asset_cases(raw)
    valid = rows + [
        {"name": "null-reset", "data": bytes(blank_data()), "message": 0,
         "color": 0x323232FF, "text": None, "input_length": None},
        synthetic_case("empty-nonnull", b"\0", 0x80402010),
        synthetic_case("single-line-64-byte-boundary", b"A" * 64 + b"\0"),
        synthetic_case("two-lines-scan-end-terminator", b"A" * 64 + b"\n" + b"B" * 62 + b"\0"),
        synthetic_case("high-bit-content", b"A\xff\x80Z\0"),
        synthetic_case("newline-first-byte", b"\nSecond\0"),
    ]
    controls = [
        synthetic_case("overlong-first-line-guard", b"X" * 65 + b"\0"),
        synthetic_case("overlong-second-line-guard", b"A\n" + b"B" * 65 + b"\0"),
        synthetic_case("unterminated-128-byte-guard", b"Y" * 128),
    ]
    return valid, controls, asset_info


def regread(uc, name: str) -> int:
    return uc.reg_read(getattr(arm, f"UC_ARM_REG_{name}"))


class Machine:
    def __init__(self, image: bytes, candidate: dict | None):
        require_unicorn()
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.mem_map(TEXT, TEXT_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE | unicorn.UC_PROT_EXEC)
        self.uc.mem_write(TEXT, image)
        self.uc.mem_map(INJECT, INJECT_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE | unicorn.UC_PROT_EXEC)
        self.candidate = candidate
        if candidate:
            self.uc.mem_write(INJECT, candidate["text"])
        self.uc.mem_map(DATA, DATA_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.uc.mem_map(STACK, STACK_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.reads: set[int] = set()
        self.writes: set[int] = set()
        self.copy_calls: list[dict] = []
        self.fault = None
        self.uc.hook_add(unicorn.UC_HOOK_MEM_READ, self._mem_read)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._mem_write)
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._code)

    def _mem_read(self, _uc, _access, address, _size, _value, _user):
        self.reads.add(address)

    def _mem_write(self, _uc, _access, address, _size, _value, _user):
        self.writes.add(address)

    def _code(self, uc, address, _size, _user):
        if address == RETURN:
            uc.emu_stop()
            return
        if not self.candidate and address in (0x002C5FF4, 0x002BCF58):
            self.copy_calls.append({"pc": hex(address),
                                    "args": [hex(regread(uc, reg)) for reg in ("R0", "R1", "R2")]})

    def run(self, case: dict, *, null_manager: bool = False) -> dict:
        self.uc.mem_write(DATA, case["data"])
        manager_work = 0 if null_manager else DATA + WORK_OFF
        # Candidate uses its typed linked global; original ARM reads the pinned
        # absolute manager cell. Both have the same manager/work fixture bytes.
        self.uc.mem_write(DATA + MANAGER_OFF, bytes([1, 0, 0, 0]) + struct.pack("<I", manager_work))
        self.uc.mem_write(MANAGER_GLOBAL + 4, struct.pack("<I", manager_work))
        self.uc.mem_write(STACK, bytes([0x5A]) * STACK_SIZE)
        for i in range(13):
            self.uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), 0xA5A50000 | i)
        self.uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10 | 0xA0000000)
        self.uc.reg_write(arm.UC_ARM_REG_SP, SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.reg_write(arm.UC_ARM_REG_FPSCR, 0x01000000)
        for i in range(8, 16):
            self.uc.reg_write(getattr(arm, f"UC_ARM_REG_D{i}"), 0x1122334400000000 | i)
        self.uc.reg_write(arm.UC_ARM_REG_R0, case["message"])
        self.uc.reg_write(arm.UC_ARM_REG_R1, case["color"])
        preserved_before = {f"r{i}": regread(self.uc, f"R{i}") for i in range(4, 12)}
        d_before = [regread(self.uc, f"D{i}") for i in range(8, 16)]
        self.reads, self.writes, self.copy_calls, self.fault = set(), set(), [], None
        start = HELPER if self.candidate is None else self.candidate["entry"]
        try:
            self.uc.emu_start(start, 0, count=250000)
        except unicorn.UcError as exc:
            self.fault = f"{exc} at pc={regread(self.uc, 'PC'):#x}"
        data_after = bytes(self.uc.mem_read(DATA, DATA_SIZE))
        work = data_after[WORK_OFF:WORK_OFF + WORK_SIZE]
        return {"fault": self.fault, "stopped": regread(self.uc, "PC") == RETURN,
                "pc": hex(regread(self.uc, "PC")), "r0": regread(self.uc, "R0"),
                "sp": regread(self.uc, "SP"), "lr": regread(self.uc, "LR"),
                "preserved_before": {key: hex(value) for key, value in preserved_before.items()},
                "preserved_after": {f"r{i}": hex(regread(self.uc, f"R{i}")) for i in range(4, 12)},
                "d_before": [hex(x) for x in d_before],
                "d_after": [hex(regread(self.uc, f"D{i}")) for i in range(8, 16)],
                "fpscr": hex(regread(self.uc, "FPSCR")), "data": data_after,
                "data_sha256": sha(data_after), "work": work, "work_sha256": sha(work),
                "stack": bytes(self.uc.mem_read(SP, STACK + STACK_SIZE - SP)),
                "copy_calls": list(self.copy_calls), "read_count": len(self.reads),
                "write_count": len(self.writes),
                "pinned_manager_cell": bytes(self.uc.mem_read(MANAGER_GLOBAL, 8)),
                "typed_manager": data_after[MANAGER_OFF:MANAGER_OFF + 8],
                "asset": data_after[ASSET_OFF:ASSET_OFF + 880]}


def compare_case(case: dict, original: dict, candidate: dict) -> dict:
    errors = []
    if original["fault"] or candidate["fault"]:
        errors.append(f"fault: original={original['fault']!r}, candidate={candidate['fault']!r}")
    if not original["stopped"] or not candidate["stopped"]:
        errors.append("one execution did not return to the seeded LR")
    if original["r0"] != candidate["r0"]:
        errors.append("defined return r0 differs")
    if original["sp"] != SP or candidate["sp"] != SP:
        errors.append("SP is not balanced")
    if original["data"] != candidate["data"]:
        errors.append("full data mapping differs")
    if original["work"] != candidate["work"]:
        errors.append("ButtonHelp work differs")
    if original["typed_manager"] != candidate["typed_manager"]:
        errors.append("typed manager storage differs")
    if original["pinned_manager_cell"] != candidate["pinned_manager_cell"]:
        errors.append("pinned manager cell differs")
    if original["asset"] != candidate["asset"]:
        errors.append("mapped asset differs")
    if original["stack"] != candidate["stack"]:
        errors.append("caller-owned stack differs")
    for key in original["preserved_after"]:
        if original["preserved_after"][key] != candidate["preserved_after"][key]:
            errors.append(f"callee-saved {key} differs")
    if original["d_after"] != candidate["d_after"]:
        errors.append("d8-d15 differs")
    if original["fpscr"] != candidate["fpscr"]:
        errors.append("FPSCR differs")
    return {"name": case["name"], "text": case["text"], "input_length": case["input_length"],
            "asset_file_offset": case.get("file_offset"), "selection": case.get("selection"),
            "expected_return": "0xff" if case["message"] == 0 else "0x1",
            "passed": not errors, "errors": errors,
            "original": summarize(original), "candidate": summarize(candidate),
            "original_copy_calls": original["copy_calls"]}


def summarize(run: dict) -> dict:
    return {key: (hex(run[key]) if key in {"r0", "sp", "lr"} else run[key])
            for key in ("fault", "stopped", "pc", "r0", "sp", "lr", "preserved_after",
                        "d_after", "fpscr", "data_sha256", "work_sha256", "copy_calls",
                        "read_count", "write_count")}


def run_experiment(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    image = IMAGE_PATH.read_bytes()
    if sha(image) != IMAGE_SHA:
        raise ValueError("configured pinned code.bin hash mismatch")
    raw_tbb = ASSET_PATH.read_bytes()
    valid_cases, invalid_cases, asset_info = fixtures(raw_tbb)
    candidate = build_candidate(output)
    original_machine, candidate_machine = Machine(image, None), Machine(image, candidate)
    comparisons = []
    for case in valid_cases:
        original = original_machine.run(case)
        compiled = candidate_machine.run(case)
        comparisons.append(compare_case(case, original, compiled))

    controls = []
    for case in invalid_cases:
        result = candidate_machine.run(case)
        unchanged = result["work"] == case["data"][WORK_OFF:WORK_OFF + WORK_SIZE]
        control = {"name": case["name"], "candidate_return": hex(result["r0"]),
                   "fault": result["fault"], "workspace_unchanged": unchanged,
                   "detected": result["fault"] is None and result["r0"] == 0 and unchanged}
        controls.append(control)

    null_manager_case = synthetic_case("null-work-manager-guard", b"Valid\0")
    null_manager = candidate_machine.run(null_manager_case, null_manager=True)
    controls.append({"name": "null-work-manager-guard", "candidate_return": hex(null_manager["r0"]),
                     "fault": null_manager["fault"],
                     "work_unchanged": null_manager["work"] == null_manager_case["data"][WORK_OFF:WORK_OFF + WORK_SIZE],
                     "detected": null_manager["fault"] is None and null_manager["r0"] == 0 and
                                null_manager["work"] == null_manager_case["data"][WORK_OFF:WORK_OFF + WORK_SIZE]})

    ui_source = UI_SOURCE.read_text(encoding="utf-8")
    disabled_blocks = re.findall(r"#if\s+0\b(.*?)#endif", ui_source, flags=re.DOTALL)
    inactive_source = "\n".join(disabled_blocks)
    active_source = re.sub(r"#if\s+0\b.*?#endif", "", ui_source, flags=re.DOTALL)
    candidate_symbols = candidate["meta"]["defined_symbols"]
    checks = {"cmake_glob_includes_source": '"${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp"' in
              (ROOT / "CMakeLists.txt").read_text(encoding="utf-8"),
              "declaration_count": (ROOT / "src/camp/title_message.h").read_text(encoding="utf-8").count("H1_SetTitleHelpMessage"),
              "definition_count": (ROOT / "src/camp/title_message.cpp").read_text(encoding="utf-8").count("H1_SetTitleHelpMessage"),
              "h1_call_count": ui_source.count("camp::H1_SetTitleHelpMessage("),
              "legacy_call_count": ui_source.count("Camp_SetSlotMessage("),
              "h1_calls_in_disabled_callback_draft": inactive_source.count("camp::H1_SetTitleHelpMessage(") == 2 and
                  active_source.count("camp::H1_SetTitleHelpMessage(") == 0,
              "legacy_call_remains_disabled_non_h1_draft": inactive_source.count("Camp_SetSlotMessage(") == 1 and
                  active_source.count("Camp_SetSlotMessage(") == 0,
              "no_global_alias": not any(name in candidate_symbols for name in
                  ("camp_func_0029f10c", "Camp_SetSlotMessage")),
              "shared_copy_body_unchanged": file_sha(ROOT / "src/engine/leaf_batch37_c.cpp") ==
              "3199e5a1eb3e7b46e2273bb3eb6696b0556ea9d8da9ad6259fa26eb2a785a717",
              "original_helper_body_unchanged": file_sha(ROOT / "src/engine/leaf_batch33_c.cpp") ==
              "9235d238d06faa5e5fa52f18037302c2adc402d764c42d11147405906b75072c",
              "ledger_unchanged": file_sha(ROOT / "config/functions.csv") ==
              "b27580ea4af85889e1167e7af5f898f66e82517c0293fcc3a586fea504a94be8"}
    checks["two_h1_calls_only"] = (checks["h1_call_count"] == 2 and
                                    checks["h1_calls_in_disabled_callback_draft"] and
                                    checks["legacy_call_remains_disabled_non_h1_draft"])
    checks["one_api_declaration_definition"] = checks["declaration_count"] == 1 and checks["definition_count"] == 1

    report = {"schema_version": 1, "task_id": "h1-title-message-source-bridge",
              "passed": all(item["passed"] for item in comparisons) and all(c["detected"] for c in controls) and all(
                  [checks["cmake_glob_includes_source"], checks["two_h1_calls_only"],
                   checks["one_api_declaration_definition"], checks["no_global_alias"],
                   checks["shared_copy_body_unchanged"], checks["original_helper_body_unchanged"],
                   checks["ledger_unchanged"]]),
              "code_sha256": sha(image), "asset": asset_info,
              "candidate": candidate["meta"], "production_source": str(SOURCE),
              "h1_callsite_note": "The state-2/state-5 C++ call expressions are in the existing #if 0 readable ui_func_001e989c draft. They now name this bridge, but the currently compiled ui_func_001e989c remains its naked ARM body; no live callback dispatch was executed or changed.",
              "production_source_sha256": file_sha(SOURCE), "source_header_sha256": file_sha(SOURCE_HEADER),
              "ui_source_sha256": file_sha(UI_SOURCE),
              "ledger_source_hashes": {
                  "src/engine/leaf_batch33_c.cpp": file_sha(ROOT / "src/engine/leaf_batch33_c.cpp"),
                  "src/engine/leaf_batch37_c.cpp": file_sha(ROOT / "src/engine/leaf_batch37_c.cpp"),
                  "config/functions.csv": file_sha(ROOT / "config/functions.csv")},
              "case_count": len(comparisons), "cases": comparisons,
              "controls": controls, "integration_checks": checks,
              "evidence": {"compiled": "passed", "arm_differential": "partial",
                           "caller": "partial",
                           "runtime": "not_run"},
              "limits": ["Only exact src/camp/title_message.cpp was compiled and linked with a minimal typed manager test definition; no canonical full CMake build or final production executable/map was run.",
                         "Original equivalence is claimed only for null reset and bounded valid strings (at most two lines, each at most 64 bytes, NUL within 128 readable bytes), with valid ButtonHelp work storage.",
                         "Invalid manager/work and overlong/unterminated strings are candidate guard controls only; the pinned helper does not guard these conditions and may fault or write beyond modeled storage.",
                         "The two H1 C++ call expressions are in the pre-existing #if 0 readable callback draft; the compiled callback remains naked ARM. Static source binding is shown, but live state-2/state-5 dispatch, manager initialization/lifecycle, rendering, other callers, full runtime, and Azahar were not tested.",
                         "The original 0x0029F10C and shared 0x002C5FF4 ledger bodies and ledger labels were left untouched. The candidate uses its private internal forward-copy routine; global copy behavior was not changed."],
              "first_mismatch": next((case for case in comparisons if not case["passed"]), None)}
    (output / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output / "integration-checks.json").write_text(json.dumps(checks, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run_experiment(args.output)
    print(f"H1 production source bridge: {'PASS' if report['passed'] else 'FAIL'} "
          f"{sum(case['passed'] for case in report['cases'])}/{report['case_count']}; "
          f"controls={sum(control['detected'] for control in report['controls'])}/{len(report['controls'])}; "
          f"report={args.output / 'report.json'}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
