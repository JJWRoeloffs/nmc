"""
Bitwuzla Neural Arithmetic Utilities & Check Phase
=================================================

This module implements efficient bit-vector arithmetic primitives and neural
network quantization routines using Bitwuzla as the SMT backend.
(note: quantization is switched of for current version as we use integer)

Miscellaneous Helpers:
  - bShiftInc(arr, F_prec, bw_obj): Left-shift array elements by F_prec bits.
  - bMat(mat, bw_obj) / bVec(vec, bw_obj): Convert Python matrices/vectors to
    BV constant arrays.
  - bAnd(arr, bw_obj): Balanced conjunction over a list of terms.
  - bv2int(arr, bw_obj, bits) / todecimal(...): Decode BV terms to Python ints.
  - BLessThan / BLessThanEq / BLessThanEps: Comparison predicates over BV ranks.
  - bSetListUnEqual: Assert inequality between lists of BV values.

Neural Ranking Routines:
  - bLinear(bw_obj, W, b, inp, F_prec, bits, isDebug=False)
    • One-layer quantized neural inference: W*x + b.
  - bSignNN(bw_obj, param, x, F_prec, bits, gap, isDebug)
    • Multi-layer sign activation network producing binary masks.
  - bCAV_NRF(bw_obj, nnparam, clparam, inp, scale, F_prec, bits, gap, isDebug)
    • Combine quantized linear and sign networks to compute a ranking function.

Transition Checking:
  - check_tran(...)
    • Assert transition relation, ranking constraints, and collect SAT counterexamples.
  - check(...)
    • Iterate over all state-pair transitions to gather violations.
  - check_init(...)
    • Verify initial-state ranking precondition to gather violations.

"""

import bitwuzla
import numpy as np
import math
import warnings

warnings.filterwarnings("ignore")
from itertools import product
from nur import gurobi_train

from colorama import Fore, Style

from nur.bitwuzla_utils import (
    b_dot_positive,
    b_int,
    b_sign_func,
    b_elem_mul,
    b_sum,
    b_and,
    to_decimal,
)


"""
                               -----------------------------------
                                Miscellaneous Bitwuzla Functions
                               -----------------------------------
"""


def b_shift_inc(arr, F_prec, bw_obj):
    tm, opt, parser, bvsizeB = bw_obj
    arr2 = []
    for i in range(len(arr)):
        arr2.append(tm.mk_term(bitwuzla.Kind.BV_SHL, [arr[i], F_prec]))
    return arr2


def b_mat(mat, bw_obj):
    tm, opt, parser, bvsizeB = bw_obj
    matrix = [
        [tm.mk_bv_value(bvsizeB, mat[i][j]) for j in range(len(mat[i]))]
        for i in range(len(mat))
    ]
    return matrix


def b_vec(vec, bw_obj):
    tm, opt, parser, bvsizeB = bw_obj
    vector = [tm.mk_bv_value(bvsizeB, vec[i]) for i in range(len(vec))]
    return vector


def b_less_than(rank_before, rank_after, context):
    state_vars, inp_out_vars, bw_obj, bits = context
    tm, opt, parser, bvsizeB = bw_obj
    return tm.mk_term(bitwuzla.Kind.BV_SLT, [rank_before, rank_after])


def b_less_than_eq(rank_before, rank_after, context):
    state_vars, inp_out_vars, bw_obj, bits = context
    tm, opt, parser, bvsizeB = bw_obj
    return tm.mk_term(bitwuzla.Kind.BV_SLE, [rank_before, rank_after])


def b_less_than_eps(rank_before, rank_after, delta, context, F_prec, isDebug=False):
    state_vars, inp_out_vars, bw_obj, bits = context
    tm, opt, parser, bvsizeB = bw_obj
    dt = tm.mk_bv_value(bvsizeB, int(math.floor(delta)))
    res = tm.mk_term(
        bitwuzla.Kind.BV_SLT,
        [tm.mk_term(bitwuzla.Kind.BV_SUB, [rank_before, dt]), rank_after],
    )
    if isDebug:
        breakpoint()
    return res


def b_set_list_unequal(l1, l2, bw_obj):
    tm, opt, parser, bvsizeB = bw_obj
    res = []
    for i in range(len(l1)):
        res.append(
            tm.mk_term(
                bitwuzla.Kind.NOT,
                [
                    tm.mk_term(
                        bitwuzla.Kind.EQUAL,
                        [l1[i], tm.mk_bv_value(bvsizeB, int(l2[i]))],
                    )
                ],
            )
        )
    return res


"""
                               -----------------------------------
                                Bitwuzla Functions for CAV'25 NRF
                               -----------------------------------
"""


def bLinear(bw_obj, W, b, inp, F_prec, bits, isDebug=False):
    tm, opt, parser, bvsizeB = bw_obj
    scaled_W_py = (W * (2**F_prec)).astype(int).tolist()
    scaled_b_py = (b * (2**F_prec)).astype(int).tolist()
    scaled_b_bw = b_vec(scaled_b_py, bw_obj)
    out1 = []
    for i in range(len(scaled_W_py)):
        tmp = b_dot_positive(inp, scaled_W_py[i], bw_obj, F_prec, bits)
        out1.append(tmp)

    out = []
    for i in range(len(scaled_b_bw)):
        out.append(tm.mk_term(bitwuzla.Kind.BV_ADD, [out1[i], scaled_b_bw[i]]))

    if isDebug:
        print(f"bLin inp: {b_int(inp, bw_obj, bits)}")
        print(f"bLin W: {scaled_W_py} b: {scaled_b_py}")
        print(f"bLin out1: {b_int(out1, bw_obj, bits)}")
        print(f"bLin out: {b_int(out, bw_obj, bits)}")
        breakpoint()
    return out


def bSignNN(bw_obj, param, x, F_prec, bits, gap, isDebug):
    tm, opt, parser, bvsizeB = bw_obj
    W0, b0 = param[0]
    h_i = bLinear(bw_obj, W0, b0, x, F_prec, bits, isDebug)
    s_i = b_sign_func(bw_obj, h_i, bits, 1 == len(param), F_prec, gap)
    if isDebug:
        breakpoint()
    for i, (W, b) in enumerate(param[1:], 1):
        h_i = bLinear(bw_obj, W, b, s_i, F_prec, bits)
        s_i = b_sign_func(bw_obj, h_i, bits, i + 1 == len(param), F_prec, gap)
    return s_i


def bCAV_NRF(bw_obj, nnparam, clparam, inp, scale, F_prec, bits, gap, isDebug=False):
    tm, opt, parser, bvsizeB = bw_obj
    bZero = tm.mk_bv_value(bvsizeB, 0)

    F_btor = tm.mk_bv_value(bvsizeB, F_prec)
    scaled_inp1 = np.array(b_shift_inc(inp, F_btor, bw_obj))

    scale_py = [int(scale * (2**F_prec))] * len(scaled_inp1)
    scaled_inp = b_elem_mul(bw_obj, scaled_inp1, scale_py, F_prec, bits)

    if nnparam == None:
        z = bLinear(bw_obj, *clparam, scaled_inp, F_prec, bits, isDebug)
        V = b_sum(z, bw_obj, F_prec, bits)
        return V

    w = bSignNN(bw_obj, nnparam, scaled_inp, F_prec, bits, gap, isDebug)
    z = bLinear(bw_obj, *clparam, scaled_inp, F_prec, bits, isDebug)

    # If(wi > 0, zi, 0)
    V_arr = [
        tm.mk_term(
            bitwuzla.Kind.ITE,
            [tm.mk_term(bitwuzla.Kind.BV_SGT, [wi, bZero]), zi, bZero],
        )
        for wi, zi in zip(w, z)
    ]
    V = b_sum(V_arr, bw_obj, F_prec, bits)
    if isDebug:
        breakpoint()
    return V


def check_tran(
    q_cur,
    q_nex,
    trans_,
    V_cur,
    V_nex,
    nnparam,
    clparam,
    curr_vars,
    next_vars,
    non_state_vars,
    scale,
    ctx,
    is_acc,
    F_prec,
    bw_obj,
    bits,
    gap,
    kappa_quant,
):
    tm, opt, parser, bvsizeB = bw_obj
    cex_trans = []
    for cex_i in range(1):
        parser.bitwuzla().push()
        for cex in cex_trans:
            parser.bitwuzla().assert_formula(
                b_and(b_set_list_unequal(curr_vars, cex[1], bw_obj), bw_obj)
            )
            parser.bitwuzla().assert_formula(
                b_and(b_set_list_unequal(next_vars, cex[3], bw_obj), bw_obj)
            )

        if len(trans_) > 0:
            parser.bitwuzla().assert_formula(b_and(trans_, bw_obj))

        if is_acc[q_cur] == 1:
            eps = 1  # scale*.9*(2**F_prec)
            cnd_pre = b_less_than_eq(V_cur, kappa_quant, ctx)
            cnd_post = b_less_than_eps(V_cur, V_nex, eps, ctx, F_prec)
            parser.bitwuzla().assert_formula(b_and([cnd_pre, cnd_post], bw_obj))
        else:
            cnd_pre = b_less_than_eq(V_cur, kappa_quant, ctx)
            cnd_post = b_less_than(V_cur, V_nex, ctx)
            parser.bitwuzla().assert_formula(b_and([cnd_pre, cnd_post], bw_obj))

        res = parser.bitwuzla().check_sat()
        if res == bitwuzla.Result.SAT:
            # bPrint(curr_vars, bw_obj)
            # bPrint(next_vars, bw_obj)
            # bPrint(non_state_vars, bw_obj)
            c_cur = np.array(b_int(curr_vars, bw_obj, bits))
            c_nex = np.array(b_int(next_vars, bw_obj, bits))
            cex_trans.append((q_cur, c_cur, q_nex, c_nex))
            print(
                f"{Fore.CYAN}q = {q_cur} to q = {q_nex} is SAT {(q_cur, c_cur, q_nex, c_nex)} {Style.RESET_ALL}"
            )

            V_eval_q = gurobi_train.evalQuantNN(
                nnparam[q_cur], *clparam[q_cur], c_cur, scale, gap, F_prec
            )
            V_nex_eval_q = gurobi_train.evalQuantNN(
                nnparam[q_nex], *clparam[q_nex], c_nex, scale, gap, F_prec
            )
            V_eval = gurobi_train.evalFunkyNN(nnparam[q_cur], *clparam[q_cur], c_cur)
            V_nex_eval = gurobi_train.evalFunkyNN(
                nnparam[q_nex], *clparam[q_nex], c_nex
            )
            print(
                f"{Fore.WHITE}\tBitwuzla Rank [{to_decimal(V_cur, bw_obj, bits)/2**F_prec} -> {to_decimal(V_nex, bw_obj, bits)/2**F_prec}]; Numpy Rank [{V_eval} -> {V_nex_eval}]; ; Numpy RankQ [{V_eval_q/2**F_prec} -> {V_nex_eval_q/2**F_prec}]  {Style.RESET_ALL}"
            )

            # if(todecimal(V_cur, bw_obj, bits)/2**F_prec != V_eval):
            #    print("[POTENTIAL BUG]")
            #    V_cur = bCAV_NRF(bw_obj, nnparam[q_cur], clparam[q_cur], curr_vars, scale, F_prec, bits, gap, isDebug =  True)
            #    V_eval = gurobi_train.evalQuantNN(nnparam[q_cur], *clparam[q_cur], c_cur, scale, gap, F_prec, isDebug = True)
            #
            # if (todecimal(V_nex, bw_obj, bits)/2**F_prec != V_nex_eval):
            #    print("[POTENTIAL BUG]")
            #    V_nex = bCAV_NRF(bw_obj, nnparam[q_nex], clparam[q_nex], next_vars, scale, F_prec, bits, gap, isDebug = True)
            #    V_eval = gurobi_train.evalQuantNN(nnparam[q_nex], *clparam[q_nex], c_nex, scale, gap, F_prec, isDebug = True)
            # cnd = BLessThanEps(V_cur, V_nex, eps, ctx, F_prec, (c_cur==[255] and c_nex==[0]))
        else:
            print(f"{Fore.BLUE}q = {q_cur} to q = {q_nex} is UNSAT{Style.RESET_ALL}")
        parser.bitwuzla().pop()

    return cex_trans


def check(
    nnparam,
    clparam,
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
):
    cex = []
    tm, opt, parser, bvsizeB = bw_obj

    kappa_quant = tm.mk_bv_value(bvsizeB, int(kappa * (2**F_prec)))
    for q_cur, q_nex in product(q_set, repeat=2):
        V_cur = bCAV_NRF(
            bw_obj, nnparam[q_cur], clparam[q_cur], curr_vars, scale, F_prec, bits, gap
        )
        V_nex = bCAV_NRF(
            bw_obj, nnparam[q_nex], clparam[q_nex], next_vars, scale, F_prec, bits, gap
        )

        for trans_ in spec_automata(
            ctx, q_cur, curr_vars, None, q_nex, next_vars, None, non_state_vars, 1
        ):
            cex += check_tran(
                q_cur,
                q_nex,
                trans_,
                V_cur,
                V_nex,
                nnparam,
                clparam,
                curr_vars,
                next_vars,
                non_state_vars,
                scale,
                ctx,
                is_acc,
                F_prec,
                bw_obj,
                bits,
                gap,
                kappa_quant,
            )

    return cex


def check_init(
    nnparam,
    clparam,
    curr_vars,
    init_state_q,
    F_prec,
    bw_obj,
    scale,
    bits,
    gap,
    q_set,
    ctx,
    kappa,
):
    invar_cex = []
    tm, opt, parser, bvsizeB = bw_obj
    kappa_quant = tm.mk_bv_value(bvsizeB, int(kappa * (2**F_prec)))
    for q0 in q_set:
        if init_state_q[q0] == 0:
            continue
        V_cur = bCAV_NRF(
            bw_obj, nnparam[q0], clparam[q0], curr_vars, scale, F_prec, bits, gap
        )
        parser.bitwuzla().push()
        cnd = b_less_than(kappa_quant, V_cur, ctx)
        parser.bitwuzla().assert_formula(cnd)
        res = parser.bitwuzla().check_sat()
        if res == bitwuzla.Result.SAT:
            c_cur = np.array(b_int(curr_vars, bw_obj, bits))
            invar_cex.append((q0, c_cur))
            print(f"{Fore.CYAN}q = {q0} [InVar] is SAT {(q0, c_cur)} {Style.RESET_ALL}")

            V_eval_q = gurobi_train.evalQuantNN(
                nnparam[q0], *clparam[q0], c_cur, scale, gap, F_prec
            )
            V_eval = gurobi_train.evalFunkyNN(nnparam[q0], *clparam[q0], c_cur)
            print(
                f"{Fore.WHITE}\tBitwuzla Rank [{to_decimal(V_cur, bw_obj, bits)/2**F_prec}]; Numpy Rank [{V_eval}]; ; Numpy RankQ [{V_eval_q/2**F_prec}]  {Style.RESET_ALL}"
            )
        else:
            print(f"{Fore.BLUE}q = {q0} [InVar] is UNSAT{Style.RESET_ALL}")
        parser.bitwuzla().pop()
    return invar_cex
