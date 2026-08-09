#!/usr/bin/env python3
"""Validate an installed DGNS PyMFEM package without importing the source tree."""

from __future__ import annotations

import argparse
import importlib


EXPECTED_VERSION = "4.9.0.post2"
EXPECTED_MFEM_SHA = "ac454cb762e9711d9922f6441c496eb7d659d158"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("par",))
    args = parser.parse_args()

    mfem_package = importlib.import_module("mfem")
    sha_module = importlib.import_module("mfem.__sha__")
    assert mfem_package.__version__ == EXPECTED_VERSION
    assert sha_module.mfem == EXPECTED_MFEM_SHA

    mfem = importlib.import_module(f"mfem.{args.mode}")
    required_symbols = (
        "ALEConvectionBoundaryIntegrator",
        "DGDiffusionIntegrator",
        "DGDirichletLFIntegrator",
        "VectorNormalJumpIntegrator",
    )
    missing = [name for name in required_symbols if not hasattr(mfem, name)]
    assert not missing, f"missing patched APIs: {missing}"
    assert hasattr(mfem.DGDiffusionIntegrator, "SetPenaltyCoefficient")
    assert hasattr(mfem.DGDirichletLFIntegrator, "SetPenaltyCoefficient")

    coefficient = mfem.ConstantCoefficient(2.0)
    normal_jump = mfem.VectorNormalJumpIntegrator(coefficient)
    assert normal_jump._coeff is coefficient

    assert hasattr(mfem.ParFiniteElementSpace, "SupportsVectorL2FaceRestriction")

    # Configuring the CEED CPU backend is a runtime check, not just a symbol check.
    device = mfem.Device("ceed-cpu")
    device.Print()
    print(
        f"validated mfem.{args.mode} {mfem_package.__version__} "
        f"at MFEM {sha_module.mfem}"
    )


if __name__ == "__main__":
    main()
