#!/usr/bin/env python3
"""Generate review-only scaffolds from a repeated-mnemonic signature report.

The output pins source bytes and decoded instructions, and lists possible ARM
BL references as unverified leads. It does not infer ABI or emit implementations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import capstone


TEXT_BASE = 0x00100000
THUMB_START = 0x00100048
THUMB_END = 0x00101300


def instruction_text(insn) -> str:
    return f"{insn.mnemonic} {insn.op_str}".strip()


def decode_candidate(image: bytes, candidate: dict) -> tuple[bytes, list[str], str]:
    address = int(candidate["address"], 16)
    size = int(candidate["size"])
    offset = address - TEXT_BASE
    if size <= 0 or offset < 0 or offset + size > len(image):
        raise ValueError(f"candidate {address:#010x} is outside code image bounds")
    mode = "thumb" if THUMB_START <= address < THUMB_END else "arm"
    cs_mode = capstone.CS_MODE_THUMB if mode == "thumb" else capstone.CS_MODE_ARM
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, cs_mode)
    raw = image[offset:offset + size]
    instructions = list(decoder.disasm(raw, address))
    if sum(insn.size for insn in instructions) != size:
        raise ValueError(f"candidate {address:#010x} does not decode to its pinned size")
    decoded = [instruction_text(insn) for insn in instructions]
    reported = candidate.get("instructions")
    if reported is not None and list(reported) != decoded:
        raise ValueError(
            f"signature report instruction drift at {address:#010x}: "
            f"reported={list(reported)!r}, actual={decoded!r}"
        )
    return raw, decoded, mode


def suggest_arm_bl_xrefs(image: bytes, targets: set[int]) -> dict[int, list[int]]:
    """Find ARM direct BL targets; results are heuristics, never confirmed xrefs."""
    found = {target: [] for target in targets}
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoder.detail = True
    for insn in decoder.disasm(image, TEXT_BASE):
        if insn.id != capstone.arm.ARM_INS_BL or not insn.operands:
            continue
        operand = insn.operands[0]
        if operand.type == capstone.arm.ARM_OP_IMM and operand.imm in found:
            found[operand.imm].append(insn.address)
    return found


def select_candidates(report: dict, group_index: int, addresses: list[str]) -> tuple[dict, list[dict]]:
    groups = report.get("groups")
    if not isinstance(groups, list) or not 0 <= group_index < len(groups):
        raise ValueError(f"group index {group_index} is not present in report")
    group = groups[group_index]
    candidates = group.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError(f"group {group_index} has no candidates")
    if not addresses:
        return group, list(candidates)

    requested = {int(address, 0) for address in addresses}
    by_address = {int(item["address"], 16): item for item in candidates}
    missing = requested - by_address.keys()
    if missing:
        raise ValueError(
            "requested addresses are not members of selected group: "
            + ", ".join(f"{address:#010x}" for address in sorted(missing))
        )
    return group, [by_address[address] for address in sorted(requested)]


def build_manifest(report: dict, image: bytes, group_index: int, addresses: list[str]) -> dict:
    group, selected = select_candidates(report, group_index, addresses)
    entries = []
    for candidate in selected:
        raw, instructions, mode = decode_candidate(image, candidate)
        entries.append({
            "address": f"{int(candidate['address'], 16):#010x}",
            "name": candidate.get("name"),
            "size": len(raw),
            "category": candidate.get("category"),
            "status": candidate.get("status"),
            "src_file": candidate.get("src_file"),
            "mode": mode,
            "original_bytes_sha256": hashlib.sha256(raw).hexdigest(),
            "original_bytes_hex": raw.hex(),
            "instructions": instructions,
        })
    xrefs = suggest_arm_bl_xrefs(
        image, {int(entry["address"], 16) for entry in entries}
    )
    for entry in entries:
        address = int(entry["address"], 16)
        entry["possible_arm_bl_callers"] = [f"{callsite:#010x}" for callsite in xrefs[address]]
        entry["caller_review_required"] = True

    return {
        "schema_version": 1,
        "purpose": "review scaffold only; no semantic contract or implementation inferred",
        "source_signature_report": report.get("source"),
        "code_image_sha256": hashlib.sha256(image).hexdigest(),
        "group_index_zero_based": group_index,
        "mnemonics": group.get("mnemonics", []),
        "candidate_count_in_group": group.get("count", len(group.get("candidates", []))),
        "selected_candidate_count": len(entries),
        "caller_xref_scan": {
            "kind": "possible ARM direct BL targets",
            "confirmed": False,
            "thumb_calls_scanned": False,
            "limitations": (
                "A linear ARM decode can mistake literal/data words for code; "
                "indirect calls and Thumb BL are not included. Manually inspect "
                "each candidate in its containing function before treating any "
                "listed address as a caller. Absence is not evidence of no callers."
            ),
        },
        "candidates": entries,
    }


def render_review(manifest: dict) -> str:
    lines = [
        "# Semantic-family review scaffold",
        "",
        "> Generated triage material only. No ABI, high-level meaning, or C++ implementation is inferred.",
        "> Caller addresses are ARM BL scan suggestions; verify them in containing functions.",
        "",
        f"- Code image SHA-256: `{manifest['code_image_sha256']}`",
        f"- Signature group (zero-based): `{manifest['group_index_zero_based']}`",
        f"- Mnemonic sequence: `{', '.join(manifest['mnemonics'])}`",
        f"- Selected candidates: {manifest['selected_candidate_count']}",
        "",
        "## Review checklist",
        "",
        "- [ ] Confirm each entry's instruction boundary and exact bytes against the pinned image.",
        "- [ ] Identify arguments, return use, callee-saved state, and NZCV consumers from callers.",
        "- [ ] Establish memory width, signedness, alignment, aliasing, null, and fault behavior.",
        "- [ ] Separate ordinary RAM from MMIO, concurrent observers, and side effects.",
        "- [ ] Define directed cases and at least one negative control before writing C++.",
        "- [ ] Add caller windows only after manually verifying callsites and observed state.",
        "",
        "## Candidates",
        "",
    ]
    for entry in manifest["candidates"]:
        lines.extend([
            f"### `{entry['address']}` — {entry.get('name') or 'unnamed'}",
            "",
            f"- Size/mode: {entry['size']} bytes, {entry['mode']}",
            f"- Original SHA-256: `{entry['original_bytes_sha256']}`",
            f"- Ledger status/category: `{entry.get('status')}` / `{entry.get('category')}`",
            "- Possible ARM BL callers (unverified): "
            + (", ".join(f"`{address}`" for address in entry["possible_arm_bl_callers"])
               or "none found by this scan"),
            "- Exact instruction sequence:",
            "",
        ])
        lines.extend(f"  - `{insn}`" for insn in entry["instructions"])
        lines.extend([
            "",
            f"- Bytes: `{entry['original_bytes_hex']}`",
            "",
        ])
    lines.extend([
        "## Implementation placeholder",
        "",
        "See `candidate_skeleton.cpp`. It intentionally contains comments only;",
        "do not infer a signature or fill in behavior from mnemonic similarity alone.",
        "",
    ])
    return "\n".join(lines)


def render_cpp_placeholder(manifest: dict) -> str:
    lines = [
        "// Generated review-only scaffold. This file intentionally does not compile.",
        "// Confirm argument/return types, callers, memory effects, and flags first.",
        "",
    ]
    for entry in manifest["candidates"]:
        lines.extend([
            f"// Original: {entry.get('name') or '<unnamed>'} at {entry['address']} ({entry['size']} bytes).",
            f"// SHA-256: {entry['original_bytes_sha256']}",
            "// Assembly:",
        ])
        lines.extend(f"//   {insn}" for insn in entry["instructions"])
        lines.append("// TODO: document observed contract and implement only after differential cases are defined.")
        lines.append("")
    return "\n".join(lines)


def generate_scaffold(
    report_path: Path,
    code_path: Path,
    output_dir: Path,
    group_index: int,
    addresses: list[str] | None = None,
) -> dict:
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    image = Path(code_path).read_bytes()
    manifest = build_manifest(report, image, group_index, addresses or [])
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / "family_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "review.md").write_text(render_review(manifest), encoding="utf-8")
    (output_dir / "candidate_skeleton.cpp").write_text(
        render_cpp_placeholder(manifest), encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--groups", required=True, type=Path, help="JSON from group_candidate_signatures.py")
    parser.add_argument("--code", required=True, type=Path, help="Verified extracted code.bin")
    parser.add_argument("--group-index", required=True, type=int, help="Zero-based group index in the report")
    parser.add_argument("--address", action="append", default=[], help="Optional candidate address filter; repeat as needed")
    parser.add_argument("--output", required=True, type=Path, help="New output directory; existing directories are refused")
    args = parser.parse_args()
    try:
        manifest = generate_scaffold(
            args.groups, args.code, args.output, args.group_index, args.address
        )
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(
        f"Wrote review scaffold for {manifest['selected_candidate_count']} candidates "
        f"to {args.output} (caller references are unverified suggestions)."
    )


if __name__ == "__main__":
    main()
