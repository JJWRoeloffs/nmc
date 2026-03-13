N_lims = [
    30,
    300,
    600,
    900,
    1200,
    1800,
    2400,
    3000,
    6000,
    9000,
    12000,
    15000,
    18000,
    36000,
    72000,
    144000,
    288000,
]
CBITSs = [0] * len(N_lims)
specTXT = "FG !rst -> (GF state = 1)"
module_name = "Thermocouple"
file_name = "thermocouple"

LTLSpec = "LTLSPEC F G (Verilog.Thermocouple.rst = FALSE) -> G F (Verilog.Thermocouple.state[1] = FALSE & Verilog.Thermocouple.state[0] = TRUE)"
SVSpec = "(@(posedge clk) s_eventually !rst -> state)"

start_ex = 0
scale = 1
size = [3]  # [1, 1]
gap = 1e-3  # this is the gap of the sign activation function
F_prec = 5
bits = 50

Ps = [1 for N_lim in N_lims]
Ms = [N_lim * 2 for N_lim in N_lims]

is_acc = [0, 1]
is_init = [1, 0]
init_samp = [(0, [float(0), float(0), float(0)])]

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
                    nur.BUnSet(curr_vars, "state", 1, ctx),
                    nur.Bset(non_state, "rst", 0, ctx),
                    nur.BUnSet(next_vars, "state", 1, ctx),
                ]
            )
        elif q_cur == 1 and q_nex == 1:
            cases.append(
                [
                    nur.BUnSet(curr_vars, "state", 1, ctx),
                    nur.Bset(non_state, "rst", 0, ctx),
                    nur.BUnSet(next_vars, "state", 1, ctx),
                ]
            )
        return cases
