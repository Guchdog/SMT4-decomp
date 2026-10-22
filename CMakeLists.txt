cmake_minimum_required(VERSION 3.20)
option(SMT4_ARMV6K "Build the supported freestanding Nintendo 3DS ARMv6K target" ON)
if(SMT4_ARMV6K)
    # Establish cross-compilation before compiler feature/link checks.
    set(CMAKE_SYSTEM_NAME Generic)
    set(CMAKE_SYSTEM_PROCESSOR arm)
    set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)
    set(CMAKE_CXX_COMPILER_TARGET armv6k-none-eabihf)
endif()
project(smt4_decomp LANGUAGES CXX)

if(NOT SMT4_ARMV6K)
    message(FATAL_ERROR "Only the ARMv6K/3DS build is supported. Configure with -DSMT4_ARMV6K=ON and Clang; host ports are future work.")
endif()
if(NOT CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    message(FATAL_ERROR "The ARMv6K build requires Clang. Set CMAKE_CXX_COMPILER to clang++.")
endif()

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

execute_process(COMMAND "${CMAKE_CXX_COMPILER}" -print-resource-dir
    OUTPUT_VARIABLE SMT4_CLANG_RESOURCE_DIR OUTPUT_STRIP_TRAILING_WHITESPACE
    RESULT_VARIABLE SMT4_RESOURCE_RESULT)
if(NOT SMT4_RESOURCE_RESULT EQUAL 0 OR NOT EXISTS "${SMT4_CLANG_RESOURCE_DIR}/include/stddef.h")
    message(FATAL_ERROR "Cannot locate Clang's builtin resource headers.")
endif()

file(GLOB_RECURSE SMT4_SOURCES CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp")
add_library(smt4_decomp STATIC ${SMT4_SOURCES})
target_include_directories(smt4_decomp SYSTEM PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}/include/freestanding")
target_include_directories(smt4_decomp PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/include")
target_compile_options(smt4_decomp PRIVATE
        # CMake otherwise strips this as an implicit include, despite -nostdinc.
        "SHELL:-isystem \"${SMT4_CLANG_RESOURCE_DIR}/include\""
        --target=armv6k-none-eabihf
        -mcpu=mpcore
        -mfpu=vfpv2
        -mfloat-abi=hard
        -O2
        -fno-exceptions
        -fno-rtti
        -ffreestanding
        -nostdinc
        -nostdinc++
)
