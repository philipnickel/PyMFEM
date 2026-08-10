import gc
import sys

import numpy as np


if len(sys.argv) > 1 and sys.argv[1] == "-p":
    from mpi4py import MPI

    import mfem.par as mfem

    use_parallel = True
else:
    import mfem.ser as mfem

    use_parallel = False


def make_coefficient(values):
    """Return a temporary Vector to exercise the constructor's deep copy."""

    return mfem.Vector(np.ascontiguousarray(values, dtype=np.float64))


def test_vector_divdiv_binding():
    assert hasattr(mfem, "VectorDivDivIntegrator")

    serial_mesh = mfem.Mesh.MakeCartesian2D(
        2,
        2,
        mfem.Element.QUADRILATERAL,
    )
    if use_parallel:
        mesh = mfem.ParMesh(MPI.COMM_WORLD, serial_mesh)
    else:
        mesh = serial_mesh

    collection = mfem.L2_FECollection(2, 2, mfem.BasisType.GaussLobatto)
    if use_parallel:
        space = mfem.ParFiniteElementSpace(
            mesh,
            collection,
            2,
            mfem.Ordering.byNODES,
        )
        form = mfem.ParBilinearForm(space)
    else:
        space = mfem.FiniteElementSpace(
            mesh,
            collection,
            2,
            mfem.Ordering.byNODES,
        )
        form = mfem.BilinearForm(space)

    element_count = int(mesh.GetNE())
    explicit_integrator = mfem.VectorDivDivIntegrator(
        make_coefficient(np.ones(element_count)),
    )
    gc.collect()
    explicit_coefficient = explicit_integrator.GetElementCoefficient()
    explicit_coefficient.HostRead()
    np.testing.assert_array_equal(
        np.asarray(explicit_coefficient.GetDataArray()),
        np.ones(element_count),
    )

    integrator = mfem.VectorDivDivIntegrator()
    integrator.SetElementCoefficient(make_coefficient(np.ones(element_count)))
    gc.collect()

    form.SetAssemblyLevel(mfem.AssemblyLevel_PARTIAL)
    form.AddDomainIntegrator(integrator)
    form.Assemble()

    state = mfem.Vector(space.GetVSize())
    state.Assign(np.linspace(0.125, 1.0, state.Size(), dtype=np.float64))
    first = mfem.Vector(state.Size())
    form.Mult(state, first)
    first.HostRead()
    first_values = np.asarray(first.GetDataArray()).copy()
    assert np.linalg.norm(first_values) > 0.0

    integrator.SetElementCoefficient(
        make_coefficient(2.0 * np.ones(element_count)),
    )
    gc.collect()
    form.Assemble()

    second = mfem.Vector(state.Size())
    form.Mult(state, second)
    second.HostRead()
    second_values = np.asarray(second.GetDataArray()).copy()
    np.testing.assert_allclose(
        second_values,
        2.0 * first_values,
        rtol=2.0e-13,
        atol=2.0e-13,
    )

    retained = integrator.GetElementCoefficient()
    assert retained._link is integrator
    retained.HostRead()
    np.testing.assert_array_equal(
        np.asarray(retained.GetDataArray()),
        2.0 * np.ones(element_count),
    )


if __name__ == "__main__":
    test_vector_divdiv_binding()
