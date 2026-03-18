"""
CAV-NUR -> Computer Aided Verification using Neural Reasoning.
"""

from __future__ import annotations

import random
from time import perf_counter
from itertools import product

import numpy as np
import bitwuzla as bw
from colorama import Fore, Style

from nur import gurobi_check
from nur import gurobi_train
from nur.bitwuzla_utils import set_lhs_state, b_and, b_int
from nur.parsing import read_svfile


def random_lhs_set(state_vars, state_names, curr_vars, bw_obj):
    """Sample random assignments for state variables and return assignment + term."""
    val = []
    for state in state_names:
        lb, ub = state_vars[state]["lb"], state_vars[state]["ub"]
        val.append(random.randint(lb, ub))
    return val, set_lhs_state(curr_vars, val, bw_obj)


def get_random_samples(
    samples,
    bw_obj,
    curr_vars,
    next_vars,
    non_state_vars,
    spec_automata,
    ctx,
    q_set,
    bits,
    state_vars,
    state_names,
    rnd_smpC,
):
    """Collect random SAT/UNSAT transitions under random LHS sampling."""
    tm, opt, parser, bvsizeB = bw_obj
    print(20 * "=")
    print("Random Samples")
    print(20 * "=")
    for q_cur, q_nex in product(q_set, repeat=2):
        print(f"{Fore.CYAN}q = {q_cur} to q = {q_nex}{Style.RESET_ALL}")
        for smp_cnt in range(0, rnd_smpC):
            for trans_ in spec_automata(
                ctx, q_cur, curr_vars, None, q_nex, next_vars, None, non_state_vars, 1
            ):
                parser.bitwuzla().push()
                val_lhs, set_lhs = random_lhs_set(
                    state_vars, state_names, curr_vars, bw_obj
                )
                parser.bitwuzla().assert_formula(set_lhs)
                if len(trans_) > 0:
                    parser.bitwuzla().assert_formula(b_and(trans_, bw_obj))
                res = parser.bitwuzla().check_sat()
                if res == bw.Result.SAT:
                    # bPrint(curr_vars, bw_obj)
                    c_cur = np.array(b_int(curr_vars, bw_obj, bits))
                    c_nex = np.array(b_int(next_vars, bw_obj, bits))
                    samples.append((q_cur, c_cur, q_nex, c_nex))
                    print(
                        f"{Fore.LIGHTGREEN_EX}Valid sample: {(q_cur, c_cur, q_nex, c_nex)}{Style.RESET_ALL}"
                    )
                else:
                    print(
                        f"{Fore.YELLOW}Invalid LHS Sample: ({q_cur}, {val_lhs}, {q_nex},  X) {Style.RESET_ALL}"
                    )
                parser.bitwuzla().pop()


def get_first_samples(
    samples,
    bw_obj,
    curr_vars,
    next_vars,
    non_state_vars,
    spec_automata,
    ctx,
    q_set,
    bits,
    state_vars,
    state_names,
):
    """Collect initial SAT transitions without random inputs as sample tuples."""
    tm, opt, parser, bvsizeB = bw_obj
    print(20 * "=")
    print("Initial Samples")
    print(20 * "=")
    for q_cur, q_nex in product(q_set, repeat=2):
        # print(f"q = {q_cur} to q = {q_nex}")
        for trans_ in spec_automata(
            ctx, q_cur, curr_vars, None, q_nex, next_vars, None, non_state_vars, 1
        ):
            parser.bitwuzla().push()
            if len(trans_) > 0:
                parser.bitwuzla().assert_formula(b_and(trans_, bw_obj))
            res = parser.bitwuzla().check_sat()
            if res == bw.Result.SAT:
                # bPrint(curr_vars, bw_obj)
                c_cur = np.array(b_int(curr_vars, bw_obj, bits))
                c_nex = np.array(b_int(next_vars, bw_obj, bits))
                samples.append((q_cur, c_cur, q_nex, c_nex))
                print(
                    f"{Fore.CYAN}q = {q_cur} to q = {q_nex} is SAT {(q_cur, c_cur, q_nex, c_nex)}{Style.RESET_ALL}"
                )
            else:
                print(
                    f"{Fore.CYAN}q = {q_cur} to q = {q_nex} is UNSAT{Style.RESET_ALL}"
                )
            parser.bitwuzla().pop()


def fake_cex_check(samples, cex):
    """Ensure no duplicate counterexamples between existing samples and new cex."""
    for ce in cex:
        for sample in samples:
            cnd = (
                ce[0] == sample[0]
                and np.array_equal(ce[1], sample[1])
                and ce[2] == sample[2]
                and np.array_equal(ce[3], sample[3])
            )
            if cnd:
                breakpoint()
                assert False


def train_an_nrf(
    bw_obj,
    hyperparameters,
    samples,
    init_samp,
    curr_vars,
    next_vars,
    non_state_vars,
    spec_automata,
    ctx,
    F_prec,
    bits,
    is_acc,
    q_set,
    is_init,
    isAuto=True,
):
    """
    Train neural ranking/invariant functions with Gurobi or SMT-based learner.
    Alternate training (nnparam) and verification (gurobi_check.check), collect timings.
    Return (training_time, checking_time, iterations) or (None,None,iter) on failure.
    """
    scale, P, size, gap, M, kappa = hyperparameters
    bw_time = 0
    gu_time = 0
    cex = samples
    cex_init = init_samp
    mipL = gurobi_train.MIPLearn(is_acc, size=size, P=P, M=M)
    for try_i in range(5000):
        begin = perf_counter()
        nnparam, linparam, kappa, best_F = gurobi_train.gurobi_nn_train(
            try_i,
            mipL,
            cex,
            cex_init,
            samples,
            init_samp,
            scale,
            P,
            is_acc,
            size,
            gap,
            kappa,
        )
        if nnparam == None:
            return None, None, try_i
        F_prec = best_F  # max(best_F, F_prec)
        print(f"PRECISION: {F_prec}")
        gu_time += perf_counter() - begin

        begin = perf_counter()
        cex = gurobi_check.check(
            nnparam,
            linparam,
            curr_vars,
            next_vars,
            non_state_vars,
            scale,
            spec_automata,
            ctx,
            q_set,
            is_acc,
            F_prec,
            bw_obj,
            bits,
            gap,
            kappa,
        )
        cex_init = gurobi_check.check_init(
            nnparam,
            linparam,
            curr_vars,
            is_init,
            F_prec,
            bw_obj,
            scale,
            bits,
            gap,
            q_set,
            ctx,
            kappa,
        )
        bw_time += perf_counter() - begin
        if (len(cex) + len(cex_init)) == 0:
            print(
                f"{Fore.GREEN}\t*********  Yay! We've got a ranking function.  ************{Style.RESET_ALL}"
            )
            break
        fake_cex_check(samples, cex)
        # new_samples = cex
        samples += cex
        init_samp += cex_init
    else:
        print(
            f"{Fore.RED}\t*********  Ranking Function training Failed!  ************{Style.RESET_ALL}"
        )
    return gu_time, bw_time, try_i


def run_experiment(
    name,
    hyperparameters,
    bw_obj,
    curr_vars,
    next_vars,
    non_state_vars,
    spec_automata,
    ctx,
    F_prec,
    bits,
    is_acc,
    init_samp,
    is_init,
    state_vars,
    state_names,
    rnd_smpC,
    isAuto,
):
    """
    Orchestrate the full workflow: initial+random sampling, training loop,
    optional auto-architecture growth, return final metrics and model size.
    """
    init_samp = [(x, np.array(xs)) for x, xs in init_samp]
    scale, P, size, gap, M, kappa = hyperparameters
    seed = 2
    random.seed(seed)
    q_set = list(range(len(is_acc)))
    samples = []
    get_first_samples(
        samples,
        bw_obj,
        curr_vars,
        next_vars,
        non_state_vars,
        spec_automata,
        ctx,
        q_set,
        bits,
        state_vars,
        state_names,
    )
    get_random_samples(
        samples,
        bw_obj,
        curr_vars,
        next_vars,
        non_state_vars,
        spec_automata,
        ctx,
        q_set,
        bits,
        state_vars,
        state_names,
        rnd_smpC,
    )
    while True:
        gu_time, bw_time, guess_cnt = train_an_nrf(
            bw_obj,
            hyperparameters,
            samples,
            init_samp,
            curr_vars,
            next_vars,
            non_state_vars,
            spec_automata,
            ctx,
            F_prec,
            bits,
            is_acc,
            q_set,
            is_init,
        )
        if gu_time == None and isAuto == True:
            size = [size[0], 1 if len(size) == 1 else (size[1] + 1)]
            hyperparameters = scale, P, size, gap, M, kappa
            if size[1] == 5:
                exit()
        else:
            break
    return gu_time, bw_time, guess_cnt, size


__all__ = ("run_experiment", "read_svfile")
