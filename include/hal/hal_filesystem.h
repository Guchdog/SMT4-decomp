#pragma once
#include "hal_types.h"

namespace smt4::hal {

enum class SeekOrigin : u32 {
    Begin   = 0,
    Current = 1,
    End     = 2,
};

class IFile {
public:
    virtual ~IFile() = default;
    virtual size_t Read(void* dest, size_t bytes) = 0;
    virtual size_t Write(const void* src, size_t bytes) = 0;
    virtual bool Seek(s64 offset, SeekOrigin origin) = 0;
    virtual u64 Tell() const = 0;
    virtual u64 GetSize() const = 0;
    virtual void Close() = 0;
};

bool FileSystem_Mount(const char* archive_name, const char* host_root);
bool FileSystem_Unmount(const char* archive_name);
IFile* FileSystem_Open(const char* virtual_path, bool write_mode);

} // namespace smt4::hal
