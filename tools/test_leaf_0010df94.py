import os
import struct
import sys
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM
from unicorn.arm_const import (
    UC_ARM_REG_C1_C0_2,
    UC_ARM_REG_CPSR,
    UC_ARM_REG_FPEXC,
    UC_ARM_REG_LR,
    UC_ARM_REG_PC,
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
    UC_ARM_REG_R6,
    UC_ARM_REG_S0,
    UC_ARM_REG_SP,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from build_check import compile_tu_armv6k  # noqa: E402

CODE_BIN = REPO_ROOT / "extracted" / "exefs" / "code.bin"
SRC_CPP = REPO_ROOT / "src" / "engine" / "leaf_batch45_c.cpp"

FUNC_ADDR = 0x0010DF94
FUNC_SIZE = 0x0010E508 - 0x0010DF94  # 1396 bytes (entry func_0010df94)
FUNC_2BCD00 = 0x002BCD00
FUNC_2BCD94 = 0x002BCD94

SND_STATE = 0x004E3138
SLOT_A = 0x004E3170
SLOT_B = 0x004E3178
OBJ4_PTR = 0x004E3180

STUB_RET = 0x00600000
STUB_2BCD00 = 0x00600100
STUB_2BCD94 = 0x00600200
CAND_BASE = 0x00700000
STACK_TOP = 0x0080FFF0

OBJ_BASE = 0x00500000
PA0 = OBJ_BASE + 0x000
PA1 = OBJ_BASE + 0x100
PB0 = OBJ_BASE + 0x200
PB1 = OBJ_BASE + 0x300
OBJ4 = OBJ_BASE + 0x400


def parse_elf_symbols(elf_bytes: bytes):
    e_shoff = struct.unpack_from("<I", elf_bytes, 0x20)[0]
    e_shentsize = struct.unpack_from("<H", elf_bytes, 0x2E)[0]
    e_shnum = struct.unpack_from("<H", elf_bytes, 0x30)[0]
    e_shstrndx = struct.unpack_from("<H", elf_bytes, 0x32)[0]
    sh = []
    for i in range(e_shnum):
        off = e_shoff + i * e_shentsize
        sh.append(struct.unpack_from("<10I", elf_bytes, off))
    shstr = elf_bytes[sh[e_shstrndx][4] : sh[e_shstrndx][4] + sh[e_shstrndx][5]]

    def sec_name(s):
        idx = s[0]
        end = shstr.index(0, idx)
        return shstr[idx:end].decode("ascii", "replace")

    syms = {}
    sym_list = []
    for s in sh:
        if s[1] == 2:  # SHT_SYMTAB
            strtab = elf_bytes[sh[s[6]][4] : sh[s[6]][4] + sh[s[6]][5]]
            ent_sz = s[9] or 16
            n = s[5] // ent_sz
            for idx in range(n):
                st_name, st_value, st_size, st_info, st_other, st_shndx = struct.unpack_from(
                    "<IIIBBH", elf_bytes, s[4] + idx * ent_sz
                )
                end = strtab.index(0, st_name)
                name = strtab[st_name:end].decode("ascii", "replace")
                sym_list.append((name, st_value, st_size, st_info, st_shndx))
                if name:
                    syms[name] = (st_value, st_size, st_shndx)
    return sh, sec_name, syms, sym_list


def patch_cand_elf(elf_bytes: bytes, base_addr: int, target_name: str, stub_map: dict):
    sh, sec_name, syms, sym_list = parse_elf_symbols(elf_bytes)
    if target_name not in syms:
        raise RuntimeError(f"Symbol {target_name} not found in compiled ELF")
    func_val, func_size, func_shndx = syms[target_name]
    text_s = sh[func_shndx]
    text_name = sec_name(text_s)
    text_bytes = bytearray(elf_bytes[text_s[4] : text_s[4] + text_s[5]])

    # Build address-to-symbol map for .rodata/.data/etc if needed
    sec_bases = {}
    cursor = base_addr + len(text_bytes)
    cursor = (cursor + 15) & ~15
    extra_blobs = bytearray()
    for i, s in enumerate(sh):
        if i == func_shndx:
            sec_bases[i] = base_addr
        elif s[1] == 1 and (s[2] & 2):  # SHT_PROGBITS & SHF_ALLOC
            blob = elf_bytes[s[4] : s[4] + s[5]]
            sec_bases[i] = cursor
            extra_blobs.extend(blob)
            pad = ((len(blob) + 15) & ~15) - len(blob)
            extra_blobs.extend(b"\x00" * pad)
            cursor += len(blob) + pad

    for s in sh:
        if s[1] != 9:  # SHT_REL
            continue
        if sec_name(sh[s[7]]) != text_name:
            continue
        ent_sz = s[9] or 8
        n = s[5] // ent_sz
        for idx in range(n):
            r_offset, r_info = struct.unpack_from("<II", elf_bytes, s[4] + idx * ent_sz)
            r_sym = r_info >> 8
            r_type = r_info & 0xFF
            sname, sval, _, _, sshndx = sym_list[r_sym]
            in_func = func_val <= r_offset < func_val + func_size
            if not in_func:
                if not (r_type in (28, 29) and sname in stub_map):
                    continue
            if r_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
                if sname in stub_map:
                    target = stub_map[sname]
                elif sshndx == func_shndx:
                    target = base_addr + sval
                else:
                    raise RuntimeError(f"Unresolved branch target {sname}")
                pc = base_addr + r_offset + 8
                disp = (target - pc) >> 2
                insn = struct.unpack_from("<I", text_bytes, r_offset)[0]
                insn = (insn & 0xFF000000) | (disp & 0x00FFFFFF)
                struct.pack_into("<I", text_bytes, r_offset, insn)
            elif r_type in (2, 43, 44):  # ABS32 / MOVW_ABS_NC / MOVT_ABS
                target = sec_bases[sshndx] + sval
                if r_type == 2:
                    addend = struct.unpack_from("<i", text_bytes, r_offset)[0]
                    struct.pack_into("<I", text_bytes, r_offset, (target + addend) & 0xFFFFFFFF)
                elif r_type == 43:
                    insn = struct.unpack_from("<I", text_bytes, r_offset)[0]
                    imm16 = target & 0xFFFF
                    insn = (insn & 0xFFF0F000) | ((imm16 & 0xF000) << 4) | (imm16 & 0x0FFF)
                    struct.pack_into("<I", text_bytes, r_offset, insn)
                elif r_type == 44:
                    insn = struct.unpack_from("<I", text_bytes, r_offset)[0]
                    imm16 = (target >> 16) & 0xFFFF
                    insn = (insn & 0xFFF0F000) | ((imm16 & 0xF000) << 4) | (imm16 & 0x0FFF)
                    struct.pack_into("<I", text_bytes, r_offset, insn)
            else:
                raise RuntimeError(f"Unhandled reloc type {r_type} for {sname}")

    image = bytes(text_bytes) + bytes(extra_blobs)
    return base_addr + func_val, image


def setup_uc(code_bytes: bytes, is_orig: bool):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(0x00100000, 0x00300000)
    uc.mem_map(0x00400000, 0x00200000)
    uc.mem_map(STUB_RET, 0x00010000)
    uc.mem_map(CAND_BASE, 0x00100000)
    uc.mem_map(0x00800000, 0x00020000)

    # Enable VFP
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    if is_orig:
        uc.mem_write(FUNC_ADDR, code_bytes)
        # Patch stubs at original target addresses
        bx_lr = struct.pack("<I", 0xE12FFF1E)
        uc.mem_write(FUNC_2BCD00, bx_lr)
        uc.mem_write(FUNC_2BCD94, bx_lr)
    else:
        uc.mem_write(CAND_BASE, code_bytes)
        bx_lr = struct.pack("<I", 0xE12FFF1E)
        uc.mem_write(STUB_2BCD00, bx_lr)
        uc.mem_write(STUB_2BCD94, bx_lr)

    uc.mem_write(STUB_RET, struct.pack("<I", 0xE12FFF1E))
    return uc


def run_case(orig_bytes: bytes, cand_entry: int, cand_image: bytes, case: dict):
    results = []
    for is_orig in (True, False):
        uc = setup_uc(orig_bytes if is_orig else cand_image, is_orig)

        # Zero state & objects
        uc.mem_write(SND_STATE, b"\x00" * 0x50)
        uc.mem_write(OBJ_BASE, b"\x00" * 0x500)

        # Populate snd_state
        duck_scale = case.get("duck_scale", 0.5)
        fade_down = case.get("fade_down", 10)
        fade_up = case.get("fade_up", 20)
        start_delay = case.get("start_delay", 2)
        end_delay = case.get("end_delay", 3)
        timer = case.get("timer", 0)
        flags = case.get("flags", 1)
        state = case.get("state", 0)
        mode_flag = case.get("mode_flag", 0)

        uc.mem_write(
            SND_STATE,
            struct.pack("<f5IBBB", duck_scale, fade_down, fade_up, start_delay, end_delay, timer, flags, state, mode_flag),
        )

        # Slot A / B / OBJ4
        slot_a_ptrs = [0, 0]
        for idx, base in enumerate((PA0, PA1)):
            cfg = case.get(f"pA{idx}")
            if cfg is not None:
                slot_a_ptrs[idx] = base
                uc.mem_write(base + 0x20, struct.pack("<I", cfg.get("handle", 0)))
                uc.mem_write(base + 0x38, struct.pack("<BB", cfg.get("flags", 0), cfg.get("vol", 0)))
        uc.mem_write(SLOT_A, struct.pack("<II", slot_a_ptrs[0], slot_a_ptrs[1]))

        slot_b_ptrs = [0, 0]
        for idx, base in enumerate((PB0, PB1)):
            cfg = case.get(f"pB{idx}")
            if cfg is not None:
                slot_b_ptrs[idx] = base
                uc.mem_write(base + 0x00, struct.pack("<I", cfg.get("handle", 0)))
                uc.mem_write(base + 0x0C, struct.pack("<BB", cfg.get("flags", 0), cfg.get("vol", 0)))
        uc.mem_write(SLOT_B, struct.pack("<II", slot_b_ptrs[0], slot_b_ptrs[1]))

        obj4_cfg = case.get("obj4")
        if obj4_cfg is not None:
            uc.mem_write(OBJ4_PTR, struct.pack("<I", OBJ4))
            uc.mem_write(OBJ4 + 0x20, struct.pack("<4I", *obj4_cfg))
        else:
            uc.mem_write(OBJ4_PTR, struct.pack("<I", 0))

        calls = []
        addr_2bcd00 = FUNC_2BCD00 if is_orig else STUB_2BCD00
        addr_2bcd94 = FUNC_2BCD94 if is_orig else STUB_2BCD94
        ret_2bcd00 = case.get("ret_2bcd00", 0)

        def hook_code(uc_inst, address, size, user_data):
            if address == addr_2bcd00:
                calls.append(("2bcd00",))
                uc_inst.reg_write(UC_ARM_REG_R0, ret_2bcd00)
            elif address == addr_2bcd94:
                h = uc_inst.reg_read(UC_ARM_REG_R0)
                ft = uc_inst.reg_read(UC_ARM_REG_R1)
                s0_bits = uc_inst.reg_read(UC_ARM_REG_S0)
                calls.append(("2bcd94", h, ft, s0_bits))

        uc.hook_add(1 << 2, hook_code)  # UC_HOOK_CODE = 4

        uc.reg_write(UC_ARM_REG_CPSR, 0x10)
        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, STUB_RET)
        uc.reg_write(UC_ARM_REG_R6, 0)

        entry = FUNC_ADDR if is_orig else cand_entry
        try:
            uc.emu_start(entry, STUB_RET, timeout=5_000_000, count=100_000)
        except Exception as exc:
            pc = uc.reg_read(UC_ARM_REG_PC)
            sp = uc.reg_read(UC_ARM_REG_SP)
            raise RuntimeError(f"UcError is_orig={is_orig} case={case['name']} pc=0x{pc:08x} sp=0x{sp:08x}: {exc}") from exc

        out_state = bytes(uc.mem_read(SND_STATE, 0x1C))
        results.append((out_state, calls))

    if results[0] != results[1]:
        return False, f"orig={results[0]} != cand={results[1]}"
    return True, "ok"


CASES = [
    {"name": "disabled_flag", "flags": 0, "state": 0, "mode_flag": 1},
    {"name": "mode0_obj4_null", "flags": 1, "state": 0, "mode_flag": 0, "obj4": None},
    {"name": "unknown_state_3", "flags": 1, "state": 3, "mode_flag": 1, "timer": 7},
    {"name": "state0_mode1_inactive", "flags": 1, "state": 0, "mode_flag": 1, "ret_2bcd00": 0, "timer": 5},
    {"name": "state0_mode0_obj4_all_zero", "flags": 1, "state": 0, "mode_flag": 0, "obj4": (0, 0, 0, 0), "timer": 4},
    {
        "name": "state0_mode0_wait_timer",
        "flags": 1,
        "state": 0,
        "mode_flag": 0,
        "obj4": (0, 0, 0x123, 0),
        "timer": 1,
        "start_delay": 2,
    },
    {
        "name": "state0_duck_all_slots",
        "flags": 1,
        "state": 0,
        "mode_flag": 1,
        "ret_2bcd00": 1,
        "timer": 2,
        "start_delay": 2,
        "duck_scale": 0.5,
        "fade_down": 15,
        "pA0": {"flags": 2, "vol": 100, "handle": 0x101},
        "pA1": {"flags": 4, "vol": 0, "handle": 0x102},
        "pB0": {"flags": 6, "vol": 255, "handle": 0x201},
        "pB1": {"flags": 2, "vol": 64, "handle": 0},
    },
    {
        "name": "state0_no_slots_updated",
        "flags": 1,
        "state": 0,
        "mode_flag": 1,
        "ret_2bcd00": 1,
        "timer": 2,
        "start_delay": 2,
        "pA0": {"flags": 1, "vol": 50, "handle": 0x101},
        "pB0": None,
    },
    {"name": "state1_active_stays", "flags": 1, "state": 1, "mode_flag": 1, "ret_2bcd00": 1, "timer": 0},
    {
        "name": "state1_obj4_active_stays",
        "flags": 1,
        "state": 1,
        "mode_flag": 0,
        "obj4": (0, 1, 0, 0),
        "timer": 0,
    },
    {
        "name": "state1_inactive_to_state2",
        "flags": 1,
        "state": 1,
        "mode_flag": 0,
        "obj4": (0, 0, 0, 0),
        "timer": 3,
    },
    {
        "name": "state2_wait_inactive",
        "flags": 1,
        "state": 2,
        "mode_flag": 1,
        "ret_2bcd00": 0,
        "timer": 1,
        "end_delay": 3,
    },
    {
        "name": "state2_wait_retriggered",
        "flags": 1,
        "state": 2,
        "mode_flag": 1,
        "ret_2bcd00": 1,
        "timer": 1,
        "end_delay": 3,
    },
    {
        "name": "state2_restore_all",
        "flags": 0x0D,
        "state": 2,
        "mode_flag": 1,
        "timer": 3,
        "end_delay": 3,
        "fade_up": 30,
        "pA0": {"flags": 2, "vol": 0, "handle": 0x101},
        "pA1": {"flags": 4, "vol": 127, "handle": 0x102},
        "pB0": {"flags": 2, "vol": 64, "handle": 0x201},
        "pB1": {"flags": 2, "vol": 200, "handle": 0x202},
    },
    {
        "name": "state2_restore_no_slotA_flags",
        "flags": 1,
        "state": 2,
        "mode_flag": 0,
        "obj4": (0, 0, 0, 0),
        "timer": 3,
        "end_delay": 3,
        "fade_up": 25,
        "pA0": {"flags": 2, "vol": 80, "handle": 0x101},
        "pA1": {"flags": 4, "vol": 80, "handle": 0x102},
        "pB0": {"flags": 2, "vol": 50, "handle": 0x201},
        "pB1": None,
    },
]


def run_negative_controls(orig_bytes: bytes, cand_entry: int, cand_image: bytes):
    # Test 5 mutations on candidate image or case comparison to ensure checker catches discrepancies
    # 1. Mutant: corrupt fade_up in state2_restore_all comparison
    # Actually let's compile 5 small mutated C++ snippets or verify mutated expectations are rejected
    mutants = [
        ("mut1_missing_bit4_flag", "if (any_updated)", "if (false)"),
        ("mut2_wrong_gain_clamp", "vol = 0x7Fu;", "vol = 0x40u;"),
        ("mut3_wrong_fade_up", "u32 fade_time = *reinterpret_cast<u32*>(snd_state + 8);", "u32 fade_time = *reinterpret_cast<u32*>(snd_state + 4);"),
        ("mut4_missing_obj4_28", "*reinterpret_cast<const u32*>(obj4 + 0x28) != 0u ||", "false ||"),
        ("mut5_wrong_state2_transition", "snd_state[0x19] = 2u;", "snd_state[0x19] = 0u;"),
    ]
    src_text = SRC_CPP.read_text(encoding="utf-8")
    tmp_dir = REPO_ROOT / "build" / "test_leaf_0010df94_mut"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for mname, old, new in mutants:
        assert old in src_text, f"Mutant target missing: {old}"
        mut_src = tmp_dir / f"{mname}.cpp"
        mut_obj = tmp_dir / f"{mname}.o"
        mut_src.write_text(src_text.replace(old, new, 1), encoding="utf-8")
        res = compile_tu_armv6k(mut_src, mut_obj)
        if res.returncode != 0:
            raise RuntimeError(f"Mutant {mname} failed to compile: {res.stderr}")
        m_entry, m_img = patch_cand_elf(
            mut_obj.read_bytes(),
            CAND_BASE,
            "func_0010df94",
            {"func_002bcd00": STUB_2BCD00, "func_002bcd94": STUB_2BCD94},
        )
        caught = False
        for c in CASES:
            ok, _ = run_case(orig_bytes, m_entry, m_img, c)
            if not ok:
                caught = True
                break
        if not caught:
            raise RuntimeError(f"Negative control {mname} was NOT caught!")
        print(f"NEG_CTRL PASS (caught): {mname}")


def main():
    code_all = CODE_BIN.read_bytes()
    off = FUNC_ADDR - 0x00100000
    orig_bytes = code_all[off : off + FUNC_SIZE]

    obj_out = REPO_ROOT / "build" / "test_leaf_0010df94.o"
    obj_out.parent.mkdir(parents=True, exist_ok=True)
    res = compile_tu_armv6k(SRC_CPP, obj_out)
    if res.returncode != 0:
        print("COMPILE FAIL:\n", res.stderr)
        sys.exit(1)

    cand_entry, cand_image = patch_cand_elf(
        obj_out.read_bytes(),
        CAND_BASE,
        "func_0010df94",
        {"func_002bcd00": STUB_2BCD00, "func_002bcd94": STUB_2BCD94},
    )

    for c in CASES:
        ok, msg = run_case(orig_bytes, cand_entry, cand_image, c)
        if not ok:
            print(f"FAIL {c['name']}: {msg}")
            sys.exit(1)
        print(f"PASS: {c['name']}")

    run_negative_controls(orig_bytes, cand_entry, cand_image)
    print(f"ALL PASS: {len(CASES)} cases + 5 negative controls")


if __name__ == "__main__":
    main()
