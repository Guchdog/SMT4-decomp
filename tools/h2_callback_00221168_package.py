import hashlib, json, runpy, struct, sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from tools.h2_calc_code_patch import encode_ips, apply_ips

ref = (root / 'extracted/exefs/code.bin').read_bytes()
base = (root / 'build/agent-work/H2-semantic/h2-final-image-composition/run-001/composed-003/code.h2-final.bin').read_bytes()
digest = lambda data: hashlib.sha256(data).hexdigest()
if digest(ref) != '1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558': raise ValueError('original hash')
if digest(base) != 'acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446': raise ValueError('H2 base hash')
entry, span = 0x221168, 148
offset = entry - 0x100000
if base[offset:offset+span] != ref[offset:offset+span]: raise ValueError('base modified candidate slot')
# Conservative aligned-word and ARM branch scan; data and unaligned/indirect
# references require separate scrutiny and are not excluded by this scan.
hits = []
for i in range(0, len(base)-3, 4):
    addr = 0x100000 + i
    word = struct.unpack_from('<I', base, i)[0]
    if entry < word < entry + span and word % 4 == 0:
        hits.append(('word', addr, word))
    if not entry <= addr < entry + span and word & 0x0e000000 == 0x0a000000:
        imm = word & 0xffffff
        if imm & 0x800000: imm -= 0x1000000
        target = addr + 8 + (imm << 2)
        if entry < target < entry + span:
            hits.append(('branch', addr, target))
if hits: raise ValueError(f'possible interior references: {hits[:20]}')
m = runpy.run_path(str(root / 'tools/h2_callback_00221168_experiment.py'))
candidate = m['candidate']
if len(candidate) != 140: raise ValueError('candidate size changed')
run = m['execute']
run.__globals__['original'] = base
for case in range(64):
    for caller, helper in ((False,False),(True,False),(True,True)):
        if run(candidate,case,False,caller,helper) != run(candidate,case,True,caller,helper):
            raise ValueError(f'H2-base differential mismatch: {case} {caller} {helper}')
patched = bytearray(base)
patched[offset:offset+len(candidate)] = candidate
patched = bytes(patched)
records = []
i = 0
while i < len(ref):
    if ref[i] == patched[i]: i += 1; continue
    start = i
    while i < len(ref) and ref[i] != patched[i] and i-start < 65535: i += 1
    records.append((start, patched[start:i]))
ips = encode_ips(records, len(ref))
if apply_ips(ref, ips) != patched: raise ValueError('IPS roundtrip')
out = root / 'build/h2-callback-00221168/integrated'
out.mkdir(parents=True, exist_ok=True)
(out/'code.bin').write_bytes(patched)
(out/'code.ips').write_bytes(ips)
(out/'manifest.json').write_text(json.dumps({'base_sha256':digest(base),'image_sha256':digest(patched),'ips_sha256':digest(ips),'candidate_sha256':digest(candidate),'candidate_size':len(candidate),'interior_scan_hits':hits,'h2_base_offline_cases':192,'limitations':['aligned words and ARM branches only','selector stubbed','one original-helper dependency stubbed']}, indent=2)+'\n')
print('H2 integrated offline checks passed; image SHA-256', digest(patched))
