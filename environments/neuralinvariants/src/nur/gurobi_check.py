"""
Bitwuzla Neural Arithmetic Utilities & Check Phase
=================================================

This module implements efficient bit-vector arithmetic primitives and neural
network quantization routines using Bitwuzla as the SMT backend.
(note: quantization is switched of for current version as we use integer)
"""

from __future__ import annotations

import math
import warnings
from itertools import product

warnings.filterwarnings("ignore")

import bitwuzla
import numpy as np
from colorama import Fore, Style

from nur import gurobi_train
from nur.bitwuzla_utils import (
    b_dot_positive,
    b_int,
    b_sign_func,
    b_elem_mul,
    b_sum,
    b_and,
    to_decimal,
)

from nur.check_with_nuxmv import NuXMVChecker, bw_to_verlog

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from nur.gurobi_train import NNParams, LinParams
    from nur.bitwuzla_utils import BwObj, BwContext
    from numbers import Number


def b_shift_inc(arr, F_prec, bw_obj: BwObj):
    """Left-shift array elements by F_prec bits."""
    tm, _opt, _parser, _bvsizeB = bw_obj
    arr2 = []
    for i in range(len(arr)):
        arr2.append(tm.mk_term(bitwuzla.Kind.BV_SHL, [arr[i], F_prec]))
    return arr2


def b_mat(mat, bw_obj: BwObj):
    """Convert Python matrices/vectors to BV constant arrays."""
    tm, _opt, _parser, bvsizeB = bw_obj
    matrix = [
        [tm.mk_bv_value(bvsizeB, mat[i][j]) for j in range(len(mat[i]))]
        for i in range(len(mat))
    ]
    return matrix


def b_vec(vec, bw_obj: BwObj):
    """Balanced conjunction over a list of terms."""
    tm, _opt, _parser, bvsizeB = bw_obj
    vector = [tm.mk_bv_value(bvsizeB, vec[i]) for i in range(len(vec))]
    return vector


def b_less_than(rank_before, rank_after, context: BwContext):
    """Comparison predicate over BV ranks."""
    _state_vars, _inp_out_vars, bw_obj, _bits = context
    tm, _opt, _parser, _bvsizeB = bw_obj
    return tm.mk_term(bitwuzla.Kind.BV_SLT, [rank_before, rank_after])


def b_less_than_eq(rank_before, rank_after, context: BwContext):
    """Comparison predicate over BV ranks."""
    _state_vars, _inp_out_vars, bw_obj, _bits = context
    tm, _opt, _parser, _bvsizeB = bw_obj
    return tm.mk_term(bitwuzla.Kind.BV_SLE, [rank_before, rank_after])


def b_less_than_eps(rank_before, rank_after, delta, context: BwContext, F_prec):
    """Comparison predicate over BV ranks."""
    _state_vars, _inp_out_vars, bw_obj, _bits = context
    tm, _opt, _parser, bvsizeB = bw_obj
    dt = tm.mk_bv_value(bvsizeB, int(math.floor(delta)))
    res = tm.mk_term(
        bitwuzla.Kind.BV_SLT,
        [tm.mk_term(bitwuzla.Kind.BV_SUB, [rank_before, dt]), rank_after],
    )
    return res


def b_set_list_unequal(l1, l2, bw_obj: BwObj):
    """Assert inequality between lists of BV values."""
    tm, _opt, _parser, bvsizeB = bw_obj
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


def b_linear(bw_obj: BwObj, W, b, inp, F_prec, bits, printing=False):
    """One-layer quantized neural inference: W*x + b."""
    tm, _opt, _parser, _bvsizeB = bw_obj
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

    if printing:
        print(f"bLin inp: {b_int(inp, bw_obj, bits)}")
        print(f"bLin W: {scaled_W_py} b: {scaled_b_py}")
        print(f"bLin out1: {b_int(out1, bw_obj, bits)}")
        print(f"bLin out: {b_int(out, bw_obj, bits)}")
        breakpoint()
    return out


def b_sign_nn(bw_obj: BwObj, param, x, F_prec, bits, gap):
    """Multi-layer sign activation network producing binary masks."""
    _tm, _opt, _parser, _bvsizeB = bw_obj
    W0, b0 = param[0]
    h_i = b_linear(bw_obj, W0, b0, x, F_prec, bits)
    s_i = b_sign_func(bw_obj, h_i, bits, 1 == len(param), F_prec, gap)
    for i, (W, b) in enumerate(param[1:], 1):
        h_i = b_linear(bw_obj, W, b, s_i, F_prec, bits)
        s_i = b_sign_func(bw_obj, h_i, bits, i + 1 == len(param), F_prec, gap)
    return s_i


def bCAV_NRF(bw_obj: BwObj, nnparam, clparam, inp, scale, F_prec, bits, gap):
    """Combine quantized linear and sign networks to compute a ranking function."""
    tm, _opt, _parser, bvsizeB = bw_obj
    bZero = tm.mk_bv_value(bvsizeB, 0)

    F_btor = tm.mk_bv_value(bvsizeB, F_prec)
    scaled_inp1 = np.array(b_shift_inc(inp, F_btor, bw_obj))

    scale_py = [int(scale * (2**F_prec))] * len(scaled_inp1)
    scaled_inp = b_elem_mul(bw_obj, scaled_inp1, scale_py, F_prec, bits)

    if nnparam == None:
        z = b_linear(bw_obj, *clparam, scaled_inp, F_prec, bits)
        V = b_sum(z, bw_obj, F_prec, bits)
        return V

    w = b_sign_nn(bw_obj, nnparam, scaled_inp, F_prec, bits, gap)
    z = b_linear(bw_obj, *clparam, scaled_inp, F_prec, bits)

    # If(wi > 0, zi, 0)
    V_arr = [
        tm.mk_term(
            bitwuzla.Kind.ITE,
            [tm.mk_term(bitwuzla.Kind.BV_SGT, [wi, bZero]), zi, bZero],
        )
        for wi, zi in zip(w, z)
    ]
    V = b_sum(V_arr, bw_obj, F_prec, bits)
    return V


def check_tran(
    q_cur: int,
    q_nex: int,
    trans_: list[bitwuzla.Term],
    V_cur: bitwuzla.Term,
    V_nex: bitwuzla.Term,
    nnparam: NNParams,
    clparam: LinParams,
    curr_vars: list[bitwuzla.Term],
    next_vars: list[bitwuzla.Term],
    non_state_vars: list[bitwuzla.Term],
    scale: int,
    ctx: BwContext,
    is_acc: list[int],
    F_prec: int,
    bw_obj: BwObj,
    bits: int,
    gap: float,
    kappa_quant: bitwuzla.Term,
) -> list:
    """Assert transition relation, ranking constraints, and collect SAT counterexamples."""
    assert isinstance(V_cur, bitwuzla.Term)
    assert isinstance(V_nex, bitwuzla.Term)
    assert all(isinstance(tr, bitwuzla.Term) for tr in trans_)
    assert isinstance(q_cur, int)
    assert isinstance(q_nex, int)
    assert isinstance(bits, int)
    assert isinstance(gap, float)
    assert isinstance(F_prec, int)
    assert isinstance(is_acc, list)
    assert all(x == 1 or x == 0 for x in is_acc)
    assert isinstance(scale, int)
    assert all(isinstance(x, bitwuzla.Term) for x in curr_vars)
    assert all(isinstance(x, bitwuzla.Term) for x in next_vars)
    assert all(isinstance(x, bitwuzla.Term) for x in non_state_vars)

    _tm, _opt, parser, _bvsizeB = bw_obj
    cex_trans = []
    parser.bitwuzla().push()

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
        NuXMVChecker.check_state_unreachable(
            [bw_to_verlog(str(x)) for x in curr_vars],
            [bw_to_verlog(str(x)) for x in next_vars],
            [bw_to_verlog(str(x)) for x in non_state_vars],
        )
        c_cur = np.array(b_int(curr_vars, bw_obj, bits))
        c_nex = np.array(b_int(next_vars, bw_obj, bits))
        cex_trans.append((q_cur, c_cur, q_nex, c_nex))
        print(
            f"{Fore.CYAN}q = {q_cur} to q = {q_nex} is SAT {(q_cur, c_cur, q_nex, c_nex)} {Style.RESET_ALL}"
        )

        V_eval_q = gurobi_train.eval_quant_nn(
            nnparam[q_cur], *clparam[q_cur], c_cur, scale, gap, F_prec
        )
        V_nex_eval_q = gurobi_train.eval_quant_nn(
            nnparam[q_nex], *clparam[q_nex], c_nex, scale, gap, F_prec
        )
        V_eval = gurobi_train.eval_funky_nn(nnparam[q_cur], *clparam[q_cur], c_cur)
        V_nex_eval = gurobi_train.eval_funky_nn(nnparam[q_nex], *clparam[q_nex], c_nex)
        print(
            f"{Fore.WHITE}\tBitwuzla Rank [{to_decimal(V_cur, bw_obj, bits)/2**F_prec} -> {to_decimal(V_nex, bw_obj, bits)/2**F_prec}]; Numpy Rank [{V_eval} -> {V_nex_eval}]; ; Numpy RankQ [{V_eval_q/2**F_prec} -> {V_nex_eval_q/2**F_prec}]  {Style.RESET_ALL}"
        )

    else:
        print(f"{Fore.BLUE}q = {q_cur} to q = {q_nex} is UNSAT{Style.RESET_ALL}")
    parser.bitwuzla().pop()

    return cex_trans


def check(
    nnparam: NNParams,
    clparam: LinParams,
    curr_vars: list[bitwuzla.Term],
    next_vars: list[bitwuzla.Term],
    non_state_vars: list[bitwuzla.Term],
    scale: int,
    spec_automata: Callable,
    ctx: BwContext,
    q_set: list[int],
    is_acc: list[int],
    F_prec: int,
    bw_obj: BwObj,
    bits: int,
    gap: float,
    kappa: Number,
):
    """Iterate over all state-pair transitions to gather violations."""
    assert isinstance(gap, float)
    assert isinstance(scale, int)
    assert isinstance(q_set, list)
    assert all(isinstance(item, int) for item in q_set)
    assert all(isinstance(x, bitwuzla.Term) for x in curr_vars)
    assert all(isinstance(x, bitwuzla.Term) for x in next_vars)
    assert all(isinstance(x, bitwuzla.Term) for x in non_state_vars)
    cex = []
    tm, _opt, _parser, bvsizeB = bw_obj

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
    nnparam: NNParams,
    clparam: LinParams,
    curr_vars: list[bitwuzla.Term],
    init_state_q,
    F_prec: int,
    bw_obj: BwObj,
    scale: int,
    bits: int,
    gap: float,
    q_set: list[int],
    ctx: BwContext,
    kappa: Number,
):
    """Verify initial-state ranking precondition to gather violations."""
    invar_cex = []
    tm, _opt, parser, bvsizeB = bw_obj
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

            V_eval_q = gurobi_train.eval_quant_nn(
                nnparam[q0], *clparam[q0], c_cur, scale, gap, F_prec
            )
            V_eval = gurobi_train.eval_funky_nn(nnparam[q0], *clparam[q0], c_cur)
            print(
                f"{Fore.WHITE}\tBitwuzla Rank [{to_decimal(V_cur, bw_obj, bits)/2**F_prec}]; Numpy Rank [{V_eval}]; ; Numpy RankQ [{V_eval_q/2**F_prec}]  {Style.RESET_ALL}"
            )
        else:
            print(f"{Fore.BLUE}q = {q0} [InVar] is UNSAT{Style.RESET_ALL}")
        parser.bitwuzla().pop()
    return invar_cex
