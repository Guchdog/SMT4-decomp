#pragma once
#include "hal_types.h"

namespace smt4::hal {

struct AudioConfig {
    u32 sample_rate;
    u8  channel_count;
    u16 buffer_size_frames;
};

bool Audio_Init(const AudioConfig& config);
void Audio_Shutdown();

bool Audio_QueueBuffer(const void* pcm_data, u32 byte_count);
void Audio_SetMasterVolume(f32 volume);
f32  Audio_GetMasterVolume();

u32 Audio_ProcessOutput(void* out_buffer, u32 requested_frames);
u32 Audio_GetQueuedFrameCount();
u64 Audio_GetTotalBytesProcessed();

} // namespace smt4::hal
