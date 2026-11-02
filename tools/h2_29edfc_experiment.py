"""Offline differential and original TitleConfig_Calc composition for 0x0029EDFC."""
from __future__ import annotations
import hashlib, json, struct, sys
from pathlib import Path
import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips, encode_ips
from tools.h2_calc_experiment import DATA, SP, WORK, Scenario
from tools.semantic_experiment import TEXT
from tools.h2_logical_query_caller_composition import (
    LogicalQueryCalcMachine, compare_runs,
)

IMAGE = ROOT / "extracted/exefs/code.bin"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
BASE = ROOT / "build/agent-work/H2-semantic/h2-titleconfig-002bdac0-convert/run004/staged/code.h2-002bdac0.bin"
BASE_SHA = "3afbd263381b66d18f8ac680529fb27e4291899b70cb74401c8b812552df8774"
SOURCE = ROOT / "experiments/semantic_equivalence/h2_29edfc_candidate.cpp"
PRODUCTION = ROOT / "src/engine/leaf_batch34_b.cpp"
HELPER_SOURCE = ROOT / "src/engine/leaf_batch16_c.cpp"
OUT = ROOT / "build/agent-work/H2-semantic/h2-titleconfig-0029edfc-convert/run001"
ADDRESS = 0x0029EDFC
HELPER = 0x002892C0
SPAN = 80
STOP = 0x0100FFFC
OBJECT = DATA + 0x1000
MASK = 0xFFFFFFFF
NOP = struct.pack("<I", 0xE320F000)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_symbol(name: str, source: Path, symbol: str):
    obj = OUT / name
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr)
    body, relocs = extract_elf_functions_detailed(obj)[symbol]
    return obj, body, relocs


def relocate(body, relocs, entry):
    fixed = bytearray(body)
    rows = []
    for reloc in relocs:
        if reloc.symbol_name != "camp_func_002892c0" or reloc.explicit_addend is not None:
            raise AssertionError(f"unexpected relocation: {reloc}")
        if reloc.relocation_type not in (28, 29):
            raise AssertionError(f"unsupported relocation type: {reloc}")
        insn = struct.unpack_from("<I", fixed, reloc.offset)[0]
        if reloc.relocation_type == 28 and insn & 0x0F000000 != 0x0B000000:
            raise AssertionError(f"R_ARM_CALL is not BL: {insn:#010x}")
        if reloc.relocation_type == 29 and insn & 0x0F000000 != 0x0A000000:
            raise AssertionError(f"R_ARM_JUMP24 is not B: {insn:#010x}")
        delta = HELPER - (entry + reloc.offset + 8)
        if delta & 3 or not -(1 << 25) <= delta < (1 << 25):
            raise AssertionError("ARM branch target out of range or unaligned")
        struct.pack_into("<I", fixed, reloc.offset,
                         (insn & 0xFF000000) | ((delta >> 2) & 0x00FFFFFF))
        rows.append({"offset": reloc.offset, "type": reloc.relocation_type,
                     "symbol": reloc.symbol_name, "target": hex(HELPER)})
    return bytes(fixed), rows


def make_direct(image: bytes, code: bytes | None):
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
    uc.mem_map(TEXT, 0x400000, unicorn.UC_PROT_ALL)
    uc.mem_write(TEXT, image)
    uc.mem_map(DATA, 0x10000, unicorn.UC_PROT_ALL)
    uc.mem_map(0x08000000, 0x10000, unicorn.UC_PROT_ALL)
    uc.mem_map(0x01000000, 0x10000, unicorn.UC_PROT_ALL)
    if code is not None:
        uc.mem_write(ADDRESS, code)
    state = {"stopped": False, "helper": [], "writes": []}

    def on_code(machine, address, size, _):
        if address == STOP:
            state["stopped"] = True
            machine.emu_stop()
        elif address == HELPER:
            state["helper"].append((machine.reg_read(arm.UC_ARM_REG_R0),
                                     machine.reg_read(arm.UC_ARM_REG_R1)))

    def on_write(machine, access, address, size, value, _):
        state["writes"].append((address, size, value & MASK))

    uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
    uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_write)
    uc._h2_state = state
    return uc


def pack_object(test):
    data = bytearray((i * 29 + 0x57) & 0xFF for i in range(0x80))
    struct.pack_into("<I", data, 0x10, test["visible"])
    struct.pack_into("<I", data, 0x1C, test["count"])
    struct.pack_into("<I", data, 0x20, test["start"])
    struct.pack_into("<I", data, 0x24, test["end"])
    data[0x60] = test["flag"]
    data[0x62] = test["disabled"]
    return bytes(data)


def direct_run(machine, index, obj_bytes):
    st = machine._h2_state
    st.update(stopped=False, helper=[], writes=[])
    machine.mem_write(OBJECT, obj_bytes)
    saved = {reg: 0x13570000 + i * 0x01010101 for i, reg in enumerate(
        (arm.UC_ARM_REG_R4, arm.UC_ARM_REG_R5, arm.UC_ARM_REG_R6, arm.UC_ARM_REG_R7,
         arm.UC_ARM_REG_R8, arm.UC_ARM_REG_R9, arm.UC_ARM_REG_R10, arm.UC_ARM_REG_R11))}
    dregs = tuple(getattr(arm, f"UC_ARM_REG_D{i}") for i in range(8, 16))
    dvalues = tuple(0x0123456789ABCDEF ^ i for i in range(8))
    machine.reg_write(arm.UC_ARM_REG_SP, SP)
    machine.reg_write(arm.UC_ARM_REG_LR, STOP)
    machine.reg_write(arm.UC_ARM_REG_R0, OBJECT)
    machine.reg_write(arm.UC_ARM_REG_R1, index & MASK)
    for reg, value in saved.items(): machine.reg_write(reg, value)
    for reg, value in zip(dregs, dvalues): machine.reg_write(reg, value)
    fault = None
    try:
        machine.emu_start(ADDRESS, 0, count=1000)
    except unicorn.UcError as exc:
        fault = str(exc)
    return {
        "fault": fault, "stopped": st["stopped"],
        "return": machine.reg_read(arm.UC_ARM_REG_R0),
        "callee_saved": tuple(machine.reg_read(reg) for reg in saved) == tuple(saved.values()),
        "sp": machine.reg_read(arm.UC_ARM_REG_SP),
        "d8_d15": tuple(machine.reg_read(reg) for reg in dregs),
        "expected_d8_d15": dvalues,
        "object": bytes(machine.mem_read(OBJECT, len(obj_bytes))),
        # The original saves r4-r6/LR on its caller-owned stack; a valid C++
        # leaf may not touch those temporary bytes. Compare persistent object
        # writes and final SP/registers, while retaining the stack-write count.
        "helper": tuple(st["helper"]),
        "writes": tuple(x for x in st["writes"] if OBJECT <= x[0] < OBJECT + len(obj_bytes)),
        "stack_write_count": sum(1 for x in st["writes"] if SP - 0x1000 <= x[0] < SP),
    }


class CursorCallerMachine(LogicalQueryCalcMachine):
    def __init__(self, image, scenario, cursor, mode0=None, mode1=None):
        self.cursor_calls = []
        self.cursor_helper_calls = []
        super().__init__(image, scenario, None, mode0, mode1)
        base = WORK + 0xE8
        for off, value in ((0x10, cursor["visible"]), (0x1C, cursor["count"]),
                           (0x20, cursor["start"]), (0x24, cursor["end"])):
            self.uc.mem_write(base + off, struct.pack("<I", value & MASK))
        self.uc.mem_write(base + 0x60, bytes((cursor["flag"],)))
        self.uc.mem_write(base + 0x62, bytes((cursor["disabled"],)))

    def _code(self, uc, address, size, user_data):
        if address == ADDRESS:
            self.cursor_calls.append((uc.reg_read(arm.UC_ARM_REG_R0),
                                      uc.reg_read(arm.UC_ARM_REG_R1),
                                      uc.reg_read(arm.UC_ARM_REG_LR) - 4))
            return  # execute original or patched body
        if address == HELPER:
            self.cursor_helper_calls.append((uc.reg_read(arm.UC_ARM_REG_R0),
                                             uc.reg_read(arm.UC_ARM_REG_R1),
                                             uc.reg_read(arm.UC_ARM_REG_LR)))
        return super()._code(uc, address, size, user_data)

    def run(self):
        result = super().run()
        result["cursor_calls"] = list(self.cursor_calls)
        result["cursor_helper_calls"] = list(self.cursor_helper_calls)
        return result


def direct_cases():
    cases = []
    for disabled in (1, 0x80, 0xFF):
        cases.append({"name": f"disabled-{disabled:02x}-raw-return", "disabled": disabled,
                      "index": 0x81234567, "visible": 2, "count": 3,
                      "start": 4, "end": 3, "flag": 0xA5})
    enabled = [
        ("equal-preserve-flag", 5, 1, 3, 2, 0x5A),
        ("mismatch-sets-flag", 4, 1, 3, 2, 0x00),
        ("wrap-equal", 0, 0, 1, 0xFFFFFFFF, 0x33),
        ("zero-count-helper", 7, 0, 0, 0, 0x41),
        ("index-zero", 0, 1, 4, 0, 0x11),
        ("negative-index", 0xFFFFFFFF, 1, 4, 0, 0x22),
        ("count-minus-one", 2, 1, 4, 0, 0x12),
        ("index-equals-count", 3, 1, 4, 0, 0x13),
        ("index-count-plus-one", 4, 1, 4, 0, 0x14),
        ("visible-greater-count", 6, 9, 3, 0, 0x15),
        ("high-positive-count", 0x7FFFFFFF, 2, 0x7FFFFFFF, 0x100, 0x16),
    ]
    for name, index, visible, count, start, flag in enabled:
        cases.append({"name": name, "disabled": 0, "index": index,
                      "visible": visible, "count": count, "start": start,
                      "end": (index - start) & MASK, "flag": flag})
    return cases


def direct_projection(result):
    return {key: result[key] for key in (
        "fault", "stopped", "return", "callee_saved", "sp", "d8_d15",
        "expected_d8_d15", "object", "helper", "writes")}


def compile_variant(name, source_text):
    source = OUT / f"{name}.cpp"
    source.write_text(source_text)
    return compile_symbol(f"{name}.o", source, "candidate_0029edfc")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    image, base = IMAGE.read_bytes(), BASE.read_bytes()
    if sha(image) != IMAGE_SHA or sha(base) != BASE_SHA:
        raise SystemExit("pinned image or cumulative base hash mismatch")
    candidate_obj, candidate_body, candidate_relocs = compile_symbol(
        "candidate.o", SOURCE, "candidate_0029edfc")
    production_obj, production_body, production_relocs = compile_symbol(
        "production.o", PRODUCTION, "camp_func_0029edfc")
    helper_obj, helper_body, helper_relocs = compile_symbol(
        "tail-helper.o", HELPER_SOURCE, "camp_func_002892c0")
    if helper_relocs or len(helper_body) != 124:
        raise AssertionError("typed tail helper changed body/relocations unexpectedly")
    candidate_final, candidate_rows = relocate(candidate_body, candidate_relocs, ADDRESS)
    production_final, production_rows = relocate(production_body, production_relocs, ADDRESS)
    candidate_temp, _ = relocate(candidate_body, candidate_relocs, 0x01001000)
    if candidate_final != production_final or candidate_rows != production_rows:
        raise AssertionError("candidate and production function bodies diverge")
    if len(candidate_body) > SPAN:
        raise AssertionError(f"candidate body {len(candidate_body)} exceeds {SPAN}-byte slot")
    original = make_direct(image, None)
    candidate = make_direct(image, candidate_final)
    direct_rows = []
    for test in direct_cases():
        expected = direct_run(original, test["index"], pack_object(test))
        actual = direct_run(candidate, test["index"], pack_object(test))
        if direct_projection(expected) != direct_projection(actual):
            raise AssertionError(f"direct mismatch {test['name']}: "
                                 f"{direct_projection(expected)} != {direct_projection(actual)}")
        if expected["fault"] or not expected["stopped"] or not expected["callee_saved"] or \
                expected["sp"] != SP or expected["d8_d15"] != expected["expected_d8_d15"]:
            raise AssertionError(f"direct ABI/fault gate failed: {test['name']}")
        expected_helpers = 0 if test["disabled"] != 0 else 1
        if len(expected["helper"]) != expected_helpers:
            raise AssertionError(f"unexpected tail-helper count: {test['name']}")
        direct_rows.append({**test, "return": expected["return"],
                            "helper_calls": len(expected["helper"]),
                            "writes": [[hex(a), n, v] for a, n, v in expected["writes"]],
                            "original_stack_write_count": expected["stack_write_count"],
                            "candidate_stack_write_count": actual["stack_write_count"]})

    source_text = SOURCE.read_text()
    mutants = [
        ("disabled-byte-return-zero", source_text.replace("return disabled;", "return 0u;"),
         "disabled-80-raw-return"),
        ("invert-flag-condition", source_text.replace("end + start != index", "end + start == index"),
         "equal-preserve-flag"),
        ("wrong-tail-index-plus-one", source_text.replace(
            "camp_func_002892c0(object, index)", "camp_func_002892c0(object, index + 1u)"),
         "index-zero"),
    ]
    controls = []
    case_by_name = {row["name"]: row for row in direct_cases()}
    for name, mutant_source, case_name in mutants:
        if mutant_source == source_text:
            raise AssertionError(f"mutant source replacement failed: {name}")
        _, body, relocs = compile_variant(f"mutant-{name}", mutant_source)
        mutant_code, _ = relocate(body, relocs, ADDRESS)
        mutant_machine = make_direct(image, mutant_code)
        test = case_by_name[case_name]
        original_result = direct_run(original, test["index"], pack_object(test))
        mutant_result = direct_run(mutant_machine, test["index"], pack_object(test))
        detected = direct_projection(original_result) != direct_projection(mutant_result)
        controls.append({"name": name, "case": case_name, "detected": detected})
        if not detected:
            raise AssertionError(f"negative control escaped: {name}")

    # Actual original TitleConfig_Calc touch paths. One case per selected row
    # proves the helper is reached only for a touched, non-selected row.
    caller_cases = [
        (Scenario("touch-unselected-index-0", 1, row=1, touch={0x101: 6}),
         {"visible": 1, "count": 3, "start": 0, "end": 2, "flag": 0, "disabled": 0}, True, 0),
        (Scenario("touch-unselected-index-1", 1, row=0, touch={0x102: 6}),
         {"visible": 1, "count": 3, "start": 0, "end": 0, "flag": 0, "disabled": 0}, True, 1),
        (Scenario("touch-unselected-index-2", 1, row=0, touch={0x103: 6}),
         {"visible": 1, "count": 0, "start": 0, "end": 0, "flag": 0x40, "disabled": 0}, True, 2),
        (Scenario("selected-row-skipped", 1, row=0, touch={0x101: 6}),
         {"visible": 1, "count": 3, "start": 0, "end": 0, "flag": 0, "disabled": 0}, False, None),
    ]
    final_image = bytearray(image)
    final_image[ADDRESS - TEXT:ADDRESS - TEXT + SPAN] = candidate_final + \
        NOP * ((SPAN - len(candidate_final)) // 4)
    caller_rows = []
    for scenario, cursor, expect_call, handled in caller_cases:
        old = CursorCallerMachine(image, scenario, cursor)
        new = CursorCallerMachine(bytes(final_image), scenario, cursor)
        old_result, new_result = old.run(), new.run()
        err = compare_runs(old_result, new_result)
        if err or old_result["cursor_calls"] != new_result["cursor_calls"] or \
                old_result["cursor_helper_calls"] != new_result["cursor_helper_calls"]:
            raise AssertionError(f"caller mismatch {scenario.label}: {err}; "
                                 f"calls={old_result['cursor_calls']} / {new_result['cursor_calls']}")
        if old_result["fault"] or new_result["fault"] or not old_result["stopped"] or \
                not new_result["stopped"]:
            raise AssertionError(f"caller did not complete: {scenario.label}")
        expected_count = 1 if expect_call else 0
        if len(new_result["cursor_calls"]) != expected_count or \
                len(new_result["cursor_helper_calls"]) != expected_count:
            raise AssertionError(f"unexpected wrapper/helper calls: {scenario.label}")
        if expect_call and new_result["cursor_calls"][0][1] != handled:
            raise AssertionError(f"wrong touched row index: {scenario.label}")
        caller_rows.append({"scenario": scenario.label,
                            "wrapper_call": ([hex(new_result["cursor_calls"][0][2]),
                                              new_result["cursor_calls"][0][1]] if expect_call else None),
                            "tail_helper": ([hex(x) for x in new_result["cursor_helper_calls"][0]] if expect_call else None),
                            "same_return_state_trace_abi": True})

    # Staging is cumulative; caller composition above deliberately uses the
    # pinned original Calc so it reaches the original 0x001EAEA4 call.
    staged = bytearray(base)
    padded = candidate_final + NOP * ((SPAN - len(candidate_final)) // 4)
    staged[ADDRESS - TEXT:ADDRESS - TEXT + SPAN] = padded
    changed = [i for i, (a, b) in enumerate(zip(base, staged)) if a != b]
    if any(not ADDRESS - TEXT <= i < ADDRESS - TEXT + SPAN for i in changed):
        raise AssertionError("staging escaped declared slot")
    ips = encode_ips([(ADDRESS - TEXT, padded)], len(base))
    if apply_ips(base, ips) != bytes(staged):
        raise AssertionError("IPS roundtrip failed")
    stage = OUT / "staged"
    stage.mkdir(exist_ok=True)
    (stage / "code.h2-0029edfc.bin").write_bytes(staged)
    (stage / "code.h2-0029edfc.ips").write_bytes(ips)
    manifest = {"original_sha256": sha(image), "base_sha256": sha(base),
                "staged_sha256": sha(staged), "ips_sha256": sha(ips),
                "address": hex(ADDRESS), "slot_bytes": SPAN,
                "candidate_bytes": len(candidate_body), "changed_bytes": len(changed),
                "only_declared_slot_changed": True, "ips_roundtrip": True,
                "relocations": candidate_rows, "runtime": "not_run"}
    (stage / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    report = {"image_sha256": sha(image), "base_sha256": sha(base),
              "candidate_source_sha256": sha(SOURCE.read_bytes()),
              "candidate_object_sha256": sha(candidate_obj.read_bytes()),
              "production_object_sha256": sha(production_obj.read_bytes()),
              "helper_object_sha256": sha(helper_obj.read_bytes()),
              "candidate_body_sha256": sha(candidate_body),
              "production_body_sha256": sha(production_body),
              "candidate_body_bytes": len(candidate_body),
              "production_body_bytes": len(production_body),
              "tail_helper_body_bytes": len(helper_body),
              "slot_bytes": SPAN, "relocations": candidate_rows,
              "direct_cases": direct_rows, "direct_case_count": len(direct_rows),
              "negative_controls": controls,
              "caller_case_count": len(caller_rows), "caller_cases": caller_rows,
              "staged_sha256": sha(staged), "ips_sha256": sha(ips),
              "changed_bytes": len(changed), "only_declared_slot_changed": True,
              "ips_roundtrip": True, "runtime": "not_run"}
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in ("direct_cases", "caller_cases")}, indent=2))


if __name__ == "__main__":
    main()
