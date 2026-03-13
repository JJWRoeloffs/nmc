N_lims = [
    250,
    500,
    750,
    1000,
    2500,
    5000,
    7500,
    10000,
    12500,
    15000,
    17500,
    20000,
    40000,
    80000,
    160000,
]
CBITSs = [0] * len(N_lims)  # unused beside size

specTXT = "X G ((!sig & X !sig & !rst) -> ( (!ds & X !ds) | (ds & X ds) ) )"
module_name = "SEVEN"
file_name = "seven_seg"

LTLSpec = "LTLSPEC X G ((Verilog.SEVEN.sig = FALSE & X Verilog.SEVEN.sig = FALSE & Verilog.SEVEN.rst = FALSE) -> ( (Verilog.SEVEN.digit_select = TRUE & X Verilog.SEVEN.digit_select = TRUE) | (Verilog.SEVEN.digit_select = FALSE & X Verilog.SEVEN.digit_select = FALSE) ) )"
SVSpec = "(@(posedge clk) (!sig and !rst and s_nexttime !sig) implies (digit_select iff s_nexttime digit_select))"

scale = 1
size = [2]  # [2, 1]
gap = 1e-3  # this is the gap of the sign activation function
F_prec = 5
bits = 50
start_ex = 0

Ps = [10 for N_lim in N_lims]
Ms = [N_lim * 2 for N_lim in N_lims]

is_acc = [0, 0, 0, 0, 1]
is_init = [1, 0, 0, 0, 0]
init_samp = [(0, [float(0), float(1)])]

try:
    from nur.bitwuzla_utils import b_set, b_unset
except ImportError:
    print("Library nur not found. Not exporting spec_automata function")
else:

    def spec_automata(ctx, q_cur, curr_vars, V0, q_nex, next_vars, V1, non_state, s):
        _, _, bw_obj, _ = ctx
        cases = []

        if q_cur == 0 and q_nex == 1:
            cases.append([])  # Transition from start state

        elif q_cur == 1 and q_nex == 1:
            cases.append(
                [
                    nur.bOr(
                        [
                            b_set(non_state, "rst", 1, ctx),
                            b_set(non_state, "sig", 1, ctx),
                        ],
                        bw_obj,
                    )
                ]
            )
        elif q_cur == 1 and q_nex == 2:
            cases.append(
                [
                    b_unset(non_state, "rst", 1, ctx),
                    b_unset(non_state, "sig", 1, ctx),
                    b_unset(curr_vars, "digit_select", 1, ctx),
                ]
            )

        elif q_cur == 1 and q_nex == 3:
            cases.append(
                [
                    b_unset(non_state, "rst", 1, ctx),
                    b_unset(non_state, "sig", 1, ctx),
                    b_set(curr_vars, "digit_select", 1, ctx),
                ]
            )

        elif q_cur == 2 and q_nex == 1:
            cases.append(
                [
                    b_set(non_state, "rst", 1, ctx),
                    b_unset(curr_vars, "digit_select", 1, ctx),
                ]
            )
            cases.append([b_set(non_state, "sig", 1, ctx)])

        elif q_cur == 2 and q_nex == 2:
            cases.append(
                [
                    b_unset(non_state, "rst", 1, ctx),
                    b_unset(non_state, "sig", 1, ctx),
                    b_unset(curr_vars, "digit_select", 1, ctx),
                ]
            )
        elif q_cur == 2 and q_nex == 4:
            cases.append(
                [
                    b_unset(non_state, "sig", 1, ctx),
                    b_set(curr_vars, "digit_select", 1, ctx),
                ]
            )

        elif q_cur == 3 and q_nex == 1:
            cases.append(
                [
                    b_set(non_state, "rst", 1, ctx),
                    b_set(curr_vars, "digit_select", 1, ctx),
                ]
            )
            cases.append([b_set(non_state, "sig", 1, ctx)])

        elif q_cur == 3 and q_nex == 3:
            cases.append(
                [
                    b_unset(non_state, "rst", 1, ctx),
                    b_unset(non_state, "sig", 1, ctx),
                    b_set(curr_vars, "digit_select", 1, ctx),
                ]
            )
        elif q_cur == 3 and q_nex == 4:
            cases.append(
                [
                    b_unset(non_state, "sig", 1, ctx),
                    b_unset(curr_vars, "digit_select", 1, ctx),
                ]
            )

        elif q_cur == 4 and q_nex == 4:
            cases.append([])

        return cases
