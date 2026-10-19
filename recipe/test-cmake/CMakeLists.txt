cmake_minimum_required(VERSION 3.20)
project(mfem_dgns_consumer LANGUAGES CXX)

find_package(MFEM 4.10 REQUIRED CONFIG)

add_executable(parmesh_smoke parmesh_smoke.cpp)
target_include_directories(parmesh_smoke PRIVATE ${MFEM_INCLUDE_DIRS})
target_link_libraries(parmesh_smoke PRIVATE ${MFEM_LIBRARIES})
