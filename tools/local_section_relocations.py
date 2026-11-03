"""Resolve local ELF32 section relocations into an in-place candidate window."""
import struct
from pathlib import Path

def resolve_local_sections(path, function, base, blob, window):
 data=Path(path).read_bytes()
 h=struct.unpack_from('<16sHHIIIIIHHHHHH',data,0)
 if h[0][:6]!=b'\x7fELF\x01\x01': raise ValueError('Expected little-endian ELF32')
 shoff,shentsize,shnum,shstridx=h[6],h[11],h[12],h[13]
 secs=[struct.unpack_from('<IIIIIIIIII',data,shoff+i*shentsize) for i in range(shnum)]
 def contents(s): return data[s[4]:s[4]+s[5]]
 shstr=contents(secs[shstridx])
 def name_at(table,off):return table[off:table.index(b'\x00',off)].decode('ascii')
 names=[name_at(shstr,s[0]) for s in secs]
 symidx=next(i for i,s in enumerate(secs) if s[1]==2);symsec=secs[symidx];strtab=contents(secs[symsec[6]])
 syms=[struct.unpack_from('<IIIBBH',data,symsec[4]+i*(symsec[9] or 16)) for i in range(symsec[5]//(symsec[9] or 16))]
 matches=[x for x in syms if name_at(strtab,x[0])==function]
 if len(matches)!=1:raise ValueError('function symbol missing or ambiguous')
 _,fstart,fsize,_,_,fsec=matches[0];fstart &= ~1
 if fsize!=len(blob):raise ValueError('function size mismatch')
 locals=[]
 for sec in secs:
  if sec[1]!=9 or sec[6]!=symidx or sec[7]!=fsec:continue
  for i in range(sec[5]//(sec[9] or 8)):
   off,info=struct.unpack_from('<II',data,sec[4]+i*(sec[9] or 8));sym=syms[info>>8]
   if fstart<=off<fstart+fsize and not name_at(strtab,sym[0]):
    if info&255!=2 or sym[3]&15!=3:raise ValueError('unsupported anonymous relocation')
    locals.append((off-fstart,sym[5]))
 copied={};handled=set()
 for offset,idx in locals:
  if idx>=len(secs):raise ValueError('invalid local relocation section')
  addend=struct.unpack_from('<I',blob,offset)[0];section=secs[idx];name=names[idx]
  if idx==fsec:
   if not fstart<=addend<fstart+fsize:raise ValueError('local text target outside candidate')
   addr=base+addend-fstart
  elif name.startswith('.rodata'):
   if addend>=section[5]:raise ValueError('rodata addend outside section')
   if idx not in copied:
    if any(s[1] in (4,9) and s[7]==idx and s[5] for s in secs):raise ValueError('rodata has relocations')
    align=max(4,section[8]);padding=(-(base+len(blob)))%align;chunk=contents(section)
    if len(blob)+padding+len(chunk)>window:raise ValueError('no room for candidate rodata')
    blob.extend(bytes(padding));copied[idx]=base+len(blob);blob.extend(chunk)
   addr=copied[idx]+addend
  else:raise ValueError(f'unsupported local section {name}')
  struct.pack_into('<I',blob,offset,addr);handled.add(offset)
 while len(blob)%4:blob.append(0)
 if len(blob)>window:raise ValueError('no room for aligned candidate')
 return handled
