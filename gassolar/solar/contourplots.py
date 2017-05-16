" contour plots "
import matplotlib.pyplot as plt
import numpy as np
import sys
from solar import Mission
from plotting import windalt_plot, labelLines
from gpkit.tools.autosweep import autosweep_1d
from battsolarcon import find_sols

def plot_contours(path=None):
    N = 100
    stime = 0.0
    numsolves = 0
    plt.rcParams.update({'font.size':19})
    hmin = 250.0
    hmax = 400.0
    for av in [80, 85, 90]:
        for lat in [25, 30, 35]:
            zo = 10
            if lat == 25:
                bs = range(30, 80, 5)
            elif lat == 30:
                bs = range(35, 80, 5)
                if av == 90:
                    del bs[0]
            else:
                bs = range(45, 80, 5)
                if av == 90:
                    del bs[0]
            fig, ax = plt.subplots()
            M = Mission(latitude=lat)
            M.substitutions.update({"W_{pay}": 10})
            for vk in M.varkeys["\\eta_{prop}"]:
                M.substitutions.update({vk: 0.75})
            for vk in M.varkeys["p_{wind}"]:
                M.substitutions.update({vk: av/100.0})
            del M.substitutions["\\eta_Mission/Aircraft/SolarCells"]
            del M.substitutions["h_{batt}"]
            M.cost = M["h_{batt}"]
            lines = []
            midx = []
            for b in bs:
                etamax = 0.4
                etamin = 0.15
                M.substitutions.update({"b_Mission/Aircraft/Wing": b})
                M.substitutions.update({"\\eta_Mission/Aircraft/SolarCells":
                                        etamax})
                sol = M.solve("mosek")
                stime += sol["soltime"]
                numsolves += 1
                del M.substitutions["\\eta_Mission, Aircraft, SolarCells"]
                if sol("h_{batt}").magnitude < hmin:
                    M.substitutions.update({"h_{batt}": hmin})
                    M.cost = M["\\eta_Mission/Aircraft/SolarCells"]
                    sol = M.solve("mosek")
                    stime += sol["soltime"]
                    numsolves += sol["soltime"]
                    etamax = sol("\\eta_Mission/Aircraft/SolarCells")

                M.substitutions.update({"h_{batt}": hmax})
                M.cost = M["\\eta_Mission/Aircraft/SolarCells"]
                sol = M.solve("mosek")
                stime += sol["soltime"]
                numsolves += 1
                etamin = sol("\\eta_Mission/Aircraft/SolarCells")

                if etamin > etamax:
                    continue

                del M.substitutions["h_{batt}"]
                M.cost = M["h_{batt}"]
                xmin_ = np.linspace(etamin, etamax, 100)
                tol = 0.01
                bst = autosweep_1d(M, tol,
                                   M["\\eta_Mission/Aircraft/SolarCells"],
                                   [etamin, etamax], solver="mosek")
                bsts = find_sols([bst])
                sols = np.hstack([bs.sols for bs in bsts])
                stime += sum(np.unique([s["soltime"] for s in sols]))
                numsolves += bst.nsols

                if b % 10 == 0:
                    l = ax.plot(xmin_, bst.sample_at(xmin_)["cost"], "k",
                                label="%d [ft]" % b, zorder=zo)
                    zo += 2
                    lines.append(l[0])
                    midx.append(np.median(xmin_))
                else:
                    ax.plot(xmin_, bst.sample_at(xmin_)["cost"], "--", c="0.5",
                            zorder=100)

            # parato fontier
            del M.substitutions["b_Mission/Aircraft/Wing"]
            M.substitutions.update({"\\eta_Mission/Aircraft/SolarCells":
                                    etamax})
            M.cost = M["h_{batt}"]
            sol = M.solve("mosek")
            etamax = 0.4
            stime += sol["soltime"]
            numsolves += 1
            del M.substitutions["\\eta_Mission/Aircraft/SolarCells"]
            if sol("h_{batt}").magnitude < hmin:
                M.substitutions.update({"h_{batt}": hmin})
                M.cost = M["\\eta_Mission/Aircraft/SolarCells"]
                sol = M.solve("mosek")
                stime += sol["soltime"]
                numsolves += sol["soltime"]
                etamax = sol("\\eta_Mission/Aircraft/SolarCells")

            M.substitutions.update({"h_{batt}": hmax})
            M.cost = M["\\eta_Mission/Aircraft/SolarCells"]
            sol = M.solve("mosek")
            stime += sol["soltime"]
            numsolves += 1
            etamin = sol("\\eta_Mission/Aircraft/SolarCells")

            if etamin > etamax:
                break
            del M.substitutions["h_{batt}"]
            M.cost = M["h_{batt}"]
            xmin_ = np.linspace(etamin, etamax, 100)
            tol = 0.01
            bst = autosweep_1d(M, tol, M["\\eta_Mission/Aircraft/SolarCells"],
                               [etamin, etamax], solver="mosek")
            bsts = find_sols([bst])
            sols = np.hstack([b.sols for b in bsts])
            stime += sum(np.unique([s["soltime"] for s in sols]))
            numsolves += bst.nsols

            ax.set_xlabel("Solar Cell Efficiency")
            ax.set_ylabel("Battery Specific Energy [Whr/kg]")
            labelLines(lines[:-1], align=True, xvals=midx, zorder=[11, 13, 15, 17])
            ax.fill_between(np.hstack([0.15, xmin_]), 0,
                            np.hstack([hmax, bst.sample_at(xmin_)["cost"]]),
                            edgecolor="r", lw=2, hatch="/", facecolor="None",
                            zorder=100)
            ax.text(0.17, 260, "Infeasible", fontsize=19)
            ax.set_xlim([0.15, 0.4])
            ax.set_ylim([250, 400])
            if path:
                fig.savefig(path + "bcontourl%da%d.pdf" % (lat, av),
                            bbox_inches="tight")
            else:
                fig.savefig("bcontourl%da%d.pdf" % (lat, av))

    print "%d solves in %.4f seconds" % (numsolves, stime)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        plot_contours(path=sys.argv[1])
    else:
        plot_contours()
