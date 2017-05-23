"print sensitivities"
import numpy as np
import sys
from gassolar.gas.gas import Mission
from gassolar.environment.wind_speeds import get_windspeed
from gassolar.solar.print_sens import plot_sens, sens_table, sol_table

if __name__ == "__main__":
    sols = []
    for t in [5, 7, 10]:
        M = Mission()
        wind = get_windspeed(38, 90, 15000, 355)
        cwind = get_windspeed(38, 90, np.linspace(0, 15000, 11)[1:], 355)
        for vk in M.varkeys["V_{wind}"]:
            if "Climb" in vk.models:
                M.substitutions.update({vk: cwind[vk.idx[0]]})
            else:
                M.substitutions.update({vk: wind})
        M.substitutions.update({"t_Mission/Loiter": t})
        M.cost = M["MTOW"]
        sol = M.solve("mosek")
        sols.append(sol)

    varnames = ["V_{wind}_Mission/Loiter/FlightSegment", "W_{pay}",
                "\\eta_{prop}", "BSFC_{min}", "t_Mission/Loiter",
                "N_{max}_Mission/AircraftLoading/WingLoading/ChordSparL"]
    latns = ["$V_{\\mathrm{wind}}$", "$W_{\\mathrm{pay}}$",
             "$\\eta_{\\mathrm{prop}}$", "$BSFC_{\\mathrm{min}}$",
             "$t_{\\mathrm{loiter}}$", "$N_{\\mathrm{max}}$"]
    fig, ax = plot_sens(M, sols[2], varnames)

    dvarns = ["MTOW", "b_Mission/Aircraft/Wing", "AR_Mission/Aircraft/Wing",
              "W_{fuel-tot}", "W_Mission/Aircraft/Wing",
              "W_Mission/Aircraft/Engine", "BSFC", "C_L", "C_D"]
    dlatns = ["MTOW", "$b$", "$A$", "$W_{\\mathrm{fuel}}$",
              "$W_{\\mathrm{wing}}$", "$W_{\\mathrm{engine}}$", "BSFC", "$C_L$",
              "$C_D$"]

    tbfvar = ["MTOW", "b_Mission/Aircraft/Wing",
              "W_Mission/Aircraft/Empennage/HorizontalTail",
              "W_Mission/Aircraft/Empennage/TailBoom", "d_0", "l_h",
              "S_Mission/Aircraft/Empennage/HorizontalTail", "AR_h", "V_h"]
    tbflat = ["MTOW", "$b$", "$W_{\\mathrm{h}}$", "$W_{\\mathrm{boom}}$",
              "$d_0$", "$l_{\\mathrm{h}}$", "$S_h$", "$A_{\\mathrm{h}}$",
              "$V_{\\mathrm{h}}$"]

    tbsols = []
    tbMs = []
    for sp in [False, True]:
        M = Mission(sp=sp)
        M.cost = M["MTOW"]
        M.substitutions.update({"t_Mission/Loiter": 9})
        tbMs.append(M)
        if sp:
            sol = M.localsolve("mosek")
        else:
            sol = M.solve("mosek")
        tbsols.append(sol)

    if len(sys.argv) > 1:
        path = sys.argv[1]
        sens_table(sols, [M], varnames, solar=False,
                   filename=path.replace("figs/", "") + "gassens.generated.tex",
                   latns=latns, title="Gas Powered Aircraft Sensitivities "
                   "(90th Percentile Winds)", label="gassens")
        sol_table(sols, [M]*3, dvarns,
                  filename=path.replace("figs/", "") + "gvals.generated.tex",
                  ttype="gas", latns=dlatns,
                  title="Gas Powered Aircraft Design Variables", label="gvals")
        sol_table(tbsols, tbMs, tbfvar, ttype="tbflexg",
                  filename=path.replace("figs/", "") + "tbfgtable.generated.tex",
                  latns=tbflat, title="Tail Boom Flexibility with Solar Model",
                  label="tbfgtable")
        fig.savefig(path + "gassensbar.pdf", bbox_inches="tight")
    else:
        sens_table(sols, [M], varnames, solar=False,
                   filename="gassens.generated.tex", latns=latns,
                   title="Gas Powered Aircraft Sensitivities "
                   "(90th Percentile Winds)")
        sol_table(sols, [M]*3, dvarns, filename="gvals.generated.tex",
                  ttype="gas", latns=dlatns,
                  title="Gas Powered Aircraft Design Variables", label="gvals")
        sol_table(tbsols, tbMs, tbfvar, ttype="tbflexg", filename="tbfgtable.generated.tex", latns=tbflat, title="Tail Boom Flexibility with Solar Model", label="tbfgtable")
        fig.savefig("gassensbar.pdf", bbox_inches="tight")
