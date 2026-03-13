N_lims = [2**pr for pr in range(8, 33)]
CBITSs = [pr for pr in range(8, 33)]
specTXT = "G !rst -> G(led -> (led U !mode1))"
module_name = "BLINK"
file_name = "blink"
LTLSpec = "LTLSPEC G Verilog.BLINK.rst = FALSE -> G ( Verilog.BLINK.led = TRUE -> (Verilog.BLINK.led = TRUE U Verilog.BLINK.mode = FALSE))"
SVSpec = "(@(posedge clk) !rst implies always (led implies (led s_until !mode)))"

start_ex = 0

scale = 1
size = [2]  # [2, 1]
gap = 1e-3  # this is the gap of the sign activation function
F_prec = 5
bits = 100

Ps = [N_lim for N_lim in N_lims]
Ms = [N_lim * 2 for N_lim in N_lims]

is_acc = [0, 1, 1]
is_init = [1, 0, 0]
init_samp = [(0, [float(0), float(0)])]


try:
    import nur
except ImportError:
    print("Library nur not found. Not exporting spec_automata function")
else:

    def spec_automata(ctx, q_cur, curr_vars, V0, q_nex, next_vars, V1, non_state, s):
        cases = []
        if q_cur == 0 and q_nex == 0:
            cases.append([nur.Bset(non_state, "rst", 0, ctx)])

        elif q_cur == 0 and q_nex == 1:
            cases.append(
                [
                    nur.Bset(non_state, "rst", 0, ctx),
                    nur.Bset(curr_vars, "mode", 1, ctx),
                    nur.Bset(non_state, "led", 1, ctx),
                ]
            )
        elif q_cur == 1 and q_nex == 1:
            cases.append(
                [
                    nur.Bset(non_state, "rst", 0, ctx),
                    nur.Bset(curr_vars, "mode", 1, ctx),
                    nur.Bset(non_state, "led", 1, ctx),
                ]
            )

        elif q_cur == 1 and q_nex == 2:
            cases.append(
                [
                    nur.Bset(non_state, "rst", 0, ctx),
                    nur.Bset(curr_vars, "mode", 1, ctx),
                    nur.BUnSet(non_state, "led", 1, ctx),
                ]
            )

        if q_cur == 2 and q_nex == 2:
            cases.append([nur.Bset(non_state, "rst", 0, ctx)])

        return cases
