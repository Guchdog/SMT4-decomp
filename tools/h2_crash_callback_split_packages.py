from pathlib import Path
import hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from tools.h2_crash_split_packages import split,hash_bytes
from tools.h2_manual_comparison_package import ORIGINAL
from tools.h2_calc_code_patch import apply_ips
from tools.h2_azahar_rsp_probe import provision_profile,file_manifest,sha256
CALLBACK='84c6eb66a6f9a2a23d46e08df4eb04d723fef852c0b8bd3405945f9dbdd5ae32'
CALLBACK_IPS='db4919f2c3cfbdff428ed319761c88487cc83f5a52438792be9c99bb2a46e3d3'
RANGES={'calc':[('calc-entry',0x1ea928,4),('calc-body',0x3fe624,2096)],'draw-secondary':[('draw-main',0x2cafd0,1464),('draw-helper',0x3fee54,124),('draw-format',0x3feed0,3),('secondary-entry',0x2caef0,4),('secondary-body',0x3feed4,292)]}
def split_callback(original,callback,ranges=RANGES): return split(original,callback,ranges,ORIGINAL,CALLBACK)
def main():
 parent=Path('E:/SMT4decomp/build/h2-manual-comparison/run-001'); out=parent/'diagnostics/run-002'; game=parent/'pinned-title.cci'; app=parent/'original/app'; previous=parent/'diagnostics/run-001/callbacks/app/user/load/mods/00040000000E5C00/exefs/code.ips'
 original=(ROOT/'extracted/exefs/code.bin').read_bytes(); prior=previous.read_bytes()
 if hash_bytes(prior)!=CALLBACK_IPS: raise ValueError('prior callback IPS identity mismatch')
 callback=apply_ips(original,prior); images,patches,counts,labels=split_callback(original,callback)
 if out.exists(): raise FileExistsError(out)
 if sha256(game)!='9cc760c2f37da9a4a3657e918e0eaebb3e8e80a91047e5c18f95aedf0242b4c2' or sha256(app/'azahar.exe')!='c248414eb5328cb8bb720775ace6959898e2f50a0a10221c3a1e7a14190183eb': raise ValueError('pinned inputs mismatch')
 out.mkdir(parents=True)
 for group in images:
  target=out/group/'app'; shutil.copytree(app,target,ignore=shutil.ignore_patterns('user'))
  user=target/'user'; user.mkdir(); provision_profile(ROOT/'build/h2-runtime/profile-pristine-user',user)
  config=user/'config/qt-config.ini'; config.parent.mkdir(); config.write_text('[Debugging]\nuse_gdbstub\\default=false\nuse_gdbstub=false\nenable_rpc_server\\default=false\nenable_rpc_server=false\n',encoding='utf8')
  dest=user/'load/mods/00040000000E5C00/exefs/code.ips'; dest.parent.mkdir(parents=True); dest.write_bytes(patches[group])
  if apply_ips(original,dest.read_bytes())!=images[group]: raise ValueError('staged patch mismatch')
 a=file_manifest(out/'calc/app/user'); b=file_manifest(out/'draw-secondary/app/user')
 a=[x for x in a if not x['path'].endswith('/code.ips')]; b=[x for x in b if not x['path'].endswith('/code.ips')]
 if a!=b or file_manifest(out/'calc/app',{'user'})!=file_manifest(out/'draw-secondary/app',{'user'}): raise ValueError('staged profiles differ')
 manifest={'original_sha256':ORIGINAL,'callback_image_sha256':CALLBACK,'prior_callback_ips_sha256':CALLBACK_IPS,'shared_cci_sha256':sha256(game),'seed_files':a,'ranges':{g:[{'name':n,'vma_start':hex(v),'vma_end_exclusive':hex(v+s),'file_offset_start':hex(v-0x100000),'bytes':s} for n,v,s in spans] for g,spans in RANGES.items()},'subsets':{g:{'image_sha256':hash_bytes(bytes(images[g])),'ips_sha256':hash_bytes(patches[g]),'changed_bytes':counts[g]} for g in images},'composition_both_orders':True,'all_differences_owned_once':True,'runtime':'not_run'}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8'); print(json.dumps(manifest,indent=2))
if __name__=='__main__': main()
