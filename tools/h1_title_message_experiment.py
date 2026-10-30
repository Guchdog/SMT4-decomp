"""Bounded original-ARM differential for the H1 title/message helper."""
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
from tools.inspect_assets import parse_tbb_header
from tools.semantic_experiment import arm, require_unicorn, unicorn

TEXT, INJECT, DATA, STACK = 0x00100000, 0x01000000, 0x02000000, 0x08000000
TEXT_SIZE, INJECT_SIZE, DATA_SIZE, STACK_SIZE = 0x00400000, 0x00010000, 0x00020000, 0x00002000
MANAGER_GLOBAL, WORK_OFF = 0x0043DA28, 0x1000
INPUT_OFF, COPY_SRC_OFF, COPY_DST_OFF = 0x8000, 0x4000, 0x6000
ASSET_OFF, H1_ROW_STRIDE, H1_STRING_FIELD = 0x10000, 0x56, 0x16
WORK_SIZE, RETURN, SP = 0x564, INJECT + 0xFFF0, STACK + 0x1000
IMAGE = ROOT / "extracted/exefs/code.bin"
ASSET = ROOT / "build/semantic-equivalence/real-assets/romfs/title/TitleTable.tbb"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
ASSET_SHA = "edd6bc1de5388e5689f797861ae6947c7c339f9b6bdb63d6c35951d72020fa41"
SOURCE = ROOT / "experiments/semantic_equivalence/h1_title_message_candidate.cpp"
HELPER = (0x0029F10C, 316, "9e432ddfb9a774f0665383f3d790f83fb7b79b44121a8e96806a114e37314873")
COPY = (0x002C5FF4, 136, "644501596cdc02773609b59f6b01e737be96c516e4546919af3c259c1b64746e")
OPT_COPY = (0x002BCF58, 116, "d4e075de5405e2393514369688bf643d3d2064f5386b321b2b9f0ee3d511e0fe")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_candidate(out: Path, source: Path = SOURCE) -> dict:
    out.mkdir(parents=True, exist_ok=False)
    clang = find_clang()
    obj = out / "title_message.o"
    compile_argv = [str(clang), *get_armv6k_flags(ROOT, clang), "-c", str(source), "-o", str(obj)]
    cp = subprocess.run(compile_argv, cwd=ROOT, capture_output=True, text=True)
    if cp.returncode:
        raise RuntimeError(f"compile failed: {cp.stderr}")
    elf = out / "title_message.elf"
    link_argv = [str(clang), *get_armv6k_flags(ROOT, clang), "-nostdlib", "-fuse-ld=lld",
                 f"-Wl,-Ttext={INJECT:#x}", "-Wl,-e,h1_title_message_candidate",
                 "-Wl,--build-id=none", "-Wl,--no-undefined", str(obj), "-o", str(elf)]
    lp = subprocess.run(link_argv, cwd=ROOT, capture_output=True, text=True)
    (out / "commands.json").write_text(json.dumps({
        "compile": {"argv": compile_argv, "exit_code": cp.returncode, "stderr": cp.stderr},
        "link": {"argv": link_argv, "exit_code": lp.returncode, "stderr": lp.stderr},
    }, indent=2) + "\n", encoding="utf-8")
    if lp.returncode:
        raise RuntimeError(f"link failed: {lp.stderr}")
    tools_dir = clang.parent
    objcopy, nm = tools_dir / "llvm-objcopy.exe", tools_dir / "llvm-nm.exe"
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
    names = {"h1_title_message_candidate", "h1_title_message_forward_copy_candidate"}
    if names - symbols.keys():
        raise RuntimeError(f"missing symbols: {sorted(names - symbols.keys())}")
    undefined = subprocess.run([str(nm), "-u", str(elf)], check=True,
                               capture_output=True, text=True).stdout.splitlines()
    if any(line.strip() for line in undefined):
        raise RuntimeError(f"unresolved symbols: {undefined}")
    text = raw.read_bytes()
    if len(text) > INJECT_SIZE:
        raise RuntimeError("candidate text exceeds injection mapping")
    return {"text": text, "symbols": {name: symbols[name] for name in names}, "elf": elf,
            "meta": {"compiler": str(clang), "compile_argv": compile_argv,
                     "compile_exit_code": cp.returncode, "link_argv": link_argv,
                     "link_exit_code": lp.returncode, "source": str(source),
                     "source_sha256": sha(source.read_bytes()),
                     "object_sha256": sha(obj.read_bytes()), "elf_sha256": sha(elf.read_bytes()),
                     "text_sha256": sha(text), "text_size": len(text), "undefined_symbols": [],
                     "symbols": {name: hex(symbols[name]) for name in names}}}


def regread(uc, name: str) -> int:
    return uc.reg_read(getattr(arm, f"UC_ARM_REG_{name}"))


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
        self.linked = linked
        self.calls: list[dict] = []
        self.opt_copy_entries = 0
        self.fault: str | None = None
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._hook)

    def _hook(self, uc, pc, _size, _user):
        if pc == RETURN:
            uc.emu_stop()
            return
        if pc == OPT_COPY[0]:
            self.opt_copy_entries += 1
        if self.linked is None:
            watched = {COPY[0]: "copy"}
        else:
            watched = {self.linked["symbols"]["h1_title_message_forward_copy_candidate"]: "copy"}
        name = watched.get(pc)
        if name:
            self.calls.append({"name": name, "pc": hex(pc),
                               "args": [hex(regread(self.uc, reg)) for reg in ("R0", "R1", "R2")]})

    def run_helper(self, data: bytes, message: int, color: int) -> dict:
        return self._run(data, "helper", (message, color))

    def run_copy(self, data: bytes, destination: int, source: int, length: int) -> dict:
        return self._run(data, "copy", (destination, source, length))

    def _run(self, data: bytes, mode: str, args: tuple[int, ...]) -> dict:
        if len(data) != DATA_SIZE:
            raise ValueError("fixture must initialize the complete data mapping")
        self.uc.mem_write(DATA, data)
        # The pinned literal is the manager structure address itself; the
        # helper loads its work pointer at manager + 4.
        self.uc.mem_write(MANAGER_GLOBAL + 4, struct.pack("<I", DATA + WORK_OFF))
        self.uc.mem_write(STACK, bytes([0x5A]) * STACK_SIZE)
        for i in range(13):
            self.uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), 0xA5A50000 | i)
        self.uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
        self.uc.reg_write(arm.UC_ARM_REG_SP, SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.reg_write(arm.UC_ARM_REG_FPSCR, 0x01000000)
        for i in range(8, 16):
            self.uc.reg_write(getattr(arm, f"UC_ARM_REG_D{i}"), 0x1111222233334400 + i)
        self.uc.reg_write(arm.UC_ARM_REG_R0, args[0])
        self.uc.reg_write(arm.UC_ARM_REG_R1, args[1])
        if len(args) > 2:
            self.uc.reg_write(arm.UC_ARM_REG_R2, args[2])
        preserved_before = {f"r{i}": regread(self.uc, f"R{i}") for i in range(4, 12)}
        preserved_before["sp"] = SP
        d_before = [regread(self.uc, f"D{i}") for i in range(8, 16)]
        self.calls, self.fault, self.opt_copy_entries = [], None, 0
        if mode == "helper":
            start = HELPER[0] if self.linked is None else self.linked["symbols"]["h1_title_message_candidate"]
        else:
            start = COPY[0] if self.linked is None else self.linked["symbols"]["h1_title_message_forward_copy_candidate"]
        try:
            self.uc.emu_start(start, 0, count=200000)
        except unicorn.UcError as exc:
            self.fault = f"{exc} at pc={regread(self.uc, 'PC'):#x}"
        preserved_after = {f"r{i}": regread(self.uc, f"R{i}") for i in range(4, 12)}
        preserved_after["sp"] = regread(self.uc, "SP")
        data_after = bytes(self.uc.mem_read(DATA, DATA_SIZE))
        return {"fault": self.fault, "pc": hex(regread(self.uc, "PC")),
                "r0": hex(regread(self.uc, "R0")), "r1": hex(regread(self.uc, "R1")),
                "preserved_before": preserved_before, "preserved_after": preserved_after,
                "d8_before": d_before,
                "d8_after": [regread(self.uc, f"D{i}") for i in range(8, 16)],
                "fpscr": regread(self.uc, "FPSCR"), "data": data_after,
                "data_sha256": sha(data_after),
                "work": data_after[WORK_OFF:WORK_OFF + WORK_SIZE],
                "work_sha256": sha(data_after[WORK_OFF:WORK_OFF + WORK_SIZE]),
                "stack": bytes(self.uc.mem_read(SP, STACK + STACK_SIZE - SP)),
                "stack_sha256": sha(bytes(self.uc.mem_read(SP, STACK + STACK_SIZE - SP))),
                "calls": list(self.calls), "optimized_copy_entries": self.opt_copy_entries}


def blank_data(fill: int = 0xA7) -> bytearray:
    return bytearray([fill]) * DATA_SIZE


def helper_fixture(name: str, message: bytes | None, color: int = 0x323232FF) -> dict:
    data = blank_data()
    message_ptr = 0
    if message is not None:
        message_ptr = DATA + INPUT_OFF
        # The supported pointer names a readable 128-byte span even when the
        # logical string terminates sooner. The scan-limit case is all content.
        data[INPUT_OFF:INPUT_OFF + 128] = bytes([0x55]) * 128
        data[INPUT_OFF:INPUT_OFF + len(message)] = message
    return {"name": name, "data": bytes(data), "message": message_ptr,
            "color": color, "input_hex": None if message is None else message.hex(),
            "input_length": None if message is None else len(message)}


def helper_cases() -> list[dict]:
    two_lines_at_scan_edge = b"A" * 64 + b"\n" + b"B" * 62 + b"\0"
    cases = [
        helper_fixture("null color reset", None),
        helper_fixture("empty nonnull string", b"\0", 0x80402010),
        helper_fixture("one line ordinary", b"Title\0"),
        helper_fixture("one line max nominal slot length", b"A" * 64 + b"\0"),
        helper_fixture("high-bit bytes treated as content", b"A\xff\x80Z\0"),
        helper_fixture("newline at first byte and short second line", b"\nSecond\0"),
        helper_fixture("two bounded lines", b"First line\nSecond line\0"),
        helper_fixture("two bounded lines with NUL at scan index 127", two_lines_at_scan_edge),
        helper_fixture("128 readable bytes without terminator stops without partial copy", b"Q" * 128),
    ]
    return cases


def real_asset_cases(raw_tbb: bytes) -> tuple[list[dict], dict]:
    if sha(raw_tbb) != ASSET_SHA or len(raw_tbb) != 880:
        raise ValueError("TitleTable.tbb does not match the frozen 880-byte asset")
    parsed = parse_tbb_header(raw_tbb)
    if parsed["magic"] != "TBCR" or parsed["table_count"] < 1:
        raise ValueError("TitleTable.tbb lacks table 0")
    table = parsed["tables"][0]
    if table["magic"] != "TBL1" or table["payload_size"] < 4 * H1_ROW_STRIDE:
        raise ValueError("TitleTable.tbb table 0 does not contain four complete H1 rows")
    payload_file_offset = table["offset"] + 0x10
    cases, rows = [], []
    for row_index in range(4):
        row_file_offset = payload_file_offset + row_index * H1_ROW_STRIDE
        string_file_offset = row_file_offset + H1_STRING_FIELD
        row_end = row_file_offset + H1_ROW_STRIDE
        nul = raw_tbb.find(b"\0", string_file_offset, row_end)
        if nul < 0:
            raise ValueError(f"H1 help row {row_index} has no NUL within its 0x56-byte row")
        string = raw_tbb[string_file_offset:nul]
        line_lengths = [len(part) for part in string.split(b"\n")]
        if len(string) >= 0x80 or any(length > 0x40 for length in line_lengths):
            raise ValueError(f"H1 help row {row_index} is outside the safe scan/line domain")
        # Map the actual asset bytes and pass the caller-derived file offset as
        # a pointer into that mapping, rather than substituting a copied string.
        data = blank_data()
        data[ASSET_OFF:ASSET_OFF + len(raw_tbb)] = raw_tbb
        pointer = DATA + ASSET_OFF + string_file_offset
        decoded = string.decode("ascii", errors="backslashreplace")
        name = f"real H1 help row {row_index}: {decoded}"
        cases.append({"name": name, "data": bytes(data), "message": pointer,
                      "color": 0x323232FF, "input_hex": string.hex(),
                      "input_length": len(string), "asset_row_index": row_index,
                      "asset_row_file_offset": row_file_offset,
                      "asset_string_payload_offset": row_index * H1_ROW_STRIDE + H1_STRING_FIELD,
                      "asset_string_file_offset": string_file_offset,
                      "asset_string_runtime_pointer": pointer,
                      "asset_line_lengths": line_lengths})
        rows.append({"row_index": row_index, "row_file_offset": row_file_offset,
                     "string_field_offset": H1_STRING_FIELD,
                     "string_payload_offset": row_index * H1_ROW_STRIDE + H1_STRING_FIELD,
                     "string_file_offset": string_file_offset,
                     "string_runtime_pointer": hex(pointer),
                     "string_hex": string.hex(), "string_ascii": decoded,
                     "string_length": len(string), "line_lengths": line_lengths,
                     "nul_file_offset": nul, "row_stride": H1_ROW_STRIDE})
    asset_report = {"path": str(ASSET.relative_to(ROOT)), "size": len(raw_tbb),
                    "sha256": sha(raw_tbb), "tbcr_header_size": parsed["header_size"],
                    "table_count": parsed["table_count"], "table0": table,
                    "payload_file_offset": payload_file_offset,
                    "h1_row_stride": H1_ROW_STRIDE,
                    "h1_string_field_offset": H1_STRING_FIELD,
                    "rows": rows}
    return cases, asset_report


def compare_runs(original: dict, candidate: dict, mode: str, name: str) -> dict:
    errors = []
    if original["fault"] or candidate["fault"]: errors.append("execution fault")
    if original["pc"] != hex(RETURN) or candidate["pc"] != hex(RETURN): errors.append("return sentinel differs")
    if original["r0"] != candidate["r0"]: errors.append("r0 differs")
    for side in (original, candidate):
        if side["preserved_after"] != side["preserved_before"]: errors.append("callee-saved GPR/SP changed")
        if side["d8_after"] != side["d8_before"]: errors.append("d8-d15 changed")
    if original["preserved_after"] != candidate["preserved_after"]: errors.append("callee-saved GPR/SP differ")
    if original["d8_after"] != candidate["d8_after"]: errors.append("d8-d15 differ")
    if original["fpscr"] != candidate["fpscr"]: errors.append("FPSCR differs")
    if original["data"] != candidate["data"]: errors.append("full data map differs")
    if original["stack"] != candidate["stack"]: errors.append("caller stack differs")
    if [(c["name"], c["args"]) for c in original["calls"]] != [(c["name"], c["args"]) for c in candidate["calls"]]:
        errors.append("copy call trace differs")
    first_memory = None
    if original["data"] != candidate["data"]:
        off = next(i for i, (a, b) in enumerate(zip(original["data"], candidate["data"])) if a != b)
        first_memory = {"address": hex(DATA + off), "offset": off,
                        "original": original["data"][off], "candidate": candidate["data"][off]}
    result = {"name": name, "mode": mode, "passed": not errors, "errors": errors,
              "first_memory_mismatch": first_memory,
              "original": {k: original[k] for k in ("fault", "pc", "r0", "preserved_after", "d8_after", "fpscr", "data_sha256", "work_sha256", "stack_sha256", "calls", "optimized_copy_entries")},
              "candidate": {k: candidate[k] for k in ("fault", "pc", "r0", "preserved_after", "d8_after", "fpscr", "data_sha256", "work_sha256", "stack_sha256", "calls", "optimized_copy_entries")}}
    if mode == "helper":
        result["original_work_hex"] = original["work"].hex()
        result["candidate_work_hex"] = candidate["work"].hex()
    return result


def run_helper_case(image: bytes, linked: dict, case: dict, mutant: dict | None = None) -> dict:
    o = Machine(image, None).run_helper(case["data"], case["message"], case["color"])
    c = Machine(image, mutant or linked).run_helper(case["data"], case["message"], case["color"])
    result = compare_runs(o, c, "helper", case["name"])
    result["input_hex"] = case["input_hex"]
    result["input_length"] = case["input_length"]
    result["color"] = hex(case["color"])
    for key in ("asset_row_index", "asset_row_file_offset", "asset_string_file_offset",
                "asset_string_payload_offset", "asset_string_runtime_pointer", "asset_line_lengths"):
        if key in case:
            result[key] = case[key]
    return result


def copy_cases() -> list[dict]:
    lengths = [0, 1, 2, 3, 4, 7, 8, 9, 31, 32, 33]
    result = []
    for da in range(4):
        for sa in range(4):
            for length in lengths:
                data = blank_data(fill=0x6D)
                src = DATA + COPY_SRC_OFF + sa
                dst = DATA + COPY_DST_OFF + da
                pattern = bytes(((i * 73 + sa * 19 + da * 11) & 0xFF) for i in range(length + 4))
                data[COPY_SRC_OFF + sa:COPY_SRC_OFF + sa + len(pattern)] = pattern
                result.append({"name": f"copy dst-align-{da} src-align-{sa} length-{length}",
                               "data": bytes(data), "destination": dst, "source": src,
                               "length": length, "dest_alignment": da, "source_alignment": sa})
    return result


def run_copy_case(image: bytes, linked: dict, case: dict, mutant: dict | None = None) -> dict:
    o = Machine(image, None).run_copy(case["data"], case["destination"], case["source"], case["length"])
    c = Machine(image, mutant or linked).run_copy(case["data"], case["destination"], case["source"], case["length"])
    result = compare_runs(o, c, "copy", case["name"])
    result.update({k: case[k] for k in ("length", "dest_alignment", "source_alignment")})
    result["original_destination_hex"] = o["data"][case["destination"] - DATA:case["destination"] - DATA + case["length"]].hex()
    return result


def build_mutant(out: Path, name: str, old: str, new: str) -> dict:
    source_text = SOURCE.read_text(encoding="utf-8")
    if source_text.count(old) != 1:
        raise ValueError(f"{name}: expected exactly one mutation anchor")
    out.mkdir(parents=True, exist_ok=False)
    mutant_source = out / f"{name}.cpp"
    mutant_source.write_text(source_text.replace(old, new), encoding="utf-8")
    linked = compile_candidate(out / "build", mutant_source)
    linked["meta"]["mutant_source_sha256"] = sha(mutant_source.read_bytes())
    return linked


def run(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    image = IMAGE.read_bytes()
    if sha(image) != IMAGE_SHA:
        raise ValueError("pinned image identity mismatch")
    raw_tbb = ASSET.read_bytes()
    actual_cases, actual_asset = real_asset_cases(raw_tbb)
    identities = {}
    for name, (address, size, expected) in (("message", HELPER), ("forward_copy", COPY), ("optimized_copy", OPT_COPY)):
        body = image[address - TEXT:address - TEXT + size]
        if len(body) != size or sha(body) != expected:
            raise ValueError(f"pinned {name} span identity mismatch")
        identities[name] = {"entry": hex(address), "size": size, "sha256": sha(body)}

    linked = compile_candidate(output / "candidate-build")
    synthetic_cases = helper_cases()
    cases = synthetic_cases + actual_cases
    helper_results = [run_helper_case(image, linked, case) for case in cases]
    direct_copy_cases = copy_cases()
    copy_results = [run_copy_case(image, linked, case) for case in direct_copy_cases]

    # Three independent sensitivity controls: wrong null return, omitted color
    # store, and changed byte-copy payload. Mutant builds are sequential.
    controls = []
    return_mutant = build_mutant(output / "negative-controls/return", "wrong_null_return",
                                 "return 0xFFu;", "return 0u;")
    return_case = cases[0]
    rr = run_helper_case(image, linked, return_case, return_mutant)
    controls.append({"name": "wrong_null_mode_return", "detected": not rr["passed"], "case": rr,
                     "mutant": return_mutant["meta"]})

    store_mutant = build_mutant(output / "negative-controls/store", "omitted_color_store",
                                "store_u32(work + 0x4CC, color);",
                                "/* mutation omits the work +0x4CC color store */")
    sr = run_helper_case(image, linked, cases[0], store_mutant)
    controls.append({"name": "omitted_color_store", "detected": not sr["passed"], "case": sr,
                     "mutant": store_mutant["meta"]})

    copy_mutant = build_mutant(output / "negative-controls/copy", "corrupt_copy_bytes",
                               "to[i] = from[i];", "to[i] = static_cast<uint8_t>(from[i] ^ 0xFFu);")
    cr = run_helper_case(image, linked, cases[2], copy_mutant)
    controls.append({"name": "corrupt_forward_copy_bytes", "detected": not cr["passed"], "case": cr,
                     "mutant": copy_mutant["meta"]})

    report = {"schema_version": 1, "task_id": "h1-title-message-candidate",
              "passed": all(c["passed"] for c in helper_results + copy_results)
                        and all(c["detected"] for c in controls),
              "reference_image_sha256": sha(image), "pinned_components": identities,
              "real_asset": actual_asset,
              "synthetic_helper_case_count": len(synthetic_cases),
              "real_asset_case_count": len(actual_cases),
              "candidate": linked["meta"], "helper_case_count": len(helper_results),
              "helper_cases": helper_results, "copy_case_count": len(copy_results),
              "copy_cases": copy_results, "negative_controls": controls,
              "first_mismatch": next(({"suite": suite, "name": c["name"], "errors": c["errors"],
                                        "first_memory_mismatch": c["first_memory_mismatch"]}
                                       for suite, caseset in (("helper", helper_results), ("copy", copy_results))
                                       for c in caseset if not c["passed"]), None),
              "supported_domain": {
                  "manager_and_work": "global cell at 0x0043DA28 resolves to a valid manager with a valid writable work pointer; modeled work extent is 0x564 bytes",
                  "message": "non-null input names at least 128 readable bytes; each copied line is at most 64 bytes; NUL/LF behavior is limited to the tested first two lines; null reset does not dereference input",
                  "copy": "forward copy of non-overlapping ranges in mapped ordinary memory; source/destination valid for length bytes",
                  "tbb": "the four frozen TitleTable.tbb table-0 rows are mapped at their file offsets and passed at payload + row*0x56 + 0x16; the actual H1 caller is not executed"},
              "projection": ["fault and return sentinel", "r0", "r4-r11 and SP preservation/equality",
                             "d8-d15 preservation/equality", "FPSCR", "full 0x20000-byte data map",
                             "0x564-byte work bytes", "caller-owned stack", "copy call arguments/order",
                             "optimized pinned copier entry count"],
              "evidence": {"compiled": "passed", "arm_differential": "partial_bounded_synthetic",
                           "caller": "not_run", "runtime": "not_run"},
              "limitations": [
                  "The 9 baseline message fixtures are synthetic; four additional cases use actual bytes and row-derived pointers from the frozen TitleTable.tbb asset. The harness invokes the helper directly and does not execute the H1 caller or construct its runtime TBB objects.",
                  "The pinned routine has no per-line cap. Candidate safety is limited to at most 64 bytes per copied line. First-line lengths above 64 overlap the nominal second slot; second-line lengths above 64 overwrite adjacent fields, and lengths above 84 exceed the modeled 0x564-byte work object. These are excluded, not accepted as safe.",
                  "The scan-boundary case supplies 128 readable ordinary bytes without terminator and observes the original's no-partial-copy cutoff; it does not claim an unbounded C string is valid.",
                  "The copy candidate is forward-only under non-overlap precondition; overlap/memmove behavior and invalid/null pointers are unsupported. Copy return and memory are checked, but volatile/MMIO access ordering is not modeled.",
                  "No H1 caller differential, production integration, emulator, Azahar, renderer, or game-runtime behavior was tested."],
              "optimized_copy_path_coverage": {"direct_matrix_cases_entering_0x002BCF58": sum(c["original"]["optimized_copy_entries"] for c in copy_results),
                                               "helper_copy_calls_entering_0x002BCF58": sum(c["original"]["optimized_copy_entries"] for c in helper_results)}}
    report["first_mismatch"] = report["first_mismatch"]
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    report = run(output)
    passed = sum(c["passed"] for c in report["helper_cases"] + report["copy_cases"])
    total = report["helper_case_count"] + report["copy_case_count"]
    controls = sum(c["detected"] for c in report["negative_controls"])
    print(f"title/message differential: {'PASS' if report['passed'] else 'FAIL'} "
          f"{passed}/{total}; controls {controls}/3; report={output / 'report.json'}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
