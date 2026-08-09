#!/usr/bin/env python3
"""Check the package's native-library portability contract."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import re
import subprocess
import sys


BUNDLED_LIBRARY_PATTERNS = {
    "MFEM": re.compile(r"libmfem"),
    "HYPRE": re.compile(r"libHYPRE", re.IGNORECASE),
    "METIS": re.compile(r"libmetis", re.IGNORECASE),
    "libCEED": re.compile(r"libceed", re.IGNORECASE),
}


def dynamic_metadata(path: Path) -> str:
    if sys.platform == "darwin":
        commands = (("otool", "-L", str(path)), ("otool", "-l", str(path)))
    else:
        commands = (("readelf", "-d", str(path)),)
    return "\n".join(
        subprocess.run(command, check=True, text=True, capture_output=True).stdout
        for command in commands
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--forbid-path",
        action="append",
        default=[],
        help="absolute build path that must not occur in loader metadata",
    )
    args = parser.parse_args()

    spec = importlib.util.find_spec("mfem")
    assert spec is not None and spec.submodule_search_locations
    package_root = Path(next(iter(spec.submodule_search_locations))).resolve()
    native_files = sorted(
        path
        for path in package_root.rglob("*")
        if path.is_file() and (path.suffix in {".so", ".dylib"} or ".so." in path.name)
    )
    assert native_files, f"no native libraries found below {package_root}"
    assert not any("_ser" in path.parts for path in native_files), (
        "parallel-only package unexpectedly contains serial extension modules"
    )
    assert not (package_root / "external" / "ser").exists(), (
        "parallel-only package unexpectedly contains a serial MFEM installation"
    )

    bundled_names = [path.name for path in native_files]
    for label, pattern in BUNDLED_LIBRARY_PATTERNS.items():
        assert any(pattern.search(name) for name in bundled_names), f"{label} is not bundled"
    assert not any(re.search(r"(^|[._-])libmpi", name, re.IGNORECASE) for name in bundled_names), (
        "libmpi must be supplied by the consuming Conda environment"
    )

    forbidden = [str(Path(path).resolve()) for path in args.forbid_path if path]
    mpi_references: list[str] = []
    relative_rpaths: list[str] = []
    for path in native_files:
        metadata = dynamic_metadata(path)
        for build_path in forbidden:
            assert build_path not in metadata, f"build path leaked into {path}: {build_path}"
        for line in metadata.splitlines():
            lower = line.lower()
            if "libmpi" in lower:
                mpi_references.append(line.strip())
            if "$origin" in lower or "@loader_path" in lower:
                relative_rpaths.append(line.strip())

    assert mpi_references, "parallel libraries do not reference external libmpi"
    assert relative_rpaths, "bundled libraries lack relative loader paths"
    print(f"inspected {len(native_files)} native files below {package_root}")
    print(f"external MPI references: {len(mpi_references)}")
    print(f"relative loader paths: {len(relative_rpaths)}")


if __name__ == "__main__":
    main()
