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

specTXT = "FG !rst -> (GF ds)"
module_name = "SEVEN"
file_name = "seven_seg"

LTLSpec = "LTLSPEC F G (Verilog.SEVEN.rst = FALSE) -> (G F (Verilog.SEVEN.digit_select = TRUE))"
SVSpec = "(@(posedge clk) s_eventually !rst -> digit_select)"

scale = 1
size = [2]  # [2, 1]
gap = 1e-3  # this is the gap of the sign activation function
F_prec = 5
bits = 50
start_ex = 0

Ps = [N_lim * 2 for N_lim in N_lims]
Ms = [N_lim * 2 for N_lim in N_lims]
is_acc = [0, 1]
is_init = [1, 0]
init_samp = [(0, [float(0), float(1)])]

try:
    import nur
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
                    nur.BUnSet(curr_vars, "digit_select", 1, ctx),
                    nur.Bset(non_state, "rst", 0, ctx),
                ]
            )
        elif q_cur == 1 and q_nex == 1:
            cases.append(
                [
                    nur.BUnSet(curr_vars, "digit_select", 1, ctx),
                    nur.Bset(non_state, "rst", 0, ctx),
                ]
            )
        return cases
