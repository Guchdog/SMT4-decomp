"""Private ARM differential for the editable 0x002C615C quotient candidate."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.build_check import find_clang, get_armv6k_flags
from tools.semantic_experiment import arm, require_unicorn, unicorn

TEXT, INJECT, DATA, STACK = 0x00100000, 0x01000000, 0x02000000, 0x08000000
TEXT_SIZE, INJECT_SIZE, DATA_SIZE, STACK_SIZE = 0x00400000, 0x00010000, 0x1000, 0x1000
ENTRY, BODY_SIZE = 0x002C615C, 556
RETURN = INJECT + 0xFFF0
IMAGE = ROOT / "extracted/exefs/code.bin"
SOURCE = ROOT / "experiments/semantic_equivalence/h1_interpolation_divide_candidate.cpp"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
BODY_SHA = "3d7cdf38585407be142951c950b3c44d2ba4d5d860470166cc4d5e4b3a2705b9"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_candidate(output: Path, source: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    clang = find_clang()
    elf = output / "candidate.elf"
    argv = [str(clang), *get_armv6k_flags(ROOT, clang), "-nostdlib", "-fuse-ld=lld",
            "-Wl,-Ttext=0x01000000", "-Wl,-e,candidate_002c615c",
            "-Wl,--build-id=none", "-Wl,--no-undefined", str(source), "-o", str(elf)]
    proc = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
    (output / "compile.json").write_text(json.dumps({
        "argv": argv, "exit_code": proc.returncode, "stdout": proc.stdout,
        "stderr": proc.stderr,
    }, indent=2) + "\n", encoding="utf-8")
    if proc.returncode:
        raise RuntimeError(f"candidate compile failed: {proc.stderr}")

    tool_dir = clang.parent
    objcopy, nm = tool_dir / "llvm-objcopy.exe", tool_dir / "llvm-nm.exe"
    if not objcopy.exists() or not nm.exists():
        raise RuntimeError("llvm-objcopy and llvm-nm are required for private ARM extraction")
    raw = output / "candidate-text.bin"
    subprocess.run([str(objcopy), "--dump-section", f".text={raw}", str(elf)],
                   check=True, capture_output=True, text=True)
    nm_result = subprocess.run([str(nm), "-u", str(elf)], check=True,
                               capture_output=True, text=True)
    undefined = [line.strip() for line in nm_result.stdout.splitlines() if line.strip()]
    if undefined:
        raise RuntimeError(f"candidate has unresolved symbols: {undefined}")
    text = raw.read_bytes()
    if len(text) > INJECT_SIZE:
        raise RuntimeError("candidate text exceeds private mapping")
    nm_all = subprocess.run([str(nm), "-n", str(elf)], check=True,
                            capture_output=True, text=True)
    symbols = {}
    for line in nm_all.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 3:
            symbols[fields[2]] = int(fields[0], 16)
    required_symbols = {"candidate_002c615c", "candidate_002c615c_divmod"}
    if not required_symbols <= symbols.keys():
        raise RuntimeError(f"candidate symbols missing: {sorted(required_symbols - symbols.keys())}")
    return {
        "text": text,
        "offsets": {name: symbols[name] - INJECT for name in required_symbols},
        "elf": elf,
        "meta": {"compiler": str(clang), "argv": argv,
                 "source_sha256": sha(source.read_bytes()),
                 "elf_sha256": sha(elf.read_bytes()), "text_sha256": sha(text),
                 "text_size": len(text),
                 "quotient_entry": hex(symbols["candidate_002c615c"]),
                 "divmod_entry": hex(symbols["candidate_002c615c_divmod"]),
                 "undefined_symbols": undefined},
    }


class Machine:
    def __init__(self, image: bytes, candidate: dict | None):
        require_unicorn()
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.mem_map(TEXT, TEXT_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE | unicorn.UC_PROT_EXEC)
        self.uc.mem_write(TEXT, image)
        self.uc.mem_map(INJECT, INJECT_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE | unicorn.UC_PROT_EXEC)
        if candidate:
            self.uc.mem_write(INJECT, candidate["text"])
        self.uc.mem_map(DATA, DATA_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.uc.mem_map(STACK, STACK_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._hook)

    def _hook(self, uc, pc, _size, _user):
        if pc == RETURN:
            uc.emu_stop()

    def run(self, numerator: int, denominator: int, candidate: dict | None,
            symbol: str = "candidate_002c615c_divmod") -> dict:
        self.uc.mem_write(DATA, bytes([0xA5]) * DATA_SIZE)
        self.uc.mem_write(STACK, bytes([0xCC]) * STACK_SIZE)
        self.uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
        for reg in range(2, 13):
            self.uc.reg_write(getattr(arm, f"UC_ARM_REG_R{reg}"), 0xA5100000 | reg)
        self.uc.reg_write(arm.UC_ARM_REG_R0, numerator & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R1, denominator & 0xFFFFFFFF)
        sp = STACK + 0x800
        self.uc.reg_write(arm.UC_ARM_REG_SP, sp)
        self.uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
        preserved_before = {f"r{i}": self.uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}"))
                            for i in range(4, 12)}
        try:
            begin = ENTRY if candidate is None else INJECT + candidate["offsets"][symbol]
            self.uc.emu_start(begin, 0, count=10000)
            fault = None
        except unicorn.UcError as exc:
            fault = f"pc={self.uc.reg_read(arm.UC_ARM_REG_PC):#x}: {exc}"
        return {
            "fault": fault,
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "r0": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "r1": self.uc.reg_read(arm.UC_ARM_REG_R1),
            "preserved_before": preserved_before,
            "preserved_after": {f"r{i}": self.uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}"))
                                for i in range(4, 12)},
            "sp_before": sp,
            "sp_after": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "data": bytes(self.uc.mem_read(DATA, DATA_SIZE)),
            "stack": bytes(self.uc.mem_read(STACK, STACK_SIZE)),
        }


def u32(value: int) -> int:
    return value & 0xFFFFFFFF


def signed32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def compare_case(image: bytes, candidate: dict, label: str, n: int, d: int,
                 *, require_data_equal: bool = True) -> dict:
    orig = Machine(image, None).run(u32(n), u32(d), None)
    cand = Machine(image, candidate).run(u32(n), u32(d), candidate)
    quotient_only = Machine(image, candidate).run(
        u32(n), u32(d), candidate, "candidate_002c615c")
    errors = []
    if orig["fault"] or cand["fault"]:
        errors.append("fault")
    if orig["pc"] != RETURN or cand["pc"] != RETURN:
        errors.append("did not return to sentinel")
    if orig["r0"] != cand["r0"]:
        errors.append("r0 quotient differs")
    if orig["r1"] != cand["r1"]:
        errors.append("r1 remainder differs")
    if orig["r0"] != quotient_only["r0"]:
        errors.append("quotient-only C wrapper differs")
    if orig["preserved_after"] != orig["preserved_before"]:
        errors.append("original callee-saved state changed")
    if cand["preserved_after"] != cand["preserved_before"]:
        errors.append("candidate callee-saved state changed")
    if orig["preserved_after"] != cand["preserved_after"]:
        errors.append("callee-saved state differs")
    if orig["sp_after"] != orig["sp_before"] or cand["sp_after"] != cand["sp_before"]:
        errors.append("SP not restored")
    if orig["data"] != cand["data"] and require_data_equal:
        errors.append("data memory differs")
    return {
        "label": label, "numerator_bits": hex(u32(n)), "denominator_bits": hex(u32(d)),
        "numerator_signed": signed32(n), "denominator_signed": signed32(d),
        "original_r0": hex(orig["r0"]), "candidate_r0": hex(cand["r0"]),
        "original_r1_remainder": hex(orig["r1"]), "candidate_r1_remainder": hex(cand["r1"]),
        "quotient_wrapper_r0": hex(quotient_only["r0"]),
        "original_fault": orig["fault"], "candidate_fault": cand["fault"],
        "original_stack_changed": orig["stack"] != bytes([0xCC]) * STACK_SIZE,
        "candidate_stack_changed": cand["stack"] != bytes([0xCC]) * STACK_SIZE,
        "original_stack_changed_offsets_from_sp": [i - 0x800 for i, (a, b) in enumerate(zip(
            orig["stack"], bytes([0xCC]) * STACK_SIZE)) if a != b],
        "candidate_stack_changed_offsets_from_sp": [i - 0x800 for i, (a, b) in enumerate(zip(
            cand["stack"], bytes([0xCC]) * STACK_SIZE)) if a != b],
        "stack_equal_after_return": orig["stack"] == cand["stack"],
        "data_equal": orig["data"] == cand["data"],
        "errors": errors, "passed": not errors,
    }


def cases(seed: int, samples: int) -> list[tuple[str, int, int]]:
    result: list[tuple[str, int, int]] = []
    # H1 caller domain: (signed16(a)-signed16(b))*4096 fits signed 32-bit;
    # the interpolation branch is only taken with duration in [1, 65535].
    h1_deltas = [-65535, -32768, -1, 0, 1, 32767, 65535]
    durations = [1, 2, 3, 8, 65535]
    for delta in h1_deltas:
        for duration in durations:
            result.append(("h1-delta-duration", delta * 4096, duration))
    # Directed signed boundaries, quotient 0/1/exact/max-near, and zero
    # divisor hook behavior. Values are bits passed in r0/r1.
    numerators = [0, 1, 2, 3, 0x7FFFFFFF, 0x80000000, 0x80000001,
                  0xFFFFFFFE, 0xFFFFFFFF]
    denominators = [0, 1, 2, 3, 7, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF]
    for n in numerators:
        for d in denominators:
            result.append(("directed-bits", n, d))
    # Signed overflow boundary is defined by the original magnitude algorithm.
    result.extend([("min-div-minus-one", 0x80000000, 0xFFFFFFFF),
                   ("max-div-one", 0x7FFFFFFF, 1),
                   ("signed-max-near", 0x7FFFFFFF, 2),
                   ("quotient-zero", 5, 9),
                   ("exact-quotient", 0x7FFFFFF0, 16)])
    rng = random.Random(seed)
    for i in range(samples):
        n = rng.getrandbits(32)
        d = rng.getrandbits(32) or 1
        result.append((f"seeded-{i}", n, d))
    return result


def run(output: Path, seed: int, samples: int) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    image = IMAGE.read_bytes()
    if sha(image) != IMAGE_SHA:
        raise ValueError("pinned image hash mismatch")
    body = image[ENTRY - TEXT:ENTRY - TEXT + BODY_SIZE]
    if len(body) != BODY_SIZE or sha(body) != BODY_SHA:
        raise ValueError("pinned 0x002C615C body hash mismatch")
    linked = build_candidate(output / "candidate-build", SOURCE)

    rows = []
    for label, n, d in cases(seed, samples):
        rows.append(compare_case(image, linked, label, n, d))
    zero_rows = [row for row in rows if int(row["denominator_bits"], 16) == 0]
    nonzero_rows = [row for row in rows if int(row["denominator_bits"], 16) != 0]

    # A one-bit quotient mutation must fail a known H1-domain case.
    source_text = SOURCE.read_text(encoding="utf-8")
    anchor = "uint32_t quotient = static_cast<uint32_t>(result);"
    if source_text.count(anchor) != 1:
        raise ValueError("wrong-quotient control mutation anchor is not unique")
    mutant_source = output / "wrong_quotient_candidate.cpp"
    mutant_source.write_text(source_text.replace(anchor,
        "uint32_t quotient = static_cast<uint32_t>(result) + 1u;"), encoding="utf-8")
    mutant = build_candidate(output / "wrong-quotient-build", mutant_source)
    mutant_case = compare_case(image, mutant, "wrong-quotient-control", 4096, 2)
    negative = {"name": "quotient-plus-one", "detected": not mutant_case["passed"],
                "source_sha256": mutant["meta"]["source_sha256"],
                "elf_sha256": mutant["meta"]["elf_sha256"],
                "text_sha256": mutant["meta"]["text_sha256"],
                "case": mutant_case}

    report = {
        "task_id": "h1-interpolation-divide-candidate",
        "passed": all(row["passed"] for row in rows) and negative["detected"],
        "reference_sha256": sha(image), "body_sha256": sha(body),
        "body_size": len(body), "entry": hex(ENTRY), "return_boundary": "BX LR at 0x002C6384",
        "candidate": linked["meta"],
        "negative_control": negative,
        "seed": seed, "seeded_cases": samples,
        "caller_domain_case_count": sum(row["label"] == "h1-delta-duration" for row in rows),
        "directed_case_count": sum(row["label"] != "h1-delta-duration" and
                                    not row["label"].startswith("seeded-") for row in rows),
        "nonzero_case_count": len(nonzero_rows), "zero_divisor_case_count": len(zero_rows),
        "case_count": len(rows), "first_mismatch": next((row for row in nonzero_rows if not row["passed"]), None),
        "memory_summary": {
            "data_equal_case_count": sum(row["data_equal"] for row in rows),
            "original_stack_changed_nonzero_case_count": sum(row["original_stack_changed"] for row in nonzero_rows),
            "candidate_stack_changed_nonzero_case_count": sum(row["candidate_stack_changed"] for row in nonzero_rows),
            "original_stack_changed_offsets_from_sp": sorted({offset for row in rows
                for offset in row["original_stack_changed_offsets_from_sp"]}),
            "candidate_stack_changed_offsets_from_sp": sorted({offset for row in rows
                for offset in row["candidate_stack_changed_offsets_from_sp"]}),
            "stack_residue_matches_case_count": sum(row["stack_equal_after_return"] for row in rows),
        },
        "zero_divisor_observation": {
            "original_r0_values": sorted({row["original_r0"] for row in zero_rows}),
            "candidate_r0_values": sorted({row["candidate_r0"] for row in zero_rows}),
            "original_stack_writes_remain_after_return": any(row["original_stack_changed"] for row in zero_rows),
            "candidate_stack_writes_remain_after_return": any(row["candidate_stack_changed"] for row in zero_rows),
            "contract": "Pinned path calls 0x0014E604, which branches to 0x001524EC (BX LR); r0 returns zero and r1 returns the original numerator bits. The original push/pop leaves temporary words in the caller stack image. Candidate matches quotient and remainder; stack residue is outside the quotient/divmod value contract.",
            "cases": zero_rows,
        },
        "cases": rows,
        "evidence": {"compiled": "passed", "arm_differential": "partial_selected_integer_domain",
                     "caller": "static_only", "runtime": "not_run"},
        "limitations": [
            "The divmod entry returns a uint64_t pair: quotient in r0 and signed remainder in r1, matching the observed output words. The C-callable quotient projection exposes r0 for callers that ignore r1; scratch registers and flags remain unspecified.",
            "Zero divisor returns r0=0 and preserves the numerator bits in r1 through 0x0014E604 -> 0x001524EC. The original also leaves temporary words in its restored stack area; the candidate models the two result words, not that incidental stack residue.",
            "The optimized C++ candidate saves/spills caller-saved or callee-saved temporaries into its restored stack frame; 359 nonzero runs leave stack residue while the pinned original has no nonzero stack residue. SP and callee-saved registers restore, and the caller may not rely on values below the current SP under AAPCS. The report records rather than equates these bytes.",
            "H1 domain is signed 16-bit coordinate delta times 4096 divided by a nonzero u16 duration. The broader directed/random cases cover signed bit patterns, but finite testing is not a formal proof.",
            "Caller analysis is static; no H1 boot/gameplay, scene lifecycle, production integration, MMIO, concurrency, or interrupt behavior was tested.",
        ],
    }
    report_path = output / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=256)
    parser.add_argument("--seed", type=int, default=20261025)
    args = parser.parse_args()
    if args.samples < 0:
        parser.error("--samples must be nonnegative")
    report = run(args.output, args.seed, args.samples)
    print(f"0x002C615C differential: {'PASS' if report['passed'] else 'FAIL'} "
          f"{report['nonzero_case_count']} nonzero cases; "
          f"zero observations={report['zero_divisor_case_count']}; report={args.output/'report.json'}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
