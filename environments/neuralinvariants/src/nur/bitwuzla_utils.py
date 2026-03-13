import bitwuzla


def set_lhs_state(var, val, bw_obj):
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


def b_range(var, bw_obj, lb, ub):
    """Constrain a BitVec term within [lb, ub] using BV_UGE and BV_ULE."""
    tm, _opt, _parser, bvsizeB = bw_obj
    l1 = tm.mk_term(bitwuzla.Kind.BV_UGE, [var, tm.mk_bv_value(bvsizeB, lb)])
    u1 = tm.mk_term(bitwuzla.Kind.BV_ULE, [var, tm.mk_bv_value(bvsizeB, ub)])
    return tm.mk_term(bitwuzla.Kind.AND, [l1, u1])


def b_and(arr, bw_obj):
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


def b_or(arr, bw_obj):
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


def b_or_of_and(arr2D, bw_obj):
    """Decode Bitwuzla BitVec results into Python integers (two’s complement)."""
    arr1D = []
    for arr in arr2D:
        arr1D.append(b_and(arr, bw_obj))
    return b_or(arr1D, bw_obj)


def b_int(arr, bw_obj, bits):
    arr2 = []
    for i in range(len(arr)):
        arr2.append(to_decimal(arr[i], bw_obj, bits))
    return arr2


def to_decimal(x, bw_obj, bits):
    _tm, _opt, parser, _bvsizeB = bw_obj
    val = int(parser.bitwuzla().get_value(x).value(10))
    s = 1 << (bits - 1)
    return (val & s - 1) - (val & s)


def b_set(arr, var, val, context):
    """Generate (or negate) equality constraints for named state/input variables."""
    state_vars, inp_out_vars, bw_obj, _bits = context
    tm, _opt, _parser, bvsizeB = bw_obj
    assert (var in state_vars.keys()) or (var in inp_out_vars.keys())
    var_keys = state_vars.keys() if (var in state_vars.keys()) else inp_out_vars.keys()
    return tm.mk_term(
        bitwuzla.Kind.EQUAL,
        [arr[[svk for svk in var_keys].index(var)], tm.mk_bv_value(bvsizeB, val)],
    )


def b_unset(arr, var, val, context):
    _state_vars, _inp_out_vars, bw_obj, _bits = context
    tm, _opt, _parser, _bvsizeB = bw_obj
    return tm.mk_term(bitwuzla.Kind.NOT, [b_set(arr, var, val, context)])


def bitwuzla_print(arr, bw_obj, *args, **kwargs):
    """Print term symbols and values or formula strings for debugging."""
    _tm, _opt, parser, _bvsizeB = bw_obj
    for ar in arr:
        value = parser.bitwuzla().get_value(ar).value(10)
        print(f" {ar.symbol()} --> {value} ", *args, **kwargs)


def bitwuzla_print_formula(trm, *args, **kwargs):
    print(trm.str(), *args, **kwargs)
