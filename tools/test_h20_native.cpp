#include "hal/hal_system.h"
#include "hal/hal_filesystem.h"
#include "hal/hal_graphics.h"
#include "hal/hal_audio.h"
#include "hal/hal_input.h"

#include <iostream>
#include <vector>
#include <cassert>
#include <cmath>
#include <cstring>
#include <filesystem>

using namespace smt4::hal;

static int g_failures = 0;

#define HAL_ASSERT(cond, msg) \
    do { \
        if (!(cond)) { \
            std::cerr << "  [FAIL] Assertion failed: " #cond " (" << (msg) << ") at line " << __LINE__ << std::endl; \
            g_failures++; \
            return; \
        } \
    } while (0)

void TestSystem() {
    std::cout << "[TEST 1/5] HAL System (Lifecycle, Clock & Memory)..." << std::endl;
    bool init_ok = System_Init();
    HAL_ASSERT(init_ok, "System_Init should return true");

    SystemInfo info = System_GetInfo();
    HAL_ASSERT(info.platform == PlatformId::NativeHost, "PlatformId should be NativeHost on host builds");
    HAL_ASSERT(info.memory_total_mb > 0, "Host memory total should be > 0");
    HAL_ASSERT(info.memory_available_mb > 0, "Host memory available should be > 0");
    std::cout << "  Platform: NativeHost | Total RAM: " << info.memory_total_mb << " MB | Avail: " << info.memory_available_mb << " MB" << std::endl;

    u64 t0 = GetTimeNanoseconds();
    SleepMilliseconds(15);
    u64 t1 = GetTimeNanoseconds();
    HAL_ASSERT(t1 >= t0, "Monotonic clock must not go backwards");
    HAL_ASSERT((t1 - t0) >= 10000000ULL, "Elapsed time after 15ms sleep must be >= 10ms");
    std::cout << "  High-res monotonic timer: t0=" << t0 << " ns, t1=" << t1 << " ns (delta=" << (t1 - t0) / 1000000ULL << " ms)" << std::endl;
    std::cout << "  [PASS] HAL System verified." << std::endl;
}

void TestFileSystem() {
    std::cout << "[TEST 2/5] HAL FileSystem (Host Virtual Archive Mount & I/O)..." << std::endl;
    std::string test_dir = "build/h20_native_test_fs";
    std::error_code ec;
    std::filesystem::create_directories(test_dir, ec);

    bool mount_ok = FileSystem_Mount("save", test_dir.c_str());
    HAL_ASSERT(mount_ok, "FileSystem_Mount should succeed");

    // Test writing host file through virtual archive mount
    IFile* f_out = FileSystem_Open("save:/test_slot.sav", true);
    HAL_ASSERT(f_out != nullptr, "Opening write file under save: archive should succeed");

    std::vector<u8> write_buf(1024);
    for (size_t i = 0; i < write_buf.size(); ++i) {
        write_buf[i] = static_cast<u8>((i * 7 + 13) & 0xFF);
    }
    // Set magic header
    write_buf[0] = 'A'; write_buf[1] = 'S'; write_buf[2] = 'D'; write_buf[3] = '1';

    size_t written = f_out->Write(write_buf.data(), write_buf.size());
    HAL_ASSERT(written == write_buf.size(), "All bytes should be written");
    HAL_ASSERT(f_out->GetSize() == 1024, "File size should match written bytes");
    HAL_ASSERT(f_out->Tell() == 1024, "Cursor should be at end of file");

    f_out->Close();
    delete f_out;

    // Test reading back the written host file
    IFile* f_in = FileSystem_Open("save:/test_slot.sav", false);
    HAL_ASSERT(f_in != nullptr, "Opening read-only file should succeed");
    HAL_ASSERT(f_in->GetSize() == 1024, "Read file size should be 1024");

    std::vector<u8> read_buf(1024, 0);
    size_t read_bytes = f_in->Read(read_buf.data(), 1024);
    HAL_ASSERT(read_bytes == 1024, "Read byte count should match 1024");
    HAL_ASSERT(std::memcmp(write_buf.data(), read_buf.data(), 1024) == 0, "Read bytes must match written bytes identically");

    // Test seek operations
    bool seek_ok = f_in->Seek(512, SeekOrigin::Begin);
    HAL_ASSERT(seek_ok, "Seek to 512 from Begin should succeed");
    HAL_ASSERT(f_in->Tell() == 512, "Tell after seek must return 512");

    u8 mid_byte = 0;
    f_in->Read(&mid_byte, 1);
    HAL_ASSERT(mid_byte == write_buf[512], "Byte at offset 512 must match");

    f_in->Close();
    delete f_in;

    // Test memory file stream
    IFile* mem_file = FileSystem_Open(":memory:", true);
    HAL_ASSERT(mem_file != nullptr, "Opening memory file should succeed");
    mem_file->Write("MEMTEST", 7);
    HAL_ASSERT(mem_file->GetSize() == 7, "Memory file size should be 7");
    delete mem_file;

    FileSystem_Unmount("save");
    std::cout << "  Host directory mounted, 1024 bytes written/read/verified, seek & memory streams tested." << std::endl;
    std::cout << "  [PASS] HAL FileSystem verified." << std::endl;
}

void TestGraphics() {
    std::cout << "[TEST 3/5] HAL Graphics (Stereoscopic 3D, Buffers & Presentation)..." << std::endl;
    bool init_ok = Graphics_Init();
    HAL_ASSERT(init_ok, "Graphics_Init should succeed");

    std::vector<u32> top_fb(400 * 240, 0xFF00FF00); // 400x240 Green
    std::vector<u32> bot_fb(320 * 240, 0xFFFF0000); // 320x240 Blue

    FramebufferConfig top_cfg{400, 240, 400 * 4, top_fb.data()};
    FramebufferConfig bot_cfg{320, 240, 320 * 4, bot_fb.data()};

    Graphics_SetFramebuffer(DisplayTarget::TopLeftScreen, top_cfg);
    Graphics_SetFramebuffer(DisplayTarget::BottomScreen, bot_cfg);

    const FramebufferConfig* fetched_top = Graphics_GetFramebuffer(DisplayTarget::TopLeftScreen);
    HAL_ASSERT(fetched_top != nullptr, "Top screen framebuffer config must be retrievable");
    HAL_ASSERT(fetched_top->width == 400 && fetched_top->height == 240, "Top screen dimensions should be 400x240");

    Graphics_Set3DMode(true);
    HAL_ASSERT(Graphics_Is3DMode() == true, "3D stereoscopic mode should be enabled");

    for (int i = 0; i < 5; ++i) {
        Graphics_Present();
    }
    HAL_ASSERT(Graphics_GetPresentCount() == 5, "Graphics present count should advance to 5");

    Graphics_WaitForVBlank();
    std::cout << "  Top/Bottom targets configured, 3D mode toggled, 5 frames presented, VBlank synchronized." << std::endl;
    std::cout << "  [PASS] HAL Graphics verified." << std::endl;
}

void TestAudio() {
    std::cout << "[TEST 4/5] HAL Audio (PCM Streaming & Master Volume Attenuation)..." << std::endl;
    AudioConfig cfg{44100, 2, 512};
    bool init_ok = Audio_Init(cfg);
    HAL_ASSERT(init_ok, "Audio_Init should succeed");

    // Create 1024 frames of 16-bit stereo PCM audio (2048 samples) with amplitude 10000
    const u32 frame_count = 1024;
    std::vector<s16> test_pcm(frame_count * 2, 10000);

    bool queue_ok = Audio_QueueBuffer(test_pcm.data(), static_cast<u32>(test_pcm.size() * sizeof(s16)));
    HAL_ASSERT(queue_ok, "Audio_QueueBuffer should succeed");
    HAL_ASSERT(Audio_GetQueuedFrameCount() == 1024, "Queued frames should be 1024");

    // Set 50% volume attenuation
    Audio_SetMasterVolume(0.5f);
    HAL_ASSERT(std::abs(Audio_GetMasterVolume() - 0.5f) < 0.001f, "Volume should be 0.5");

    std::vector<s16> out_pcm(512 * 2, 0);
    u32 drained = Audio_ProcessOutput(out_pcm.data(), 512);
    HAL_ASSERT(drained == 512, "Should drain exactly 512 frames");
    HAL_ASSERT(Audio_GetQueuedFrameCount() == 512, "512 frames should remain in queue");

    // Verify 50% attenuation applied: 10000 * 0.5 = 5000
    for (size_t i = 0; i < out_pcm.size(); ++i) {
        HAL_ASSERT(std::abs(out_pcm[i] - 5000) <= 1, "Output sample must be attenuated to 5000");
    }

    // Process remaining 512 frames at 100% volume
    Audio_SetMasterVolume(1.0f);
    drained = Audio_ProcessOutput(out_pcm.data(), 512);
    HAL_ASSERT(drained == 512, "Should drain remaining 512 frames");
    HAL_ASSERT(Audio_GetQueuedFrameCount() == 0, "Queue should be empty");
    HAL_ASSERT(std::abs(out_pcm[0] - 10000) <= 1, "Output sample must be 10000 at 100% volume");

    std::cout << "  1024 PCM stereo frames queued, master volume attenuated at 50% and 100%, queue drained cleanly." << std::endl;
    std::cout << "  [PASS] HAL Audio verified." << std::endl;
}

void TestInput() {
    std::cout << "[TEST 5/5] HAL Input (State Polling, Edge Detection & Analog Axes)..." << std::endl;
    bool init_ok = Input_Init();
    HAL_ASSERT(init_ok, "Input_Init should succeed");

    // 1. Initial state: nothing pressed
    Input_Poll();
    InputState st0 = Input_GetState();
    HAL_ASSERT(st0.buttons_held == 0 && st0.buttons_pressed == 0 && st0.buttons_released == 0, "Initial buttons must be 0");

    // 2. Press BtnA and set analog stick to (0.75, -0.5) and touch to (160, 120)
    Input_SetButton(BtnA, true);
    Input_SetCirclePad(0.75f, -0.5f);
    Input_SetTouch(true, 160, 120);

    Input_Poll();
    InputState st1 = Input_GetState();
    HAL_ASSERT(st1.buttons_pressed & BtnA, "BtnA must be in buttons_pressed on initial down edge");
    HAL_ASSERT(st1.buttons_held & BtnA, "BtnA must be in buttons_held");
    HAL_ASSERT(st1.buttons_released == 0, "No buttons should be released");
    HAL_ASSERT(std::abs(st1.circle_pad.x - 0.75f) < 0.001f, "Circle pad X should be 0.75");
    HAL_ASSERT(std::abs(st1.circle_pad.y - (-0.5f)) < 0.001f, "Circle pad Y should be -0.5");
    HAL_ASSERT(st1.touch.touching && st1.touch.x == 160 && st1.touch.y == 120, "Touch coordinates should match 160x120");

    // 3. Keep holding BtnA for next poll: pressed edge should clear, held remains
    Input_Poll();
    InputState st2 = Input_GetState();
    HAL_ASSERT((st2.buttons_pressed & BtnA) == 0, "BtnA must NOT be in buttons_pressed on hold tick");
    HAL_ASSERT(st2.buttons_held & BtnA, "BtnA must still be in buttons_held");

    // 4. Release BtnA
    Input_SetButton(BtnA, false);
    Input_Poll();
    InputState st3 = Input_GetState();
    HAL_ASSERT(st3.buttons_released & BtnA, "BtnA must be in buttons_released on up edge");
    HAL_ASSERT((st3.buttons_held & BtnA) == 0, "BtnA must NOT be in buttons_held after release");

    std::cout << "  Input edge transitions verified (pressed, held, released), Circle Pad & Touch accurate." << std::endl;
    std::cout << "  [PASS] HAL Input verified." << std::endl;
}

int main() {
    std::cout << "==================================================================" << std::endl;
    std::cout << "  SMT4 MILESTONE H20: NATIVE HOST PLATFORM ABSTRACTION TEST SUITE " << std::endl;
    std::cout << "==================================================================" << std::endl;

    TestSystem();
    TestFileSystem();
    TestGraphics();
    TestAudio();
    TestInput();

    std::cout << "==================================================================" << std::endl;
    if (g_failures == 0) {
        std::cout << "  ALL 5 HAL SUBSYSTEMS PASSED FUNCTIONAL HOST VERIFICATION (100% OK)" << std::endl;
        std::cout << "==================================================================" << std::endl;
        return 0;
    } else {
        std::cerr << "  FAILED: " << g_failures << " test assertions failed!" << std::endl;
        std::cout << "==================================================================" << std::endl;
        return 1;
    }
}
