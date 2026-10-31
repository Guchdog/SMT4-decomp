#include "hal/hal_filesystem.h"
#include <cstring>

namespace smt4::hal {

class MemoryFile : public IFile {
private:
    u8* m_buffer;
    size_t m_capacity;
    size_t m_size;
    size_t m_cursor;

public:
    MemoryFile(size_t capacity)
        : m_capacity(capacity), m_size(0), m_cursor(0) {
        m_buffer = new u8[capacity];
    }

    ~MemoryFile() override {
        delete[] m_buffer;
    }

    size_t Read(void* dest, size_t bytes) override {
        if (!dest || m_cursor >= m_size) return 0;
        size_t available = m_size - m_cursor;
        size_t to_read = (bytes < available) ? bytes : available;
        std::memcpy(dest, m_buffer + m_cursor, to_read);
        m_cursor += to_read;
        return to_read;
    }

    size_t Write(const void* src, size_t bytes) override {
        if (!src || m_cursor >= m_capacity) return 0;
        size_t available = m_capacity - m_cursor;
        size_t to_write = (bytes < available) ? bytes : available;
        std::memcpy(m_buffer + m_cursor, src, to_write);
        m_cursor += to_write;
        if (m_cursor > m_size) m_size = m_cursor;
        return to_write;
    }

    bool Seek(s64 offset, SeekOrigin origin) override {
        s64 new_pos = 0;
        switch (origin) {
            case SeekOrigin::Begin:   new_pos = offset; break;
            case SeekOrigin::Current: new_pos = static_cast<s64>(m_cursor) + offset; break;
            case SeekOrigin::End:     new_pos = static_cast<s64>(m_size) + offset; break;
        }
        if (new_pos < 0 || static_cast<size_t>(new_pos) > m_size) return false;
        m_cursor = static_cast<size_t>(new_pos);
        return true;
    }

    u64 Tell() const override { return m_cursor; }
    u64 GetSize() const override { return m_size; }
    void Close() override {}
};

static bool s_fs_mounted = false;

bool FileSystem_Mount(const char* archive_name, const char* host_root) {
    (void)archive_name;
    (void)host_root;
    s_fs_mounted = true;
    return true;
}

bool FileSystem_Unmount(const char* archive_name) {
    (void)archive_name;
    s_fs_mounted = false;
    return true;
}

IFile* FileSystem_Open(const char* virtual_path, bool write_mode) {
    (void)virtual_path;
    (void)write_mode;
    if (!s_fs_mounted) return nullptr;
    return new MemoryFile(65536);
}

} // namespace smt4::hal
