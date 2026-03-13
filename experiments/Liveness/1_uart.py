N_lims = [2**4, 2**6, 2**8, 2**9, 2**10, 2**11, 2**12, 2**14, 2**15, 2**16]
CBITSs = [4, 6, 8, 9, 10, 11, 12, 14, 15, 16]
specTXT = "FG !rst -> GF tx_state == 0"
module_name = "UART_T"
file_name = "uart_transmit"
LTLSpec = (
    "LTLSPEC F G (Verilog.UART_T.rst = FALSE) -> G F (Verilog.UART_T.tx_state = FALSE)"
)
SVSpec = "(@(posedge clk) s_eventually !rst -> !tx_state)"

start_ex = 0
scale = 1
size = [3]  # [3, 1]
gap = 1e-4  # this is the gap of the sign activation function
F_prec = 5
bits = 50

Ps = [N_lim / 2 for N_lim in N_lims]
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
                    nur.BUnSet(curr_vars, "tx_state", 0, ctx),
                    nur.Bset(non_state, "rst", 0, ctx),
                ]
            )
        elif q_cur == 1 and q_nex == 1:
            cases.append(
                [
                    nur.BUnSet(curr_vars, "tx_state", 0, ctx),
                    nur.Bset(non_state, "rst", 0, ctx),
                ]
            )
        return cases
