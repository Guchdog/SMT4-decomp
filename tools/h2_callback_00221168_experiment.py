import hashlib, random, struct, subprocess, sys
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from tools.asm_diff import extract_elf_functions_detailed
source = root / 'experiments/semantic_equivalence/h2_callback_00221168_candidate.cpp'
out = root / 'build' / 'h2-callback-00221168'
out.mkdir(parents=True, exist_ok=True)
clang = r'C:\msys64\clang64\bin\clang++.exe'
objcopy = r'C:\msys64\clang64\bin\llvm-objcopy.exe'
original = (root / 'extracted/exefs/code.bin').read_bytes()
if hashlib.sha256(original).hexdigest() != '1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558':
    raise SystemExit('Unexpected original code.bin hash')
def compile_source(src, name):
    obj, binary = out / (name + '.o'), out / (name + '.bin')
    subprocess.run([clang, '--target=armv6k-none-eabihf', '-mcpu=mpcore', '-mfpu=vfpv2', '-mfloat-abi=hard', '-O2', '-std=c++20', '-ffreestanding', '-fno-exceptions', '-fno-rtti', '-c', str(src), '-o', str(obj)], check=True)
    subprocess.run([objcopy, '-O', 'binary', '-j', '.text', str(obj), str(binary)], check=True)
    body = bytearray(binary.read_bytes())
    symbols = extract_elf_functions_detailed(obj)
    symbol, relocs = symbols['candidate_00221168']
    targets = {'h2_set_global': 0x28df3c, 'h2_get_state': 0x289640,
               'h2_get_context': 0x28686c, 'h2_select_value': 0x296f60,
               'h2_final_helper': 0x286928}
    if len(body) > 148 or len(relocs) != 6: raise ValueError('unexpected body size or relocations')
    for rel in relocs:
        if rel.relocation_type != 28 or rel.symbol_name not in targets: raise ValueError(f'unsupported relocation {rel}')
        word = struct.unpack_from('<I', body, rel.offset)[0]
        if word != 0xebfffffe: raise ValueError('unexpected branch/addend')
        delta = targets[rel.symbol_name] - (0x221168 + rel.offset + 8)
        if delta & 3 or not -0x2000000 <= delta < 0x2000000: raise ValueError('invalid ARM branch target')
        struct.pack_into('<I', body, rel.offset, 0xeb000000 | ((delta >> 2) & 0xffffff))
    return bytes(body)

def execute(code, case, patched, caller=False, real_helper=False):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(0x100000, 0x600000)
    uc.mem_write(0x100000, original)
    if patched: uc.mem_write(0x221168, code)
    uc.mem_map(0x700000, 0x10000)
    uc.mem_write(0x700000, code)
    uc.mem_map(0x800000, 0x50000)
    uc.mem_map(0x900000, 0x10000)
    rng = random.Random(case)
    obj1 = 0x800000 if case & 1 else 0
    if real_helper: obj1 = 0x800000
    obj2 = 0x800000 if case & 8 and obj1 else 0x802000
    uc.mem_write(0x800000, bytes(rng.randrange(256) for _ in range(0x4000)))
    if real_helper:
        uc.mem_write(obj1 + 8, bytes([4 if case & 4 else 1]))
        uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    w = lambda a, v: uc.mem_write(a, struct.pack('<I', v & 0xffffffff))
    w(0x43e18c, obj1); w(0x43e190, obj2)
    w(0x44deb8, 0x805000); w(0x8050d0, 0 if case & 2 and not real_helper else 0x1234); w(0x8050c0, 0x31415926)
    if caller:
        w(0x806018, 0); w(0x80601c, 9); w(0x8060bc, 0x807000)
        w(0x8060d0, 0 if case & 2 and not real_helper else 0x1234); w(0x8060c0, 0x31415926)
        uc.mem_write(0x807002, struct.pack('<H', 33))
        w(0x406140, 0x221168); w(0x406144, 1)
        uc.reg_write(UC_ARM_REG_R0, 0x806000)
    sp = 0x90f000
    uc.reg_write(UC_ARM_REG_SP, sp); uc.reg_write(UC_ARM_REG_LR, 0x600000)
    regs = [UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11]
    for i, reg in enumerate(regs): uc.reg_write(reg, 0x11110000 + i)
    events = []
    writes = []
    reached_stop = False
    def memory_write(u, access, address, size, value, data):
        if not 0x900000 <= address < 0x910000:
            writes.append((address, size, value))
    uc.hook_add(UC_HOOK_MEM_WRITE, memory_write)
    def hook(u, addr, size, data):
        nonlocal reached_stop
        if addr == 0x600000:
            reached_stop = True
            u.emu_stop(); return
        if addr in (0x28df3c, 0x289640, 0x28686c, 0x296f60, 0x286928, 0x2c1f28):
            if u.reg_read(UC_ARM_REG_CPSR) & 0x20 or u.reg_read(UC_ARM_REG_SP) & 7:
                raise AssertionError(f'ARM state/stack alignment invalid at {addr:#x}')
            args = [u.reg_read(UC_ARM_REG_R0)]
            if addr == 0x286928:
                args += [u.reg_read(UC_ARM_REG_R1), u.reg_read(UC_ARM_REG_R2), u.reg_read(UC_ARM_REG_R3)]
                args += list(struct.unpack('<II', u.mem_read(u.reg_read(UC_ARM_REG_SP), 8)))
            events.append((addr, args))
            if addr == 0x2c1f28:
                u.reg_write(UC_ARM_REG_R0, 0)
                u.reg_write(UC_ARM_REG_PC, u.reg_read(UC_ARM_REG_LR))
            elif addr == 0x296f60 or (addr == 0x286928 and not real_helper):
                if addr == 0x296f60 and case & 16:
                    w((0x806000 if caller else 0x805000) + 0xd0, 0x778899aa)
                if addr == 0x286928 and caller and case & 32:
                    w(0x806018, 3)
                u.reg_write(UC_ARM_REG_R0, (0x98765432 if case & 8 else 0) if addr == 0x296f60 else (0 if case & 4 else 0x89abcdef))
                u.reg_write(UC_ARM_REG_PC, u.reg_read(UC_ARM_REG_LR))
    uc.hook_add(UC_HOOK_CODE, hook)
    uc.emu_start(0x1a07cc if caller else 0x221168, 0, count=5000)
    if not reached_stop: raise AssertionError('execution did not return to sentinel')
    return (uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_SP), [uc.reg_read(r) for r in regs], events, writes, bytes(uc.mem_read(0x800000, 0x4000)), bytes(uc.mem_read(0x43e0bc, 4)), bytes(uc.mem_read(0x806000, 0x100)))

candidate = compile_source(source, 'h2_callback_candidate')
source_text = source.read_text()
mutations = [('branch', 'if (state == 0)', 'if (state != 0)'),
             ('write', 'object[0xa11] = 0x14', 'object[0xa11] = 0x15'),
             ('stack', 'current, 6, 1, 0)', 'current, 6, 0, 1)'),
             ('return', 'return h2_final_helper(context, value, current, 6, 1, 0);',
                        'return h2_final_helper(context, value, current, 6, 1, 0) != 0;')]
mutants = {}
for name, before, after in mutations:
    if source_text.count(before) != 1: raise ValueError(f'mutation {name} not unique')
    path = out / f'h2_callback_mutant_{name}.cpp'
    path.write_text(source_text.replace(before, after), encoding='utf-8')
    mutants[name] = compile_source(path, f'h2_callback_mutant_{name}')
detected = {name:0 for name in mutants}
for case in range(64):
    reference = execute(candidate, case, False)
    actual = execute(candidate, case, True)
    if reference != actual:
        raise SystemExit(f'candidate mismatch at case {case}: {reference[:4]} vs {actual[:4]}')
    for name, mutant in mutants.items():
        if execute(mutant, case, True) != reference: detected[name] += 1
    if execute(candidate, case, False, True) != execute(candidate, case, True, True):
        raise SystemExit(f'caller mismatch at case {case}')
    if execute(candidate, case, False, True, True) != execute(candidate, case, True, True, True):
        raise SystemExit(f'original helper composition mismatch at case {case}')
if not all(detected.values()):
    raise SystemExit(f'negative control not detected: {detected}')
print(f'PASS: 64/64 direct, 64/64 caller and 64/64 original-helper caller comparisons; negative-control detections {detected}; selector and one helper dependency stubbed.')
