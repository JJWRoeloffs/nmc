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
specTXT = "(FG !rst -> F G (flg U sig))"
module_name = "DELAY"
file_name = "delay"
LTLSpec = "LTLSPEC F G (Verilog.DELAY.rst = FALSE) -> F G ((Verilog.DELAY.flg = TRUE) U (Verilog.DELAY.sig = TRUE))"
SVSpec = "(@(posedge clk) (s_eventually always !rst) implies s_eventually always (flg s_until sig))"
range_vals_list = ["N", "N", "N", "N", "N"]

start_ex = 0
scale = 1
size = [1]  # [1, 1]
gap = 1e-2  # this is the gap of the sign activation function
F_prec = 5
bits = 50
Ps = [1 for N_lim in N_lims]
Ms = [N_lim * 2 for N_lim in N_lims]

is_acc = [0, 0, 1, 1]
is_init = [1, 0, 0, 0]
init_samp = [(0, [float(0)])]

try:
    import nur
except ImportError:
    print("Library nur not found. Not exporting spec_automata function")
else:

    def spec_automata(ctx, q_cur, curr_vars, V0, q_nex, next_vars, V1, non_state, s):
        cases = []
        if q_cur == 0 and q_nex == 0:
            cases.append([])

        elif q_cur == 0 and q_nex == 2:
            cases.append(
                [
                    nur.Bset(non_state, "rst", 0, ctx),
                    nur.BUnSet(non_state, "sig", 1, ctx),
                    nur.BUnSet(non_state, "flg", 1, ctx),
                ]
            )
        elif q_cur == 0 and q_nex == 3:
            cases.append(
                [
                    nur.Bset(non_state, "rst", 0, ctx),
                    nur.BUnSet(non_state, "sig", 1, ctx),
                    nur.Bset(non_state, "flg", 1, ctx),
                ]
            )

        elif q_cur == 2 and q_nex == 1:
            cases.append(
                [nur.Bset(non_state, "rst", 0, ctx), nur.Bset(non_state, "sig", 1, ctx)]
            )
            cases.append(
                [nur.Bset(non_state, "rst", 0, ctx), nur.Bset(non_state, "flg", 1, ctx)]
            )
        elif q_cur == 2 and q_nex == 2:
            cases.append(
                [
                    nur.Bset(non_state, "rst", 0, ctx),
                    nur.BUnSet(non_state, "sig", 1, ctx),
                    nur.BUnSet(non_state, "flg", 1, ctx),
                ]
            )
        elif q_cur == 2 and q_nex == 3:
            cases.append(
                [
                    nur.Bset(non_state, "rst", 0, ctx),
                    nur.BUnSet(non_state, "sig", 1, ctx),
                    nur.Bset(non_state, "flg", 1, ctx),
                ]
            )

        elif q_cur == 3 and q_nex == 1:
            cases.append(
                [
                    nur.Bset(non_state, "rst", 0, ctx),
                    nur.BUnSet(non_state, "sig", 1, ctx),
                    nur.BUnSet(non_state, "flg", 1, ctx),
                ]
            )
        elif q_cur == 3 and q_nex == 3:
            cases.append(
                [
                    nur.Bset(non_state, "rst", 0, ctx),
                    nur.BUnSet(non_state, "sig", 1, ctx),
                    nur.Bset(non_state, "flg", 1, ctx),
                ]
            )

        elif q_cur == 1 and q_nex == 1:
            cases.append(
                [nur.Bset(non_state, "rst", 0, ctx), nur.Bset(non_state, "sig", 1, ctx)]
            )
            cases.append(
                [nur.Bset(non_state, "rst", 0, ctx), nur.Bset(non_state, "flg", 1, ctx)]
            )
        elif q_cur == 1 and q_nex == 2:
            cases.append(
                [
                    nur.Bset(non_state, "rst", 0, ctx),
                    nur.BUnSet(non_state, "sig", 1, ctx),
                    nur.BUnSet(non_state, "flg", 1, ctx),
                ]
            )
        elif q_cur == 1 and q_nex == 3:
            cases.append(
                [
                    nur.Bset(non_state, "rst", 0, ctx),
                    nur.BUnSet(non_state, "sig", 1, ctx),
                    nur.Bset(non_state, "flg", 1, ctx),
                ]
            )

        return cases
