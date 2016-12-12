" fitting wind speed data "
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from gassolar.environment.wind_speeds import get_windspeed, interpolate
from gpfit.fit import fit
from gpfit.max_affine import max_affine
from gpfit.softmax_affine import softmax_affine
from gpfit.implicit_softmax_affine import implicit_softmax_affine
plt.rc("text", usetex=True)

def fit_setup(altitude=(40000, 80000), latitude=45, percentage=90):
    """
    Function that sets up the fit for altitude versus density. Density in
    10^-1 kg/m^3

    Inputs
    ------
    altitude: tuple - two values for the upper and lower bound of altitude
              range (ex. (40000, 80000)). Altitude in ft
    latitude: int - latitude of earth in degrees
    percentage: int - percentile wind speeds

    Outputs
    ------
    x: 1D array of x values for fit
    y: 1D array of y values for fit

    """

    N = 20
    altitude = np.linspace(altitude[0], altitude[1], N)
    wind = get_windspeed(latitude, percentage, altitude, 355)
    df = pd.read_csv("usstd_atm.csv")
    hm = altitude*0.3048
    density = []
    for h in hm:
        indh = df["Altitude"][df["Altitude"] > h].index[0]
        indl = indh-1
        xs = [df["Altitude"][indl], df["Altitude"][indh]]
        ys = [df["Density"][indl], df["Density"][indh]]
        density.append(interpolate(xs, ys, h))

    u = np.hstack(density)
    w = np.hstack(wind)
    x = np.log(u)
    y = np.log(w)

    return x, y

def return_fitSMA(u_1):

    "K=3"
    # w = (132960 * (u_1)**-2.38864 + 9.23163e-05 * (u_1)**2.73706
    #      + 8356.28 * (u_1)**-4.01751)**(1/0.763341)
    "K=4, RMS=0.004059"
    w = (1.16012e+180 * (u_1)**-97.6238 + 7.97629e+134 * (u_1)**-120.996
         + 2.31229e-93 * (u_1)**123.733
         + 3.24369e+213 * (u_1)**-46.4295)**(1/86.4913)

    "K=5, RMS=0.0154"
    # w = (3540.95 * (u_1)**-2.26982 + 4681.92 * (u_1)**-2.26415
    #      + 3345.87 * (u_1)**-1.95286 + 1.60184 * (u_1)**-3.46449
    #      + 0.00256264 * (u_1)**1.67464)**(1/0.420148)

    "K=3, RM=0.01519, alt=[40000,80000]"
    # w = (6.33474e-17 * (u_1)**10.9121 + 1.03701e+09 * (u_1)**-2.90501
    #      + 1.92786e-48 * (u_1)**-35.1658)**(1/2.61021)

    return w

def plot_fit(altitude):

    alt = np.linspace(altitude[0], altitude[-1], 100)
    fig, ax = plt.subplots()
    wfit = return_fitSMA(alt)
    wdata = get_windspeed(45, 90, altitude*1000, 355)
    ax.plot(wdata, altitude, "bo")
    ax.plot(wfit, alt, "b-")
    ax.set_xlabel("wind speed [m/s]")
    ax.set_ylabel("altitude [kft]")
    ax.set_xlim([0, 60]) #max(np.concatenate((wdata, wfit)))])
    ax.set_ylim([40, 80])
    ax.text(0, 70, "eq: $w^{86.5} = 1.16e+180u_1^{-97.6}$\n \
                    $+ 7.97e+134u_1^{-120.996}$\n \
                    $+ 2.31e-93u_1^{123.733}$\n \
                    $+ 3.24e+213u_1^{-46.4295}$\n \
                    RMS = 0.004059", fontsize=12)
    # ax.text(0, 70, "eq: $w^{-2.90} = 6.33e-17u_1^{10.91}$ \n \
    #                 $+ 1.03e+09u_1^{-2.90}$\n \
    #                 $+ 1.92e-48u_1^{-35.16}$ \n \
    #                 RMS = 0.01519", fontsize=12)
    ax.grid()
    return fig, ax

def return_yfit(cnstr, x, fittype):
    """
    given a constraint and x data, return y

    Inputs
    ------
    cnstr: Constraint - (MonomialInequality, MonomialEquality,
                         PosynomialInequality)
    x: 1D or 2D array - array of input values in log space
    fittype: string - "MA", "SMA",  or "ISMA"

    Output
    ------
    y: 1D array - array of output for the given x inputs in log space

    """

    y = 0

    if x.ndim == 1:
        x = x.reshape(x.size, 1)

    if fittype == "MA":
        if not hasattr(cnstr, "__len__"):
            cnstr = [cnstr]
        params = np.hstack([[np.log(cn.left.c), cn.left.exp.items()[0][1]]
                            for cn in cnstr])
        y, _ = max_affine(x, params)

    elif fittype == "SMA":
        alpha = 1./cnstr.left.exp.items()[0][1]
        exps = [e.items()[0][1] for e in cns.right.exps]
        params = np.hstack([[np.log(c**(alpha)), e*alpha]
                            for c, e in zip(cnstr.right.cs, exps)])
        params = np.append(params, alpha)
        y, _ = softmax_affine(x, params)

    elif fittype == "ISMA":
        wvk = [vk for vk in cnstr.varkeys if vk.name == "w"][0]
        u1vk = [vk for vk in cnstr.varkeys if vk.name == "u_1"][0]
        alphas = [-1/ex[wvk] for ex in cnstr.left.exps]
        exps = [ex[u1vk] for ex in cnstr.left.exps]
        params = np.hstack([[np.log(c**a), e*a] for c, e, a in
                            zip(cns.left.cs, exps, alphas)])
        params = np.append(params, alphas)
        y, _ = implicit_softmax_affine(x, params)

    return y

if __name__ == "__main__":

    X, Y = fit_setup()
    cns, rm = fit(X, Y, 1, "ISMA")

    yfit = return_yfit(cns, X, "ISMA")

    fig, ax = plt.subplots()
    ax.plot(np.exp(X), np.exp(Y), "*")
    ax.plot(np.exp(X), np.exp(yfit))
    fig.savefig("testfit.pdf")
