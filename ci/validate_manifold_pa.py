#!/usr/bin/env python3
"""Validate matrix-free mass and transport on embedded tensor surfaces."""

from __future__ import annotations

from mpi4py import MPI
import numpy as np

import mfem.par as mfem


class AffineField(mfem.PyCoefficient):
    def __init__(self, parent_dimension: int) -> None:
        mfem.PyCoefficient.__init__(self)
        self.parent_dimension = parent_dimension

    def EvalValue(self, point):
        if self.parent_dimension == 2:
            return point[0]
        return 0.17 * point[0] - 0.23 * point[1]


def _check(parent_dimension: int) -> float:
    if parent_dimension == 2:
        serial = mfem.Mesh.MakeCartesian2D(
            4, 2, mfem.Element.QUADRILATERAL, False, 2.0, 1.0
        )
        attribute = 3
        velocity_values = (0.7, 0.0)
        derivative = 0.7
    else:
        serial = mfem.Mesh.MakeCartesian3D(
            3, 2, 1, mfem.Element.HEXAHEDRON, 2.0, 1.5, 1.0
        )
        attribute = 6
        velocity_values = (0.7, -0.4, 0.0)
        derivative = 0.7 * 0.17 + (-0.4) * (-0.23)

    parent = mfem.ParMesh(MPI.COMM_WORLD, serial)
    surface = mfem.ParSubMesh.CreateFromBoundary(
        parent, mfem.intArray([attribute])
    )
    dimension = surface.Dimension()
    collection = mfem.L2_FECollection(
        3, dimension, mfem.BasisType.GaussLobatto
    )
    space = mfem.ParFiniteElementSpace(surface, collection)
    velocity = mfem.VectorConstantCoefficient(
        mfem.Vector(np.asarray(velocity_values, dtype=float))
    )

    mass = mfem.ParBilinearForm(space)
    mass.SetAssemblyLevel(mfem.AssemblyLevel_PARTIAL)
    mass.AddDomainIntegrator(mfem.MassIntegrator())
    mass.Assemble()
    convection = mfem.ParBilinearForm(space)
    convection.SetAssemblyLevel(mfem.AssemblyLevel_PARTIAL)
    convection.AddDomainIntegrator(mfem.ConvectionIntegrator(velocity, 1.0))
    convection.Assemble()

    one = mfem.Vector(space.GetVSize())
    one.Assign(1.0)
    field = mfem.ParGridFunction(space)
    field.ProjectCoefficient(AffineField(parent_dimension))
    expected = mfem.Vector(space.GetVSize())
    result = mfem.Vector(space.GetVSize())
    mass.Mult(one, expected)
    expected *= derivative
    convection.Mult(field, result)
    result -= expected
    local = np.max(np.abs(result.GetDataArray()), initial=0.0)
    return float(MPI.COMM_WORLD.allreduce(local, op=MPI.MAX))


def main() -> None:
    assert hasattr(mfem.SurfaceKinematicOperator, "FaceMult")
    assert hasattr(mfem.SurfaceKinematicOperator2D, "FaceMult")
    error = max(_check(2), _check(3))
    assert error < 5.0e-12, error
    print(f"validated embedded-manifold PA and face-only APIs: {error:.3e}")


if __name__ == "__main__":
    main()
