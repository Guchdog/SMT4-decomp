# Configure with: cmake -S . -B build/cmake-armv6k -G Ninja
#   -DCMAKE_TOOLCHAIN_FILE=cmake/armv6k-clang.cmake
# Set CLANG_PATH or -DCMAKE_CXX_COMPILER if clang++ is not on PATH.
set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR arm)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)
set(CMAKE_CXX_COMPILER_TARGET armv6k-none-eabihf)
set(SMT4_ARMV6K ON CACHE BOOL "Build freestanding 3DS ARMv6K" FORCE)
if(NOT CMAKE_CXX_COMPILER AND DEFINED ENV{CLANG_PATH})
    set(CMAKE_CXX_COMPILER "$ENV{CLANG_PATH}" CACHE FILEPATH "Clang C++ compiler")
endif()
