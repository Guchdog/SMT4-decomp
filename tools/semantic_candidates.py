"""Milestone-oriented discovery of readable-C++ reconstruction work.

Discovery is static triage, not evidence of behavioral equivalence. Original
machine-code bytes and the exact ledger remain reference inputs only.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
import re

from tools.audit_semantic_candidates import _candidate_definitions
from tools.find_candidates import is_asm_backed_row


def load_policy(root: Path) -> dict:
    path = root / "config" / "reconstruction.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"active_milestone": "unscoped", "priority_functions": [], "priority_sources": []}


def existing_candidate_addresses(root: Path) -> set[int]:
    addresses = set()
    for source in sorted((root / "experiments" / "semantic_equivalence").glob("*.cpp")):
        for symbol in _candidate_definitions(source):
            match = re.fullmatch(r"candidate_([0-9a-fA-F]{8})", symbol)
            if match:
                addresses.add(int(match.group(1), 16))
    return addresses


def find_semantic_candidates(
    functions_csv: Path, repo_root: Path, code_bytes: bytes = b"",
    max_size: int = 8192, limit: int = 50, category: str | None = None,
    statuses: tuple[str, ...] | None = None, include_existing: bool = False,
    policy: dict | None = None, asm_backed_only: bool = False,
) -> list[dict]:
    """Rank unreconstructed functions by milestone relevance, then size.

    Neither byte identity, leaf shape, nor compiler instruction choice is an
    eligibility criterion. Existing address-named experimental C++ is omitted
    by default so discovery does not repeatedly reconstruct the same functions.
    """
    root = Path(repo_root).resolve()
    policy = load_policy(root) if policy is None else policy
    priorities = {int(item["address"], 16): (i, item["reason"])
                  for i, item in enumerate(policy.get("priority_functions", []))}
    sources = set(policy.get("priority_sources", []))
    existing = existing_candidate_addresses(root)
    statuses = statuses if statuses is not None else (
        "matching", "non_matching", "todo", "stub", "wip")
    index_cache = {}
    candidates = []
    with Path(functions_csv).open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["status"] not in statuses or row["category"] == "raw_span":
                continue
            address, size = int(row["address"], 16), int(row["size"])
            if size <= 0 or (max_size > 0 and size > max_size):
                continue
            if category and row["category"].lower() != category.lower():
                continue
            offset = address - 0x00100000
            if code_bytes and (offset < 0 or offset + size > len(code_bytes)):
                continue
            has_candidate = address in existing
            if has_candidate and not include_existing:
                continue
            # Matching is a property of reference bytes, not reconstructed C++.
            # Skip active typed implementations, but keep missing sources and
            # scaffolding visible for semantic investigation.
            source = row.get("src_file", "").strip()
            asm_backed = is_asm_backed_row(row, root, index_cache) if source else False
            if asm_backed_only and not asm_backed:
                continue
            if (row["status"] in ("matching", "non_matching") and source
                    and (root / source).is_file() and not asm_backed
                    and not has_candidate):
                continue
            if address in priorities:
                order, reason = priorities[address]
                tier = 0
            elif source in sources:
                tier, order, reason = 1, 0, "Source participates in the active milestone"
            else:
                tier, order, reason = 2, 0, "General semantic reconstruction backlog"
            candidates.append({
                "address": f"0x{address:08x}", "size": size,
                "name": row["name"], "category": row["category"],
                "src_file": source, "reference_status": row["status"],
                "asm_backed": asm_backed, "existing_candidate": has_candidate,
                "milestone": policy.get("active_milestone", "unscoped"),
                "priority_tier": tier, "priority_order": order,
                "priority_reason": reason,
                "next_action": "validate_or_integrate" if has_candidate else "recover_contract_and_cpp",
            })
    candidates.sort(key=lambda c: (c["priority_tier"], c["priority_order"],
                                   c["size"], int(c["address"], 16)))
    return candidates[:limit] if limit > 0 else candidates
