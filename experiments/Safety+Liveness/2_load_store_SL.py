N_lims = [
    750,
    1250,
    2500,
    5000,
    7500,
    10000,
    12500,
    15000,
    17500,
    20000,
    22500,
    25000,
    50000,
    100000,
    200000,
    400000,
]
CBITSs = [10, 11, 12, 13, 13, 14, 14, 14, 15, 15, 15, 15, 16, 17, 18, 19]
specTXT = "G !rst -> X G (m -> (!s U X !m))"
module_name = "Load_Store"
file_name = "load_store"
LTLSpec = "LTLSPEC G (Verilog.Load_Store.rst = FALSE) -> X G  (((Verilog.Load_Store.m = TRUE) -> (Verilog.Load_Store.sig = FALSE U (X Verilog.Load_Store.m = FALSE))))"
SVSpec = "(@(posedge clk) (always !rst) implies s_nexttime always (m implies (!sig s_until s_nexttime !m)))"

scale = 1
size = [2]  # [2, 1]
gap = 1e-3  # this is the gap of the sign activation function
F_prec = 5
bits = 50
start_ex = 0

Ps = [10 for N_lim in N_lims]
Ms = [N_lim * 2 for N_lim in N_lims]

is_acc = [0, 0, 1, 0, 1]
is_init = [1, 0, 0, 0, 0]
init_samp = [(0, [float(0), float(1)])]

try:
    from nur.bitwuzla_utils import b_set, b_unset
except ImportError:
    print("Library nur not found. Not exporting spec_automata function")
else:

    def spec_automata(ctx, q_cur, curr_vars, V0, q_nex, next_vars, V1, non_state, s):
        cases = []
        if q_cur == 0 and q_nex == 1:
            cases.append([b_set(non_state, "rst", 0, ctx)])

        elif q_cur == 1 and q_nex == 1:
            cases.append([b_set(non_state, "rst", 0, ctx)])
        elif q_cur == 1 and q_nex == 2:
            cases.append(
                [
                    b_set(non_state, "rst", 0, ctx),
                    b_unset(non_state, "sig", 1, ctx),
                    b_set(curr_vars, "m", 1, ctx),
                ]
            )
        elif q_cur == 1 and q_nex == 3:
            cases.append(
                [
                    b_set(non_state, "rst", 0, ctx),
                    b_set(non_state, "sig", 1, ctx),
                    b_set(curr_vars, "m", 1, ctx),
                ]
            )

        elif q_cur == 2 and q_nex == 2:
            cases.append(
                [
                    b_set(non_state, "rst", 0, ctx),
                    b_unset(non_state, "sig", 1, ctx),
                    b_set(curr_vars, "m", 1, ctx),
                ]
            )
        elif q_cur == 2 and q_nex == 3:
            cases.append(
                [
                    b_set(non_state, "rst", 0, ctx),
                    b_set(non_state, "sig", 1, ctx),
                    b_set(curr_vars, "m", 1, ctx),
                ]
            )

        elif q_cur == 3 and q_nex == 4:
            cases.append(
                [b_set(non_state, "rst", 0, ctx), b_set(curr_vars, "m", 1, ctx)]
            )

        if q_cur == 4 and q_nex == 4:
            cases.append([b_set(non_state, "rst", 0, ctx)])
        return cases
