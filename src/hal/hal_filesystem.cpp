#include "hal/hal_filesystem.h"

#if defined(__arm__)

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

#else // Native Host (Windows / Linux / macOS)

#include <cstdio>
#include <cstring>
#include <string>
#include <unordered_map>
#include <filesystem>

namespace smt4::hal {

class MemoryFile : public IFile {
private:
    u8* m_buffer;
    size_t m_capacity;
    size_t m_size;
    size_t m_cursor;

public:
    explicit MemoryFile(size_t capacity)
        : m_capacity(capacity), m_size(0), m_cursor(0) {
        m_buffer = new u8[capacity]();
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

class HostFile : public IFile {
private:
    std::FILE* m_fp;
    mutable u64 m_cached_size;

public:
    explicit HostFile(std::FILE* fp)
        : m_fp(fp), m_cached_size(0) {
        UpdateSize();
    }

    ~HostFile() override {
        Close();
    }

    void UpdateSize() const {
        if (!m_fp) { m_cached_size = 0; return; }
        long cur = std::ftell(m_fp);
        std::fseek(m_fp, 0, SEEK_END);
        long end = std::ftell(m_fp);
        std::fseek(m_fp, cur, SEEK_SET);
        m_cached_size = (end >= 0) ? static_cast<u64>(end) : 0;
    }

    size_t Read(void* dest, size_t bytes) override {
        if (!m_fp || !dest || bytes == 0) return 0;
        return std::fread(dest, 1, bytes, m_fp);
    }

    size_t Write(const void* src, size_t bytes) override {
        if (!m_fp || !src || bytes == 0) return 0;
        size_t written = std::fwrite(src, 1, bytes, m_fp);
        std::fflush(m_fp);
        UpdateSize();
        return written;
    }

    bool Seek(s64 offset, SeekOrigin origin) override {
        if (!m_fp) return false;
        int std_origin = SEEK_SET;
        switch (origin) {
            case SeekOrigin::Begin:   std_origin = SEEK_SET; break;
            case SeekOrigin::Current: std_origin = SEEK_CUR; break;
            case SeekOrigin::End:     std_origin = SEEK_END; break;
        }
        return (std::fseek(m_fp, static_cast<long>(offset), std_origin) == 0);
    }

    u64 Tell() const override {
        if (!m_fp) return 0;
        long pos = std::ftell(m_fp);
        return (pos >= 0) ? static_cast<u64>(pos) : 0;
    }

    u64 GetSize() const override {
        UpdateSize();
        return m_cached_size;
    }

    void Close() override {
        if (m_fp) {
            std::fclose(m_fp);
            m_fp = nullptr;
        }
    }
};

static std::unordered_map<std::string, std::string> s_mounts;

static std::string NormalizeArchiveName(const char* name) {
    if (!name) return "";
    std::string s(name);
    if (!s.empty() && s.back() == ':') {
        s.pop_back();
    }
    return s;
}

bool FileSystem_Mount(const char* archive_name, const char* host_root) {
    if (!archive_name || !host_root) return false;
    std::string norm = NormalizeArchiveName(archive_name);
    s_mounts[norm] = host_root;
    return true;
}

bool FileSystem_Unmount(const char* archive_name) {
    if (!archive_name) return false;
    std::string norm = NormalizeArchiveName(archive_name);
    auto it = s_mounts.find(norm);
    if (it != s_mounts.end()) {
        s_mounts.erase(it);
        return true;
    }
    return false;
}

IFile* FileSystem_Open(const char* virtual_path, bool write_mode) {
    if (!virtual_path) return nullptr;

    std::string vpath(virtual_path);
    if (vpath == ":memory:" || vpath.rfind(":memory:", 0) == 0) {
        return new MemoryFile(65536);
    }

    std::string resolved_path = vpath;
    size_t colon = vpath.find(':');
    if (colon != std::string::npos && colon > 0) {
        std::string archive = vpath.substr(0, colon);
        std::string subpath = vpath.substr(colon + 1);
        while (!subpath.empty() && (subpath.front() == '/' || subpath.front() == '\\')) {
            subpath.erase(subpath.begin());
        }

        auto it = s_mounts.find(archive);
        if (it != s_mounts.end()) {
            std::filesystem::path root(it->second);
            resolved_path = (root / subpath).string();
        } else {
            return nullptr;
        }
    }

    if (write_mode) {
        std::filesystem::path p(resolved_path);
        if (p.has_parent_path()) {
            std::error_code ec;
            std::filesystem::create_directories(p.parent_path(), ec);
        }
        std::FILE* fp = std::fopen(resolved_path.c_str(), "w+b");
        if (!fp) fp = std::fopen(resolved_path.c_str(), "wb");
        if (!fp) return nullptr;
        return new HostFile(fp);
    } else {
        std::FILE* fp = std::fopen(resolved_path.c_str(), "rb");
        if (!fp) return nullptr;
        return new HostFile(fp);
    }
}

} // namespace smt4::hal

#endif
