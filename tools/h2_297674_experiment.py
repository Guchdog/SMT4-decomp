"""Offline differential for the raw 32-bit H2 getter at 0x00297674."""
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
from tools.h2_calc_experiment import (
    DATA, RETURN, SP, CalcMachine, Scenario,
    U32,
)
from tools.h2_calc_code_patch import apply_ips, encode_ips
from tools.semantic_experiment import arm_branch

IMAGE = ROOT / "extracted/exefs/code.bin"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
PRODUCTION = ROOT / "src/engine/leaf_batch21_b.cpp"
CANDIDATE = ROOT / "experiments/semantic_equivalence/h2_297674_candidate.cpp"
OUT = ROOT / "build/agent-work/H2-semantic/h2-titleconfig-00297674-convert/run001"
ADDRESS = 0x00297674
TEXT_BASE = 0x00100000
GLOBAL_SLOT = 0x0043E190
OBJECT = DATA + 0x2000
INJECT = 0x01000000
GETTER_VALUES = (0, 1, 2, 0xFF, 0x100, 0x80000000, U32)


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
                     "symbol": reloc.symbol_name, "addend": hex(old),
                     "value": hex((old + INJECT) & U32)})
    return obj, bytes(fixed), rows


class GetterMachine(CalcMachine):
    def __init__(self, image: bytes, scenario: Scenario, candidate: bytes | None,
                 patch_entry: bool):
        self.getter_entries: list[int] = []
        self.getter_memory: list[tuple[str, int, int]] = []
        self.sprite_animation_calls: list[tuple[int, int, int]] = []
        super().__init__(image, entry_code=None, scenario=scenario)
        self.uc.mem_write(GLOBAL_SLOT, struct.pack("<I", OBJECT))
        if candidate is not None:
            self.uc.mem_write(INJECT, candidate)
            if patch_entry:
                self.uc.mem_write(ADDRESS, arm_branch(ADDRESS, INJECT))
        self.uc.hook_add(unicorn.UC_HOOK_MEM_READ, self._getter_read)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._getter_write)

    def _getter_read(self, uc, access, address, size, value, _):
        if address == GLOBAL_SLOT or OBJECT <= address < OBJECT + 0x40:
            self.getter_memory.append(("read", address, size))

    def _getter_write(self, uc, access, address, size, value, _):
        if address == GLOBAL_SLOT or OBJECT <= address < OBJECT + 0x40:
            self.getter_memory.append(("write", address, size))

    def _code(self, uc, address, size, user_data):
        if address == ADDRESS:
            self.getter_entries.append(uc.reg_read(arm.UC_ARM_REG_LR) - 4)
            # Let the pinned original body or the slot trampoline execute.
            return
        if address == 0x002BDAC0:
            self.sprite_animation_calls.append(tuple(
                uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(3)))
            # Execute the pinned original helper instead of the Calc harness stub.
            return
        return super()._code(uc, address, size, user_data)


def init_global(machine: GetterMachine, value: int, pointer: int = OBJECT):
    machine.uc.mem_write(GLOBAL_SLOT, struct.pack("<I", pointer & U32))
    if pointer == OBJECT:
        machine.uc.mem_write(OBJECT + 0x1C, struct.pack("<I", value & U32))
        machine.uc.mem_write(OBJECT + 0x20, struct.pack("<I", 0x13572468))


def direct_run(image: bytes, value: int, candidate: bytes | None) -> dict:
    machine = GetterMachine(image, Scenario("direct", 2), candidate, patch_entry=False)
    init_global(machine, value)
    machine.getter_entries.clear(); machine.getter_memory.clear()
    entry = INJECT if candidate is not None else ADDRESS
    regs = tuple(getattr(arm, f"UC_ARM_REG_R{i}") for i in range(13))
    before = tuple((0xA5010000 + i * 0x01010101) & U32 for i in range(13))
    for reg, val in zip(regs, before):
        machine.uc.reg_write(reg, val)
    machine.uc.reg_write(arm.UC_ARM_REG_SP, SP)
    machine.uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
    machine.uc.reg_write(arm.UC_ARM_REG_CPSR, 0x60000010)
    expected_sp = machine.uc.reg_read(arm.UC_ARM_REG_SP)
    expected_lr = machine.uc.reg_read(arm.UC_ARM_REG_LR)
    expected_cpsr = machine.uc.reg_read(arm.UC_ARM_REG_CPSR)
    machine.trace.clear(); machine.reads.clear(); machine.writes.clear()
    machine.getter_entries.clear(); machine.getter_memory.clear()
    fault = None
    try:
        machine.uc.emu_start(entry, 0, count=10000)
    except unicorn.UcError as exc:
        fault = str(exc)
    after = tuple(machine.uc.reg_read(reg) for reg in regs)
    reads = [x for x in machine.getter_memory if x[0] == "read"]
    writes = [x for x in machine.getter_memory if x[0] == "write"]
    return {
        "fault": fault, "r0": machine.uc.reg_read(arm.UC_ARM_REG_R0),
        "expected": value & U32, "r1_r12_preserved": after[1:] == before[1:],
        "sp": machine.uc.reg_read(arm.UC_ARM_REG_SP),
        "abi_preserved": (tuple(after[4:12]) == tuple(before[4:12])
                          and machine.uc.reg_read(arm.UC_ARM_REG_SP) == expected_sp
                          and machine.uc.reg_read(arm.UC_ARM_REG_LR) == expected_lr),
        "flags_preserved": machine.uc.reg_read(arm.UC_ARM_REG_CPSR) == expected_cpsr,
        "read_trace": reads, "write_trace": writes,
        "expected_read_trace": [("read", GLOBAL_SLOT, 4), ("read", OBJECT + 0x1C, 4)],
    }


def caller_run(image: bytes, getter_value: int, prior: int) -> dict:
    scenario = Scenario(f"state2-{getter_value:08x}-prior-{prior}", 2,
                        script_runner=prior)
    machine = GetterMachine(image, scenario, None, patch_entry=False)
    init_global(machine, getter_value)
    machine.getter_entries.clear(); machine.getter_memory.clear()
    result = machine.run()
    result["getter_entries"] = list(machine.getter_entries)
    result["getter_memory"] = list(machine.getter_memory)
    result["sprite_animation_calls"] = list(machine.sprite_animation_calls)
    result["global_slot"] = GLOBAL_SLOT
    result["getter_object"] = OBJECT
    return result


def summary(result: dict) -> dict:
    keys = ("stopped", "fault", "return", "pc", "preserved", "expected_preserved",
            "work", "config", "trace", "getter_entries", "getter_memory",
            "sprite_animation_calls")
    values = {key: result.get(key) for key in keys}
    for key in ("work", "config"):
        if values.get(key) is not None:
            values[key] = values[key].hex()
    return values


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    image = IMAGE.read_bytes()
    if sha(image) != IMAGE_SHA:
        raise AssertionError("pinned original image hash changed")
    _, candidate, candidate_relocs = compile_symbol(
        "candidate.o", CANDIDATE, "candidate_00297674")
    _, production, production_relocs = compile_symbol(
        "production.o", PRODUCTION, "script_vm_func_00297674")
    if candidate != production:
        raise AssertionError("candidate and production bodies differ")

    slot_offset = ADDRESS - TEXT_BASE
    original_slot = image[slot_offset:slot_offset + 20]
    if len(original_slot) != 20:
        raise AssertionError("original slot is truncated")
    staged_mutable = bytearray(image)
    staged_mutable[slot_offset:slot_offset + 20] = production
    staged_image = bytes(staged_mutable)
    patch = encode_ips([(slot_offset, production)], len(image))
    if apply_ips(image, patch) != staged_image:
        raise AssertionError("slot-only IPS roundtrip failed")
    changed = [i for i, (old, new) in enumerate(zip(image, staged_image)) if old != new]
    if changed and (min(changed) < slot_offset or max(changed) >= slot_offset + 20):
        raise AssertionError("staged changes escaped the declared 20-byte slot")
    caller_pc = 0x001EAFAC
    caller_word = struct.unpack_from("<I", image, caller_pc - TEXT_BASE)[0]
    if caller_word >> 24 != 0xEB:
        raise AssertionError(f"expected original ARM BL at caller {caller_pc:#x}")
    branch_delta = (caller_word & 0x00FFFFFF) << 2
    if branch_delta & 0x02000000:
        branch_delta -= 0x04000000
    branch_target = caller_pc + 8 + branch_delta
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoded_candidate = list(decoder.disasm(production, ADDRESS))
    interworking = {
        "caller_pc": hex(caller_pc), "caller_instruction": hex(caller_word),
        "caller_branch_target": hex(branch_target), "target_even_arm_entry": branch_target == ADDRESS
        and (branch_target & 1) == 0,
        "candidate_entry_even": (ADDRESS & 1) == 0,
        "candidate_call_instructions": [
            {"address": hex(ins.address), "mnemonic": ins.mnemonic, "operands": ins.op_str}
            for ins in decoded_candidate if ins.mnemonic in ("bl", "blx")],
        "candidate_return_is_bx_lr": bool(decoded_candidate)
        and decoded_candidate[-2].mnemonic == "bx"
        and decoded_candidate[-2].op_str == "lr",
    }
    if not interworking["target_even_arm_entry"] or not interworking["candidate_entry_even"]:
        raise AssertionError("ARM/Thumb interworking audit failed")

    direct = []
    for value in GETTER_VALUES:
        original = direct_run(image, value, None)
        compiled = direct_run(image, value, candidate)
        direct.append({"value": hex(value), "original": original,
                       "candidate": compiled,
                       "pass": original["fault"] is None and compiled["fault"] is None
                       and original["r0"] == compiled["r0"] == (value & U32)
                       and original["read_trace"] == compiled["read_trace"]
                       and original["write_trace"] == compiled["write_trace"] == []
                       and original["r1_r12_preserved"]
                       and compiled["r1_r12_preserved"]
                       and original["abi_preserved"] and compiled["abi_preserved"]
                       and original["flags_preserved"] and compiled["flags_preserved"]})

    null_original = GetterMachine(image, Scenario("null-pointer-original", 2), None, False)
    null_candidate = GetterMachine(image, Scenario("null-pointer-candidate", 2), candidate, False)
    init_global(null_original, 0, pointer=0)
    init_global(null_candidate, 0, pointer=0)
    null_original.getter_memory.clear(); null_candidate.getter_memory.clear()
    null_original.uc.reg_write(arm.UC_ARM_REG_SP, SP)
    null_candidate.uc.reg_write(arm.UC_ARM_REG_SP, SP)
    null_original.uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
    null_candidate.uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
    null_faults = []
    for machine, entry in ((null_original, ADDRESS), (null_candidate, INJECT)):
        try:
            machine.uc.emu_start(entry, 0, count=100)
            null_faults.append(None)
        except unicorn.UcError as exc:
            null_faults.append(str(exc))
    null_case = {"original_fault": null_faults[0], "candidate_fault": null_faults[1],
                 "same_fault_presence": (null_faults[0] is None) == (null_faults[1] is None),
                 "original_reads": null_original.getter_memory,
                 "candidate_reads": null_candidate.getter_memory}

    caller = []
    for prior in (0, 1, 2, U32):
        for value in GETTER_VALUES:
            original = caller_run(image, value, prior)
            compiled = caller_run(staged_image, value, prior)
            compare_keys = ("fault", "stopped", "return", "pc", "preserved",
                            "expected_preserved", "work", "config", "trace",
                            "getter_entries", "getter_memory", "sprite_animation_calls")
            equal = all(original.get(k) == compiled.get(k) for k in compare_keys)
            caller.append({"prior_script_runner": prior, "getter_value": hex(value),
                           "original": summary(original), "candidate": summary(compiled),
                           "pass": equal and original.get("fault") is None
                           and original.get("stopped")
                           and (len(original["getter_entries"]) == (1 if prior == 2 else 0))})

    mutant_specs = [
        ("wrong-pointer-slot", 0x80000000,
         lambda code: struct.pack_into("<I", code, 16, GLOBAL_SLOT + 4)),
        ("wrong-field-offset", 0x11223344,
         lambda code: struct.pack_into("<I", code, 8, 0xE5900020)),
        ("byte-return-truncation", 0x80000000,
         lambda code: struct.pack_into("<I", code, 8, 0xE5D0001C)),
    ]
    mutants = []
    for label, value, mutate in mutant_specs:
        mutated = bytearray(candidate)
        mutate(mutated)
        observed = direct_run(image, value, bytes(mutated))
        caught = (observed["fault"] is not None or observed["r0"] != (value & U32)
                  or observed["read_trace"] != observed["expected_read_trace"])
        mutants.append({"label": label, "input": hex(value), "caught": caught,
                        "observed": observed})

    report = {
        "function": hex(ADDRESS), "pinned_image_sha256": sha(image),
        "candidate_sha256": sha(CANDIDATE.read_bytes()),
        "production_source_sha256": sha(PRODUCTION.read_bytes()),
        "candidate_body_size": len(candidate), "production_body_size": len(production),
        "original_slot_hex": original_slot.hex(), "production_slot_hex": production.hex(),
        "slot_offset": slot_offset, "ips_sha256": sha(patch),
        "staged_image_sha256": sha(staged_image), "ips_roundtrip": True,
        "changed_byte_count": len(changed),
        "arm_interworking": interworking,
        "candidate_relocations": candidate_relocs,
        "production_relocations": production_relocs,
        "slot_size": 20, "slot_fits": len(production) <= 20,
        "direct_cases": direct, "caller_cases": caller, "mutants": mutants,
        "null_pointer_case": null_case,
        "all_direct_pass": all(x["pass"] for x in direct),
        "all_caller_pass": all(x["pass"] for x in caller),
        "all_mutants_caught": all(x["caught"] for x in mutants),
        "limits": ["synthetic global pointer/object values",
                   "0x0019DFBC return values are modeled by the existing Calc harness",
                   "original 0x002BDAC0 executes when getter returns zero; its nested dependencies use Calc harness boundaries",
                   "no Azahar runtime, object lifetime, concurrent writer, or persistence claim"],
    }
    report_path = OUT / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(report_path), "body_size": len(production),
                      "slot_fits": report["slot_fits"],
                      "all_direct_pass": report["all_direct_pass"],
                      "all_caller_pass": report["all_caller_pass"],
                      "all_mutants_caught": report["all_mutants_caught"],
                      "null_pointer_same_fault_presence": null_case["same_fault_presence"]}, indent=2))
    if (not report["slot_fits"] or not report["all_direct_pass"]
            or not report["all_caller_pass"] or not report["all_mutants_caught"]
            or not null_case["same_fault_presence"]
            or null_faults[0] is None or null_faults[1] is None):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
