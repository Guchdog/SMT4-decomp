"""Offline state-5 caller-to-title-message composition differential."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools import h1_title_message_experiment as message_exp
from tools.inspect_assets import parse_tbb_header
from tools.semantic_experiment import (
    DATA, DATA_SIZE, INJECT, STACK, STACK_SIZE, TEXT, Runner, arm, unicorn,
)
from tools.tbb_semantic_experiment import TITLE_TBB_SLOT_BASE, TITLE_TBB_SLOT_ID

WINDOW_START, CALL_PC, WINDOW_STOP = 0x001EA12C, 0x001EA15C, 0x001EA160
HELPER = 0x0029F10C
HELPER_COLOR = 0x323232FF
TBB_OFF, TITLE_WORK_OFF, HELP_WORK_OFF = 0x100, 0x800, 0x900
HELP_WORK_SIZE, HELP_FIELD, HELP_STRIDE = 0x564, 0x16, 0x56
HELP_TEXT_OFF, HELP_TEXT_CAPACITY = 0x4D0, 0x40
MANAGER_WORK_GLOBAL = 0x0043DA2C
RETURN_LR = INJECT + 0x1FFC
SP = STACK + 0x1000
IMAGE = ROOT / "extracted/exefs/code.bin"
ASSET = ROOT / "build/semantic-equivalence/real-assets/romfs/title/TitleTable.tbb"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
ASSET_SHA = "edd6bc1de5388e5689f797861ae6947c7c339f9b6bdb63d6c35951d72020fa41"
EXPECTED_TEXT = (
    "Start a new game from the beginning.",
    "Load a saved game and continue playing.",
    "Configure audio settings.",
    "Download additional content.",
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def bl_word(source: int, destination: int) -> bytes:
    displacement = destination - source - 8
    if displacement % 4 or not -(1 << 25) <= displacement < (1 << 25):
        raise ValueError("ARM BL target is unaligned or outside range")
    return struct.pack("<I", 0xEB000000 | ((displacement >> 2) & 0xFFFFFF))


def asset_layout(raw: bytes) -> dict:
    if len(raw) != 880 or sha(raw) != ASSET_SHA:
        raise ValueError("frozen TitleTable.tbb identity mismatch")
    parsed = parse_tbb_header(raw)
    table = parsed["tables"][0]
    if parsed["magic"] != "TBCR" or parsed["header_size"] != 0x20 or table["magic"] != "TBL1":
        raise ValueError("unexpected title table container layout")
    payload_offset = table["offset"] + 0x10
    if table["payload_size"] < 4 * HELP_STRIDE:
        raise ValueError("H1 TBB payload does not contain four rows")
    rows = []
    for index, expected in enumerate(EXPECTED_TEXT):
        payload_relative = HELP_FIELD + HELP_STRIDE * index
        file_offset = payload_offset + payload_relative
        row_limit = payload_offset + HELP_STRIDE * (index + 1)
        nul = raw.find(b"\0", file_offset, row_limit)
        if nul < 0:
            raise ValueError(f"selection {index} has no in-row NUL")
        text = raw[file_offset:nul].decode("ascii")
        if text != expected or len(text) > HELP_TEXT_CAPACITY:
            raise ValueError(f"selection {index} text/domain mismatch: {text!r}")
        rows.append({"selection": index, "payload_relative_offset": payload_relative,
                     "file_offset": file_offset, "nul_file_offset": nul,
                     "text": text, "length": len(text), "line_lengths": [len(text)],
                     "mapped_pointer": DATA + TBB_OFF + file_offset})
    return {"sha256": sha(raw), "size": len(raw), "header_size": parsed["header_size"],
            "table_count": parsed["table_count"], "table0": table,
            "payload_file_offset": payload_offset, "rows": rows}


def make_case(raw: bytes, selection: int) -> dict:
    data = bytearray([0x6D]) * DATA_SIZE
    data[TBB_OFF:TBB_OFF + len(raw)] = raw
    data[TITLE_WORK_OFF:TITLE_WORK_OFF + 0x100] = bytes([0xC3]) * 0x100
    struct.pack_into("<I", data, TITLE_WORK_OFF + 8, selection)
    data[HELP_WORK_OFF:HELP_WORK_OFF + HELP_WORK_SIZE] = bytes([0xA7]) * HELP_WORK_SIZE
    stack = bytes(((i * 37 + 0x23) & 0xFF) for i in range(STACK_SIZE))
    regs = [0xA5A50000 + i * 0x101 for i in range(13)]
    regs[5] = DATA + TITLE_WORK_OFF
    regs[8] = 0x0044E300
    return {"name": f"state5-title-message-selection-{selection}",
            "selection": selection, "data": bytes(data), "stack": stack,
            "registers": regs, "nzcv": 0xA0000000}


class CompositionMachine:
    def __init__(self, image: bytes, linked: dict | None):
        self.image = image
        self.linked = linked
        self.candidate_entry = (linked["symbols"]["h1_title_message_candidate"]
                                if linked else None)
        self.copy_entry = (linked["symbols"]["h1_title_message_forward_copy_candidate"]
                           if linked else None)
        self.runner = Runner(image, WINDOW_START)
        self.uc = self.runner.uc
        if linked:
            if INJECT + len(linked["text"]) >= INJECT + 0x2000:
                raise ValueError("linked candidate text exceeds injection mapping")
            self.uc.mem_write(INJECT, linked["text"])
        self._install_globals()
        self.current_case: dict | None = None
        self.wrong_row_control = False
        self.pre_call: dict | None = None
        self.helper_entry: dict | None = None
        self.copy_calls: list[dict] = []
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._hook)

    def _install_globals(self):
        slot_ptr_addr = TITLE_TBB_SLOT_BASE + TITLE_TBB_SLOT_ID * 0x10 + 4
        for address in (slot_ptr_addr, MANAGER_WORK_GLOBAL):
            page = address & ~0xFFF
            self.uc.mem_protect(page, 0x1000,
                                unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE | unicorn.UC_PROT_EXEC)
        self.uc.mem_write(slot_ptr_addr, struct.pack("<I", DATA + TBB_OFF))
        self.uc.mem_write(MANAGER_WORK_GLOBAL, struct.pack("<I", DATA + HELP_WORK_OFF))

    def _read(self, reg: str) -> int:
        return self.uc.reg_read(getattr(arm, f"UC_ARM_REG_{reg}"))

    def _hook(self, uc, pc, _size, _user):
        if pc == WINDOW_STOP:
            self.runner.stopped = True
            uc.emu_stop()
            return
        if pc == CALL_PC:
            self.pre_call = {"pc": hex(pc),
                "r0": self._read("R0"), "r1": self._read("R1"),
                "r2": self._read("R2"), "r3": self._read("R3"),
                "r12": self._read("R12"),
                "r4": self._read("R4"), "r5": self._read("R5"),
                "r8": self._read("R8"), "sp": self._read("SP"), "lr": self._read("LR")}
            if self.wrong_row_control and self.current_case["selection"] == 1 and self.linked:
                row0 = DATA + TBB_OFF + 0x30 + HELP_FIELD
                uc.reg_write(arm.UC_ARM_REG_R0, row0)
            return
        if (pc == HELPER if self.linked is None else pc == self.candidate_entry):
            self.helper_entry = {"pc": hex(pc), "r0": self._read("R0"),
                                 "r1": self._read("R1"), "r4": self._read("R4"),
                                 "r5": self._read("R5"), "r8": self._read("R8"),
                                 "sp": self._read("SP"), "lr": self._read("LR")}
        copy_pc = 0x002C5FF4 if self.linked is None else self.copy_entry
        if pc == copy_pc:
            self.copy_calls.append({"r0": self._read("R0"), "r1": self._read("R1"),
                                    "r2": self._read("R2"), "pc": hex(pc)})

    def run(self, case: dict, *, wrong_row: bool = False) -> dict:
        self.current_case = case
        self.wrong_row_control = wrong_row
        self.pre_call, self.helper_entry, self.copy_calls = None, None, []
        self.uc.mem_write(DATA, case["data"])
        self.uc.mem_write(STACK, case["stack"])
        self.uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10 | case["nzcv"])
        for i, value in enumerate(case["registers"]):
            self.uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), value)
        self.uc.reg_write(arm.UC_ARM_REG_SP, SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, RETURN_LR)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        d_values = [((0x3F800000 << 32) | 0x3EAAAAAB)] + [
            0x1122334400000000 | (0x55660000 + i) for i in range(1, 8)]
        for i, value in enumerate(d_values, start=8):
            self.uc.reg_write(getattr(arm, f"UC_ARM_REG_D{i}"), value)
        self.runner.reads.clear()
        self.runner.writes.clear()
        self.runner.stops = (WINDOW_STOP,)
        self.runner.stopped = False
        fault = None
        try:
            self.uc.emu_start(WINDOW_START, 0, count=4096)
        except unicorn.UcError as exc:
            fault = f"{exc} at pc={self._read('PC'):#x}"
        registers = {f"r{i}": self._read(f"R{i}") for i in range(13)}
        registers.update({"sp": self._read("SP"), "lr": self._read("LR"),
                          "nzcv": self._read("CPSR") & 0xF0000000})
        d_after = [self._read(f"D{i}") for i in range(8, 16)]
        data_after = bytes(self.uc.mem_read(DATA, DATA_SIZE))
        stack_after = bytes(self.uc.mem_read(SP, STACK + STACK_SIZE - SP))
        return {"fault": fault, "stopped": self.runner.stopped,
                "pc": self._read("PC"), "registers": registers,
                "d8_d15": d_after, "fpscr": self._read("FPSCR"),
                "data": data_after, "data_sha256": sha(data_after),
                "title_work": data_after[TITLE_WORK_OFF:TITLE_WORK_OFF + 0x100],
                "help_work": data_after[HELP_WORK_OFF:HELP_WORK_OFF + HELP_WORK_SIZE],
                "asset_bytes": data_after[TBB_OFF:TBB_OFF + len(ASSET.read_bytes())],
                "stack": stack_after, "stack_sha256": sha(stack_after),
                "pre_call": self.pre_call, "helper_entry": self.helper_entry,
                "copy_calls": list(self.copy_calls),
                "reads": sorted(self.runner.reads), "writes": sorted(self.runner.writes),
                "initial_d8_d15": d_values}


def changed_ranges(before: bytes, after: bytes, base: int) -> list[dict]:
    offsets = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    if not offsets:
        return []
    groups = []
    start = previous = offsets[0]
    for offset in offsets[1:]:
        if offset != previous + 1:
            groups.append((start, previous + 1))
            start = offset
        previous = offset
    groups.append((start, previous + 1))
    return [{"start": base + start, "end_exclusive": base + end,
             "length": end - start} for start, end in groups]


def compare_case(case: dict, original: dict, candidate: dict, row: dict) -> dict:
    errors = []
    expected_pointer = row["mapped_pointer"]
    for label, execution in (("original", original), ("candidate", candidate)):
        if execution["fault"]: errors.append(f"{label} fault")
        if not execution["stopped"] or execution["pc"] != WINDOW_STOP:
            errors.append(f"{label} did not stop at helper return resume PC")
        pre = execution["pre_call"] or {}
        if pre.get("r0") != expected_pointer: errors.append(f"{label} pre-call row pointer differs")
        if pre.get("r1") != HELPER_COLOR: errors.append(f"{label} pre-call color differs")
        if pre.get("r4") != case["selection"]: errors.append(f"{label} pre-call selection differs")
        if pre.get("r5") != DATA + TITLE_WORK_OFF: errors.append(f"{label} title work pointer differs")
        if pre.get("r8") != 0x0044E300: errors.append(f"{label} seeded r8 differs")
        entry = execution["helper_entry"] or {}
        if entry.get("r0") != expected_pointer: errors.append(f"{label} helper entry pointer differs")
        if entry.get("lr") != WINDOW_STOP: errors.append(f"{label} helper LR is not caller resume")
        if execution["registers"]["r0"] != 1: errors.append(f"{label} helper return status differs")
        if execution["registers"]["sp"] != SP: errors.append(f"{label} SP is unbalanced")
        if execution["asset_bytes"] != case["data"][TBB_OFF:TBB_OFF + len(ASSET.read_bytes())]:
            errors.append(f"{label} mutated TitleTable.tbb bytes")
    if original["data"] != candidate["data"]: errors.append("full data mapping differs")
    if original["title_work"] != candidate["title_work"]: errors.append("title-main work differs")
    if original["help_work"] != candidate["help_work"]: errors.append("ButtonHelp work differs")
    if original["stack"] != candidate["stack"]: errors.append("caller-owned stack differs")
    for reg in ("r4", "r5", "r6", "r7", "r8", "r9", "r10", "r11", "sp"):
        if original["registers"][reg] != candidate["registers"][reg]:
            errors.append(f"defined register {reg} differs")
    if original["d8_d15"] != candidate["d8_d15"]: errors.append("d8-d15 differs")
    if original["fpscr"] != candidate["fpscr"]: errors.append("FPSCR differs")
    original_copy_args = [{k: call[k] for k in ("r0", "r1", "r2")}
                          for call in original["copy_calls"]]
    candidate_copy_args = [{k: call[k] for k in ("r0", "r1", "r2")}
                           for call in candidate["copy_calls"]]
    if original_copy_args != candidate_copy_args: errors.append("copy call arguments/order differs")

    text = row["text"].encode("ascii")
    expected_work = bytearray([0xA7]) * HELP_WORK_SIZE
    expected_work[0x4CC:0x4D0] = struct.pack("<I", HELPER_COLOR)
    expected_work[0x4CB] = 1
    expected_work[0x550:0x554] = bytes(4)
    expected_work[0x554] = 0xFF
    expected_work[0x4D0:0x550] = bytes(0x80)
    expected_work[0x4D0:0x4D0 + len(text)] = text
    expected_work[0x55C] = 0
    if original["help_work"] != bytes(expected_work): errors.append("original ButtonHelp output differs from expected fields/text")
    if candidate["help_work"] != bytes(expected_work): errors.append("candidate ButtonHelp output differs from expected fields/text")

    diag = {}
    for label, execution in (("original", original), ("candidate", candidate)):
        diag[label] = {"pre_call_volatile": {f"r{i}": execution["pre_call"][f"r{i}"]
                                                for i in range(4)} |
                       {"r12": execution["pre_call"]["r12"], "nzcv": None},
                       "return_volatile": {f"r{i}": execution["registers"][f"r{i}"]
                                            for i in range(4)} |
                       {"r12": execution["registers"]["r12"],
                        "nzcv": execution["registers"]["nzcv"]}}
    return {"name": case["name"], "selection": case["selection"],
            "text": row["text"], "text_length": row["length"],
            "expected_row_pointer": hex(expected_pointer),
            "passed": not errors, "errors": errors,
            "original": _summary(original), "candidate": _summary(candidate),
            "original_volatile_diagnostics": diag["original"],
            "candidate_volatile_diagnostics": diag["candidate"],
            "changed_title_work_ranges": changed_ranges(case["data"][TITLE_WORK_OFF:TITLE_WORK_OFF + 0x100],
                                                         original["title_work"], DATA + TITLE_WORK_OFF),
            "changed_help_work_ranges": changed_ranges(case["data"][HELP_WORK_OFF:HELP_WORK_OFF + HELP_WORK_SIZE],
                                                        original["help_work"], DATA + HELP_WORK_OFF),
            "first_memory_mismatch": _first_mismatch(original["data"], candidate["data"])}


def _summary(execution: dict) -> dict:
    return {"fault": execution["fault"], "stopped": execution["stopped"],
            "pc": hex(execution["pc"]), "registers": {k: hex(v) for k, v in execution["registers"].items()},
            "d8_d15": [hex(v) for v in execution["d8_d15"]],
            "fpscr": hex(execution["fpscr"]), "data_sha256": execution["data_sha256"],
            "title_work_hex": execution["title_work"].hex(),
            "help_work_hex": execution["help_work"].hex(),
            "stack_sha256": execution["stack_sha256"],
            "pre_call": ({k: (hex(v) if isinstance(v, int) else v)
                           for k, v in execution["pre_call"].items()}
                         if execution["pre_call"] else None),
            "helper_entry": ({k: (hex(v) if isinstance(v, int) else v)
                               for k, v in execution["helper_entry"].items()}
                             if execution["helper_entry"] else None),
            "copy_calls": [{k: (hex(v) if isinstance(v, int) else v) for k, v in c.items()}
                           for c in execution["copy_calls"]],
            "asset_unchanged": execution["asset_bytes"] == ASSET.read_bytes()}


def _first_mismatch(a: bytes, b: bytes) -> dict | None:
    if a == b:
        return None
    offset = next(i for i, (x, y) in enumerate(zip(a, b)) if x != y)
    return {"address": hex(DATA + offset), "offset": offset, "original": a[offset], "candidate": b[offset]}


def run(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    image = IMAGE.read_bytes()
    raw = ASSET.read_bytes()
    if sha(image) != IMAGE_SHA:
        raise ValueError("pinned code.bin identity mismatch")
    rows = asset_layout(raw)
    linked = message_exp.compile_candidate(output / "candidate-build")
    helper_address = linked["symbols"]["h1_title_message_candidate"]
    branch = bl_word(CALL_PC, helper_address)
    candidate_image = bytearray(image)
    call_offset = CALL_PC - TEXT
    before_branch = bytes(candidate_image[call_offset:call_offset + 4])
    candidate_image[call_offset:call_offset + 4] = branch
    changed = [i for i, (a, b) in enumerate(zip(image, candidate_image)) if a != b]
    if bytes(candidate_image[call_offset:call_offset + 4]) != branch or any(
            not call_offset <= offset < call_offset + 4 for offset in changed):
        raise ValueError("private candidate image differs outside the state-5 helper BL")
    original = CompositionMachine(image, None)
    candidate = CompositionMachine(bytes(candidate_image), linked)
    case_results, executions = [], {}
    for row in rows["rows"]:
        case = make_case(raw, row["selection"])
        o = original.run(case)
        c = candidate.run(case)
        executions[row["selection"]] = (case, o, c, row)
        case_results.append(compare_case(case, o, c, row))

    # Sensitivity control changes only the candidate's incoming helper r0 for
    # selection 1, after the real caller's row pointer has been recorded.
    ctl_case, ctl_original, _, ctl_row = executions[1]
    wrong = candidate.run(ctl_case, wrong_row=True)
    wrong_entry_pointer = wrong["helper_entry"]["r0"]
    expected_selection1 = ctl_row["mapped_pointer"]
    expected_selection0 = rows["rows"][0]["mapped_pointer"]
    wrong_work_matches_original = wrong["help_work"] == ctl_original["help_work"]
    wrong_control = {"name": "selection1_candidate_entry_forced_to_row0",
        "pre_call_pointer": hex(wrong["pre_call"]["r0"]),
        "expected_selection1_pointer": hex(expected_selection1),
        "wrong_helper_entry_pointer": hex(wrong_entry_pointer),
        "expected_selection0_pointer": hex(expected_selection0),
        "candidate_entry_pointer_rejected": wrong_entry_pointer != expected_selection1,
        "final_help_work_differs_from_original": not wrong_work_matches_original,
        "first_memory_mismatch": _first_mismatch(ctl_original["data"], wrong["data"]),
        "wrong_entry_work_text": wrong["help_work"][HELP_TEXT_OFF:HELP_TEXT_OFF + len(EXPECTED_TEXT[0])].decode("ascii"),
        "expected_selection1_text": EXPECTED_TEXT[1]}
    wrong_control["detected"] = (wrong["pre_call"]["r0"] == expected_selection1
                                  and wrong_entry_pointer == expected_selection0
                                  and wrong_control["candidate_entry_pointer_rejected"]
                                  and wrong_control["final_help_work_differs_from_original"]
                                  and wrong_control["first_memory_mismatch"] is not None)

    report = {"schema_version": 1, "task_id": "h1-title-message-caller-composition",
              "passed": all(case["passed"] for case in case_results) and wrong_control["detected"],
              "reference_image_sha256": sha(image), "asset": rows,
              "candidate": linked["meta"],
              "caller_window": {"start": hex(WINDOW_START), "call_pc": hex(CALL_PC),
                                "stop_after_helper_return": hex(WINDOW_STOP),
                                "pinned_call_word": before_branch.hex(),
                                "candidate_bl_word": branch.hex(),
                                "candidate_helper_address": hex(helper_address),
                                "candidate_image_changed_offsets": [hex(x) for x in changed],
                                "candidate_image_patch_width": 4,
                                "candidate_image_diff_bytes": len(changed),
                                "original_routes_to": hex(HELPER),
                                "candidate_routes_to": hex(helper_address),
                                "tbb_getters": "pinned Tbb_GetGlobalSubTable/Tbb_GetSubTable/Tbb_GetPayloadData in both images"},
              "frame": {"title_main_work": hex(DATA + TITLE_WORK_OFF),
                        "help_work": hex(DATA + HELP_WORK_OFF), "help_work_size": HELP_WORK_SIZE,
                        "manager_work_global": hex(MANAGER_WORK_GLOBAL),
                        "tbb_global_slot_pointer": hex(TITLE_TBB_SLOT_BASE + TITLE_TBB_SLOT_ID * 0x10 + 4),
                        "asset_container": hex(DATA + TBB_OFF), "sp": hex(SP),
                        "seeded_r8": hex(0x0044E300), "nzcv": hex(0xA0000000),
                        "initial_d8_d15": [hex(x) for x in executions[0][1]["initial_d8_d15"]],
                        "s17_initial_bits": hex(0x3F800000)},
              "case_count": len(case_results), "cases": case_results,
              "wrong_row_control": wrong_control,
              "projection": ["pre-call pointer/color/index/title block/r8/SP/LR",
                             "helper entry pointer and LR; return/r0/resume PC/SP",
                             "r4-r11, d8-d15 and FPSCR equality", "full 0x1000 data map",
                             "separate title-main and 0x564-byte ButtonHelp blocks",
                             "unchanged real TBB asset", "complete caller-owned stack",
                             "normalized real copy dependency call arguments/order",
                             "r0-r3/r12/NZCV diagnostics only"],
              "evidence": {"compiled": "passed", "arm_differential": "partial_real_asset_caller_window",
                           "caller": "partial_state5_window_only", "runtime": "not_run"},
              "limitations": [
                  "The execution starts at 0x001EA12C with a synthetic active-state caller frame and stops at 0x001EA160 after helper return. It does not execute state-5 readiness/input work, the full callback, later branches, or title lifecycle.",
                  "The four rows are from one frozen 880-byte TitleTable.tbb asset. The H1 TBB getters and caller arithmetic execute as pinned ARM, but no live resource manager, object construction, callback binding, rendering, or other locale is exercised.",
                  "The candidate-side image differs from pinned code.bin only in the 4-byte BL at 0x001EA15C; the candidate helper and its linked copy dependency execute from private injection text. This proves the selected composition boundary, not production integration/placement.",
                  "The candidate safe domain remains valid manager/work pointers, these bounded single-line strings, and non-overlapping forward-copy spans. Malformed/overlong strings, invalid pointers, MMIO, event/input behavior, Azahar/emulator, and game-runtime equivalence are not validated.",
                  "Caller-saved volatile registers and condition flags may differ and are recorded diagnostically; memory read/write footprints are not compared because the pinned copier uses different alignment paths." ]}
    report["first_mismatch"] = next(({"selection": c["selection"], "errors": c["errors"],
                                      "first_memory_mismatch": c["first_memory_mismatch"]}
                                     for c in case_results if not c["passed"]), None)
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    report = run(output)
    passed = sum(case["passed"] for case in report["cases"])
    print(f"title-message caller composition: {'PASS' if report['passed'] else 'FAIL'} "
          f"{passed}/{report['case_count']}; wrong-row control="
          f"{'detected' if report['wrong_row_control']['detected'] else 'missed'}; "
          f"report={output / 'report.json'}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
