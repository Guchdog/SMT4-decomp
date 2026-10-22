cmake_minimum_required(VERSION 3.20)
project(smt4_decomp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Freestanding 3DS ARMv6K includes and project headers
include_directories(SYSTEM ${CMAKE_CURRENT_SOURCE_DIR}/include/freestanding)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

if(SMT4_ARMV6K)
    add_compile_options(
        --target=armv6k-none-eabihf
        -mcpu=mpcore
        -mfpu=vfpv2
        -mfloat-abi=hard
        -fno-exceptions
        -fno-rtti
        -ffreestanding
        -nostdinc
        -nostdinc++
    )
endif()

file(GLOB_RECURSE SMT4_SOURCES
    "${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp"
)

add_library(smt4_decomp STATIC ${SMT4_SOURCES})
