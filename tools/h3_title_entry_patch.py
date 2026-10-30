#!/usr/bin/env python3
"""Compose the validated H3 title-entry candidate over the audited H1/H2 image."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k,find_clang,get_armv6k_flags
from tools.h2_calc_code_patch import apply_ips,encode_ips
from tools.h3_candidate_support import relocate_h3_entry
ORIGINAL=ROOT/'extracted/exefs/code.bin'
BASE=ROOT/'build/agent-work/H2-semantic/h2-init-ready-final-image/run-013/combined-build-final/code.combined.bin'
SOURCE=ROOT/'experiments/semantic_equivalence/h3_title_load_entry_candidate.cpp'
ADDRESS=0x0030A9A4; TEXT=0x00100000; NEXT=0x0030AA1C
ORIGINAL_SHA='1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
BASE_SHA='7b2bc2983a890e1c4cf1ae71beca9f574260d98d6cfcdffb3bbb34bd3eb2b291'

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def changed_records(before:bytes,after:bytes)->list[tuple[int,bytes]]:
    out=[]; i=0
    while i<len(before):
        if before[i]==after[i]: i+=1; continue
        start=i; i+=1
        while i<len(before) and before[i]!=after[i] and i-start<0xffff: i+=1
        out.append((start,after[start:i]))
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
    original=ORIGINAL.read_bytes(); base=BASE.read_bytes()
    if sha(original)!=ORIGINAL_SHA: raise SystemExit('pinned original hash mismatch')
    if sha(base)!=BASE_SHA: raise SystemExit('pinned H1/H2 image hash mismatch')
    if len(original)!=len(base): raise SystemExit('composed image size differs')
    off=ADDRESS-TEXT; end=off+0x78
    if base[off:end]!=original[off:end]: raise SystemExit('H1/H2 base changed the H3 entry window')
    if ADDRESS+0x78!=NEXT: raise SystemExit('candidate window does not end at next function entry')
    a.output.mkdir(parents=True,exist_ok=False)
    obj=a.output/'h3_title_load_entry_candidate.o'
    result=compile_tu_armv6k(SOURCE,obj,ROOT)
    if result.returncode: raise SystemExit(result.stderr or 'candidate compile failed')
    code,relocs=extract_elf_functions_detailed(obj)['h3_title_load_entry_candidate']
    if len(code)!=0x78: raise SystemExit(f'candidate is {len(code)} bytes; expected exact 0x78-byte window')
    linked,rows=relocate_h3_entry(code,relocs,ADDRESS)
    if linked[0x74:0x78] != original[off+0x74:off+0x78]:
        # Manager literal is expected to remain the same absolute global address.
        raise SystemExit('candidate literal pool does not preserve manager address')
    final=bytearray(base); final[off:end]=linked; final=bytes(final)
    records=changed_records(original,final); ips=encode_ips(records,len(original))
    if apply_ips(original,ips)!=final: raise SystemExit('IPS round trip mismatch')
    if final[off:end]!=linked or final[off+0x78:NEXT-TEXT]==base[off+0x78:NEXT-TEXT]: pass
    image_path=a.output/'code.h3-final.bin'; ips_path=a.output/'code.h3-final.ips'
    image_path.write_bytes(final); ips_path.write_bytes(ips)
    report={'status':'passed','scope':'H1/H2 composed image plus in-place H3 0x0030A9A4 replacement','original_sha256':sha(original),'h1_h2_base_sha256':sha(base),'candidate_source_sha256':sha(SOURCE.read_bytes()),'candidate_object_sha256':sha(obj.read_bytes()),'candidate_size':len(code),'candidate_relocations':rows,'entry_vma':hex(ADDRESS),'window_file_offset':hex(off),'window_size':len(linked),'next_entry_vma':hex(NEXT),'outside_entry_window_matches_h1_h2':final[:off]==base[:off] and final[end:]==base[end:],'ips_sha256':sha(ips),'ips_record_count':len(records),'ips_round_trip':True,'final_image_sha256':sha(final),'image_path':str(image_path),'ips_path':str(ips_path)}
    (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
