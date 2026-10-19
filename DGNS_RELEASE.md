# DGNS Conda releases

This branch publishes a stock MFEM 4.10 C++ library and the matching parallel
PyMFEM wrapper as immutable Conda packages on the public Prefix.dev channel
`philipnickel/philipnickel-dgns`. The DGNS C++ solver and PyMFEM link the same
`libmfem`, so one environment carries a single MFEM build.

## Binary contract (`4.10.0.post1`)

- Linux x86-64 and macOS ARM64 (minimum macOS 13)
- CPython 3.14 only
- CPU only: no CUDA/HIP, no OpenMP, no libCEED
- OpenMPI 5.0.10, mpi4py 4.1.2, HYPRE 3.2, METIS 5, MPFR, zlib and
  BLAS/LAPACK from Conda-forge
- stock upstream MFEM, tag `v4.10`
  (commit `d964264cdb9a13e94a201b6c236c7721e0c8765f`) from
  `https://github.com/mfem/mfem.git`, with no source patches

MFEM is configured to match the solver's Spack spec
`mfem@4.10.0 +mpi +metis +zlib +lapack +mpfr +gslib +threadsafe ~libceed
~openmp cxxstd=17` (with HYPRE), built as shared libraries.

## Outputs

One recipe (`recipe/recipe.yaml`) builds two packages from the same MFEM
source tree:

- `mfem-dgns` installs MFEM's headers, shared `libmfem`, a static
  position-independent GSLIB 1.0.9 (`libgs.a`, `include/gslib/`),
  `share/mfem/config.mk`, and `lib/cmake/mfem/MFEMConfig.cmake`. A C++
  project in a Pixi/Conda environment can use `find_package(MFEM)` or read
  `config.mk`. Its package test configures and runs a two-rank `ParMesh`
  consumer (`recipe/test-cmake`).
- `pymfem-dgns` installs the Python module `mfem` with the parallel
  `mfem.par` wrapper only. It is built with PyMFEM's external-MFEM options
  (`mfem-prefix`, `hypre-prefix`, `metis-prefix`, `gslib-prefix`) against
  `mfem-dgns` and pins it exactly.

## Building and publishing

Run `pixi run build-conda` to reproduce and test both packages locally.
Pushing `dgns-v4.10.0.post1` builds both platforms and publishes all four
packages through `.github/workflows/release_binary.yml`. Manual workflow
dispatches build without publishing.

The workflow uses GitHub OIDC as a Prefix.dev trusted publisher for
repository `philipnickel/PyMFEM` and workflow file `release_binary.yml`; no
API token is stored. Consumers use the channel URL
`https://prefix.dev/philipnickel/philipnickel-dgns`.

Published packages are immutable. For any change, bump the version in
`recipe/recipe.yaml`, `mfem/__init__.py`, `pixi.toml`, `ci/validate_install.py`
and the workflow's `RELEASE_VERSION`, then publish `post2` (or later) instead
of overwriting an existing package.
