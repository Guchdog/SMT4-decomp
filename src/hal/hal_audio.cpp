#include "hal/hal_audio.h"

namespace smt4::hal {

static bool s_audio_init = false;
static AudioConfig s_config{};
static f32 s_volume = 1.0f;

bool Audio_Init(const AudioConfig& config) {
    s_config = config;
    s_audio_init = true;
    s_volume = 1.0f;
    return true;
}

void Audio_Shutdown() {
    s_audio_init = false;
}

bool Audio_QueueBuffer(const void* pcm_data, u32 byte_count) {
    if (!s_audio_init || !pcm_data || byte_count == 0) return false;
    return true;
}

void Audio_SetMasterVolume(f32 volume) {
    if (volume < 0.0f) volume = 0.0f;
    if (volume > 1.0f) volume = 1.0f;
    s_volume = volume;
}

f32 Audio_GetMasterVolume() {
    return s_volume;
}

} // namespace smt4::hal
