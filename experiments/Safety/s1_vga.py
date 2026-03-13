Mults = [1, 2, 3, 4, 5, 6, 8, 10, 12, 16]
specTXT = "X G ((disp_ena & !rst) -> ((h_sync <-> X !h_sync) | (!h_sync <-> X h_sync)))"
module_name = "VGA"

N_lims = [0] * len(Mults)  # Only size of array needed
CBITSs = [0] * len(Mults)  # Only size of array needed

file_name = "vga"
LTLSpec = "LTLSPEC X G ((Verilog.VGA.disp_ena = TRUE & Verilog.VGA.rst = FALSE) -> ((Verilog.VGA.h_sync = TRUE <-> X Verilog.VGA.h_sync = FALSE) | (Verilog.VGA.h_sync = FALSE <-> X Verilog.VGA.h_sync = TRUE)))"
SVSpec = "(@(posedge clk)  (##1 disp_ena & !rst |-> (h_sync iff s_nexttime !h_sync) ))"

start_ex = 0

scale = 1
size = [4]  # [4, 1]
gap = 1e-4  # this is the gap of the sign activation function
F_prec = 5
bits = 50

Ps = [1 for Mult in Mults]
Ms = [Mult * 66 * 2 for Mult in Mults]

is_acc = [0, 0, 0, 0, 1]
is_init = [1, 0, 0, 0, 0]
init_samp = [(0, [float(0), float(0), float(0), float(0)])]

try:
    from nur.bitwuzla_utils import b_set, b_unset
except ImportError:
    print("Library nur not found. Not exporting spec_automata function")
else:

    def spec_automata(ctx, q_cur, curr_vars, V0, q_nex, next_vars, V1, non_state, s):
        _, _, bw_obj, _ = ctx
        cases = []

        if q_cur == 0 and q_nex == 1:
            cases.append([])  # Transition from start state

        elif q_cur == 1 and q_nex == 1:
            cases.append([b_unset(non_state, "disp_ena", 1, ctx)])
            cases.append([b_set(non_state, "rst", 1, ctx)])

        elif q_cur == 1 and q_nex == 2:
            cases.append(
                [
                    b_set(non_state, "disp_ena", 1, ctx),
                    b_unset(curr_vars, "h_sync", 1, ctx),
                    b_unset(non_state, "rst", 1, ctx),
                ]
            )

        elif q_cur == 1 and q_nex == 3:
            cases.append(
                [
                    b_set(non_state, "disp_ena", 1, ctx),
                    b_set(curr_vars, "h_sync", 1, ctx),
                    b_unset(non_state, "rst", 1, ctx),
                ]
            )

        elif q_cur == 2 and q_nex == 1:
            cases.append(
                [
                    b_unset(non_state, "disp_ena", 1, ctx),
                    b_set(curr_vars, "h_sync", 1, ctx),
                ]
            )
            cases.append(
                [
                    b_set(non_state, "rst", 1, ctx),
                    b_set(curr_vars, "h_sync", 1, ctx),
                ]
            )

        elif q_cur == 2 and q_nex == 3:
            cases.append(
                [
                    b_set(non_state, "disp_ena", 1, ctx),
                    b_set(curr_vars, "h_sync", 1, ctx),
                    b_unset(non_state, "rst", 1, ctx),
                ]
            )

        elif q_cur == 2 and q_nex == 4:
            cases.append([b_unset(curr_vars, "h_sync", 1, ctx)])

        elif q_cur == 3 and q_nex == 1:
            cases.append(
                [
                    b_unset(non_state, "disp_ena", 1, ctx),
                    b_unset(curr_vars, "h_sync", 1, ctx),
                ]
            )
            cases.append(
                [
                    b_set(non_state, "rst", 1, ctx),
                    b_unset(curr_vars, "h_sync", 1, ctx),
                ]
            )

        elif q_cur == 3 and q_nex == 2:
            cases.append(
                [
                    b_set(non_state, "disp_ena", 1, ctx),
                    b_unset(curr_vars, "h_sync", 1, ctx),
                    b_unset(non_state, "rst", 1, ctx),
                ]
            )

        elif q_cur == 3 and q_nex == 4:
            cases.append([b_set(curr_vars, "h_sync", 1, ctx)])

        elif q_cur == 4 and q_nex == 4:
            cases.append([])

        return cases
