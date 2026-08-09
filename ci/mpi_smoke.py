#!/usr/bin/env python3
"""Two-rank import and collective smoke test for the parallel package."""

from mpi4py import MPI

import mfem.par as mfem


comm = MPI.COMM_WORLD
assert comm.size == 2, f"expected two MPI ranks, got {comm.size}"
assert comm.allreduce(comm.rank + 1, op=MPI.SUM) == 3
assert hasattr(mfem, "VectorNormalJumpIntegrator")
if comm.rank == 0:
    print("two-rank mfem.par smoke test passed")
