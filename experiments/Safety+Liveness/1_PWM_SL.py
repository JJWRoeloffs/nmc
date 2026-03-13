N_lims = [
    2**10,
    2**11,
    2**12,
    2**13,
    2**14,
    2**15,
    2**16,
    2**17,
    2**18,
    2**19,
    2**20,
    2**21,
]
CBITSs = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]
specTXT = "GF !ub_p & X G (!ub_p -> !pulse)"
module_name = "PWM_TOP"

file_name = "PWM"
LTLSpec = "LTLSPEC G F (Verilog.PWM_TOP.ub_pulse = FALSE) & X G (Verilog.PWM_TOP.ub_pulse = FALSE -> Verilog.PWM_TOP.pulse_red = FALSE)"
SVSpec = None

start_ex = 0

scale = 1
size = [1]  # [1, 1]
gap = 1e-3  # this is the gap of the sign activation function
F_prec = 5
bits = 50

Ps = [10 for N_lim in N_lims]
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
        if q_cur == 0 and q_nex == 1:
            cases.append([])

        elif q_cur == 1 and q_nex == 1:
            cases.append([nur.Bset(non_state, "ub_pulse", 1, ctx)])
            cases.append([nur.BUnSet(non_state, "pulse_red", 1, ctx)])
        elif q_cur == 1 and q_nex == 2:
            cases.append(
                [
                    nur.BUnSet(non_state, "ub_pulse", 1, ctx),
                    nur.Bset(non_state, "pulse_red", 1, ctx),
                ]
            )
        elif q_cur == 1 and q_nex == 3:
            cases.append([nur.Bset(non_state, "ub_pulse", 1, ctx)])

        elif q_cur == 2 and q_nex == 2:
            cases.append([])

        elif q_cur == 3 and q_nex == 3:
            cases.append([nur.Bset(non_state, "ub_pulse", 1, ctx)])
        return cases
