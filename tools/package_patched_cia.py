import struct, hashlib, subprocess, time
from pathlib import Path

ROOT = Path(r"C:\Users\altair\.codex\worktrees\semantic-equivalence-experiment\SMT4decomp")
STAGING = Path(r"E:\SMT4decomp\build\cia-staging")
STAGING.mkdir(parents=True, exist_ok=True)

EXTRACTED = Path(r"E:\SMT4decomp\extracted")
PATCHED_CODE = Path(r"E:\SMT4decomp\build\codex-h19-check\final-rebuild-v15\h19\code.h19-final.bin")
MAKEROM = Path(r"E:\emulador3ds\makerom.exe")
ROMFS_BIN = STAGING / "romfs.bin"
PLAINRGN_BIN = STAGING / "plainrgn.bin"
OUT_NCCH = STAGING / "patched_ncch0.bin"
OUT_CIA = STAGING / "Shin_Megami_Tensei_IV_Patched.cia"

def align(val, alignment=512):
    return (val + (alignment - 1)) & ~(alignment - 1)

def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()

def build_exefs(code_bytes, banner_bytes, icon_bytes, logo_bytes):
    # 4 files
    files = [
        (b".code\x00\x00\x00", code_bytes),
        (b"banner\x00\x00", banner_bytes),
        (b"icon\x00\x00\x00\x00", icon_bytes),
        (b"logo\x00\x00\x00\x00", logo_bytes),
    ]
    
    header = bytearray(0x200)
    current_off = 0
    offsets_and_sizes = []
    
    for i, (name, data) in enumerate(files):
        sz = len(data)
        struct.pack_into("<8sII", header, i * 16, name, current_off, sz)
        offsets_and_sizes.append((current_off, sz, data))
        current_off = align(current_off + sz, 512)
        
    # Hashes are stored in reverse order at 0xC0..0x200
    # Hash 0 is at 0x200 - 32, Hash 1 at 0x200 - 64, etc.
    for i, (name, data) in enumerate(files):
        h = sha256(data)
        slot = 0x200 - (i + 1) * 32
        header[slot : slot + 32] = h
        
    # Assemble exefs
    exefs_body = bytearray(current_off)
    for off, sz, data in offsets_and_sizes:
        exefs_body[off : off + sz] = data
        
    return bytes(header) + bytes(exefs_body)

def main():
    print("Reading inputs...")
    code_bytes = PATCHED_CODE.read_bytes()
    banner_bytes = (EXTRACTED / "exefs/banner.bin").read_bytes()
    icon_bytes = (EXTRACTED / "exefs/icon.bin").read_bytes()
    logo_bytes = (EXTRACTED / "exefs/logo.bin").read_bytes()
    exheader_raw = bytearray((EXTRACTED / "exheader.bin").read_bytes())
    plainrgn_bytes = PLAINRGN_BIN.read_bytes()
    
    # 1. Update ExHeader: uncompressed code bit (sci_flags at 0xD bit 0 = 0)
    exheader_raw[0xD] &= ~1
    exheader_bytes = bytes(exheader_raw)
    exheader_hash = sha256(exheader_bytes[:0x400])
    
    # 2. Build ExeFS
    print("Building ExeFS...")
    exefs_bytes = build_exefs(code_bytes, banner_bytes, icon_bytes, logo_bytes)
    exefs_hash = sha256(exefs_bytes[:0x200])
    exefs_media_units = len(exefs_bytes) // 512
    
    # 3. Read template NCCH Header from ncch0.bin
    ncch0_template = open(STAGING / "ncch0.bin", "rb")
    ncch_hdr = bytearray(ncch0_template.read(0x200))
    
    # Plain region offset: 0x5 (byte 0xa00), size: 1 unit
    # ExeFS offset: 0x6 (byte 0xc00), size: exefs_media_units
    exefs_off_mu = 6
    romfs_off_mu = align(exefs_off_mu + exefs_media_units, 16) # align to 8KB (16 media units)
    
    romfs_sz_mu = struct.unpack_from("<I", ncch_hdr, 0x1B4)[0]
    content_sz_mu = romfs_off_mu + romfs_sz_mu
    
    # Update NCCH header fields:
    # 0x104: Content size in media units
    struct.pack_into("<I", ncch_hdr, 0x104, content_sz_mu)
    # 0x160: ExHeader hash
    ncch_hdr[0x160 : 0x180] = exheader_hash
    # 0x1A0: ExeFS offset, size in media units
    struct.pack_into("<II", ncch_hdr, 0x1A0, exefs_off_mu, exefs_media_units)
    # 0x1B0: RomFS offset, size in media units
    struct.pack_into("<II", ncch_hdr, 0x1B0, romfs_off_mu, romfs_sz_mu)
    # 0x1C0: ExeFS hash
    ncch_hdr[0x1C0 : 0x1E0] = exefs_hash
    
    print(f"ExeFS size: {len(exefs_bytes)} bytes ({exefs_media_units} MU)")
    print(f"RomFS offset: {romfs_off_mu} MU (byte {romfs_off_mu * 512:#x})")
    print(f"Total NCCH Content Size: {content_sz_mu} MU ({content_sz_mu * 512 / (1024*1024):.2f} MB)")
    
    # 4. Stream-write the patched NCCH
    print(f"Writing {OUT_NCCH}...")
    t0 = time.time()
    with open(OUT_NCCH, "wb") as fout:
        # 0x000..0x200: NCCH Header
        fout.write(ncch_hdr)
        # 0x200..0xA00: ExHeader
        fout.write(exheader_bytes)
        # 0xA00..0xC00: Plain Region
        fout.write(plainrgn_bytes)
        # 0xC00..: ExeFS
        fout.write(exefs_bytes)
        # Padding up to romfs_off_mu * 512
        padding = (romfs_off_mu * 512) - fout.tell()
        if padding > 0:
            fout.write(b"\x00" * padding)
        # RomFS stream copy
        print("Copying RomFS...")
        with open(ROMFS_BIN, "rb") as fromfs:
            chunk = 32 * 1024 * 1024
            while True:
                buf = fromfs.read(chunk)
                if not buf:
                    break
                fout.write(buf)
                
    print(f"Patched NCCH written in {time.time() - t0:.2f}s ({OUT_NCCH.stat().st_size} bytes)")
    
    # 5. Build CIA with makerom
    print("Building final CIA with makerom...")
    cmd = [
        str(MAKEROM),
        "-f", "cia",
        "-target", "t",
        "-ignoresign",
        "-content", f"{OUT_NCCH}:0:0x0000",
        "-o", str(OUT_CIA)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print("MAKEROM STDOUT:\n", res.stdout)
    if res.stderr:
        print("MAKEROM STDERR:\n", res.stderr)
    print("Exit code:", res.returncode)
    if OUT_CIA.exists():
        print(f"SUCCESS: Generated CIA at {OUT_CIA} ({OUT_CIA.stat().st_size} bytes)")

if __name__ == "__main__":
    main()
