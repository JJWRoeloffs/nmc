Mults = [1, 2, 3, 4, 5, 6, 8, 10, 12, 16]
specTXT = "G (Vcnt0 -> (Vcnt0 U Hcnt0))))"
module_name = "VGA"

N_lims = [0] * len(Mults)  # Only size of array needed
CBITSs = [0] * len(Mults)  # Only size of array needed

file_name = "vga"
LTLSpec = "LTLSPEC G ((Verilog.VGA.v_cnt[0] = FALSE & Verilog.VGA.v_cnt[1] = FALSE & Verilog.VGA.v_cnt[2] = FALSE & Verilog.VGA.v_cnt[3] = FALSE & Verilog.VGA.v_cnt[4] = FALSE) -> ((Verilog.VGA.v_cnt[0] = FALSE & Verilog.VGA.v_cnt[1] = FALSE & Verilog.VGA.v_cnt[2] = FALSE & Verilog.VGA.v_cnt[3] = FALSE & Verilog.VGA.v_cnt[4] = FALSE) U (Verilog.VGA.h_cnt[0] = FALSE & Verilog.VGA.h_cnt[1] = FALSE & Verilog.VGA.h_cnt[2] = FALSE & Verilog.VGA.h_cnt[3] = FALSE & Verilog.VGA.h_cnt[4] = FALSE & Verilog.VGA.h_cnt[5] = FALSE & Verilog.VGA.h_cnt[6] = FALSE)))"
SVSpec = "(@(posedge clk) v_cnt==0 implies (v_cnt==0 s_until h_cnt==0))"

start_ex = 0

scale = 1
size = [4]  # [4, 1]
gap = 1e-4  # this is the gap of the sign activation function
F_prec = 5
bits = 50

Ps = [10 for Mult in Mults]
Ms = [Mult * 66 * 2 for Mult in Mults]

is_acc = [0, 1, 1]
is_init = [1, 0, 0]
init_samp = [(0, [float(0), float(0), float(0), float(0)])]

try:
    import nur
except ImportError:
    print("Library nur not found. Not exporting spec_automata function")
else:

    def spec_automata(ctx, q_cur, curr_vars, V0, q_nex, next_vars, V1, non_state, s):
        _, _, bw_obj, _ = ctx
        cases = []

        if q_cur == 0 and q_nex == 0:
            cases.append([])

        elif q_cur == 0 and q_nex == 1:
            cases.append(
                [
                    nur.BUnSet(curr_vars, "h_cnt", 0, ctx),
                    nur.Bset(curr_vars, "v_cnt", 0, ctx),
                    nur.BUnSet(next_vars, "h_cnt", 0, ctx),
                    nur.Bset(next_vars, "v_cnt", 0, ctx),
                ]
            )

            cases.append(
                [
                    nur.BUnSet(curr_vars, "h_cnt", 0, ctx),
                    nur.Bset(curr_vars, "v_cnt", 0, ctx),
                    nur.BUnSet(next_vars, "h_cnt", 0, ctx),
                    nur.BUnSet(next_vars, "v_cnt", 0, ctx),
                ]
            )

        elif q_cur == 1 and q_nex == 1:
            cases.append(
                [
                    nur.BUnSet(curr_vars, "h_cnt", 0, ctx),
                    nur.Bset(curr_vars, "v_cnt", 0, ctx),
                    nur.BUnSet(next_vars, "h_cnt", 0, ctx),
                    nur.Bset(next_vars, "v_cnt", 0, ctx),
                ]
            )

            cases.append(
                [
                    nur.BUnSet(curr_vars, "h_cnt", 0, ctx),
                    nur.Bset(curr_vars, "v_cnt", 0, ctx),
                    nur.BUnSet(next_vars, "h_cnt", 0, ctx),
                    nur.BUnSet(next_vars, "v_cnt", 0, ctx),
                ]
            )

        elif q_cur == 1 and q_nex == 2:
            cases.append(
                [
                    nur.BUnSet(curr_vars, "h_cnt", 0, ctx),
                    nur.BUnSet(curr_vars, "v_cnt", 0, ctx),
                ]
            )

        elif q_cur == 2 and q_nex == 2:
            cases.append([])

        return cases
