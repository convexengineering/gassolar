" solar irrandiance model "
import numpy as np
from numpy import sin, tan, cos, arccos, deg2rad
import matplotlib.pyplot as plt
from gpfit.fit import fit
import pandas as pd
plt.rcParams.update({'font.size':15})

def get_Eirr(latitude, day, N=50.0):
    """
    day is juilian day, measured from Jan 1st
    latitude is in degrees
    Returns:
    -------
    ESirr: Solar energy per unit area of from the sun Whr/m^2
    tday: time of daylight
    tnight: time of daylight
    p: 2d array [2, 50] Power per unit area [0] and time array [1]
    """
    assert isinstance(day, int)

    beta = 2*np.pi*(day-1)/365
    lat = deg2rad(latitude)
    delta = (0.006918 - 0.399912*cos(beta) + 0.070257*sin(beta) -
             0.006758*cos(2*beta) + 0.000907*sin(2*beta) -
             0.002697*cos(3*beta) + 0.00148*sin(3*beta))
    tstart = 12/np.pi*arccos(-tan(delta)*tan(lat))
    tend = -tstart
    t = np.linspace(tstart, tend, N)
    costhsun = sin(delta)*sin(lat) + cos(delta)*cos(lat)*cos(2*np.pi*t/24)

    r0 = 149.597e6 # avg distance from earth to sun km
    Reo = r0*(1 + 0.017*sin(2*np.pi*(day-93)/365))
    Psun = 63372630 # energy from sun surface W/m^2
    Rsun = 695842 # radius of the sun, km
    P0 = Psun*4*np.pi*Rsun**2/4/np.pi/Reo**2
    tau = np.exp(-0.175/costhsun)
    P = P0*costhsun# *tau
    E = np.trapz(P)*(abs(tend-tstart))/N
    tday = tstart*2
    tnight = 24-tstart*2
    plot = [P, t]
    return E, tday, tnight, plot

if __name__ == "__main__":
    ES, td, tn, p = get_Eirr(30, 355, N=1000)
    fig, ax = plt.subplots()
    ax.fill_between([-12, -td/2], 0, 80, alpha=0.5, facecolor="b",
                    linewidth=2, color="b")
    ax.fill_between([td/2, 12], 0, 80, alpha=0.5, facecolor="b", linewidth=2,
                    color="b")
    ax.fill_between(p[1], p[0], 80, where=p[0] < 80, linewidth=2, color="b",
                    facecolor="m", alpha=0.5)
    ax.fill_between(p[1], 0, p[0], hatch="xx", color="r", linewidth=2,
                    facecolor="none")
    newp = []
    for pp in p[0]:
        if pp < 80:
            newp.append(pp)
        else:
            newp.append(80)
    ax.fill_between(p[1], 0, newp, linewidth=2, color="g", facecolor="g",
                    alpha=0.5)
    ax.set_xlabel("Time [hr]")
    ax.set_ylabel("Available Solar Power [W/m$^2$]")
    ax.set_xlim([-12, 12])
    ax.text(-1.2, 400, "$(E/S)_{\mathrm{sun}}$", fontsize=15)
    ax.text(-10, 30, "$E_{\mathrm{batt}}/S_{\mathrm{solar}}$", fontsize=15)
    ax.text(7, 30, "$E_{\mathrm{batt}}/S_{\mathrm{solar}}$", fontsize=15)
    ax.text(-1.2, 30, "$(E/S)_{\mathrm{day}}$", fontsize=15)
    ax.annotate("$(E/S)_C$", xy=(-4.9, 70), xytext=(-9, 220),
                arrowprops=dict(facecolor='black', shrink=0.05, width=1.5,
                                headwidth=10, frac=0.1))
    ax.annotate("", xy=(5.5, 70), xytext=(-6.8, 205),
                arrowprops=dict(facecolor='black', shrink=0.05, width=1.5,
                                headwidth=10, frac=0.025))
    ax.grid()
    ax2 = ax.twinx()
    ax2.set_yticks([0, 80, 900])
    ax2.set_yticklabels(["", "$(P/S)_{\mathrm{min}}$", ""])
    fig.savefig("../../gassolarpaper/lat30.pdf", bbox_inches="tight")

    data = {}
    fig1, ax1 = plt.subplots()
    fig2, ax2 = plt.subplots()
    # for l in range(20, 61):
    for l, col in zip([30], ["g"]):

        ES, td, tn, p = get_Eirr(l, 355)
        params = [l]

        P = p[0][p[1] > 0]
        t = p[1][p[1] > 0]
        f = np.array([np.trapz(P[:i+1])*(t[0]-t[i])/i for i in
                      range(1, len(P)-1)])
        ends = np.array([P[i]*(t[0]-t[i]) for i in range(1, len(P))][:-1])
        Eday = np.array([P[i]*t[i] for i in range(1, len(P))][:-1])
        C = ends - f
        B = Eday + f

        x = np.log(P[1:-15])
        y = np.log(2*C[:-14])
        cn, rm = fit(x, y, 1, "MA")
        print "RMS error: %.4f" % rm
        yfit = cn.evaluate(x)
        ax1.plot(P[1:-15], 2*C[:-14], "o", c=col, markerfacecolor="none")
        ax1.plot(P[1:-15], np.exp(yfit), c=col, label="%dth Latitude" % l)
        ax1.set_xlabel("Minimum Necessary Power $(P/S)_{\mathrm{min}}$ [W/m$^2$]")
        ax1.set_ylabel("Extra Required Battery Energy $(E/S)_C}$ [Whr/m$^2$]")
        ax1.grid()
        params.append(cn[0].right.c)
        params.append(cn[0].right.exp[list(cn[0].varkeys["u_fit_(0,)"])[0]])

        x = np.log(P[1:-15])
        y = np.log(2*B[:-14])
        cn, rm = fit(x, y, 1, "MA")
        print "RMS error: %.4f" % rm
        yfit = cn.evaluate(x)
        ax2.plot(P[1:-15], 2*B[:-14], "o", c=col, markerfacecolor="none")
        ax2.plot(P[1:-15], np.exp(yfit), c=col, label="%dth Latitude" % l)
        ax2.grid()
        ax2.set_xlabel("Minimum Necessary Power $(P/S)_{\mathrm{min}}$ [W/m$^2$]")
        ax2.set_ylabel("Daytime Energry for Solar Cells $(E/S)_{\mathrm{day}}$ [Whr/m$^2$]")
        params.append(cn[0].right.c)
        params.append(cn[0].right.exp[list(cn[0].varkeys["u_fit_(0,)"])[0]])
        data["%d" % l] = params

    fig1.savefig("../../gassolarpaper/Cenergy.pdf")
    fig2.savefig("../../gassolarpaper/Benergy.pdf")
    # df = pd.DataFrame(data).transpose()
    # colnames = ["latitude", "Cc", "Ce", "Bc", "Be"]
    # df.columns = colnames
    # df.to_csv("solarirrdata.csv")
