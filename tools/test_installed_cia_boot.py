import subprocess, socket, time, shutil, sys, os
from pathlib import Path

ROOT = Path(r"C:\Users\altair\.codex\worktrees\semantic-equivalence-experiment\SMT4decomp")
AZAHAR_EXE = Path(r"E:\SMT4decomp\build\h0-h3-closure-20261028\h2-rsp-corrected-run001\original\app\azahar.exe")
STAGING_DIR = Path(r"E:\SMT4decomp\build\cia-staging\azahar_installed_test")
SEED_DIR = Path(r"E:\SMT4decomp\build\h0-h3-closure-20261028\h2-rsp-corrected-run001\original\app\user")
NCCH_PATH = Path(r"E:\SMT4decomp\build\cia-staging\patched_ncch0.bin")

sys.path.insert(0, str(ROOT))
from tools.h2_azahar_rsp_probe import Rsp, ProbeError, decode_r0

PORT = 60420
ADDR_TITLE_MAIN_INIT = 0x001EB02C
ADDR_UI_INPUT_TRIGGER2 = 0x002BFFBC

def rsp_read_mem(rsp: Rsp, addr: int, size: int) -> bytes:
    raw = rsp.request(f"m{addr:x},{size:x}".encode("ascii"))
    if raw.startswith(b"E") or len(raw) != size * 2:
        raise ProbeError(f"memory read failed at {addr:#x}+{size:#x}: {raw!r}")
    return bytes.fromhex(raw.decode("ascii"))

def rsp_write_mem(rsp: Rsp, addr: int, data: bytes) -> None:
    hex_payload = data.hex().encode("ascii")
    reply = rsp.request(f"M{addr:x},{len(data):x}:".encode("ascii") + hex_payload)
    if reply != b"OK":
        raise ProbeError(f"memory write failed at {addr:#x}+{len(data):#x}: {reply!r}")

def rsp_set_bp(rsp: Rsp, addr: int, length: int = 4) -> None:
    reply = rsp.request(f"Z0,{addr:x},{length:x}".encode("ascii"))
    if reply != b"OK":
        raise ProbeError(f"failed to set breakpoint at {addr:#x}: {reply!r}")

def rsp_clear_bp(rsp: Rsp, addr: int, length: int = 4) -> None:
    reply = rsp.request(f"z0,{addr:x},{length:x}".encode("ascii"))
    if reply != b"OK":
        raise ProbeError(f"failed to clear breakpoint at {addr:#x}: {reply!r}")

def run_to_bp(rsp: Rsp, addr: int, length: int = 4) -> int:
    rsp_set_bp(rsp, addr, length)
    try:
        reply = rsp.continue_to_stop()
        pc = decode_r0(rsp.request(b"p0f"))
        if pc != addr:
            raise ProbeError(f"expected stop at {addr:#x}, got {pc:#x}")
        return pc
    finally:
        rsp_clear_bp(rsp, addr, length)

def setup_installed_title():
    if STAGING_DIR.exists():
        shutil.rmtree(STAGING_DIR)
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    
    app_dir = AZAHAR_EXE.parent
    for item in app_dir.iterdir():
        if item.name == "user":
            continue
        dest = STAGING_DIR / item.name
        if item.is_file():
            shutil.copy2(item, dest)
        elif item.is_dir():
            shutil.copytree(item, dest)
            
    user_dest = STAGING_DIR / "user"
    shutil.copytree(SEED_DIR, user_dest)
    
    # Place installed title in sdmc
    title_dir = user_dest / "sdmc" / "Nintendo 3DS" / ("0" * 32) / ("0" * 32) / "title" / "00040000" / "000e5c00" / "content"
    title_dir.mkdir(parents=True, exist_ok=True)
    app_target = title_dir / "00000000.app"
    print(f"Creating hardlink/copy of patched NCCH to {app_target}...")
    try:
        os.link(str(NCCH_PATH), str(app_target))
    except Exception:
        shutil.copy2(NCCH_PATH, app_target)
    print("Installed title staged successfully!")
    return app_target

def test_boot(app_path: Path):
    exe = STAGING_DIR / "azahar.exe"
    cmd = [str(exe), "-g", str(PORT), str(app_path)]
    print(f"Launching installed title: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, cwd=str(STAGING_DIR))
    
    rsp = None
    try:
        t0 = time.time()
        connected = False
        while time.time() - t0 < 30:
            if proc.poll() is not None:
                raise RuntimeError(f"Azahar died prematurely with code {proc.returncode}")
            try:
                s = socket.create_connection(("127.0.0.1", PORT), timeout=1.0)
                rsp = Rsp(s, timeout=15.0)
                connected = True
                print("Connected to Azahar GDB stub!")
                break
            except (ConnectionRefusedError, OSError):
                time.sleep(0.5)
                
        if not connected:
            raise RuntimeError("Failed to connect to GDB stub within 30s")
            
        supported = rsp.request(b"qSupported:multiprocess+;swbreak+;hwbreak+;QStartNoAckMode+")
        print(f"qSupported: {supported.decode('ascii', errors='replace')}")
        if rsp.request(b"!") != b"OK":
            raise ProbeError("extended mode rejected")
        proc_info = rsp.request(b"qfProcessInfo")
        print(f"proc_info: {proc_info.decode('ascii', errors='replace')}")
        pid_hex = proc_info.split(b":", 1)[1].split(b";", 1)[0]
        stop = rsp.request(b"vAttach;" + pid_hex)
        print(f"vAttach stop: {stop.decode('ascii', errors='replace')}")

        # Fast-advance past initial "Touch Screen / Press A" StartMenu
        orig_trigger2 = rsp_read_mem(rsp, ADDR_UI_INPUT_TRIGGER2, 8)
        stub_trigger2 = bytes([0x01, 0x00, 0xa0, 0xe3, 0x1e, 0xff, 0x2f, 0xe1])  # mov r0, #1; bx lr
        rsp_write_mem(rsp, ADDR_UI_INPUT_TRIGGER2, stub_trigger2)
        try:
            print("Running to ADDR_TITLE_MAIN_INIT (0x001EB02C)...")
            t_start = time.time()
            pc = run_to_bp(rsp, ADDR_TITLE_MAIN_INIT)
            print(f"SUCCESS: Hit Title Main Init in {time.time() - t_start:.2f}s! Guest PC = {pc:#x}")
            return True
        finally:
            try:
                rsp_write_mem(rsp, ADDR_UI_INPUT_TRIGGER2, orig_trigger2)
            except Exception:
                pass
            
    except Exception as e:
        print(f"Error during test: {e}")
        return False
    finally:
        if rsp:
            try:
                rsp.request(b"D")
            except Exception:
                pass
            try:
                rsp.sock.close()
            except Exception:
                pass
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except Exception:
                proc.kill()

if __name__ == "__main__":
    app_path = setup_installed_title()
    ok = test_boot(app_path)
    print("Installed title boot:", "PASSED" if ok else "FAILED")
    sys.exit(0 if ok else 1)
