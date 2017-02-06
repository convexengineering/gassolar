"print sensitivities"
from gassolar.solar.solar import Mission

def sens_table(sols, varnames,
               filename="../../gassolarpaper/solarsens.generated.tex"):
    with open(filename, "w") as f:
        f.write("\\begin{longtable}{lccccccccccccc}\n")
        f.write("\\caption{Sensitivities}\\\\\n")
        f.write("\\toprule\n")
        f.write("\\toprule\n")
        f.write("\\label{t:sens}\n")
        f.write("& Latitude $=25$ & Latitude $=25$ & Latitude $=25$ & Latitude $=25$ \\\\\n")
        f.write("Variables & 85th Percentile Winds & 85th Percentile Winds & 90th Percentile Winds & 90th Percentile Winds \\\\\n")
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
    for l in [25, 30]:
        for p in [85, 90]:
            M = Mission(latitude=l)
            M.cost = M["W_{total}"]
            for vk in M.varkeys["p_{wind}"]:
                M.substitutions.update({vk: p/100.0})
            sol = M.solve("mosek")
            sols.append(sol)

    sens_table(sols, ["p_{wind}", "\\eta_Mission, Aircraft, SolarCells", "\\eta_{charge}", "\\eta_{discharge}", "\\rho_{solar}", "t_{night}", "(E/S)_{irr}", "m_{fac}_Mission, Aircraft, Wing", "h_{batt}", "W_{pay}", "\\eta_{prop}"], filename="test.tex")
