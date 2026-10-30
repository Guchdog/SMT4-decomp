import struct
from pathlib import Path

import pytest

from tools.asm_diff import ElfRelocation
from tools.h2_apt_utility4_inplace_experiment import (
    ENTRY,
    ENTRY_SIZE,
    TEXT,
    WRAPPER,
    compose_in_place,
    resolve_call_relocation,
    verify_call_target,
)

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "build/agent-work/H2-semantic/h2-apt-utility4-caller-probe-runtime/reference/code.bin"
SAMPLE = bytes.fromhex(
    "004e2de90000a0e300008de504008de50400a0e30010a0e30020a0e30030a0e3"
    "feffffeb0c88bde8")
RELOC = ElfRelocation(offset=32, relocation_type=28, symbol_name="apt_wrapper")


def test_direct_call_relocation_resolves_to_original_wrapper():
    linked, details = resolve_call_relocation(SAMPLE, (RELOC,), ENTRY)
    verify_call_target(linked, RELOC, ENTRY, WRAPPER)
    assert len(linked) == 40
    assert details == [{"offset": 32, "type": "R_ARM_CALL", "symbol": "apt_wrapper",
                        "addend": -8, "place": hex(ENTRY + 32), "target": hex(WRAPPER),
                        "instruction": "0xebffd2be"}]


def test_wrong_target_and_unsupported_relocation_are_rejected():
    wrong, _ = resolve_call_relocation(SAMPLE, (RELOC,), ENTRY, target=WRAPPER + 4)
    with pytest.raises(ValueError, match="wrapper target"):
        verify_call_target(wrong, RELOC, ENTRY, WRAPPER)
    bad = ElfRelocation(offset=32, relocation_type=2, symbol_name="apt_wrapper")
    with pytest.raises(ValueError, match="unsupported call relocation"):
        resolve_call_relocation(SAMPLE, (bad,), ENTRY)


def test_in_place_composition_changes_only_candidate_bytes():
    original = REFERENCE.read_bytes()
    patched = compose_in_place(original, SAMPLE)
    offset = ENTRY - TEXT
    assert patched[offset:offset + len(SAMPLE)] == SAMPLE
    assert patched[offset + len(SAMPLE):offset + ENTRY_SIZE] == original[offset + len(SAMPLE):offset + ENTRY_SIZE]
    assert patched[:offset] == original[:offset]
    assert patched[offset + ENTRY_SIZE:] == original[offset + ENTRY_SIZE:]
    with pytest.raises(ValueError, match="must fit"):
        compose_in_place(original, SAMPLE + b"\x00" * (ENTRY_SIZE + 1 - len(SAMPLE)))
