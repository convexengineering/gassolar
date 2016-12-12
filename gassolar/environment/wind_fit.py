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

def fit_setup(altitude=(40000, 80000), latitude=45):
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
    percentiles = range(75, 100, 5) + [99]
    altitude = np.linspace(altitude[0], altitude[1], N)
    df = pd.read_csv("usstd_atm.csv")
    wind = []
    ps = []
    for p in percentiles:
        wind.append(get_windspeed(latitude, p, altitude, 355))
        ps.append([p]*len(altitude))

    hm = altitude*0.3048
    density = []
    for h in hm:
        indh = df["Altitude"][df["Altitude"] > h].index[0]
        indl = indh-1
        xs = [df["Altitude"][indl], df["Altitude"][indh]]
        ys = [df["Density"][indl], df["Density"][indh]]
        density.append(interpolate(xs, ys, h))

    u1 = np.hstack([density]*len(percentiles))
    u2 = np.hstack(ps)
    w = np.hstack(wind)
    x = np.log([u1, u2])
    y = np.log(w)

    return x, y

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
    else:
        x = x.T

    if fittype == "MA":
        if not hasattr(cnstr, "__len__"):
            cnstr = [cnstr]
        vkn = range(1, len(cnstr[0].varkeys))
        expos = np.array(
            [cn.left.exp[list(cn.varkeys["u_%d" % n])[0]] for cn in cnstr
             for n in vkn]).reshape(len(cnstr), len(vkn))
        params = np.hstack([np.hstack([np.log(cn.left.c), ex])
                            for cn, ex in zip(cnstr, expos)])
        y, _ = max_affine(x, params)

    elif fittype == "SMA":
        wvk = [vk for vk in cnstr.varkeys if vk.name == "w"][0]
        alpha = [1/ex[wvk] for ex in cnstr.left.exps][0]
        vkn = range(1, len(cnstr.varkeys))
        expos = np.array(
            [e[list(cnstr.varkeys["u_%d" % n])[0]] for e in cnstr.right.exps
             for n in vkn]).reshape(len(cnstr.right.cs), len(vkn))
        params = np.hstack([np.hstack([np.log(c**(alpha))] + [ex*alpha])
                            for c, ex in zip(cnstr.right.cs, expos)])
        params = np.append(params, alpha)
        y, _ = softmax_affine(x, params)

    elif fittype == "ISMA":
        wvk = [vk for vk in cnstr.varkeys if vk.name == "w"][0]
        alphas = [-1/ex[wvk] for ex in cnstr.left.exps]
        vkn = range(1, len(cnstr.varkeys))
        expos = np.array(
            [e[list(cnstr.varkeys["u_%d" % n])[0]] for e in cnstr.left.exps
             for n in vkn]).reshape(len(cnstr.left.cs), len(vkn))
        params = np.hstack([np.hstack([np.log(c**a)] + [e*a]) for c, e, a in
                            zip(cns.left.cs, expos, alphas)])
        params = np.append(params, alphas)
        y, _ = implicit_softmax_affine(x, params)

    return y

def plot_fits(xdata, ydata, yfit):

    x1 = np.flipud(np.unique(xdata[0]))
    x2 = np.unique(xdata[1])
    colors = ["b", "r", "g", "m", "k", "y"]
    assert len(colors) == len(x2)
    fig, ax = plt.subplots()
    for p, y, yf, cl in zip(x2, ydata.reshape(len(x2), len(x1)),
                            yfit.reshape(len(x2), len(x1)), colors):
        ax.plot(np.exp(x1), np.exp(y), "o", c=cl)
        ax.plot(np.exp(x1), np.exp(yf), c=cl,
                label="%d Percentile Winds" % np.rint(np.exp(p)))
    ax.legend(fontsize=8)
    ax.set_xlabel("Air Density $10^{-1}$ [kg/m$^3$]")
    ax.set_ylabel("Wind Speed [m/s]")
    ax.grid()
    return fig, ax

if __name__ == "__main__":

    X, Y = fit_setup()
    cns, rm = fit(X, Y, 4, "SMA")

    yfit = return_yfit(cns, X, "SMA")
    fig, ax = plot_fits(X, Y, yfit)

    fig.savefig("testfit.pdf")
