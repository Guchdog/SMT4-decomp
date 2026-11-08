#pragma once
#include "types.h"

namespace smt4::engine {

inline u32 Ld32(const u8* p) { return *reinterpret_cast<const u32*>(p); }
inline u16 Ld16(const u8* p) { return *reinterpret_cast<const u16*>(p); }
inline u8 Ld8(const u8* p) { return *p; }
inline void St32(u8* p, u32 v) { *reinterpret_cast<u32*>(p) = v; }
inline void St16(u8* p, u16 v) { *reinterpret_cast<u16*>(p) = v; }
inline void St8(u8* p, u8 v) { *p = v; }

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00170e20(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0;
    do {
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        r7 = Ld32(s + 8);
        r8 = Ld32(s + 12);
        s += Stride;
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r7);
        St32(d + 12, r8);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00170e3c(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, sb = 0, sl = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    r3 = Ld32(s + 0);
    r4 = Ld32(s + 4);
    r5 = Ld32(s + 8);
    r6 = Ld32(s + 12);
    s += Stride;
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    r5 = ip & (r5 >> 1);
    r6 = ip & (r6 >> 1);
    do {
        r7 = Ld32(s + 0);
        r8 = Ld32(s + 4);
        sb = Ld32(s + 8);
        sl = Ld32(s + 12);
        s += Stride;
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = ip & (sl >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        r5 = r5 + sb;
        r6 = r6 + sl;
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r5);
        St32(d + 12, r6);
        d += Stride;
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        r5 = Ld32(s + 8);
        r6 = Ld32(s + 12);
        s += Stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r5 = ip & (r5 >> 1);
        r6 = ip & (r6 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        sb = sb + r5;
        sl = sl + r6;
        St32(d + 0, r7);
        St32(d + 4, r8);
        St32(d + 8, sb);
        St32(d + 12, sl);
        d += Stride;
        n -= 2u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00170ecc(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    do {
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        r7 = Ld32(s + 8);
        r8 = Ld32(s + 12);
        sb = Ld8(s + 16);
        s += Stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        r3 = r3 + (r3 >> 8);
        r3 = r3 + (r4 << 24);
        r4 = r4 + (r4 >> 8);
        r4 = r4 + (r7 << 24);
        r7 = r7 + (r7 >> 8);
        r7 = r7 + (r8 << 24);
        r8 = r8 + (r8 >> 8);
        r8 = r8 + (sb << 24);
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r7);
        St32(d + 12, r8);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00170f24(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, sb = 0, sl = 0, ip = 0, lr = 0;
    ip = 0x7f7f7f7fU;
    r3 = Ld32(s + 0);
    r4 = Ld32(s + 4);
    r5 = Ld32(s + 8);
    r6 = Ld32(s + 12);
    lr = Ld8(s + 16);
    s += Stride;
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    r5 = ip & (r5 >> 1);
    r6 = ip & (r6 >> 1);
    lr = ip & (lr >> 1);
    r3 = r3 + (r3 >> 8);
    r3 = r3 + (r4 << 24);
    r4 = r4 + (r4 >> 8);
    r4 = r4 + (r5 << 24);
    r5 = r5 + (r5 >> 8);
    r5 = r5 + (r6 << 24);
    r6 = r6 + (r6 >> 8);
    r6 = r6 + (lr << 24);
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    r5 = ip & (r5 >> 1);
    r6 = ip & (r6 >> 1);
    do {
        r7 = Ld32(s + 0);
        r8 = Ld32(s + 4);
        sb = Ld32(s + 8);
        sl = Ld32(s + 12);
        lr = Ld8(s + 16);
        s += Stride;
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = ip & (sl >> 1);
        lr = ip & (lr >> 1);
        r7 = r7 + (r7 >> 8);
        r7 = r7 + (r8 << 24);
        r8 = r8 + (r8 >> 8);
        r8 = r8 + (sb << 24);
        sb = sb + (sb >> 8);
        sb = sb + (sl << 24);
        sl = sl + (sl >> 8);
        sl = sl + (lr << 24);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = ip & (sl >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        r5 = r5 + sb;
        r6 = r6 + sl;
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r5);
        St32(d + 12, r6);
        d += Stride;
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        r5 = Ld32(s + 8);
        r6 = Ld32(s + 12);
        lr = Ld8(s + 16);
        s += Stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r5 = ip & (r5 >> 1);
        r6 = ip & (r6 >> 1);
        lr = ip & (lr >> 1);
        r3 = r3 + (r3 >> 8);
        r3 = r3 + (r4 << 24);
        r4 = r4 + (r4 >> 8);
        r4 = r4 + (r5 << 24);
        r5 = r5 + (r5 >> 8);
        r5 = r5 + (r6 << 24);
        r6 = r6 + (r6 >> 8);
        r6 = r6 + (lr << 24);
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r5 = ip & (r5 >> 1);
        r6 = ip & (r6 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        sb = sb + r5;
        sl = sl + r6;
        St32(d + 0, r7);
        St32(d + 4, r8);
        St32(d + 8, sb);
        St32(d + 12, sl);
        d += Stride;
        n -= 2u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00171058(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0, sb = 0;
    s = s - 1;
    do {
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        r7 = Ld32(s + 8);
        r8 = Ld32(s + 12);
        sb = Ld8(s + 16);
        s += Stride;
        r3 = r3 >> 8;
        r3 = r3 + (r4 << 24);
        r4 = r4 >> 8;
        r4 = r4 + (r7 << 24);
        r7 = r7 >> 8;
        r7 = r7 + (r8 << 24);
        r8 = r8 >> 8;
        r8 = r8 + (sb << 24);
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r7);
        St32(d + 12, r8);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_0017109c(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, sb = 0, sl = 0, ip = 0, lr = 0;
    s = s - 1;
    ip = 0x7f7f7f7fU;
    r3 = Ld32(s + 0);
    r4 = Ld32(s + 4);
    r5 = Ld32(s + 8);
    r6 = Ld32(s + 12);
    lr = Ld8(s + 16);
    s += Stride;
    r3 = r3 >> 8;
    r3 = r3 + (r4 << 24);
    r4 = r4 >> 8;
    r4 = r4 + (r5 << 24);
    r5 = r5 >> 8;
    r5 = r5 + (r6 << 24);
    r6 = r6 >> 8;
    r6 = r6 + (lr << 24);
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    r5 = ip & (r5 >> 1);
    r6 = ip & (r6 >> 1);
    do {
        r7 = Ld32(s + 0);
        r8 = Ld32(s + 4);
        sb = Ld32(s + 8);
        sl = Ld32(s + 12);
        lr = Ld8(s + 16);
        s += Stride;
        r7 = r7 >> 8;
        r7 = r7 + (r8 << 24);
        r8 = r8 >> 8;
        r8 = r8 + (sb << 24);
        sb = sb >> 8;
        sb = sb + (sl << 24);
        sl = sl >> 8;
        sl = sl + (lr << 24);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = ip & (sl >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        r5 = r5 + sb;
        r6 = r6 + sl;
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r5);
        St32(d + 12, r6);
        d += Stride;
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        r5 = Ld32(s + 8);
        r6 = Ld32(s + 12);
        lr = Ld8(s + 16);
        s += Stride;
        r3 = r3 >> 8;
        r3 = r3 + (r4 << 24);
        r4 = r4 >> 8;
        r4 = r4 + (r5 << 24);
        r5 = r5 >> 8;
        r5 = r5 + (r6 << 24);
        r6 = r6 >> 8;
        r6 = r6 + (lr << 24);
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r5 = ip & (r5 >> 1);
        r6 = ip & (r6 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        sb = sb + r5;
        sl = sl + r6;
        St32(d + 0, r7);
        St32(d + 4, r8);
        St32(d + 8, sb);
        St32(d + 12, sl);
        d += Stride;
        n -= 2u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00171198(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0, sb = 0, sl = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s - 1;
    do {
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        r7 = Ld32(s + 8);
        r8 = Ld32(s + 12);
        sb = Ld16(s + 16);
        s += Stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = r3 >> 16;
        sl = sl + (r4 << 16);
        sl = sl + (r3 >> 8);
        r3 = sl + (r4 << 24);
        sl = r4 >> 16;
        sl = sl + (r7 << 16);
        sl = sl + (r4 >> 8);
        r4 = sl + (r7 << 24);
        sl = r7 >> 16;
        sl = sl + (r8 << 16);
        sl = sl + (r7 >> 8);
        r7 = sl + (r8 << 24);
        sl = r8 >> 16;
        sl = sl + (sb << 16);
        sl = sl + (r8 >> 8);
        r8 = sl + (sb << 24);
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r7);
        St32(d + 12, r8);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00171214(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, sb = 0, sl = 0, fp = 0, ip = 0, lr = 0;
    ip = 0x7f7f7f7fU;
    s = s - 1;
    r3 = Ld32(s + 0);
    r4 = Ld32(s + 4);
    r5 = Ld32(s + 8);
    r6 = Ld32(s + 12);
    lr = Ld16(s + 16);
    s += Stride;
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    r5 = ip & (r5 >> 1);
    r6 = ip & (r6 >> 1);
    lr = ip & (lr >> 1);
    fp = r3 >> 16;
    fp = fp + (r4 << 16);
    fp = fp + (r3 >> 8);
    r3 = fp + (r4 << 24);
    fp = r4 >> 16;
    fp = fp + (r5 << 16);
    fp = fp + (r4 >> 8);
    r4 = fp + (r5 << 24);
    fp = r5 >> 16;
    fp = fp + (r6 << 16);
    fp = fp + (r5 >> 8);
    r5 = fp + (r6 << 24);
    fp = r6 >> 16;
    fp = fp + (lr << 16);
    fp = fp + (r6 >> 8);
    r6 = fp + (lr << 24);
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    r5 = ip & (r5 >> 1);
    r6 = ip & (r6 >> 1);
    do {
        r7 = Ld32(s + 0);
        r8 = Ld32(s + 4);
        sb = Ld32(s + 8);
        sl = Ld32(s + 12);
        lr = Ld16(s + 16);
        s += Stride;
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = ip & (sl >> 1);
        lr = ip & (lr >> 1);
        fp = r7 >> 16;
        fp = fp + (r8 << 16);
        fp = fp + (r7 >> 8);
        r7 = fp + (r8 << 24);
        fp = r8 >> 16;
        fp = fp + (sb << 16);
        fp = fp + (r8 >> 8);
        r8 = fp + (sb << 24);
        fp = sb >> 16;
        fp = fp + (sl << 16);
        fp = fp + (sb >> 8);
        sb = fp + (sl << 24);
        fp = sl >> 16;
        fp = fp + (lr << 16);
        fp = fp + (sl >> 8);
        sl = fp + (lr << 24);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = ip & (sl >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        r5 = r5 + sb;
        r6 = r6 + sl;
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r5);
        St32(d + 12, r6);
        d += Stride;
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        r5 = Ld32(s + 8);
        r6 = Ld32(s + 12);
        lr = Ld16(s + 16);
        s += Stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r5 = ip & (r5 >> 1);
        r6 = ip & (r6 >> 1);
        lr = ip & (lr >> 1);
        fp = r3 >> 16;
        fp = fp + (r4 << 16);
        fp = fp + (r3 >> 8);
        r3 = fp + (r4 << 24);
        fp = r4 >> 16;
        fp = fp + (r5 << 16);
        fp = fp + (r4 >> 8);
        r4 = fp + (r5 << 24);
        fp = r5 >> 16;
        fp = fp + (r6 << 16);
        fp = fp + (r5 >> 8);
        r5 = fp + (r6 << 24);
        fp = r6 >> 16;
        fp = fp + (lr << 16);
        fp = fp + (r6 >> 8);
        r6 = fp + (lr << 24);
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r5 = ip & (r5 >> 1);
        r6 = ip & (r6 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        sb = sb + r5;
        sl = sl + r6;
        St32(d + 0, r7);
        St32(d + 4, r8);
        St32(d + 8, sb);
        St32(d + 12, sl);
        d += Stride;
        n -= 2u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_001713ac(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0, sb = 0;
    s = s + 2;
    do {
        r3 = Ld16(s - 2);
        r4 = Ld32(s + 0);
        r7 = Ld32(s + 4);
        r8 = Ld32(s + 8);
        sb = Ld16(s + 12);
        s += Stride;
        r3 = r3 + (r4 << 16);
        r4 = r4 >> 16;
        r4 = r4 + (r7 << 16);
        r7 = r7 >> 16;
        r7 = r7 + (r8 << 16);
        r8 = r8 >> 16;
        r8 = r8 + (sb << 16);
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r7);
        St32(d + 12, r8);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_001713f0(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, sb = 0, sl = 0, ip = 0, lr = 0;
    ip = 0x7f7f7f7fU;
    s = s + 2;
    r3 = Ld16(s - 2);
    r4 = Ld32(s + 0);
    r5 = Ld32(s + 4);
    r6 = Ld32(s + 8);
    lr = Ld16(s + 12);
    s += Stride;
    r3 = r3 + (r4 << 16);
    r4 = r4 >> 16;
    r4 = r4 + (r5 << 16);
    r5 = r5 >> 16;
    r5 = r5 + (r6 << 16);
    r6 = r6 >> 16;
    r6 = r6 + (lr << 16);
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    r5 = ip & (r5 >> 1);
    r6 = ip & (r6 >> 1);
    do {
        r7 = Ld16(s - 2);
        r8 = Ld32(s + 0);
        sb = Ld32(s + 4);
        sl = Ld32(s + 8);
        lr = Ld16(s + 12);
        s += Stride;
        r7 = r7 + (r8 << 16);
        r8 = r8 >> 16;
        r8 = r8 + (sb << 16);
        sb = sb >> 16;
        sb = sb + (sl << 16);
        sl = sl >> 16;
        sl = sl + (lr << 16);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = ip & (sl >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        r5 = r5 + sb;
        r6 = r6 + sl;
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r5);
        St32(d + 12, r6);
        d += Stride;
        r3 = Ld16(s - 2);
        r4 = Ld32(s + 0);
        r5 = Ld32(s + 4);
        r6 = Ld32(s + 8);
        lr = Ld16(s + 12);
        s += Stride;
        r3 = r3 + (r4 << 16);
        r4 = r4 >> 16;
        r4 = r4 + (r5 << 16);
        r5 = r5 >> 16;
        r5 = r5 + (r6 << 16);
        r6 = r6 >> 16;
        r6 = r6 + (lr << 16);
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r5 = ip & (r5 >> 1);
        r6 = ip & (r6 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        sb = sb + r5;
        sl = sl + r6;
        St32(d + 0, r7);
        St32(d + 4, r8);
        St32(d + 8, sb);
        St32(d + 12, sl);
        d += Stride;
        n -= 2u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_001714ec(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0, sb = 0, sl = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s + 2;
    do {
        r3 = Ld16(s - 2);
        r4 = Ld32(s + 0);
        r7 = Ld32(s + 4);
        r8 = Ld32(s + 8);
        sb = Ld32(s + 12);
        s += Stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = r3 + (r4 << 16);
        sl = sl + (r3 >> 8);
        r3 = sl + (r4 << 8);
        r4 = r4 >> 16;
        sl = r4 + (r7 << 16);
        sl = sl + (r4 >> 8);
        r4 = sl + (r7 << 8);
        r7 = r7 >> 16;
        sl = r7 + (r8 << 16);
        sl = sl + (r7 >> 8);
        r7 = sl + (r8 << 8);
        r8 = r8 >> 16;
        sl = r8 + (sb << 16);
        sl = sl + (r8 >> 8);
        r8 = sl + (sb << 8);
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r7);
        St32(d + 12, r8);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00171564(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, sb = 0, sl = 0, fp = 0, ip = 0, lr = 0;
    ip = 0x7f7f7f7fU;
    s = s + 2;
    r3 = Ld16(s - 2);
    r4 = Ld32(s + 0);
    r5 = Ld32(s + 4);
    r6 = Ld32(s + 8);
    lr = Ld32(s + 12);
    s += Stride;
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    r5 = ip & (r5 >> 1);
    r6 = ip & (r6 >> 1);
    lr = ip & (lr >> 1);
    fp = r3 + (r4 << 16);
    fp = fp + (r3 >> 8);
    r3 = fp + (r4 << 8);
    r4 = r4 >> 16;
    fp = r4 + (r5 << 16);
    fp = fp + (r4 >> 8);
    r4 = fp + (r5 << 8);
    r5 = r5 >> 16;
    fp = r5 + (r6 << 16);
    fp = fp + (r5 >> 8);
    r5 = fp + (r6 << 8);
    r6 = r6 >> 16;
    fp = r6 + (lr << 16);
    fp = fp + (r6 >> 8);
    r6 = fp + (lr << 8);
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    r5 = ip & (r5 >> 1);
    r6 = ip & (r6 >> 1);
    do {
        r7 = Ld16(s - 2);
        r8 = Ld32(s + 0);
        sb = Ld32(s + 4);
        sl = Ld32(s + 8);
        lr = Ld32(s + 12);
        s += Stride;
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = ip & (sl >> 1);
        lr = ip & (lr >> 1);
        fp = r7 + (r8 << 16);
        fp = fp + (r7 >> 8);
        r7 = fp + (r8 << 8);
        r8 = r8 >> 16;
        fp = r8 + (sb << 16);
        fp = fp + (r8 >> 8);
        r8 = fp + (sb << 8);
        sb = sb >> 16;
        fp = sb + (sl << 16);
        fp = fp + (sb >> 8);
        sb = fp + (sl << 8);
        sl = sl >> 16;
        fp = sl + (lr << 16);
        fp = fp + (sl >> 8);
        sl = fp + (lr << 8);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = ip & (sl >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        r5 = r5 + sb;
        r6 = r6 + sl;
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r5);
        St32(d + 12, r6);
        d += Stride;
        r3 = Ld16(s - 2);
        r4 = Ld32(s + 0);
        r5 = Ld32(s + 4);
        r6 = Ld32(s + 8);
        lr = Ld32(s + 12);
        s += Stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r5 = ip & (r5 >> 1);
        r6 = ip & (r6 >> 1);
        lr = ip & (lr >> 1);
        fp = r3 + (r4 << 16);
        fp = fp + (r3 >> 8);
        r3 = fp + (r4 << 8);
        r4 = r4 >> 16;
        fp = r4 + (r5 << 16);
        fp = fp + (r4 >> 8);
        r4 = fp + (r5 << 8);
        r5 = r5 >> 16;
        fp = r5 + (r6 << 16);
        fp = fp + (r5 >> 8);
        r5 = fp + (r6 << 8);
        r6 = r6 >> 16;
        fp = r6 + (lr << 16);
        fp = fp + (r6 >> 8);
        r6 = fp + (lr << 8);
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r5 = ip & (r5 >> 1);
        r6 = ip & (r6 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        sb = sb + r5;
        sl = sl + r6;
        St32(d + 0, r7);
        St32(d + 4, r8);
        St32(d + 8, sb);
        St32(d + 12, sl);
        d += Stride;
        n -= 2u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_001716f0(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0, sb = 0;
    s = s + 1;
    do {
        r3 = Ld8(s - 1);
        r4 = Ld32(s + 0);
        r7 = Ld32(s + 4);
        r8 = Ld32(s + 8);
        sb = Ld32(s + 12);
        s += Stride;
        r3 = r3 + (r4 << 8);
        r4 = r4 >> 24;
        r4 = r4 + (r7 << 8);
        r7 = r7 >> 24;
        r7 = r7 + (r8 << 8);
        r8 = r8 >> 24;
        r8 = r8 + (sb << 8);
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r7);
        St32(d + 12, r8);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00171730(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, sb = 0, sl = 0, ip = 0, lr = 0;
    ip = 0x7f7f7f7fU;
    s = s + 1;
    r3 = Ld8(s - 1);
    r4 = Ld32(s + 0);
    r5 = Ld32(s + 4);
    r6 = Ld32(s + 8);
    lr = Ld32(s + 12);
    s += Stride;
    r3 = r3 + (r4 << 8);
    r4 = r4 >> 24;
    r4 = r4 + (r5 << 8);
    r5 = r5 >> 24;
    r5 = r5 + (r6 << 8);
    r6 = r6 >> 24;
    r6 = r6 + (lr << 8);
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    r5 = ip & (r5 >> 1);
    r6 = ip & (r6 >> 1);
    do {
        r7 = Ld8(s - 1);
        r8 = Ld32(s + 0);
        sb = Ld32(s + 4);
        sl = Ld32(s + 8);
        lr = Ld32(s + 12);
        s += Stride;
        r7 = r7 + (r8 << 8);
        r8 = r8 >> 24;
        r8 = r8 + (sb << 8);
        sb = sb >> 24;
        sb = sb + (sl << 8);
        sl = sl >> 24;
        sl = sl + (lr << 8);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = ip & (sl >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        r5 = r5 + sb;
        r6 = r6 + sl;
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r5);
        St32(d + 12, r6);
        d += Stride;
        r3 = Ld8(s - 1);
        r4 = Ld32(s + 0);
        r5 = Ld32(s + 4);
        r6 = Ld32(s + 8);
        lr = Ld32(s + 12);
        s += Stride;
        r3 = r3 + (r4 << 8);
        r4 = r4 >> 24;
        r4 = r4 + (r5 << 8);
        r5 = r5 >> 24;
        r5 = r5 + (r6 << 8);
        r6 = r6 >> 24;
        r6 = r6 + (lr << 8);
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r5 = ip & (r5 >> 1);
        r6 = ip & (r6 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        sb = sb + r5;
        sl = sl + r6;
        St32(d + 0, r7);
        St32(d + 4, r8);
        St32(d + 8, sb);
        St32(d + 12, sl);
        d += Stride;
        n -= 2u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00171820(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s + 1;
    do {
        r3 = Ld8(s - 1);
        r4 = Ld32(s + 0);
        r7 = Ld32(s + 4);
        r8 = Ld32(s + 8);
        sb = Ld32(s + 12);
        s += Stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        r3 = r3 + (r4 << 8);
        r3 = r3 + r4;
        r4 = r7 + (r4 >> 24);
        r4 = r4 + (r7 << 8);
        r7 = r8 + (r7 >> 24);
        r7 = r7 + (r8 << 8);
        r8 = sb + (r8 >> 24);
        r8 = r8 + (sb << 8);
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r7);
        St32(d + 12, r8);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_0017187c(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, sb = 0, sl = 0, ip = 0, lr = 0;
    ip = 0x7f7f7f7fU;
    s = s + 1;
    r3 = Ld8(s - 1);
    r4 = Ld32(s + 0);
    r5 = Ld32(s + 4);
    r6 = Ld32(s + 8);
    lr = Ld32(s + 12);
    s += Stride;
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    r5 = ip & (r5 >> 1);
    r6 = ip & (r6 >> 1);
    lr = ip & (lr >> 1);
    r3 = r3 + (r4 << 8);
    r3 = r3 + r4;
    r4 = r5 + (r4 >> 24);
    r4 = r4 + (r5 << 8);
    r5 = r6 + (r5 >> 24);
    r5 = r5 + (r6 << 8);
    r6 = lr + (r6 >> 24);
    r6 = r6 + (lr << 8);
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    r5 = ip & (r5 >> 1);
    r6 = ip & (r6 >> 1);
    do {
        r7 = Ld8(s - 1);
        r8 = Ld32(s + 0);
        sb = Ld32(s + 4);
        sl = Ld32(s + 8);
        lr = Ld32(s + 12);
        s += Stride;
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = ip & (sl >> 1);
        lr = ip & (lr >> 1);
        r7 = r7 + (r8 << 8);
        r7 = r7 + r8;
        r8 = sb + (r8 >> 24);
        r8 = r8 + (sb << 8);
        sb = sl + (sb >> 24);
        sb = sb + (sl << 8);
        sl = lr + (sl >> 24);
        sl = sl + (lr << 8);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = ip & (sl >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        r5 = r5 + sb;
        r6 = r6 + sl;
        St32(d + 0, r3);
        St32(d + 4, r4);
        St32(d + 8, r5);
        St32(d + 12, r6);
        d += Stride;
        r3 = Ld8(s - 1);
        r4 = Ld32(s + 0);
        r5 = Ld32(s + 4);
        r6 = Ld32(s + 8);
        lr = Ld32(s + 12);
        s += Stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r5 = ip & (r5 >> 1);
        r6 = ip & (r6 >> 1);
        lr = ip & (lr >> 1);
        r3 = r3 + (r4 << 8);
        r3 = r3 + r4;
        r4 = r5 + (r4 >> 24);
        r4 = r4 + (r5 << 8);
        r5 = r6 + (r5 >> 24);
        r5 = r5 + (r6 << 8);
        r6 = lr + (r6 >> 24);
        r6 = r6 + (lr << 8);
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r5 = ip & (r5 >> 1);
        r6 = ip & (r6 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        sb = sb + r5;
        sl = sl + r6;
        St32(d + 0, r7);
        St32(d + 4, r8);
        St32(d + 8, sb);
        St32(d + 12, sl);
        d += Stride;
        n -= 2u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_001719b8(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0;
    do {
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        s += Stride;
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_001719d4(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    r3 = Ld32(s + 0);
    r4 = Ld32(s + 4);
    s += Stride;
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    do {
        r7 = Ld32(s + 0);
        r8 = Ld32(s + 4);
        s += Stride;
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += Stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        s += Stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        St32(d + 0, r7);
        St32(d + 4, r8);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
done:
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00171a3c(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    do {
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        sb = Ld8(s + 8);
        s += Stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        sb = ip & (sb >> 1);
        r3 = r3 + (r3 >> 8);
        r3 = r3 + (r4 << 24);
        r4 = r4 + (r4 >> 8);
        r4 = r4 + (sb << 24);
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00171a7c(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    r3 = Ld32(s + 0);
    r4 = Ld32(s + 4);
    sb = Ld8(s + 8);
    s += Stride;
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    sb = ip & (sb >> 1);
    r3 = r3 + (r3 >> 8);
    r3 = r3 + (r4 << 24);
    r4 = r4 + (r4 >> 8);
    r4 = r4 + (sb << 24);
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    do {
        r7 = Ld32(s + 0);
        r8 = Ld32(s + 4);
        sb = Ld8(s + 8);
        s += Stride;
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        r7 = r7 + (r7 >> 8);
        r7 = r7 + (r8 << 24);
        r8 = r8 + (r8 >> 8);
        r8 = r8 + (sb << 24);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += Stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        sb = Ld8(s + 8);
        s += Stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        sb = ip & (sb >> 1);
        r3 = r3 + (r3 >> 8);
        r3 = r3 + (r4 << 24);
        r4 = r4 + (r4 >> 8);
        r4 = r4 + (sb << 24);
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        St32(d + 0, r7);
        St32(d + 4, r8);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
done:
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00171b44(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, sb = 0;
    s = s - 1;
    do {
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        sb = Ld8(s + 8);
        s += Stride;
        r3 = r3 >> 8;
        r3 = r3 + (r4 << 24);
        r4 = r4 >> 8;
        r4 = r4 + (sb << 24);
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00171b78(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0, sb = 0, ip = 0;
    s = s - 1;
    ip = 0x7f7f7f7fU;
    r3 = Ld32(s + 0);
    r4 = Ld32(s + 4);
    sb = Ld8(s + 8);
    s += Stride;
    r3 = r3 >> 8;
    r3 = r3 + (r4 << 24);
    r4 = r4 >> 8;
    r4 = r4 + (sb << 24);
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    do {
        r7 = Ld32(s + 0);
        r8 = Ld32(s + 4);
        sb = Ld8(s + 8);
        s += Stride;
        r7 = r7 >> 8;
        r7 = r7 + (r8 << 24);
        r8 = r8 >> 8;
        r8 = r8 + (sb << 24);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += Stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        sb = Ld8(s + 8);
        s += Stride;
        r3 = r3 >> 8;
        r3 = r3 + (r4 << 24);
        r4 = r4 >> 8;
        r4 = r4 + (sb << 24);
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        St32(d + 0, r7);
        St32(d + 4, r8);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
done:
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00171c20(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, sb = 0, sl = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s - 1;
    do {
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        sb = Ld16(s + 8);
        s += Stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        sb = ip & (sb >> 1);
        sl = r3 >> 16;
        sl = sl + (r4 << 16);
        sl = sl + (r3 >> 8);
        r3 = sl + (r4 << 24);
        sl = r4 >> 16;
        sl = sl + (sb << 16);
        sl = sl + (r4 >> 8);
        r4 = sl + (sb << 24);
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00171c74(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0, sb = 0, sl = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s - 1;
    r3 = Ld32(s + 0);
    r4 = Ld32(s + 4);
    sb = Ld16(s + 8);
    s += Stride;
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    sb = ip & (sb >> 1);
    sl = r3 >> 16;
    sl = sl + (r4 << 16);
    sl = sl + (r3 >> 8);
    r3 = sl + (r4 << 24);
    sl = r4 >> 16;
    sl = sl + (sb << 16);
    sl = sl + (r4 >> 8);
    r4 = sl + (sb << 24);
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    do {
        r7 = Ld32(s + 0);
        r8 = Ld32(s + 4);
        sb = Ld16(s + 8);
        s += Stride;
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = r7 >> 16;
        sl = sl + (r8 << 16);
        sl = sl + (r7 >> 8);
        r7 = sl + (r8 << 24);
        sl = r8 >> 16;
        sl = sl + (sb << 16);
        sl = sl + (r8 >> 8);
        r8 = sl + (sb << 24);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += Stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld32(s + 0);
        r4 = Ld32(s + 4);
        sb = Ld16(s + 8);
        s += Stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        sb = ip & (sb >> 1);
        sl = r3 >> 16;
        sl = sl + (r4 << 16);
        sl = sl + (r3 >> 8);
        r3 = sl + (r4 << 24);
        sl = r4 >> 16;
        sl = sl + (sb << 16);
        sl = sl + (r4 >> 8);
        r4 = sl + (sb << 24);
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        St32(d + 0, r7);
        St32(d + 4, r8);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
done:
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00171d70(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, sb = 0;
    do {
        r3 = Ld16(s);
        s += 2;
        r4 = Ld32(s);
        s += 4;
        sb = Ld16(s);
        s -= 6;
        s += Stride;
        r3 = r3 + (r4 << 16);
        r4 = r4 >> 16;
        r4 = r4 + (sb << 16);
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00171da0(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    r3 = Ld16(s);
    s += 2;
    r4 = Ld32(s);
    s += 4;
    sb = Ld16(s);
    s -= 6;
    s += Stride;
    r3 = r3 + (r4 << 16);
    r4 = r4 >> 16;
    r4 = r4 + (sb << 16);
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    do {
        r7 = Ld16(s);
        s += 2;
        r8 = Ld32(s);
        s += 4;
        sb = Ld16(s);
        s -= 6;
        s += Stride;
        r7 = r7 + (r8 << 16);
        r8 = r8 >> 16;
        r8 = r8 + (sb << 16);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += Stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld16(s);
        s += 2;
        r4 = Ld32(s);
        s += 4;
        sb = Ld16(s);
        s -= 6;
        s += Stride;
        r3 = r3 + (r4 << 16);
        r4 = r4 >> 16;
        r4 = r4 + (sb << 16);
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        St32(d + 0, r7);
        St32(d + 4, r8);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
done:
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00171e44(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, sb = 0, sl = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s + 2;
    do {
        r3 = Ld16(s - 2);
        r4 = Ld32(s + 0);
        sb = Ld32(s + 4);
        s += Stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        sb = ip & (sb >> 1);
        sl = r3 + (r4 << 16);
        sl = sl + (r3 >> 8);
        r3 = sl + (r4 << 8);
        r4 = r4 >> 16;
        sl = r4 + (sb << 16);
        sl = sl + (r4 >> 8);
        r4 = sl + (sb << 8);
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00171e94(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0, sb = 0, sl = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s + 2;
    r3 = Ld16(s - 2);
    r4 = Ld32(s + 0);
    sb = Ld32(s + 4);
    s += Stride;
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    sb = ip & (sb >> 1);
    sl = r3 + (r4 << 16);
    sl = sl + (r3 >> 8);
    r3 = sl + (r4 << 8);
    r4 = r4 >> 16;
    sl = r4 + (sb << 16);
    sl = sl + (r4 >> 8);
    r4 = sl + (sb << 8);
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    do {
        r7 = Ld16(s - 2);
        r8 = Ld32(s + 0);
        sb = Ld32(s + 4);
        s += Stride;
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        sl = r7 + (r8 << 16);
        sl = sl + (r7 >> 8);
        r7 = sl + (r8 << 8);
        r8 = r8 >> 16;
        sl = r8 + (sb << 16);
        sl = sl + (r8 >> 8);
        r8 = sl + (sb << 8);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += Stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld16(s - 2);
        r4 = Ld32(s + 0);
        sb = Ld32(s + 4);
        s += Stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        sb = ip & (sb >> 1);
        sl = r3 + (r4 << 16);
        sl = sl + (r3 >> 8);
        r3 = sl + (r4 << 8);
        r4 = r4 >> 16;
        sl = r4 + (sb << 16);
        sl = sl + (r4 >> 8);
        r4 = sl + (sb << 8);
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        St32(d + 0, r7);
        St32(d + 4, r8);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
done:
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00171f84(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, sb = 0;
    s = s + 1;
    do {
        r3 = Ld8(s - 1);
        r4 = Ld32(s + 0);
        sb = Ld32(s + 4);
        s += Stride;
        r3 = r3 + (r4 << 8);
        r4 = r4 >> 24;
        r4 = r4 + (sb << 8);
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00171fb4(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s + 1;
    r3 = Ld8(s - 1);
    r4 = Ld32(s + 0);
    sb = Ld32(s + 4);
    s += Stride;
    r3 = r3 + (r4 << 8);
    r4 = r4 >> 24;
    r4 = r4 + (sb << 8);
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    do {
        r7 = Ld8(s - 1);
        r8 = Ld32(s + 0);
        sb = Ld32(s + 4);
        s += Stride;
        r7 = r7 + (r8 << 8);
        r8 = r8 >> 24;
        r8 = r8 + (sb << 8);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += Stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld8(s - 1);
        r4 = Ld32(s + 0);
        sb = Ld32(s + 4);
        s += Stride;
        r3 = r3 + (r4 << 8);
        r4 = r4 >> 24;
        r4 = r4 + (sb << 8);
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        St32(d + 0, r7);
        St32(d + 4, r8);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
done:
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00172050(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s + 1;
    do {
        r3 = Ld8(s - 1);
        r4 = Ld32(s + 0);
        sb = Ld32(s + 4);
        s += Stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        sb = ip & (sb >> 1);
        r3 = r3 + (r4 << 8);
        r3 = r3 + r4;
        r4 = sb + (r4 >> 24);
        r4 = r4 + (sb << 8);
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00172094(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r4 = 0, r7 = 0, r8 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s + 1;
    r3 = Ld8(s - 1);
    r4 = Ld32(s + 0);
    sb = Ld32(s + 4);
    s += Stride;
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    sb = ip & (sb >> 1);
    r3 = r3 + (r4 << 8);
    r3 = r3 + r4;
    r4 = sb + (r4 >> 24);
    r4 = r4 + (sb << 8);
    r3 = ip & (r3 >> 1);
    r4 = ip & (r4 >> 1);
    do {
        r7 = Ld8(s - 1);
        r8 = Ld32(s + 0);
        sb = Ld32(s + 4);
        s += Stride;
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        sb = ip & (sb >> 1);
        r7 = r7 + (r8 << 8);
        r7 = r7 + r8;
        r8 = sb + (r8 >> 24);
        r8 = r8 + (sb << 8);
        r7 = ip & (r7 >> 1);
        r8 = ip & (r8 >> 1);
        r3 = r3 + r7;
        r4 = r4 + r8;
        St32(d + 0, r3);
        St32(d + 4, r4);
        d += Stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld8(s - 1);
        r4 = Ld32(s + 0);
        sb = Ld32(s + 4);
        s += Stride;
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        sb = ip & (sb >> 1);
        r3 = r3 + (r4 << 8);
        r3 = r3 + r4;
        r4 = sb + (r4 >> 24);
        r4 = r4 + (sb << 8);
        r3 = ip & (r3 >> 1);
        r4 = ip & (r4 >> 1);
        r7 = r7 + r3;
        r8 = r8 + r4;
        St32(d + 0, r7);
        St32(d + 4, r8);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
done:
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00172160(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0;
    do {
        r3 = Ld32(s);
        s += Stride;
        St32(d, r3);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00172174(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r7 = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    r3 = Ld32(s);
    s += Stride;
    r3 = ip & (r3 >> 1);
    do {
        r7 = Ld32(s);
        s += Stride;
        r7 = ip & (r7 >> 1);
        r3 = r3 + r7;
        St32(d, r3);
        d += Stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld32(s);
        s += Stride;
        r3 = ip & (r3 >> 1);
        r7 = r7 + r3;
        St32(d, r7);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
done:
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_001721b4(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    do {
        r3 = Ld32(s);
        sb = Ld8(s + 4);
        s += Stride;
        r3 = ip & (r3 >> 1);
        sb = ip & (sb >> 1);
        r3 = r3 + (r3 >> 8);
        r3 = r3 + (sb << 24);
        St32(d, r3);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_001721e4(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r7 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    r3 = Ld32(s);
    sb = Ld8(s + 4);
    s += Stride;
    r3 = ip & (r3 >> 1);
    sb = ip & (sb >> 1);
    r3 = r3 + (r3 >> 8);
    r3 = r3 + (sb << 24);
    r3 = ip & (r3 >> 1);
    do {
        r7 = Ld32(s);
        sb = Ld8(s + 4);
        s += Stride;
        r7 = ip & (r7 >> 1);
        sb = ip & (sb >> 1);
        r7 = r7 + (r7 >> 8);
        r7 = r7 + (sb << 24);
        r7 = ip & (r7 >> 1);
        r3 = r3 + r7;
        St32(d, r3);
        d += Stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld32(s);
        sb = Ld8(s + 4);
        s += Stride;
        r3 = ip & (r3 >> 1);
        sb = ip & (sb >> 1);
        r3 = r3 + (r3 >> 8);
        r3 = r3 + (sb << 24);
        r3 = ip & (r3 >> 1);
        r7 = r7 + r3;
        St32(d, r7);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
done:
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_0017226c(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, sb = 0;
    s = s - 1;
    do {
        r3 = Ld32(s);
        sb = Ld8(s + 4);
        s += Stride;
        r3 = r3 >> 8;
        r3 = r3 + (sb << 24);
        St32(d, r3);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00172294(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r7 = 0, sb = 0, ip = 0;
    s = s - 1;
    ip = 0x7f7f7f7fU;
    r3 = Ld32(s);
    sb = Ld8(s + 4);
    s += Stride;
    r3 = r3 >> 8;
    r3 = r3 + (sb << 24);
    r3 = ip & (r3 >> 1);
    do {
        r7 = Ld32(s);
        sb = Ld8(s + 4);
        s += Stride;
        r7 = r7 >> 8;
        r7 = r7 + (sb << 24);
        r7 = ip & (r7 >> 1);
        r3 = r3 + r7;
        St32(d, r3);
        d += Stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld32(s);
        sb = Ld8(s + 4);
        s += Stride;
        r3 = r3 >> 8;
        r3 = r3 + (sb << 24);
        r3 = ip & (r3 >> 1);
        r7 = r7 + r3;
        St32(d, r7);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
done:
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00172308(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, sb = 0, sl = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s - 1;
    do {
        r3 = Ld32(s);
        sb = Ld16(s + 4);
        s += Stride;
        r3 = ip & (r3 >> 1);
        sb = ip & (sb >> 1);
        sl = r3 >> 16;
        sl = sl + (sb << 16);
        sl = sl + (r3 >> 8);
        r3 = sl + (sb << 24);
        St32(d, r3);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00172344(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r7 = 0, sb = 0, sl = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s - 1;
    r3 = Ld32(s);
    sb = Ld16(s + 4);
    s += Stride;
    r3 = ip & (r3 >> 1);
    sb = ip & (sb >> 1);
    sl = r3 >> 16;
    sl = sl + (sb << 16);
    sl = sl + (r3 >> 8);
    r3 = sl + (sb << 24);
    r3 = ip & (r3 >> 1);
    do {
        r7 = Ld32(s);
        sb = Ld16(s + 4);
        s += Stride;
        r7 = ip & (r7 >> 1);
        sb = ip & (sb >> 1);
        sl = r7 >> 16;
        sl = sl + (sb << 16);
        sl = sl + (r7 >> 8);
        r7 = sl + (sb << 24);
        r7 = ip & (r7 >> 1);
        r3 = r3 + r7;
        St32(d, r3);
        d += Stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld32(s);
        sb = Ld16(s + 4);
        s += Stride;
        r3 = ip & (r3 >> 1);
        sb = ip & (sb >> 1);
        sl = r3 >> 16;
        sl = sl + (sb << 16);
        sl = sl + (r3 >> 8);
        r3 = sl + (sb << 24);
        r3 = ip & (r3 >> 1);
        r7 = r7 + r3;
        St32(d, r7);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
done:
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_001723e8(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, sb = 0;
    do {
        r3 = Ld16(s);
        s += 2;
        sb = Ld16(s);
        s -= 2;
        s += Stride;
        r3 = r3 + (sb << 16);
        St32(d, r3);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00172408(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r7 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    r3 = Ld16(s);
    s += 2;
    sb = Ld16(s);
    s -= 2;
    s += Stride;
    r3 = r3 + (sb << 16);
    r3 = ip & (r3 >> 1);
    do {
        r7 = Ld16(s);
        s += 2;
        sb = Ld16(s);
        s -= 2;
        s += Stride;
        r7 = r7 + (sb << 16);
        r7 = ip & (r7 >> 1);
        r3 = r3 + r7;
        St32(d, r3);
        d += Stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld16(s);
        s += 2;
        sb = Ld16(s);
        s -= 2;
        s += Stride;
        r3 = r3 + (sb << 16);
        r3 = ip & (r3 >> 1);
        r7 = r7 + r3;
        St32(d, r7);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
done:
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_0017246c(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, sb = 0, sl = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s + 2;
    do {
        r3 = Ld16(s - 2);
        sb = Ld32(s);
        s += Stride;
        r3 = ip & (r3 >> 1);
        sb = ip & (sb >> 1);
        sl = r3 + (sb << 16);
        sl = sl + (r3 >> 8);
        r3 = sl + (sb << 8);
        St32(d, r3);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_001724a0(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r7 = 0, sb = 0, sl = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s + 2;
    r3 = Ld16(s - 2);
    sb = Ld32(s);
    s += Stride;
    r3 = ip & (r3 >> 1);
    sb = ip & (sb >> 1);
    sl = r3 + (sb << 16);
    sl = sl + (r3 >> 8);
    r3 = sl + (sb << 8);
    r3 = ip & (r3 >> 1);
    do {
        r7 = Ld16(s - 2);
        sb = Ld32(s);
        s += Stride;
        r7 = ip & (r7 >> 1);
        sb = ip & (sb >> 1);
        sl = r7 + (sb << 16);
        sl = sl + (r7 >> 8);
        r7 = sl + (sb << 8);
        r7 = ip & (r7 >> 1);
        r3 = r3 + r7;
        St32(d, r3);
        d += Stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld16(s - 2);
        sb = Ld32(s);
        s += Stride;
        r3 = ip & (r3 >> 1);
        sb = ip & (sb >> 1);
        sl = r3 + (sb << 16);
        sl = sl + (r3 >> 8);
        r3 = sl + (sb << 8);
        r3 = ip & (r3 >> 1);
        r7 = r7 + r3;
        St32(d, r7);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
done:
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_0017252c(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, sb = 0;
    s = s + 1;
    do {
        r3 = Ld8(s - 1);
        sb = Ld32(s);
        s += Stride;
        r3 = r3 + (sb << 8);
        St32(d, r3);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_0017254c(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r7 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s + 1;
    r3 = Ld8(s - 1);
    sb = Ld32(s);
    s += Stride;
    r3 = r3 + (sb << 8);
    r3 = ip & (r3 >> 1);
    do {
        r7 = Ld8(s - 1);
        sb = Ld32(s);
        s += Stride;
        r7 = r7 + (sb << 8);
        r7 = ip & (r7 >> 1);
        r3 = r3 + r7;
        St32(d, r3);
        d += Stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld8(s - 1);
        sb = Ld32(s);
        s += Stride;
        r3 = r3 + (sb << 8);
        r3 = ip & (r3 >> 1);
        r7 = r7 + r3;
        St32(d, r7);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
done:
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_001725a8(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s + 1;
    do {
        r3 = Ld8(s - 1);
        sb = Ld32(s);
        s += Stride;
        r3 = ip & (r3 >> 1);
        sb = ip & (sb >> 1);
        r3 = r3 + (sb << 8);
        r3 = r3 + sb;
        St32(d, r3);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_001725d8(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r7 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    s = s + 1;
    r3 = Ld8(s - 1);
    sb = Ld32(s);
    s += Stride;
    r3 = ip & (r3 >> 1);
    sb = ip & (sb >> 1);
    r3 = r3 + (sb << 8);
    r3 = r3 + sb;
    r3 = ip & (r3 >> 1);
    do {
        r7 = Ld8(s - 1);
        sb = Ld32(s);
        s += Stride;
        r7 = ip & (r7 >> 1);
        sb = ip & (sb >> 1);
        r7 = r7 + (sb << 8);
        r7 = r7 + sb;
        r7 = ip & (r7 >> 1);
        r3 = r3 + r7;
        St32(d, r3);
        d += Stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld8(s - 1);
        sb = Ld32(s);
        s += Stride;
        r3 = ip & (r3 >> 1);
        sb = ip & (sb >> 1);
        r3 = r3 + (sb << 8);
        r3 = r3 + sb;
        r3 = ip & (r3 >> 1);
        r7 = r7 + r3;
        St32(d, r7);
        d += Stride;
        n -= 1u;
    } while (n != 0u);
done:
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00172658(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0;
    do {
        r3 = Ld16(s);
        s += Stride;
        St16(d, static_cast<u16>(r3));
        d += Stride;
        n -= 1u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00172674(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r7 = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    r3 = Ld16(s);
    s += Stride;
    r3 = ip & (r3 >> 1);
    do {
        r7 = Ld16(s);
        s += Stride;
        r7 = ip & (r7 >> 1);
        r3 = r3 + r7;
        St16(d, static_cast<u16>(r3));
        d += Stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld16(s);
        s += Stride;
        r3 = ip & (r3 >> 1);
        r7 = r7 + r3;
        St16(d, static_cast<u16>(r7));
        d += Stride;
        n -= 1u;
    } while (n != 0u);
done:
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_001726c8(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    do {
        r3 = Ld16(s);
        sb = Ld8(s + 2);
        s += Stride;
        r3 = ip & (r3 >> 1);
        sb = ip & (sb >> 1);
        r3 = r3 + (r3 >> 8);
        r3 = r3 + (sb << 8);
        St16(d, static_cast<u16>(r3));
        d += Stride;
        n -= 1u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_001726fc(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r7 = 0, sb = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    r3 = Ld16(s);
    sb = Ld8(s + 2);
    s += Stride;
    r3 = ip & (r3 >> 1);
    sb = ip & (sb >> 1);
    r3 = r3 + (r3 >> 8);
    r3 = r3 + (sb << 8);
    r3 = ip & (r3 >> 1);
    do {
        r7 = Ld16(s);
        sb = Ld8(s + 2);
        s += Stride;
        r7 = ip & (r7 >> 1);
        sb = ip & (sb >> 1);
        r7 = r7 + (r7 >> 8);
        r7 = r7 + (sb << 8);
        r7 = ip & (r7 >> 1);
        r3 = r3 + r7;
        St16(d, static_cast<u16>(r3));
        d += Stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld16(s);
        sb = Ld8(s + 2);
        s += Stride;
        r3 = ip & (r3 >> 1);
        sb = ip & (sb >> 1);
        r3 = r3 + (r3 >> 8);
        r3 = r3 + (sb << 8);
        r3 = ip & (r3 >> 1);
        r7 = r7 + r3;
        St16(d, static_cast<u16>(r7));
        d += Stride;
        n -= 1u;
    } while (n != 0u);
done:
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_0017278c(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, sb = 0;
    s = s + 1;
    do {
        r3 = Ld8(s - 1);
        sb = Ld8(s);
        s += Stride;
        r3 = r3 + (sb << 8);
        St16(d, static_cast<u16>(r3));
        d += Stride;
        n -= 1u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_001727b0(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r7 = 0, sb = 0, ip = 0;
    s = s + 1;
    ip = 0x7f7f7f7fU;
    r3 = Ld8(s - 1);
    sb = Ld8(s);
    s += Stride;
    r3 = r3 + (sb << 8);
    r3 = ip & (r3 >> 1);
    do {
        r7 = Ld8(s - 1);
        sb = Ld8(s);
        s += Stride;
        r7 = r7 + (sb << 8);
        r7 = ip & (r7 >> 1);
        r3 = r3 + r7;
        St16(d, static_cast<u16>(r3));
        d += Stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld8(s - 1);
        sb = Ld8(s);
        s += Stride;
        r3 = r3 + (sb << 8);
        r3 = ip & (r3 >> 1);
        r7 = r7 + r3;
        St16(d, static_cast<u16>(r7));
        d += Stride;
        n -= 1u;
    } while (n != 0u);
done:
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00172814(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, sb = 0, sl = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    do {
        r3 = Ld8(s);
        sb = Ld16(s + 1);
        s += Stride;
        r3 = ip & (r3 >> 1);
        sb = ip & (sb >> 1);
        sl = sb << 24;
        sl = r3 + (sl >> 16);
        r3 = sl + sb;
        St16(d, static_cast<u16>(r3));
        d += Stride;
        n -= 1u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_0017284c(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r7 = 0, sb = 0, sl = 0, ip = 0;
    ip = 0x7f7f7f7fU;
    r3 = Ld8(s);
    sb = Ld16(s + 1);
    s += Stride;
    r3 = ip & (r3 >> 1);
    sb = ip & (sb >> 1);
    sl = sb << 24;
    sl = r3 + (sl >> 16);
    r3 = sl + sb;
    r3 = ip & (r3 >> 1);
    do {
        r7 = Ld8(s);
        sb = Ld16(s + 1);
        s += Stride;
        r7 = ip & (r7 >> 1);
        sb = ip & (sb >> 1);
        sl = sb << 24;
        sl = r7 + (sl >> 16);
        r7 = sl + sb;
        r7 = ip & (r7 >> 1);
        r3 = r3 + r7;
        St16(d, static_cast<u16>(r3));
        d += Stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld8(s);
        sb = Ld16(s + 1);
        s += Stride;
        r3 = ip & (r3 >> 1);
        sb = ip & (sb >> 1);
        sl = sb << 24;
        sl = r3 + (sl >> 16);
        r3 = sl + sb;
        r3 = ip & (r3 >> 1);
        r7 = r7 + r3;
        St16(d, static_cast<u16>(r7));
        d += Stride;
        n -= 1u;
    } while (n != 0u);
done:
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_001728e8(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0;
    do {
        r3 = Ld8(s);
        s += Stride;
        St8(d, static_cast<u8>(r3));
        d += Stride;
        n -= 1u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_001728fc(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r7 = 0;
    r3 = Ld8(s);
    s += Stride;
    r3 = r3 >> 1;
    do {
        r7 = Ld8(s);
        s += Stride;
        r7 = r7 >> 1;
        r3 = r3 + r7;
        St8(d, static_cast<u8>(r3));
        d += Stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld8(s);
        s += Stride;
        r3 = r3 >> 1;
        r7 = r7 + r3;
        St8(d, static_cast<u8>(r7));
        d += Stride;
        n -= 1u;
    } while (n != 0u);
done:
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_00172938(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, sb = 0;
    s = s + 1;
    do {
        r3 = Ld8(s - 1);
        sb = Ld8(s);
        s += Stride;
        r3 = r3 >> 1;
        r3 = r3 + (sb >> 1);
        St8(d, static_cast<u8>(r3));
        d += Stride;
        n -= 1u;
    } while (n != 0u);
    
    
}

template <u32 Stride>
__attribute__((always_inline)) inline void TexConv_0017295c(const u8* src, u8* dst, u32 count) {
    const u8* s = src;
    u8* d = dst;
    u32 n = count;
    u32 r3 = 0, r7 = 0, sb = 0;
    r3 = Ld8(s);
    s += 1;
    sb = Ld8(s);
    s += Stride;
    r3 = r3 >> 1;
    r3 = r3 + (sb >> 1);
    r3 = r3 >> 1;
    do {
        r7 = Ld8(s - 1);
        sb = Ld8(s);
        s += Stride;
        r7 = r7 >> 1;
        r7 = r7 + (sb >> 1);
        r7 = r7 >> 1;
        r3 = r3 + r7;
        St8(d, static_cast<u8>(r3));
        d += Stride;
        n -= 1u;
        if (n == 0u) goto done;
        r3 = Ld8(s - 1);
        sb = Ld8(s);
        s += Stride;
        r3 = r3 >> 1;
        r3 = r3 + (sb >> 1);
        r3 = r3 >> 1;
        r7 = r7 + r3;
        St8(d, static_cast<u8>(r7));
        d += Stride;
        n -= 1u;
    } while (n != 0u);
done:
    
    
}

} // namespace smt4::engine
