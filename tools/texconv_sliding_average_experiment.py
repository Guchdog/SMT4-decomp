"""Differential validation for the dormant TexConv sliding-average helper."""
from __future__ import annotations

import argparse
import csv
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

import capstone
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang, get_armv6k_flags
from tools.semantic_experiment import (
    DATA, STACK, STACK_SIZE, SP, TEXT, Case, Execution,
)

try:
    import unicorn
    from unicorn import arm_const as arm
except ImportError:
    unicorn = None
    arm = None

TEXT_SIZE = 0x00400000
TEXT_BASE = 0x01200000
DATA_SIZE = 0x8000
RETURN = 0x011FF000
FUNCTIONS = {
    0x001721E4: {"size": 136, "stride": 0x400},
    0x001787E4: {"size": 136, "stride": 0x100},
    0x0017EDE4: {"size": 136, "stride": 0x200},
}
SOURCE_OFFSET = 0x100
DESTINATION_OFFSET = 0x4000
U32_MASK = 0xFFFFFFFF
REQUIRED_SYMBOLS = {
    *(f"candidate_{address:08x}" for address in FUNCTIONS),
    "negative_wrong_stride_100",
    "negative_row_copy_instead_of_average",
}


def require_unicorn() -> None:
    if unicorn is None:
        raise RuntimeError(
            "Install optional experiment dependencies with pip install -r requirements-experiment.txt"
        )


def _linked_text_and_symbols(path: Path) -> tuple[int, bytes, dict[str, tuple[int, int]]]:
    """Read the linked ELF's executable section and symbol locations."""
    blob = Path(path).read_bytes()
    if len(blob) < 52 or blob[:4] != b"\x7fELF" or blob[4] != 1 or blob[5] != 1:
        raise ValueError("Expected a little-endian ELF32 executable")
    header = struct.unpack_from("<16sHHIIIIIHHHHHH", blob, 0)
    _, _, machine, _, _, _, section_offset, _, _, _, _, section_size, section_count, names_index = header
    if machine != 40 or section_size != 40 or section_count == 0:
        raise ValueError("Expected ARM ELF32 with a complete section table")
    sections = [
        struct.unpack_from("<IIIIIIIIII", blob, section_offset + index * section_size)
        for index in range(section_count)
    ]
    if names_index >= len(sections):
        raise ValueError("Invalid section-name string table index")
    names_section = sections[names_index]
    section_names = blob[names_section[4]:names_section[4] + names_section[5]]

    def cstring(table: bytes, offset: int) -> str:
        if offset < 0 or offset >= len(table):
            return ""
        end = table.find(b"\0", offset)
        return table[offset:end if end >= 0 else len(table)].decode("ascii", errors="replace")

    text_index = next(
        (i for i, item in enumerate(sections) if cstring(section_names, item[0]) == ".text"),
        None,
    )
    if text_index is None:
        raise ValueError("Linked candidate has no .text section")
    text_section = sections[text_index]
    if not (text_section[2] & 0x4) or text_section[5] == 0:
        raise ValueError("Linked .text is not a non-empty executable section")
    text_base = text_section[3]
    text = blob[text_section[4]:text_section[4] + text_section[5]]

    symbols: dict[str, tuple[int, int]] = {}
    for section in sections:
        if section[1] != 2:  # SHT_SYMTAB
            continue
        if section[6] >= len(sections):
            raise ValueError("Invalid symbol string table link")
        strings_section = sections[section[6]]
        strings = blob[strings_section[4]:strings_section[4] + strings_section[5]]
        entry_size = section[9] or 16
        if entry_size < 16:
            raise ValueError("Invalid ELF32 symbol size")
        for index in range(section[5] // entry_size):
            name_offset, value, size, info, _, target_section = struct.unpack_from(
                "<IIIBBH", blob, section[4] + index * entry_size
            )
            name = cstring(strings, name_offset)
            if name and target_section == text_index and info & 0x0F == 2:
                symbols[name] = (value & ~1, size)
    missing = REQUIRED_SYMBOLS - symbols.keys()
    if missing:
        raise ValueError(f"Linked candidate lacks required symbols: {sorted(missing)}")
    for name in REQUIRED_SYMBOLS:
        start, size = symbols[name]
        if size <= 0 or start < text_base or start + size > text_base + len(text):
            raise ValueError(f"Candidate symbol outside linked .text: {name}")
    return text_base, text, symbols


def _instructions(image: bytes, address: int, size: int) -> tuple[tuple[str, str], ...]:
    offset = address - TEXT
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoded = list(decoder.disasm(image[offset:offset + size], address))
    if sum(item.size for item in decoded) != size:
        raise ValueError(f"Incomplete ARM decode at {address:#010x}")
    result = []
    for item in decoded:
        operands = item.op_str.lower()
        if item.mnemonic.lower() in {"b", "bne", "beq", "bl"} and operands.startswith("#0x"):
            target = int(operands[1:], 16)
            operands = f"#rel:{target - item.address:+x}"
        result.append((item.mnemonic.lower(), operands))
    return tuple(result)


def verify_reference(image: bytes, expected_hash: str, ledger: list[dict[str, str]]) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if digest != expected_hash:
        raise ValueError("code.bin SHA-256 does not match the pinned game revision")
    by_address = {int(row["address"], 16): row for row in ledger}
    shapes: dict[int, tuple[tuple[str, str], ...]] = {}
    rows = {}
    for address, spec in FUNCTIONS.items():
        row = by_address.get(address)
        if (row is None or row["status"].strip() != "matching"
                or int(row["size"]) != spec["size"]):
            raise ValueError(f"Missing matching {spec['size']}-byte ledger row at {address:#010x}")
        instructions = _instructions(image, address, spec["size"])
        stride = spec["stride"]
        normalized = tuple(
            (mnemonic, operands.replace(f"#0x{stride:x}", "#STRIDE"))
            for mnemonic, operands in instructions
        )
        shapes[address] = normalized
        digest_fn = hashlib.sha256(image[address - TEXT:address - TEXT + spec["size"]]).hexdigest()
        rows[hex(address)] = {
            "size": spec["size"], "stride": hex(stride), "ledger_name": row["name"],
            "category": row["category"], "sha256": digest_fn,
            "instructions": [f"{mnemonic} {operands}".strip() for mnemonic, operands in instructions],
        }
    if len(set(shapes.values())) != 1:
        raise ValueError("The three ARM bodies are not the same after normalizing stride immediates")
    for address, spec in FUNCTIONS.items():
        instrs = shapes[address]
        if instrs[-1] != ("mov", "pc, lr"):
            raise ValueError(f"Expected an AAPCS return at {address:#010x}")
        if not any("ldr ip, [pc, #-0x838]" == f"{mnemonic} {operands}" for mnemonic, operands in instrs):
            raise ValueError(f"Missing packed-channel mask literal load at {address:#010x}")
        mask_address = address - 0x830
        mask_offset = mask_address - TEXT
        if struct.unpack_from("<I", image, mask_offset)[0] != 0x7F7F7F7F:
            raise ValueError(f"Packed-channel mask literal changed at {mask_address:#010x}")
    return {"code_sha256": digest, "functions": rows,
            "normalized_instruction_count": len(next(iter(shapes.values())))}


def audit_existing_cpp_source() -> dict:
    """Establish whether the existing helper is live code or an isolated draft."""
    source_path = ROOT / "src/engine/tex_convert.cpp"
    source = source_path.read_text(encoding="utf-8")
    source_files = list((ROOT / "src").rglob("*.cpp")) + list((ROOT / "include").rglob("*.h"))
    occurrences = sum(
        len(re.findall(r"\bTexConv_001721e4\s*\(", path.read_text(encoding="utf-8")))
        for path in source_files
    )
    definition = re.search(
        r"\[\[maybe_unused\]\]\s+static\s+void\s+TexConv_001721e4\s*\(",
        source,
    )
    if occurrences != 1 or definition is None:
        raise ValueError(
            "Expected exactly one maybe_unused static definition and no production callsites"
        )
    signature = source[definition.start():source.find("\n}", definition.start()) + 2]
    if ("const u8*& src" not in signature or "u8*& dst" not in signature
            or "u32 stride" not in signature or "src = s;" not in signature
            or "dst = d;" not in signature):
        raise ValueError("Existing C++ helper no longer has the expected pointer-reference/stride contract")
    return {
        "source": "src/engine/tex_convert.cpp",
        "status": "dormant-static-cpp-draft",
        "maybe_unused_static_definition_count": 1,
        "source_occurrence_count": occurrences,
        "production_callsite_found": False,
        "clone_adaptation": "same helper called with per-clone stride 0x400, 0x100, or 0x200",
    }


def _case(address: int, count: int, label: str, seed: int, pattern: str = "random") -> Case:
    if count <= 0:
        raise ValueError("The ARM routine is a do-while converter; count must be positive")
    stride = FUNCTIONS[address]["stride"]
    if SOURCE_OFFSET + (count + 1) * stride + 8 >= DATA_SIZE:
        raise ValueError("Source rows do not fit in the mapped data region")
    if DESTINATION_OFFSET + count * stride + 4 >= DATA_SIZE:
        raise ValueError("Destination rows do not fit in the mapped data region")
    rng = random.Random(seed ^ address ^ sum((i + 1) * ord(ch) for i, ch in enumerate(label)))
    data = bytearray(rng.randbytes(DATA_SIZE))
    if pattern == "zero":
        data[:] = bytes(DATA_SIZE)
    elif pattern == "high-low-boundaries":
        data[:] = bytes(DATA_SIZE)
        words = (0x00000000, 0xFFFFFFFF, 0x80808080, 0x7F7F7F7F,
                 0x01020304, 0xFEFDFCFB, 0x80000001, 0x01010101)
        for row in range(count + 1):
            struct.pack_into("<I", data, SOURCE_OFFSET + row * stride,
                             words[row % len(words)])
            data[SOURCE_OFFSET + row * stride + 4] = (row * 0x3D + 0xFF) & 0xFF
    regs = [rng.getrandbits(32) for _ in range(13)]
    regs[0] = DATA + SOURCE_OFFSET
    regs[1] = DATA + DESTINATION_OFFSET
    regs[2] = count
    return Case(label, tuple(regs), bytes(data), rng.randbytes(STACK_SIZE), rng.getrandbits(4) << 28)


def _projected_output_difference(original: Execution, candidate: Execution) -> str | None:
    """Compare output/memory under a projected contract, not full equivalence."""
    for label, result in (("original", original), ("candidate", candidate)):
        if result.fault:
            return f"{label} fault: {result.fault}"
        if not result.stopped:
            return f"{label} did not reach the return sentinel"
    if original.pc != candidate.pc:
        return "return continuation differs"
    # The pinned original overwrites r7 and r9 (SB) without saving them. All
    # other AAPCS-preserved GPRs, SP, and d8-d15 must match.
    ignored_preserved_indices = {3, 5}
    for index, (actual, expected) in enumerate(
        zip(candidate.preserved, candidate.expected_preserved)
    ):
        if actual != expected:
            return f"candidate violates callee-save contract at tuple index {index}"
    for index, (left, right) in enumerate(zip(original.preserved, candidate.preserved)):
        if index in ignored_preserved_indices:
            continue
        if left != right:
            return f"preserved state differs at tuple index {index}"
    if original.data != candidate.data:
        return "data memory differs"
    if original.live_stack != candidate.live_stack:
        return "caller-visible stack memory differs"
    if original.reads != candidate.reads:
        return "observable read footprint differs"
    if original.writes != candidate.writes:
        return "observable write footprint differs"
    return None


class LinkedTexConvRunner:
    """Execute original ARM code and linked experiment code in one ARM machine."""
    def __init__(self, image: bytes, text_base: int, linked_text: bytes):
        require_unicorn()
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.mem_map(TEXT, TEXT_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
        self.uc.mem_write(TEXT, image)
        mapped_size = (len(linked_text) + 0xFFF) & ~0xFFF
        self.uc.mem_map(text_base, mapped_size, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
        self.uc.mem_write(text_base, linked_text)
        self.uc.mem_map(RETURN, 0x1000, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
        self.uc.mem_map(DATA, DATA_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.uc.mem_map(STACK, STACK_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.reg_ids = tuple(getattr(arm, f"UC_ARM_REG_R{i}") for i in range(13))
        self.d_ids = tuple(getattr(arm, f"UC_ARM_REG_D{i}") for i in range(8, 16))
        self.reads: set[int] = set()
        self.writes: set[int] = set()
        self.stopped = False
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._instruction)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_READ | unicorn.UC_HOOK_MEM_WRITE, self._memory)

    def _instruction(self, uc, address, _size, _user_data):
        if address == RETURN:
            self.stopped = True
            uc.emu_stop()

    def _memory(self, _uc, access, address, size, _value, _user_data):
        target = self.writes if access == unicorn.UC_MEM_WRITE else self.reads
        if DATA <= address < DATA + DATA_SIZE:
            target.update(range(address, min(address + size, DATA + DATA_SIZE)))
        elif SP <= address < STACK + STACK_SIZE:
            target.update(range(address, min(address + size, STACK + STACK_SIZE)))

    def run(self, start: int, case: Case, *, budget: int = 50000) -> Execution:
        uc = self.uc
        uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10 | case.nzcv)
        for reg_id, value in zip(self.reg_ids, case.registers):
            uc.reg_write(reg_id, value)
        expected_d = tuple(((case.registers[4] << 32) | case.registers[5]) ^ i for i in range(8))
        for reg_id, value in zip(self.d_ids, expected_d):
            uc.reg_write(reg_id, value)
        uc.reg_write(arm.UC_ARM_REG_SP, SP)
        uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
        uc.mem_write(DATA, case.data)
        uc.mem_write(STACK, case.stack)
        self.reads.clear()
        self.writes.clear()
        self.stopped = False
        fault = None
        try:
            uc.emu_start(start, 0, count=budget)
        except unicorn.UcError as error:
            fault = str(error)
        preserved = tuple(uc.reg_read(reg_id) for reg_id in self.reg_ids[4:12])
        preserved += (uc.reg_read(arm.UC_ARM_REG_SP),)
        preserved += tuple(uc.reg_read(reg_id) for reg_id in self.d_ids)
        return Execution(
            self.stopped, fault, uc.reg_read(arm.UC_ARM_REG_R0),
            uc.reg_read(arm.UC_ARM_REG_PC), uc.reg_read(arm.UC_ARM_REG_CPSR) & 0xF0000000,
            preserved, case.registers[4:12] + (SP,) + expected_d,
            bytes(uc.mem_read(DATA, DATA_SIZE)), bytes(uc.mem_read(SP, STACK_SIZE // 2)),
            frozenset(self.reads), frozenset(self.writes),
        )


def _link_candidate(source: Path, output: Path) -> tuple[int, bytes, dict[str, tuple[int, int]]]:
    ROOT = Path(__file__).resolve().parents[1]
    object_path = output.with_suffix(".o")
    build = compile_tu_armv6k(source, object_path, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr or "ARMv6K candidate compilation failed")
    funcs = extract_elf_functions_detailed(object_path)
    missing = REQUIRED_SYMBOLS - funcs.keys()
    if missing:
        raise ValueError(f"Candidate object is missing symbols: {sorted(missing)}")
    # All calls, including the existing helper and the local freestanding memcpy,
    # are resolved into a small fixed-address image for Unicorn execution.
    command = [
        str(find_clang()), *get_armv6k_flags(ROOT), "-nostdlib",
        f"-Wl,-Ttext={TEXT_BASE:#x}",
        "-Wl,--entry=candidate_001721e4", str(object_path), "-o", str(output),
    ]
    linked = subprocess.run(command, capture_output=True, text=True)
    if linked.returncode:
        raise RuntimeError(linked.stderr or "Could not link isolated ARM candidate image")
    return _linked_text_and_symbols(output)


def run(code_path: Path, output: Path, *, samples: int = 16,
        seed: int = 20261024) -> dict:
    if samples < 0:
        raise ValueError("samples must be non-negative")
    image = Path(code_path).read_bytes()
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
        ledger = list(csv.DictReader(stream))
    reference = verify_reference(image, game["code_sha256"], ledger)
    cpp_status = audit_existing_cpp_source()
    source_path = ROOT / "experiments/semantic_equivalence/texconv_sliding_average_candidates.cpp"
    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    text_base, text, symbols = _link_candidate(source_path, output / "texconv_sliding_average.elf")
    runner = LinkedTexConvRunner(image, text_base, text)

    results = []
    for address in FUNCTIONS:
        candidate_address, _ = symbols[f"candidate_{address:08x}"]
        original_cases = []
        for label, count, pattern in (
            ("one-row-boundary", 1, "high-low-boundaries"),
            ("two-row-even", 2, "high-low-boundaries"),
            ("three-row-odd", 3, "high-low-boundaries"),
            ("five-row", 5, "random"),
            ("all-zero", 3, "zero"),
        ):
            original_cases.append(_case(address, count, label, seed, pattern))
        rng = random.Random(seed ^ address)
        for index in range(samples):
            count = 1 + (index % 8)
            original_cases.append(_case(address, count, f"random-{index}",
                                        rng.getrandbits(32), "random"))
        failures = []
        comparisons = 0
        abi_observation = None
        for case in original_cases:
            left = runner.run(address, case)
            right = runner.run(candidate_address, case)
            comparisons += 1
            if abi_observation is None:
                preserved_names = ["r4", "r5", "r6", "r7", "r8", "r9", "r10", "r11", "sp"] + [
                    f"d{index}" for index in range(8, 16)
                ]
                abi_observation = {
                    "original_registers_changed_from_entry": [
                        name for name, actual, expected in zip(
                            preserved_names, left.preserved, left.expected_preserved
                        ) if actual != expected
                    ],
                    "candidate_registers_changed_from_entry": [
                        name for name, actual, expected in zip(
                            preserved_names, right.preserved, right.expected_preserved
                        ) if actual != expected
                    ],
                    "interpretation": "The original overwrites r7 and r9/SB; candidate must preserve all AAPCS callee-saved state. No caller window is claimed.",
                }
            reason = _projected_output_difference(left, right)
            if reason:
                failures.append({"case": case.label, "reason": reason})
                break
        results.append({"address": hex(address), "stride": hex(FUNCTIONS[address]["stride"]),
                        "candidate_symbol": f"candidate_{address:08x}",
                        "candidate_size": symbols[f"candidate_{address:08x}"][1],
                        "comparisons": comparisons, "abi_observation": abi_observation,
                        "projected_output_memory_passed": not failures,
                        "failure": failures[0] if failures else None})

    control_case = _case(0x001787E4, 3, "negative-controls", seed, "high-low-boundaries")
    clone_runner = lambda symbol: runner.run(symbol, control_case)
    original = clone_runner(0x001787E4)
    controls = []
    for name in ("negative_wrong_stride_100", "negative_row_copy_instead_of_average"):
        candidate, _ = symbols[name]
        result = clone_runner(candidate)
        reason = _projected_output_difference(original, result)
        controls.append({"name": name, "detected": reason is not None, "reason": reason})

    if hashlib.sha256(source_path.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("Candidate source changed during the experiment")
    return {
        "schema": 1,
        "experiment": "texconv_sliding_average_three_clone_family",
        "status": "projected-output-parity-pass; full-equivalence-blocked-on-ABI-and-caller-evidence",
        "output_parity_passed": all(item["projected_output_memory_passed"] for item in results),
        "abi_compatible": False,
        "full_equivalence_passed": False,
        "code_sha256": reference["code_sha256"],
        "reference": reference,
        "existing_cpp_source": cpp_status,
        "linked_candidate_text": {"base": hex(text_base), "size": len(text)},
        "source_sha256": source_hash,
        "functions": results,
        "negative_controls": controls,
        "scenarios": ["count=1,2,3,5 boundaries", "all-zero source", f"{samples} seeded random cases per clone (counts 1..8)"],
        "limits": [
            "The existing helper is static and currently has no production callers; this is isolated validation, not production activation.",
            "Only disjoint, aligned ordinary RAM buffers are covered; invalid count=0 is rejected because the original is a do-while routine.",
            "No verified direct callers or indirect dispatch table windows are claimed.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=Path("extracted/exefs/code.bin"))
    parser.add_argument("--output", type=Path, default=Path("build/semantic-equivalence/texconv-sliding-average"))
    parser.add_argument("--samples", type=int, default=16)
    parser.add_argument("--seed", type=int, default=20261024)
    args = parser.parse_args()
    report = run(args.code, args.output, samples=args.samples, seed=args.seed)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not (report["output_parity_passed"] and all(
        item["detected"] for item in report["negative_controls"]
    )):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
