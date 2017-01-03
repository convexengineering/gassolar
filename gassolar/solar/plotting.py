import numpy as np
import matplotlib.pyplot as plt
from gpfit.softmax_affine import softmax_affine
import os
import pandas as pd

path = os.path.abspath(__file__).replace(os.path.basename(__file__), "").replace(os.sep+"solar"+os.sep, os.sep+"environment"+os.sep)
path = "/Users/mjburton11/MIT/GPKIT/gpkit-projects/gas_solar_trade/gassolar/environment/"
DF = pd.read_csv(path + "windaltfitdata.csv")

def windalt_plot(latitude, sol):
    alt = np.linspace(40000, 80000, 20)
    den = density(alt)
    x = np.log([np.hstack([den]*6),
                np.hstack([[p/100.0]*len(den)
                           for p in range(75, 100, 5) + [99]])]).T

    df = DF[DF["latitude"] == latitude]
    params = np.append(np.hstack([[
        np.log((df["c%d" % i]**(1/df["alpha"])).iloc[0]),
        (df["e%d1" % i]/df["alpha"]).iloc[0],
        (df["e%d2" % i]/df["alpha"]).iloc[0]] for i in range(1, 5)]),
                       1/df["alpha"].iloc[0])

    vwind = (np.exp(softmax_affine(x, params)[0])*100).reshape(6, 20)[3]
    fig, ax = plt.subplots()
    ax.plot(alt/1000.0, vwind*1.95384)
    altsol = altitude(min([sol(sv).magnitude for sv in sol("\\rho")]))
    vsol = max([sol(sv).to("knots").magnitude for sv in sol("V")])
    ax.plot(altsol/1000, vsol, "o", markersize=10, label="operating point")
    ax.legend(numpoints=1)
    ax.set_xlabel("Altitude [kft]")
    ax.set_ylabel("Wind Speed [knots]")
    ax.grid()
    ax.set_ylim([0, 200])
    return fig, ax

def altitude(density):
    g = 9.80665 # m/s^2
    R = 287.04 # m^2/K/s^2
    T11 = 216.65 # K
    p11 = 22532 # Pa
    p = density*R*T11
    h = (11000 - R*T11/g*np.log(p/p11))/0.3048
    return h

def density(altitude):
    g = 9.80665 # m/s^2
    R = 287.04 # m^2/K/s^2
    T11 = 216.65 # K
    p11 = 22532 # Pa
    p = 22632*np.exp(-g/R/T11*(altitude*0.3048-11000))
    den = p/R/T11
    return den
