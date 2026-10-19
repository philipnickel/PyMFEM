#!/usr/bin/env python3
"""Two-rank import, collective and ParMesh smoke test for the parallel package."""

from mpi4py import MPI

import mfem.par as mfem


comm = MPI.COMM_WORLD
assert comm.size == 2, f"expected two MPI ranks, got {comm.size}"
assert comm.allreduce(comm.rank + 1, op=MPI.SUM) == 3

serial = mfem.Mesh.MakeCartesian2D(8, 8, mfem.Element.QUADRILATERAL)
mesh = mfem.ParMesh(comm, serial)
fec = mfem.H1_FECollection(2, mesh.Dimension())
fes = mfem.ParFiniteElementSpace(mesh, fec)
assert mesh.GetGlobalNE() == 64
assert fes.GlobalTrueVSize() == 289
if comm.rank == 0:
    print("two-rank mfem.par smoke test passed")
