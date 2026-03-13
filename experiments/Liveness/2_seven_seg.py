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

specTXT = "FG !rst -> (GF ds & GF !ds)"
module_name = "SEVEN"
file_name = "seven_seg"

LTLSpec = "LTLSPEC F G (Verilog.SEVEN.rst = FALSE) -> ( (G F (Verilog.SEVEN.digit_select = FALSE)) & (G F (Verilog.SEVEN.digit_select = TRUE)))"
SVSpec = "(@(posedge clk) s_eventually !rst implies ((s_eventually digit_select) and (s_eventually !digit_select)))"

scale = 1
size = [2]  # [2]
gap = 1e-3  # this is the gap of the sign activation function
F_prec = 5
bits = 50
start_ex = 0

Ps = [N_lim * 2 for N_lim in N_lims[:7]] + [N_lim * 4 for N_lim in N_lims[7:]]
Ms = [N_lim * 2 for N_lim in N_lims]

is_acc = [0, 1, 1]
is_init = [1, 0, 0]
init_samp = [(0, [float(0), float(1)])]


try:
    from nur.bitwuzla_utils import b_set, b_unset
except ImportError:
    print("Library nur not found. Not exporting spec_automata function")
else:

    def spec_automata(ctx, q_cur, curr_vars, V0, q_nex, next_vars, V1, non_state, s):
        cases = []
        if q_cur == 0 and q_nex == 0:
            cases.append([])
        elif q_cur == 0 and q_nex == 1:
            cases.append(
                [
                    b_unset(curr_vars, "digit_select", 1, ctx),
                    b_set(non_state, "rst", 0, ctx),
                ]
            )
        elif q_cur == 1 and q_nex == 1:
            cases.append(
                [
                    b_unset(curr_vars, "digit_select", 1, ctx),
                    b_set(non_state, "rst", 0, ctx),
                ]
            )
        elif q_cur == 0 and q_nex == 2:
            cases.append(
                [
                    b_unset(curr_vars, "digit_select", 0, ctx),
                    b_set(non_state, "rst", 0, ctx),
                ]
            )
        elif q_cur == 2 and q_nex == 2:
            cases.append(
                [
                    b_unset(curr_vars, "digit_select", 0, ctx),
                    b_set(non_state, "rst", 0, ctx),
                ]
            )
        return cases
