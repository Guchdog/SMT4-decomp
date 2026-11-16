#!/usr/bin/env python3
"""Differential test for ui_func_002d7f0c and ui_func_002e1b90 using Unicorn ARM emulation."""

import struct
import sys
from pathlib import Path
import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"

FUNC1_ADDR = 0x002d7f0c
FUNC2_ADDR = 0x002e1b90
FUNC_SIZE = 596

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
CODE_ADDR  = 0x00200000
CODE_SIZE  = 0x00200000  # 2MB
DATA_ADDR  = 0x00440000
DATA_SIZE  = 0x00020000  # 128KB
GPU_ADDR   = 0x00500000
GPU_SIZE   = 0x00010000  # 64KB
TRAP_ADDR  = 0x90000000

# Function stub addresses
STUB_2C5F7C = 0x002c5f7c
STUB_288310 = 0x00288310
STUB_2C5218 = 0x002c5218
STUB_2C5188 = 0x002c5188
STUB_24A9D4 = 0x0024a9d4
STUB_24C564 = 0x0024c564
STUB_281ADC = 0x00281adc
STUB_2C1ABC = 0x002c1abc
STUB_2C1B64 = 0x002c1b64
CALLBACK_ADDR = 0x00240000

def get_orig_bytes(addr):
    with open(ORIG_BIN, "rb") as f:
        f.seek(addr - 0x00100000)
        return f.read(FUNC_SIZE)

def get_symbol_offset(obj_file, sym_name):
    data = Path(obj_file).read_bytes()
    e_shoff, e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<IIHH", data, 32)[0], struct.unpack_from("<H", data, 46)[0], struct.unpack_from("<H", data, 48)[0], struct.unpack_from("<H", data, 50)[0]
    sections = [struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    symtab = [s for s in sections if s[1] == 2][0]
    strtab = sections[symtab[6]]
    for i in range(symtab[5] // 16):
        st_name, st_val, st_size, st_info, st_other, st_shndx = struct.unpack_from("<IIIBBH", data, symtab[4] + i * 16)
        name = data[strtab[4] + st_name:].split(b"\x00")[0].decode("ascii", errors="replace")
        if sym_name == name or name == f"_{sym_name}":
            return st_val
    return 0

def compile_candidate(func_name):
    out_dir = ROOT / "build/test_leaf_002d7f0c"
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_file = out_dir / "leaf_batch45_a.o"
    src_file = ROOT / "src/engine/leaf_batch45_a.cpp"
    res = compile_tu_armv6k(src_file, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    funcs = extract_elf_functions_detailed(obj_file)
    cand_entry = None
    for k in funcs:
        if func_name in k:
            cand_entry = funcs[k]
            break
    if not cand_entry:
        raise RuntimeError(f"Function {func_name} not found in {obj_file}: available {list(funcs.keys())}")
    
    code_raw, relocs = cand_entry
    code = bytearray(code_raw)
    func_sym_offset = get_symbol_offset(obj_file, func_name)
    base_target = FUNC1_ADDR if func_name == "ui_func_002d7f0c" else FUNC2_ADDR

    # Apply relocations
    for rel in relocs:
        offset = rel.offset
        sym = rel.symbol_name
        if rel.relocation_type in (28, 29, 10):  # R_ARM_CALL / R_ARM_JUMP24
            target = None
            if "ui_func_002c5f7c" in sym: target = STUB_2C5F7C
            elif "func_00288310" in sym: target = STUB_288310
            elif "ui_func_002c5218" in sym: target = STUB_2C5218
            elif "ui_func_002c5188" in sym: target = STUB_2C5188
            elif "func_0024a9d4" in sym: target = STUB_24A9D4
            elif "func_0024c564" in sym: target = STUB_24C564
            elif "engine_func_00281adc" in sym: target = STUB_281ADC
            elif "ui_func_002c1abc" in sym: target = STUB_2C1ABC
            elif "ui_func_002c1b64" in sym: target = STUB_2C1B64
            if target is not None:
                pc = base_target + offset + 8
                disp = (target - pc) >> 2
                orig_inst = struct.unpack_from("<I", code, offset)[0]
                cond = orig_inst & 0xFF000000
                new_inst = cond | (disp & 0x00FFFFFF)
                struct.pack_into("<I", code, offset, new_inst)
        elif rel.relocation_type == 2:  # R_ARM_ABS32
            orig_addend = struct.unpack_from("<I", code, offset)[0]
            if sym == ".text":
                target = base_target + (orig_addend - func_sym_offset)
                struct.pack_into("<I", code, offset, target)
    return bytes(code)

class EmulationRunner:
    def __init__(self):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(GPU_ADDR, GPU_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.call_log = []

        # Install stubs
        bx_lr = struct.pack("<I", 0xe12fff1e)
        stubs = [
            (STUB_2C5F7C, self._on_2c5f7c),
            (STUB_288310, self._on_288310),
            (STUB_2C5218, self._on_2c5218),
            (STUB_2C5188, self._on_2c5188),
            (STUB_24A9D4, self._on_24a9d4),
            (STUB_24C564, self._on_24c564),
            (STUB_281ADC, self._on_281adc),
            (STUB_2C1ABC, self._on_2c1abc),
            (STUB_2C1B64, self._on_2c1b64),
            (CALLBACK_ADDR, self._on_callback),
        ]
        for s_addr, s_hook in stubs:
            self.uc.mem_write(s_addr, bx_lr)
            self.uc.hook_add(unicorn.UC_HOOK_CODE, s_hook, begin=s_addr, end=s_addr)

    def _on_2c5f7c(self, uc, address, size, user_data):
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        self.call_log.append(("ui_func_002c5f7c", r0, r1))
        # 0x002c5f7c logic: r0=1, r1=0 -> 0x0f10
        ret = 0x0f10
        uc.reg_write(arm.UC_ARM_REG_R0, ret)

    def _on_288310(self, uc, address, size, user_data):
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(("func_00288310", r0))

    def _on_2c5218(self, uc, address, size, user_data):
        self.call_log.append(("ui_func_002c5218",))
        uc.reg_write(arm.UC_ARM_REG_R0, 0x1234)

    def _on_2c5188(self, uc, address, size, user_data):
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        self.call_log.append(("ui_func_002c5188", r0, r1))

    def _on_24a9d4(self, uc, address, size, user_data):
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        self.call_log.append(("func_0024a9d4", r0, r1))

    def _on_24c564(self, uc, address, size, user_data):
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(("func_0024c564", r0))

    def _on_281adc(self, uc, address, size, user_data):
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(("engine_func_00281adc", r0))

    def _on_2c1abc(self, uc, address, size, user_data):
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(("ui_func_002c1abc", r0))

    def _on_2c1b64(self, uc, address, size, user_data):
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(("ui_func_002c1b64", r0))

    def _on_callback(self, uc, address, size, user_data):
        self.call_log.append(("callback",))

    def run(self, code_bytes, func_addr, initial_state):
        self.call_log = []
        # Write code
        self.uc.mem_write(func_addr, code_bytes)

        # Clear memory
        self.uc.mem_write(DATA_ADDR, b"\x00" * DATA_SIZE)
        self.uc.mem_write(GPU_ADDR, b"\x00" * GPU_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        # Set 0x0044ea00 -> pointer to GPU_ADDR (0x00500000)
        self.uc.mem_write(0x0044ea00, struct.pack("<I", GPU_ADDR))

        # Set 0x0044ea80 state object
        state_obj_data = initial_state.get("state_obj", b"\x00" * 0x40)
        self.uc.mem_write(0x0044ea80, state_obj_data)

        # Set stacks in GPU_ADDR
        # Stack 0: GPU_ADDR + 0x11ec
        # Stack 1: GPU_ADDR + 0x124c
        # Stack 2: GPU_ADDR + 0x12ac
        for offset, s_data in initial_state.get("stacks", {}).items():
            self.uc.mem_write(GPU_ADDR + offset, s_data)

        # Init registers
        sp = STACK_ADDR + STACK_SIZE - 0x100
        self.uc.reg_write(arm.UC_ARM_REG_SP, sp)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)

        # Run
        try:
            self.uc.emu_start(func_addr, TRAP_ADDR, timeout=5000000)
        except Exception as e:
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {e}")

        # Collect state
        gpu_result = bytes(self.uc.mem_read(GPU_ADDR + 0x11ec, 0x120))
        state_result = bytes(self.uc.mem_read(0x0044ea80, 0x40))
        return {
            "call_log": list(self.call_log),
            "gpu_stacks": gpu_result,
            "state_obj": state_result,
        }

def make_stack_data(depth, entries, callback_flag=0, callback_addr=CALLBACK_ADDR):
    buf = bytearray(0x60)
    struct.pack_into("<I", buf, 0x00, depth)
    for i, e in enumerate(entries):
        struct.pack_into("<I", buf, 0x08 + i * 4, e)
    buf[0x18] = callback_flag
    struct.pack_into("<I", buf, 0x1c, callback_addr)
    return bytes(buf)

def main():
    print("Running differential tests for ui_func_002d7f0c and ui_func_002e1b90...")

    orig1_code = get_orig_bytes(FUNC1_ADDR)
    orig2_code = get_orig_bytes(FUNC2_ADDR)
    cand1_code = compile_candidate("ui_func_002d7f0c")
    cand2_code = compile_candidate("ui_func_002e1b90")

    runner = EmulationRunner()

    # Define test cases
    test_cases = []

    # Case 1: Default/minimal state (state_obj[0] = 0)
    state_obj1 = bytearray(0x40)
    state_obj1[0] = 0
    test_cases.append({
        "name": "state_obj[0]=0, callbacks=0",
        "state_obj": bytes(state_obj1),
        "stacks": {
            0x11ec: make_stack_data(0, [100]),
            0x124c: make_stack_data(0, [200]),
            0x12ac: make_stack_data(0, [300]),
        }
    })

    # Case 2: state_obj[0] = 1, calls 00288310
    state_obj2 = bytearray(0x40)
    state_obj2[0] = 1
    test_cases.append({
        "name": "state_obj[0]=1, callbacks=0",
        "state_obj": bytes(state_obj2),
        "stacks": {
            0x11ec: make_stack_data(0, [100]),
            0x124c: make_stack_data(0, [200]),
            0x12ac: make_stack_data(0, [300]),
        }
    })

    # Case 3: state_obj with extra flags at 0x10, 0x20, 0x2c
    state_obj3 = bytearray(0x40)
    state_obj3[0] = 1
    struct.pack_into("<I", state_obj3, 0x10, 0x1111)
    struct.pack_into("<I", state_obj3, 0x20, 0x2222)
    struct.pack_into("<I", state_obj3, 0x2c, 0x3333)
    test_cases.append({
        "name": "state_obj[0]=1 with flags 0x10, 0x20, 0x2c",
        "state_obj": bytes(state_obj3),
        "stacks": {
            0x11ec: make_stack_data(0, [100]),
            0x124c: make_stack_data(0, [200]),
            0x12ac: make_stack_data(0, [300]),
        }
    })

    # Case 4: callback_flag = 1 on stacks
    test_cases.append({
        "name": "callback_flag=1 on all stacks",
        "state_obj": bytes(state_obj1),
        "stacks": {
            0x11ec: make_stack_data(0, [100], callback_flag=1),
            0x124c: make_stack_data(0, [200], callback_flag=1),
            0x12ac: make_stack_data(0, [300], callback_flag=1),
        }
    })

    # Case 5: Higher initial stack depth (depth=2)
    test_cases.append({
        "name": "depth=2 initial on all stacks",
        "state_obj": bytes(state_obj3),
        "stacks": {
            0x11ec: make_stack_data(2, [10, 20, 30]),
            0x124c: make_stack_data(2, [40, 50, 60]),
            0x12ac: make_stack_data(2, [70, 80, 90]),
        }
    })

    # Case 6: Stack 0 initial entry 0 vs 1 (triggers callback comparison)
    test_cases.append({
        "name": "stack0 top entry is 0 (equal to new_val)",
        "state_obj": bytes(state_obj1),
        "stacks": {
            0x11ec: make_stack_data(0, [0]),
            0x124c: make_stack_data(0, [0x0f10]),  # equal to 002c5f7c return
            0x12ac: make_stack_data(0, [300]),
        }
    })

    total_tests = 0
    passed_tests = 0

    # Test ui_func_002d7f0c
    print("\n--- Testing ui_func_002d7f0c (mode 1) ---")
    for tc in test_cases:
        total_tests += 1
        res_orig = runner.run(orig1_code, FUNC1_ADDR, tc)
        res_cand = runner.run(cand1_code, FUNC1_ADDR, tc)

        assert res_orig["call_log"] == res_cand["call_log"], f"Call log mismatch on {tc['name']}:\n  Orig: {res_orig['call_log']}\n  Cand: {res_cand['call_log']}"
        assert res_orig["gpu_stacks"] == res_cand["gpu_stacks"], f"GPU stacks mismatch on {tc['name']}"
        assert res_orig["state_obj"] == res_cand["state_obj"], f"State obj mismatch on {tc['name']}"
        passed_tests += 1
        print(f"  [PASS] {tc['name']}")

    # Test ui_func_002e1b90
    print("\n--- Testing ui_func_002e1b90 (mode 2) ---")
    for tc in test_cases:
        total_tests += 1
        res_orig = runner.run(orig2_code, FUNC2_ADDR, tc)
        res_cand = runner.run(cand2_code, FUNC2_ADDR, tc)

        assert res_orig["call_log"] == res_cand["call_log"], f"Call log mismatch on {tc['name']}:\n  Orig: {res_orig['call_log']}\n  Cand: {res_cand['call_log']}"
        assert res_orig["gpu_stacks"] == res_cand["gpu_stacks"], f"GPU stacks mismatch on {tc['name']}"
        assert res_orig["state_obj"] == res_cand["state_obj"], f"State obj mismatch on {tc['name']}"
        passed_tests += 1
        print(f"  [PASS] {tc['name']}")

    print(f"\nAll {passed_tests}/{total_tests} differential test cases PASSED!")

if __name__ == "__main__":
    main()
