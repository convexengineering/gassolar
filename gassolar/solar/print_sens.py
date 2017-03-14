"print sensitivities"
from gassolar.solar.solar import Mission
import matplotlib.pyplot as plt
import numpy as np
import sys

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

def plot_sens(model, sol, varnames, latns=None):
    fig, ax = plt.subplots()
    pss = []
    ngs = []
    sens = {}
    for vname, latn in zip(varnames, latns):
        sen = sol["sensitivities"]["constants"][vname]
        if hasattr(sen, "__len__"):
            vk = max(sen)
            sen = sol["sensitivities"]["constants"][vk]
        else:
            vk = model[vname]
        sens[vk] = sen

    labels = []
    for s in sorted(np.absolute(sens.values()), reverse=True):
        vn = [se for se in sens if abs(sens[se]) == s][0]
        labels.append(model[vn].descr["label"])
        if sens[vn] > 0:
            pss.append(sens[vn])
            ngs.append(0)
        else:
            ngs.append(abs(sens[vn]))
            pss.append(0)

    ind = np.arange(0.5, len(varnames) + 0.5, 1)
    ax.bar(ind - 0.25, pss, 0.5, color="#4D606E")
    ax.bar(ind - 0.25, ngs, 0.5, color="#3FBAC2")
    ax.set_xlim([0.0, ind[-1]+0.5])
    ax.set_xticks(ind)
    ax.set_xticklabels(labels, rotation=-45, ha="left")
    ax.legend(["Positive", "Negative"])
    ax.set_ylabel("sensitivities")
    return fig, ax


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

    varns =  ["p_{wind}", "\\eta_Mission, Aircraft, SolarCells",
              "\\eta_{charge}", "\\eta_{discharge}", "\\rho_{solar}",
              "t_{night}", "(E/S)_{irr}", "h_{batt}", "W_{pay}",
              "\\eta_{prop}"]
    latns =  ["$p_{\\mathrm{wind}}$", "$\\eta_{\\mathrm{solar}}$",
              "$\\eta_{\\mathrm{charge}}$", "$\\eta_{\\mathrm{discharge}}$",
              "$\\rho_{\\mathrm{solar}}$",
              "$t_{\\mathrm{night}}$", "$(E/S)_{\\mathrm{irr}}$",
              "$h_{\\mathrm{batt}}$", "$W_{\\mathrm{pay}}$",
              "$\\eta_{\\mathrm{prop}}$"]
    sens_table(sols, varns, filename="test.tex")
    fig, ax = plot_sens(M, sols[3], varns, latns=latns)
    if len(sys.argv) > 1:
        path = sys.argv[1]
        fig.savefig(path + "solarsensbar.pdf", bbox_inches="tight")
    else:
        fig.savefig("solarsensbar.pdf", bbox_inches="tight")

