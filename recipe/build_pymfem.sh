#!/usr/bin/env bash
# Build the parallel-only PyMFEM wrapper against the mfem-dgns package in $PREFIX.
# external/mfem holds the same stock MFEM source tree; SWIG and the wrapped
# miniapp sources (dist_solver, navier, dpg utilities) are read from it.
set -euxo pipefail

export PYMFEM_BUILD_NCPU="${PYMFEM_BUILD_NCPU:-2}"

# MFEM's error macros embed __FILE__ of its installed headers; strip the host
# prefix so the extension modules stay relocatable.
export CFLAGS="${CFLAGS:-} -fmacro-prefix-map=${PREFIX}/="
export CPPFLAGS="${CPPFLAGS:-} -fmacro-prefix-map=${PREFIX}/="

$PYTHON -m pip install . --no-deps --no-build-isolation -vv \
  -Cwith-parallel=Yes \
  -Cno-serial=Yes \
  -Cmfem-prefix="$PREFIX" \
  -Chypre-prefix="$PREFIX" \
  -Cmetis-prefix="$PREFIX" \
  -Cwith-gslib=Yes \
  -Cgslib-prefix="$PREFIX" \
  -Cmfem-source="$SRC_DIR/external/mfem" \
  -Cmfem-miniapps=No \
  -CMPICC="$PREFIX/bin/mpicc" \
  -CMPICXX="$PREFIX/bin/mpicxx"
