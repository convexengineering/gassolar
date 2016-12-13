" fitting wind speed data "
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from gassolar.environment.wind_speeds import get_windspeed, interpolate
from gpfit.fit import fit
from gpfit.evaluate_fit import evaluate_fit
from gpfit.max_affine import max_affine
from gpfit.softmax_affine import softmax_affine
from gpfit.implicit_softmax_affine import implicit_softmax_affine
plt.rc("text", usetex=True)

PERCT_NORM = 100.0
WIND_NORM = 10.0

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
        wind.append(np.array(get_windspeed(latitude, p, altitude, 355))
                             / WIND_NORM)
        ps.append([p/PERCT_NORM]*len(altitude))

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

def plot_fits(xdata, ydata, yfit, latitude, rm=None):

    x1 = np.flipud(np.unique(xdata[0]))
    x2 = np.unique(xdata[1])
    colors = ["b", "r", "g", "m", "k", "y"]
    assert len(colors) == len(x2)
    fig, ax = plt.subplots()
    for p, y, yf, cl in zip(x2, ydata.reshape(len(x2), len(x1)),
                            yfit.reshape(len(x2), len(x1)), colors):
        ax.plot(np.exp(x1), np.exp(y)*WIND_NORM, "o", c=cl)
        ax.plot(np.exp(x1), np.exp(yf)*WIND_NORM, c=cl,
                label="%d Percentile Winds" % np.rint(np.exp(p)*PERCT_NORM))
    ax.legend(fontsize=8)
    ax.set_xlabel("Air Density $10^{-1}$ [kg/m$^3$]")
    ax.set_ylabel("Wind Speed [m/s]")
    ax.grid()
    if rm:
        ax.set_title("Latitude %d, RMS Error = %.3f" % (l, rm))
    else:
        ax.set_title("Latitude %d" % l)
    return fig, ax

if __name__ == "__main__":

    constraintlist = []
    data = {}

    # for l in range(20, 60, 1):
    for l in [40]:
        print "Fitting for %d latitude" % l
        altitudestart = range(40000, 50500, 500)
        for j, a in enumerate(altitudestart):
            X, Y = fit_setup(altitude=(a, 80000), latitude=l)
            tol = True
            i = 0
            while tol:
                if i > 5:
                    tol = False
                    continue
                else:
                    print "rms iter=%d" % i
                np.random.seed(i)
                cns, rm = fit(X, Y, 4, "SMA")
                if rm > 0.05:
                    i += 1
                    print "Latitude: %d     RMS Error: %.3f" % (l, rm)
                    continue
                yfit = evaluate_fit(cns, X, "SMA")
                if not hasattr(yfit, "__len__"):
                    i += 1
                    print "Params out of range"
                    continue
                else:
                    tol = False
            if rm < 0.05:
                print "RMS Error: %.3f after iter=%d, Altitude %d" % (rm, j, a)
                wvk = [vk for vk in cns.varkeys if vk.name == "w"][0]
                alpha = [ex[wvk] for ex in cns.left.exps][0]
                vkn = range(1, len(cns.varkeys))
                expos = np.array(
                    [e[list(cns.varkeys["u_%d" % n])[0]] for e in
                     cns.right.exps for n in vkn]).reshape(
                         len(cns.right.cs), len(vkn))
                params = np.hstack([np.hstack([c] + [ex]) for c, ex in
                                    zip(cns.right.cs, expos)])
                params = np.append(params, alpha)
                data[l] = params
                break
            else:
                print "RMS Error: %.3f, Alt iter=%d" % (rm, j)
        fig, ax = plot_fits(X, Y, yfit, l, rm=rm)
        fig.savefig("windfitl%d.pdf" % l)
        plt.close()

    df = pd.DataFrame(data).transpose()
    colnames = np.hstack([["c%d" % d, "e%d1" % d, "e%d2" % d] for d in
                          range(1, 5, 1)])
    colnames = np.append(colnames, "alpha")
    df.columns = colnames
    df.to_csv("windaltfitdata.csv")
