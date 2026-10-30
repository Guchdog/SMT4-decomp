#!/usr/bin/env python3
"""One bounded original-only H2 State-2 RSP capture; no guest-state forcing."""
from __future__ import annotations
import argparse, hashlib, json, os, random, shutil, socket, struct, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.h2_azahar_rsp_probe import Rsp, ProbeError, PROFILE_SEED_FILES, listener_owner, reserve_port, provision_profile, sha256

PACKET_ROOT=ROOT/'build/agent-work/H2-semantic/h2-state2-dispatch-runtime-capture/001'
TASK=PACKET_ROOT/'task.json'
H2DIFF=ROOT/'build/agent-work/H2-semantic/h2-rsp-slider-boundaries-restart/run-001/checks/h2-differential/report.json'
H2CALL=ROOT/'build/agent-work/H2-semantic/h2-rsp-slider-boundaries-restart/run-001/checks/h2-caller/report.json'
H3CALL=ROOT/'build/agent-work/H2-semantic/h2-rsp-slider-boundaries-restart/run-001/checks/h3-caller-002/report.json'
AZAHAR=ROOT/'build/agent-work/H2-semantic/h2-private-azahar-source/build-clang64/bin/Release/azahar.exe'
AZROOT=ROOT/'build/agent-work/H2-semantic/h2-private-azahar-source/azahar'
GAME=Path(r'E:\emulador3ds\00040000000E5C00 Shin Megami Tensei IV (CTR-P-AMXE) (v0.1.0) (U).piratelegit-decrypted.cci')
SEED=ROOT/'build/h2-runtime/profile-pristine-user'
SAVE_FIXTURE=ROOT/'build/h3-fixture/source/sdds4game1.sav'
SAVE_REL=Path('sdmc/Nintendo 3DS/00000000000000000000000000000000/00000000000000000000000000000000/title/00040000/000e5c00/data/00000001/sdds4game1.sav')
CODE=ROOT/'extracted/exefs/code.bin'
EXPECTED_CCI_SHA256='9cc760c2f37da9a4a3657e918e0eaebb3e8e80a91047e5c18f95aedf0242b4c2'
SUPPLIED_SAVE=Path(r'E:\emulador3ds\sdds4game1.sav')
EXPECTED_SAVE_SHA256='6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9'
MANIFEST=ROOT/'build/agent-work/H2-semantic/h2-private-azahar-source/h2-delivery-manifest.json'
RUNTIME_PACKAGE_PIN=ROOT/'docs/agent-work/h2-azahar-runtime-package-pin.json'
DLL_SOURCE_EXE=Path(r'E:\emulador3ds\azahar.exe')
EXPECTED_DLL_SOURCE_EXE_SHA256='c248414eb5328cb8bb720775ace6959898e2f50a0a10221c3a1e7a14190183eb'
PACKET_BASE=ROOT/'build/agent-work/H2-semantic/h2-state2-dispatch-runtime-capture'
STAGE_BASE=ROOT/'build/h2-runtime/h2-state2-dispatch-capture'
STAGE_DIRS={'h2-state2-dispatch-runtime-capture':'h2-state2-dispatch-capture','h2-state2-nested-callback-capture':'h2-state2-nested-callback-capture'}

# Guest code addresses from the pinned original image.
TRIGGER=0x002B902C; TRIGGER2=0x002BFFBC; LOGICAL=0x002C1830
TITLE_INIT=0x001EB02C; TITLE_READY=0x001EA15C; TITLE_CONFIG_INIT=0x002F4CA0
CALC=0x001EA928; CALC_RETURN=0x001EAFE4; CALC_STATE2=0x001EAF98
DISPATCH_CALL=0x0019DFE8; DISPATCH_RETURN=0x0019DFEC; CALC_STATE2_DISPATCH_RETURN=0x001EAFA0
CALC_FOLLOWUP_RETURN=0x001EAFB0; SECONDARY=0x002CAEF0; SECONDARY_EXIT=0x002CAFC8
READY_HELPER_CALL=0x002FC104; READY_HELPER_RETURN=0x002FC108; READY_OUTER_CALL=0x001EA3C8; READY_OUTER_RETURN=0x001EA3CC
G_TITLE_MAIN=0x0044E300; G_TITLE_CONFIG=0x0044E2D0; G_CONFIG=0x0044E0F8; HANDLER_TABLE=0x0044DED0
NESTED_HANDLER_TABLE=0x00406038; NESTED_WRAPPER=0x001A07CC
NESTED_CALLBACK_CALL=0x001A07FC; NESTED_CALLBACK_RETURN=0x001A0800
MAX_NESTED_CALLBACK_RETURNS=20
PRE_TITLE_MODE1_RETURN=0x002C18E0
INPUT_MODE_WORD=0x004650A8; INPUT_COUNTERS=0x004E3C58
MAX_PRE_TITLE_ORIGINAL_QUERIES=4096
PRE_TITLE_CALLERS={0x0010EDFC:'camp_func_0010edd4',0x0010EF08:'camp_func_0010edd4',0x0010EF70:'camp_func_0010edd4',0x0010EFC8:'camp_func_0010efb4'}
DANGEROUS=(0x0026FA94,0x0030A9A4)
# Read-only checkpoints around the native boot-script command which follows
# the one exact pre-menu call permitted below. These resolve where startup
# diverges without repeating a long blind wait or writing guest data.
SCRIPT_PROGRESS={
    0x001C05AC:'after-global-resource-query',
    0x001C05B8:'after-map-script-resource-init',
    0x001C05C4:'after-command-word-increment',
}
DISPATCH_CALLER_RETURN=0x00103164
DISPATCH_CALLER_NEXT=0x00103168
DISPATCH_CALLER_BRANCH_INPUT=0x0010316C
DISPATCH_CALLER_ZERO_BRANCH_TARGET=0x0010319C
DISPATCH_CALLER_COMMON_HELPER_RETURN=0x001031A4
DISPATCH_CALLER_PROBE_ARM_WORDS={0x00103164:0xE1A05000,0x00103168:0xE5D80010,0x0010316C:0xE3500000,0x00103170:0x0A000009,0x0010319C:0xE3A00000,0x001031A0:0xEB07048B,0x001031A4:0xE3750001}
BOOT_DISPATCH_EPILOGUE=0x001C03D0
BOOT_COMMAND_RETURN_CONTEXT_WORD=12
SVC_RETURN_PC=0x002A88A8
ATOMIC_RECHECK_PC=0x001465A8
ATOMIC_RETRY_BRANCH_PC=0x001465CC
ATOMIC_RETRY_CALL_PC=0x001465A4
MAX_ATOMIC_RETRY_BRANCH_HITS=2
ASD_SYNC_WAIT_RETURN_PC=0x002C36DC
ASD_LOCK_THREAD_COMPARE_PC=0x002C3AB4
ASD_LOCK_OWNER_STORE_PC=0x002C3ACC
ASD_LOCK_OWNER_POSTSTORE_PC=0x002C3AD0
ASD_LOCK_OBJECT_CALL_PC=0x0013AD6C
ASD_LOCK_OBJECT_RETURN_PC=0x0013AD70

class TraceError(RuntimeError): pass

class TraceDeadlineError(TraceError):
    def __init__(self, message:str):
        super().__init__(message)
        self.interrupt_stop_reply:bytes|None=None
        self.interrupt_error:str|None=None

def digest(b:bytes)->str: return hashlib.sha256(b).hexdigest()
def file_hash(p:Path)->str: return digest(p.read_bytes())
def read32(b:bytes,o:int=0)->int: return struct.unpack_from('<I',b,o)[0]
def frame_rsp(payload:bytes)->bytes: return b'$'+payload+b'#'+f'{sum(payload)&255:02x}'.encode()
def reg(rsp:Rsp,n:int)->int:
    raw=rsp.request(f'p{n:x}'.encode())
    try: b=bytes.fromhex(raw.decode())
    except Exception as e: raise TraceError(f'bad register p{n:x}: {raw!r}') from e
    if len(b)!=4: raise TraceError(f'expected 4-byte p{n:x}, got {len(b)}')
    return int.from_bytes(b,'little')
def mem(rsp:Rsp,a:int,n:int)->bytes:
    raw=rsp.request(f'm{a:x},{n:x}'.encode())
    if raw.startswith(b'E') or len(raw)!=2*n: raise TraceError(f'memory read failed {a:#x}+{n:#x}: {raw!r}')
    return bytes.fromhex(raw.decode())
def write_mem(rsp:Rsp,a:int,b:bytes,allowed:set[int]):
    if a not in allowed: raise TraceError(f'write outside temporary query stubs: {a:#x}')
    ans=rsp.request(f'M{a:x},{len(b):x}:'.encode()+b.hex().encode())
    if ans!=b'OK' or mem(rsp,a,len(b))!=b: raise TraceError(f'temporary stub write/readback failed at {a:#x}')
def setbp(rsp,a:int,n:int=4):
    if rsp.request(f'Z0,{a:x},{n:x}'.encode())!=b'OK': raise TraceError(f'breakpoint set failed {a:#x}')
def clearbp(rsp,a:int,n:int=4):
    if rsp.request(f'z0,{a:x},{n:x}'.encode())!=b'OK': raise TraceError(f'breakpoint clear failed {a:#x}')
def stop_pc(rsp:Rsp)->int: return reg(rsp,15)&0xffffffff

def interrupt_guest_and_wait(rsp:Rsp,timeout_s:float=2.0)->bytes:
    """Interrupt a timed-out continue and collect its read-only stop packet."""
    previous=rsp.sock.gettimeout()
    rsp.sock.settimeout(timeout_s)
    try:
        # RSP defines a raw ETX byte as an asynchronous interrupt, not a guest
        # memory/register write. The supervisor later terminates only its
        # disposable child as usual.
        rsp.sock.sendall(b'\x03')
        reply=rsp._packet()
        if not reply.startswith(b'T'):
            raise TraceError(f'guest interrupt returned unexpected stop packet {reply!r}')
        return reply
    finally:
        rsp.sock.settimeout(previous)

def timeout_guest_snapshot(rsp:Rsp,stop_reply:bytes)->dict:
    """Record a bounded register/stack snapshot after an explicit timeout interrupt."""
    registers={f'r{i}':hex(reg(rsp,i)&0xffffffff) for i in range(13)}
    sp=reg(rsp,13)&0xffffffff; lr=reg(rsp,14)&0xffffffff; pc=stop_pc(rsp)
    result={'stop_reply':stop_reply.decode('ascii','replace'),'pc':hex(pc),'lr':hex(lr),'sp':hex(sp),'r0_r12':registers}
    stack=b''
    if 0x00100000<=sp<0x20000000:
        try:
            stack=mem(rsp,sp,0x80)
            result['stack_prefix_0x80']=stack.hex()
        except Exception as exc: result['stack_read_error']=str(exc)
    if 0x00100000<=pc<0x20000000:
        try: result['pc_bytes_0x10']=mem(rsp,pc&~1,0x10).hex()
        except Exception as exc: result['pc_read_error']=str(exc)
    if pc==SVC_RETURN_PC and lr==ATOMIC_RECHECK_PC and len(stack)>=4:
        address=read32(stack)
        result['saved_r4_address_at_svc_return']=hex(address)
        if 0x00100000<=address and address+12<=0x20000000:
            raw_words={}
            for offset in (0,4,8):
                try:
                    value=read32(mem(rsp,address+offset,4))
                    raw_words[f'offset_{offset:#x}']=hex(value)
                    if offset==0:
                        result['word_at_saved_r4_at_interrupt']=hex(value)
                        result['word_at_saved_r4_signed']=value if value<0x80000000 else value-0x100000000
                except Exception as exc:
                    raw_words[f'offset_{offset:#x}_read_error']=str(exc)
            result['raw_words_at_saved_r4']=raw_words
    return result

def continue_until_deadline(rsp:Rsp,deadline:float,phase:str)->bytes:
    remaining=deadline-time.monotonic()
    if remaining<=0: raise TraceError(f'{phase} wall-clock bound expired before the next guest stop')
    previous=rsp.sock.gettimeout()
    rsp.sock.settimeout(remaining)
    try:
        return rsp.continue_to_stop()
    except TimeoutError as exc:
        error=TraceDeadlineError(f'{phase} wall-clock bound expired waiting for a guest stop')
        try: error.interrupt_stop_reply=interrupt_guest_and_wait(rsp)
        except Exception as interrupt_error: error.interrupt_error=f'{type(interrupt_error).__name__}: {interrupt_error}'
        raise error from exc
    finally:
        rsp.sock.settimeout(previous)
def title_config(rsp:Rsp)->tuple[int,int|None]:
    p=read32(mem(rsp,G_TITLE_CONFIG,4)); return p,(read32(mem(rsp,p+8,4)) if p else None)
def title_main(rsp:Rsp)->tuple[int,int|None,int|None]:
    p=read32(mem(rsp,G_TITLE_MAIN,4))
    return p,(read32(mem(rsp,p+8,4)) if p else None),(mem(rsp,p+0x63,1)[0] if p else None)
def title_main_state(rsp:Rsp)->tuple[int,int|None,int|None,int|None]:
    p=read32(mem(rsp,G_TITLE_MAIN,4))
    if not p:return 0,None,None,None
    return p,read32(mem(rsp,p+0x9c,4)),read32(mem(rsp,p+8,4)),mem(rsp,p+0x63,1)[0]
def task_fields(rsp:Rsp,p:int)->dict:
    if not p:return {'task_ptr':'0x00000000'}
    fields=mem(rsp,p,0xd4)
    ip=read32(fields,0x18); table=read32(fields,0xbc)
    try: hid=struct.unpack('<H',mem(rsp,table+4*ip,2))[0] if table else None
    except Exception: hid=None
    try: target=read32(mem(rsp,HANDLER_TABLE+4*hid,4)) if hid is not None else None
    except Exception: target=None
    try: nested_id=struct.unpack('<H',mem(rsp,table+4*ip+2,2))[0] if table and ip<0x1000 else None
    except Exception: nested_id=None
    try: nested_target=read32(mem(rsp,NESTED_HANDLER_TABLE+8*nested_id,4)) if nested_id is not None else None
    except Exception: nested_target=None
    return {'task_ptr':hex(p),'instruction_index':ip,'method_table':hex(table),'handler_id':hid,'handler_target_raw':hex(target) if target is not None else None,'nested_handler_id':nested_id,'nested_handler_target_raw':hex(nested_target) if nested_target is not None else None,'counter_cc':read32(fields,0xcc),'counter_d0':read32(fields,0xd0)}

def nested_callback_return_count(trace:dict)->int:
    return sum(1 for event in trace.get('nested_callbacks',[]) if event.get('phase')=='return')

def nested_callback_return_cap_reached(trace:dict)->bool:
    return nested_callback_return_count(trace)>=MAX_NESTED_CALLBACK_RETURNS

def title_query_breakpoints_for_phase(title_main_init_entered:bool)->tuple[int,...]:
    # Do not stop the emulator for generic pre-title windows that happen to
    # reuse these helpers. The original TitleMain initializer allocates and
    # publishes TitleMainWork before it registers its callbacks, and its pinned
    # ARM body does not call either query helper.
    return (TRIGGER,TRIGGER2) if title_main_init_entered else ()

def script_progress_snapshot(rsp:Rsp,pc:int,elapsed_s:float)->dict:
    context=reg(rsp,4)
    prefix=mem(rsp,context,0x40) if context else b''
    return {
        'label':'native-script-progress',
        'phase':SCRIPT_PROGRESS.get(pc,'native-dispatch-caller-return'),
        'pc':hex(pc),
        'elapsed_s':round(elapsed_s,3),
        'r0_r3':[hex(reg(rsp,i)) for i in range(4)],
        'lr':hex(reg(rsp,14)&~1),
        'context_pointer':hex(context) if context else None,
        'context_prefix_0x40':prefix.hex() if prefix else None,
        # +0x08 is recorded raw: its semantic field name is not established
        # for this caller context by the current type declaration.
        'context_word_plus_8':read32(prefix,8) if len(prefix)>=12 else None,
    }

def sync_wait_return_snapshot(rsp:Rsp,pc:int,elapsed_s:float)->dict:
    pointer=reg(rsp,4)&0xffffffff
    event={
        'label':'sync-wait-return-observation',
        'phase':'post-wrapper-callsite',
        'pc':hex(pc),
        'elapsed_s':round(elapsed_s,3),
        'r0_r4':[hex(reg(rsp,i)&0xffffffff) for i in range(5)],
        'r4_indirect_word_raw':None,
    }
    if 0x00100000<=pointer<0x20000000:
        try:
            raw=mem(rsp,pointer,4)
            if len(raw)==4:
                event['r4_indirect_word_raw']=hex(read32(raw))
        except Exception as exc:
            event['r4_indirect_word_read_error']=str(exc)
    return event

def atomic_retry_snapshot(rsp:Rsp,pc:int,elapsed_s:float)->dict:
    r2=reg(rsp,2)&0xffffffff
    r4=reg(rsp,4)&0xffffffff
    event={
        'label':'atomic-retry-path-observation',
        'phase':'conditional-branch-target' if pc==ATOMIC_RETRY_BRANCH_PC else 'retry-call-site',
        'pc':hex(pc),
        'elapsed_s':round(elapsed_s,3),
        'r0_r4':[hex(reg(rsp,i)&0xffffffff) for i in range(5)],
        'r2_signed':r2 if r2<0x80000000 else r2-0x100000000,
        'r4_indirect_word_raw':None,
    }
    if 0x00100000<=r4<0x20000000:
        try:
            raw=mem(rsp,r4,4)
            if len(raw)==4:
                event['r4_indirect_word_raw']=hex(read32(raw))
        except Exception as exc:
            event['r4_indirect_word_read_error']=str(exc)
    return event

def lock_thread_compare_snapshot(rsp:Rsp,pc:int,elapsed_s:float,expected_object_base:int|None=None)->dict:
    current=reg(rsp,0)&0xffffffff
    address=reg(rsp,4)&0xffffffff
    event={
        'label':'lock-thread-compare-raw-observation',
        'pc':hex(pc),
        'elapsed_s':round(elapsed_s,3),
        'current_thread_token_raw':hex(current),
        'object_base_raw':hex(address),
        'target_base_match':expected_object_base is None or address==expected_object_base,
        'object_words_raw':None,
    }
    if not event['target_base_match']:
        return event
    if 0x00100000<=address and address+12<=0x20000000:
        try:
            raw=mem(rsp,address,12)
            event['object_words_raw']={
                f'offset_{offset:#x}':hex(read32(raw,offset))
                for offset in (0,4,8)
            }
        except Exception as exc:
            event['object_words_read_error']=str(exc)
    return event

def lock_object_return_snapshot(rsp:Rsp,pc:int,elapsed_s:float,expected_object_base:int|None=None)->dict:
    address=reg(rsp,4)&0xffffffff
    event={
        'label':'lock-object-return-raw-observation',
        'pc':hex(pc),
        'elapsed_s':round(elapsed_s,3),
        'object_base_raw':hex(address),
        'target_base_match':expected_object_base is None or address==expected_object_base,
        'object_words_raw':None,
        'object_byte_0x76_raw':None,
    }
    if not event['target_base_match']:
        return event
    if 0x00100000<=address and address+12<=0x20000000:
        try:
            raw=mem(rsp,address,12)
            event['object_words_raw']={
                f'offset_{offset:#x}':hex(read32(raw,offset))
                for offset in (0,4,8)
            }
        except Exception as exc:
            event['object_words_read_error']=str(exc)
    if 0x00100000<=address+0x76 and address+0x77<=0x20000000:
        try:
            raw=mem(rsp,address+0x76,1)
            event['object_byte_0x76_raw']=hex(raw[0])
        except Exception as exc:
            event['object_byte_0x76_read_error']=str(exc)
    return event

def lock_owner_store_snapshot(rsp:Rsp,pc:int,elapsed_s:float,expected_object_base:int|None=None)->dict:
    owner=reg(rsp,0)&0xffffffff
    address=reg(rsp,4)&0xffffffff
    event={
        'label':'lock-owner-store-prewrite-raw-observation',
        'pc':hex(pc),
        'elapsed_s':round(elapsed_s,3),
        'owner_value_raw':hex(owner),
        'object_base_raw':hex(address),
        'target_base_match':expected_object_base is None or address==expected_object_base,
        'object_words_raw':None,
    }
    if not event['target_base_match']:
        return event
    if 0x00100000<=address and address+12<=0x20000000:
        try:
            raw=mem(rsp,address,12)
            event['object_words_raw']={
                f'offset_{offset:#x}':hex(read32(raw,offset))
                for offset in (0,4,8)
            }
        except Exception as exc:
            event['object_words_read_error']=str(exc)
    return event

def lock_owner_poststore_snapshot(rsp:Rsp,pc:int,elapsed_s:float,expected_object_base:int|None=None)->dict:
    value=reg(rsp,0)&0xffffffff
    address=reg(rsp,4)&0xffffffff
    event={
        'label':'lock-owner-poststore-raw-observation',
        'pc':hex(pc),
        'elapsed_s':round(elapsed_s,3),
        'r0_raw':hex(value),
        'object_base_raw':hex(address),
        'target_base_match':expected_object_base is None or address==expected_object_base,
        'object_words_raw':None,
    }
    if not event['target_base_match']:
        return event
    if 0x00100000<=address and address+12<=0x20000000:
        try:
            raw=mem(rsp,address,12)
            event['object_words_raw']={
                f'offset_{offset:#x}':hex(read32(raw,offset))
                for offset in (0,4,8)
            }
        except Exception as exc:
            event['object_words_read_error']=str(exc)
    return event

def should_rearm_atomic_retry_branch(branch_hits:int,callsite_hits:int)->bool:
    """Permit one second branch observation only after one branch-to-call pass."""
    return branch_hits==1 and callsite_hits==1 and branch_hits<MAX_ATOMIC_RETRY_BRANCH_HITS

def startup_lock_path_breakpoints(enabled:bool)->tuple[int,...]:
    """Opt-in early lock observers; keep the State-5 route free of extra stops by default."""
    return (ATOMIC_RETRY_BRANCH_PC,ASD_SYNC_WAIT_RETURN_PC,ASD_LOCK_OBJECT_CALL_PC) if enabled else ()

def startup_progress_breakpoints(enabled:bool)->tuple[int,...]:
    """Opt-in native-command progress stops; the title route does not require them."""
    return tuple(SCRIPT_PROGRESS) if enabled else ()

def should_arm_boot_dispatch_epilogue(pc:int,context_word_plus_8:int|None,armed:bool)->bool:
    return (pc==0x001C05C4 and context_word_plus_8==BOOT_COMMAND_RETURN_CONTEXT_WORD and not armed)

def should_arm_targeted_caller_return(saved_pc_raw:str|None)->bool:
    return saved_pc_raw==hex(DISPATCH_CALLER_RETURN)

def boot_dispatch_epilogue_snapshot(rsp:Rsp,elapsed_s:float)->dict:
    context=reg(rsp,4)&0xffffffff; sp=reg(rsp,13)&0xffffffff
    frame=mem(rsp,sp,8) if 0x00100000<=sp<0x20000000 else b''
    prefix=mem(rsp,context+8,4) if 0x00100000<=context<0x20000000 else b''
    return {
        'label':'native-dispatch-common-return-before-pop',
        'pc':hex(stop_pc(rsp)),
        'elapsed_s':round(elapsed_s,3),
        'context_pointer':hex(context),
        'context_word_plus_8':read32(prefix) if len(prefix)==4 else None,
        'sp':hex(sp),
        'saved_r4_raw':hex(read32(frame)) if len(frame)>=4 else None,
        'saved_pc_raw':hex(read32(frame,4)) if len(frame)>=8 else None,
        'pre_pop_r0':hex(reg(rsp,0)&0xffffffff),
        'stack_frame_0x08':frame.hex() if frame else None,
    }

def step_dispatch_caller_return(rsp:Rsp,active:set[int],deadline:float)->str:
    # Stop at the targeted caller's first instruction and execute it once.
    # Re-arm is intentionally omitted: this caller is generic and its other
    # returns flooded the original run before the boot-command return arrived.
    if DISPATCH_CALLER_RETURN in active:
        clearbp(rsp,DISPATCH_CALLER_RETURN); active.discard(DISPATCH_CALLER_RETURN)
    if DISPATCH_CALLER_NEXT in active:
        raise TraceError('dispatcher caller step breakpoint is already active')
    setbp(rsp,DISPATCH_CALLER_NEXT); active.add(DISPATCH_CALLER_NEXT)
    continue_until_deadline(rsp,deadline,'dispatcher caller step')
    if stop_pc(rsp)!=DISPATCH_CALLER_NEXT:
        raise TraceError(f'dispatcher caller did not reach step PC {DISPATCH_CALLER_NEXT:#x}')
    clearbp(rsp,DISPATCH_CALLER_NEXT); active.discard(DISPATCH_CALLER_NEXT)
    return hex(DISPATCH_CALLER_NEXT)

def dispatch_caller_branch_input_snapshot(rsp:Rsp,elapsed_s:float)->dict:
    pc=stop_pc(rsp)
    if pc!=DISPATCH_CALLER_BRANCH_INPUT:
        raise TraceError(f'dispatch caller byte probe stopped at {pc:#x}, expected {DISPATCH_CALLER_BRANCH_INPUT:#x}')
    r8=reg(rsp,8)&0xffffffff
    value=reg(rsp,0)&0xffffffff
    return {
        'label':'native-command-caller-branch-input',
        'phase':'after-original-ldrb-before-cmp',
        'pc':hex(pc),
        'elapsed_s':round(elapsed_s,3),
        'r0_loaded_raw':hex(value),
        'r8_base_raw':hex(r8),
        'source_address':hex((r8+0x10)&0xffffffff),
    }

def step_dispatch_caller_branch_input(rsp:Rsp,active:set[int],deadline:float,started:float)->dict:
    if stop_pc(rsp)!=DISPATCH_CALLER_NEXT:
        raise TraceError(f'dispatch caller byte probe must start at {DISPATCH_CALLER_NEXT:#x}')
    if DISPATCH_CALLER_BRANCH_INPUT in active:
        raise TraceError('dispatcher caller byte probe breakpoint is already active')
    setbp(rsp,DISPATCH_CALLER_BRANCH_INPUT); active.add(DISPATCH_CALLER_BRANCH_INPUT)
    continue_until_deadline(rsp,deadline,'dispatcher caller byte probe')
    event=dispatch_caller_branch_input_snapshot(rsp,time.monotonic()-started)
    clearbp(rsp,DISPATCH_CALLER_BRANCH_INPUT); active.discard(DISPATCH_CALLER_BRANCH_INPUT)
    return event

def dispatch_caller_zero_target_snapshot(rsp:Rsp,elapsed_s:float)->dict:
    pc=stop_pc(rsp)
    if pc!=DISPATCH_CALLER_ZERO_BRANCH_TARGET:
        raise TraceError(f'zero-branch target stop at {pc:#x}, expected {DISPATCH_CALLER_ZERO_BRANCH_TARGET:#x}')
    return {'label':'native-command-caller-zero-branch-target','phase':'after-original-cmp-beq-before-mov','pc':hex(pc),'elapsed_s':round(elapsed_s,3),'r0_raw':hex(reg(rsp,0)&0xffffffff),'r4_raw':hex(reg(rsp,4)&0xffffffff),'r5_raw':hex(reg(rsp,5)&0xffffffff),'lr':hex(reg(rsp,14)&~1)}

def dispatch_caller_common_helper_return_snapshot(rsp:Rsp,elapsed_s:float)->dict:
    pc=stop_pc(rsp)
    if pc!=DISPATCH_CALLER_COMMON_HELPER_RETURN:
        raise TraceError(f'common-helper return stop at {pc:#x}, expected {DISPATCH_CALLER_COMMON_HELPER_RETURN:#x}')
    return {'label':'native-command-caller-common-helper-return','phase':'after-original-bl-2c43d4','pc':hex(pc),'elapsed_s':round(elapsed_s,3),'r0_raw':hex(reg(rsp,0)&0xffffffff),'r4_raw':hex(reg(rsp,4)&0xffffffff),'r5_raw':hex(reg(rsp,5)&0xffffffff),'lr':hex(reg(rsp,14)&~1)}

def step_dispatch_caller_zero_path(rsp:Rsp,active:set[int],deadline:float,started:float)->list[dict]:
    if stop_pc(rsp)!=DISPATCH_CALLER_BRANCH_INPUT:
        raise TraceError(f'zero-branch probe must start at {DISPATCH_CALLER_BRANCH_INPUT:#x}')
    if reg(rsp,0)&0xffffffff:
        raise TraceError('zero-branch target probe requested for a nonzero loaded byte')
    if DISPATCH_CALLER_ZERO_BRANCH_TARGET in active:
        raise TraceError('zero-branch target breakpoint is already active')
    setbp(rsp,DISPATCH_CALLER_ZERO_BRANCH_TARGET); active.add(DISPATCH_CALLER_ZERO_BRANCH_TARGET)
    continue_until_deadline(rsp,deadline,'dispatcher caller zero-branch target')
    target=dispatch_caller_zero_target_snapshot(rsp,time.monotonic()-started)
    clearbp(rsp,DISPATCH_CALLER_ZERO_BRANCH_TARGET); active.discard(DISPATCH_CALLER_ZERO_BRANCH_TARGET)
    if DISPATCH_CALLER_COMMON_HELPER_RETURN in active:
        raise TraceError('common-helper return breakpoint is already active')
    setbp(rsp,DISPATCH_CALLER_COMMON_HELPER_RETURN); active.add(DISPATCH_CALLER_COMMON_HELPER_RETURN)
    continue_until_deadline(rsp,deadline,'dispatcher caller common-helper return')
    helper=dispatch_caller_common_helper_return_snapshot(rsp,time.monotonic()-started)
    clearbp(rsp,DISPATCH_CALLER_COMMON_HELPER_RETURN); active.discard(DISPATCH_CALLER_COMMON_HELPER_RETURN)
    return [target,helper]

def verify_dispatch_caller_probe_arm_words(image:bytes,base:int=0x00100000)->dict:
    if any(pc&1 for pc in DISPATCH_CALLER_PROBE_ARM_WORDS):
        raise TraceError('dispatcher caller probe addresses must be ARM-aligned')
    actual={}
    for pc,expected in DISPATCH_CALLER_PROBE_ARM_WORDS.items():
        offset=pc-base
        if offset<0 or offset+4>len(image):
            raise TraceError(f'dispatcher caller instruction lies outside the pinned image: {pc:#x}')
        actual[pc]=read32(image,offset)
        if actual[pc]!=expected:
            raise TraceError(f'dispatcher caller ARM word mismatch at {pc:#x}: {actual[pc]:#010x} != {expected:#010x}')
    return {hex(pc):hex(word) for pc,word in actual.items()}

def pass_through_pre_title_mode1_query(title_work:int,addr:int,return_pc:int)->bool:
    # Before TitleMainWork exists, this exact return PC is the mode-1 helper
    # call inside camp_func_002c1830. Preserve the original read-only query.
    return title_work==0 and addr==TRIGGER2 and return_pc==PRE_TITLE_MODE1_RETURN

def record_pre_title_query(summary:dict,sample:dict)->None:
    summary['calls']+=1
    key='|'.join(str(sample.get(k)) for k in ('id','wrapper_caller_return_raw','return','mode_word_before','counter_before'))
    group=summary['groups'].setdefault(key,{k:sample.get(k) for k in ('id','wrapper_caller_return_raw','wrapper_caller_name','return','mode_word_before','counter_before')}|{'count':0})
    group['count']+=1

def return_stub(value:int)->bytes:
    return struct.pack('<II',0xE3A00000|(value&255),0xE12FFF1E)

def query_stub(addr:int, first:int, second:int|None=None, response:int=1)->bytes:
    # ARM: cmp r0,first; [cmpeq r1,second]; moveq r0,#response; movne r0,#0; bx lr
    words=[0xE3500000|(first&255)]
    if second is not None: words.append(0x03510000|(second&255))
    words += [0x03A00000|(response&255),0x13A00000,0xE12FFF1E]
    return struct.pack('<'+'I'*len(words),*words)

def verify_offline_gates()->dict:
    task=json.loads(TASK.read_text()); bad=[]
    for rel,want in task['input_sha256'].items():
        p=ROOT/rel; got=file_hash(p) if p.is_file() else 'MISSING'
        if got!=want: bad.append({'path':rel,'expected':want,'actual':got})
    if bad: raise TraceError(f'frozen input hash mismatch: {bad}')
    diff=json.loads(H2DIFF.read_text()); h2=json.loads(H2CALL.read_text()); h3=json.loads(H3CALL.read_text())
    if any(row['passed']!=row['total'] for row in diff['callbacks'].values()): raise TraceError('H2 offline callback differential is incomplete')
    if any(row['cases_passed']!=row['case_count'] or row.get('first_counterexample') for row in diff['mapper_results']): raise TraceError('H2 mapper differential gate failed')
    if diff['fill_pair']['cases_passed']!=diff['fill_pair']['cases_expected'] or not diff['fill_pair']['negative_control_detected']: raise TraceError('H2 FillPair differential gate failed')
    if diff['caller_exit_code']!=0 or diff['caller_compile_exit']!=0: raise TraceError('H2 differential caller composition gate failed')
    if not h2.get('passed') or h2.get('case_count')!=h2.get('cases_passed') or h2.get('reference_sha256')!=file_hash(CODE): raise TraceError('H2 caller composition gate failed')
    if not h3.get('passed') or h3.get('reference',{}).get('code_sha256')!=file_hash(CODE): raise TraceError('H3 final-image caller gate failed')
    if h3.get('reference',{}).get('caller_target_low_bit')!=0 or not all(h3.get('in_place_equivalence',{}).values()): raise TraceError('H3 final-image ARM interworking/composition assertion failed')
    # Verify the original ARM BL targets used by the scenario have bit 0 clear,
    # including the caller whose post-call return is instrumented below.
    image=CODE.read_bytes(); base=0x100000
    dispatch_probe_words=verify_dispatch_caller_probe_arm_words(image,base)
    def bl_target(pc:int)->int:
        word=read32(image,pc-base); imm=word&0xffffff; disp=(imm<<2)-((1<<26) if imm&0x800000 else 0)
        if word>>24!=0xeb: raise TraceError(f'expected ARM BL at {pc:#x}, got {word:#010x}')
        return (pc+8+disp)&0xffffffff
    calls={hex(pc):hex(bl_target(pc)) for pc in (0x001EA348,0x001EA3B4,ASD_LOCK_OBJECT_CALL_PC)}
    return_word=read32(image,ASD_LOCK_OBJECT_RETURN_PC-base)
    owner_store_word=read32(image,ASD_LOCK_OWNER_STORE_PC-base)
    owner_poststore_word=read32(image,ASD_LOCK_OWNER_POSTSTORE_PC-base)
    if (calls['0x1ea348']!='0x30a9a4' or calls['0x1ea3b4']!='0x2f4ca0'
            or calls[hex(ASD_LOCK_OBJECT_CALL_PC)]!='0x2c3aa8'
            or any(int(v,16)&1 for v in calls.values())
            or ASD_LOCK_OBJECT_RETURN_PC!=ASD_LOCK_OBJECT_CALL_PC+4
            or return_word!=0xE5D40076
            or owner_store_word!=0xE5840004
            or ASD_LOCK_OWNER_POSTSTORE_PC!=ASD_LOCK_OWNER_STORE_PC+4
            or owner_poststore_word!=0xE5940008):
        raise TraceError(f'ARM interworking/call-return check failed: calls={calls}, return_word={return_word:#010x}, owner_store_word={owner_store_word:#010x}, owner_poststore_word={owner_poststore_word:#010x}')
    cci_sha=file_hash(GAME); save_sha=file_hash(SUPPLIED_SAVE)
    if cci_sha!=EXPECTED_CCI_SHA256: raise TraceError(f'CCI source hash mismatch: {cci_sha}')
    if save_sha!=EXPECTED_SAVE_SHA256: raise TraceError(f'supplied save hash mismatch: {save_sha}')
    return {'task_input_hashes':'passed','h2_differential':'passed','h2_caller':'passed','h3_final_image_caller':'passed','arm_interworking':'passed','h2_diff_source_identity_warnings':diff.get('source_identity_mismatches',[]),'checked_original_bl_targets':calls,'checked_lock_return_site':{'pc':hex(ASD_LOCK_OBJECT_RETURN_PC),'raw_instruction':hex(return_word),'expected_arm_instruction':'0xe5d40076'},'checked_lock_owner_store_site':{'pc':hex(ASD_LOCK_OWNER_STORE_PC),'raw_instruction':hex(owner_store_word),'expected_arm_instruction':'0xe5840004'},'checked_lock_owner_poststore_site':{'pc':hex(ASD_LOCK_OWNER_POSTSTORE_PC),'raw_instruction':hex(owner_poststore_word),'expected_arm_instruction':'0xe5940008'},'checked_dispatch_caller_byte_probe_instructions':dispatch_probe_words,'source_assets':{'cci_path':str(GAME),'cci_sha256_before':cci_sha,'expected_cci_sha256':EXPECTED_CCI_SHA256,'supplied_save_path':str(SUPPLIED_SAVE),'supplied_save_sha256_before':save_sha,'expected_supplied_save_sha256':EXPECTED_SAVE_SHA256,'save_staged_or_loaded':False},'reports':{str(p.relative_to(ROOT)):file_hash(p) for p in (H2DIFF,H2CALL,H3CALL)}}

PROFILE_CONFIG_FILES=(Path('config/qt-config.ini'),Path('config/custom/00040000000E5C00.ini'))

def stage_app(stage:Path, seed:Path, package_pin:dict, save_fixture:Path)->tuple[Path,Path,list[dict],list[dict],list[dict],dict]:
    if stage.exists(): raise TraceError(f'staging path already exists: {stage}')
    app=stage/'app'; app.mkdir(parents=True); user=app/'user'; user.mkdir()
    source=AZAHAR.resolve(strict=True); app_exe=app/'azahar.exe'; shutil.copy2(source,app_exe)
    dll_root=DLL_SOURCE_EXE.resolve(strict=True).parent
    if file_hash(DLL_SOURCE_EXE)!=EXPECTED_DLL_SOURCE_EXE_SHA256: raise TraceError('DLL-source Azahar executable pin mismatch')
    if package_pin['source_executable']['sha256']!=EXPECTED_DLL_SOURCE_EXE_SHA256: raise TraceError('dependency pin document names an unexpected package executable')
    expected={x['path']:x for x in package_pin['runtime_files']}
    actual_paths=[]
    for p in dll_root.iterdir():
        if p.is_file() and p.suffix.lower()=='.dll': actual_paths.append(p)
    for rel in ('plugins','scripting/AzaharRPC.py','qt.conf'):
        p=dll_root/rel
        if p.is_file(): actual_paths.append(p)
        elif p.is_dir(): actual_paths.extend(x for x in p.rglob('*') if x.is_file())
    actual={str(p.relative_to(dll_root)).replace('\\','/'):p for p in actual_paths}
    if set(actual)!=set(expected): raise TraceError(f'Azahar runtime dependency set differs from reviewed pin: missing={sorted(set(expected)-set(actual))}, extra={sorted(set(actual)-set(expected))}')
    runtime_assets=[]
    for rel,p in sorted(actual.items()):
        record={'path':rel,'source_sha256':file_hash(p),'expected_sha256':expected[rel]['sha256'],'bytes':p.stat().st_size}
        if record['source_sha256']!=record['expected_sha256']: raise TraceError(f'Azahar runtime dependency hash mismatch: {rel}')
        target=app/Path(rel); target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,target)
        record['staged_sha256']=file_hash(target)
        if record['staged_sha256']!=record['source_sha256']: raise TraceError(f'staged Azahar dependency changed: {rel}')
        runtime_assets.append(record)
    qt=dll_root/'qt.conf'
    if qt.is_file(): shutil.copy2(qt,app/'qt.conf')
    if file_hash(app_exe)!=file_hash(source): raise TraceError('staged executable hash mismatch')
    files=provision_profile(seed,user)
    config_src=seed/'config'
    config_records=[]
    for rel in PROFILE_CONFIG_FILES:
        src=seed/rel
        if not src.is_file(): raise TraceError(f'pinned profile config missing: {rel.as_posix()}')
        resolved=src.resolve(strict=True)
        if not resolved.is_relative_to(seed.resolve(strict=True)): raise TraceError(f'profile config escapes seed root: {rel.as_posix()}')
        config_records.append({'relative_path':rel.as_posix(),'source_sha256':file_hash(resolved),'bytes':resolved.stat().st_size})
    if config_src.is_dir(): shutil.copytree(config_src,user/'config',dirs_exist_ok=True)
    for record,rel in zip(config_records,PROFILE_CONFIG_FILES):
        staged=user/rel
        record['staged_sha256_after_copy']=file_hash(staged)
        if record['staged_sha256_after_copy']!=record['source_sha256']: raise TraceError(f'profile config copy/hash mismatch: {rel.as_posix()}')
    qt_ini=user/'config/qt-config.ini'
    if qt_ini.exists():
        raw=qt_ini.read_bytes()
        raw=(raw.replace(b'frame_limit\\default=true',b'frame_limit\\default=false')
             .replace(b'frame_limit=100',b'frame_limit=0')
             .replace(b'use_vsync\\default=true',b'use_vsync\\default=false')
             .replace(b'use_vsync=true',b'use_vsync=false'))
        qt_ini.write_bytes(raw)
    game_ini=user/'config/custom/00040000000E5C00.ini'
    if game_ini.exists():
        raw=game_ini.read_bytes(); crlf=b'\r\n' if b'\r\n' in raw else b'\n'
        raw=(raw.replace(b'frame_limit\\use_global=true',b'frame_limit\\use_global=false'+crlf+b'frame_limit=0')
             .replace(b'use_vsync\\use_global=true',b'use_vsync\\use_global=false'+crlf+b'use_vsync=false'))
        game_ini.write_bytes(raw)
    for record,rel in zip(config_records,PROFILE_CONFIG_FILES): record['staged_sha256_after_runtime_settings']=file_hash(user/rel)
    fixture_hash=file_hash(save_fixture)
    if fixture_hash!=EXPECTED_SAVE_SHA256: raise TraceError(f'disposable save fixture hash mismatch: {fixture_hash}')
    save_target=user/SAVE_REL
    save_target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(save_fixture,save_target)
    staged_hash=file_hash(save_target)
    if staged_hash!=EXPECTED_SAVE_SHA256: raise TraceError(f'staged disposable save fixture hash mismatch: {staged_hash}')
    fixture_record={'source':str(save_fixture),'source_sha256_before':fixture_hash,'destination':str(save_target),'staged_sha256':staged_hash,'bytes':save_target.stat().st_size}
    if file_hash(save_fixture)!=fixture_hash: raise TraceError('disposable save fixture changed while staging')
    return app_exe,user,files,runtime_assets,config_records,fixture_record

def attach(proc:subprocess.Popen,port:int,timeout:float)->tuple[socket.socket,Rsp,str,int]:
    deadline=time.monotonic()+90
    while time.monotonic()<deadline:
        if proc.poll() is not None: raise TraceError(f'Azahar exited before listener: {proc.returncode}')
        owner=listener_owner(port)
        if owner is not None: break
        time.sleep(.2)
    owner=listener_owner(port)
    if owner!=proc.pid: raise TraceError(f'listener owner mismatch/not loopback-only: {owner} != {proc.pid}')
    sock=socket.create_connection(('127.0.0.1',port),timeout=timeout); rsp=Rsp(sock,timeout)
    sup=rsp.request(b'qSupported:multiprocess+;swbreak+;hwbreak+;QStartNoAckMode+')
    if not sup or sup.startswith(b'E'): raise TraceError(f'qSupported failed: {sup!r}')
    if rsp.request(b'!')!=b'OK': raise TraceError('extended mode rejected')
    info=rsp.request(b'qfProcessInfo')
    if not info.startswith(b'pid:'): raise TraceError(f'qfProcessInfo failed: {info!r}')
    pid=info.split(b':',1)[1].split(b';',1)[0].decode()
    try: guest_pid=int(pid,16)
    except ValueError as e: raise TraceError(f'invalid RSP guest process id {pid!r}') from e
    if guest_pid<=0: raise TraceError(f'RSP reported nonpositive guest process id {pid!r}')
    stop=rsp.request(b'vAttach;'+pid.encode())
    if not stop.startswith(b'T'): raise TraceError(f'vAttach failed: {stop!r}')
    return sock,rsp,pid,owner

def run_to(rsp:Rsp,pc:int,active:set[int],timeout_s:float)->None:
    setbp(rsp,pc); active.add(pc)
    deadline=time.monotonic()+timeout_s
    try:
        continue_until_deadline(rsp,deadline,'breakpoint wait')
        actual=stop_pc(rsp)
        if actual!=pc: raise TraceError(f'expected breakpoint {pc:#x}, stopped at {actual:#x}')
    except Exception:
        raise

def patch_query_once(rsp:Rsp,addr:int,match0:int,match1:int|None,response:int,active:set[int],trace:list[dict],label:str)->dict:
    # Stop before the original query, patch only its code, restore at this call's LR.
    setbp(rsp,addr); active.add(addr)
    while True:
        rsp.continue_to_stop(); pc=stop_pc(rsp)
        if pc!=addr: raise TraceError(f'{label}: unexpected stop {pc:#x} while waiting for query {addr:#x}')
        a0=reg(rsp,0); a1=reg(rsp,1); lr=reg(rsp,14)&~1
        clearbp(rsp,addr); active.discard(addr)
        original=mem(rsp,addr,20 if match1 is not None else 16)
        stub=query_stub(addr,match0,match1)
        write_mem(rsp,addr,stub,{TRIGGER,TRIGGER2,LOGICAL})
        return_added = lr not in active
        if return_added: setbp(rsp,lr); active.add(lr)
        try:
            rsp.continue_to_stop()
            if stop_pc(rsp)!=lr: raise TraceError(f'{label}: query did not return at {lr:#x}')
            rv=reg(rsp,0)
        finally:
            # Restore query bytes before resuming the title callback.
            write_mem(rsp,addr,original,{TRIGGER,TRIGGER2,LOGICAL})
            if return_added: clearbp(rsp,lr); active.discard(lr)
        observed={'label':label,'address':hex(addr),'args':[hex(a0),hex(a1)],'return':rv,'requested_response':response,'return_pc':hex(lr)}
        trace.append(observed)
        if response is None or ((a0==match0 and (match1 is None or a1==match1)) == (response==1)):
            return observed
        # Not the logical query to answer; re-arm and allow original helper output to be deterministic zero.
        if len(trace)>512: raise TraceError(f'{label}: exceeded 512 query calls')
        # return 0 for nonmatching inputs was supplied by stub; next call is intercepted on next iteration.
        setbp(rsp,addr); active.add(addr)

def logical_stub_scenario(rsp:Rsp,trace:list[dict],active:set[int],timeout_s:float,observe_startup_lock_path:bool=False,observe_startup_progress:bool=False)->dict:
    # Observe the actual title menu state and feed only original logical trigger queries.
    startup_observers=startup_lock_path_breakpoints(observe_startup_lock_path)
    progress_observers=startup_progress_breakpoints(observe_startup_progress)
    for a in DANGEROUS+(TITLE_INIT,TITLE_CONFIG_INIT)+title_query_breakpoints_for_phase(False)+progress_observers+startup_observers: setbp(rsp,a); active.add(a)
    startup_summary={'label':'pre-title-original-mode1-query-summary','calls':0,'groups':{}}
    trace.append(startup_summary)
    started=time.monotonic(); deadline=started+timeout_s; query_count=0; pre_title_query_count=0; right_events=[]; confirm_event=None; title_init_seen=False; boot_startup_passed=False; boot_dispatch_epilogue_armed=False; targeted_caller_return_armed=False; atomic_retry_branch_hits=0; atomic_retry_callsite_hits=0; lock_object_base=None
    while time.monotonic()<deadline and query_count<512 and pre_title_query_count<MAX_PRE_TITLE_ORIGINAL_QUERIES:
        continue_until_deadline(rsp,deadline,'title startup'); pc=stop_pc(rsp)
        if pc==ASD_SYNC_WAIT_RETURN_PC:
            trace.append(sync_wait_return_snapshot(rsp,pc,time.monotonic()-started))
            clearbp(rsp,ASD_SYNC_WAIT_RETURN_PC); active.discard(ASD_SYNC_WAIT_RETURN_PC)
            continue
        if pc==ASD_LOCK_OBJECT_CALL_PC:
            lock_object_base=reg(rsp,0)&0xffffffff
            trace.append({'label':'lock-object-specific-callsite','pc':hex(pc),'elapsed_s':round(time.monotonic()-started,3),'object_base_raw':hex(lock_object_base),'lr':hex(reg(rsp,14)&~1)})
            clearbp(rsp,ASD_LOCK_OBJECT_CALL_PC); active.discard(ASD_LOCK_OBJECT_CALL_PC)
            if ASD_LOCK_THREAD_COMPARE_PC not in active:
                setbp(rsp,ASD_LOCK_THREAD_COMPARE_PC); active.add(ASD_LOCK_THREAD_COMPARE_PC)
            if ASD_LOCK_OWNER_STORE_PC not in active:
                setbp(rsp,ASD_LOCK_OWNER_STORE_PC); active.add(ASD_LOCK_OWNER_STORE_PC)
            if ASD_LOCK_OWNER_POSTSTORE_PC not in active:
                setbp(rsp,ASD_LOCK_OWNER_POSTSTORE_PC); active.add(ASD_LOCK_OWNER_POSTSTORE_PC)
            if ASD_LOCK_OBJECT_RETURN_PC not in active:
                setbp(rsp,ASD_LOCK_OBJECT_RETURN_PC); active.add(ASD_LOCK_OBJECT_RETURN_PC)
            continue
        if pc==ASD_LOCK_OWNER_STORE_PC:
            trace.append(lock_owner_store_snapshot(rsp,pc,time.monotonic()-started,lock_object_base))
            clearbp(rsp,ASD_LOCK_OWNER_STORE_PC); active.discard(ASD_LOCK_OWNER_STORE_PC)
            continue
        if pc==ASD_LOCK_OWNER_POSTSTORE_PC:
            trace.append(lock_owner_poststore_snapshot(rsp,pc,time.monotonic()-started,lock_object_base))
            clearbp(rsp,ASD_LOCK_OWNER_POSTSTORE_PC); active.discard(ASD_LOCK_OWNER_POSTSTORE_PC)
            continue
        if pc==ASD_LOCK_OBJECT_RETURN_PC:
            trace.append(lock_object_return_snapshot(rsp,pc,time.monotonic()-started,lock_object_base))
            clearbp(rsp,ASD_LOCK_OBJECT_RETURN_PC); active.discard(ASD_LOCK_OBJECT_RETURN_PC)
            continue
        if pc==ASD_LOCK_THREAD_COMPARE_PC:
            trace.append(lock_thread_compare_snapshot(rsp,pc,time.monotonic()-started,lock_object_base))
            clearbp(rsp,ASD_LOCK_THREAD_COMPARE_PC); active.discard(ASD_LOCK_THREAD_COMPARE_PC)
            continue
        if pc==ATOMIC_RETRY_BRANCH_PC:
            atomic_retry_branch_hits+=1
            event=atomic_retry_snapshot(rsp,pc,time.monotonic()-started)
            event['observation_index']=atomic_retry_branch_hits
            trace.append(event)
            clearbp(rsp,ATOMIC_RETRY_BRANCH_PC); active.discard(ATOMIC_RETRY_BRANCH_PC)
            if atomic_retry_branch_hits==1:
                setbp(rsp,ATOMIC_RETRY_CALL_PC); active.add(ATOMIC_RETRY_CALL_PC)
            continue
        if pc==ATOMIC_RETRY_CALL_PC:
            atomic_retry_callsite_hits+=1
            event=atomic_retry_snapshot(rsp,pc,time.monotonic()-started)
            event['observation_index']=atomic_retry_callsite_hits
            trace.append(event)
            clearbp(rsp,ATOMIC_RETRY_CALL_PC); active.discard(ATOMIC_RETRY_CALL_PC)
            if should_rearm_atomic_retry_branch(atomic_retry_branch_hits,atomic_retry_callsite_hits):
                setbp(rsp,ATOMIC_RETRY_BRANCH_PC); active.add(ATOMIC_RETRY_BRANCH_PC)
            continue
        if pc==DISPATCH_CALLER_RETURN and targeted_caller_return_armed:
            event=script_progress_snapshot(rsp,pc,time.monotonic()-started)
            event['phase']='targeted-native-command-caller-return'
            trace.append(event)
            clearbp(rsp,DISPATCH_CALLER_RETURN); active.discard(DISPATCH_CALLER_RETURN)
            targeted_caller_return_armed=False
            event['caller_step_pc']=step_dispatch_caller_return(rsp,active,deadline)
            branch_input=step_dispatch_caller_branch_input(rsp,active,deadline,started)
            trace.append(branch_input)
            if int(branch_input['r0_loaded_raw'],16)==0:
                trace.extend(step_dispatch_caller_zero_path(rsp,active,deadline,started))
            continue
        if pc==DISPATCH_CALLER_RETURN:
            raise TraceError('generic dispatcher caller return stopped without the targeted epilogue arm')
        if pc==BOOT_DISPATCH_EPILOGUE and boot_dispatch_epilogue_armed:
            event=boot_dispatch_epilogue_snapshot(rsp,time.monotonic()-started)
            trace.append(event)
            clearbp(rsp,BOOT_DISPATCH_EPILOGUE); active.discard(BOOT_DISPATCH_EPILOGUE)
            boot_dispatch_epilogue_armed=False
            if should_arm_targeted_caller_return(event['saved_pc_raw']):
                setbp(rsp,DISPATCH_CALLER_RETURN); active.add(DISPATCH_CALLER_RETURN)
                targeted_caller_return_armed=True
            continue
        if pc in SCRIPT_PROGRESS:
            event=script_progress_snapshot(rsp,pc,time.monotonic()-started)
            trace.append(event)
            clearbp(rsp,pc); active.discard(pc)
            if should_arm_boot_dispatch_epilogue(pc,event['context_word_plus_8'],boot_dispatch_epilogue_armed):
                setbp(rsp,BOOT_DISPATCH_EPILOGUE); active.add(BOOT_DISPATCH_EPILOGUE)
                boot_dispatch_epilogue_armed=True
            continue
        work,state,selection,flag=title_main_state(rsp)
        if pc in DANGEROUS:
            r4=reg(rsp,4); sp=reg(rsp,13)
            lr=reg(rsp,14)&~1; r0=reg(rsp,0)
            event={'label':'safety-guard','pc':hex(pc),'lr':hex(lr),'r0_r12':[hex(reg(rsp,i)) for i in range(13)],'sp':hex(sp),'title_work':hex(work) if work else None,'title_state':state,'selection':selection,'flag_63':flag,'r4_context_pointer':hex(r4)}
            context=b''
            try: context=mem(rsp,r4,0x40); event['r4_context_prefix_0x40']=context.hex()
            except Exception as exc: event['r4_context_read_error']=str(exc)
            script_state=read32(context,8) if len(context)>=12 else None
            event['r4_context_state_plus_8']=script_state
            # The pinned H3 runtime reaches the title initializer after this one
            # pre-menu boot script call. Permit only its observed exact context;
            # retain guards for every title-driven New Game/Load dispatch.
            if (pc==0x0026FA94 and not work and script_state==11 and r0==0 and not boot_startup_passed):
                event['classification']='single-pre-menu-original-boot-call'
                event['action']='executed-original-callee-once; no guest state was written'
                clearbp(rsp,pc); active.discard(pc); setbp(rsp,lr); active.add(lr)
                continue_until_deadline(rsp,deadline,'title startup')
                if stop_pc(rsp)!=lr: raise TraceError(f'pre-menu boot callee did not return at {lr:#x}')
                event['callee_return_r0']=reg(rsp,0)
                event['title_work_after_return']=hex(title_main_state(rsp)[0]) if title_main_state(rsp)[0] else None
                clearbp(rsp,lr); active.discard(lr); setbp(rsp,pc); active.add(pc)
                trace.append(event); boot_startup_passed=True
                continue
            if 0x00100000<=sp<0x20000000:
                try: event['stack_prefix_0x80']=mem(rsp,sp,0x80).hex()
                except Exception as exc: event['stack_read_error']=str(exc)
            trace.append(event)
            raise TraceError(f'safety guard hit before Audio Settings (title_work={work}, caller_state={script_state}): {pc:#x}')
        if pc==TITLE_INIT:
            title_init_seen=True
            for a in title_query_breakpoints_for_phase(title_init_seen):
                if a not in active: setbp(rsp,a); active.add(a)
            trace.append({'label':'title-main-init','pc':hex(pc),'title_work':hex(work) if work else None,'query_breakpoints_armed_after_entry':True})
            clearbp(rsp,TITLE_INIT); active.discard(TITLE_INIT); continue
        if pc==TITLE_CONFIG_INIT:
            if not confirm_event: raise TraceError('Audio Settings initializer reached without observed A query')
            clearbp(rsp,TITLE_CONFIG_INIT); active.discard(TITLE_CONFIG_INIT)
            for a in DANGEROUS+(TRIGGER,TRIGGER2):
                if a in active: clearbp(rsp,a); active.discard(a)
            return {'title_main_init_observed':title_init_seen,'title_work':hex(work) if work else None,'title_state_before_open':state,'selection_before_open':selection,'right_queries':right_events,'a_confirm':confirm_event,'audio_settings_init':hex(pc),'query_count':query_count}
        if pc not in (TRIGGER,TRIGGER2): raise TraceError(f'unexpected title-input stop {pc:#x}')
        addr=pc; a0=reg(rsp,0); lr=reg(rsp,14)&~1
        if pass_through_pre_title_mode1_query(work,addr,lr):
            # The original mode-1 helper is a read-only lookup. Let it execute
            # unchanged while the title object is absent; forcing a zero here
            # can suppress a real startup input edge and prevent title init.
            sp=reg(rsp,13)
            try: wrapper_caller=read32(mem(rsp,sp+12,4))
            except Exception: wrapper_caller=None
            mode_word=read32(mem(rsp,INPUT_MODE_WORD,4))
            counter=read32(mem(rsp,INPUT_COUNTERS+4*a0,4)) if a0<31 else None
            clearbp(rsp,addr); active.discard(addr)
            return_added=lr not in active
            if return_added: setbp(rsp,lr); active.add(lr)
            try:
                continue_until_deadline(rsp,deadline,'title startup')
                if stop_pc(rsp)!=lr: raise TraceError(f'original mode-1 query missed return PC {lr:#x}')
                rv=reg(rsp,0)
            finally:
                if return_added: clearbp(rsp,lr); active.discard(lr)
            sample={'id':a0,'return':rv,'return_pc':hex(lr),'wrapper_caller_return_raw':hex(wrapper_caller) if wrapper_caller is not None else None,'wrapper_caller_name':PRE_TITLE_CALLERS.get(wrapper_caller),'mode_word_before':hex(mode_word),'counter_before':hex(counter) if counter is not None else None,'original_helper_executed':True,'temporary_code_stub_used':False}
            record_pre_title_query(startup_summary,sample); pre_title_query_count+=1
            setbp(rsp,addr); active.add(addr)
            continue
        desired_id=None; response=0; label='title-input-unanswered'
        if state==1 and addr==TRIGGER2 and a0==0:
            # Original intro animation polls A in state 1 (caller return 0x3bce08).
            # The accepted H3 startup uses this same logical query to skip it.
            desired_id=0; response=1; label='title-intro-confirm'
        elif state==5 and selection is not None and addr==TRIGGER:
            if selection in (0,1): desired_id=6
            elif selection==3: desired_id=5
            if desired_id is not None: response=1; label='title-navigation'
        elif state==5 and selection==2 and addr==TRIGGER2 and a0==0:
            desired_id=0; response=1; label='title-a-confirm'
        original=mem(rsp,addr,16)
        clearbp(rsp,addr); active.discard(addr)
        write_mem(rsp,addr,query_stub(addr,desired_id if desired_id is not None else 0xff,response=response),{TRIGGER,TRIGGER2,LOGICAL})
        return_added=lr not in active
        if return_added: setbp(rsp,lr); active.add(lr)
        try:
            continue_until_deadline(rsp,deadline,'title startup')
            if stop_pc(rsp)!=lr: raise TraceError(f'{label}: query did not return at {lr:#x}')
            rv=reg(rsp,0)
        finally:
            write_mem(rsp,addr,original,{TRIGGER,TRIGGER2,LOGICAL})
            if return_added: clearbp(rsp,lr); active.discard(lr)
        after_work,after_state,after_selection,after_flag=title_main_state(rsp)
        event={'label':label,'address':hex(addr),'id':a0,'return':rv,'requested_response':response,'title_work_before':hex(work) if work else None,'title_state_before':state,'selection_before':selection,'title_work_after_query':hex(after_work) if after_work else None,'title_state_after_query':after_state,'selection_after_query':after_selection,'flag_63_after_query':after_flag,'return_pc':hex(lr)}
        trace.append(event); query_count+=1
        if label=='title-navigation' and rv==1: right_events.append(event)
        if label=='title-a-confirm' and rv==1: confirm_event=event
        for a in (TRIGGER,TRIGGER2):
            if a not in active: setbp(rsp,a); active.add(a)
    if pre_title_query_count>=MAX_PRE_TITLE_ORIGINAL_QUERIES: raise TraceError(f'pre-title original mode-1 query bound {MAX_PRE_TITLE_ORIGINAL_QUERIES} exceeded')
    if query_count>=512: raise TraceError('original title input query bound 512 exceeded')
    raise TraceError('timed out before the original title callback opened Audio Settings')

def state2_capture(rsp:Rsp,trace:dict,active:set[int],timeout_s:float)->dict:
    # Wait for the original Calc callback to be initialized in State 1; read-only state checks.
    setbp(rsp,CALC); active.add(CALC); deadline=time.monotonic()+timeout_s; attempts=0
    while time.monotonic()<deadline and attempts<80:
        continue_until_deadline(rsp,deadline,'Calc initialization'); pc=stop_pc(rsp)
        if pc!=CALC: raise TraceError(f'Calc entry wait stopped at {pc:#x}')
        work,state=title_config(rsp)
        if work and state==1: break
        lr=reg(rsp,14)&~1; clearbp(rsp,CALC); active.discard(CALC); setbp(rsp,lr); active.add(lr)
        continue_until_deadline(rsp,deadline,'Calc initialization'); clearbp(rsp,lr); active.discard(lr); setbp(rsp,CALC); active.add(CALC); attempts+=1
    else: raise TraceError('TitleConfig Calc State 1 not reached within bound')
    trace['calc_state1']={'work':hex(work),'state':state,'attempts':attempts}
    # The first State-1 entry was reached with this breakpoint still armed.
    # Remove it before continuing the callback or the observer will stop at
    # CALC again instead of seeing its logical query/return sequence.
    if CALC in active: clearbp(rsp,CALC); active.discard(CALC)
    # One original Calc call with controlled A query (0,1); no work/state/config writes.
    caller_lr=reg(rsp,14)&~1; query_events=[]; raw_input_events=[]
    for a in (TRIGGER,TRIGGER2,LOGICAL,caller_lr): setbp(rsp,a); active.add(a)
    injected=False; query_count=0
    while query_count<128:
        continue_until_deadline(rsp,deadline,'State-2 capture'); pc=stop_pc(rsp)
        if pc==caller_lr: break
        if pc in (TRIGGER,TRIGGER2):
            a0,a1=reg(rsp,0),reg(rsp,1); lr=reg(rsp,14)&~1
            clearbp(rsp,pc); active.discard(pc)
            orig=mem(rsp,pc,8); write_mem(rsp,pc,return_stub(0),{TRIGGER,TRIGGER2,LOGICAL})
            return_added=lr not in active
            if return_added: setbp(rsp,lr); active.add(lr)
            try:
                continue_until_deadline(rsp,deadline,'State-2 capture')
                if stop_pc(rsp)!=lr: raise TraceError(f'raw input query missed return PC {lr:#x}')
                rv=reg(rsp,0)
            finally:
                write_mem(rsp,pc,orig,{TRIGGER,TRIGGER2,LOGICAL})
                if return_added: clearbp(rsp,lr); active.discard(lr)
            raw_input_events.append({'address':hex(pc),'args':[a0,a1],'return':rv,'return_pc':hex(lr),'requested_response':0})
            query_count+=1; setbp(rsp,pc); active.add(pc)
            continue
        if pc!=LOGICAL: raise TraceError(f'Calc query stopped at unexpected PC {pc:#x}')
        a0,a1=reg(rsp,0),reg(rsp,1); lr=reg(rsp,14)&~1
        clearbp(rsp,LOGICAL); active.discard(LOGICAL)
        orig=mem(rsp,LOGICAL,20)
        wanted=1 if (a0==0 and a1==1 and not injected) else 0
        stub=return_stub(wanted)
        write_mem(rsp,LOGICAL,stub,{TRIGGER,TRIGGER2,LOGICAL})
        return_added = lr not in active
        if return_added: setbp(rsp,lr); active.add(lr)
        try:
            continue_until_deadline(rsp,deadline,'State-2 capture')
            if stop_pc(rsp)!=lr: raise TraceError('logical query missed return PC')
            rv=reg(rsp,0)
        finally:
            write_mem(rsp,LOGICAL,orig,{TRIGGER,TRIGGER2,LOGICAL})
            if return_added: clearbp(rsp,lr); active.discard(lr)
        injected |= (a0==0 and a1==1 and rv==1)
        query_events.append({'args':[a0,a1],'return':rv,'return_pc':hex(lr)})
        query_count+=1; setbp(rsp,LOGICAL); active.add(LOGICAL)
    for a in (TRIGGER,TRIGGER2,LOGICAL,caller_lr):
        if a in active: clearbp(rsp,a); active.discard(a)
    work,state=title_config(rsp)
    trace['calc_raw_input_queries']=raw_input_events
    trace['calc_a_confirm']={'query_events':query_events,'injected':injected,'state_after_callback':state,'work':hex(work),'callback_return_pc':hex(caller_lr)}
    if not injected or state!=2: raise TraceError(f'original Calc did not enter State 2 after logical A (injected={injected}, state={state})')
    # Capture real dispatcher handlers, Calc branch, Secondary, and readiness. All reads are RSP m/p only.
    watch=(CALC,SECONDARY,READY_HELPER_CALL,READY_OUTER_CALL)
    for a in watch: setbp(rsp,a); active.add(a)
    deadline=time.monotonic()+timeout_s; handler_seq=0; readiness=0; stop_reason='timeout'; calc_returns=set(); helper_pending=False; outer_ready_pending=False; secondary_pending=False
    while time.monotonic()<deadline:
        continue_until_deadline(rsp,deadline,'State-2 capture'); pc=stop_pc(rsp)
        work,state=title_config(rsp)
        if pc in calc_returns:
            clearbp(rsp,pc); active.discard(pc); calc_returns.discard(pc)
            trace.setdefault('calc_returns',[]).append({'pc':hex(pc),'work':hex(work) if work else None,'state':state})
            setbp(rsp,CALC); active.add(CALC)
            continue
        if pc==CALC:
            trace['calc_entries'].append({'pc':hex(pc),'work':hex(work) if work else None,'state':state})
            if work is None or state!=2:
                stop_reason='calc_state_transition'; break
            clearbp(rsp,CALC); active.discard(CALC)
            lr=reg(rsp,14)&~1
            calc_returns.add(lr); setbp(rsp,lr); active.add(lr)
            for a in (DISPATCH_CALL,CALC_STATE2_DISPATCH_RETURN,CALC_FOLLOWUP_RETURN):
                if a not in active: setbp(rsp,a); active.add(a)
            continue
        elif pc==DISPATCH_CALL:
            task=reg(rsp,0); r1=reg(rsp,1); f=task_fields(rsp,task); f.update({'pc':hex(pc),'r1_handler_target':hex(r1),'calc_state':state})
            handler_seq+=1; f['sequence']=handler_seq; trace['handler_entries'].append(f)
            target=r1&~1; tlen=2 if r1&1 else 4
            clearbp(rsp,DISPATCH_CALL); active.discard(DISPATCH_CALL)
            setbp(rsp,target,tlen); active.add(target)
            continue_until_deadline(rsp,deadline,'State-2 capture')
            if stop_pc(rsp)!=target: raise TraceError(f'handler target expected {target:#x}, got {stop_pc(rsp):#x}')
            entry={'pc':hex(stop_pc(rsp)),'lr':hex(reg(rsp,14)&~1),'r0_r3':[reg(rsp,i) for i in range(4)],'task_snapshot':dict(f)}
            trace['handler_entries'][-1]['actual_entry']=entry
            setbp(rsp,DISPATCH_RETURN); active.add(DISPATCH_RETURN)
            nested_event=None
            if target==NESTED_WRAPPER:
                setbp(rsp,NESTED_CALLBACK_CALL); active.add(NESTED_CALLBACK_CALL)
            clearbp(rsp,target,tlen); active.discard(target)
            continue_until_deadline(rsp,deadline,'State-2 capture')
            if target==NESTED_WRAPPER:
                if stop_pc(rsp)!=NESTED_CALLBACK_CALL: raise TraceError(f'nested wrapper missed BLX site: {stop_pc(rsp):#x}')
                actual_nested_target=reg(rsp,0)
                if f.get('nested_handler_target_raw') is not None and int(f['nested_handler_target_raw'],16)!=actual_nested_target:
                    raise TraceError(f'nested callback target mismatch: method table={f["nested_handler_target_raw"]}, BLX r0={actual_nested_target:#x}')
                nested_event={'phase':'call','sequence':nested_callback_return_count(trace)+1,'wrapper_handler_sequence':handler_seq,'task':hex(reg(rsp,4)),'instruction_index':reg(rsp,5),'nested_id':f.get('nested_handler_id'),'nested_target_from_table':f.get('nested_handler_target_raw'),'nested_target_at_blx':hex(actual_nested_target),'blx_pc':hex(NESTED_CALLBACK_CALL),'r4_task':hex(reg(rsp,4)),'r5_instruction_index':reg(rsp,5),'r6_entry':hex(reg(rsp,6))}
                trace.setdefault('nested_callbacks',[]).append(nested_event)
                clearbp(rsp,NESTED_CALLBACK_CALL); active.discard(NESTED_CALLBACK_CALL)
                setbp(rsp,NESTED_CALLBACK_RETURN); active.add(NESTED_CALLBACK_RETURN)
                continue_until_deadline(rsp,deadline,'State-2 capture')
                if stop_pc(rsp)!=NESTED_CALLBACK_RETURN: raise TraceError(f'nested callback missed return site: {stop_pc(rsp):#x}')
                nested_event.update({'phase':'return','return_pc':hex(NESTED_CALLBACK_RETURN),'callback_return_r0':reg(rsp,0),'task_after_callback':task_fields(rsp,reg(rsp,4))})
                clearbp(rsp,NESTED_CALLBACK_RETURN); active.discard(NESTED_CALLBACK_RETURN)
                continue_until_deadline(rsp,deadline,'State-2 capture')
            if stop_pc(rsp)!=DISPATCH_RETURN: raise TraceError('handler did not return to script dispatcher')
            rv=reg(rsp,0); f2=task_fields(rsp,task); f2.update({'sequence':handler_seq,'handler_return':rv,'calc_state':title_config(rsp)[1]})
            trace['handler_returns'].append(f2)
            clearbp(rsp,DISPATCH_RETURN); active.discard(DISPATCH_RETURN)
            setbp(rsp,DISPATCH_CALL); active.add(DISPATCH_CALL)
            if nested_callback_return_cap_reached(trace): stop_reason='nested_callback_return_cap'; break
            if handler_seq>=128: stop_reason='handler_return_cap'; break
            continue
        if pc==CALC_STATE2_DISPATCH_RETURN:
            trace['calc_dispatch_results'].append({'pc':hex(pc),'r0':reg(rsp,0),'state':state,'work':hex(work) if work else None})
            clearbp(rsp,pc); active.discard(pc)
            if state!=2: stop_reason='calc_state_transition'; break
        elif pc==CALC_FOLLOWUP_RETURN:
            trace['calc_followup_results'].append({'pc':hex(pc),'r0':reg(rsp,0),'state':state,'work':hex(work) if work else None})
            clearbp(rsp,pc); active.discard(pc)
        elif pc==SECONDARY:
            trace['secondary'].append({'phase':'entry','pc':hex(pc),'lr':hex(reg(rsp,14)&~1),'work':hex(work) if work else None,'state':state})
            clearbp(rsp,SECONDARY); active.discard(SECONDARY); setbp(rsp,SECONDARY_EXIT); active.add(SECONDARY_EXIT); secondary_pending=True
        elif pc==SECONDARY_EXIT:
            trace['secondary'].append({'phase':'exit','pc':hex(pc),'lr':hex(reg(rsp,14)&~1),'work':hex(work) if work else None,'state':state})
            clearbp(rsp,SECONDARY_EXIT); active.discard(SECONDARY_EXIT); secondary_pending=False; setbp(rsp,SECONDARY); active.add(SECONDARY)
        elif pc==READY_HELPER_CALL:
            trace['readiness'].append({'phase':'task_activity_call','task':hex(reg(rsp,0)),'work':hex(work) if work else None,'state':state})
            clearbp(rsp,READY_HELPER_CALL); active.discard(READY_HELPER_CALL); setbp(rsp,READY_HELPER_RETURN); active.add(READY_HELPER_RETURN); helper_pending=True
        elif pc==READY_HELPER_RETURN:
            if trace['readiness'] and trace['readiness'][-1].get('phase')=='task_activity_call': trace['readiness'][-1]['task_activity_return']=reg(rsp,0)
            clearbp(rsp,READY_HELPER_RETURN); active.discard(READY_HELPER_RETURN); helper_pending=False; setbp(rsp,READY_HELPER_CALL); active.add(READY_HELPER_CALL)
        elif pc==READY_OUTER_CALL:
            clearbp(rsp,READY_OUTER_CALL); active.discard(READY_OUTER_CALL); setbp(rsp,READY_OUTER_RETURN); active.add(READY_OUTER_RETURN); outer_ready_pending=True
        elif pc==READY_OUTER_RETURN:
            readiness+=1; trace['readiness'].append({'phase':'outer_ready_return','result':reg(rsp,0),'work':hex(work) if work else None,'state':state,'index':readiness})
            clearbp(rsp,READY_OUTER_RETURN); active.discard(READY_OUTER_RETURN); outer_ready_pending=False; setbp(rsp,READY_OUTER_CALL); active.add(READY_OUTER_CALL)
            if not work or state!=2: stop_reason='work_cleared_or_state_transition'; break
            if readiness>=40: stop_reason='readiness_check_cap'; break
        if len(trace['handler_returns'])>=128: stop_reason='handler_return_cap'; break
    trace['stop_reason']=stop_reason
    return {'stop_reason':stop_reason,'handler_returns':len(trace['handler_returns']),'nested_callback_returns':nested_callback_return_count(trace),'readiness_checks':readiness}

def main(argv=None)->int:
    global TASK
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--task-json',type=Path,default=TASK)
    ap.add_argument('--run-dir',type=Path)
    ap.add_argument('--output',type=Path)
    ap.add_argument('--port',type=int,default=0)
    ap.add_argument('--startup-timeout',type=float,default=90)
    ap.add_argument('--packet-timeout',type=float,default=30)
    ap.add_argument('--capture-timeout',type=float,default=180)
    ap.add_argument('--observe-startup-lock-path',action='store_true',help='arm bounded SVC/atomic-lock diagnostics before entering TitleMain; adds debugger stops to the startup route')
    ap.add_argument('--observe-startup-command-progress',action='store_true',help='arm native-command progress/return breakpoints before TitleMain; adds debugger stops to the startup route')
    args=ap.parse_args(argv)
    TASK=args.task_json.resolve(strict=True)
    packet_root=TASK.parent.resolve()
    task_id=json.loads(TASK.read_text())['task']['id']
    stage_name=STAGE_DIRS.get(task_id)
    if stage_name is None:
        print(f'ERROR: unsupported task id for isolated runtime staging: {task_id}',file=sys.stderr); return 2
    packet_base=ROOT/'build/agent-work/H2-semantic'/task_id
    stage_base=ROOT/'build/h2-runtime'/stage_name
    run_dir=(args.run_dir or stage_base/packet_root.name).resolve()
    output=(args.output or packet_root/'runtime-report.json').resolve()
    if not packet_root.is_relative_to(packet_base.resolve()) or not output.is_relative_to(packet_root) or not run_dir.is_relative_to(stage_base.resolve()):
        print('ERROR: report output must remain under the packet and runtime staging under the short disposable stage root',file=sys.stderr); return 2
    runner_path=Path(__file__).resolve(); runner_sha_before=file_hash(runner_path)
    report={'schema_version':1,'task_id':task_id,'mode':'original_only','status':'not_started','launch_count':0,'limitations':[],'task_packet':str(TASK),'task_packet_sha256':file_hash(TASK),'runner_path':str(runner_path),'runner_sha256_before':runner_sha_before,'invocation_argv':sys.argv[:],'observer_options':{'startup_lock_path':args.observe_startup_lock_path,'startup_command_progress':args.observe_startup_command_progress},'stage_root':str(run_dir)}
    proc=None; sock=None; rsp=None; active=set(); user=None; proc_out=None; proc_err=None
    try:
        gates=verify_offline_gates(); report['offline_gates']=gates
        if not output.parent.exists(): raise TraceError('output root does not exist')
        if output.exists() or run_dir.exists(): raise TraceError('output/run path already exists; refusing overwrite')
        if not AZAHAR.is_file() or sha256(AZAHAR)!=json.loads(TASK.read_text())['input_sha256'][str(AZAHAR.relative_to(ROOT)).replace('\\','/')]: raise TraceError('private Azahar binary pin mismatch')
        package_pin=json.loads(RUNTIME_PACKAGE_PIN.read_text())
        if file_hash(RUNTIME_PACKAGE_PIN)!=json.loads(TASK.read_text())['input_sha256']['docs/agent-work/h2-azahar-runtime-package-pin.json']: raise TraceError('Azahar runtime dependency pin document changed')
        report['runtime_package_pin_sha256']=file_hash(RUNTIME_PACKAGE_PIN)
        man=json.loads(MANIFEST.read_text()); gdb=next(x for x in man['feature_inputs'] if x['path'].replace('\\','/')=='src/core/gdbstub/gdbstub.cpp')
        gdbsrc=AZROOT/'src/core/gdbstub/gdbstub.cpp'
        if file_hash(gdbsrc)!=gdb['sha256']: raise TraceError('pinned GDB source hash mismatch')
        gdbtext=gdbsrc.read_text(errors='replace')
        if 'htonl(INADDR_LOOPBACK)' not in gdbtext or 'htonl(INADDR_ANY)' in gdbtext: raise TraceError('pinned GDB source is not strictly loopback-bound')
        game_hash=gates['source_assets']['cci_sha256_before']; save_hash=gates['source_assets']['supplied_save_sha256_before']
        fixture_hash=file_hash(SAVE_FIXTURE)
        if fixture_hash!=EXPECTED_SAVE_SHA256: raise TraceError('disposable save fixture source hash mismatch')
        if fixture_hash!=json.loads(TASK.read_text())['input_sha256']['build/h3-fixture/source/sdds4game1.sav']: raise TraceError('disposable save fixture packet pin mismatch')
        report['input_artifacts']={'game_path':str(GAME),'game_sha256_before':game_hash,'expected_game_sha256':EXPECTED_CCI_SHA256,'supplied_save_path':str(SUPPLIED_SAVE),'supplied_save_sha256_before':save_hash,'expected_supplied_save_sha256':EXPECTED_SAVE_SHA256,'supplied_save_staged_or_loaded':False,'disposable_save_fixture_path':str(SAVE_FIXTURE),'disposable_save_fixture_sha256_before':fixture_hash,'disposable_save_fixture_sha256_after':None,'disposable_save_fixture_staged_or_loaded':False,'code_sha256':file_hash(CODE),'azahar_sha256':file_hash(AZAHAR),'gdbstub_source_sha256':file_hash(gdbsrc)}
        if file_hash(CODE)!=json.loads(TASK.read_text())['input_sha256']['extracted/exefs/code.bin']: raise TraceError('original code image hash mismatch')
        seed_hashes={p.as_posix():file_hash(SEED/p) for p in PROFILE_SEED_FILES}; report['profile_seed_hashes_before']=seed_hashes
        port=args.port
        if not port:
            for _ in range(100):
                candidate=random.randrange(40000,60000)
                try: reserve_port(candidate); port=candidate; break
                except ProbeError: continue
        if not port: raise TraceError('could not reserve an unused loopback port')
        reserve_port(port); report['port']=port
        app_exe,user,seed_records,runtime_assets,config_records,fixture_record=stage_app(run_dir,SEED,package_pin,SAVE_FIXTURE); report['staged_executable']=str(app_exe); report['staged_executable_sha256']=file_hash(app_exe); report['profile_seed_records']=seed_records; report['runtime_dependency_assets']=runtime_assets; report['runtime_dependency_asset_count']=len(runtime_assets); report['staged_profile_config_records']=config_records; report['disposable_save_fixture']=fixture_record
        report['input_artifacts']['disposable_save_fixture_staged_or_loaded']=True
        report['staged_profile_before_launch']=[{'path':x.relative_to(user).as_posix(),'sha256':file_hash(x),'bytes':x.stat().st_size} for x in user.rglob('*') if x.is_file()]
        run_dir.mkdir(exist_ok=True)
        proc_out=(run_dir/'azahar.stdout.log').open('wb'); proc_err=(run_dir/'azahar.stderr.log').open('wb')
        launch_command=[str(app_exe),'-g',str(port),str(GAME)]; report['launch_command']=launch_command
        proc=subprocess.Popen(launch_command,cwd=str(app_exe.parent),stdin=subprocess.DEVNULL,stdout=proc_out,stderr=proc_err,shell=False)
        report['launch_count']=1; report['host_pid']=proc.pid; report['status']='launched'
        sock,rsp,pid,listener_pid=attach(proc,port,args.packet_timeout); report['emulated_pid']=pid
        report['listener_verified']={'address':'127.0.0.1','port':port,'owner_pid':listener_pid,'child_pid':proc.pid,'gdbstub_source_sha256':file_hash(gdbsrc)}
        trace={'handler_entries':[],'handler_returns':[],'nested_callbacks':[],'calc_entries':[],'calc_dispatch_results':[],'calc_followup_results':[],'secondary':[],'readiness':[],'navigation_queries':[],'logical_queries':[]}
        report['trace']=trace
        # Reach Audio Settings through the original State-5 callback and reversible logical query stubs.
        path=logical_stub_scenario(rsp,trace['navigation_queries'],active,args.startup_timeout,args.observe_startup_lock_path,args.observe_startup_command_progress); report['navigation']=path
        # Wait for Calc state 1 with read-only entry/return observations.
        report['capture']=state2_capture(rsp,trace,active,args.capture_timeout); report['trace']=trace; report['status']='captured_partial'
    except Exception as e:
        report['error']=f'{type(e).__name__}: {e}'; report['trace']=report.get('trace',{})
        if isinstance(e,TraceDeadlineError):
            report['timeout_interrupt']={'stop_reply':e.interrupt_stop_reply.decode('ascii','replace') if e.interrupt_stop_reply else None,'interrupt_error':e.interrupt_error}
            if e.interrupt_stop_reply is not None and rsp is not None:
                try: report['timeout_guest_state']=timeout_guest_snapshot(rsp,e.interrupt_stop_reply)
                except Exception as snapshot_error: report['timeout_guest_state_error']=f'{type(snapshot_error).__name__}: {snapshot_error}'
        if report['status']=='not_started': report['status']='blocked_before_launch'
        elif report['status']=='launched': report['status']='partial_failed'
    finally:
        if proc is not None and proc.poll() is None:
            # Remove breakpoints where the RSP session is responsive, then terminate only this child.
            if rsp is not None:
                for a in list(active):
                    try: clearbp(rsp,a); active.discard(a)
                    except Exception: pass
            try: proc.terminate(); proc.wait(timeout=10); report['shutdown']='terminated_by_supervisor'
            except subprocess.TimeoutExpired:
                proc.kill(); proc.wait(timeout=5); report['shutdown']='killed_by_supervisor_after_timeout'
        elif proc is not None: report['shutdown']={'process_exit_code':proc.returncode,'clean_close_observed':False,'note':'process exited before supervisor termination; no graceful-close observation was collected'}
        if sock is not None:
            try: sock.close()
            except OSError: pass
        for f in (proc_out,proc_err):
            if f:
                try: f.close()
                except Exception: pass
        if user is not None and user.exists():
            # Delete only the task's disposable staged profile, never the source seed or any installed profile.
            try: report['staged_user_before_cleanup']=[{'path':x.relative_to(user).as_posix(),'sha256':file_hash(x),'bytes':x.stat().st_size} for x in user.rglob('*') if x.is_file()]
            except Exception as e: report['staged_user_snapshot_error']=str(e)
            try:
                log=user/'log/azahar_log.txt'
                if log.is_file():
                    log_copy=run_dir/'azahar-user.log'
                    shutil.copy2(log,log_copy)
                    report['preserved_user_log']={'path':str(log_copy),'sha256':file_hash(log_copy),'bytes':log_copy.stat().st_size}
            except Exception as e: report['preserved_user_log_error']=str(e)
            shutil.rmtree(user); report['staged_profile_removed']=True
        try:
            report['input_artifacts']['game_sha256_after']=file_hash(GAME)
            report['input_artifacts']['game_unchanged']=report['input_artifacts']['game_sha256_before']==report['input_artifacts']['game_sha256_after']==EXPECTED_CCI_SHA256
            report['input_artifacts']['supplied_save_sha256_after']=file_hash(SUPPLIED_SAVE)
            report['input_artifacts']['supplied_save_unchanged']=report['input_artifacts']['supplied_save_sha256_before']==report['input_artifacts']['supplied_save_sha256_after']==EXPECTED_SAVE_SHA256
            report['input_artifacts']['disposable_save_fixture_sha256_after']=file_hash(SAVE_FIXTURE)
            report['input_artifacts']['disposable_save_fixture_unchanged']=report['input_artifacts']['disposable_save_fixture_sha256_before']==report['input_artifacts']['disposable_save_fixture_sha256_after']==EXPECTED_SAVE_SHA256
        except Exception as e: report['input_artifacts_after_error']=str(e)
        try:
            report['runner_sha256_after']=file_hash(runner_path)
            report['runner_unchanged_during_run']=report['runner_sha256_before']==report['runner_sha256_after']
        except Exception as e: report['runner_hash_after_error']=str(e)
        try: report['profile_seed_hashes_after']={p.as_posix():file_hash(SEED/p) for p in PROFILE_SEED_FILES}; report['profile_seed_unchanged']=report['profile_seed_hashes_before']==report['profile_seed_hashes_after']
        except Exception: pass
        report['active_breakpoints_after_cleanup']=sorted(hex(x) for x in active)
        if output.parent.exists(): output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    return 0 if report['status']=='captured_partial' else 2
if __name__=='__main__': raise SystemExit(main())
