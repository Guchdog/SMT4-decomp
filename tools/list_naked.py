import re, csv

with open('src/engine/leaf_batch30_c.cpp', 'r') as f:
    data = f.read()

matches = re.findall(r'extern "C" __attribute__\(\(naked\)\) void (\w+)\(\)', data)
print(f"Total naked functions: {len(matches)}")

# Also look up their sizes and addresses from functions.csv
sizes = {}
with open('config/functions.csv', 'r') as f:
    for row in csv.reader(f):
        if row and len(row) >= 5:
            try:
                sizes[row[4]] = (row[0], int(row[1]))
            except ValueError:
                continue

for name in matches:
    addr, sz = sizes.get(name, ('unknown', 0))
    print(f"{name:30} {addr:12} {sz:4} B")
