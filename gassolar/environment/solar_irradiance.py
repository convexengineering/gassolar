" solar irrandiance model "
import numpy as np
from numpy import sin, tan, cos, arccos, deg2rad
import matplotlib.pyplot as plt
from gpfit.fit import fit
import sys
import pandas as pd
plt.rcParams.update({'font.size':15})
GENERATE = False

#pylint disable: invalid-name
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

def twi_fits(latitude, day, gen=False):

    np.random.seed(0)

    ES, td, tn, p = get_Eirr(latitude, day)
    params = [latitude]

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
    cn, err = fit(x, y, 1, "MA")
    rm = err
    print "RMS error: %.4f" % rm
    dftw = cn.get_dataframe(x)
    if not gen:
        fig1, ax1 = plt.subplots()
        fig2, ax2 = plt.subplots()
        yfit = cn.evaluate(x)
        ax1.plot(P[1:-15], 2*C[:-14], "o", c="g", markerfacecolor="none",
                 mew=1.5)
        ax1.plot(P[1:-15], np.exp(yfit), c="g",
                 label="%dth Latitude" % latitude, lw=2)
        ax1.set_xlabel("Minimum Power $(P/S)_{\mathrm{min}}$ [W/m$^2$]",
                       fontsize=19)
        ax1.set_ylabel("Twilight Energy $(E/S)_{\mathrm{twilight}}}$ " +
                       "[Whr/m$^2$]", fontsize=19)
        ax1.grid()
        params.append(cn[0].right.c)
        params.append(cn[0].right.exp[list(cn[0].varkeys["u_fit_(0,)"])[0]])

    x = np.log(P[1:-15])
    y = np.log(2*B[:-14])
    cn, err = fit(x, y, 1, "MA")
    rm = err
    print "RMS error: %.4f" % rm
    dfday = cn.get_dataframe(x)
    if not gen:
        yfit = cn.evaluate(x)
        ax2.plot(P[1:-15], 2*B[:-14], "o", c="g", markerfacecolor="none",
                 mew=1.5)
        ax2.plot(P[1:-15], np.exp(yfit), c="g",
                 label="%dth Latitude" % latitude, lw=2)
        ax2.grid()
        ax2.set_xlabel("Minimum Necessary Power $(P/S)_{\mathrm{min}}$ " +
                       "[W/m$^2$]", fontsize=19)
        ax2.set_ylabel("Daytime Energry $(E/S)_{\mathrm{day}}$ [Whr/m$^2$]",
                       fontsize=19)
        fig1.savefig(path + "Cenergy.pdf")
        fig2.savefig(path + "Benergy.pdf")
    return dftw, dfday

if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = ""

    if not GENERATE:
        ES, td, tn, p = get_Eirr(30, 355, N=1000)
        fig, ax = plt.subplots()
        ax.fill_between([-12, -td/2], 0, 80, alpha=0.3, facecolor="b",
                        linewidth=2, color="b")
        ax.fill_between([td/2, 12], 0, 80, alpha=0.3, facecolor="b",
                        linewidth=2, color="b")
        ax.fill_between(p[1], p[0], 80, where=p[0] < 80, linewidth=2,
                        color="b", facecolor="m", alpha=0.3)
        ax.fill_between(p[1], 0, p[0], hatch="xx", color="r", linewidth=2,
                        facecolor="none")
        newp = []
        for pp in p[0]:
            if pp < 80:
                newp.append(pp)
            else:
                newp.append(80)
        ax.fill_between(p[1], 0, newp, linewidth=2, color="g", facecolor="g",
                        alpha=0.3)
        ax.set_xlabel("Time [hr]")
        ax.set_ylabel("Available Solar Power [W/m$^2$]")
        ax.set_xlim([-12, 12])
        ax.text(-1.2, 400, "$(E/S)_{\mathrm{sun}}$", fontsize=15)
        ax.text(-1.2, 30, "$(E/S)_{\mathrm{day}}$", fontsize=15)
        ax.annotate("$(E/S)_{\mathrm{twilight}}$", xy=(-4.9, 70),
                    xytext=(-10.1, 220),
                    arrowprops=dict(facecolor='black', shrink=0.05, width=1.5,
                                    headwidth=10, frac=0.1))
        ax.annotate("", xy=(5.5, 70), xytext=(-6.7, 205),
                    arrowprops=dict(facecolor='black', shrink=0.05, width=1.5,
                                    headwidth=10, frac=0.025))
        ax.grid()
        ax2 = ax.twinx()
        ax2.set_yticks([0, 80, 900])
        ax2.set_yticklabels(["", "$(P/S)_{\mathrm{min}}$", ""])
        fig.savefig(path + "lat30.pdf", bbox_inches="tight")

        # solar irradiance by year
        Fig, Ax = plt.subplots()
        Mos = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep",
               "oct", "nov", "dec", "jan"]
        Dayinmo = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        Moday = [sum(Dayinmo[:i+1]) for i in range(len(Dayinmo))]
        Mid = [(Moday[i]+Moday[i+1])/2 for i in range(len(Moday)-1)]
        es = []
        for d in range(365):
            E, _, _, _ = get_Eirr(30, d)
            es.append(E)
        ind = es.index(min(es))
        Ax.annotate("winter solstice", xy=(ind, min(es)), xytext=(200, 5500),
                   arrowprops=dict(arrowstyle="->"))
        Ax.plot(range(365), es)
        Ax.set_xticks(Moday)
        Ax.set_xticks(Mid, minor=True)
        Ax.set_xticklabels(Mos, minor=True)
        Ax.set_xticklabels([])
        Ax.set_ylabel("Daily Solar Energy [Whr/m$^2$]")
        Ax.grid()
        Ax.set_xlim([0, 365])
        Ax.set_ylim([0, 12000])
        Fig.savefig(path + "eirrvsmonth.pdf", bbox_inches="tight")

    if GENERATE:
        datatw = []
        dataday = []
        lat = range(20, 61)
        for l in lat:
            dft, dfd = twi_fits(l, 355)
            dataday.append(dft)
            datatw.append(dfd)
        df = pd.concat(datatw)
        df['latitude'] = pd.Series(np.arange(20, 61, 1), index=df.index)
        df.to_csv("solar_twlightfit.csv")
        df = pd.concat(dataday)
        df['latitude'] = pd.Series(np.arange(20, 61, 1), index=df.index)
        df.to_csv("solar_dayfit.csv")
    else:
        _, _ = twi_fits([30], 355, gen=True)

