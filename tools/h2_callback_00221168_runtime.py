import hashlib, json, runpy, sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from tools import h2_autonomous_gdb_verify as base
from tools import h2_postconfirm_nested_callback_trace as observer

runpy.run_path(str(root/'tools/h2_callback_00221168_package.py'))
folder = root/'build/h2-callback-00221168/integrated'
manifest = json.loads((folder/'manifest.json').read_text())
for name, key in [('code.bin','image_sha256'),('code.ips','ips_sha256')]:
    if hashlib.sha256((folder/name).read_bytes()).hexdigest() != manifest[key]: raise ValueError('package hash changed')
output = root/'build/h2-callback-00221168/runtime-observed-001'
old = base.wait_for_title_reset_after_confirm
base.wait_for_title_reset_after_confirm = observer.traced_wait
try:
    rc = base.main(['--final-image', str(folder/'code.bin'), '--final-ips', str(folder/'code.ips'), '--output-dir', str(output), '--startup-timeout', '180', '--base-port', '59950'])
finally:
    base.wait_for_title_reset_after_confirm = old
if rc: raise SystemExit(rc)
path = output/'autonomous-gdb-verification.json'
report = json.loads(path.read_text())
comparison = observer.compare_traces(report)
(output/'nested-callback-comparison.json').write_text(json.dumps(comparison, indent=2)+'\n')
print(json.dumps(comparison, indent=2))
if comparison['status'] != 'matched_observed_events': raise SystemExit('nested callback trace missing or divergent')
if not all(e.get('nested_target_at_blx_raw') == hex(0x221168) for e in comparison['original_events']):
    raise SystemExit('unexpected nested callback target')
