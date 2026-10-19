#!/usr/bin/env python3
"""
SMT4 RomFS UI Table (.tbb / TBCR) and Atlus FlowScript (.bf / FLW0) Asset Inspector.
"""

import argparse
import struct
from pathlib import Path


def parse_tbb_header(data: bytes) -> dict:
    """
    Parses a Shin Megami Tensei IV .tbb table container (TBCR / TBL1).
    Header layout:
      0x00: 'TBCR' (4 bytes)
      0x04: header_size (u32, typically 0x10)
      0x08: table_count (u32)
      0x0C: reserved (u32)
    Followed by TBL1 sub-tables:
      0x00: 'TBL1' (4 bytes)
      0x04: table_size (u32)
      0x08: unknown/flags (u32)
      0x0C: row_size (u32)
    """
    if len(data) < 16:
        raise ValueError("Data too short for TBB header")

    magic = data[:4].decode("ascii", "ignore")
    hdr_size, table_count, reserved = struct.unpack_from("<III", data, 4)

    tables = []
    pos = hdr_size
    for _ in range(table_count):
        if pos + 16 > len(data):
            break
        sub_magic = data[pos : pos + 4].decode("ascii", "ignore")
        if sub_magic != "TBL1":
            break
        tbl_size, flags, row_size = struct.unpack_from("<III", data, pos + 4)
        payload_bytes = max(0, tbl_size - 16)
        row_count = (payload_bytes // row_size) if row_size > 0 else 0
        tables.append(
            {
                "magic": sub_magic,
                "offset": pos,
                "table_size": tbl_size,
                "row_size": row_size,
                "row_count": row_count,
            }
        )
        pos += (tbl_size + 15) & ~15

    return {
        "magic": magic,
        "header_size": hdr_size,
        "table_count": table_count,
        "tables": tables,
    }


def parse_bf_header(data: bytes) -> dict:
    """
    Parses an Atlus FlowScript (.bf / FLW0) binary header.
    Header layout:
      0x00: file_type (u8), compressed (u8), user_id (u16)
      0x04: file_size (u32)
      0x08: 'FLW0' (4 bytes)
      0x0C: reserved (u32)
      0x10: section_count (u32)
      0x14: local_int_vars (u16), local_flt_vars (u16)
      0x18: endianness/padding (8 bytes)
      0x20: section table (section_count * 16 bytes: section_type, element_size, count, offset)
    """
    if len(data) < 32:
        raise ValueError("Data too short for BF header")

    file_size = struct.unpack_from("<I", data, 4)[0]
    magic = data[8:12].decode("ascii", "ignore")
    section_count, local_ints, local_flts = struct.unpack_from("<IHH", data, 0x10)

    sections = []
    procedures = []
    for i in range(section_count):
        sec_off = 0x20 + i * 16
        if sec_off + 16 > len(data):
            break
        sec_type, elem_size, count, data_off = struct.unpack_from("<IIII", data, sec_off)
        sections.append(
            {
                "index": i,
                "type": sec_type,
                "element_size": elem_size,
                "count": count,
                "offset": data_off,
            }
        )
        # Section type 0 is Procedure Label table
        if sec_type == 0 and elem_size >= 32:
            for p_idx in range(count):
                p_pos = data_off + p_idx * elem_size
                if p_pos + elem_size <= len(data):
                    raw_name = data[p_pos : p_pos + 24].split(b"\x00", 1)[0]
                    proc_name = raw_name.decode("ascii", "ignore")
                    if proc_name:
                        procedures.append(proc_name)

    return {
        "magic": magic,
        "file_size": file_size,
        "section_count": section_count,
        "local_ints": local_ints,
        "local_floats": local_flts,
        "sections": sections,
        "procedures": procedures,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect SMT4 .tbb and .bf RomFS assets")
    parser.add_argument("paths", nargs="+", type=Path, help="Files to inspect")
    args = parser.parse_args()

    for p in args.paths:
        raw = p.read_bytes()
        if p.suffix.lower() == ".tbb":
            info = parse_tbb_header(raw)
            print(f"[TBB] {p}: magic={info['magic']}, tables={info['table_count']}, details={info['tables']}")
        elif p.suffix.lower() == ".bf":
            info = parse_bf_header(raw)
            print(
                f"[BF]  {p}: magic={info['magic']}, size={info['file_size']}, sections={info['section_count']}, procedures={info['procedures']}"
            )


if __name__ == "__main__":
    main()
