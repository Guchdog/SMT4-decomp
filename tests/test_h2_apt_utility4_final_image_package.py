from tools.h2_apt_utility4_final_image_package import (
    contiguous_records,
    delta_is_authorized,
    overlaps,
)


def test_authorization_accepts_declared_spans_and_rejects_other_bytes():
    original = bytes(32)
    patched = bytearray(original)
    patched[4:8] = b"ABCD"
    assert delta_is_authorized(original, bytes(patched), [(4, 8)])
    patched[20] = 1
    assert not delta_is_authorized(original, bytes(patched), [(4, 8)])


def test_image_diffs_are_split_into_exact_contiguous_records():
    original = bytes(12)
    patched = bytearray(original)
    patched[2:4] = b"xy"
    patched[8] = 0x7F
    assert contiguous_records(original, bytes(patched)) == [(2, b"xy"), (8, b"\x7f")]


def test_candidate_must_not_overlap_a_composed_base_record():
    assert overlaps(10, 20, [(15, 30)])
    assert not overlaps(10, 15, [(15, 30)])
