#!/usr/bin/env python3
"""Validate an installed DGNS PyMFEM package without importing the source tree."""

from __future__ import annotations

import argparse
import importlib


EXPECTED_VERSION = "4.10.0.post1"
# Stock upstream MFEM release tag v4.10 (https://github.com/mfem/mfem).
EXPECTED_MFEM_SHA = "d964264cdb9a13e94a201b6c236c7721e0c8765f"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("par",))
    args = parser.parse_args()

    mfem_package = importlib.import_module("mfem")
    sha_module = importlib.import_module("mfem.__sha__")
    assert mfem_package.__version__ == EXPECTED_VERSION, mfem_package.__version__
    assert sha_module.mfem == EXPECTED_MFEM_SHA, sha_module.mfem

    mfem = importlib.import_module(f"mfem.{args.mode}")
    required_symbols = (
        "ParMesh",
        "ParFiniteElementSpace",
        "HypreBoomerAMG",
        "DGMassInverse",
        "FindPointsGSLIB",
    )
    missing = [name for name in required_symbols if not hasattr(mfem, name)]
    assert not missing, f"missing APIs: {missing}"

    # libCEED is not part of this build; only native MFEM backends are valid.
    device = mfem.Device("cpu")
    device.Print()
    print(
        f"validated mfem.{args.mode} {mfem_package.__version__} "
        f"at MFEM {sha_module.mfem}"
    )


if __name__ == "__main__":
    main()
