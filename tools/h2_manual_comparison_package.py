from pathlib import Path
import sys, json, hashlib, shutil, argparse
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.h2_calc_code_patch import apply_ips, encode_ips
from tools.h2_azahar_rsp_probe import stage_runtime, file_manifest, sha256
ORIGINAL='1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
FINAL='5e9aa08b449985f012e24400c45b4b037e4a0d5d069723b6cfa7ccf83300d8fa'
CHAIN=[('h2-init-ready-final-image/run-013/combined-build-final/code.combined.ips','3901823e725afb914a9bc49c5f86038f8c285c107eedaa3a4337a64bc5b062d3','7b2bc2983a890e1c4cf1ae71beca9f574260d98d6cfcdffb3bbb34bd3eb2b291'),('h2-config-mapper-production-integration/run-008/checks/production-mapper-patch/code.h2-mappers.ips','72b9c68d2aca701c899978adeb793698032097a2599d70ab9c90a0361336e214','97b6c2ab9ea7f15904bbee3ad42115599bd3529220dbfba818a77bbbcfbe321c'),('h2-pair-fill-production-integration/run-003/checks/production-fill-patch/code.h2-fill-pair.ips','5b0a75a1526aec8db88b0f02cf0f9eef98e657a51a5b2bb5e1993932b9d5a4c2',FINAL)]
def digest(b): return hashlib.sha256(b).hexdigest()
def compose(original, final):
    if len(original)!=len(final): raise ValueError('image sizes differ')
    records=[]; i=0
    while i<len(original):
        if original[i]==final[i]: i+=1; continue
        start=i
        # Avoid IPS EOF marker offset by including the preceding byte.
        if start==0x454f46: start-=1
        i+=1
        while i<len(original) and original[i]!=final[i] and i-start<65535: i+=1
        records.append((start,final[start:i]))
    patch=encode_ips(records,len(original))
    if apply_ips(original,patch)!=final: raise ValueError('roundtrip mismatch')
    return patch,records

def main():
    p=argparse.ArgumentParser(); p.add_argument('--output',type=Path,required=True); a=p.parse_args()
    out=a.output.resolve(); allowed=Path('E:/SMT4decomp/build/h2-manual-comparison').resolve()
    if not out.is_relative_to(allowed) or out==allowed or out.exists(): raise ValueError('output must be a new directory under designated root')
    image=(ROOT/'extracted/exefs/code.bin').read_bytes()
    if digest(image)!=ORIGINAL: raise ValueError('original hash mismatch')
    current=image; rows=[]
    for rel, patchhash, result in CHAIN:
        path=ROOT/'build/agent-work/H2-semantic'/rel; patch=path.read_bytes()
        if digest(patch)!=patchhash: raise ValueError('chain patch mismatch')
        before=digest(current); current=apply_ips(current,patch)
        if digest(current)!=result: raise ValueError('chain image mismatch')
        rows.append({'path':str(path),'input_sha256':before,'ips_sha256':patchhash,'result_sha256':result})
    finalfile=ROOT/'build/agent-work/H2-semantic/h2-pair-fill-production-integration/run-003/checks/production-fill-patch/code.h2-fill-pair.bin'
    if current!=finalfile.read_bytes(): raise ValueError('independent final image mismatch')
    patch,records=compose(image,current)
    game=Path('E:/SMT4decomp/build/h2-runtime/h2-azahar-rsp-probe/run-007-59931/pinned-title.cci')
    if sha256(game)!='9cc760c2f37da9a4a3657e918e0eaebb3e8e80a91047e5c18f95aedf0242b4c2': raise ValueError('CCI mismatch')
    out.mkdir(parents=True)
    # stage_runtime copies the same image twice; remove the second verified copy,
    # leaving exactly one shared pinned CCI in the package.
    seed=ROOT/'build/h2-runtime/profile-pristine-user'; exe=Path('E:/emulador3ds/azahar.exe')
    for name in ('original','patched'):
        stage_runtime(exe,game,seed,out/name)
        copied=out/name/'pinned-title.cci'
        if sha256(copied)!=sha256(game): raise ValueError('CCI copy mismatch')
        if name=='original': shutil.move(str(copied),str(out/'pinned-title.cci'))
        else: copied.unlink()
        config=out/name/'app/user/config/qt-config.ini'; config.parent.mkdir(parents=True)
        config.write_text('[Debugging]\nuse_gdbstub\\default=false\nuse_gdbstub=false\nenable_rpc_server\\default=false\nenable_rpc_server=false\n',encoding='utf-8')
    u0=out/'original/app/user'; u1=out/'patched/app/user'
    if file_manifest(u0)!=file_manifest(u1): raise ValueError('seed profiles differ')
    seeds=file_manifest(u0)
    dest=u1/'load/mods/00040000000E5C00/exefs/code.ips'; dest.parent.mkdir(parents=True); dest.write_bytes(patch)
    if apply_ips(image,dest.read_bytes())!=current: raise ValueError('staged patch mismatch')
    if file_manifest(u0)!=[x for x in file_manifest(u1) if x['path']!='load/mods/00040000000E5C00/exefs/code.ips']: raise ValueError('profiles differ outside patch')
    manifest={'original_sha256':ORIGINAL,'final_sha256':FINAL,'chain':rows,'standalone_ips_sha256':digest(patch),'record_count':len(records),'changed_bytes':sum(x!=y for x,y in zip(image,current)),'cci_sha256':sha256(out/'pinned-title.cci'),'azahar_sha256':sha256(exe),'seed_files':seeds,'profiles_match_except_patch':True,'runtime_not_run':True}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(manifest,indent=2))
if __name__=='__main__': main()
