#!/usr/bin/python3
"""
Python file to orchistrate the different experiments, giving myself a sane commandline interface.
Done in Python instead of bash because I'm not doing argparsing in bash.
Done in Python instead of docker-compose because I want to program too much in here
Done in Python instead of Makefile because... you know what? Let's forget it.
"""
from __future__ import annotations

import os
import sys
import signal
import atexit
import subprocess
from pathlib import Path
from datetime import datetime

from typing import Iterable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from io import TextIOWrapper


NOW = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
RESULTS_DIR = Path.cwd() / f"results_{NOW}"
RESULTS_DIR.mkdir()

RUNNING = []


def containername(environment: str) -> str:
    return f"nmcbench_{NOW}_{environment}"


def docker(*args: str, logfile: Optional[TextIOWrapper] = None, quiet: bool = False):
    proc = subprocess.Popen(
        ["docker", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert proc.stdout is not None

    with proc.stdout:
        for line in proc.stdout:
            if not quiet:
                sys.stdout.write(line)
            if logfile is not None:
                logfile.write(line)

    proc.wait()

    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, args)


@atexit.register
def kill_all():
    if RUNNING:
        docker("rm", "-f", *RUNNING, quiet=True)
        RUNNING.clear()


def _signal_handler(_sig, _frame):
    kill_all()
    sys.exit(1)


signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


def build(environment: str):
    """
    Create the docker image of `environment` running `docker build`
    """
    docker(
        "build",
        "-t",
        containername(environment),
        f"environments/{environment}",
    )


def start(environment: str):
    """
    Start the docker image of `environment` in detatched mode, sleeping infinitely
    """
    docker(
        "run",
        "-d",
        "--name",
        containername(environment),
        "-t",
        "-v",
        f"{Path.cwd()}/data:/root/data",
        "-v",
        f"{RESULTS_DIR}:/root/results",
        "-v",
        f"{Path.cwd()}/experiments:/root/experiments",
        containername(environment),
        "sleep",
        "infinity",
    )
    RUNNING.append(containername(environment))


def run_experiments(environment: str, experiment: Iterable[Path], *args: str):
    """
    Run environment's `run_experiment.py` file reading in the files in `experiment`.
    These experiment files have to be python config files living inside `experiments/`
    """
    for filename in experiment:
        if filename.suffix != ".py":
            print(f"{filename} is not a python file. Skipping.")
            continue
        logfile_dir = RESULTS_DIR / filename.parent.name
        logfile_dir.mkdir(exist_ok=True)
        with open(logfile_dir / f"{filename.stem}_{environment}.log", "w") as logfile:
            docker(
                "exec",
                "-i",
                containername(environment),
                "python3",
                "-u",
                "/root/run_experiment.py",
                f"/root/{filename}",
                "/root/data/",
                "/root/results/",
                *args,
                logfile=logfile,
            )
        if os.name != "nt":
            st = RESULTS_DIR.stat()
            docker(
                "exec",
                containername(environment),
                "chown",
                "-R",
                f"{st.st_uid}:{st.st_gid}",
                "/root/results/",
            )
