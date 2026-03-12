Mults = [1, 2, 3, 4, 5, 6, 8, 10, 12, 16]
specTXT = "F G ! rst-> G F disp_ena"
module_name = "VGA"

N_lims = [0] * len(Mults)  # Only size of array needed
CBITSs = [0] * len(Mults)  # Only size of array needed

file_name = "vga"
LTLSpec = "LTLSPEC F G (Verilog.VGA.rst = FALSE) -> G F (Verilog.VGA.disp_ena = TRUE)"
SVSpec = "(@(posedge clk) s_eventually !rst -> disp_ena)"
range_vals_list = ["N"] * 100

start_ex = 0

scale = 1
size = [4]  # [4, 1]
gap = 1e-4  # this is the gap of the sign activation function
F_prec = 5
bits = 50

Ps = [1 for Mult in Mults]
Ms = [Mult * 66 * 2 for Mult in Mults]
is_acc = [0, 1]
is_init = [1, 0]
init_samp = [(0, [float(0), float(0), float(0), float(0)])]


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
                    nur.BUnSet(non_state, "disp_ena", 0, ctx),
                    nur.Bset(non_state, "rst", 0, ctx),
                ]
            )
        elif q_cur == 1 and q_nex == 1:
            cases.append(
                [
                    nur.BUnSet(non_state, "disp_ena", 0, ctx),
                    nur.Bset(non_state, "rst", 0, ctx),
                ]
            )
        return cases
