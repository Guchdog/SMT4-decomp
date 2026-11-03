#!/usr/bin/env python3
"""Run the bounded H3 caller check against an explicitly identified integrated image."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import h3_title_caller_composition as caller

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--image',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 image=a.image.read_bytes();ancestor=(ROOT/'build/agent-work/H3-semantic/h3-title-entry/in-place-patch-run002/code.h3-final.bin').read_bytes()
 if hashlib.sha256(ancestor).hexdigest()!=caller.H3_FINAL_CODE_SHA256:raise ValueError('H3 ancestor hash mismatch')
 if len(image)!=len(ancestor):raise ValueError('integrated image length mismatch')
 start=0x0030a9a4-0x00100000
 if image[start:start+120]!=ancestor[start:start+120]:raise ValueError('H3 replacement differs from pinned ancestor')
 digest=hashlib.sha256(image).hexdigest();caller.H3_FINAL_CODE_SHA256=digest
 report=caller.run_experiment(a.output,caller.CODE,a.image)
 summary={'image_sha256':digest,'passed':report['passed'],'scope':'H3 state-7 caller with explicit helper stubs; tested in-place image','source_report':'report.json','limitations':report['limitations']}
 (a.output/'integrated-image-verification.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8');print(json.dumps(summary));return 0 if report['passed'] else 1
if __name__=='__main__':sys.exit(main())
