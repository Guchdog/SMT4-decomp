"""Link the bounded H3 entry candidate's two known ARM call relocations."""
from __future__ import annotations
import struct

TARGETS = {
    "h3_original_save_load_ui_calc": 0x00202950,
    "h3_original_get_presentation_point": 0x002BF6D0,
}
R_ARM_CALL = 28

def relocate_h3_entry(code: bytes, relocations, base: int) -> tuple[bytes, list[dict]]:
    out=bytearray(code); rows=[]
    for reloc in relocations:
        if reloc.relocation_type != R_ARM_CALL or reloc.symbol_name not in TARGETS:
            raise ValueError(f"unsupported H3 entry relocation: {reloc}")
        target=TARGETS[reloc.symbol_name]
        source=base+reloc.offset
        displacement=target-(source+8)
        if base&3 or source&3 or target&1 or displacement&3 or not -(1<<25)<=displacement<(1<<25):
            raise ValueError(f"unsafe ARM call relocation {source:#x}->{target:#x}")
        word=struct.unpack_from('<I',out,reloc.offset)[0]
        if word&0x0f000000 != 0x0b000000:
            raise ValueError(f"R_ARM_CALL site is not BL: {word:#010x}")
        linked=0xeb000000|((displacement>>2)&0xffffff)
        struct.pack_into('<I',out,reloc.offset,linked)
        rows.append({'offset':hex(reloc.offset),'symbol':reloc.symbol_name,'source':hex(source),'target':hex(target),'word':hex(linked)})
    if len(rows)!=2: raise ValueError(f"expected exactly two calls, got {len(rows)}")
    return bytes(out),rows
