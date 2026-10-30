#!/usr/bin/env python3
"""Autonomous H3 original/final comparison using the private loopback GDB stub."""
from __future__ import annotations
import argparse,hashlib,json,socket,subprocess,time,shutil,struct
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.h2_azahar_rsp_probe import Rsp,ProbeError,reserve_port,listener_owner,decode_r0
from tools.h2_autonomous_gdb_verify import (run_to_bp,rsp_set_bp,rsp_clear_bp,rsp_read_mem,rsp_write_mem,rsp_read_u32,rsp_write_u32,ADDR_TITLE_MAIN_INIT,ADDR_TITLE_TOP_READY,ADDR_UI_INPUT_TRIGGER2)
ORIG=0x0030A9A4; TITLE_WORK_GLOBAL=0x0044E300; SAVE_MANAGER=0x0044DE28; SAVE_CALLBACK=0x001C8D28; SAVE_CALLBACK_EXIT=0x001CA4A8; FIELD_MANAGER=0x00208CE8; TITLE_STATE8=0x001EA358; INPUT_TRIGGER2=0x002BFFBC; SAVE_PROCESS_START=0x0026B874; SAVE_STATUS_SETTER=0x002C5948
CCI=Path(r'E:/emulador3ds/00040000000E5C00 Shin Megami Tensei IV (CTR-P-AMXE) (v0.1.0) (U).piratelegit-decrypted.cci')
PORTS={'original':54342,'patched':54343}

def sha(b):return hashlib.sha256(b).hexdigest()
def tree_manifest(root):
 out={}
 for p in sorted(root.rglob('*')):
  if p.is_file():
   rel=p.relative_to(root).as_posix()
   if rel.startswith('load/mods/'):continue
   out[rel]={'size':p.stat().st_size,'sha256':sha(p.read_bytes())}
 return out
def save_snapshot(user):
 p=user/'sdmc/Nintendo 3DS/00000000000000000000000000000000/00000000000000000000000000000000/title/00040000/000e5c00/data/00000001/sdds4game1.sav'
 return {'path':str(p),'exists':p.is_file(),'size':p.stat().st_size if p.is_file() else None,'sha256':sha(p.read_bytes()) if p.is_file() else None}
def profile_state(rsp):
 manager=rsp_read_mem(rsp,SAVE_MANAGER,0x10); work=int.from_bytes(manager[4:8],'little')
 vm_ptr=rsp_read_u32(rsp,work+0x248) if work else 0
 vm=rsp_read_mem(rsp,vm_ptr,0xE0) if vm_ptr else b''
 method_ptr=int.from_bytes(vm[0xBC:0xC0],'little') if len(vm)>=0xC0 else 0
 instruction=int.from_bytes(vm[0x18:0x1C],'little') if len(vm)>=0x1C else None
 handler_id=int.from_bytes(rsp_read_mem(rsp,method_ptr+4*instruction,2),'little') if method_ptr and instruction is not None and instruction<0x1000 else None
 handler_ptr=rsp_read_u32(rsp,0x0044DED0+4*handler_id) if handler_id is not None else None
 nested_id=int.from_bytes(rsp_read_mem(rsp,method_ptr+4*instruction+2,2),'little') if method_ptr and instruction is not None and instruction<0x1000 else None
 nested_ptr=rsp_read_u32(rsp,0x00406038+8*nested_id) if nested_id is not None else None
 return {'manager_hex':manager.hex(),'work_ptr':hex(work),'work_hex':rsp_read_mem(rsp,work,0x388).hex() if work else None,'work_state':rsp_read_u32(rsp,work+8) if work else None,'selected_slot':rsp_read_u32(rsp,work+0x10) if work else None,'slot0_text_hex':rsp_read_mem(rsp,work+0x24c,0x4c).hex() if work else None,'script_vm':{'ptr':hex(vm_ptr) if vm_ptr else None,'bytes':vm.hex() if vm else None,'instruction':instruction,'method_table':hex(method_ptr) if method_ptr else None,'handler_id':handler_id,'handler_ptr':hex(handler_ptr) if handler_ptr else None,'nested_id':nested_id,'nested_handler_ptr':hex(nested_ptr) if nested_ptr else None}}
def pc(rsp): return decode_r0(rsp.request(b'p0f'))
def write_reg(rsp,index,value):
 reply=rsp.request(f'P{index:x}={value.to_bytes(4,"little").hex()}'.encode())
 if reply!=b'OK':raise ProbeError(f'could not write guest register {index}: {reply!r}')
def capture_screen(artifact_dir,name):
 um=shutil.which('um') or shutil.which('um.exe')
 if not um:return {'returncode':None,'error':'um CLI not found'}
 screen=artifact_dir/name
 s=subprocess.run([um,'win','shot','--exe','azahar.exe',str(screen),'--scale','0.33'],capture_output=True,text=True,timeout=30)
 thumb=screen.with_name(screen.stem+'_small'+screen.suffix)
 return {'returncode':s.returncode,'stdout':s.stdout.strip(),'stderr':s.stderr.strip(),'path':str(thumb if thumb.exists() else screen)}
def field_observation(rsp,regs,index,force=False):
 base={'index':index,'entry_registers':[hex(x) for x in regs],'r1_r2_context_arg':hex(regs[1])}
 if index not in (0,1,2,5,10,25,50,100,249) and not force:return base
 slots={}
 for label,address in (('map_enemy_work_slot',0x00447600),('map_main_work_slot',0x00447E28),('map_scene_view_slot',0x00447E88),('map_epl_work_slot',0x00447A10),('axis_work_slot',0x004650A0)):
  try:slots[label]=hex(rsp_read_u32(rsp,address))
  except Exception as exc:slots[label]=f'error:{exc}'
 def pointed(prefix,length):
  try:
   ptr=int(slots[prefix],16)
   return rsp_read_mem(rsp,ptr,length).hex() if ptr else None
  except Exception as exc:return f'error:{exc}'
 base.update({'global_pointer_slots':slots,'scene_view_prefix_0x170':pointed('map_scene_view_slot',0x170),'map_enemy_work_prefix_0x80':pointed('map_enemy_work_slot',0x80),'map_main_work_prefix_0xc8':pointed('map_main_work_slot',0xc8),'map_epl_work_prefix_0x188':pointed('map_epl_work_slot',0x188),'axis_work_prefix_0x20':pointed('axis_work_slot',0x20)})
 for label,address in (('input_buffer_0x4e3c28',0x004E3C28),('input_buffer_0x4e3c48',0x004E3C48)):
  try:base[label]=rsp_read_mem(rsp,address,0x20).hex()
  except Exception as exc:base[label]=f'error:{exc}'
 return base
def scene_view_snapshot(rsp):
 try:
  ptr=rsp_read_u32(rsp,0x00447E88)
  if not ptr:return {'pointer':None}
  valid=0x10000<=ptr and ptr+0x170<=0xFFFFF000
  result={'pointer':hex(ptr),'size':0x170,'range_valid':valid}
  if valid:
   try:result['prefix_0x170']=rsp_read_mem(rsp,ptr,0x170).hex()
   except Exception as exc:result['read_error']=str(exc)
  return result
 except Exception as exc:return {'read_error':str(exc)}
def stopped_thread_id(stop_reply):
 for field in stop_reply.split(';'):
  if field.startswith('thread:') and field[7:]:return field[7:]
 return None
def navi_callback_state_snapshot(rsp,callback_object):
 snapshot={'callback_object_pointer':hex(callback_object)}
 bounded_probe_read(rsp,snapshot,'callback_object_prefix_0x60',callback_object,0x60)
 try:host=rsp_read_u32(rsp,0x0044CDF0)
 except Exception as exc:
  snapshot['navi_host_slot_read_error']=str(exc);host=0
 snapshot['navi_global_slot_address']='0x0044cdf0';snapshot['navi_global_host_pointer']=hex(host)
 for label,offset in (('host_plus_0x30',0x30),('host_plus_0x38',0x38)):
  bounded_probe_read(rsp,snapshot,label,host+offset,4)
 pair_address=host+0xB64
 valid=0x10000<=host and pair_address+8<=0xFFFFF000
 snapshot['navi_callback_pair_validation']={'address':hex(pair_address),'size':8,'range_valid':valid}
 if valid:
  try:
   pair=rsp_read_mem(rsp,pair_address,8)
   words=[int.from_bytes(pair[i:i+4],'little') for i in (0,4)]
   snapshot['navi_callback_pair_hex']=pair.hex();snapshot['navi_callback_pair_words']=[hex(x) for x in words]
  except Exception as exc:snapshot['navi_callback_pair_read_error']=str(exc)
 try:input_object=rsp_read_u32(rsp,0x0043DA2C)
 except Exception as exc:snapshot['input_object_slot_read_error']=str(exc);input_object=0
 snapshot['input_object_slot_address']='0x0043da2c';snapshot['input_object_pointer']=hex(input_object)
 bounded_probe_read(rsp,snapshot,'input_object_fields_plus_0x4b8_to_0x4be',input_object+0x4B8,7)
 snapshot['scene_view']=scene_view_snapshot(rsp)
 return snapshot
def trace_navi_callback_returns(rsp,callback_object,entry_stop_reply='',max_events=24):
 return_sites=(0x00399D88,0x00399D98,0x00399DAC,0x00399DB8,0x00399DCC,0x00399DEC,0x00399E00,0x00399E14,0x001A95E8)
 armed=[];events=[];remove_errors=[];entry_thread=stopped_thread_id(entry_stop_reply);status='event_limit'
 try:
  for address in return_sites:
   rsp_set_bp(rsp,address);armed.append(address)
  for stop_index in range(max_events):
   here,interrupted,stop=continue_and_read_pc(rsp)
   if interrupted:
    status='external_rsp_timeout';events.append({'stop_index':stop_index,'status':status,'pc':hex(here),'stop_reply':stop,'thread_id':stopped_thread_id(stop),'thread_id_source':'gdb_stop_reply'});break
   thread=stopped_thread_id(stop)
   event={'stop_index':stop_index,'pc':hex(here),'thread_id':thread,'thread_id_source':'gdb_stop_reply','entry_thread_id':entry_thread,'same_thread_as_entry':thread==entry_thread if thread is not None and entry_thread is not None else None,'stop_reply':stop}
   event['registers_r0_r4']=[hex(decode_r0(rsp.request(f'p{j:x}'.encode()))) for j in range(5)]
   event['lr']=hex(decode_r0(rsp.request(b'p0e')));event['sp']=hex(decode_r0(rsp.request(b'p0d')))
   event['snapshot']=navi_callback_state_snapshot(rsp,callback_object)
   events.append(event)
   if here not in armed:
    status='unexpected_stop';event['status']=status;break
   rsp_clear_bp(rsp,here);armed.remove(here)
   if here==0x001A95E8:
    status='callback_return_observed';break
  else:status='event_limit'
 finally:
  for address in tuple(armed):
   try:rsp_clear_bp(rsp,address);armed.remove(address)
   except Exception as exc:remove_errors.append({'address':hex(address),'error':str(exc)})
 return {'status':status,'event_limit':max_events,'entry_thread_id':entry_thread,'events':events,'target_loop_has_internal_bound':False,'breakpoints_removed':not armed and not remove_errors,'breakpoint_removal_errors':remove_errors}
def axis_input_snapshot(rsp):
 def read(address,size):
  try:return rsp_read_mem(rsp,address,size).hex()
  except Exception as exc:return f'error:{exc}'
 try:
  manager=rsp_read_mem(rsp,0x004650A0,0x20)
  calibration=int.from_bytes(manager[:4],'little')
  calibration_data=read(calibration,0x20) if calibration else None
 except Exception as exc:
  manager=f'error:{exc}';calibration=None;calibration_data=None
 return {'manager_0x004650a0_prefix_0x20':manager.hex() if isinstance(manager,bytes) else manager,
         'calibration_pointer':hex(calibration) if calibration else None,
         'calibration_prefix_0x20':calibration_data,
         'primary_records_0x004e3c28_prefix_0x30':read(0x004E3C28,0x30),
         'alternate_record_0x004e3c48_prefix_0x10':read(0x004E3C48,0x10),
         'counter_table_0x004e3c58_prefix_0x7c':read(0x004E3C58,0x7c)}
def bounded_probe_read(rsp,event,label,pointer,size):
 valid=0x10000<=pointer and pointer+size<=0xFFFFF000
 sample={'address':hex(pointer),'size':size,'range_valid':valid}
 if valid:
  try:sample['bytes']=rsp_read_mem(rsp,pointer,size).hex()
  except Exception as exc:sample['read_error']=str(exc)
 event[label]=sample
 return sample
def input_copy_header(rsp,event,label,pointer):
 if 0x10000<=pointer and pointer+0x14<=0xFFFFF000:
  bounded_probe_read(rsp,event,label+'_cursor_count',pointer,0x14)
  bounded_probe_read(rsp,event,label+'_extended_fields',pointer+0xA8,0x14)
 else:
  event[label+'_address_validation']={'address':hex(pointer),'range_valid':False,'size':0x14}
def input_copy_stack(rsp,event,sp,callee_frame,entry_r3=None):
 args=sp+(0x48 if callee_frame else 0)
 try:
  cursor_ptr=rsp_read_u32(rsp,args); count_ptr=rsp_read_u32(rsp,args+4)
  event['caller_stack_arguments']={'frame_sp':hex(sp),'argument_base':hex(args),'cursor_pointer':hex(cursor_ptr),'count_pointer':hex(count_ptr)}
  bounded_probe_read(rsp,event,'caller_cursor_pair',cursor_ptr,8)
  bounded_probe_read(rsp,event,'caller_count_word',count_ptr,4)
  count_output=entry_r3 if entry_r3 is not None else (rsp_read_u32(rsp,sp+0x20) if callee_frame else sp+8)
  event['selected_count_output_pointer']=hex(count_output)
  bounded_probe_read(rsp,event,'selected_count_output_word',count_output,4)
 except Exception as exc:event['caller_stack_arguments_read_error']=str(exc)
def trace_input_copy_retries(rsp,max_events=256):
 addresses=(0x0012A780,0x0012A85C,0x0012A89C,0x0012A8DC)
 names={0x0012A780:'attempt_load_entry',0x0012A85C:'payload_load_boundary',0x0012A89C:'stability_check_boundary',0x0012A8DC:'stable_commit_boundary'}
 armed=set();attempts=[];current=None;status='event_limit';last_stop=None
 def arm(address):
  if address not in armed:
   rsp_set_bp(rsp,address);armed.add(address)
 def clear(address):
  if address in armed:
   rsp_clear_bp(rsp,address);armed.discard(address)
 try:
  for address in addresses:arm(address)
  for stop_index in range(max_events):
   here,interrupted,stop=continue_and_read_pc(rsp)
   last_stop={'pc':hex(here),'interrupted':interrupted,'stop_reply':stop}
   if interrupted:
    status='external_rsp_timeout';break
   if here not in names:
    status='unexpected_stop';last_stop['expected_addresses']=[hex(x) for x in addresses];break
   regs=[decode_r0(rsp.request(f'p{j:x}'.encode())) for j in range(13)]
   sp=decode_r0(rsp.request(b'p0d'))
   lr=decode_r0(rsp.request(b'p0e'))
   observation={'address':hex(here),'name':names[here],'stop_index':stop_index,'registers_r0_r12':[hex(x) for x in regs],'sp':hex(sp),'lr':hex(lr),'stop_reply':stop}
   source=regs[0]
   if 0x10000<=source and source+0x14<=0xFFFFF000:
    observation['source_cursor_count']=bounded_probe_read(rsp,observation,'source_cursor_count',source,0x14)
   if here==0x0012A780:
    if current is not None and current.get('stability_check') is not None:
     current['branch_after_check']='retry_target_0x0012A780'
    current={'attempt_number':len(attempts),'load_entry':observation}
    attempts.append(current)
   elif current is None:
    status='missing_attempt_entry';last_stop=observation;break
   elif here==0x0012A85C:
    source_slot=regs[3];destination=decode_r0(rsp.request(b'p7'))
    observation.update({'effective_source_slot_index':hex(regs[2]),'live_loaded_count_r4':hex(regs[4]),'copy_loop_index':hex(regs[5]),'source_slot_base':hex(source_slot),'source_payload_address':hex(source_slot+0x28),'destination_address':hex(destination)})
    bounded_probe_read(rsp,observation,'selected_source_payload',source_slot+0x28,0x10)
    bounded_probe_read(rsp,observation,'destination_before_copy',destination,0x10)
    input_copy_stack(rsp,observation,sp,True)
    current['payload_load']=observation
   elif here==0x0012A89C:
    observation.update({'live_loaded_count_r4':hex(regs[4]),'source_header_pointer':hex(source)})
    input_copy_header(rsp,observation,'source_header_at_stability_check',source)
    destination=regs[1]
    bounded_probe_read(rsp,observation,'destination_after_copy_before_check',destination,0x10)
    input_copy_stack(rsp,observation,sp,True)
    current['stability_check']=observation
   else:
    observation['commit_source_slot_base']=current.get('payload_load',{}).get('source_slot_base')
    observation['commit_source_slot_index']=current.get('payload_load',{}).get('effective_source_slot_index')
    current['branch_after_check']='stable_commit_target_0x0012A8DC'
    current['stable_commit']=observation
    status='stable_commit_observed';clear(here);break
   clear(here)
   if here==0x0012A85C:
    arm(0x0012A780)
   elif here==0x0012A780:
    arm(0x0012A85C);arm(0x0012A89C)
  else:
   status='event_limit'
 finally:
  for address in tuple(armed):
   try:clear(address)
   except Exception:pass
 return {'status':status,'max_events':max_events,'attempt_count':len(attempts),'attempts':attempts,'last_stop':last_stop,'unbounded_target_loop_note':'The target retry loop has no internal bound; event ceiling and RSP timeout are external capture limits.'}
def capture_input_copy_stable_commit(rsp):
 address=0x0012A8DC
 try:rsp_set_bp(rsp,address)
 except Exception as exc:return {'status':'breakpoint_setup_error','error':str(exc),'target_loop_has_internal_bound':False}
 here,interrupted,stop=continue_and_read_pc(rsp)
 result={'target_address':hex(address),'pc':hex(here),'interrupted':interrupted,'stop_reply':stop,'retry_iterations_observed':False,'target_loop_has_internal_bound':False}
 if interrupted:
  result['status']='external_rsp_timeout'
  try:rsp_clear_bp(rsp,address)
  except Exception:pass
  return result
 if here!=address:
  result['status']='unexpected_stop'
  try:rsp_clear_bp(rsp,address)
  except Exception:pass
  return result
 try:
  regs=[decode_r0(rsp.request(f'p{j:x}'.encode())) for j in range(13)]
  sp=decode_r0(rsp.request(b'p0d'));lr=decode_r0(rsp.request(b'p0e'))
  result.update({'status':'stable_commit_observed','registers_r0_r12':[hex(x) for x in regs],'sp':hex(sp),'lr':hex(lr),'effective_source_count_r4':hex(regs[4]),'selected_record_count_sb':hex(regs[9])})
  source_ptr=rsp_read_u32(rsp,sp+0x14);destination=rsp_read_u32(rsp,sp+0x18);count_ptr=rsp_read_u32(rsp,sp+0x20)
  result.update({'saved_source_object_pointer':hex(source_ptr),'saved_destination_pointer':hex(destination),'saved_result_count_pointer':hex(count_ptr),'source_index_formula':'(signed_r4 + 8) remainder 8 at first iteration i=0, as implemented by 0x0012A83C..0x0012A858'})
  if 0<=regs[4]<=7:
   index=(regs[4]+8)%8;slot=source_ptr+index*0x10
   result.update({'derived_committed_source_index':index,'derived_committed_source_slot_base':hex(slot),'derived_committed_payload_address':hex(slot+0x28)})
   source_ok=0x10000<=source_ptr and source_ptr+0x100<=0xFFFFF000 and slot+0x38<=source_ptr+0x100
   result['source_object_span_valid']=source_ok
   if source_ok:bounded_probe_read(rsp,result,'committed_source_payload',slot+0x28,0x10)
   else:result['committed_source_payload_address_validation']={'range_valid':False}
  else:
   result['derived_committed_source_index']=None
   result['committed_source_payload_address_validation']={'range_valid':False,'reason':'r4 outside observed nonnegative 0..7 domain'}
  bounded_probe_read(rsp,result,'destination_at_stable_commit_before_final_stores',destination,0x10)
  bounded_probe_read(rsp,result,'source_header_at_stable_commit',source_ptr,0x14)
  result['caller_cursor_pointer']=hex(rsp_read_u32(rsp,sp+0x48));result['caller_count_pointer']=hex(rsp_read_u32(rsp,sp+0x4c))
 except Exception as exc:
  result['capture_error']=str(exc)
 finally:
  try:rsp_clear_bp(rsp,address)
  except Exception:pass
 return result
def probe_field_calls(rsp,addresses,axis_output=None,input_copy_retry_trace=False,input_copy_retry_event_limit=256,input_copy_stable_commit=False,navi_callback_return_trace=False):
 probes=[]
 for address in (FIELD_MANAGER,0x0020CE7C):
  try:rsp_clear_bp(rsp,address)
  except Exception:pass
 for address in addresses:
  event={'address':hex(address),'hit':False}
  try:
   rsp_set_bp(rsp,address)
   here,interrupted,stop=continue_and_read_pc(rsp)
   event.update({'pc':hex(here),'interrupted':interrupted,'stop_reply':stop})
   if not interrupted and here==address:
    regs=[decode_r0(rsp.request(f'p{j:x}'.encode())) for j in range(4)]
    lr=decode_r0(rsp.request(b'p0e'));sp=decode_r0(rsp.request(b'p0d'))
    event.update({'hit':True,'entry_registers':[hex(x) for x in regs],'lr':hex(lr),'sp':hex(sp)})
    try:event['gpr_r0_to_r12']=[hex(decode_r0(rsp.request(f'p{j:x}'.encode()))) for j in range(13)]
    except Exception as exc:event['gpr_read_error']=str(exc)
    event['axis_input_snapshot_at_entry']=axis_input_snapshot(rsp)
    if address==0x00399D60:
     # The installed callback-like pair is static evidence only. At a live
     # entry, capture the current host slot and pair read-only after validating
     # the complete address span; do not assume the slot owns this r0 object.
     host=rsp_read_u32(rsp,0x0044CDF0)
     event['navi_global_slot_address']='0x0044cdf0'
     event['navi_global_host_pointer']=hex(host)
     pair_address=host+0xB64
     valid=0x10000<=host and pair_address+8<=0xFFFFF000
     event['navi_callback_pair_validation']={'address':hex(pair_address),'size':8,'range_valid':valid}
     if valid:
      try:
       pair=rsp_read_mem(rsp,pair_address,8)
       event['navi_callback_pair_hex']=pair.hex()
       pair_words=[int.from_bytes(pair[i:i+4],'little') for i in (0,4)]
       event['navi_callback_pair_words']=[hex(x) for x in pair_words]
       event['navi_callback_pair_matches_static_table']=(pair_words==[0x00399D60,0])
      except Exception as exc:event['navi_callback_pair_read_error']=str(exc)
     event['navi_callback_state_at_entry']=navi_callback_state_snapshot(rsp,regs[0])
     if navi_callback_return_trace:
      rsp_clear_bp(rsp,address)
      event['navi_callback_call_return_trace']=trace_navi_callback_returns(rsp,regs[0],stop)
    if address==0x0011C640:
     input_copy_header(rsp,event,'source_header_at_caller',regs[0])
     input_copy_stack(rsp,event,sp,False,regs[3])
    elif address==0x0012A758:
     input_copy_header(rsp,event,'source_header_at_helper_entry',regs[0])
     input_copy_stack(rsp,event,sp,False,regs[3])
     if address==0x0012A758 and input_copy_retry_trace:
      rsp_clear_bp(rsp,address)
      event['input_copy_retry_trace']=trace_input_copy_retries(rsp,input_copy_retry_event_limit)
     if address==0x0012A758 and input_copy_stable_commit:
      rsp_clear_bp(rsp,address)
      event['input_copy_stable_commit']=capture_input_copy_stable_commit(rsp)
    elif address==0x0012A85C:
     source_slot=regs[3]; destination=decode_r0(rsp.request(b'p7'))
     event.update({'effective_source_slot_index':hex(regs[2]),'copy_loop_index':hex(decode_r0(rsp.request(b'p5'))),'source_slot_base':hex(source_slot),'destination_slot':hex(destination)})
     bounded_probe_read(rsp,event,'selected_source_record',source_slot+0x28,0x10)
     bounded_probe_read(rsp,event,'destination_before_copy',destination,0x10)
     input_copy_header(rsp,event,'source_header_before_payload_loads',regs[0])
     input_copy_stack(rsp,event,sp,True)
    elif address==0x0012A89C:
     input_copy_header(rsp,event,'source_header_at_stability_check',regs[0])
     bounded_probe_read(rsp,event,'destination_after_copy',regs[1],0x10)
     input_copy_stack(rsp,event,sp,True)
    elif address==0x0011C644:
     output=decode_r0(rsp.request(b'p4'))
     count_pointer=sp+8
     event.update({'copy_result_count_pointer':hex(count_pointer),'copy_result_count_word':rsp_read_mem(rsp,count_pointer,4).hex(),'primary_output_pointer':hex(output)})
     bounded_probe_read(rsp,event,'primary_output_after_copy_before_transform',output,0x10)
     input_copy_stack(rsp,event,sp,False,sp+8)
    elif address==0x0011C66C:
     output=decode_r0(rsp.request(b'p4'))
     event['primary_output_pointer']=hex(output)
     bounded_probe_read(rsp,event,'primary_output_after_transform',output,0x10)
    for label,pointer in (('r0_pointer',regs[0]),('r1_pointer',regs[1])):
     size=0x100 if address==0x0011C640 and label=='r0_pointer' else 0x40
     if 0x10000<=pointer and pointer+size<=0xFFFFF000:
      if address==0x0011C640 and label=='r0_pointer':
       event['source_object_address_validation']={'address':hex(pointer),'size':size,'range_valid':True,'capture':'entry'}
      try:event[label+f'_prefix_0x{size:x}']=rsp_read_mem(rsp,pointer,size).hex()
      except Exception as exc:event[label+'_read_error']=str(exc)
     elif address==0x0011C640 and label=='r0_pointer':
      event['source_object_address_validation']={'address':hex(pointer),'size':size,'range_valid':False,'capture':'entry'}
    event['scene_view_at_entry']=scene_view_snapshot(rsp)
    try:event['stack_hex']=rsp_read_mem(rsp,sp,0x40).hex()
    except Exception as exc:event['stack_read_error']=str(exc)
    if address==0x0027FBC8:
     event['mode_r2']=regs[2]
     event['output_pointer_registers']=[hex(regs[0]),hex(regs[1])]
     return_address=lr&0xFFFFFFFE
     try:
      rsp_set_bp(rsp,return_address);rsp_clear_bp(rsp,address)
      ret_pc,ret_interrupted,ret_stop=continue_and_read_pc(rsp)
      event.update({'return_pc':hex(ret_pc),'return_interrupted':ret_interrupted,'return_stop_reply':ret_stop})
      if not ret_interrupted and ret_pc==return_address:
       event['return_registers']=[hex(decode_r0(rsp.request(f'p{j:x}'.encode()))) for j in range(4)]
       for label,pointer in (('output0',regs[0]),('output1',regs[1])):
        if pointer:
         try:event[label+'_hex']=rsp_read_mem(rsp,pointer,4).hex()
         except Exception as exc:event[label+'_read_error']=str(exc)
       if axis_output is not None:
        if regs[2]!=0 or lr!=0x001FA94C:
         event['axis_override']={'applied':False,'reason':'caller or mode did not match the observed field-camera query'}
        elif any(not pointer or pointer&3 or abs(pointer-sp)>0x40 for pointer in (regs[0],regs[1])):
         event['axis_override']={'applied':False,'reason':'output pointers failed the observed caller-stack bounds check'}
        else:
         rsp_write_mem(rsp,regs[0],struct.pack('<f',axis_output[0]))
         rsp_write_mem(rsp,regs[1],struct.pack('<f',axis_output[1]))
         write_reg(rsp,0,1)
         event['axis_override']={'applied':True,'values':list(axis_output),'output0_hex':struct.pack('<f',axis_output[0]).hex(),'output1_hex':struct.pack('<f',axis_output[1]).hex(),'return_value':1,'method':'override only the observed helper output slots at its caller return; raw input buffers remain untouched'}
     finally:
      try:rsp_clear_bp(rsp,return_address)
      except Exception:pass
    event['scene_view_at_stop']=scene_view_snapshot(rsp)
    event['axis_input_snapshot_at_stop']=axis_input_snapshot(rsp)
   probes.append(event)
   if address==0x0012A758 and input_copy_stable_commit and event.get('input_copy_stable_commit',{}).get('status')!='stable_commit_observed':
    return probes
  finally:
   try:rsp_clear_bp(rsp,address)
   except Exception:pass
 # The source object is captured again after the bounded probe sequence so its
 # bytes can be compared across the observed producer/copy calls. This is an
 # RSP memory read only; no guest register or memory writes are issued here.
 for event in probes:
  validation=event.get('source_object_address_validation',{})
  pointer=int(validation.get('address','0'),16) if validation.get('range_valid') else 0
  size=int(validation.get('size',0))
  if pointer and size==0x100 and pointer+size<=0xFFFFF000:
   try:
    after=rsp_read_mem(rsp,pointer,size).hex()
    event['r0_pointer_prefix_0x100_after_probes']=after
    before=event.get('r0_pointer_prefix_0x100')
    if before is not None:event['source_object_unchanged_through_probes']=before==after
   except Exception as exc:event['r0_pointer_after_probes_read_error']=str(exc)
 return probes
def advance_field_scene(rsp,first_regs,ticks,artifact_dir=None,focus_game=False,probe_addresses=(),axis_output=None,input_copy_retry_trace=False,input_copy_retry_event_limit=256,input_copy_stable_commit=False,navi_callback_return_trace=False):
 observations=[field_observation(rsp,first_regs,0)];status=[]
 def one_field_tick(index,record=True):
  try:rsp_clear_bp(rsp,FIELD_MANAGER)
  except Exception:pass
  rsp_set_bp(rsp,0x0020CE7C)
  here,interrupted,stop=continue_and_read_pc(rsp)
  if interrupted or here!=0x0020CE7C:
   return {'index':index,'returned_to_manager_epilogue':False,'pc':hex(here),'interrupted':interrupted,'stop_reply':stop}
  rsp_clear_bp(rsp,0x0020CE7C)
  rsp_set_bp(rsp,FIELD_MANAGER)
  here,interrupted,stop=continue_and_read_pc(rsp)
  if interrupted or here!=FIELD_MANAGER:
   return {'index':index,'next_manager_tick':False,'pc':hex(here),'interrupted':interrupted,'stop_reply':stop}
  regs=[decode_r0(rsp.request(f'p{j:x}'.encode())) for j in range(4)]
  if record:observations.append(field_observation(rsp,regs,index))
  return {'index':index,'returned_to_manager_epilogue':True,'next_manager_tick':True,'registers':[hex(x) for x in regs]}
 for i in range(1,ticks):
  tick_status=one_field_tick(i)
  status.append({k:v for k,v in tick_status.items() if k!='registers'})
  if not tick_status.get('next_manager_tick'):break
 field_call_probes=probe_field_calls(rsp,probe_addresses,axis_output,input_copy_retry_trace,input_copy_retry_event_limit,input_copy_stable_commit,navi_callback_return_trace) if probe_addresses and status and status[-1].get('next_manager_tick') else []
 if focus_game and artifact_dir:
  screen=capture_screen(artifact_dir,'field-scene-screen.png')
 else:screen=None
 try:rsp_clear_bp(rsp,FIELD_MANAGER)
 except Exception:pass
 try:rsp_clear_bp(rsp,0x0020CE7C)
 except Exception:pass
 return observations,status,screen,field_call_probes
def continue_and_read_pc(rsp):
 try: stop=rsp.continue_to_stop(); return pc(rsp),False,stop.decode('ascii','replace')
 except TimeoutError:
  rsp.sock.sendall(b'\x03')
  try:stop=rsp._packet().decode('ascii','replace')
  except Exception:stop='interrupt-no-stop-reply'
  return pc(rsp),True,stop
def run_one(kind,root,user,port,timeout,callbacks,confirm_load=False,post_callbacks=60,focus_game=False,artifact_dir=None,field_tick_count=70,slot=0,trigger_id=0,probe_only=False,missing_save_before_read=False,force_status_error=False,missing_save_before_confirm=False,field_probe_addresses=(),axis_output=None,input_copy_retry_trace=False,input_copy_retry_event_limit=256,input_copy_stable_commit=False,navi_callback_return_trace=False):
 app=root/'app';exe=app/'azahar.exe';stdout=root/'azahar.stdout.log';stderr=root/'azahar.stderr.log';reserve_port(port)
 save_path=Path(save_snapshot(user)['path']);hidden_save=None;read_error_injection={'requested':True,'removed_at':None,'restored_at':None} if (missing_save_before_read or missing_save_before_confirm) else None;status_error_injection={'requested':True,'applied_at':None,'original_status_register':None} if force_status_error else None
 with stdout.open('w',encoding='utf-8') as out,stderr.open('w',encoding='utf-8') as err:
  proc=subprocess.Popen([str(exe),'-g',str(port),str(CCI)],cwd=app,stdin=subprocess.DEVNULL,stdout=out,stderr=err,shell=False)
  try:
   deadline=time.monotonic()+timeout
   while time.monotonic()<deadline:
    if proc.poll() is not None: raise ProbeError(f'Azahar exited early ({proc.returncode})')
    owner=listener_owner(port)
    if owner is not None: break
    time.sleep(.2)
   if listener_owner(port)!=proc.pid: raise ProbeError('GDB stub is not owned by this private child')
   sock=socket.create_connection(('127.0.0.1',port),timeout=20);rsp=Rsp(sock,timeout=20)
   try:
    supported=rsp.request(b'qSupported:multiprocess+;swbreak+;hwbreak+;QStartNoAckMode+')
    if not supported or supported.startswith(b'E'):raise ProbeError(f'qSupported failed: {supported!r}')
    if rsp.request(b'!')!=b'OK':raise ProbeError('extended mode rejected')
    info=rsp.request(b'qfProcessInfo')
    if not info.startswith(b'pid:'):raise ProbeError(f'no guest process: {info!r}')
    pid=info.split(b':',1)[1].split(b';',1)[0]
    if not rsp.request(b'vAttach;'+pid).startswith(b'T'):raise ProbeError('guest attach failed')
    focus_result=None;screen_result=None
    if focus_game:
     um=shutil.which('um') or shutil.which('um.exe')
     if not um:raise ProbeError('universal-modder um CLI not found for requested foreground run')
     f=subprocess.run([um,'win','drive','--proc','azahar','focus'],capture_output=True,text=True,timeout=20)
     focus_result={'returncode':f.returncode,'stdout':f.stdout.strip(),'stderr':f.stderr.strip()}
     if f.returncode:raise ProbeError(f'could not focus the private Azahar window: {f.stderr.strip()}')
    trigger_orig=rsp_read_mem(rsp,ADDR_UI_INPUT_TRIGGER2,8)
    rsp_write_mem(rsp,ADDR_UI_INPUT_TRIGGER2,bytes.fromhex('0100a0e31eff2fe1'))
    try: run_to_bp(rsp,ADDR_TITLE_MAIN_INIT)
    finally: rsp_write_mem(rsp,ADDR_UI_INPUT_TRIGGER2,trigger_orig)
    run_to_bp(rsp,ADDR_TITLE_TOP_READY)
    title_work=rsp_read_u32(rsp,TITLE_WORK_GLOBAL)
    if not title_work:raise ProbeError('title work pointer is null')
    # H1/H2 runtime uses this observed logical touch-confirm seam; select Load Game row 1.
    rsp_write_u32(rsp,title_work+8,1);rsp_write_mem(rsp,title_work+0x63,b'\x01')
    run_to_bp(rsp,ORIG)
    entry_regs=[decode_r0(rsp.request(f'p{i:x}'.encode())) for i in range(4)]
    run_to_bp(rsp,TITLE_STATE8)
    title_after=rsp_read_mem(rsp,title_work,0xa0)
    if focus_game and artifact_dir:
     screen=artifact_dir/'title-screen.png'
     screen_result=capture_screen(artifact_dir,'title-screen.png')
    # Observe save/load callback state without injecting UI input yet.
    ui_samples=[]
    for i in range(callbacks):
     run_to_bp(rsp,SAVE_CALLBACK)
     ui_samples.append(profile_state(rsp))
     # A software breakpoint leaves PC at its instruction. Do not arm the
     # same entry again until this callback has executed and returned.
     run_to_bp(rsp,SAVE_CALLBACK_EXIT)
    pulse_observation=None; post_load_confirm=None; events=[]; progress_samples=[]; field_hit=False; field_regs=None; field_ticks=[];field_tick_status=[];field_scene_screen=None;field_call_probes=[]; stalled_at=None
    if confirm_load:
     state=profile_state(rsp); work=int(state['work_ptr'],16); work_bytes=bytes.fromhex(state['work_hex'])
     if not 0<=slot<=2:raise ProbeError(f'invalid slot index {slot}; expected 0..2')
     if not 0<=trigger_id<=30:raise ProbeError(f'invalid logical trigger id {trigger_id}; expected 0..30')
     if rsp_read_u32(rsp,SAVE_MANAGER+8)!=slot or state['selected_slot']!=slot:
      rsp_write_u32(rsp,SAVE_MANAGER+8,slot);rsp_write_u32(rsp,work+0x10,slot)
     selected=rsp_read_u32(rsp,SAVE_MANAGER+8)
     slot_active=work_bytes[0x34c+slot]
     text=rsp_read_mem(rsp,work+0x24c+slot*0x80,0x4c)
     name_nonzero=any(text[:0x12])
     if state['work_state']!=2 or selected!=slot:
      raise ProbeError(f'refusing confirmation outside load state/selected slot: state={state["work_state"]}, selected={selected}, target={slot}')
     if slot==0 and (not slot_active or not name_nonzero):
      raise ProbeError(f'refusing populated-slot confirmation without slot data: active={slot_active}, name_nonzero={name_nonzero}')
     if slot>0 and (slot_active or name_nonzero):
      raise ProbeError(f'refusing empty-slot probe because target slot {slot} contains a populated name: active={slot_active}, name_nonzero={name_nonzero}')
     before_input=rsp_read_mem(rsp,INPUT_TRIGGER2,16)
     confirm_stub=((0xE3500000|trigger_id).to_bytes(4,'little')+bytes.fromhex('0100a0030000a0131eff2fe1')) # cmp r0,#trigger_id; moveq r0,#1; movne r0,#0; bx lr
     try:
      run_to_bp(rsp,SAVE_CALLBACK)
      at_entry=profile_state(rsp)
      at_work=bytes.fromhex(at_entry['work_hex'])
      if at_entry['work_state']!=2 or rsp_read_u32(rsp,SAVE_MANAGER+8)!=slot or at_work[0x34c+slot] != slot_active:
       raise ProbeError('load state/selected slot changed before controlled confirm')
      if missing_save_before_confirm:
       hidden_save=save_path.with_name(save_path.name+'.h3-missing-probe')
       if not save_path.is_file() or hidden_save.exists():raise ProbeError('refusing pre-confirm missing-save probe: expected intact save and unused quarantine path')
       save_path.rename(hidden_save);read_error_injection.update({'save_path':str(save_path),'quarantine_path':str(hidden_save),'removed_at':'before_confirm'})
      rsp_write_mem(rsp,INPUT_TRIGGER2,confirm_stub)
      run_to_bp(rsp,SAVE_CALLBACK_EXIT)
     finally:
      rsp_write_mem(rsp,INPUT_TRIGGER2,before_input)
     after_pulse=profile_state(rsp)
     pulse_observation={'trigger_id':trigger_id,'target_slot':slot,'slot_active':slot_active,'name_nonzero':name_nonzero,'work_state_before':at_entry['work_state'],'work_state_after_callback':after_pulse['work_state'],'manager_flags_after_callback':after_pulse['manager_hex'][:8],'selected_slot_before':rsp_read_u32(rsp,SAVE_MANAGER+8),'slot_text_hex':text.hex(),'stub_restored':rsp_read_mem(rsp,INPUT_TRIGGER2,16)==before_input}
     if focus_game and (slot>0 or trigger_id!=0) and artifact_dir:pulse_observation['screen_result']=capture_screen(artifact_dir,'controlled-input-screen.png')
     trace_targets={0x0026B874:'save_load_process_start',0x002EF9AC:'save_load_process_step',0x00322D70:'save_load_process_read',0x00247C64:'save_load_io_worker',0x002D8E0C:'save_file_reader',0x002D8E60:'save_file_open_result',0x002C5948:'save_load_status_setter',0x002CED0C:'load_validation',0x001E989C:'title_main_callback',TITLE_STATE8:'title_state8',0x0019DFBC:'script_vm_dispatcher',0x001A07CC:'script_vm_nested_handler',0x001A080C:'script_vm_nested_return',0x001A0830:'script_vm_nested_zero_result',0x001C9C34:'save_ui_dispatcher_return'}
     armed=set(trace_targets)
     for addr in armed:rsp_set_bp(rsp,addr)
     rsp_set_bp(rsp,FIELD_MANAGER)
     try:
      for i in range(post_callbacks):
       rsp_set_bp(rsp,SAVE_CALLBACK)
       while True:
        here,interrupted,stop_reply=continue_and_read_pc(rsp)
        if interrupted:
         sp=decode_r0(rsp.request(b'p0d'));lr=decode_r0(rsp.request(b'p0e'))
         try:threads=rsp.request(b'qfThreadInfo').decode('ascii','replace')
         except Exception as exc:threads=f'error:{exc}'
         try:current_thread=rsp.request(b'qC').decode('ascii','replace')
         except Exception as exc:current_thread=f'error:{exc}'
         thread_states=[]
         try:
          ids=threads[1:].split(',') if threads.startswith('m') else []
          for tid in ids:
           if rsp.request(b'Hg'+tid.encode())==b'OK':
            thread_states.append({'id':tid,'pc':hex(decode_r0(rsp.request(b'p0f'))),'sp':hex(decode_r0(rsp.request(b'p0d'))),'lr':hex(decode_r0(rsp.request(b'p0e'))),'r0':hex(decode_r0(rsp.request(b'p00')))})
         except Exception as exc:thread_states.append({'error':str(exc)})
         stalled_at={'address':hex(here),'registers':[hex(decode_r0(rsp.request(f'p{j:x}'.encode()))) for j in range(4)],'sp':hex(sp),'lr':hex(lr),'stack_hex':rsp_read_mem(rsp,sp,0x80).hex() if 0x00100000<=sp<0x20000000 else None,'stop_reply':stop_reply,'threads':threads,'current_thread':current_thread,'thread_states':thread_states,'title_work_9c':hex(rsp_read_u32(rsp,title_work+0x9c)),'global_43e2f0':rsp_read_mem(rsp,0x0043E2F0,8).hex(),'manager_hex':rsp_read_mem(rsp,SAVE_MANAGER,0x10).hex(),'work_hex':profile_state(rsp)['work_hex'],'script_vm':profile_state(rsp)['script_vm']};field_hit=False
         if focus_game and artifact_dir:stalled_at['screen_result']=capture_screen(artifact_dir,'load-stall-screen.png')
         break
        if here==FIELD_MANAGER:
         field_hit=True;field_regs=[decode_r0(rsp.request(f'p{j:x}'.encode())) for j in range(4)];break
        if here in trace_targets:
         events.append({'address':hex(here),'name':trace_targets[here],'registers':[hex(decode_r0(rsp.request(f'p{j:x}'.encode()))) for j in range(4)],'lr':hex(decode_r0(rsp.request(b'p0e'))),'global_43e2f0':rsp_read_mem(rsp,0x0043E2F0,8).hex()})
         if trace_targets[here]=='save_load_io_worker':
          buffer_ptr=decode_r0(rsp.request(b'p3'))
          try:events[-1]['r3_buffer_head_0x120']=rsp_read_mem(rsp,buffer_ptr,0x120).hex()
          except Exception as exc:events[-1]['r3_buffer_read_error']=str(exc)
         if trace_targets[here] in ('save_file_reader','save_file_open_result'):
          events[-1]['save_reader_global_43e310_hex']=rsp_read_mem(rsp,0x0043E310,0x10).hex()
         if trace_targets[here]=='save_load_process_start':events[-1]['missing_save_injection_requested']=missing_save_before_read
         if missing_save_before_read and trace_targets[here]=='save_load_process_start' and hidden_save is None:
          hidden_save=save_path.with_name(save_path.name+'.h3-missing-probe')
          if not save_path.is_file() or hidden_save.exists():raise ProbeError('refusing missing-save injection: expected intact save and unused quarantine path')
          save_path.rename(hidden_save);read_error_injection.update({'save_path':str(save_path),'quarantine_path':str(hidden_save),'removed_at':'save_load_process_start'})
          events[-1]['save_temporarily_removed']=True
         if trace_targets[here]=='save_load_status_setter' and hidden_save is not None:
          hidden_save.rename(save_path);hidden_save=None;read_error_injection['restored_at']='save_load_status_setter';events[-1]['save_restored_before_status_setter']=True
         if force_status_error and trace_targets[here]=='save_load_status_setter' and status_error_injection['applied_at'] is None:
          status_error_injection['original_status_register']=events[-1]['registers'][0];write_reg(rsp,0,0);events[-1]['forced_status_register']='0x0';status_error_injection['applied_at']='save_load_status_setter_entry'
         rsp_clear_bp(rsp,here);armed.discard(here);continue
        if here!=SAVE_CALLBACK:raise ProbeError(f'unexpected GDB stop at {here:#x} during post-load trace')
        rsp_clear_bp(rsp,SAVE_CALLBACK);snap=profile_state(rsp);title_word=rsp_read_u32(rsp,title_work+0x9c);wb=bytes.fromhex(snap['work_hex']) if snap['work_hex'] else b''
        progress_samples.append({'index':i,'work_state':snap['work_state'],'sub_state':int.from_bytes(wb[0x0c:0x10],'little') if wb else None,'selected_slot':snap['selected_slot'],'manager_selected':rsp_read_u32(rsp,SAVE_MANAGER+8),'manager_flags':bytes.fromhex(snap['manager_hex'])[:4].hex(),'active_slots':wb[0x34c:0x34e].hex() if wb else None,'flags_49_54_55_70_71_72_73_355_378':[wb[o] for o in (0x49,0x54,0x55,0x70,0x71,0x72,0x73,0x355,0x378)] if wb else None,'counter_78':int.from_bytes(wb[0x78:0x7c],'little') if wb else None,'global_43e2f0':rsp_read_mem(rsp,0x0043E2F0,8).hex(),'title_work_9c':hex(title_word),'slot0_text_hex':snap['slot0_text_hex']})
        rsp_set_bp(rsp,SAVE_CALLBACK_EXIT)
        while True:
         here,interrupted,stop_reply=continue_and_read_pc(rsp)
         if interrupted:
          sp=decode_r0(rsp.request(b'p0d'));lr=decode_r0(rsp.request(b'p0e'))
          try:threads=rsp.request(b'qfThreadInfo').decode('ascii','replace')
          except Exception as exc:threads=f'error:{exc}'
          try:current_thread=rsp.request(b'qC').decode('ascii','replace')
          except Exception as exc:current_thread=f'error:{exc}'
          thread_states=[]
          try:
           ids=threads[1:].split(',') if threads.startswith('m') else []
           for tid in ids:
            if rsp.request(b'Hg'+tid.encode())==b'OK':
             thread_states.append({'id':tid,'pc':hex(decode_r0(rsp.request(b'p0f'))),'sp':hex(decode_r0(rsp.request(b'p0d'))),'lr':hex(decode_r0(rsp.request(b'p0e'))),'r0':hex(decode_r0(rsp.request(b'p00')))})
          except Exception as exc:thread_states.append({'error':str(exc)})
          stalled_at={'address':hex(here),'registers':[hex(decode_r0(rsp.request(f'p{j:x}'.encode()))) for j in range(4)],'sp':hex(sp),'lr':hex(lr),'stack_hex':rsp_read_mem(rsp,sp,0x80).hex() if 0x00100000<=sp<0x20000000 else None,'stop_reply':stop_reply,'threads':threads,'current_thread':current_thread,'thread_states':thread_states,'title_work_9c':hex(rsp_read_u32(rsp,title_work+0x9c)),'global_43e2f0':rsp_read_mem(rsp,0x0043E2F0,8).hex(),'manager_hex':rsp_read_mem(rsp,SAVE_MANAGER,0x10).hex(),'work_hex':profile_state(rsp)['work_hex'],'script_vm':profile_state(rsp)['script_vm']};field_hit=False
          if focus_game and artifact_dir:stalled_at['screen_result']=capture_screen(artifact_dir,'load-stall-screen.png')
          break
         if here==FIELD_MANAGER:
          field_hit=True;field_regs=[decode_r0(rsp.request(f'p{j:x}'.encode())) for j in range(4)];break
         if here in trace_targets:
          events.append({'address':hex(here),'name':trace_targets[here],'registers':[hex(decode_r0(rsp.request(f'p{j:x}'.encode()))) for j in range(4)],'lr':hex(decode_r0(rsp.request(b'p0e'))),'global_43e2f0':rsp_read_mem(rsp,0x0043E2F0,8).hex()})
          if trace_targets[here]=='save_load_io_worker':
           buffer_ptr=decode_r0(rsp.request(b'p03'))
           try:events[-1]['r3_buffer_head_0x120']=rsp_read_mem(rsp,buffer_ptr,0x120).hex()
           except Exception as exc:events[-1]['r3_buffer_read_error']=str(exc)
          if trace_targets[here]=='save_load_io_worker':
           buffer_ptr=decode_r0(rsp.request(b'p3'))
           try:events[-1]['r3_buffer_head_0x120']=rsp_read_mem(rsp,buffer_ptr,0x120).hex()
           except Exception as exc:events[-1]['r3_buffer_read_error']=str(exc)
          if trace_targets[here]=='save_load_process_start':events[-1]['missing_save_injection_requested']=missing_save_before_read
          if missing_save_before_read and trace_targets[here]=='save_load_process_start' and hidden_save is None:
           hidden_save=save_path.with_name(save_path.name+'.h3-missing-probe')
           if not save_path.is_file() or hidden_save.exists():raise ProbeError('refusing missing-save injection: expected intact save and unused quarantine path')
           save_path.rename(hidden_save);read_error_injection.update({'save_path':str(save_path),'quarantine_path':str(hidden_save),'removed_at':'save_load_process_start'})
           events[-1]['save_temporarily_removed']=True
          if trace_targets[here]=='save_load_status_setter' and hidden_save is not None:
           hidden_save.rename(save_path);hidden_save=None;read_error_injection['restored_at']='save_load_status_setter';events[-1]['save_restored_before_status_setter']=True
          if force_status_error and trace_targets[here]=='save_load_status_setter' and status_error_injection['applied_at'] is None:
           status_error_injection['original_status_register']=events[-1]['registers'][0];write_reg(rsp,0,0);events[-1]['forced_status_register']='0x0';status_error_injection['applied_at']='save_load_status_setter_entry'
          rsp_clear_bp(rsp,here);armed.discard(here);continue
         if here==SAVE_CALLBACK_EXIT:
          rsp_clear_bp(rsp,SAVE_CALLBACK_EXIT);break
         raise ProbeError(f'unexpected GDB stop at {here:#x} while stepping the load UI callback')
        if field_hit or stalled_at:break
       if field_hit or stalled_at:break
     finally:
      for addr in armed|{FIELD_MANAGER,SAVE_CALLBACK,SAVE_CALLBACK_EXIT}:
       try:rsp_clear_bp(rsp,addr)
       except Exception:pass
     # The copied save now shows the game's "Load complete" A prompt. Resume
     # only after the success bytes and state-5 work record are both observed.
     wb=bytes.fromhex(stalled_at['work_hex']) if stalled_at and stalled_at.get('work_hex') else b''
     status=bytes.fromhex(stalled_at['global_43e2f0']) if stalled_at else b''
     if stalled_at and len(wb)>8 and int.from_bytes(wb[8:12],'little')==5 and status[:4]==b'\x01\x00\x00\x01':
      try:
       rsp.request(b'Hg1')
       rsp.timeout=60;rsp.sock.settimeout(60)
       rsp_set_bp(rsp,INPUT_TRIGGER2)
       here,interrupted,stop_reply=continue_and_read_pc(rsp)
       if not interrupted and here==INPUT_TRIGGER2:
        trigger_id=decode_r0(rsp.request(b'p00'));lr=decode_r0(rsp.request(b'p0e'))
        if trigger_id==0:
         write_reg(rsp,0,1);write_reg(rsp,15,lr)
         post_load_confirm={'trigger_id':0,'return_value':1,'callsite_lr':hex(lr),'method':'one logical input getter result after observed Load complete dialog'}
        else:
         post_load_confirm={'trigger_id_seen':trigger_id,'error':'input getter stopped on a non-confirm trigger'}
       else:
        post_load_confirm={'error':'input getter not reached after load-complete status','pc':hex(here),'interrupted':interrupted,'stop_reply':stop_reply}
       rsp_clear_bp(rsp,INPUT_TRIGGER2)
       if post_load_confirm and 'return_value' in post_load_confirm:
        rsp_set_bp(rsp,FIELD_MANAGER);rsp_set_bp(rsp,SAVE_CALLBACK_EXIT)
        here,interrupted,stop_reply=continue_and_read_pc(rsp)
        if not interrupted and here==FIELD_MANAGER:
         field_hit=True;field_regs=[decode_r0(rsp.request(f'p{j:x}'.encode())) for j in range(4)]
         post_load_confirm['field_manager_reached']=True
        elif not interrupted and here==SAVE_CALLBACK_EXIT:
         rsp_clear_bp(rsp,SAVE_CALLBACK_EXIT)
         post_load_confirm['callback_exit_reached']=True
         snap=profile_state(rsp);post_load_confirm['work_state_after_ack']=snap['work_state'];post_load_confirm['manager_flags_after_ack']=snap['manager_hex'][:8]
         here,interrupted,stop_reply=continue_and_read_pc(rsp)
         if not interrupted and here==FIELD_MANAGER:
          field_hit=True;field_regs=[decode_r0(rsp.request(f'p{j:x}'.encode())) for j in range(4)]
          post_load_confirm['field_manager_reached']=True
         else:
          post_load_confirm['field_manager_reached']=False;post_load_confirm['post_ack_pc']=hex(here);post_load_confirm['post_ack_interrupted']=interrupted
        else:
         post_load_confirm['callback_or_field_not_reached']=True;post_load_confirm['pc']=hex(here);post_load_confirm['interrupted']=interrupted;post_load_confirm['stop_reply']=stop_reply
       rsp_clear_bp(rsp,FIELD_MANAGER);rsp_clear_bp(rsp,SAVE_CALLBACK_EXIT)
      except Exception as exc:
       post_load_confirm={'error':str(exc)}
      finally:
       try:rsp_clear_bp(rsp,INPUT_TRIGGER2)
       except Exception:pass
      if field_hit and field_regs:
       field_ticks,field_tick_status,field_scene_screen,field_call_probes=advance_field_scene(rsp,field_regs,field_tick_count,artifact_dir,focus_game,field_probe_addresses,axis_output,input_copy_retry_trace,input_copy_retry_event_limit,input_copy_stable_commit,navi_callback_return_trace)
    # Observe field map entry if it is already reached; bounded continuation only.
    if not confirm_load:
     try:
      rsp_set_bp(rsp,FIELD_MANAGER);rsp.continue_to_stop();field_hit=(pc(rsp)==FIELD_MANAGER)
     except Exception: field_hit=False
     finally:
      try:rsp_clear_bp(rsp,FIELD_MANAGER)
      except Exception:pass
     field_regs=[decode_r0(rsp.request(f'p{i:x}'.encode())) for i in range(4)] if field_hit else None
    post_read_screen=capture_screen(artifact_dir,'post-read-state-screen.png') if focus_game and (missing_save_before_read or force_status_error) and artifact_dir else None
    return {'kind':kind,'focus_result':focus_result,'screen_result':screen_result,'entry_registers':[hex(x) for x in entry_regs],'title_work_state8_hex':title_after.hex(),'save_load_samples':ui_samples,'controlled_load_confirm':pulse_observation,'load_complete_confirm':post_load_confirm,'post_confirm_events':events,'post_confirm_progress':progress_samples,'stalled_at':stalled_at,'field_manager_reached':field_hit,'field_manager_registers':[hex(x) for x in field_regs] if field_regs else None,'field_scene_ticks':field_ticks,'field_tick_status':field_tick_status,'field_scene_screen':field_scene_screen,'field_call_probes':field_call_probes,'post_read_screen':post_read_screen,'read_error_injection':read_error_injection,'status_error_injection':status_error_injection,'profile_user_before':tree_manifest(user),'save_before':save_snapshot(user)}
   finally:sock.close()
  finally:
   if proc.poll() is None:proc.terminate()
   try:proc.wait(timeout=10)
   except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
   if hidden_save is not None and hidden_save.exists():hidden_save.rename(save_path)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--profile-root',type=Path,default=ROOT/'build/h3-runtime/isolated',help='root containing original/ and patched/ staged profiles');ap.add_argument('--callbacks',type=int,default=20);ap.add_argument('--timeout',type=float,default=90);ap.add_argument('--confirm-load',action='store_true');ap.add_argument('--post-callbacks',type=int,default=60);ap.add_argument('--focus-game',action='store_true');ap.add_argument('--field-ticks',type=int,default=70);ap.add_argument('--field-probe-address',action='append',default=[],help='observe an original function address after the H3 field checkpoint (repeatable; e.g. 0x27fbc8)');ap.add_argument('--field-axis-output',help='controlled float pair x,y for the observed 0x27fbc8 query; overrides only its two caller-stack outputs on return');ap.add_argument('--input-copy-retry-trace',action='store_true',help='trace repeated source-copy attempts through a finite event limit');ap.add_argument('--input-copy-retry-event-limit',type=int,default=256,help='external maximum number of RSP breakpoint stops in the input-copy retry trace');ap.add_argument('--input-copy-stable-commit',action='store_true',help='allow the target helper retry loop to run without per-attempt stops, then capture only its stable commit if reached');ap.add_argument('--navi-callback-return-trace',action='store_true',help='bounded read-only trace of the live Navi callback through helper returns to LR 0x001A95E8; requires --field-probe-address 0x00399D60');ap.add_argument('--slot',type=int,default=0);ap.add_argument('--trigger-id',type=int,default=0);ap.add_argument('--probe-only',action='store_true');ap.add_argument('--missing-save-before-read',action='store_true',help='temporarily rename the staged save at the first load-process start breakpoint');ap.add_argument('--missing-save-before-confirm',action='store_true',help='temporarily rename the staged save after slot validation and before the controlled confirm input');ap.add_argument('--force-status-error',action='store_true',help='set status-setter r0 to zero at its entry to probe failure handling');a=ap.parse_args()
 if a.output.exists() and any(a.output.iterdir()):raise SystemExit('output directory is not fresh')
 a.output.mkdir(parents=True,exist_ok=True)
 root=a.profile_root.resolve(); runs=[]
 for kind in ('original','patched'):
  stage=root/kind; user=stage/'app/user'; port=PORTS[kind]
  run_artifacts=a.output/kind;run_artifacts.mkdir(parents=True,exist_ok=True)
  before=save_snapshot(user)
  if a.missing_save_before_read and a.missing_save_before_confirm:raise SystemExit('choose only one missing-save injection point')
  axis_output=None
  if a.field_axis_output:
   try:axis_output=tuple(float(x) for x in a.field_axis_output.split(','))
   except ValueError as exc:raise SystemExit(f'invalid --field-axis-output pair: {exc}')
   if len(axis_output)!=2 or any(not -1.0<=x<=1.0 for x in axis_output):raise SystemExit('--field-axis-output needs two comma-separated values within [-1,1]')
  if a.input_copy_retry_trace and a.input_copy_stable_commit:raise SystemExit('choose either per-attempt trace or stable-commit capture')
  if a.navi_callback_return_trace and 0x00399D60 not in tuple(int(x,0) for x in a.field_probe_address):raise SystemExit('--navi-callback-return-trace requires --field-probe-address 0x00399D60')
  result=run_one(kind,stage,user,port,a.timeout,a.callbacks,a.confirm_load,0 if a.probe_only else a.post_callbacks,a.focus_game,run_artifacts,a.field_ticks,a.slot,a.trigger_id,a.probe_only,a.missing_save_before_read,a.force_status_error,a.missing_save_before_confirm,tuple(int(x,0) for x in a.field_probe_address),axis_output,a.input_copy_retry_trace,a.input_copy_retry_event_limit,a.input_copy_stable_commit,a.navi_callback_return_trace)
  after=save_snapshot(user);result['save_before']=before;result['save_after']=after;result['save_unchanged']=before==after
  result['profile_after']=tree_manifest(user);result['non_mod_profile_unchanged']=result['profile_user_before']==result['profile_after']
  (a.output/f'{kind}.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');runs.append(result)
 scene_sig=lambda run:[(t['entry_registers'][0],t['entry_registers'][3],t['r1_r2_context_arg']) for t in run['field_scene_ticks']]
 comparison={'title_entry_registers_equal':runs[0]['entry_registers']==runs[1]['entry_registers'],'title_state8_equal':runs[0]['title_work_state8_hex']==runs[1]['title_work_state8_hex'],'save_load_callbacks_equal':runs[0]['save_load_samples']==runs[1]['save_load_samples'],'post_confirm_events_equal':runs[0]['post_confirm_events']==runs[1]['post_confirm_events'],'post_confirm_progress_equal':runs[0]['post_confirm_progress']==runs[1]['post_confirm_progress'],'load_complete_acknowledged_both':all((x.get('load_complete_confirm') or {}).get('return_value')==1 for x in runs),'field_manager_reached_both':all(x['field_manager_reached'] for x in runs),'field_scene_semantics_equal':scene_sig(runs[0])==scene_sig(runs[1]),'field_scene_ticks_both':all(len(x['field_scene_ticks'])>=2 for x in runs),'empty_slot_rejected_both':a.slot>0 and all(x.get('controlled_load_confirm',{}).get('slot_active')==0 and not x.get('controlled_load_confirm',{}).get('name_nonzero') and (x.get('post_confirm_progress') or [{}])[-1].get('work_state')==2 and not any(e.get('name')=='save_load_process_start' for e in x['post_confirm_events']) and not x['field_manager_reached'] for x in runs),'missing_save_response_both':a.missing_save_before_read and all((x.get('read_error_injection') or {}).get('restored_at')=='save_load_status_setter' and any(e.get('name')=='save_load_io_worker' for e in x['post_confirm_events']) and any(e.get('name')=='save_load_status_setter' for e in x['post_confirm_events']) and not x['field_manager_reached'] for x in runs),'save_unchanged_both':all(x['save_unchanged'] for x in runs),'profile_unchanged_both':all(x['non_mod_profile_unchanged'] for x in runs)}
 comparison.pop('missing_save_response_both',None)
 expected_removal_point='before_confirm' if a.missing_save_before_confirm else 'save_load_process_start'
 comparison['missing_file_removed_and_restored_both']=(a.missing_save_before_read or a.missing_save_before_confirm) and all((x.get('read_error_injection') or {}).get('removed_at')==expected_removal_point and (x.get('read_error_injection') or {}).get('restored_at')=='save_load_status_setter' for x in runs)
 comparison['setter_argument_r0_one_both']=(a.missing_save_before_read or a.missing_save_before_confirm) and all(any(e.get('name')=='save_load_status_setter' and e.get('registers',[None])[0]=='0x1' for e in x['post_confirm_events']) for x in runs)
 open_result=lambda x:next((e for e in x['post_confirm_events'] if e.get('name')=='save_file_open_result'),None)
 result_flag=lambda x:next((bytes.fromhex(e.get('global_43e2f0',''))[3] for e in x['post_confirm_events'] if e.get('name')=='save_load_status_setter' and len(bytes.fromhex(e.get('global_43e2f0','')))>=4),None)
 comparison['save_file_open_failure_both']=(a.missing_save_before_read or a.missing_save_before_confirm) and all(open_result(x) is not None and open_result(x).get('registers',[None])[0]=='0x0' for x in runs)
 comparison['load_result_flag_zero_both']=(a.missing_save_before_read or a.missing_save_before_confirm) and all(result_flag(x)==0 for x in runs)
 comparison['load_result_flag_one_both']=not (a.missing_save_before_read or a.missing_save_before_confirm) and all(result_flag(x)==1 for x in runs)
 comparison['real_read_error_reproduced_both']=(a.missing_save_before_read or a.missing_save_before_confirm) and all((x.get('read_error_injection') or {}).get('removed_at')==expected_removal_point and (x.get('read_error_injection') or {}).get('restored_at')=='save_load_status_setter' and open_result(x) is not None and open_result(x).get('registers',[None])[0]=='0x0' and result_flag(x)==0 and not x['field_manager_reached'] for x in runs)
 comparison['forced_status_error_response_both']=a.force_status_error and all((x.get('status_error_injection') or {}).get('applied_at')=='save_load_status_setter_entry' and any(e.get('name')=='save_load_status_setter' for e in x['post_confirm_events']) and not x['field_manager_reached'] and x['save_unchanged'] for x in runs)
 report={'status':'observed','target_slot':a.slot,'trigger_id':a.trigger_id,'probe_only':a.probe_only,'missing_save_before_read':a.missing_save_before_read,'missing_save_before_confirm':a.missing_save_before_confirm,'force_status_error':a.force_status_error,'comparison':comparison,'runs':[{k:v for k,v in r.items() if k not in ('profile_user_before','profile_after','title_work_state8_hex','save_load_samples')} for r in runs],'details':['save_load_samples contain raw workspace bytes and are written to per-run JSON',f'controlled trigger-{a.trigger_id} result was issued only in load state 2 after verifying target slot {a.slot} data/empty-state','post_confirm_events capture first entry at each selected original load service','missing-save injection records a temporary removal point and restoration; a real read-error pass requires a zero result from the original save-file open boundary and a zero load-result byte in both paired runs','setter input r0 is a flag mask, not the load result code; use the captured status bytes and original branch behavior','forced status failure is a debugger-injected negative control and is not evidence of real filesystem read-error handling','runtime comparison is exploratory unless a loaded scene checkpoint is reached']}
 (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':report['status'],'comparison':comparison,'output':str(a.output)},indent=2))
if __name__=='__main__':main()
