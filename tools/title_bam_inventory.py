#!/usr/bin/env python3
"""Read-only inventory of the title BAM wrapper and its CGFX/CANM metadata.

This deliberately does not export resource payloads.  It reads only the two
title BAM ranges and the TitleTable.tbb integrity anchor from a decrypted CCI,
then reports animation dictionary names, frame counts, kinds, and member counts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from pathlib import Path
from typing import BinaryIO


EXPECTED_TITLE_TABLE_SHA256 = "edd6bc1de5388e5689f797861ae6947c7c339f9b6bdb63d6c35951d72020fa41"
TITLE_BAM_PATHS = ("/title/title_top1.bam", "/title/title_top2.bam")
TITLE_TABLE_PATH = "/title/TitleTable.tbb"
SECTOR_SIZE = 0x200
MAX_CCI_READ = 16 * 1024 * 1024
MAX_SECTIONS = 16
MAX_RESOURCES = 4096
MAX_NAME_BYTES = 256

ANIMATION_KINDS = {
    9: "skeletal",
    10: "material",
    11: "visibility",
    12: "camera",
    13: "light",
    14: "fog",
}


def _need(data: bytes, offset: int, size: int, limit: int | None = None, what: str = "range") -> None:
    bound = len(data) if limit is None else min(len(data), limit)
    if offset < 0 or size < 0 or offset > bound or size > bound - offset:
        raise ValueError(f"{what} outside validated bounds")


def _u16(data: bytes, offset: int, limit: int | None = None) -> int:
    _need(data, offset, 2, limit, "u16")
    return struct.unpack_from("<H", data, offset)[0]


def _u32(data: bytes, offset: int, limit: int | None = None) -> int:
    _need(data, offset, 4, limit, "u32")
    return struct.unpack_from("<I", data, offset)[0]


def _i32(data: bytes, offset: int, limit: int | None = None) -> int:
    _need(data, offset, 4, limit, "i32")
    return struct.unpack_from("<i", data, offset)[0]


def _relative_target(data: bytes, pointer_field: int, limit: int) -> int | None:
    relative = _i32(data, pointer_field, limit)
    if relative == 0:
        return None
    target = pointer_field + relative
    if target < 0 or target >= limit:
        raise ValueError("relative pointer outside containing section")
    return target


def _cstring(data: bytes, offset: int, limit: int) -> str:
    if offset < 0 or offset >= limit:
        raise ValueError("string offset outside containing section")
    end = data.find(b"\0", offset, min(limit, offset + MAX_NAME_BYTES + 1))
    if end < 0:
        raise ValueError("unterminated or overlong CGFX name")
    try:
        value = data[offset:end].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("CGFX metadata name is not UTF-8") from exc
    if not value:
        raise ValueError("empty CGFX metadata name")
    return value


def _read_exact_at(stream: BinaryIO, file_size: int, offset: int, size: int) -> bytes:
    if offset < 0 or size < 0 or size > MAX_CCI_READ or offset > file_size or size > file_size - offset:
        raise ValueError("CCI read range outside file or configured size limit")
    stream.seek(offset)
    data = stream.read(size)
    if len(data) != size:
        raise ValueError("short read from CCI")
    return data


def parse_cci_layout(ncsd_header: bytes, ncch_header: bytes, file_size: int) -> dict:
    """Validate the first NCSD partition and its clear NCCH RomFS range."""
    if len(ncsd_header) < 0x200 or ncsd_header[0x100:0x104] != b"NCSD":
        raise ValueError("CCI does not contain an NCSD header at 0x100")
    partition_lba, partition_units = struct.unpack_from("<II", ncsd_header, 0x120)
    if partition_lba == 0 or partition_units == 0:
        raise ValueError("CCI has no first NCSD partition")
    partition_offset = partition_lba * SECTOR_SIZE
    partition_size = partition_units * SECTOR_SIZE
    if partition_offset > file_size or partition_size > file_size - partition_offset:
        raise ValueError("NCSD first partition exceeds CCI file bounds")
    if len(ncch_header) < 0x200 or ncch_header[0x100:0x104] != b"NCCH":
        raise ValueError("first partition has no NCCH header at +0x100")
    romfs_offset = _u32(ncch_header, 0x1B0) * SECTOR_SIZE
    romfs_size = _u32(ncch_header, 0x1B4) * SECTOR_SIZE
    if romfs_offset == 0 or romfs_size == 0:
        raise ValueError("NCCH has no RomFS section")
    if romfs_offset > partition_size or romfs_size > partition_size - romfs_offset:
        raise ValueError("NCCH RomFS range exceeds first partition")
    return {
        "partition_offset": partition_offset,
        "partition_size": partition_size,
        "romfs_file_offset": partition_offset + romfs_offset,
        "romfs_size": romfs_size,
    }


def _index_entry(index: list, path: str) -> dict:
    found = [item for item in index if isinstance(item, dict) and item.get("path") == path]
    if len(found) != 1:
        raise ValueError(f"RomFS index must contain exactly one {path}")
    item = found[0]
    offset, size = item.get("romfs_offset"), item.get("size")
    if not isinstance(offset, int) or isinstance(offset, bool) or not isinstance(size, int) or isinstance(size, bool):
        raise ValueError(f"invalid RomFS index range for {path}")
    if offset < 0 or size <= 0 or size > MAX_CCI_READ:
        raise ValueError(f"out-of-policy RomFS range for {path}")
    return {"path": path, "romfs_offset": offset, "size": size}


def parse_cgfx(data: bytes) -> dict:
    """Parse bounded CGFX section and animation dictionary metadata only."""
    _need(data, 0, 0x14, what="CGFX header")
    if data[:4] != b"CGFX":
        raise ValueError("missing CGFX magic")
    if _u16(data, 4) != 0xFEFF:
        raise ValueError("unsupported CGFX byte order mark")
    header_size = _u16(data, 6)
    revision = _u32(data, 8)
    file_length = _u32(data, 0x0C)
    section_count = _u32(data, 0x10)
    if header_size < 0x14 or header_size > file_length or file_length > len(data):
        raise ValueError("invalid CGFX header/file size")
    if section_count == 0 or section_count > MAX_SECTIONS:
        raise ValueError("CGFX section count outside safety limit")

    sections = []
    cursor = header_size
    for _ in range(section_count):
        _need(data, cursor, 8, file_length, "CGFX section header")
        magic = data[cursor : cursor + 4]
        length = _u32(data, cursor + 4, file_length)
        if length < 8:
            raise ValueError("CGFX section length is smaller than its header")
        _need(data, cursor, length, file_length, "CGFX section")
        sections.append((magic, cursor, length))
        cursor += length

    data_sections = [item for item in sections if item[0] == b"DATA"]
    if len(data_sections) != 1:
        raise ValueError("CGFX must contain exactly one DATA section")
    _, data_offset, data_length = data_sections[0]
    if _u32(data, data_offset + 4, file_length) != data_length:
        raise ValueError("DATA length disagrees with section length")
    if data_length < 8 + 16 * 8:
        raise ValueError("DATA header is too short for 16 resource dictionary slots")

    dictionaries = {}
    data_end = data_offset + data_length
    for kind, kind_name in ANIMATION_KINDS.items():
        pair = data_offset + 8 + kind * 8
        count = _u32(data, pair, data_end)
        dictionary_offset = _relative_target(data, pair + 4, data_end)
        if count > MAX_RESOURCES:
            raise ValueError("CGFX animation count exceeds safety limit")
        if count == 0:
            if dictionary_offset is not None:
                # Empty tables may retain a non-null pointer; it is not followed.
                continue
            dictionaries[kind] = []
            continue
        if dictionary_offset is None:
            raise ValueError("non-empty animation dictionary has null offset")
        entries = _parse_dictionary(data, dictionary_offset, count, data_end)
        dictionaries[kind] = [(kind_name, name, object_offset) for name, object_offset in entries]

    animations = []
    for kind in ANIMATION_KINDS:
        for kind_name, dictionary_name, object_offset in dictionaries.get(kind, []):
            animations.append(
                _parse_canm(data, object_offset, data_end, kind_name, dictionary_name)
            )
    return {
        "animations": animations,
        "animation_count": len(animations),
        "track_count": sum(animation["track_count"] for animation in animations),
    }


def _parse_dictionary(data: bytes, offset: int, expected_count: int, data_end: int) -> list[tuple[str, int]]:
    _need(data, offset, 0x1C, data_end, "CGFX DICT header")
    if data[offset : offset + 4] != b"DICT":
        raise ValueError("animation dictionary pointer does not target DICT")
    length = _u32(data, offset + 4, data_end)
    count = _u32(data, offset + 8, data_end)
    if count != expected_count or count > MAX_RESOURCES:
        raise ValueError("CGFX dictionary count mismatch or safety limit exceeded")
    minimum_length = 0x1C + 16 * count  # 12-byte fixed header plus 16-byte root node
    if length < minimum_length:
        raise ValueError("CGFX dictionary is too short for its declared entries")
    _need(data, offset, length, data_end, "CGFX DICT")
    result = []
    for index in range(count):
        node = offset + 0x1C + 16 * index
        name_target = _relative_target(data, node + 8, data_end)
        object_target = _relative_target(data, node + 12, data_end)
        if name_target is None or object_target is None:
            raise ValueError("CGFX animation dictionary entry has a null name/object")
        name = _cstring(data, name_target, data_end)
        result.append((name, object_target))
    return result


def _parse_canm(data: bytes, offset: int, data_end: int, kind: str, dictionary_name: str) -> dict:
    _need(data, offset, 0x28, data_end, "CANM header")
    if data[offset : offset + 4] != b"CANM":
        raise ValueError("animation dictionary object is not CANM")
    revision = _u32(data, offset + 4, data_end)
    name_target = _relative_target(data, offset + 8, data_end)
    _relative_target(data, offset + 12, data_end)  # validate target-group pointer, do not export its text
    name = _cstring(data, name_target, data_end) if name_target is not None else dictionary_name
    frame_count = struct.unpack_from("<f", data, offset + 20)[0]
    member_count = _u32(data, offset + 24, data_end)
    member_dictionary = _relative_target(data, offset + 28, data_end)
    if not math.isfinite(frame_count) or frame_count < 0 or frame_count > 10_000_000:
        raise ValueError("CANM frame count outside safety limit")
    if member_count > MAX_RESOURCES:
        raise ValueError("CANM track count exceeds safety limit")
    if member_count:
        if member_dictionary is None:
            raise ValueError("CANM has tracks but no member dictionary")
        _parse_dictionary(data, member_dictionary, member_count, data_end)
    return {
        "kind": kind,
        "name": name,
        "frames": frame_count,
        "track_count": member_count,
    }


def parse_bam_inventory(bam: bytes, asset_path: str) -> dict:
    """Validate this title BAM wrapper and return only CGFX/CANM metadata."""
    if len(bam) < 0x100 or bam[:4] != b"ATBC":
        raise ValueError(f"{asset_path}: invalid ATBC wrapper")
    if _u32(bam, 4) != len(bam):
        raise ValueError(f"{asset_path}: ATBC declared size mismatch")
    mdlsign_offset = _u32(bam, 0x14)
    if mdlsign_offset < 0x20 or mdlsign_offset > len(bam) - 0x10:
        raise ValueError(f"{asset_path}: invalid MDLSIGN offset")
    if bam[mdlsign_offset : mdlsign_offset + 7] != b"MDLSIGN":
        raise ValueError(f"{asset_path}: MDLSIGN pointer/tag mismatch")
    cgfx_size = _u32(bam, mdlsign_offset + 8)
    cgfx_offset = mdlsign_offset + 0x80
    _need(bam, cgfx_offset, cgfx_size, what="embedded CGFX")
    if cgfx_offset + cgfx_size != len(bam):
        raise ValueError(f"{asset_path}: embedded CGFX does not end at BAM boundary")
    metadata = parse_cgfx(bam[cgfx_offset : cgfx_offset + cgfx_size])
    metadata["path"] = asset_path
    return metadata


def inventory_cci(cci_path: Path, index_path: Path) -> list[dict]:
    """Read and verify two title BAMs from a decrypted CCI, without extracting."""
    index = json.loads(Path(index_path).read_text(encoding="utf-8"))
    if not isinstance(index, list):
        raise ValueError("RomFS index root must be a list")
    with Path(cci_path).open("rb") as stream:
        file_size = Path(cci_path).stat().st_size
        ncsd = _read_exact_at(stream, file_size, 0, 0x200)
        if ncsd[0x100:0x104] != b"NCSD":
            raise ValueError("CCI does not contain NCSD at offset 0x100")
        partition_lba = _u32(ncsd, 0x120)
        partition_offset = partition_lba * SECTOR_SIZE
        ncch = _read_exact_at(stream, file_size, partition_offset, 0x200)
        layout = parse_cci_layout(ncsd, ncch, file_size)

        anchor = _index_entry(index, TITLE_TABLE_PATH)
        if anchor["romfs_offset"] > layout["romfs_size"] or anchor["size"] > layout["romfs_size"] - anchor["romfs_offset"]:
            raise ValueError("TitleTable.tbb range exceeds RomFS")
        anchor_bytes = _read_exact_at(
            stream,
            file_size,
            layout["romfs_file_offset"] + anchor["romfs_offset"],
            anchor["size"],
        )
        anchor_sha256 = hashlib.sha256(anchor_bytes).hexdigest()
        if anchor_sha256.lower() != EXPECTED_TITLE_TABLE_SHA256:
            raise ValueError("TitleTable.tbb SHA-256 anchor mismatch")

        results = []
        for path in TITLE_BAM_PATHS:
            entry = _index_entry(index, path)
            if entry["romfs_offset"] > layout["romfs_size"] or entry["size"] > layout["romfs_size"] - entry["romfs_offset"]:
                raise ValueError(f"{path} range exceeds RomFS")
            data = _read_exact_at(
                stream,
                file_size,
                layout["romfs_file_offset"] + entry["romfs_offset"],
                entry["size"],
            )
            results.append(parse_bam_inventory(data, path))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cci", required=True, type=Path, help="decrypted CCI input; read-only")
    parser.add_argument("--romfs-index", required=True, type=Path, help="existing romfs_index.json")
    args = parser.parse_args()
    for asset in inventory_cci(args.cci, args.romfs_index):
        print(f"{asset['path']}: {asset['animation_count']} animations, {asset['track_count']} tracks")
        for animation in asset["animations"]:
            print(
                f"  {animation['kind']}: {animation['name']} | {animation['frames']:g} frames, "
                f"{animation['track_count']} tracks"
            )


if __name__ == "__main__":
    main()
