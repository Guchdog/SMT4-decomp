"""Offline differential and mode-2 caller composition for 0x002C17D4."""
from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

import capstone
import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips, encode_ips
from tools.h2_calc_experiment import CalcMachine, Scenario, DATA, RETURN, SP, U32
from tools.semantic_experiment import arm_branch

IMAGE = ROOT / "extracted/exefs/code.bin"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
PRODUCTION = ROOT / "src/engine/leaf_batch32_c.cpp"
CANDIDATE = ROOT / "experiments/semantic_equivalence/h2_2c17d4_candidate.cpp"
OUT = ROOT / "build/agent-work/H2-semantic/h2-titleconfig-002c17d4-convert/run001"
TEXT_BASE = 0x00100000
ADDRESS = 0x002C17D4
WRAPPER = 0x002C1830
TABLE = 0x004099C0
MODE = 0x004650A8
STATE_INACTIVE = 0x004E3C28
STATE_ACTIVE = 0x004E3C48
INJECT = 0x01000000
TABLE_BYTES = 31 * 8


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_symbol(name: str, source: Path, symbol: str):
    obj = OUT / name
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr)
    body, relocs = extract_elf_functions_detailed(obj)[symbol]
    fixed = bytearray(body)
    rows = []
    for reloc in relocs:
        if reloc.relocation_type != 2 or reloc.symbol_name:
            raise AssertionError(f"unexpected relocation: {reloc}")
        old = struct.unpack_from("<I", fixed, reloc.offset)[0]
        struct.pack_into("<I", fixed, reloc.offset, (old + INJECT) & U32)
        rows.append({"offset": reloc.offset, "type": reloc.relocation_type,
                     "addend": hex(old), "value": hex((old + INJECT) & U32)})
    return obj, bytes(fixed), rows


class QueryMachine(CalcMachine):
    def __init__(self, image: bytes, candidate: bytes | None = None):
        self.target_access: list[tuple[str, int, int]] = []
        self.helper_calls: list[tuple[int, int]] = []
        self.wrapper_entries: list[tuple[int, int]] = []
        super().__init__(image, entry_code=None, scenario=Scenario("query", 1))
        if candidate is not None:
            self.uc.mem_write(INJECT, candidate)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_READ, self._target_read)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._target_write)

    @staticmethod
    def _targeted(address: int) -> bool:
        return (TABLE <= address < TABLE + TABLE_BYTES
                or address == MODE or address in (STATE_INACTIVE, STATE_ACTIVE))

    def _target_read(self, uc, access, address, size, value, _):
        if self._targeted(address):
            self.target_access.append(("read", address, size))

    def _target_write(self, uc, access, address, size, value, _):
        if self._targeted(address):
            self.target_access.append(("write", address, size))

    def _code(self, uc, address, size, user_data):
        if address == ADDRESS:
            caller = uc.reg_read(arm.UC_ARM_REG_LR) - 4
            self.helper_calls.append((caller, uc.reg_read(arm.UC_ARM_REG_R0)))
            return  # execute the pinned or staged helper body
        if address == WRAPPER:
            self.wrapper_entries.append((uc.reg_read(arm.UC_ARM_REG_R0),
                                         uc.reg_read(arm.UC_ARM_REG_R1)))
            return  # execute the pinned original dispatcher body
        return super()._code(uc, address, size, user_data)


def pinned_table(image: bytes) -> bytes:
    offset = TABLE - TEXT_BASE
    return image[offset:offset + TABLE_BYTES]


def table_with_row(base: bytes, query_id: int, gate: int, mask: int) -> bytes:
    rows = bytearray(base)
    struct.pack_into("<II", rows, query_id * 8, gate & U32, mask & U32)
    return bytes(rows)


def setup_globals(machine: QueryMachine, rows: bytes, mode: int,
                  inactive: int, active: int):
    machine.uc.mem_write(TABLE, rows)
    machine.uc.mem_write(MODE, struct.pack("<I", mode & U32))
    machine.uc.mem_write(STATE_INACTIVE, struct.pack("<I", inactive & U32))
    machine.uc.mem_write(STATE_ACTIVE, struct.pack("<I", active & U32))
    machine.target_access.clear()
    machine.helper_calls.clear()
    machine.wrapper_entries.clear()


def direct_run(image: bytes, query_id: int, rows: bytes, mode: int,
               inactive: int, active: int, candidate: bytes | None = None) -> dict:
    machine = QueryMachine(image, candidate)
    setup_globals(machine, rows, mode, inactive, active)
    entry = INJECT if candidate is not None else ADDRESS
    regs = tuple(getattr(arm, f"UC_ARM_REG_R{i}") for i in range(13))
    initial = tuple((0xC0010000 + i * 0x01010101) & U32 for i in range(13))
    for reg, value in zip(regs, initial):
        machine.uc.reg_write(reg, value)
    machine.uc.reg_write(arm.UC_ARM_REG_R0, query_id & U32)
    machine.uc.reg_write(arm.UC_ARM_REG_SP, SP)
    machine.uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
    machine.trace.clear(); machine.reads.clear(); machine.writes.clear()
    fault = None
    try:
        machine.uc.emu_start(entry, 0, count=10000)
    except unicorn.UcError as exc:
        fault = str(exc)
    after = tuple(machine.uc.reg_read(reg) for reg in regs)
    return {
        "fault": fault,
        "return": machine.uc.reg_read(arm.UC_ARM_REG_R0),
        "preserved_r4_r11": after[4:12] == initial[4:12],
        "sp": machine.uc.reg_read(arm.UC_ARM_REG_SP),
        "lr": machine.uc.reg_read(arm.UC_ARM_REG_LR),
        "target_access": list(machine.target_access),
    }


def wrapper_run(image: bytes, original: bytes, query_id: int, rows: bytes,
                mode: int, inactive: int, active: int) -> dict:
    machine = QueryMachine(image)
    setup_globals(machine, rows, mode, inactive, active)
    for i in range(13):
        machine.uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), 0xBEEF0000 + i)
    machine.uc.reg_write(arm.UC_ARM_REG_R0, query_id & U32)
    machine.uc.reg_write(arm.UC_ARM_REG_R1, 2)
    machine.uc.reg_write(arm.UC_ARM_REG_SP, SP)
    machine.uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
    machine.trace.clear(); machine.reads.clear(); machine.writes.clear()
    fault = None
    try:
        machine.uc.emu_start(WRAPPER, 0, count=10000)
    except unicorn.UcError as exc:
        fault = str(exc)
    return {
        "fault": fault, "return": machine.uc.reg_read(arm.UC_ARM_REG_R0),
        "stopped": machine.stop, "wrapper_entries": list(machine.wrapper_entries),
        "helper_calls": list(machine.helper_calls),
        "target_access": list(machine.target_access),
        "sp": machine.uc.reg_read(arm.UC_ARM_REG_SP),
    }


def expected_read_trace(query_id: int, gate: int, mode: int) -> list[tuple[str, int, int]]:
    if query_id >= 31:
        return []
    row = TABLE + query_id * 8
    result = [("read", row, 4)]
    if gate == 0:
        state_addr = STATE_ACTIVE if mode & 1 else STATE_INACTIVE
        result.extend((("read", row + 4, 4), ("read", MODE, 4),
                       ("read", state_addr, 4)))
    return result


def accesses_by_address(accesses: list) -> list[tuple[str, int]]:
    return [(kind, address) for kind, address, _size in accesses]


def direct_cases(image: bytes, candidate: bytes) -> list[dict]:
    original_rows = pinned_table(image)
    cases = []
    for query_id in range(31):
        gate, mask = struct.unpack_from("<II", original_rows, query_id * 8)
        for mode, inactive, active in (
            (0x100, mask, 0), (0x101, 0, mask),
            (0x200, 0, 0), (0x201, mask | 0x80000000, mask ^ U32),
        ):
            cases.append((f"pinned-{query_id}-{mode:x}", query_id, original_rows,
                          gate, mask, mode, inactive, active))

    for query_id in (31, 32, 0x7FFFFFFF, 0x80000000, U32):
        rows = table_with_row(bytes(TABLE_BYTES), 0, 0, 1)
        cases.append((f"out-of-range-{query_id:x}", query_id, rows, 0, 0, 0, 1, 1))

    cases.extend([
        ("gate-short-circuit", 16, table_with_row(bytes(TABLE_BYTES), 16, 1, 1),
         1, 1, 0x101, 0, 1),
        ("mask-zero", 2, table_with_row(bytes(TABLE_BYTES), 2, 0, 0),
         0, 0, 1, U32, U32),
        ("one-bit-overlap", 9, table_with_row(bytes(TABLE_BYTES), 9, 0, 0x400),
         0, 0x400, 1, 0, 0x400),
        ("multiple-bit-overlap", 5, table_with_row(bytes(TABLE_BYTES), 5, 0, 0x60),
         0, 0x60, 0, 0x60, 0),
        ("no-overlap", 4, table_with_row(bytes(TABLE_BYTES), 4, 0, 0x20),
         0, 0x20, 0x80000001, 0x10, 0x40),
    ])

    results = []
    for label, query_id, rows, gate, mask, mode, inactive, active in cases:
        chosen = active if mode & 1 else inactive
        expected = 0 if query_id >= 31 or gate != 0 else int((chosen & mask) != 0)
        original = direct_run(image, query_id, rows, mode, inactive, active)
        compiled = direct_run(image, query_id, rows, mode, inactive, active, candidate)
        wanted = expected_read_trace(query_id, gate, mode)
        wanted_candidate = [(kind, address, 1 if address == MODE else size)
                            for kind, address, size in wanted]
        passed = (original["fault"] is None and compiled["fault"] is None
                  and original["return"] == compiled["return"] == expected
                  and original["target_access"] == wanted
                  and compiled["target_access"] == wanted_candidate
                  and original["preserved_r4_r11"] and compiled["preserved_r4_r11"]
                  and original["sp"] == compiled["sp"] == SP
                  and original["lr"] == compiled["lr"] == RETURN)
        results.append({"label": label, "id": hex(query_id), "gate": hex(gate),
                        "mask": hex(mask), "mode": hex(mode),
                        "inactive": hex(inactive), "active": hex(active),
                        "expected": expected, "original": original,
                        "candidate": compiled, "pass": passed})
    return results


def dispatcher_cases(original_image: bytes, staged_image: bytes,
                     original_rows: bytes) -> list[dict]:
    cases = []
    for query_id in range(3, 7):
        _, primary_mask = struct.unpack_from("<II", original_rows, query_id * 8)
        _, secondary_mask = struct.unpack_from("<II", original_rows, (query_id + 9) * 8)
        for label, word, expected_ids in (
            ("primary", primary_mask, [query_id]),
            ("secondary", secondary_mask, [query_id, query_id + 9]),
            ("none", 0, [query_id, query_id + 9]),
            ("both-short-circuit", primary_mask | secondary_mask, [query_id]),
        ):
            mode = 0x101
            rows = original_rows
            original = wrapper_run(original_image, original_image, query_id, rows,
                                   mode, 0, word)
            staged = wrapper_run(staged_image, original_image, query_id, rows,
                                 mode, 0, word)
            helper_ids = [entry[1] for entry in original["helper_calls"]]
            expected_return = 1 if label in ("primary", "secondary", "both-short-circuit") else 0
            passed = (original["fault"] is None and staged["fault"] is None
                      and original["stopped"] and staged["stopped"]
                      and original["return"] == staged["return"] == expected_return
                      and helper_ids == expected_ids
                      and original["helper_calls"] == staged["helper_calls"]
                      and accesses_by_address(original["target_access"])
                      == accesses_by_address(staged["target_access"]))
            cases.append({"id": query_id, "case": label, "state_word": hex(word),
                          "original": original, "staged": staged, "pass": passed})

    out_of_range = 31
    original = wrapper_run(original_image, original_image, out_of_range, original_rows,
                           0x102, 0, 0xFFFFFFFF)
    staged = wrapper_run(staged_image, original_image, out_of_range, original_rows,
                         0x102, 0, 0xFFFFFFFF)
    cases.append({"id": out_of_range, "case": "dispatcher-out-of-range",
                  "original": original, "staged": staged,
                  "pass": original["return"] == staged["return"] == 0
                  and original["helper_calls"] == staged["helper_calls"]
                  == [(0x002C18F0, out_of_range)]
                  and original["fault"] is None and staged["fault"] is None})
    return cases


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    image = IMAGE.read_bytes()
    if sha(image) != IMAGE_SHA:
        raise AssertionError("pinned original image hash changed")
    _, candidate, candidate_relocs = compile_symbol(
        "candidate.o", CANDIDATE, "candidate_002c17d4")
    _, production, production_relocs = compile_symbol(
        "production.o", PRODUCTION, "ui_func_002c17d4")
    if candidate != production:
        raise AssertionError("candidate and production bodies differ")

    slot_size = 92
    if len(production) > slot_size:
        raise AssertionError(f"production body {len(production)} exceeds {slot_size}-byte slot")
    offset = ADDRESS - TEXT_BASE
    original_slot = image[offset:offset + slot_size]
    staged_bytes = bytearray(image)
    staged_bytes[offset:offset + slot_size] = production + bytes(slot_size - len(production))
    staged_image = bytes(staged_bytes)
    patch = encode_ips([(offset, staged_bytes[offset:offset + slot_size])], len(image))
    if apply_ips(image, patch) != staged_image:
        raise AssertionError("slot-only IPS roundtrip failed")
    changed = [i for i, (a, b) in enumerate(zip(image, staged_image)) if a != b]
    if changed and (min(changed) < offset or max(changed) >= offset + slot_size):
        raise AssertionError("staged changes escaped the declared slot")

    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoded = list(decoder.disasm(production, ADDRESS))
    if (any(x.mnemonic in ("bl", "blx") for x in decoded)
            or not any(x.mnemonic == "bx" and x.op_str == "lr" for x in decoded)):
        raise AssertionError("candidate ARM entry/call/return audit failed")
    call_sites = (0x002C18F0, 0x002C19B0)
    interworking = []
    for pc in call_sites:
        word = struct.unpack_from("<I", image, pc - TEXT_BASE)[0]
        delta = (word & 0x00FFFFFF) << 2
        if delta & 0x02000000:
            delta -= 0x04000000
        target = pc + 8 + delta
        interworking.append({"pc": hex(pc), "instruction": hex(word),
                             "target": hex(target), "target_even_arm": target == ADDRESS
                             and (target & 1) == 0})
    if not all(x["target_even_arm"] for x in interworking):
        raise AssertionError("original wrapper ARM call target/interworking check failed")

    direct = direct_cases(image, candidate)
    caller = dispatcher_cases(image, staged_image, pinned_table(image))
    mutants_spec = [
        ("off-by-one-id-bound", "id >= 31u", "id >= 32u",
         31, bytes(TABLE_BYTES + 8), 0x100, 0, 1),
        ("wrong-table-stride", "id * 8u", "id * 4u",
         5, table_with_row(bytes(TABLE_BYTES), 5, 0, 1), 0x100, 1, 0),
        ("wrong-mode-bit", "mode & 1u", "mode & 2u",
         0, table_with_row(bytes(TABLE_BYTES), 0, 0, 1), 0x101, 0, 1),
        ("inverted-gate", "row[0] != 0u", "row[0] == 0u",
         16, table_with_row(bytes(TABLE_BYTES), 16, 1, 1), 0x101, 0, 1),
    ]
    mutants = []
    for label, old, new, query_id, rows, mode, inactive, active in mutants_spec:
        source_text = CANDIDATE.read_text(encoding="utf-8")
        if old not in source_text:
            raise AssertionError(f"mutant source anchor missing: {old}")
        mutant_source = OUT / f"mutant_{label}.cpp"
        mutant_source.write_text(source_text.replace(old, new, 1), encoding="utf-8")
        _, body, _ = compile_symbol(f"mutant_{label}.o", mutant_source,
                                    "candidate_002c17d4")
        if label == "off-by-one-id-bound":
            expanded = bytearray(rows)
            struct.pack_into("<II", expanded, 31 * 8, 0, 1)
            rows = bytes(expanded)
        gate, mask = struct.unpack_from("<II", rows, query_id * 8) if query_id < 31 else (0, 0)
        original = direct_run(image, query_id, rows, mode, inactive, active)
        observed = direct_run(image, query_id, rows, mode, inactive, active, body)
        expected = 0 if query_id >= 31 or gate != 0 else int(((active if mode & 1 else inactive) & mask) != 0)
        caught = (observed["fault"] is not None or observed["return"] != expected
                  or accesses_by_address(observed["target_access"])
                  != accesses_by_address(original["target_access"]))
        mutants.append({"label": label, "caught": caught, "expected": expected,
                        "original": original, "mutant": observed})

    report = {
        "function": hex(ADDRESS), "pinned_image_sha256": sha(image),
        "candidate_sha256": sha(CANDIDATE.read_bytes()),
        "production_source_sha256": sha(PRODUCTION.read_bytes()),
        "candidate_body_size": len(candidate), "production_body_size": len(production),
        "candidate_relocations": candidate_relocs,
        "production_relocations": production_relocs,
        "slot_size": slot_size, "slot_fits": len(production) <= slot_size,
        "original_slot_sha256": sha(original_slot), "slot_offset": offset,
        "staged_image_sha256": sha(staged_image), "ips_sha256": sha(patch),
        "ips_roundtrip": True, "changed_byte_count": len(changed),
        "arm_interworking": {"calls": interworking, "candidate_entry_even": ADDRESS % 2 == 0,
                             "candidate_call_sites": [x.address for x in decoded if x.mnemonic in ("bl", "blx")],
                             "returns_via_bx_lr": any(x.mnemonic == "bx" and x.op_str == "lr"
                                                      for x in decoded)},
        "direct_cases": direct, "caller_cases": caller, "mutants": mutants,
        "all_direct_pass": all(x["pass"] for x in direct),
        "all_caller_pass": all(x["pass"] for x in caller),
        "all_mutants_caught": all(x["caught"] for x in mutants),
        "limits": ["Static logical IDs do not prove physical controls or natural runtime input.",
                   "The compiler narrows the mode load to one byte because only bit 0 is observed; caller composition uses ordinary aligned RAM, not MMIO.",
                   "The dispatcher mode-2 composition is exercised; the full 0x0029F278 cursor update is not executed.",
                   "The conflict between prior refresh-stride audits remains unresolved; this helper's fixed-address reads are independent of ID."],
    }
    path = OUT / "report.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(path), "body_size": len(production),
                      "direct": len(direct), "direct_pass": report["all_direct_pass"],
                      "caller": len(caller), "caller_pass": report["all_caller_pass"],
                      "mutants_caught": report["all_mutants_caught"]}, indent=2))
    if not report["slot_fits"] or not report["all_direct_pass"] or not report["all_caller_pass"] or not report["all_mutants_caught"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
