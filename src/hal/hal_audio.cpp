#include "hal/hal_audio.h"

#if defined(__arm__)

namespace smt4::hal {

static bool s_audio_init = false;
static AudioConfig s_config{};
static f32 s_volume = 1.0f;
static u32 s_queued_frames = 0;
static u64 s_total_bytes = 0;

bool Audio_Init(const AudioConfig& config) {
    s_config = config;
    s_audio_init = true;
    s_volume = 1.0f;
    s_queued_frames = 0;
    s_total_bytes = 0;
    return true;
}

void Audio_Shutdown() {
    s_audio_init = false;
}

bool Audio_QueueBuffer(const void* pcm_data, u32 byte_count) {
    if (!s_audio_init || !pcm_data || byte_count == 0) return false;
    u32 bytes_per_frame = (s_config.channel_count ? s_config.channel_count : 2) * sizeof(s16);
    s_queued_frames += byte_count / bytes_per_frame;
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

u32 Audio_ProcessOutput(void* out_buffer, u32 requested_frames) {
    (void)out_buffer;
    u32 frames = (requested_frames < s_queued_frames) ? requested_frames : s_queued_frames;
    s_queued_frames -= frames;
    u32 bytes = frames * (s_config.channel_count ? s_config.channel_count : 2) * sizeof(s16);
    s_total_bytes += bytes;
    return frames;
}

u32 Audio_GetQueuedFrameCount() {
    return s_queued_frames;
}

u64 Audio_GetTotalBytesProcessed() {
    return s_total_bytes;
}

} // namespace smt4::hal

#else // Native Host (Windows / Linux / macOS)

#include <vector>
#include <cstring>
#include <algorithm>

namespace smt4::hal {

static bool s_audio_init = false;
static AudioConfig s_config{};
static f32 s_volume = 1.0f;
static std::vector<s16> s_sample_queue;
static u64 s_total_bytes_processed = 0;

bool Audio_Init(const AudioConfig& config) {
    s_config = config;
    if (s_config.channel_count == 0) s_config.channel_count = 2;
    if (s_config.sample_rate == 0) s_config.sample_rate = 32728;
    s_audio_init = true;
    s_volume = 1.0f;
    s_sample_queue.clear();
    s_total_bytes_processed = 0;
    return true;
}

void Audio_Shutdown() {
    s_audio_init = false;
    s_sample_queue.clear();
}

bool Audio_QueueBuffer(const void* pcm_data, u32 byte_count) {
    if (!s_audio_init || !pcm_data || byte_count == 0) return false;
    const s16* samples = reinterpret_cast<const s16*>(pcm_data);
    u32 sample_count = byte_count / sizeof(s16);
    s_sample_queue.insert(s_sample_queue.end(), samples, samples + sample_count);
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

u32 Audio_ProcessOutput(void* out_buffer, u32 requested_frames) {
    if (!s_audio_init || !out_buffer || requested_frames == 0) return 0;
    u32 channels = s_config.channel_count ? s_config.channel_count : 2;
    u32 requested_samples = requested_frames * channels;
    s16* out_samples = reinterpret_cast<s16*>(out_buffer);

    u32 available_samples = static_cast<u32>(s_sample_queue.size());
    u32 samples_to_copy = (requested_samples < available_samples) ? requested_samples : available_samples;

    for (u32 i = 0; i < samples_to_copy; ++i) {
        f32 sample_val = static_cast<f32>(s_sample_queue[i]) * s_volume;
        if (sample_val > 32767.0f) sample_val = 32767.0f;
        if (sample_val < -32768.0f) sample_val = -32768.0f;
        out_samples[i] = static_cast<s16>(sample_val);
    }

    // Zero out remaining frames in case of buffer underrun
    if (samples_to_copy < requested_samples) {
        std::memset(out_samples + samples_to_copy, 0, (requested_samples - samples_to_copy) * sizeof(s16));
    }

    s_sample_queue.erase(s_sample_queue.begin(), s_sample_queue.begin() + samples_to_copy);
    u32 frames_processed = samples_to_copy / channels;
    s_total_bytes_processed += samples_to_copy * sizeof(s16);
    return frames_processed;
}

u32 Audio_GetQueuedFrameCount() {
    u32 channels = s_config.channel_count ? s_config.channel_count : 2;
    return static_cast<u32>(s_sample_queue.size()) / channels;
}

u64 Audio_GetTotalBytesProcessed() {
    return s_total_bytes_processed;
}

} // namespace smt4::hal

#endif
