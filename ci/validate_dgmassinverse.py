#!/usr/bin/env python3
"""Exercise the native DG mass inverse and its fixed-operator adapter."""

from __future__ import annotations

import gc

from mpi4py import MPI
import numpy as np

import mfem.par as mfem


def main() -> None:
    assert hasattr(mfem, "DGMassInverse")
    assert hasattr(mfem, "DGMassInversePreconditioner")

    serial_mesh = mfem.Mesh.MakeCartesian2D(
        2,
        2,
        mfem.Element.QUADRILATERAL,
        True,
        1.0,
        1.0,
    )
    mesh = mfem.ParMesh(MPI.COMM_WORLD, serial_mesh)
    collection = mfem.L2_FECollection(3, 2, mfem.BasisType.GaussLobatto)
    space = mfem.ParFiniteElementSpace(
        mesh,
        collection,
        2,
        mfem.Ordering.byNODES,
    )

    # MFEM's PA MassIntegrator is scalar. Build the reference action on the
    # matching scalar space, then pack its two independent component loads in
    # byNODES ordering for the vector-valued inverse.
    scalar_space = mfem.ParFiniteElementSpace(mesh, collection)
    mass = mfem.ParBilinearForm(scalar_space)
    mass.SetAssemblyLevel(mfem.AssemblyLevel_PARTIAL)
    mass.AddDomainIntegrator(mfem.MassIntegrator())
    mass.Assemble()

    inverse = mfem.DGMassInverse(space, mfem.BasisType.GaussLegendre)
    inverse.SetRelTol(1.0e-13)
    inverse.SetAbsTol(0.0)
    inverse.SetMaxIter(100)
    inverse.Update()
    preconditioner = mfem.DGMassInversePreconditioner(inverse)

    # Both native objects retain only non-owning C++ references. The SWIG
    # ownership links must keep their complete dependency chain alive.
    assert inverse._link[0] is space
    assert preconditioner._link is inverse
    gc.collect()

    size = space.GetTrueVSize()
    source = mfem.Vector(size)
    source_values = np.linspace(-1.0, 1.0, size, dtype=np.float64)
    source.GetDataArray()[:] = source_values
    load = mfem.Vector(size)
    recovered = mfem.Vector(size)
    scalar_size = scalar_space.GetTrueVSize()
    scalar_source = mfem.Vector(scalar_size)
    scalar_load = mfem.Vector(scalar_size)
    for component in range(2):
        component_slice = slice(component * scalar_size, (component + 1) * scalar_size)
        scalar_source.GetDataArray()[:] = source_values[component_slice]
        mass.Mult(scalar_source, scalar_load)
        load.GetDataArray()[component_slice] = scalar_load.GetDataArray()

    # This call is the purpose of the adapter: an outer Krylov solver may
    # forward its Helmholtz operator without retargeting the fixed mass inverse.
    preconditioner.SetOperator(mass)
    preconditioner.Mult(load, recovered)
    np.testing.assert_allclose(
        recovered.GetDataArray(),
        source_values,
        rtol=2.0e-11,
        atol=2.0e-12,
    )
    print(
        "validated native DGMassInverse and DGMassInversePreconditioner "
        f"on {size} vector-valued DG unknowns"
    )


if __name__ == "__main__":
    main()
