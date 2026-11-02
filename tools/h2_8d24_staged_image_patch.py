#!/usr/bin/env python3
"""Build a reproducible one-function H2 image/IPS for 0x002B8D24."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

import capstone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.h2_calc_code_patch import apply_ips, encode_ips

IMAGE = ROOT / "extracted/exefs/code.bin"
SOURCE = ROOT / "src/engine/leaf_batch46_a.cpp"
SYMBOL = "battle_func_002b8d24"
VMA = 0x002B8D24
SPAN = 360
IMAGE_BASE = 0x00100000
ORIGINAL_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
ARM_NOP = struct.pack("<I", 0xE320F000)
U32 = 0xFFFFFFFF


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "build/h2-8d24-staged")
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    original = IMAGE.read_bytes()
    if sha(original) != ORIGINAL_SHA256:
        raise SystemExit("pinned original image hash mismatch")
    build_dir = out / "tu-build"
    subprocess.run([sys.executable, str(ROOT / "tools/build_check.py"),
                    "--tu", str(SOURCE), "--out-dir", str(build_dir), "-j", "1"],
                   check=True, cwd=ROOT)
    obj = build_dir / "engine/leaf_batch46_a.o"
    body, relocations = extract_elf_functions_detailed(obj)[SYMBOL]
    if relocations:
        raise SystemExit(f"production function has unresolved relocations: {relocations}")
    if len(body) != 356 or len(body) > SPAN or (SPAN - len(body)) % 4:
        raise SystemExit(f"unexpected production body size {len(body)} for {SPAN}-byte slot")

    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoder.detail = True
    # The final eight bytes are two fixed ARM helper addresses, not instructions.
    code_size = len(body) - 8
    instructions = list(decoder.disasm(body[:code_size], VMA))
    if sum(item.size for item in instructions) != code_size:
        raise SystemExit("production code prefix did not decode completely as ARM")
    slot_end = VMA + SPAN
    tail = slot_end - 4
    for insn in instructions:
        if insn.group(capstone.CS_GRP_JUMP):
            for operand in insn.operands:
                if operand.type == capstone.arm.ARM_OP_IMM and operand.imm == tail:
                    raise SystemExit("branch enters the final padding word")
        if insn.id == capstone.arm.ARM_INS_LDR and len(insn.operands) >= 2:
            source = insn.operands[1]
            if source.type == capstone.arm.ARM_OP_MEM and source.mem.base == capstone.arm.ARM_REG_PC:
                target = insn.address + 8 + source.mem.disp
                if target == tail:
                    raise SystemExit("PC-relative load reads the final padding word")
    literals = struct.unpack_from("<II", body, len(body) - 8)
    if literals != (0x002AF854, 0x002BF030) or any(value & 1 for value in literals):
        raise SystemExit(f"unexpected helper literal/interworking addresses: {literals!r}")
    # The third dependency is synthesized as MOV/ORR immediates rather than a
    # literal load. Verify that the compiled target and BLX register agree.
    mov_values = [item.operands[1].imm for item in instructions
                  if item.mnemonic == "mov" and len(item.operands) == 2
                  and item.operands[0].type == capstone.arm.ARM_OP_REG
                  and decoder.reg_name(item.operands[0].reg) == "r2"
                  and item.operands[1].type == capstone.arm.ARM_OP_IMM]
    orr_values = [item.operands[2].imm for item in instructions
                  if item.mnemonic == "orr" and len(item.operands) == 3
                  and item.operands[0].type == capstone.arm.ARM_OP_REG
                  and decoder.reg_name(item.operands[0].reg) == "r2"
                  and item.operands[1].type == capstone.arm.ARM_OP_REG
                  and decoder.reg_name(item.operands[1].reg) == "r2"
                  and item.operands[2].type == capstone.arm.ARM_OP_IMM]
    if 0x4F0 not in mov_values or 0x138000 not in orr_values or (0x4F0 | 0x138000) != 0x001384F0:
        raise SystemExit("compiled set-byte helper pointer is not 0x001384F0")
    blx_regs = {decoder.reg_name(item.operands[0].reg)
                for item in instructions if item.mnemonic == "blx"
                and item.operands and item.operands[0].type == capstone.arm.ARM_OP_REG}
    if not {"r2", "r3", "r5", "r8"}.issubset(blx_regs):
        raise SystemExit(f"unexpected indirect ARM helper call registers: {blx_regs}")

    offset = VMA - IMAGE_BASE
    replacement = body + ARM_NOP * ((SPAN - len(body)) // 4)
    patched = bytearray(original)
    patched[offset:offset + SPAN] = replacement
    patch = encode_ips([(offset, replacement)], len(original))
    if apply_ips(original, patch) != bytes(patched):
        raise SystemExit("IPS round trip mismatch")
    if bytes(patched[offset:offset + SPAN]) != replacement or replacement[-4:] != ARM_NOP:
        raise SystemExit("final slot bytes or ARM NOP tail mismatch")

    image_path = out / "code.h2-8d24.bin"
    ips_path = out / "code.h2-8d24.ips"
    manifest_path = out / "manifest.json"
    image_path.write_bytes(patched)
    ips_path.write_bytes(patch)
    manifest = {
        "function": hex(VMA), "symbol": SYMBOL, "classification": "non_matching",
        "source": str(SOURCE.relative_to(ROOT)), "source_sha256": sha(SOURCE.read_bytes()),
        "object": str(obj.relative_to(ROOT)), "object_sha256": sha(obj.read_bytes()),
        "body_bytes": len(body), "slot_bytes": SPAN, "tail_policy": "one ARM NOP at slot end",
        "helper_literals": [hex(value) for value in literals],
        "verified_even_arm_call_targets": ["0x002af854", "0x002bf030", "0x001384f0"],
        "original_image_sha256": sha(original), "patched_image_sha256": sha(patched),
        "ips_sha256": sha(patch), "ips_roundtrip": True,
        "artifact_paths": {"image": str(image_path.relative_to(ROOT)),
                           "ips": str(ips_path.relative_to(ROOT))},
        "evidence": {"compiled": "passed", "arm_interworking": "passed for helper pointers",
                     "arm_differential": "not_run", "caller": "not_run", "runtime": "not_run"},
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"PASS {len(body)}/{SPAN} bytes; ARM NOP tail; IPS round-trip")
    print(f"image sha256 {sha(patched)}")
    print(f"IPS sha256 {sha(patch)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
