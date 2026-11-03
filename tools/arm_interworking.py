"""Relocate ARM calls to Thumb routines while preserving tail-call return state."""
import struct

def relocate_thumb_call(blob, offset, base, target, relocation_type, window_size):
    if target & 1 or target & 2 == 0:
        raise ValueError('expected an even halfword-aligned Thumb entry')
    site = base + offset
    if site & 3 or offset < 0 or offset + 4 > len(blob):
        raise ValueError('invalid ARM relocation site')
    if relocation_type not in (28, 29):
        raise ValueError('unsupported Thumb relocation')
    original = struct.unpack_from('<I', blob, offset)[0]
    expected = 0xEB000000 if relocation_type == 28 else 0xEA000000
    if original & 0xFF000000 != expected:
        raise ValueError('expected an unconditional ARM BL or B instruction')
    if relocation_type == 28:
        delta = target - (site + 8)
        if delta & 1 or not -(1 << 25) <= delta < (1 << 25):
            raise ValueError('Thumb call out of ARM BLX range')
        insn = 0xFA000000 | ((delta >> 2) & 0xFFFFFF) | ((delta & 2) << 23)
    elif relocation_type == 29:
        if len(blob) % 4 or len(blob) + 12 > window_size:
            raise ValueError('no room for ARM-Thumb tail-call veneer')
        veneer = base + len(blob)
        delta = veneer - (site + 8)
        if delta & 3 or not -(1 << 25) <= delta < (1 << 25):
            raise ValueError('veneer out of ARM branch range')
        insn = 0xEA000000 | ((delta >> 2) & 0xFFFFFF)
        blob.extend(struct.pack('<III', 0xE59FC000, 0xE12FFF1C, target | 1))
    else:
        raise ValueError('unsupported Thumb relocation')
    struct.pack_into('<I', blob, offset, insn)
