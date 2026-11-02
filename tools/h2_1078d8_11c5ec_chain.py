#!/usr/bin/env python3
"""Compose the production H2 input refresher and state reader in one staged image."""
from __future__ import annotations
import argparse, hashlib, json, random, struct
from pathlib import Path
import sys
import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import h2_1078d8_experiment as refresh
from tools import h2_11c5ec_experiment as reader
from tools.h2_calc_code_patch import apply_ips, encode_ips

IMAGE = ROOT / 'extracted/exefs/code.bin'
IMAGE_SHA = refresh.IMAGE_SHA
REFRESH = refresh.ADDRESS
READER = reader.ADDRESS
IMAGE_BASE = refresh.ENTRY
CODE_SIZE = refresh.CODE_SIZE
INPUT, TABLE, STATE, COUNTERS = refresh.INPUT, refresh.TABLE, refresh.STATE, refresh.COUNTERS
CTX, OBJECT, SOURCE = 0x00500000, 0x00510000, 0x00520000
DATA_SIZE = 0x40000
STACK, STACK_SIZE, SP = 0x08000000, 0x10000, 0x08008000
STOP = STACK + 0x9000
U32 = 0xFFFFFFFF


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_staged(out: Path, original: bytes):
    reader_body, reader_relocs, reader_args = reader.compile_body(out / 'reader-build')
    refresh_body, refresh_relocs, refresh_args = refresh.build_body(out / 'refresh-build')
    if len(reader_body) != 304 or len(refresh_body) > 164:
        raise ValueError(f'unexpected body sizes: reader={len(reader_body)}, refresh={len(refresh_body)}')
    if READER & 3:
        raise ValueError('reader entry is not word aligned ARM')
    if not any(x['symbol'] == 'func_0011c5ec' and x['type'] == 28 for x in refresh_relocs):
        raise ValueError('refresher lacks even ARM R_ARM_CALL to state reader')
    r_payload = reader_body
    f_payload = refresh_body + struct.pack('<I', 0xE320F000) * ((164-len(refresh_body))//4)
    staged = bytearray(original)
    roff, foff = READER-IMAGE_BASE, REFRESH-IMAGE_BASE
    staged[roff:roff+304] = r_payload
    staged[foff:foff+164] = f_payload
    patches = [(roff,r_payload),(foff,f_payload)]
    ips = encode_ips(patches, len(original))
    result = bytes(staged)
    if apply_ips(original, ips) != result:
        raise AssertionError('two-slot IPS replay differs from staged image')
    (out/'staged-image.bin').write_bytes(result)
    (out/'staged-slots.ips').write_bytes(ips)
    return result, reader_body, refresh_body, reader_relocs, refresh_relocs, reader_args, refresh_args, patches


class Machine:
    def __init__(self, image: bytes, case: dict):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM|unicorn.UC_MODE_LITTLE_ENDIAN)
        self.uc.mem_map(IMAGE_BASE, CODE_SIZE)
        self.uc.mem_write(IMAGE_BASE,image)
        self.uc.mem_map(0x004E3000,0x1000)
        self.uc.mem_map(CTX,DATA_SIZE)
        self.uc.mem_map(STACK,STACK_SIZE)
        self.case=case; self.writes=[]; self.ring_calls=[]
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE,self._write)
        self.uc.hook_add(unicorn.UC_HOOK_CODE,self._ring,begin=reader.RING_READER,end=reader.RING_READER)
        self.uc.hook_add(unicorn.UC_HOOK_CODE,self._stop,begin=STOP,end=STOP)
        self.setup()

    @staticmethod
    def _stop(uc,_address,_size,_data): uc.emu_stop()

    def _write(self,uc,_access,address,size,value,_data):
        self.writes.append((address,size,value&U32))

    def _ring(self,uc,_address,_size,_data):
        sp=uc.reg_read(arm.UC_ARM_REG_SP)
        args=[uc.reg_read(getattr(arm,f'UC_ARM_REG_R{i}')) for i in range(4)]
        stack=list(struct.unpack('<II',uc.mem_read(sp,8)))
        src,out,requested,count_ptr=args; timestamp_ptr,index_ptr=stack
        self.ring_calls.append({'source_is_fixture':src==SOURCE,'output':out,'requested':requested,
          'count_out_in_frame':SP-0x200<=count_ptr<SP,
          'timestamp_out_in_frame':SP-0x200<=timestamp_ptr<SP,
          'index_out_in_frame':SP-0x200<=index_ptr<SP,'sp_aligned_8':sp%8==0})
        if self.case['count']>0:
            w=self.case['record']; uc.mem_write(out,struct.pack('<IIIhh',*w))
        uc.mem_write(count_ptr,struct.pack('<i',self.case['count']))
        uc.mem_write(timestamp_ptr,struct.pack('<Q',0x1122334455667788))
        uc.mem_write(index_ptr,struct.pack('<I',0x12345678))
        uc.reg_write(arm.UC_ARM_REG_R0,0x76543210)
        uc.reg_write(arm.UC_ARM_REG_PC,uc.reg_read(arm.UC_ARM_REG_LR))

    def setup(self):
        c=self.case
        self.uc.mem_write(CTX,c['context_bytes'])
        self.uc.mem_write(CTX,struct.pack('<I',OBJECT))
        self.uc.mem_write(OBJECT,bytes(16))
        self.uc.mem_write(OBJECT+4,struct.pack('<I',SOURCE))
        self.uc.mem_write(SOURCE,bytes(0x100))
        self.uc.mem_write(INPUT,struct.pack('<I',CTX))
        self.uc.mem_write(INPUT+4,struct.pack('<I',0xBAD0BAD0))
        self.uc.mem_write(STATE,c['output_bytes'])
        self.uc.mem_write(TABLE,b''.join(struct.pack('<II',*x) for x in c['table']))
        self.uc.mem_write(COUNTERS,b''.join(struct.pack('<I',x) for x in c['counters']))
        for addr,val in ((reader.MODE,c['mode']),(reader.FLAG_A,c['flag_a']),
                         (reader.FLAG_B,c['flag_b']),(reader.POSTPROCESS_GATE,c['post_gate'])):
            self.uc.mem_write(addr,bytes((val,)))

    def run(self):
        regs=[getattr(arm,f'UC_ARM_REG_R{i}') for i in range(13)]
        init=[(0xC1000000+i*0x01010101)&U32 for i in range(13)]
        for r,v in zip(regs,init): self.uc.reg_write(r,v)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC,0x40000000)
        self.uc.reg_write(arm.UC_ARM_REG_SP,SP); self.uc.reg_write(arm.UC_ARM_REG_LR,STOP)
        fault=None
        try: self.uc.emu_start(REFRESH,0,count=100000)
        except unicorn.UcError as e: fault=str(e)
        after=[self.uc.reg_read(r) for r in regs]
        relevant=[x for x in self.writes if
            (STATE<=x[0]<STATE+0x20) or (CTX<=x[0]<CTX+0x60) or
            x[0]==INPUT+4 or COUNTERS<=x[0]<COUNTERS+128]
        return {'fault':fault,'sp':self.uc.reg_read(arm.UC_ARM_REG_SP),
          'callee_saved':after[4:12]==init[4:12],
          'context':bytes(self.uc.mem_read(CTX,0x60)).hex(),
          'state':bytes(self.uc.mem_read(STATE,0x20)).hex(),
          'availability':struct.unpack('<I',self.uc.mem_read(INPUT+4,4))[0],
          'counters':list(struct.unpack('<32I',self.uc.mem_read(COUNTERS,128))),
          'ring_calls':self.ring_calls.copy(),'global_writes':relevant}


def make_case(index:int,seed:int,mode:int,count:int,selector:int,flag_a:int,flag_b:int,post_gate:int):
    rng=random.Random((seed&U32)^(index*0x9E3779B1))
    context=bytearray(rng.randrange(256) for _ in range(0x60))
    context[0x30]=index&1
    struct.pack_into('<B',context,0x18,selector)
    for off,value in ((0x0C,20+index%25),(0x0E,28+index%21),(0x12,130+index%25),(0x14,145-index%9),(0x16,200-index%60)):
        struct.pack_into('<h',context,off,value)
    w=[rng.getrandbits(32) for _ in range(3)]
    if index&2:w[0]|=0x2000
    record=(*w,rng.randint(-32768,32767),rng.randint(-32768,32767))
    table=[]
    for row in range(31):
        gate=1 if (index+row)%11==0 else 0
        mask=(1<<((index+row)%32))
        table.append((gate,mask))
    counters=[rng.getrandbits(32) for _ in range(31)]+[0xDEADBEEF]
    output=bytes(rng.randrange(256) for _ in range(0x20))
    return {'mode':mode,'count':count,'selector':selector,'flag_a':flag_a,'flag_b':flag_b,'post_gate':post_gate,
      'context_bytes':bytes(context),'output_bytes':output,'record':record,'table':table,'counters':counters}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--seed',type=int,default=20261116); args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True); original=IMAGE.read_bytes()
    if sha(original)!=IMAGE_SHA: raise SystemExit('pinned original image hash mismatch')
    staged,reader_body,refresh_body,reader_relocs,refresh_relocs,reader_args,refresh_args,patches=build_staged(args.out,original)
    cases=[]; index=0
    for mode in (0,4):
      for count in (-1,0,1):
       for selector in (0,1,2,3):
        for a,b in ((0,0),(1,0),(1,1)):
         for post in (0,1):
          cases.append(make_case(index,args.seed,mode,count,selector,a,b,post)); index+=1
    mismatch=[]; all_results=[]
    for i,case in enumerate(cases):
      ref=Machine(original,case).run(); got=Machine(staged,case).run()
      all_results.append((ref,got))
      if ref!=got:mismatch.append({'case':i,'original':ref,'candidate':got})
    fixture_hash=sha(json.dumps(cases,sort_keys=True,separators=(',',':'),default=lambda x:x.hex()).encode())
    sorted_ranges=sorted((off,off+len(payload)) for off,payload in patches)
    cursor=0; only_slots=True
    for start,end in sorted_ranges:
      only_slots=only_slots and original[cursor:start]==staged[cursor:start]
      cursor=end
    only_slots=only_slots and original[cursor:]==staged[cursor:]
    case_summary=[]
    for i,(case,(ref,got)) in enumerate(zip(cases,all_results)):
      case_summary.append({'case':i,'mode':case['mode'],'count':case['count'],
        'selector':case['selector'],'flags':[case['flag_a'],case['flag_b']],
        'post_gate':case['post_gate'],'equal':ref==got,
        'availability':ref['availability'],'state_word':ref['state'][:8],
        'counter_head':ref['counters'][:4],'counter_tail':ref['counters'][-2:],
        'ring_calls':ref['ring_calls'],'ordered_write_count':len(ref['global_writes']),
        'abi_ok':ref['callee_saved'] and got['callee_saved'] and ref['sp']==SP and got['sp']==SP})
    report={'image_sha256':sha(original),'fixture_sha256':fixture_hash,'seed':args.seed,
      'reader_body_bytes':len(reader_body),'refresh_body_bytes':len(refresh_body),
      'reader_relocations':reader_relocs,'refresh_relocations':refresh_relocs,
      'direct_compositions':len(cases),'mismatches':mismatch,'case_summary':case_summary,
      'exact_two_slot_ips_replay':True,
      'patched_slots':[{'address':hex(IMAGE_BASE+off),'size':len(payload),'sha256':sha(payload)} for off,payload in patches],
      'only_declared_slots_changed':only_slots,
      'all_passed':False,
      'scope':'pinned original versus both production C++ bodies staged at original VMAs; valid disjoint synthetic memory; 0x0012A758 ring-reader seam controlled'}
    report['all_passed']=not mismatch and report['only_declared_slots_changed'] and all(
      not ref['fault'] and not got['fault'] and ref['callee_saved'] and got['callee_saved'] and ref['sp']==SP and got['sp']==SP and
      all(call['source_is_fixture'] and call['requested']==1 and call['sp_aligned_8'] and call['count_out_in_frame'] and call['timestamp_out_in_frame'] and call['index_out_in_frame'] for call in ref['ring_calls']+got['ring_calls'])
      for ref,got in all_results)
    (args.out/'staged-image.bin').write_bytes(staged)
    (args.out/'staged-slots.ips').write_bytes(encode_ips(patches,len(original)))
    (args.out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'all_passed':report['all_passed'],'compositions':len(cases),'mismatches':len(mismatch),'fixture_sha256':fixture_hash,'report':str(args.out/'report.json')}))
    return 0 if report['all_passed'] else 1
if __name__=='__main__': raise SystemExit(main())
