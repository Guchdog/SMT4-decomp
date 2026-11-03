from pathlib import Path
import sys, struct, unicorn, json, argparse, hashlib
from unicorn.arm_const import *
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))

cmps={0x206cbc,0x2e4608,0x206c38,0x2e4584,0x2dca98,0x2c6d30,0x1f61a4,0x1d1bb8}
def run(code,mode,values):
 u=unicorn.Uc(unicorn.UC_ARCH_ARM,unicorn.UC_MODE_ARM);u.ctl_set_cpu_model(UC_CPU_ARM_11MPCORE);u.mem_map(0x100000,0x480000);u.mem_write(0x100000,code);u.mem_map(0x8000000,0x10000);u.mem_map(0xfff0000,0x10000)
 work=0x8001000; opt=0x8009000;u.mem_write(0x44e190,struct.pack('<I',work));u.mem_write(opt+0x16,bytes([mode]));u.mem_write(work+0x2230,struct.pack('<h',len(values)));u.mem_write(work+0xe30,struct.pack('<%di'%len(values),*values));u.reg_write(UC_ARM_REG_SP,0xfff8000);u.reg_write(UC_ARM_REG_LR,0x100004);events=[]
 def hook(uc,addr,size,data):
  if addr==0x2a0fac:uc.reg_write(UC_ARM_REG_R0,opt);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
  elif addr in cmps:
   events.append(hex(addr));a,b=uc.reg_read(UC_ARM_REG_R0),uc.reg_read(UC_ARM_REG_R1);x=struct.unpack('<i',uc.mem_read(a,4))[0];y=struct.unpack('<i',uc.mem_read(b,4))[0];val=(x>y)-(x<y);val=-val if mode&128 else val;uc.reg_write(UC_ARM_REG_R0,val&0xffffffff);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
  elif addr==0x2b7f0a:events.append('qsort-thumb' if uc.reg_read(UC_ARM_REG_CPSR)&32 else 'qsort-arm')
 u.hook_add(unicorn.UC_HOOK_CODE,hook)
 try:
  u.emu_start(0x32c4bc,0x100004,count=100000);pc=u.reg_read(UC_ARM_REG_PC);array=list(struct.unpack('<%di'%len(values),u.mem_read(work+0xe30,len(values)*4)));return {'pc':hex(pc),'array':array,'events':events}
 except Exception as e:return {'fault':repr(e),'pc':hex(u.reg_read(UC_ARM_REG_PC)),'events':events}

def main():
 parser=argparse.ArgumentParser(description='Bounded original-vs-integrated item sort caller test')
 parser.add_argument('--image',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
 original=(root/'extracted/exefs/code.bin').read_bytes();patched=args.image.read_bytes()
 if len(original)!=len(patched):raise ValueError('image length mismatch')
 results=[]
 for values in ([7,-3,5,0],[1,1,0,1],[42],[3,2]):
  for mode in (0,1,0x81,2,0x82,3,0x83,8,0x88):
   a=run(original,mode,values);b=run(patched,mode,values)
   ok=a==b and a.get('pc')=='0x100004' and 'fault' not in a
   results.append({'mode':mode,'input':values,'passed':ok,'original':a,'patched':b})
 mutant=bytearray(patched);site=0x32c51c-0x100000;mutant[site:site+4]=struct.pack('<I',0xeafe2e67)
 negative=run(bytes(mutant),1,[7,-3,5,0]);detected=negative.get('fault') is not None or negative.get('pc')!='0x100004'
 report={'original_sha256':hashlib.sha256(original).hexdigest(),'image_sha256':hashlib.sha256(patched).hexdigest(),'scope':'full item-sort caller, real Thumb qsort; option accessor and comparator bodies hooked','passed':all(r['passed'] for r in results) and detected,'cases':results,'negative_control_detected':detected,'negative_control':negative,'limits':['Comparator implementations are hooked and not validated.','Only specified input arrays and modes are covered.','Register preservation and entire memory footprint are not compared.']}
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps({'passed':report['passed'],'cases':len(results),'negative_control_detected':detected,'image_sha256':report['image_sha256']}));return 0 if report['passed'] else 1
if __name__=='__main__':sys.exit(main())
