import pandas as pd
import numpy as np
import sys
import os
from numpy import logspace, log, log10
import matplotlib.pyplot as plt
from gpfit.fit import fit
from scipy import interpolate
import gpkitmodels.GP.aircraft.engine.gas_engine as Engine
plt.rcParams.update({'font.size':19})

np.random.seed(0)
PATH = (os.path.abspath(__file__).replace(os.path.basename(__file__), "")
        + os.sep)
GENERATE = True

def plot_BSFCtoPower(power_csv, bsfc_csv):
    # Fitting BSFC vs. Power
    df = pd.read_csv(power_csv)
    p = df['P']
    rpm = df["RPM"]
    f = interpolate.interp1d(rpm, p)
    df = pd.read_csv(bsfc_csv)
    df = df[(df["RPM"] > min(rpm)) & (df["RPM"] < max(rpm))]
    rpmnew = df["RPM"]
    u = f(rpmnew)/max(p)
    w = df['BSFC']/min(df["BSFC"])
    x = np.array(log(u))
    y = np.array(log(w))
    Type = 'SMA'
    K = 2

    cstrt, error = fit(x, y, K, Type)
    print "RMS error = %.4f" % error
    yfit = cstrt.evaluate(x)
    dfc = cstrt.get_dataframe()

    fig, ax = plt.subplots()
    ax.plot(u*100, w*min(df["BSFC"]), "o", mfc="None", ms=7, mew=1.5)
    ax.plot(u*100, np.exp(yfit)*min(df["BSFC"]), linewidth=2)
    ax.set_xlabel("Percent Power")
    ax.set_ylabel("$BSFC$ [kg/kW/hr]")
    ax.legend(["RCV Engine Ltd. Data", "GP approximation"], fontsize=15)
    ax.set_ylim([0, 1])
    ax.set_xlim([0, 100])
    ax.grid()
    return dfc, fig, ax

def plot_BSFCtoRPM():
    # Fitting BSFC vs. RPM
    df = pd.read_csv('Dataset_BSFC_kgKwh.csv')
    RPM = df['RPM']
    RPMmax = np.amax(RPM)
    BSFC = df['BSFC']
    BSFCmin = np.amin(BSFC)
    x = np.array(log(RPM/RPMmax))
    y = np.array(log(BSFC/BSFCmin))
    Type = 'SMA'
    K = 2

    cstrt, rmserror = fit(x,y,K,Type)
    print "RMS error = %.4f" % rmserror
    yfit = cstrt.evaluate(x)

    fig, ax = plt.subplots()
    ax.plot(RPM, BSFC, "o", markerfacecolor="None")
    ax.plot(RPM, np.exp(yfit)*BSFCmin)
    ax.set_xlabel("$RPM$")
    ax.set_ylabel("$BSFC$ [lb/hp/hr]")
    ax.legend(["Manufacture Data", "GP approximation"])
    ax.grid()
    return fig, ax

def plot_RPMtoPower():
    # Fitting Power vs. RPM
    df = pd.read_csv('Dataset_Power_Kw.csv')
    RPM = df['RPM']
    RPM_max = np.amax(RPM)
    P = df['P']
    P_max = np.amax(P)
    y = np.array(log(P/P_max))
    x = np.array(log(RPM/RPM_max))
    Type = 'SMA'
    K = 1
    cstrt, rmserror = fit(x,y,K,Type)
    print "RMS error = %.4f" % rmserror
    yfit = cstrt.evaluate(x)

    fig, ax = plt.subplots()
    ax.plot(RPM, P, "o", markerfacecolor="None")
    ax.plot(RPM, np.exp(yfit)*P_max)
    ax.set_xlabel("$RPM$")
    ax.set_ylabel("Shaft Power [kW]")
    ax.legend(["Manufacture Data", "GP approximation"])
    ax.grid()
    return fig, ax

def plot_lapse():
    # fit lapse rate
    df = pd.read_csv("DF35_maxPvh.csv")
    u = df["ft"]
    w = df["kW"]/max(df["kW"])
    x = np.array(u)
    y = np.array(w)

    A = np.vstack([x, np.ones(len(x))]).T
    m, c = np.linalg.lstsq(A, y)[0]
    print "Equation: y = %.4gx + %.4f" % (m, c)
    fig, ax = plt.subplots()
    ax.plot(x, y, 'o', label='RCV Engine Data', markerfacecolor="None")
    ax.plot(x, m*x + c, label='Fitted Line')
    ax.set_ylabel("Engine Lapse Rate")
    ax.set_xlabel("Altitude [ft]")
    ax.legend()
    ax.grid()
    return fig, ax

if __name__ == "__main__":
    csvname = PATH + 'Dataset_Power_Kw.csv'
    csvname2 = PATH + 'Dataset_BSFC_kgKwh.csv'
    df, fig, ax = plot_BSFCtoPower(csvname, csvname2)
    if GENERATE:
        path  = os.path.dirname(Engine.__file__)
        df.to_csv(path + os.sep + "powerBSFCfit.csv", index=False)
    else:
        df.to_csv("powerBSFCfit.csv", index=False)
    if len(sys.argv) > 1:
        path = sys.argv[1]
        fig.savefig(path + "powertobsfcfit.pdf", bbox_inches="tight")
    else:
        fig.savefig("powertobsfcfit.pdf", bbox_inches="tight")

