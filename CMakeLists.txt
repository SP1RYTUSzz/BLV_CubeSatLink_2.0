cmake_minimum_required(VERSION 3.13)
include(pico_sdk_import.cmake)
project(blv C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
pico_sdk_init()
add_executable(blv
blv.c
)
target_link_libraries(blv pico_stdlib hardware_spi hardware_uart)
pico_add_extra_outputs(blv)
