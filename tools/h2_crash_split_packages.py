from pathlib import Path
import hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from tools.h2_manual_comparison_package import compose, ORIGINAL, FINAL
from tools.h2_calc_code_patch import apply_ips
from tools.h2_azahar_rsp_probe import provision_profile,file_manifest,sha256
# VMA intervals, exclusive upper bound, derived from run-013 manifest and
# mapper/fill production integration spans. Image base 0x100000.
RANGES={'init-deps': [('fill',0x27edf8,24),('mapper-a',0x2cab70,92),('mapper-b',0x21f39c,92),('mapper-c',0x2e0af4,92),('initializer',0x2f4ca0,572),('ready',0x2fc0ec,48),('strings',0x42ab78,68)], 'callbacks': [('calc-entry',0x1ea928,4),('secondary-entry',0x2caef0,4),('draw',0x2cafd0,1464),('cave',0x3fe624,2524)]}
def hash_bytes(b): return hashlib.sha256(b).hexdigest()
def split(original,final,ranges=RANGES,expected_original=ORIGINAL,expected_final=FINAL):
 if hash_bytes(original)!=expected_original or hash_bytes(final)!=expected_final: raise ValueError('image identity mismatch')
 if len(original)!=len(final): raise ValueError('size mismatch')
 ownership=bytearray(len(original)); labels={};
 for i,(group,spans) in enumerate(ranges.items(),1):
  for label,vma,size in spans:
   start=vma-0x100000; end=start+size
   if start<0 or end>len(original) or size<=0: raise ValueError('invalid range')
   if any(ownership[start:end]): raise ValueError('overlapping ranges')
   ownership[start:end]=bytes([i])*size; labels[label]=(start,end)
 images={group:bytearray(original) for group in ranges}; counts={group:0 for group in ranges}
 groups=list(ranges)
 for pos,(a,b) in enumerate(zip(original,final)):
  if a==b: continue
  owner=ownership[pos]
  if not owner: raise ValueError(f'unclassified difference at {pos:#x}')
  group=groups[owner-1]; images[group][pos]=b; counts[group]+=1
 patches={g:compose(original,bytes(data))[0] for g,data in images.items()}
 if len(groups)!=2: raise ValueError('expected two partitions')
 a,b=groups
 if apply_ips(apply_ips(original,patches[a]),patches[b])!=final or apply_ips(apply_ips(original,patches[b]),patches[a])!=final: raise ValueError('composition mismatch')
 for group in groups:
  if apply_ips(original,patches[group])!=bytes(images[group]): raise ValueError('roundtrip mismatch')
 return images,patches,counts,labels

def main():
 original=(ROOT/'extracted/exefs/code.bin').read_bytes(); final=(ROOT/'build/agent-work/H2-semantic/h2-pair-fill-production-integration/run-003/checks/production-fill-patch/code.h2-fill-pair.bin').read_bytes()
 images,patches,counts,labels=split(original,final)
 parent=Path('E:/SMT4decomp/build/h2-manual-comparison/run-001'); out=parent/'diagnostics/run-001'; game=parent/'pinned-title.cci'; app=parent/'original/app'
 if out.exists(): raise FileExistsError(out)
 if sha256(game)!='9cc760c2f37da9a4a3657e918e0eaebb3e8e80a91047e5c18f95aedf0242b4c2' or sha256(app/'azahar.exe')!='c248414eb5328cb8bb720775ace6959898e2f50a0a10221c3a1e7a14190183eb': raise ValueError('pinned inputs mismatch')
 out.mkdir(parents=True)
 for group in images:
  target=out/group/'app'; shutil.copytree(app,target,ignore=shutil.ignore_patterns('user'))
  user=target/'user'; user.mkdir(); provision_profile(ROOT/'build/h2-runtime/profile-pristine-user',user)
  config=user/'config/qt-config.ini'; config.parent.mkdir(); config.write_text('[Debugging]\nuse_gdbstub\\default=false\nuse_gdbstub=false\nenable_rpc_server\\default=false\nenable_rpc_server=false\n',encoding='utf8')
  dest=user/'load/mods/00040000000E5C00/exefs/code.ips'; dest.parent.mkdir(parents=True); dest.write_bytes(patches[group])
  if apply_ips(original,dest.read_bytes())!=images[group]: raise ValueError('staged patch mismatch')
 a=file_manifest(out/'init-deps/app/user'); b=file_manifest(out/'callbacks/app/user')
 a=[x for x in a if not x['path'].endswith('/code.ips')]; b=[x for x in b if not x['path'].endswith('/code.ips')]
 if a!=b or file_manifest(out/'init-deps/app',{'user'})!=file_manifest(out/'callbacks/app',{'user'}): raise ValueError('staged profiles differ')
 manifest={'original_sha256':ORIGINAL,'final_sha256':FINAL,'shared_cci_sha256':sha256(game),'seed_files':a,'ranges':{g:[{'name':n,'vma_start':hex(v),'vma_end_exclusive':hex(v+s),'file_offset_start':hex(v-0x100000),'bytes':s} for n,v,s in spans] for g,spans in RANGES.items()},'subsets':{g:{'image_sha256':hash_bytes(bytes(images[g])),'ips_sha256':hash_bytes(patches[g]),'changed_bytes':counts[g]} for g in images},'composition_both_orders':True,'all_differences_owned_once':True,'runtime':'not_run'}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8'); print(json.dumps(manifest,indent=2))
if __name__=='__main__': main()
