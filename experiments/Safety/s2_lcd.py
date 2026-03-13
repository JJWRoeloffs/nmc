N_lims = [
    500,
    1000,
    1500,
    2500,
    5000,
    7500,
    10000,
    12500,
    15000,
    17500,
    20000,
    22500,
    90000,
    180000,
]
CBITSs = [9, 10, 11, 12, 13, 13, 14, 14, 14, 15, 15, 15, 17, 18]
specTXT = "XG ((X state1) -> (busy))"
module_name = "LCD"
file_name = "lcd"
LTLSpec = "LTLSPEC X G ( X ( Verilog.LCD.state[1] = FALSE &  Verilog.LCD.state[0] = TRUE)  ->  (Verilog.LCD.busy = TRUE))"
SVSpec = "(@(posedge clk) s_nexttime ((s_nexttime state==1) implies busy))"


start_ex = 0
scale = 1
size = [2]  # [2, 1]
gap = 1e-4  # this is the gap of the sign activation function
F_prec = 5
bits = 50
Ps = [5 for N_lim in N_lims]
Ms = [N_lim * 2 for N_lim in N_lims]

is_acc = [0, 0, 0, 1]
is_init = [1, 0, 0, 0]
init_samp = [(0, [float(0), float(0)])]

try:
    import nur
except ImportError:
    print("Library nur not found. Not exporting spec_automata function")
else:

    def spec_automata(ctx, q_cur, curr_vars, V0, q_nex, next_vars, V1, non_state, s):
        _, _, bw_obj, _ = ctx
        cases = []

        if q_cur == 0 and q_nex == 1:
            cases.append([])

        elif q_cur == 1 and q_nex == 1:
            cases.append([nur.Bset(non_state, "busy", 1, ctx)])
        elif q_cur == 1 and q_nex == 2:
            cases.append([nur.BUnSet(non_state, "busy", 1, ctx)])

        elif q_cur == 2 and q_nex == 2:
            cases.append(
                [
                    nur.BUnSet(non_state, "busy", 1, ctx),
                    nur.BUnSet(curr_vars, "state", 1, ctx),
                ]
            )
        elif q_cur == 2 and q_nex == 1:
            cases.append(
                [
                    nur.Bset(non_state, "busy", 1, ctx),
                    nur.BUnSet(curr_vars, "state", 1, ctx),
                ]
            )
        elif q_cur == 2 and q_nex == 3:
            cases.append([nur.Bset(curr_vars, "state", 1, ctx)])

        elif q_cur == 3 and q_nex == 3:
            cases.append([])

        return cases
