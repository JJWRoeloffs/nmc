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
specTXT = "XG (sig -> X X !sig)"
module_name = "Load_Store"
file_name = "load_store"
LTLSpec = (
    "LTLSPEC X G (Verilog.Load_Store.sig = TRUE  -> X X Verilog.Load_Store.sig = FALSE)"
)
SVSpec = "(@(posedge clk) s_nexttime (sig |-> ##2 !sig))"

scale = 1
size = [2]  # [2, 1]
gap = 1e-3  # this is the gap of the sign activation function
F_prec = 5
bits = 50
start_ex = 0

Ps = [N_lim for N_lim in N_lims[:7]] + [N_lim * 2 for N_lim in N_lims[7:]]
Ms = [N_lim * 2 for N_lim in N_lims]

is_acc = [0, 0, 0, 0, 1]
is_init = [1, 0, 0, 0, 0]
init_samp = [(0, [float(0), float(1)])]

try:
    import nur
except ImportError:
    print("Library nur not found. Not exporting spec_automata function")
else:

    def spec_automata(ctx, q_cur, curr_vars, V0, q_nex, next_vars, V1, non_state, s):
        cases = []
        if q_cur == 0 and q_nex == 1:
            cases.append([])

        elif q_cur == 1 and q_nex == 1:
            cases.append([])
        elif q_cur == 1 and q_nex == 2:
            cases.append([nur.Bset(non_state, "sig", 1, ctx)])

        elif q_cur == 2 and q_nex == 3:
            cases.append([])

        elif q_cur == 3 and q_nex == 4:
            cases.append([nur.Bset(non_state, "sig", 1, ctx)])

        elif q_cur == 4 and q_nex == 4:
            cases.append([])
        return cases
