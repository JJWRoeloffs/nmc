N_lims = [2**8, 2**9, 2**10, 2**11, 2**12, 2**13, 2**14, 2**15, 2**16, 2**17, 2**18]
CBITSs = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
specTXT = "FG !rst -> GF (sig & X !sig)"
module_name = "GRAY"
file_name = "gray"
LTLSpec = "LTLSPEC F G (Verilog.GRAY.rst = FALSE) -> G F (Verilog.GRAY.sig = TRUE & X Verilog.GRAY.sig = FALSE)"
SVSpec = "(@(posedge clk) s_eventually (!rst implies (sig and s_nexttime !sig)))"

start_ex = 0

scale = 1
size = [1]  # [1]
gap = 1e-3  # this is the gap of the sign activation function
F_prec = 5
bits = 100

Ps = [N_lim + 1 for N_lim in N_lims]
Ms = [N_lim * 2 for N_lim in N_lims]

is_acc = [0, 1, 1]
is_init = [1, 0, 0]
init_samp = [(0, [float(0)])]

try:
    import nur
except ImportError:
    print("Library nur not found. Not exporting spec_automata function")
else:

    def spec_automata(
        ctx, q_cur, curr_vars, V0, q_nex, next_vars, V1, non_state_vars, s
    ):
        cases = []
        if q_cur == 0 and q_nex == 0:
            cases.append([])
        elif q_cur == 0 and q_nex == 1:
            cases.append(
                [
                    nur.BUnSet(non_state_vars, "sig", 1, ctx),
                    nur.Bset(non_state_vars, "rst", 0, ctx),
                ]
            )
        elif q_cur == 0 and q_nex == 2:
            cases.append(
                [
                    nur.Bset(non_state_vars, "sig", 1, ctx),
                    nur.Bset(non_state_vars, "rst", 0, ctx),
                ]
            )
        elif q_cur == 1 and q_nex == 1:
            cases.append(
                [
                    nur.BUnSet(non_state_vars, "sig", 1, ctx),
                    nur.Bset(non_state_vars, "rst", 0, ctx),
                ]
            )
        elif q_cur == 1 and q_nex == 2:
            cases.append(
                [
                    nur.Bset(non_state_vars, "sig", 1, ctx),
                    nur.Bset(non_state_vars, "rst", 0, ctx),
                ]
            )
        elif q_cur == 2 and q_nex == 2:
            cases.append(
                [
                    nur.Bset(non_state_vars, "sig", 1, ctx),
                    nur.Bset(non_state_vars, "rst", 0, ctx),
                ]
            )
        return cases
