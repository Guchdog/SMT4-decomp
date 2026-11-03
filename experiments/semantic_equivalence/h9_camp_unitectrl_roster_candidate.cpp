#include <cstdint>
using u8=uint8_t; using u16=uint16_t; using u32=uint32_t;
extern "C" {
void* engine_func_002c0ec4(u32,u32);
void engine_func_002c0e9c(void*);
u32 engine_func_002c0e4c(void*);
void* row_func_002b9364(u16);
void* AsdMem_Alloc_002c4b84(u32,u32,u32,u32,u32);
void qsort_002b7f0a(void*,u32,u32,void*);
}
struct UniteRow {u16 id;u8 race;u8 field_03;u8 pad[2];u16 flags;};
struct UniteEntry {u16 id;u16 field_02;};
struct UniteCtrlRoster {u8 counts[0x38];UniteEntry* buckets[0x38];u8 tail[0xA8];};
extern "C" UniteCtrlRoster* h9_camp_unitectrl_roster_candidate(UniteCtrlRoster* roster) {
 void* table=engine_func_002c0ec4(0,0);engine_func_002c0e9c(table);u32 rows=engine_func_002c0e4c(table);
 u8 offsets[0x38];
 for(u32 i=0;i<0x38;i++){offsets[i]=0;roster->counts[i]=0;}
 for(u32 i=0;i<rows;i++){auto* r=static_cast<UniteRow*>(row_func_002b9364(static_cast<u16>(i)));if(r->race<0x38 && (r->flags&1))roster->counts[r->race]++;}
 for(u32 i=0;i<0x38;i++){roster->buckets[i]=nullptr;if(roster->counts[i])roster->buckets[i]=static_cast<UniteEntry*>(AsdMem_Alloc_002c4b84(0x100,0x100,0,roster->counts[i]*4,1));}
 for(u32 i=0;i<rows;i++){auto* r=static_cast<UniteRow*>(row_func_002b9364(static_cast<u16>(i)));if(r->race<0x38 && (r->flags&1)){auto* e=&roster->buckets[r->race][offsets[r->race]++];e->id=r->id;e->field_02=r->field_03;}}
 for(u32 i=0;i<0x38;i++)if(roster->buckets[i])qsort_002b7f0a(roster->buckets[i],roster->counts[i],4,reinterpret_cast<void*>(0x00219600));
 auto* b=reinterpret_cast<u8*>(roster);
 b[0x11c]=0;*reinterpret_cast<u16*>(b+0x11e)=0;b[0x118]=0;*reinterpret_cast<u16*>(b+0x11a)=0;b[0x143]=0;b[0x120]=0;b[0x121]=0;
 for(u32 i=0;i<16;i++)b[0x122+i]=0;
 b[0x132]=0;*reinterpret_cast<u16*>(b+0x134)&=0x03ff;b[0x136]=0;*reinterpret_cast<u16*>(b+0x138)=0xffff;*reinterpret_cast<u16*>(b+0x13a)=0xffff;b[0x17c]=0;
 return roster;
}
extern "C" void h9_camp_unitectrl_roster_mutation(UniteCtrlRoster* roster){roster->counts[0]=0xff;}
