#!/usr/bin/env bash
# Build stock MFEM (plus a static, position-independent GSLIB) into $PREFIX.
# The feature set mirrors the DGNS solver's Spack spec:
#   mfem@4.10.0 +mpi +metis +zlib +lapack +gslib ~mpfr ~threadsafe
#               ~libceed ~openmp cxxstd=17 (hypre, CPU only)
set -euxo pipefail

NCPU="${PYMFEM_BUILD_NCPU:-${CPU_COUNT:-2}}"

# ---- GSLIB 1.0.9 (MPI, static, -fPIC) -------------------------------------
# Installs $PREFIX/lib/libgs.a, $PREFIX/include/gslib/*.h and the
# $PREFIX/include/gslib.h forwarding header.
pushd external/gslib
make clean
make CC="$PREFIX/bin/mpicc" MPI=1 STATIC=1 SHARED=0 CFLAGS="-O2 -fPIC"
make CC="$PREFIX/bin/mpicc" MPI=1 STATIC=1 SHARED=0 CFLAGS="-O2 -fPIC" DESTDIR="$PREFIX" install
popd

# ---- MFEM 4.10 (stock upstream source) -------------------------------------
# Conda-forge's CXXFLAGS carry -O2 and a generic CPU baseline (linux-64:
# -march=nocona, SSE3 only), which come after CMake's Release -O3 in config.mk
# and leave the partial-assembly kernels unvectorized for AVX2/FMA. Append -O3
# and the DGNS CPU baseline so they take precedence: x86-64-v3 (AVX2, FMA;
# Haswell and newer, every DTU hpc node in use) and Apple M1 or newer.
case "${target_platform:-}" in
  linux-64) export CXXFLAGS="${CXXFLAGS:-} -O3 -march=x86-64-v3" ;;
  osx-arm64) export CXXFLAGS="${CXXFLAGS:-} -O3 -mcpu=apple-m1" ;;
  *) export CXXFLAGS="${CXXFLAGS:-} -O3" ;;
esac

cmake -S external/mfem -B build-mfem \
  ${CMAKE_ARGS} \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$PREFIX" \
  -DCMAKE_INSTALL_LIBDIR=lib \
  -DCMAKE_INSTALL_NAME_DIR="@rpath" \
  -DCMAKE_MACOSX_RPATH=ON \
  -DCMAKE_CXX_STANDARD=17 \
  -DBUILD_SHARED_LIBS=ON \
  -DMPI_C_COMPILER="$PREFIX/bin/mpicc" \
  -DMPI_CXX_COMPILER="$PREFIX/bin/mpicxx" \
  -DMFEM_USE_MPI=ON \
  -DMFEM_USE_METIS=ON \
  -DMFEM_USE_METIS_5=ON \
  -DMETIS_DIR="$PREFIX" \
  -DHYPRE_DIR="$PREFIX" \
  -DMFEM_USE_ZLIB=ON \
  -DZLIB_DIR="$PREFIX" \
  -DMFEM_USE_LAPACK=ON \
  -DBLAS_LIBRARIES="$PREFIX/lib/libblas${SHLIB_EXT}" \
  -DLAPACK_LIBRARIES="$PREFIX/lib/liblapack${SHLIB_EXT}" \
  -DMFEM_USE_MPFR=OFF \
  -DMFEM_USE_GSLIB=ON \
  -DGSLIB_DIR="$PREFIX" \
  -DMFEM_THREAD_SAFE=OFF \
  -DMFEM_USE_OPENMP=OFF \
  -DMFEM_USE_CEED=OFF \
  -DMFEM_USE_CUDA=OFF \
  -DMFEM_USE_EXCEPTIONS=OFF \
  -DMFEM_ENABLE_TESTING=OFF \
  -DMFEM_ENABLE_EXAMPLES=OFF \
  -DMFEM_ENABLE_MINIAPPS=OFF

cmake --build build-mfem --parallel "$NCPU"
cmake --install build-mfem

# The build-environment compiler path recorded by MFEMConfig.cmake does not
# exist in a consumer environment; point it at the packaged MPI wrapper.
sed -i.bak -E \
  "s|^set\\(MFEM_CXX_COMPILER \".*\"\\)|set(MFEM_CXX_COMPILER \"$PREFIX/bin/mpicxx\")|" \
  "$PREFIX/lib/cmake/mfem/MFEMConfig.cmake"
rm -f "$PREFIX/lib/cmake/mfem/MFEMConfig.cmake.bak"
