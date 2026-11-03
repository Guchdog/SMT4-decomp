import re

with open('src/engine/leaf_batch31_c.cpp', 'r') as f:
    text = f.read()

pattern = r'// DECOMP_FUNC\((0x[0-9a-fA-F]+),\s*(\d+)\)\s*\nextern "C" __attribute__\(\(naked\)\) void (\w+)\(\)'
matches = re.findall(pattern, text)
print(f"Total remaining naked functions: {len(matches)}")
for i, m in enumerate(matches[:15]):
    print(f"#{i+51}: addr={m[0]}, size={m[1]}, name={m[2]}")
