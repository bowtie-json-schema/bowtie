cmake_minimum_required(VERSION 3.16)
project(bowtie_blaze LANGUAGES CXX)
include(blaze/vendor/core/cmake/Sourcemeta.cmake)
add_subdirectory(./blaze)
execute_process(
  COMMAND git -C /tmp/blaze rev-parse --short=8 HEAD
  OUTPUT_VARIABLE GIT_COMMIT_HASH
  OUTPUT_STRIP_TRAILING_WHITESPACE)

add_executable(bowtie_blaze bowtie_blaze.cpp)
target_compile_definitions(bowtie_blaze
  PRIVATE BLAZE_VERSION="${GIT_COMMIT_HASH}")

target_link_libraries(bowtie_blaze
  PRIVATE sourcemeta::core::json)
target_link_libraries(bowtie_blaze
  PRIVATE sourcemeta::core::jsonschema)
target_link_libraries(bowtie_blaze
  PRIVATE sourcemeta::blaze::compiler)
target_link_libraries(bowtie_blaze
  PRIVATE sourcemeta::blaze::evaluator)
