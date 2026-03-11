"""
Run ebmc from an imported config file. This needs to have the following things defined:

start_ex: int
    The index of the first file to run. Used to skip files
N_lims: list[int]
    For ebmc, all that matters is that this list contains an equal amount of unique numbers,
    as there are files to be ran.
filename: str
    the name, excluding the `_N` of the files in `datapath` to run.
specTXT: str
    The spec to check in TXT to be put in the logs
SVSpec: str
    The SVSpec to check, or none if there is a nuSmvSpec instead.
"""

import re
import argparse
import subprocess
import importlib.util
from pathlib import Path
from time import perf_counter


def existing_path(p: str) -> Path:
    path = Path(p)
    if not path.exists():
        raise argparse.ArgumentTypeError(f"{p} does not exist")
    return path


parser = argparse.ArgumentParser(prog="ebmc entrypoint")
parser.add_argument("runargs_path", type=existing_path)
parser.add_argument("datapath", type=existing_path)
parser.add_argument("resultspath", type=existing_path)
arguments = parser.parse_args()
print(f"Starting ebmc test with {arguments.runargs_path}")

taskname = arguments.runargs_path.stem

# This forces us to always have a new results directory, not passing exists_ok
# It's not the most convenient, but a lot safer than accedentally overwriting results
resultspath = arguments.resultspath / f"ebmc_{taskname}"
resultspath.mkdir()


# We load the config as a python module.
# This is kinda jank, and I would have preferred to do it literally any other way,
# but it's the best that was possible with the way the original code was set up.
spec = importlib.util.spec_from_file_location("runargs", arguments.runargs_path)
assert spec is not None, "The passed runargs is not importable as python module"
assert spec.loader is not None, "The passed runargs is a runnable loader, but not "
argsmodule = importlib.util.module_from_spec(spec)
spec.loader.exec_module(argsmodule)

# All this is still mostly taken over from the original
# I just extracted all the nuxmv-relevant things to make it not as coupled
# and avoided hardcoding as many filepaths.
for dut_i in range(argsmodule.start_ex, len(argsmodule.N_lims)):
    name = f"{argsmodule.file_name}_{dut_i+1}"
    N_lim: int = argsmodule.N_lims[dut_i]
    idtxt = f"{name} ({argsmodule.specTXT}) {N_lim}"
    print(idtxt)

    # Since we will be moving files around with ebmc and such, we need some unique temp dir.
    # Not using TemporaryDirectory because I'm not sure if it has overhead. It's containerised anyway.
    tempdir = Path() / f"generated_{taskname}_ebmc_{dut_i}"
    tempdir.mkdir()

    # Add the SVSpec to the target file
    sourcepath: Path = arguments.datapath / f"{name}.sv"
    assert sourcepath.exists(), f"Input file by name {sourcepath} cannot be found"

    modified_content = re.sub(
        "endmodule",
        f"\tp1: assert property  ({argsmodule.SVSpec}) ;\nendmodule",
        sourcepath.read_text(),
    )
    targetpath = tempdir / "with_svs.sv"
    targetpath.write_text(modified_content)
    sourcepath = targetpath

    # Actually run the thing
    start = perf_counter()
    subprocess.run(["ebmc", targetpath, "--bdd"], check=True)
    duration = perf_counter() - start

    print(f"Ran ebmc on {arguments.runargs_path}, ID {idtxt}")
    print(f"runtime: {duration:.3f}")
    resultsfile = resultspath.joinpath(f"{name}.txt").write_text(f"{duration}; {idtxt}")
