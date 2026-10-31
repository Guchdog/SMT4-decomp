import capstone

with open('extracted/exefs/code.bin', 'rb') as f:
    code = f.read()

VMA_BASE = 0x00100000
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)

funcs = [
    (0x0038B030, 16, "func_0038b030"),
    (0x0038B600, 24, "func_0038b600"),
    (0x0038B618, 32, "func_0038b618"),
    (0x0038B638, 44, "func_0038b638"),
    (0x0038C248, 28, "func_0038c248"),
]

for addr, size, name in funcs:
    offset = addr - VMA_BASE
    data = code[offset:offset+size]
    print(f"=== {name} (0x{addr:08X}, {size}B) ===")
    for insn in md.disasm(data, addr):
        print(f"  0x{insn.address:08X}: {insn.mnemonic:<8} {insn.op_str}")
    print()
