# DGNS Conda releases

This branch publishes the patched MFEM/PyMFEM stack as immutable Conda
packages on the public Prefix.dev channel
`philipnickel/philipnickel-dgns`. The supported binary contract is:

- CPython 3.12 and 3.14
- Linux x86-64 and macOS ARM64 (minimum macOS 13)
- parallel `mfem.par` wrapper only
- OpenMPI 5.0.10 and mpi4py 4.1.2 from Conda-forge
- bundled MFEM, HYPRE, METIS, and libCEED

The Conda package is named `pymfem-dgns`; it installs the normal `mfem` Python
module. The package version is `4.9.0.post10`. PyMFEM clones
`philipnickel/mfem` at commit `57b68b1a28c4e7f647b4b6af0ac6b23cb042c543`,
recorded in
`_build_system/build_consts.py`, so a moving branch is never used.

The CPU build supports native tensor-product face partial assembly with up to
16 basis and quadrature points per dimension. This covers polynomial degree 10
with the DGNS dealiased face rule (11 basis points and 16 quadrature points).
CUDA and HIP retain MFEM's previous 10-point face limit and are outside this
package's binary contract.

Run `pixi run build-conda` to reproduce and test a native package locally.
Pushing `dgns-v4.9.0.post10` builds both supported platforms and publishes them
through `.github/workflows/release_binary.yml`. Manual workflow dispatches
perform both builds without publishing.

Before the first tagged run, create the public Prefix.dev channel
`philipnickel-dgns` and add a GitHub trusted publisher for repository
`philipnickel/PyMFEM` and workflow file `release_binary.yml`. The workflow uses
GitHub OIDC and stores no Prefix.dev API token. Publishing uses the fully
qualified channel reference `philipnickel/philipnickel-dgns`; consumers use
the public channel URL `https://prefix.dev/philipnickel/philipnickel-dgns`.

Published packages are immutable. For a change after `post10`, update the
package and Python versions, the exact MFEM commit if needed, the validation
constants in `ci/`, and the expected release tag. Publish `post11` (or later)
instead of overwriting an existing package.
