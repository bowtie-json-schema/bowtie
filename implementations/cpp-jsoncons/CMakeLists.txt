cmake_minimum_required(VERSION 3.16)
project(bowtie_jsoncons LANGUAGES CXX)

set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3")
set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -march=native")
set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -mtune=native")
find_package(jsoncons CONFIG REQUIRED)

add_executable(bowtie_jsoncons bowtie_jsoncons.cpp)
target_link_libraries(bowtie_jsoncons PRIVATE jsoncons)
