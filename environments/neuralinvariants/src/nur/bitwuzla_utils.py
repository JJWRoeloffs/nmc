import math

import bitwuzla

from typing import Any

BwObj = tuple[bitwuzla.TermManager, bitwuzla.Options, bitwuzla.Parser, bitwuzla.Sort]
BwContext = tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], BwObj, int]


def b_mul(bvar, number, bw_obj: BwObj, bvsizeB_larger, dpt):
    """
    Perform constant multiplication via recursive shift-and-add decomposition.
    Handles positive/negative factors by splitting into power-of-two and bias.
    """
    tm, _opt, _parser, _bvsizeB = bw_obj
    if number == 0:
        return tm.mk_term(
            bitwuzla.Kind.BV_MUL, [bvar, tm.mk_bv_value(bvsizeB_larger, 0)]
        )

    sign = 1 if number > 0 else -1
    pow_2 = math.floor(math.log2(abs(number)))
    bias = abs(number) - 2 ** math.floor(math.log2(abs(number)))
    t1 = tm.mk_term(bitwuzla.Kind.BV_SHL, [bvar, tm.mk_bv_value(bvsizeB_larger, pow_2)])
    if bias > 2:
        t2 = b_mul(bvar, bias, bw_obj, bvsizeB_larger, dpt + 1)
    else:
        t2 = tm.mk_term(
            bitwuzla.Kind.BV_MUL, [bvar, tm.mk_bv_value(bvsizeB_larger, bias)]
        )
    if sign == 1:
        return tm.mk_term(bitwuzla.Kind.BV_ADD, [t1, t2])
    else:
        return tm.mk_term(
            bitwuzla.Kind.BV_MUL,
            [
                tm.mk_term(bitwuzla.Kind.BV_ADD, [t1, t2]),
                tm.mk_bv_value(bvsizeB_larger, -1),
            ],
        )


def b_dot_positive(arrVar, arrNum, bw_obj: BwObj, F_prec, bits):
    """
    Separates positive and negative coefficients, computes two dot-products,
    and subtracts negative sum from positive sum.
    """
    tm, _opt, _parser, _bvsizeB = bw_obj
    posVar, posNum, negVar, negNum = [], [], [], []
    for i in range(0, len(arrNum)):
        if arrNum[i] > 0:
            posVar.append(arrVar[i])
            posNum.append(arrNum[i])
        else:
            negVar.append(arrVar[i])
            negNum.append(arrNum[i] * -1)
    negDot = b_dot_new(negVar, negNum, bw_obj, F_prec, bits)
    posDot = b_dot_new(posVar, posNum, bw_obj, F_prec, bits)
    return tm.mk_term(bitwuzla.Kind.BV_SUB, [posDot, negDot])


def b_dot_new(arrVar, arrNum, bw_obj: BwObj, F_prec, bits):
    """
    Balanced recursive summation of term-by-term multiplications.
    For single-element lists, extends and shifts for fixed-point precision.
    """
    tm, _opt, _parser, bvsizeB = bw_obj
    ln = len(arrVar)
    if ln == 0:
        return tm.mk_bv_value(bvsizeB, 0)
    if ln == 1:
        bvsizeB_larger = tm.mk_bv_sort(bits + F_prec)
        F_btor_larger = tm.mk_bv_value(bvsizeB_larger, F_prec)
        _cnst = tm.mk_bv_value(bvsizeB_larger, arrNum[0])
        var = tm.mk_term(bitwuzla.Kind.BV_SIGN_EXTEND, [arrVar[0]], [F_prec])
        tmp = tm.mk_term(
            bitwuzla.Kind.BV_ASHR,
            [b_mul(var, arrNum[0], bw_obj, bvsizeB_larger, 0), F_btor_larger],
        )
        tmp = tm.mk_term(bitwuzla.Kind.BV_EXTRACT, [tmp], [bits - 1, 0])
        return tmp
    part = ln // 2
    return tm.mk_term(
        bitwuzla.Kind.BV_ADD,
        [
            b_dot_new(arrVar[:part], arrNum[:part], bw_obj, F_prec, bits),
            b_dot_new(arrVar[part:], arrNum[part:], bw_obj, F_prec, bits),
        ],
    )


def b_elem_mul(bw_obj, mat1, scaled_weight, F_prec, bits, isDebug=False):
    """
    Element-wise multiplication of a BV array and integer weights,
    applying sign-extend, multiply, arithmetic shift, and extract.
    """
    tm, _opt, _parser, _bvsizeB = bw_obj
    out = []
    for i in range(len(mat1)):
        if isDebug:
            breakpoint()
        bvsizeB_larger = tm.mk_bv_sort(bits + F_prec)
        F_btor_larger = tm.mk_bv_value(bvsizeB_larger, F_prec)
        _cnst = tm.mk_bv_value(bvsizeB_larger, scaled_weight[i])
        var = tm.mk_term(bitwuzla.Kind.BV_SIGN_EXTEND, [mat1[i]], [F_prec])
        tmp = tm.mk_term(
            bitwuzla.Kind.BV_ASHR,
            [b_mul(var, scaled_weight[i], bw_obj, bvsizeB_larger, 0), F_btor_larger],
        )
        tmp = tm.mk_term(bitwuzla.Kind.BV_EXTRACT, [tmp], [bits - 1, 0])
        out.append(tmp)
    return out


def b_sum(arrVar, bw_obj: BwObj, F_prec, bits):
    """
    Balanced tree addition of BV terms for efficient summing.
    """
    tm, _opt, _parser, bvsizeB = bw_obj
    ln = len(arrVar)
    if ln == 0:
        return tm.mk_bv_value(bvsizeB, 0)
    if ln == 1:
        return arrVar[0]
    part = ln // 2
    return tm.mk_term(
        bitwuzla.Kind.BV_ADD,
        [
            b_sum(arrVar[:part], bw_obj, F_prec, bits),
            b_sum(arrVar[part:], bw_obj, F_prec, bits),
        ],
    )


def b_sign_func(bw_obj: BwObj, arrVar, bits, isLast, F_prec, gap):
    """
    Compute discrete sign values (+1, 0, -1) for each term based on MSB
    and a gap threshold using ITE constructs.
    """
    # msb -> sign bit
    # Determine if x is zero
    # is_zero_v1 = (inp == 0)
    # is_zero_v2 = (gap > inp) & (inp > -gap)
    # Compute the sign: 1 for positive, 0 for zero, -1 for negative
    # sign = is_zero ? 0 : (msb ? -1 : 1)
    tm, _opt, _parser, bvsizeB = bw_obj
    signs = []
    val = 1 if isLast else 2 ** (F_prec)
    bZero = tm.mk_bv_value(bvsizeB, 0)
    bneg1 = tm.mk_bv_value(bvsizeB, -val)
    bpos1 = tm.mk_bv_value(bvsizeB, val)
    bgap = tm.mk_bv_value(bvsizeB, int(gap * 2 ** (F_prec)))
    bgap_neg = tm.mk_bv_value(bvsizeB, -int(gap * 2 ** (F_prec)))

    for i in range(len(arrVar)):
        is_zero_v1 = tm.mk_term(bitwuzla.Kind.EQUAL, [arrVar[i], bZero])
        _is_zero_v2 = tm.mk_term(
            bitwuzla.Kind.AND,
            [
                tm.mk_term(bitwuzla.Kind.BV_SGT, [bgap, arrVar[i]]),
                tm.mk_term(bitwuzla.Kind.BV_SGT, [arrVar[i], bgap_neg]),
            ],
        )
        msb = tm.mk_term(bitwuzla.Kind.BV_EXTRACT, [arrVar[i]], [bits - 1, bits - 1])
        msb = tm.mk_term(
            bitwuzla.Kind.EQUAL, [msb, tm.mk_bv_value(tm.mk_bv_sort(1), 1)]
        )
        sign = tm.mk_term(
            bitwuzla.Kind.ITE,
            [is_zero_v1, bZero, tm.mk_term(bitwuzla.Kind.ITE, [msb, bneg1, bpos1])],
        )
        signs.append(sign)

    return signs


def set_lhs_state(var, val, bw_obj: BwObj):
    """
    Build a balanced conjunction of BV equalities to assign values to state bits
    [for random sample ablation study].
    """
    tm, _opt, _parser, bvsizeB = bw_obj
    eq_this = tm.mk_term(bitwuzla.Kind.EQUAL, [var[0], tm.mk_bv_value(bvsizeB, val[0])])
    if len(var) == 1:
        return eq_this
    return tm.mk_term(
        bitwuzla.Kind.AND, [eq_this, set_lhs_state(var[1:], val[1:], bw_obj)]
    )


def b_range(var, bw_obj: BwObj, lb, ub):
    """Constrain a BitVec term within [lb, ub] using BV_UGE and BV_ULE."""
    tm, _opt, _parser, bvsizeB = bw_obj
    l1 = tm.mk_term(bitwuzla.Kind.BV_UGE, [var, tm.mk_bv_value(bvsizeB, lb)])
    u1 = tm.mk_term(bitwuzla.Kind.BV_ULE, [var, tm.mk_bv_value(bvsizeB, ub)])
    return tm.mk_term(bitwuzla.Kind.AND, [l1, u1])


def b_and(arr, bw_obj: BwObj):
    """Recursively assemble balanced AND/OR trees over lists of terms."""
    tm, _opt, _parser, _bvsizeB = bw_obj
    if len(arr) == 1:
        return arr[0]
    if len(arr) == 2:  # REMOVE THIS CASE ITS REDUNDANT
        return tm.mk_term(bitwuzla.Kind.AND, [arr[0], arr[1]])
    part = len(arr) // 2
    return tm.mk_term(
        bitwuzla.Kind.AND, [b_and(arr[:part], bw_obj), b_and(arr[part:], bw_obj)]
    )


def b_or(arr, bw_obj: BwObj):
    """Create a disjunction of conjunctions for 2D arrays of terms."""
    tm, _opt, _parser, _bvsizeB = bw_obj
    if len(arr) == 1:
        return arr[0]
    if len(arr) == 2:  # REMOVE THIS CASE ITS REDUNDANT
        return tm.mk_term(bitwuzla.Kind.OR, [arr[0], arr[1]])
    part = len(arr) // 2
    return tm.mk_term(
        bitwuzla.Kind.OR, [b_or(arr[:part], bw_obj), b_or(arr[part:], bw_obj)]
    )


def b_or_of_and(arr2D, bw_obj: BwObj):
    """Decode Bitwuzla BitVec results into Python integers (b_int’s complement)."""
    arr1D = []
    for arr in arr2D:
        arr1D.append(b_and(arr, bw_obj))
    return b_or(arr1D, bw_obj)


def b_int(arr, bw_obj: BwObj, bits):
    arr2 = []
    for i in range(len(arr)):
        arr2.append(to_decimal(arr[i], bw_obj, bits))
    return arr2


def to_decimal(x, bw_obj: BwObj, bits):
    _tm, _opt, parser, _bvsizeB = bw_obj
    val = int(parser.bitwuzla().get_value(x).value(10))
    s = 1 << (bits - 1)
    return (val & s - 1) - (val & s)


def b_set(arr, var, val, context: BwContext):
    """Generate (or negate) equality constraints for named state/input variables."""
    state_vars, inp_out_vars, bw_obj, _bits = context
    tm, _opt, _parser, bvsizeB = bw_obj
    assert (var in state_vars.keys()) or (var in inp_out_vars.keys())
    var_keys = state_vars.keys() if (var in state_vars.keys()) else inp_out_vars.keys()
    return tm.mk_term(
        bitwuzla.Kind.EQUAL,
        [arr[[svk for svk in var_keys].index(var)], tm.mk_bv_value(bvsizeB, val)],
    )


def b_unset(arr, var, val, context: BwContext):
    _state_vars, _inp_out_vars, bw_obj, _bits = context
    tm, _opt, _parser, _bvsizeB = bw_obj
    return tm.mk_term(bitwuzla.Kind.NOT, [b_set(arr, var, val, context)])


def bitwuzla_print(arr, bw_obj: BwObj, *args, **kwargs):
    """Print term symbols and values or formula strings for debugging."""
    _tm, _opt, parser, _bvsizeB = bw_obj
    for ar in arr:
        value = parser.bitwuzla().get_value(ar).value(10)
        print(f" {ar.symbol()} --> {value} ", *args, **kwargs)


def bitwuzla_print_formula(trm, *args, **kwargs):
    print(trm.str(), *args, **kwargs)
