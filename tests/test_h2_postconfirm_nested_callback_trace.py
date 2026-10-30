from __future__ import annotations
import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import h2_postconfirm_nested_callback_trace as probe

class Sock:
    def __init__(self): self.timeout = 30.0
    def gettimeout(self): return self.timeout
    def settimeout(self, value): self.timeout = value

class FakeRsp:
    def __init__(self):
        self.sock, self.pc = Sock(), 0
        self.regs, self.mem, self.active, self.stops = {i:0 for i in range(16)}, {}, set(), []
    def put32(self, a, v):
        for i,b in enumerate(int(v & 0xffffffff).to_bytes(4,"little")): self.mem[a+i] = b
    def queue(self, pc, regs=None): self.stops.append((pc,{int(k):int(v) for k,v in (regs or {}).items()}))
    def continue_to_stop(self):
        if not self.stops: raise AssertionError("unexpected continue")
        self.pc, regs = self.stops.pop(0); self.regs.update(regs); self.regs[15] = self.pc; return b"T05"
    def request(self, p):
        if p.startswith(b"Z0,"): self.active.add(int(p.split(b",")[1],16)); return b"OK"
        if p.startswith(b"z0,"): self.active.discard(int(p.split(b",")[1],16)); return b"OK"
        if p.startswith(b"p"):
            n=int(p[1:],16); return int(self.regs.get(n,self.pc)&0xffffffff).to_bytes(4,"little").hex().encode()
        if p.startswith(b"m"):
            a,n=(int(x,16) for x in p[1:].split(b",")); return bytes(self.mem.get(a+i,0) for i in range(n)).hex().encode()
        raise AssertionError(f"unexpected request {p!r}")

def make_case(timeout=10.0, cap=20):
    r=FakeRsp(); task,method,work,index=0x00120000,0x00130000,0x00140000,12
    r.put32(probe.WORK_GLOBAL,work); r.put32(work+8,2)
    r.put32(task+0xbc,method); r.put32(task+0x18,index)
    r.put32(method+4*index,8|(3<<16)); r.put32(probe.HANDLER_TABLE+8*4,0x001A07CC)
    entry=probe.NESTED_TABLE+3*8; r.put32(entry,0x00221168)
    r.put32(task+0xcc,1); r.put32(task+0xd0,1)
    r.queue(probe.CALL,{0:0x00221168,4:task,5:index,6:entry,14:probe.CALLBACK_RET})
    r.queue(probe.CALLBACK_RET,{0:0})
    r.queue(probe.HANDLER_RET,{0:2,4:task})
    r.queue(probe.WRAPPER_RETURN,{0:2})
    r.queue(probe.READY,{14:0x001EA3CC})
    r.queue(0x001EA3CC,{0:0})
    return r,probe.NestedObserver(r,timeout_s=timeout,max_nested=cap)

class NestedTraceTests(unittest.TestCase):
    def test_captures_dynamic_target_inner_result_and_outer_return(self):
        rsp,obs=make_case(); result=obs.run(max_polls=1); trace=result["nested_callback_observation"]; e=trace["nested_callbacks"][0]
        self.assertEqual((e["outer_handler_id"],e["nested_id"]),(8,3))
        self.assertEqual(e["nested_target_at_blx_raw"],"0x221168")
        self.assertTrue(e["nested_target_matches_table"])
        self.assertEqual((e["callback_return_raw"],e["outer_handler_return_raw"]),(0,2))
        self.assertEqual(e["outer_handler_return_pc"],hex(probe.WRAPPER_RETURN))
        self.assertEqual(trace["observer_guest_writes"],0)
        self.assertTrue(trace["breakpoints_cleared"]); self.assertFalse(rsp.active)
    def test_wrapper_return_is_captured_without_dispatcher_pairing(self):
        rsp,obs=make_case()
        rsp.put32(0x00120000+0x18,11)  # return observer sees a different active script index
        result=obs.run(max_polls=1)
        event=result["nested_callback_observation"]["nested_callbacks"][0]
        self.assertEqual(event["outer_handler_return_raw"],2)
        self.assertEqual(event["outer_handler_return_pc"],hex(probe.WRAPPER_RETURN))
    def test_callback_cap_disarms_nested_callsite(self):
        rsp,obs=make_case(cap=1); obs.run(max_polls=1)
        self.assertNotIn(probe.CALL,rsp.active); self.assertIn("nested_return_cap",obs.caps)
    def test_deadline_cleans_breakpoints(self):
        rsp,obs=make_case(timeout=0.0); result=obs.run(max_polls=1); trace=result["nested_callback_observation"]
        self.assertEqual(trace["stop_reason"],"wall_clock_deadline")
        self.assertTrue(trace["breakpoints_cleared"]); self.assertFalse(rsp.active)
    def test_unexpected_stop_is_recorded_not_swallowed(self):
        rsp,obs=make_case(); rsp.stops=[(0x00123456,{})]
        result=obs.run(max_polls=1); trace=result["nested_callback_observation"]
        self.assertEqual(trace["stop_reason"],"unexpected_stop_or_rsp_error")
        self.assertIn("unexpected guest stop at 0x123456",trace["error"])
        self.assertFalse(rsp.active)
    def test_no_events_differ_from_matching_events(self):
        empty={"original_run":{},"patched_run":{}}
        self.assertEqual(probe.compare_traces(empty)["status"],"no_events_observed")
        rsp,obs=make_case(); event=obs.run(max_polls=1)["nested_callback_observation"]["nested_callbacks"][0]
        paired={"original_run":{"post_confirm_readiness_trace":{"nested_callback_observation":{"nested_callbacks":[event]}}},
                "patched_run":{"post_confirm_readiness_trace":{"nested_callback_observation":{"nested_callbacks":[dict(event)]}}}}
        self.assertEqual(probe.compare_traces(paired)["status"],"matched_observed_events")
        paired["patched_run"]["post_confirm_readiness_trace"]["nested_callback_observation"]["nested_callbacks"][0]["callback_return_raw"]=1
        self.assertEqual(probe.compare_traces(paired)["status"],"diverged_or_incomplete")

if __name__ == "__main__": unittest.main()
