"""
Run the model from the _Let a neural network be your invariant_ paper.
This needs the following things defined:
Ps: list[int]
    blah
Ms: list[int]
    blah
N_lims: list[int]
    blah
filename: str
    the name, excluding the `_N` of the files in `datapath` to run.
specTXT: str
    The spec to check in TXT to be put in the logs
module_name: str
    The name of the module
bits: int
    blah
F_prec: int
    blah
init_samp: list[tuple[int, list[float]]]
spec_automata: Callable
    blah

Hyperparemeters:
scale: int
size: list[int]
gap float

"""

import argparse
import subprocess
import importlib.util
from pathlib import Path
from time import perf_counter

import nur


def existing_path(p: str) -> Path:
    path = Path(p)
    if not path.exists():
        raise argparse.ArgumentTypeError(f"{p} does not exist")
    return path


parser = argparse.ArgumentParser(prog="ebmc entrypoint")
parser.add_argument("runargs_path", type=existing_path)
parser.add_argument("datapath", type=existing_path)
parser.add_argument("resultspath", type=existing_path)
parser.add_argument("--samples", type=int, default=0)
parser.add_argument(
    "--learning_engine", choices=["gurobi", "cvc5", "z3", "msat"], default="gurobi"
)
parser.add_argument("--unbounded", action="store_true")
parser.add_argument("--auto", action="store_true")
arguments = parser.parse_args()
print(f"Starting neuralinvariants test with {arguments.runargs_path}")
if arguments.learning_engine == "gurobi" and arguments.unbounded:
    parser.error("Gurobi cannot be run with unbounded parameters")

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

if arguments.unbounded:
    ps = [None] * len(argsmodule.Ps)
else:
    ps = argsmodule.Ps

gu_times, bw_times, total_times, guess_cnts = [], [], [], []

for dut_i in range(argsmodule.start_ex, len(argsmodule.N_lims)):
    N_lim = argsmodule.N_lims[dut_i]
    P = ps[dut_i]
    M = argsmodule.Ms[dut_i]
    kappa = None  # N_lim
    hyperparameters = (argsmodule.scale, P, argsmodule.size, argsmodule.gap, M, kappa)
    name = f"{argsmodule.file_name}_{dut_i+1}"
    idtxt = f"{name} ({argsmodule.specTXT}) {N_lim}"
    print(f"\t\t\t\t {idtxt}\n\t\t\t\t")

    tempdir = Path() / f"generated_{taskname}_neuralinvariants_{dut_i}"
    tempdir.mkdir()

    # Add the SVSpec to the target file
    svfile: Path = arguments.datapath / f"{name}.sv"
    assert svfile.exists(), f"Input file by name {svfile} cannot be found"

    start = perf_counter()
    (
        state_vars,
        inp_out_vars,
        bw_obj,
        curr_vars,
        next_vars,
        non_state_vars,
        state_names,
    ) = nur.read_svfile(svfile, argsmodule.module_name, argsmodule.bits)
    ctx = state_vars, inp_out_vars, bw_obj, argsmodule.bits
    gu_time, bw_time, guess_cnt, size_success = nur.runExperiment(
        name,
        hyperparameters,
        bw_obj,
        curr_vars,
        next_vars,
        non_state_vars,
        argsmodule.spec_automata,
        ctx,
        argsmodule.F_prec,
        argsmodule.bits,
        argsmodule.is_acc,
        argsmodule.init_samp,
        argsmodule.is_init,
        state_vars,
        state_names,
        arguments.samples,
        arguments.learning_engine,
        arguments.auto,
    )
    duration = perf_counter() - start
    print(
        f"BITS ---------->>>>>>>>> {argsmodule.bits} {idtxt} E: {arguments.learning_engine} P: {P} RndSmps: {arguments.samples} isAuto: {arguments.auto} Arch: {size_success}"
    )
    print(f"Learn Time: {gu_time}; Check Time: {bw_time}; Guess cnt: {guess_cnt}")
    print(f"Total Time: {duration}\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")
