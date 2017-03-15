"print sensitivities"
import numpy as np
import sys
from gassolar.gas.gas import Mission
from gassolar.environment.wind_speeds import get_windspeed
from gassolar.solar.print_sens import plot_sens

def sens_table(sols, varnames,
               filename="../../gassolarpaper/gassens.generated.tex"):
    with open(filename, "w") as f:
        f.write("\\begin{longtable}{lccccccccccccc}\n")
        f.write("\\caption{Gas Sensitivities}\\\\\n")
        f.write("\\toprule\n")
        f.write("\\toprule\n")
        f.write("\\label{t:sens}\n")
        f.write("Variable & 5 Day Endurance & 7 Day Endurance & 9 Day Endurance\\\\\n")
        f.write("\\midrule\n")
        for vname in varnames:
            sens = []
            for s in sols:
                sen = s["sensitivities"]["constants"][vname]
                if hasattr(sen, "__len__"):
                    sen = s["sensitivities"]["constants"][max(sen)]
                sens.append(sen)
            vals = "$" + vname + "$ &" + " & ".join(["%.3g" % x for x in sens])
            f.write(vals + "\\\\\n")
        f.write("\\bottomrule\n")
        f.write("\\end{longtable}")

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
        M.substitutions.update({"t_Mission, Loiter": t})
        M.cost = M["MTOW"]
        sol = M.solve("mosek")
        sols.append(sol)

    varnames = ["V_{wind}_Mission, Loiter, FlightSegment", "W_{pay}", "\\eta_{prop}", "BSFC_{min}", "t_Mission, Loiter", "N_{max}_Mission, AircraftLoading, WingLoading, GustL"]
    latns = ["$V_{\\mathrm{wind}}$", "$W_{\\mathrm{pay}}$", "$\\eta_{\\mathrm{prop}}$", "$BSFC_{\\mathrm{min}}$", "$t_{\\mathrm{loiter}}$", "$N_{\\mathrm{max}}$"]
    sens_table(sols, varnames, filename="sens.generated.tex")
    fig, ax = plot_sens(M, sols[2], varnames, latns=latns)

    if len(sys.argv) > 1:
        path = sys.argv[1]
        fig.savefig(path + "gassensbar.pdf", bbox_inches="tight")
    else:
        fig.savefig("gassensbar.pdf", bbox_inches="tight")

