"lift to drag ratio"
import matplotlib.pyplot as plt
import numpy as np
from gassolar.gas.gas import Mission
from gassolar.environment.wind_speeds import get_windspeed
from gassolar.solar.plotting import labelLines

def return_cd(cl, re):
    cd = (0.0247*cl**2.49*re**-1.11 + 2.03e-7*cl**12.7*re**-0.338 +
          6.35e10*cl**-0.243*re**-3.43 + 6.49e-6*cl**-1.9*re**-0.681)**(1/3.72)
    return cd

M = Mission()
M.cost = 1/M["t_Mission, Loiter"]
for e in M.varkeys["\\eta_{prop}"]:
    M.substitutions.update({e: 0.75})
fig, ax = plt.subplots()
wind = get_windspeed(38, 90, 15000, 355)
cwind = get_windspeed(38, 90, np.linspace(0, 15000, 11)[1:], 355)
for vk in M.varkeys["V_{wind}"]:
    if "Climb" in vk.models:
        M.substitutions.update({vk: cwind[vk.idx[0]]})
    else:
        M.substitutions.update({vk: wind})
M.substitutions.update({"MTOW": 200})
sol = M.solve("mosek")
re = sol("Re_Mission, Loiter, FlightSegment, AircraftPerf, WingAero")[-1]
clm = sol("C_L_Mission, Loiter, FlightSegment, AircraftPerf, WingAero")
cdm = sol("c_{dp}_Mission, Loiter, FlightSegment, AircraftPerf, WingAero")
cl = np.linspace(0.2, 1.5, 100)
cd = return_cd(cl, re)
cl15 = cl**1.5/cd
clmax = cl[cl15 == max(cl15)]
cdmax = cd[cl15 == max(cl15)]
l = ax.plot(clm, cdm, "o", mfc="None", ms=7, mew=1.5,
            label="With Wind Constraint")
ax.annotate("mission start", xy=(clm[0], cdm[0]), xytext=(0.87, 0.0062),
            arrowprops=dict(arrowstyle="->"), fontsize=13)
ax.annotate("mission end", xy=(clm[-1], cdm[-1]), xytext=(0.42, 0.0072),
            arrowprops=dict(arrowstyle="->"), fontsize=13)
lines1 = [l[0]]

for vk in M.varkeys["m_{fac}"]:
    if "Loiter" in vk.descr["models"] and "FlightState" in vk.descr["models"]:
        M.substitutions.update({vk:0.01})
sol = M.solve("mosek")
clw = sol("C_L_Mission, Loiter, FlightSegment, AircraftPerf, WingAero")
cdw = sol("c_{dp}_Mission, Loiter, FlightSegment, AircraftPerf, WingAero")
l = ax.plot(clw, cdw, "s", mfc="None", ms=7, mew=1.5,
            label="Without Wind Constraint")
ax.annotate("mission start", xy=(clw[0], cdw[0]), xytext=(1.2, 0.0087),
            arrowprops=dict(arrowstyle="->"), fontsize=13)
ax.annotate("mission end", xy=(clw[-1], cdw[-1]), xytext=(0.9, 0.013),
            arrowprops=dict(arrowstyle="->"), fontsize=13)
l = ax.plot(clmax, cdmax, "+", mec="b", mfc="None", ms=7, mew=1.5)
lines1.append(l[0])
l = ax.plot(cl, cd, linewidth=2, label="Re=%3.fk" % (re/1000.), c="b",
            zorder=1)
lines = [l[0]]
re = sol("Re_Mission, Loiter, FlightSegment, AircraftPerf, WingAero")
for i, r, col in zip(range(5), re, ["", "m", "m", "c", "c"]):
    cd = return_cd(cl, r)
    cl15 = cl**1.5/cd
    clmax = cl[cl15 == max(cl15)]
    cdmax = cd[cl15 == max(cl15)]
    if i == 2 or i == 4:
        l = ax.plot(cl, cd, linewidth=2, label="Re=%3.fk" % (r/1000.),
                    c=col, zorder=1)
        lines.append(l[0])
        ax.plot(clmax, cdmax, "+", mec=col, mfc="None", ms=7, mew=1.5)

labelLines(lines, fontsize=12, zorder=2.5, align=False,
           xvals=[0.95, 0.75, 0.6])
ax.set_xlabel("$C_L$")
ax.set_ylabel("$c_{d_p}$")
ax.legend(["With Wind Constraint", "Without Wind Constraint"], fontsize=15,
          loc=2)
ax.grid()
fig.savefig("../../gassolarpaper/polarmission.pdf", bbox_inches="tight")
