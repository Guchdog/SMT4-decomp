#!/usr/bin/env python3
"""Differentially exercise TitleConfig_Draw with explicit renderer services.

The pinned ARM callback and experimental C++ are run from identical initialized
snapshots in Unicorn. Cursor, TBB, layout, rendering, and touch helper semantics
are mocked at the exact call boundaries; this does not test the title caller or
the visible meaning of UI IDs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import unicorn
from unicorn import arm_const as arm
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang
from tools.semantic_experiment import TEXT, arm_branch

ADDRESS = 0x002CAFD0
INJECT = 0x01000000
INJECT_SIZE = 0x10000
DATA = 0x02000000
DATA_SIZE = 0x10000
WORK = DATA + 0x100
SPRITE = DATA + 0x300
NODES = DATA + 0x1000
TABLE = DATA + 0x2800
PAYLOAD = DATA + 0x3000
GPU = DATA + 0x4000
GPU_STATE = GPU + 0x1000 + 0x2AC
STACK = 0x08000000
STACK_SIZE = 0x8000
SP = STACK + STACK_SIZE // 2
RETURN = INJECT + INJECT_SIZE - 4
INDIRECT_CALLBACK = INJECT + 0x8000
WORK_GLOBAL = 0x0044E2D0
CONFIG_GLOBAL = 0x0044E0F8
RENDER_ROOT_GLOBAL = 0x0044EA00
SYMBOL = "candidate_002cafd0"
SOURCE = ROOT / "experiments/semantic_equivalence/h2_draw_candidate.cpp"
CODE_DEFAULT = ROOT / "extracted/exefs/code.bin"

SERVICES = {
    0x002BF558: "panel_draw",
    0x002BF460: "sprite_draw",
    0x0029F260: "cursor_scroll",
    0x0029F248: "cursor_selected_row",
    0x0029D8E4: "cursor_row_count",
    0x002BF6D0: "layout_node",
    0x002C5FA4: "render_value",
    0x002C0EC4: "tbb_subtable",
    0x002C0E9C: "tbb_payload",
    0x002BE7FC: "format_text",
    0x002BE77C: "font_draw",
    0x0029D8FC: "touch_state",
}

# BLX helper targets use bit 0 to select instruction state. The original Draw
# callback reaches only the formatter in Thumb state; all other named helpers
# and the fixture's indirect callback are ARM entries.
SERVICE_THUMB = {0x002BE7FC: True}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relocated_candidate(obj: Path) -> tuple[bytes, list[dict]]:
    functions = extract_elf_functions_detailed(obj)
    if SYMBOL not in functions:
        raise ValueError(f"object lacks {SYMBOL}")
    code, relocations = functions[SYMBOL]
    fixed = bytearray(code)
    records = []
    for relocation in relocations:
        if relocation.relocation_type != 2 or relocation.symbol_name:
            raise ValueError(f"unsupported candidate relocation: {relocation}")
        original = struct.unpack_from("<I", fixed, relocation.offset)[0]
        target = (original + INJECT) & 0xFFFFFFFF
        struct.pack_into("<I", fixed, relocation.offset, target)
        records.append({"offset": hex(relocation.offset), "addend": hex(original),
                        "guest_target": hex(target), "kind": "local R_ARM_ABS32 .text"})
    return bytes(fixed), records


class DrawScenario:
    def __init__(self, label: str, *, state: int = 1, row_count: int = 3,
                 selected_row: int = 0, scroll: int = 0,
                 touches: dict[int, int] | None = None, cache_flag: int = 0,
                 cached_values: tuple[int, ...] = (0, 0, 0, 0, 0, 0, 0, 0),
                 expect_no_tbb: bool = False):
        self.label = label
        self.state = state
        self.row_count = row_count
        self.selected_row = selected_row
        self.scroll = scroll
        self.touches = touches or {}
        self.cache_flag = cache_flag
        self.cached_values = cached_values
        self.expect_no_tbb = expect_no_tbb


def directed_scenarios() -> list[DrawScenario]:
    cases = [
        DrawScenario("row-count-zero", row_count=0),
        DrawScenario("row-count-negative", row_count=-1),
        DrawScenario("inactive-three-rows", state=0),
    ]
    for selected_row in (0, 1, 2):
        cases.append(DrawScenario(f"active-selected-row-{selected_row}",
                                  selected_row=selected_row))
        for code in (1, 2, 6):
            for offset, name in ((0x1C, "row"), (0x1E, "decrement"),
                                 (0x20, "increment"), (0x22, "special")):
                handle = 0x110 + (offset - 0x1C) // 2
                cases.append(DrawScenario(
                    f"active-row-{selected_row}-{name}-touch-{code}",
                    selected_row=selected_row, touches={handle: code}))
    cases.extend((
        DrawScenario("cache-dirty-flag", selected_row=1, cache_flag=1),
        DrawScenario("cached-values-match", selected_row=2,
                     cached_values=(0x60000100, 0x60000700, 0, 0, 0, 0, 0, 0)),
        DrawScenario("negative-absolute-index", state=0, row_count=1,
                     scroll=-1, expect_no_tbb=True),
        DrawScenario("absolute-index-three", state=0, row_count=1,
                     scroll=3, expect_no_tbb=True),
    ))
    return cases


class DrawMachine:
    def __init__(self, image: bytes, candidate: bytes | None = None,
                 scenario: DrawScenario | None = None):
        self.scenario = scenario or DrawScenario("default")
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.mem_map(TEXT, 0x00400000, unicorn.UC_PROT_ALL)
        self.uc.mem_write(TEXT, image)
        self.uc.mem_map(INJECT, INJECT_SIZE, unicorn.UC_PROT_ALL)
        self.uc.mem_map(DATA, DATA_SIZE, unicorn.UC_PROT_ALL)
        self.uc.mem_map(STACK, STACK_SIZE, unicorn.UC_PROT_ALL)
        if candidate is not None:
            self.uc.mem_write(INJECT, candidate)
            self.uc.mem_write(ADDRESS, arm_branch(ADDRESS, INJECT))
        self.trace: list[tuple] = []
        self.stop = False
        self.hook_fault: str | None = None
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._code)
        self._initialize()

    @staticmethod
    def _pack_s16(data: bytearray, offset: int, value: int):
        struct.pack_into("<h", data, offset, value)

    def _initialize(self):
        sc = self.scenario
        work = bytearray(0x158)
        struct.pack_into("<I", work, 0x08, sc.state)
        struct.pack_into("<I", work, 0x5C, SPRITE)
        for offset, value in ((0x1C, 0x110), (0x1E, 0x111), (0x20, 0x112), (0x22, 0x113)):
            self._pack_s16(work, offset, value)
        struct.pack_into("<III", work, 0x28, 2, 5, 9)
        # Explicit safe words for option indices -1 and 3 in the guard fixtures.
        struct.pack_into("<I", work, 0x24, 4)
        struct.pack_into("<I", work, 0x34, 7)
        self.uc.mem_write(WORK, bytes(work))
        self.uc.mem_write(WORK_GLOBAL, struct.pack("<I", WORK))
        self.uc.mem_write(CONFIG_GLOBAL, bytes.fromhex("3250503000000000"))
        sprite = bytearray(0x20)
        struct.pack_into("<ii", sprite, 0x0C, 110 << 12, 55 << 12)
        self.uc.mem_write(SPRITE, bytes(sprite))

        # Every possible group-0x2F node gets deterministic signed layout
        # coordinates. Values are fixtures only; no visible label is inferred.
        for node_id in range(0x80):
            node = bytearray(0x10)
            struct.pack_into("<hh", node, 8, (node_id % 7) * 3 - 4,
                             (node_id % 5) * 2 - 2)
            self.uc.mem_write(NODES + node_id * 0x10, bytes(node))

        # TBB row descriptors use the contract's 0x96 byte stride.
        self.uc.mem_write(PAYLOAD, bytes(0x96 * 3 + 0x20))
        self.uc.mem_write(TABLE, bytes(0x40))

        cache = bytearray(0x80)
        struct.pack_into("<I", cache, 0, 0)  # active row index
        for index, value in enumerate(sc.cached_values):
            struct.pack_into("<I", cache, 8 + index * 4, value)
        cache[0x18] = sc.cache_flag & 0xFF
        struct.pack_into("<I", cache, 0x1C, INDIRECT_CALLBACK)
        self.uc.mem_write(GPU_STATE, bytes(cache))
        self.uc.mem_write(RENDER_ROOT_GLOBAL, struct.pack("<I", GPU))

    def _return(self, value: int = 0):
        self.uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_PC, self.uc.reg_read(arm.UC_ARM_REG_LR))

    def _record_draw(self, name: str, args: list[int]):
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        stack = struct.unpack("<II", bytes(self.uc.mem_read(sp, 8)))
        self.trace.append((name, *[x & 0xFFFFFFFF for x in args], *stack))

    def _code(self, uc, address, _size, _user_data):
        if address == RETURN:
            self.stop = True
            uc.emu_stop()
            return
        if address == INDIRECT_CALLBACK:
            actual_thumb = bool(uc.reg_read(arm.UC_ARM_REG_CPSR) & 0x20)
            if actual_thumb:
                self.hook_fault = "cache_callback entered Thumb; fixture target is ARM"
                uc.emu_stop()
                return
            self.trace.append(("cache_callback", uc.reg_read(arm.UC_ARM_REG_R0)))
            self._return(uc.reg_read(arm.UC_ARM_REG_R0))
            return
        name = SERVICES.get(address)
        if name is None:
            return
        actual_thumb = bool(uc.reg_read(arm.UC_ARM_REG_CPSR) & 0x20)
        expected_thumb = SERVICE_THUMB.get(address, False)
        if actual_thumb != expected_thumb:
            self.hook_fault = (
                f"{name} entered with CPSR.T={int(actual_thumb)}, "
                f"expected {int(expected_thumb)}"
            )
            uc.emu_stop()
            return
        r = [uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4)]
        sc = self.scenario
        result = 0
        if address in (0x002BF558, 0x002BF460):
            self._record_draw(name, r)
        elif address == 0x0029F260:
            self.trace.append((name, r[0]))
            result = sc.scroll
        elif address == 0x0029F248:
            self.trace.append((name, r[0]))
            result = sc.selected_row
        elif address == 0x0029D8E4:
            self.trace.append((name, r[0]))
            result = sc.row_count
        elif address == 0x002BF6D0:
            self.trace.append((name, r[0], r[1]))
            result = NODES + (r[1] & 0xFF) * 0x10
        elif address == 0x002C5FA4:
            self.trace.append((name, *r[:3]))
            result = 0x60000000 | ((r[1] & 0xFFFF) << 8) | (r[2] & 0xFF)
        elif address == 0x002C0EC4:
            self.trace.append((name, r[0], r[1]))
            result = TABLE
        elif address == 0x002C0E9C:
            self.trace.append((name, r[0]))
            result = PAYLOAD
        elif address == 0x002BE7FC:
            descriptor_index = max(0, r[2] - PAYLOAD) // 0x96
            self.trace.append((name, r[1], descriptor_index, int(actual_thumb)))
            uc.mem_write(r[0], f"Option{descriptor_index}\x00".encode("ascii"))
        elif address == 0x002BE77C:
            floats = tuple(uc.reg_read(getattr(arm, f"UC_ARM_REG_S{i}")) for i in range(5))
            text = bytes(uc.mem_read(r[2], 0x5C)).split(b"\x00", 1)[0].decode("ascii", "replace")
            self.trace.append((name, r[0], r[1], text, *floats))
        elif address == 0x0029D8FC:
            handle = r[0] & 0xFFFF
            result = sc.touches.get(handle, 0)
            self.trace.append((name, handle, result))
        self._return(result)

    def run(self) -> dict:
        r_ids = tuple(getattr(arm, f"UC_ARM_REG_R{i}") for i in range(13))
        initial_r = [0xA5A50000 + i * 0x10101 for i in range(13)]
        initial_r[0] = 0xCAFEBABE
        self.uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10 | 0x60000000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        for reg, value in zip(r_ids, initial_r):
            self.uc.reg_write(reg, value)
        self.uc.reg_write(arm.UC_ARM_REG_SP, SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
        d_ids = tuple(getattr(arm, f"UC_ARM_REG_D{i}") for i in range(8, 16))
        initial_d = tuple(0x0123456789ABCDEF ^ i for i in range(8))
        for reg, value in zip(d_ids, initial_d):
            self.uc.reg_write(reg, value)
        self.trace.clear()
        fault = None
        try:
            self.uc.emu_start(ADDRESS, 0, count=200000)
        except unicorn.UcError as exc:
            fault = str(exc)
        preserved = tuple(self.uc.reg_read(reg) for reg in r_ids[4:12])
        preserved += (self.uc.reg_read(arm.UC_ARM_REG_SP),)
        preserved += tuple(self.uc.reg_read(reg) for reg in d_ids)
        expected = tuple(initial_r[4:12]) + (SP,) + initial_d
        return {
            "stopped": self.stop,
            "fault": self.hook_fault or fault,
            "return": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "preserved": preserved,
            "expected_preserved": expected,
            "work": bytes(self.uc.mem_read(WORK, 0x158)),
            "config": bytes(self.uc.mem_read(CONFIG_GLOBAL, 8)),
            "cache": bytes(self.uc.mem_read(GPU_STATE, 0x80)),
            "trace": list(self.trace),
        }


def compare(original: dict, candidate: dict) -> str | None:
    for label, record in (("original", original), ("candidate", candidate)):
        if record["fault"]:
            return f"{label} fault: {record['fault']}"
        if not record["stopped"]:
            return f"{label} failed to reach return sentinel"
        if record["preserved"] != record["expected_preserved"]:
            return f"{label} violates callee-saved register/SP/d8-d15 ABI"
    for field in ("return", "pc", "work", "config", "cache", "trace"):
        if original[field] != candidate[field]:
            return f"{field} differs"
    return None


def compare_fixture(code: bytes, image: bytes, sc: DrawScenario):
    original = DrawMachine(image, scenario=sc).run()
    rebuilt = DrawMachine(image, candidate=code, scenario=sc).run()
    return original, rebuilt, compare(original, rebuilt)


def compile_candidate(source: Path, output: Path):
    obj = output
    build = compile_tu_armv6k(source, obj, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr or f"ARM compilation failed: {source}")
    body, relocations = relocated_candidate(obj)
    return body, relocations, build


def experiment(code_path: Path, output: Path) -> dict:
    start = time.perf_counter()
    output.mkdir(parents=True, exist_ok=False)
    image = code_path.read_bytes()
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    image_hash = hashlib.sha256(image).hexdigest()
    if len(image) != game["code_bin_size"] or image_hash != game["code_sha256"]:
        raise ValueError("--code must be the pinned configured original code image")
    source_hash = sha256(SOURCE)
    body, relocations, build = compile_candidate(SOURCE, output / "h2_draw_candidate.o")

    cases = []
    first = None
    for scenario in directed_scenarios():
        original, rebuilt, error = compare_fixture(body, image, scenario)
        original_format_indices = [event[2] for event in original["trace"]
                                   if event[0] == "format_text"]
        candidate_format_indices = [event[2] for event in rebuilt["trace"]
                                    if event[0] == "format_text"]
        original_subtable_calls = sum(event[0] == "tbb_subtable"
                                      for event in original["trace"])
        original_payload_calls = sum(event[0] == "tbb_payload"
                                     for event in original["trace"])
        candidate_subtable_calls = sum(event[0] == "tbb_subtable"
                                       for event in rebuilt["trace"])
        candidate_payload_calls = sum(event[0] == "tbb_payload"
                                      for event in rebuilt["trace"])
        guard_ok = (not scenario.expect_no_tbb
                    or (not original_format_indices and not candidate_format_indices
                        and not any(event[0] in ("tbb_subtable", "tbb_payload")
                                    for event in original["trace"] + rebuilt["trace"])))
        difference = error or (None if guard_ok else "unexpected TBB access in guard fixture")
        item = {"case": scenario.label, "passed": difference is None,
                "trace_count": len(original["trace"]),
                "formatted_descriptor_indices": original_format_indices,
                "tbb_subtable_calls": original_subtable_calls,
                "tbb_payload_calls": original_payload_calls,
                "candidate_tbb_subtable_calls": candidate_subtable_calls,
                "candidate_tbb_payload_calls": candidate_payload_calls,
                "difference": difference}
        cases.append(item)
        if difference is not None and first is None:
            first = {"case": scenario.label, "reason": difference,
                     "original_trace": original["trace"],
                     "candidate_trace": rebuilt["trace"],
                     "original_cache": original["cache"].hex(),
                     "candidate_cache": rebuilt["cache"].hex()}

    # Compile a faulty TBB-stride candidate as a real behavioral negative control.
    bad_source = output / "h2_draw_candidate_bad_stride.cpp"
    source_text = SOURCE.read_text(encoding="utf-8")
    old_expression = "static_cast<u32>(absolute_index) * 0x96u"
    new_expression = "static_cast<u32>(absolute_index) * 0x56u"
    if source_text.count(old_expression) != 1:
        raise ValueError("could not uniquely construct the wrong-stride control")
    bad_source.write_text(source_text.replace(old_expression, new_expression), encoding="utf-8")
    bad_body, _, bad_build = compile_candidate(bad_source, output / "h2_draw_candidate_bad_stride.o")
    control_case = DrawScenario("negative-control-wrong-tbb-stride", selected_row=1)
    ctrl_original = DrawMachine(image, scenario=control_case).run()
    ctrl_bad = DrawMachine(image, candidate=bad_body, scenario=control_case).run()
    negative = {"name": "compiled-wrong-tbb-stride",
                "detected": compare(ctrl_original, ctrl_bad) is not None,
                "difference": compare(ctrl_original, ctrl_bad)}

    # Negative control: restore the former even pointer so BLX deliberately
    # enters the Thumb formatter's address in ARM state. The helper hook must
    # catch this before returning a synthetic result.
    old_pointer = "call<void>(0x002BE7FDu, formatted, kTextFormatString, descriptor);"
    bad_pointer = "call<void>(0x002BE7FCu, formatted, kTextFormatString, descriptor);"
    if source_text.count(old_pointer) != 1:
        raise ValueError("could not uniquely construct the wrong-state control")
    bad_state_source = output / "h2_draw_candidate_bad_formatter_state.cpp"
    bad_state_source.write_text(source_text.replace(old_pointer, bad_pointer), encoding="utf-8")
    bad_state_body, _, bad_state_build = compile_candidate(
        bad_state_source, output / "h2_draw_candidate_bad_formatter_state.o")
    state_case = DrawScenario("negative-control-wrong-formatter-state", selected_row=0)
    state_original = DrawMachine(image, scenario=state_case).run()
    state_bad = DrawMachine(image, candidate=bad_state_body, scenario=state_case).run()
    state_difference = compare(state_original, state_bad)
    state_negative = {"name": "compiled-even-formatter-pointer",
                      "detected": state_difference is not None,
                      "difference": state_difference,
                      "original_formatter_mode": next(
                          (event[-1] for event in state_original["trace"]
                           if event[0] == "format_text"), None),
                      "candidate_fault": state_bad["fault"]}

    if sha256(SOURCE) != source_hash:
        raise RuntimeError("candidate source changed during experiment")
    compiler = subprocess.run([str(find_clang()), "--version"], capture_output=True,
                              text=True, check=True).stdout.splitlines()[0]
    passed = (first is None and all(item["passed"] for item in cases)
              and negative["detected"] and state_negative["detected"])
    report = {
        "schema": 1,
        "passed": passed,
        "scope": "TitleConfig_Draw isolated callback with explicit cursor/TBB/layout/render/touch mocks",
        "reference_sha256": image_hash,
        "source_sha256": source_hash,
        "runner_sha256": sha256(Path(__file__)),
        "object_sha256": sha256(output / "h2_draw_candidate.o"),
        "compiler": compiler,
        "compile_command": build.args,
        "compile_exit": build.returncode,
        "candidate_bytes": len(body),
        "relocations_applied": relocations,
        "negative_control_compile_exit": bad_build.returncode,
        "wrong_state_control_compile_exit": bad_state_build.returncode,
        "case_count": len(cases),
        "cases_passed": sum(item["passed"] for item in cases),
        "first_counterexample": first,
        "negative_control": negative,
        "instruction_state_negative_control": state_negative,
        "evidence": {"compiled": "passed", "arm_differential": "passed" if passed else "failed",
                     "caller": "not_run", "runtime": "not_run"},
        "limits": [
            "Cursor, TBB, layout, format/font, panel/sprite, render-value, and touch behavior are explicit deterministic mocks; helper internals and visible label/input meanings are unresolved.",
            "Work and configuration bytes are compared across the callback; renderer cache bytes and ordered helper/callback traces are also compared.",
            "No initializer-created caller state, task scheduler ordering, concurrent calc state, Azahar runtime, or user input was tested.",
            "Rows 0, 1, and 2 use controlled helper results. Separate guard fixtures exercise absolute indices -1 and 3 with option reads inside the initialized work allocation; these do not establish that either cursor state is caller-reachable.",
        ],
        "cases": cases,
        "elapsed_seconds": round(time.perf_counter() - start, 3),
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=CODE_DEFAULT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = experiment(args.code, args.output)
    print(json.dumps({"passed": report["passed"], "report": str(args.output / "report.json"),
                      "case_count": report["case_count"],
                      "cases_passed": report["cases_passed"],
                      "first_counterexample": report["first_counterexample"],
                      "negative_control": report["negative_control"]}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
