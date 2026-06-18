# Bowtie implementations/cpp-iris — builds the IHOP harness against a cloned IRIS
# tree. The harness source lives here (Bowtie repo); only the validator library
# is fetched from GitHub at image build time.
cmake_minimum_required(VERSION 3.20)
project(cpp-iris-bowtie LANGUAGES CXX)

if(NOT EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/iris/CMakeLists.txt")
    message(FATAL_ERROR
        "IRIS source not found at ${CMAKE_CURRENT_SOURCE_DIR}/iris")
endif()

set(IRIS_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(IRIS_BUILD_BENCHMARKS OFF CACHE BOOL "" FORCE)
set(IRIS_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(IRIS_BUILD_SIMDJSON OFF CACHE BOOL "" FORCE)
set(IRIS_BUILD_GATEWAY OFF CACHE BOOL "" FORCE)
set(IRIS_BUILD_DB OFF CACHE BOOL "" FORCE)
set(IRIS_BUILD_BOWTIE OFF CACHE BOOL "" FORCE)
set(IRIS_ENABLE_JIT OFF CACHE BOOL "" FORCE)
set(IRIS_ENABLE_LTO OFF CACHE BOOL "" FORCE)

add_subdirectory(iris iris-build)

add_executable(bowtie_iris bowtie_iris.cpp)
target_link_libraries(bowtie_iris PRIVATE iris)
target_compile_features(bowtie_iris PRIVATE cxx_std_20)
