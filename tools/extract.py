#!/usr/bin/env python3
"""
CIA Decryptor, 3DS BLZ (.code) Decompressor, and RomFS Extractor
for Shin Megami Tensei IV (CTR-P-AMXE / 00040000000E5C00).
"""

import argparse
import hashlib
import json
import struct
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Util import Counter


def rol128(val: int, shift: int) -> int:
    return ((val << shift) | (val >> (128 - shift))) & ((1 << 128) - 1)


def derive_normal_key(key_x: bytes, key_y: bytes, generator: bytes) -> bytes:
    kx = int.from_bytes(key_x, "big")
    ky = int.from_bytes(key_y, "big")
    gen = int.from_bytes(generator, "big")
    res = rol128((rol128(kx, 2) ^ ky) + gen, 87)
    return res.to_bytes(16, "big")


def load_aes_keys(path: Path) -> dict[str, bytes]:
    keys: dict[str, bytes] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            keys[k.strip()] = bytes.fromhex(v.strip())
    return keys


def decompress_blz(data: bytes) -> bytes:
    """Decompresses Nintendo 3DS Backward LZ77 (BLZ) compressed .code data."""
    if len(data) < 8:
        return data

    hdr_and_comp, inc_size = struct.unpack_from("<II", data, len(data) - 8)
    comp_size = hdr_and_comp & 0xFFFFFF
    hdr_size = (hdr_and_comp >> 24) & 0xFF
    total_size = len(data) + inc_size
    prefix_len = len(data) - comp_size

    out = bytearray(total_size)
    out[:prefix_len] = data[:prefix_len]

    src_pos = len(data) - hdr_size
    dst_pos = total_size

    # Local bindings for fast tight loop in Python
    src = memoryview(data)
    while dst_pos > prefix_len and src_pos > prefix_len:
        src_pos -= 1
        flags = src[src_pos]
        for bit in range(8):
            if dst_pos <= prefix_len or src_pos <= prefix_len:
                break
            if (flags & (0x80 >> bit)) == 0:
                src_pos -= 1
                dst_pos -= 1
                out[dst_pos] = src[src_pos]
            else:
                src_pos -= 2
                pair = (src[src_pos + 1] << 8) | src[src_pos]
                length = (pair >> 12) + 3
                disp = (pair & 0xFFF) + 3
                # Copy backwards: source in out is dst_pos + disp - 1
                for _ in range(length):
                    dst_pos -= 1
                    out[dst_pos] = out[dst_pos + disp]

    return bytes(out)


def _align64(val: int) -> int:
    return (val + 63) & ~63


class CIAExtractor:
    """Decrypts and extracts ExeFS, ExHeader, and RomFS from a 3DS CIA image."""

    def __init__(self, cia_path: Path, keys_path: Path):
        self.cia_path = Path(cia_path)
        self.keys = load_aes_keys(Path(keys_path))
        self._parse_headers()

    def _parse_headers(self) -> None:
        with open(self.cia_path, "rb") as f:
            hdr = f.read(0x20)
            (
                hdr_size,
                self.cia_type,
                self.cia_ver,
                cert_size,
                tik_size,
                tmd_size,
                meta_size,
                self.content_size,
            ) = struct.unpack("<IHHIIIIQ", hdr)

            cert_off = _align64(hdr_size)
            tik_off = cert_off + _align64(cert_size)
            tmd_off = tik_off + _align64(tik_size)
            self.content_off = tmd_off + _align64(tmd_size)

            f.seek(tik_off)
            tik = f.read(tik_size)
            enc_title_key = tik[0x1BF:0x1CF]
            self.title_id = tik[0x1DC:0x1E4]

            common_key = derive_normal_key(
                self.keys["slot0x3DKeyX"], self.keys["common0"], self.keys["generator"]
            )
            self.title_key = AES.new(
                common_key, AES.MODE_CBC, iv=self.title_id + b"\x00" * 8
            ).decrypt(enc_title_key)

            # Decrypt NCCH header of Content 0
            f.seek(self.content_off)
            ncch_raw = f.read(0x200)
            self.ncch_hdr = AES.new(
                self.title_key, AES.MODE_CBC, iv=b"\x00" * 16
            ).decrypt(ncch_raw)

            if self.ncch_hdr[0x100:0x104] != b"NCCH":
                raise ValueError("Failed to decrypt NCCH header: invalid magic")

            self.key_y = self.ncch_hdr[:16]
            self.ncch_key = derive_normal_key(
                self.keys["slot0x2CKeyX"], self.key_y, self.keys["generator"]
            )
            self.partition_id_rev = self.ncch_hdr[0x108:0x110][::-1]
            self.product_code = (
                self.ncch_hdr[0x150:0x160].rstrip(b"\x00").decode("ascii", "ignore")
            )
            self.exefs_off = struct.unpack_from("<I", self.ncch_hdr, 0x1A0)[0] * 0x200
            self.exefs_size = struct.unpack_from("<I", self.ncch_hdr, 0x1A4)[0] * 0x200
            self.romfs_off = struct.unpack_from("<I", self.ncch_hdr, 0x1B0)[0] * 0x200
            self.romfs_size = struct.unpack_from("<I", self.ncch_hdr, 0x1B4)[0] * 0x200

    def read_ncch_section(
        self, section_base: int, section_type: int, rel_offset: int, size: int
    ) -> bytes:
        """
        Reads and double-decrypts (outer TitleKey AES-CBC + inner NCCH AES-CTR)
        an arbitrary byte range [rel_offset, rel_offset + size) within an NCCH section.
        """
        abs_ncch_start = section_base + rel_offset
        block_start = abs_ncch_start & ~0xF
        pad_head = abs_ncch_start - block_start
        aligned_len = (pad_head + size + 15) & ~0xF

        with open(self.cia_path, "rb") as f:
            if block_start == 0:
                iv = b"\x00" * 16
                f.seek(self.content_off)
            else:
                f.seek(self.content_off + block_start - 16)
                iv = f.read(16)
            enc_data = f.read(aligned_len)

        cbc_dec = AES.new(self.title_key, AES.MODE_CBC, iv=iv).decrypt(enc_data)

        rel_block_start = block_start - section_base
        ctr_prefix = self.partition_id_rev + bytes([section_type]) + b"\x00" * 7
        init_val = int.from_bytes(ctr_prefix, "big") + (rel_block_start >> 4)
        ctr = Counter.new(128, initial_value=init_val)
        ctr_dec = AES.new(self.ncch_key, AES.MODE_CTR, counter=ctr).decrypt(cbc_dec)

        return ctr_dec[pad_head : pad_head + size]

    def extract_exefs(self, out_dir: Path) -> dict:
        out_dir = Path(out_dir)
        exefs_dir = out_dir / "exefs"
        exefs_dir.mkdir(parents=True, exist_ok=True)

        exhdr = self.read_ncch_section(0x200, 1, 0, 0x800)
        (out_dir / "exheader.bin").write_bytes(exhdr)

        app_title = exhdr[:8].rstrip(b"\x00").decode("ascii", "ignore")
        sci_flags = exhdr[0xD]
        is_compressed = bool(sci_flags & 1)
        text_addr, text_pages, text_size = struct.unpack_from("<III", exhdr, 0x10)
        ro_addr, ro_pages, ro_size = struct.unpack_from("<III", exhdr, 0x20)
        data_addr, data_pages, data_size = struct.unpack_from("<III", exhdr, 0x30)
        bss_size = struct.unpack_from("<I", exhdr, 0x3C)[0]

        code_out = exefs_dir / "code.bin"
        exefs_raw = self.read_ncch_section(self.exefs_off, 2, 0, self.exefs_size)
        exefs_hdr = exefs_raw[:0x200]

        for i in range(10):
            entry = exefs_hdr[i * 16 : (i + 1) * 16]
            name = entry[:8].rstrip(b"\x00").decode("ascii", "ignore")
            if not name:
                continue
            f_off, f_size = struct.unpack_from("<II", entry, 8)
            file_bytes = exefs_raw[0x200 + f_off : 0x200 + f_off + f_size]
            if name == ".code":
                if code_out.exists() and code_out.stat().st_size == 0x377000:
                    decomp_code = code_out.read_bytes()
                else:
                    decomp_code = (
                        decompress_blz(file_bytes) if is_compressed else file_bytes
                    )
                    code_out.write_bytes(decomp_code)
            else:
                (exefs_dir / f"{name}.bin").write_bytes(file_bytes)

        code_sha256 = hashlib.sha256(code_out.read_bytes()).hexdigest()
        info = {
            "product_code": self.product_code,
            "app_title": app_title,
            "compressed_code": is_compressed,
            "code_sha256": code_sha256,
            "text": {"vaddr": text_addr, "size": text_size, "pages": text_pages},
            "rodata": {"vaddr": ro_addr, "size": ro_size, "pages": ro_pages},
            "data": {"vaddr": data_addr, "size": data_size, "pages": data_pages},
            "bss": {"size": bss_size},
        }
        (out_dir / "exefs_info.json").write_text(
            json.dumps(info, indent=2), encoding="utf-8"
        )
        return info

    def build_romfs_index(self, out_dir: Path) -> list[dict]:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        index_file = out_dir / "romfs_index.json"
        if index_file.exists():
            return json.loads(index_file.read_text(encoding="utf-8"))

        # Read first 2 MB of RomFS to parse Level 3 metadata tables
        meta_chunk = self.read_ncch_section(self.romfs_off, 3, 0, 0x200000)
        if meta_chunk[:4] != b"IVFC":
            raise ValueError("Invalid RomFS IVFC magic")

        l3_off = 0x1000
        (
            hdr_len,
            dir_hash_off,
            dir_hash_len,
            dir_meta_off,
            dir_meta_len,
            file_hash_off,
            file_hash_len,
            file_meta_off,
            file_meta_len,
            file_data_off,
        ) = struct.unpack_from("<10I", meta_chunk, l3_off)

        dir_tab = meta_chunk[l3_off + dir_meta_off : l3_off + dir_meta_off + dir_meta_len]
        file_tab = meta_chunk[
            l3_off + file_meta_off : l3_off + file_meta_off + file_meta_len
        ]

        entries: list[dict] = []

        def walk_dir(d_off: int, prefix: str = "") -> None:
            parent, sibling, child_dir, child_file, next_hash, name_len = (
                struct.unpack_from("<6I", dir_tab, d_off)
            )
            name = dir_tab[d_off + 24 : d_off + 24 + name_len].decode(
                "utf-16le", "ignore"
            )
            path_str = f"{prefix}/{name}" if name else ""

            f_off = child_file
            while f_off != 0xFFFFFFFF:
                f_parent, f_sib, f_data_off, f_data_len, f_hash, f_name_len = (
                    struct.unpack_from("<IIQQII", file_tab, f_off)
                )
                f_name = file_tab[f_off + 32 : f_off + 32 + f_name_len].decode(
                    "utf-16le", "ignore"
                )
                entries.append(
                    {
                        "path": f"{path_str}/{f_name}",
                        "romfs_offset": l3_off + file_data_off + f_data_off,
                        "size": f_data_len,
                    }
                )
                f_off = f_sib

            c_dir = child_dir
            while c_dir != 0xFFFFFFFF:
                walk_dir(c_dir, path_str)
                _, c_dir, _, _, _, _ = struct.unpack_from("<6I", dir_tab, c_dir)

        walk_dir(0)
        index_file.write_text(json.dumps(entries, indent=2), encoding="utf-8")
        return entries

    def extract_romfs_files(
        self,
        out_dir: Path,
        filter_exts: list[str] | None = None,
        filter_dirs: list[str] | None = None,
    ) -> int:
        out_dir = Path(out_dir)
        entries = self.build_romfs_index(out_dir.parent)
        count = 0
        for item in entries:
            rel_path: str = item["path"]
            if filter_dirs and not any(rel_path.startswith(d) for d in filter_dirs):
                continue
            if filter_exts and not any(
                rel_path.lower().endswith(ext.lower()) for ext in filter_exts
            ):
                continue

            dest = out_dir / rel_path.lstrip("/")
            dest.parent.mkdir(parents=True, exist_ok=True)
            data = self.read_ncch_section(
                self.romfs_off, 3, item["romfs_offset"], item["size"]
            )
            dest.write_bytes(data)
            count += 1
        return count


def verify_extracted_code(code_path: Path, game_info_path: Path) -> bool:
    code_path = Path(code_path)
    game_info = json.loads(Path(game_info_path).read_text(encoding="utf-8"))
    if not code_path.exists():
        return False
    data = code_path.read_bytes()
    if len(data) != game_info["code_bin_size"]:
        return False
    actual_sha = hashlib.sha256(data).hexdigest()
    return actual_sha.lower() == game_info["code_sha256"].lower()


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract SMT4 CIA for decompilation")
    parser.add_argument("--cia", type=Path, default=None, help="Path to CIA file")
    parser.add_argument(
        "--keys", type=Path, default=Path("aes_keys.txt"), help="Path to aes_keys.txt"
    )
    parser.add_argument(
        "--out", type=Path, default=Path("extracted"), help="Output directory"
    )
    parser.add_argument(
        "--info",
        type=Path,
        default=Path("config/game_info.json"),
        help="Path to game_info.json",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify extracted code.bin size and SHA-256 against config/game_info.json",
    )
    parser.add_argument(
        "--romfs-dirs",
        nargs="*",
        default=["/saveLoadUI", "/saveLoadER", "/shop", "/status", "/title"],
        help="RomFS directory prefixes to extract",
    )
    parser.add_argument(
        "--romfs-exts",
        nargs="*",
        default=None,
        help="RomFS extensions to extract (e.g. .tbb .bf)",
    )
    parser.add_argument(
        "--all", action="store_true", help="Extract all 20,126 RomFS files"
    )
    args = parser.parse_args()

    if args.check:
        ok = verify_extracted_code(args.out / "exefs" / "code.bin", args.info)
        if not ok:
            raise SystemExit("Verification FAILED: code.bin does not match game_info.json")
        print("Verification OK: extracted/exefs/code.bin matches expected SHA-256.")
        return

    cia_path = args.cia or next(Path(".").glob("*.cia"))
    extractor = CIAExtractor(cia_path, args.keys)
    info = extractor.extract_exefs(args.out)
    print(
        f"Extracted ExeFS: {info['product_code']} ({info['app_title'].strip()}), code.bin SHA-256: {info['code_sha256']}"
    )
    index = extractor.build_romfs_index(args.out)
    print(f"Indexed {len(index)} RomFS files.")
    if args.all:
        n = extractor.extract_romfs_files(args.out / "romfs")
    else:
        n = extractor.extract_romfs_files(
            args.out / "romfs",
            filter_exts=args.romfs_exts,
            filter_dirs=args.romfs_dirs,
        )
    print(f"Extracted {n} RomFS files to {args.out / 'romfs'}.")


if __name__ == "__main__":
    main()
