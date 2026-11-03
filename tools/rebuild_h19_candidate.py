#!/usr/bin/env python3
"""Rebuild the H8-H19 staged chain in a fresh, isolated output directory."""
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.h2_calc_code_patch import encode_ips,apply_ips
from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

def sha(data): return hashlib.sha256(data).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=False)
    first=importlib.import_module('tools.h8_staged_image_patch')
    if sha(first.ORIGINAL.read_bytes()) != first.ORIGINAL_SHA or sha(first.DEFAULT_BASE.read_bytes()) != first.H7_BASE_SHA:
        raise ValueError('original or H7 base hash mismatch')
    # H7 descends from an older H2 composition whose draw callback clears the
    # Thumb state bit on the formatting function. Restore the separately
    # validated H2 instruction, after pinning both inputs and the old word.
    h2=ROOT/'build/agent-work/H2-semantic/h2-final-image-composition/run-001/composed-003/code.h2-final.bin'
    if sha(h2.read_bytes()) != 'acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446':
        raise ValueError('validated H2 image hash mismatch')
    data=bytearray(first.DEFAULT_BASE.read_bytes());off=0x002cb258-0x00100000
    if data[off:off+4] != bytes.fromhex('80308ae2') or h2.read_bytes()[off:off+4] != bytes.fromhex('81308ae2'):
        raise ValueError('unexpected title formatting target instruction')
    data[off:off+4]=h2.read_bytes()[off:off+4]
    # Restore reviewed H2 production helper windows, but only after compiling
    # the current sources and proving their bodies are identical to H2.
    original=first.ORIGINAL.read_bytes();h2_image=h2.read_bytes()
    helper_specs=[('src/engine/leaf_batch32_b.cpp',[('camp_func_0021f39c',0x21f39c,92)]),
                  ('src/engine/leaf_batch32_c.cpp',[('camp_func_002cab70',0x2cab70,92),('camp_func_002e0af4',0x2e0af4,92)]),
                  ('src/engine/leaf_matching.cpp',[('camp_func_0027edf8',0x27edf8,24)])]
    h2_helpers=[];provenance=out/'h2-current-sources';provenance.mkdir()
    for index,(source,specs) in enumerate(helper_specs):
        obj=provenance/f'unit{index}.o';res=compile_tu_armv6k(ROOT/source,obj,ROOT)
        if res.returncode:raise RuntimeError(f'Failed to compile {source}: {res.stderr}')
        funcs=extract_elf_functions_detailed(obj)
        for symbol,addr,width in specs:
            raw,relocs=funcs[symbol];start=addr-0x100000
            if relocs or len(raw)>width or raw!=h2_image[start:start+len(raw)]:
                raise ValueError(f'Current {symbol} differs from validated H2 body')
            if data[start:start+width]!=original[start:start+width]:
                raise ValueError(f'H7 base unexpectedly changes {symbol}')
            data[start:start+width]=h2_image[start:start+width]
            h2_helpers.append({'symbol':symbol,'vma':hex(addr),'window_bytes':width,'source':source,
                               'source_sha256':sha((ROOT/source).read_bytes()),'object_sha256':sha(obj.read_bytes()),
                               'body_sha256':sha(raw)})
    prev=out/'code.h7-title-fixed.bin';prev.write_bytes(data);stages=[]
    for n in range(8,20):
        mod=importlib.import_module(f'tools.h{n}_staged_image_patch')
        base=prev if prev is not None else mod.DEFAULT_BASE
        stage=out/f'h{n}';stage.mkdir()
        if n<=10:mod.stage_candidates(stage,base);dest=stage/f'code.h{n}-final.bin'
        elif n==11:mod.stage_composite_image(base,stage);dest=stage/f'code.h{n}-final.bin'
        else:
            data,_=mod.patch_binary(base.read_bytes(),stage)
            dest=stage/f'code.h{n}-final.bin';dest.write_bytes(data)
        sources=[]
        for item in getattr(mod,'SUBSYSTEMS',getattr(mod,'CRT_SUBSYSTEMS',[])):
            if 'src' in item:
                path=ROOT/item['src'];sources.append({'path':item['src'],'sha256':sha(path.read_bytes())})
        stages.append({'stage':n,'base_sha256':sha(base.read_bytes()),'image_sha256':sha(dest.read_bytes()),'script_sha256':sha(Path(mod.__file__).read_bytes()),'sources':sources})
        prev=dest
    original=(ROOT/'extracted/exefs/code.bin').read_bytes();image=prev.read_bytes()
    if len(original)!=len(image):raise ValueError('image length differs from reference')
    for entry in h2_helpers:
        start=int(entry['vma'],16)-0x100000;width=entry['window_bytes']
        if image[start:start+width]!=h2_image[start:start+width]:raise ValueError(f"Later stage overwrote {entry['symbol']}")
    records=[];i=0
    while i<len(original):
        if original[i]==image[i]:i+=1;continue
        start=i
        while i<len(original) and original[i]!=image[i] and i-start<65535:i+=1
        records.append((start,image[start:i]))
    ips=encode_ips(records,len(original))
    if apply_ips(original,ips)!=image:raise ValueError('IPS roundtrip failed')
    (out/'code.h19-rebuilt.ips').write_bytes(ips)
    manifest={'scope':'H8-H19 staging on H7 with validated H2 Thumb-bit repair; not a full source link','original_sha256':sha(original),'image_sha256':sha(image),'ips_sha256':sha(ips),'ips_roundtrip':True,'h2_current_source_helpers':h2_helpers,'stages':stages,'support_sha256':{name:sha((ROOT/name).read_bytes()) for name in ('tools/build_check.py','tools/asm_diff.py','tools/arm_interworking.py','tools/local_section_relocations.py','tools/rebuild_h19_candidate.py')}}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'image_sha256':sha(image),'ips_sha256':sha(ips),'ips_roundtrip':True},indent=2))
    return 0
if __name__=='__main__':sys.exit(main())
