"""Small shared setup helpers for isolated ARM semantic experiments.

Family-specific instruction pins, test cases, caller windows, comparison
policies, and negative controls deliberately remain in each experiment module.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.semantic_experiment import validate_leaf


@dataclass(frozen=True)
class PinnedReference:
    """The configured image and ledger after size and SHA-256 validation."""

    image: bytes
    game_info: dict
    ledger: list[dict[str, str]]


def load_pinned_reference(
    code_path: Path,
    game_info_path: Path,
    ledger_path: Path,
) -> PinnedReference:
    """Read code.bin, game metadata, and function ledger; reject revision drift."""
    image = Path(code_path).read_bytes()
    game_info = json.loads(Path(game_info_path).read_text(encoding="utf-8"))
    try:
        expected_size = int(game_info["code_bin_size"])
        expected_hash = str(game_info["code_sha256"]).lower()
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("game_info must define integer code_bin_size and code_sha256") from error

    if len(image) != expected_size:
        raise ValueError(
            f"code.bin size mismatch: expected {expected_size}, got {len(image)}"
        )
    actual_hash = hashlib.sha256(image).hexdigest()
    if actual_hash != expected_hash:
        raise ValueError(
            f"code.bin SHA-256 mismatch: expected {expected_hash}, got {actual_hash}"
        )
    with Path(ledger_path).open(encoding="utf-8", newline="") as stream:
        ledger = list(csv.DictReader(stream))
    if not ledger:
        raise ValueError("function ledger is empty or has no data rows")
    return PinnedReference(image=image, game_info=game_info, ledger=ledger)


def compile_candidate_symbols(
    source_path: Path,
    object_path: Path,
    repo_root: Path,
    required_symbols: Iterable[str],
) -> dict[str, bytes]:
    """Compile one ARMv6K TU and return validated, relocation-free functions.

    Every extracted function is validated, including helper/control symbols;
    required_symbols only controls the final presence check.
    """
    source_path = Path(source_path)
    object_path = Path(object_path)
    repo_root = Path(repo_root)
    build = compile_tu_armv6k(source_path, object_path, repo_root)
    if build.returncode:
        raise RuntimeError(build.stderr or "ARMv6K candidate compilation failed")

    extracted = extract_elf_functions_detailed(object_path)
    compiled: dict[str, bytes] = {}
    for symbol, (code, relocations) in extracted.items():
        if relocations:
            raise ValueError(f"Unsupported relocation in {symbol}: {relocations}")
        try:
            validate_leaf(code)
        except ValueError as error:
            raise ValueError(f"Invalid leaf candidate {symbol}: {error}") from error
        compiled[symbol] = code

    missing = set(required_symbols) - compiled.keys()
    if missing:
        raise ValueError(f"Missing required candidate symbols: {sorted(missing)}")
    return compiled
