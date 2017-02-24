" fitting wind speed data "
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from gassolar.environment.wind_speeds import get_windspeed, interpolate
from gpfit.fit import fit
plt.rc("text", usetex=True)
plt.rcParams.update({'font.size':15})

GENERATE = False
PERCT_NORM = 100.0
WIND_NORM = 100.0
RHO_NORM = 1.0

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
    g = 9.80665 # m/s^2
    R = 287.04 # m^2/K/s^2
    T11 = 216.65 # K
    p = 22632*np.exp(-g/R/T11*(hm-11000))
    density = p/R/T11*RHO_NORM

    u1 = np.hstack([density]*len(percentiles))
    u2 = np.hstack(ps)
    w = np.hstack(wind)
    x = np.log([u1, u2])
    y = np.log(w)

    return x, y

def plot_fits(xdata, ydata, yfit, latitude):

    x1 = np.flipud(np.unique(xdata[0]))
    x2 = np.unique(xdata[1])
    colors = ["b", "r", "g", "m", "k", "y"]
    assert len(colors) == len(x2)
    fig, ax = plt.subplots()
    yfits = []
    for p, y, yf, cl in zip(x2, ydata.reshape(len(x2), len(x1)),
                            yfit.reshape(len(x2), len(x1)), colors):
        pp = np.exp(p)
        if pp == 0.75 or pp == 0.85 or pp == 0.95:
            ax.plot(np.exp(x1), np.exp(y)*WIND_NORM, "o", mec="k", mfc="none",
                    mew=1.5)
            yfits.append(np.exp(yf)*WIND_NORM)
            if pp == 0.85:
                wid = 2
            else:
                wid = 1
            ax.plot(np.exp(x1), np.exp(yf)*WIND_NORM, c="#3E31AE", lw=wid)
                    #label="%d Percentile Winds" % np.rint(np.exp(p)*PERCT_NORM))
    #ax.legend(loc=2, fontsize=15)
    ax.fill_between(np.exp(x1), yfits[0], yfits[-1], alpha=0.2,
                    facecolor="#3E31AE", edgecolor="None")
    if not GENERATE:
        for i, p in enumerate(["75\%", "85\%", "95\%"]):
            ax.text(np.exp(x1)[0]+0.005, yfits[i][0]-1.0, p)
    ax.set_xlabel("Air Density [kg/m$^3$]")
    ax.set_ylabel("Wind Speed [m/s]")
    ax.grid()
    return fig, ax

if __name__ == "__main__":

    if GENERATE:
        latitude = range(20, 61, 1)
    else:
        latitude = [35]

    constraintlist = []
    data = {}

    for l in latitude:
        print "Fitting for %d latitude" % l
        altitudestart = range(40000, 50500, 500)
        for j, a in enumerate(altitudestart):
            X, Y = fit_setup(altitude=(a, 80000), latitude=l)
            tol = True
            i = 0
            rms = []
            while tol:
                if i > 100:
                    tol = False
                    continue
                else:
                    print "rms iter=%d" % i
                np.random.seed(i)
                cns, rm = fit(X, Y, 4, "SMA")
                rms.append(rm)
                if rm > 0.05:
                    i += 1
                    print "Latitude: %d     RMS Error: %.3f" % (l, rm)
                    if rm > 0.06:
                        print "RMS too big... try new altitude range"
                        tol = False
                    if i > 10 and np.all(np.round(rms, 3), round(rm, 3)):
                        print "RPM not changing... try new altitude range"
                        tol = False
                    continue
                yfit = cns.evaluate(X)
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
                vkn = range(len(cns.right.varkeys))
                expos = np.array(
                    [e[list(cns.varkeys["u_fit_(%d,)" % n])[0]] for e in
                     cns.right.exps for n in vkn]).reshape(
                         len(cns.right.cs), len(vkn))
                params = np.hstack([l] + [np.hstack([c] + [ex]) for c, ex in
                                          zip(cns.right.cs, expos)])
                params = np.append(params, alpha)
                data["%d" % l] = params
                break
            else:
                print "RMS Error: %.3f, Alt iter=%d" % (rm, j)
        fig, ax = plot_fits(X, Y, yfit, l)
        if not GENERATE:
            fig.savefig("../../gassolarpaper/windfitl%d.pdf" % l,
                        bbox_inches="tight")
        plt.close()

    if GENERATE:
        df = pd.DataFrame(data).transpose()
        colnames = np.hstack([["c%d" % d, "e%d1" % d, "e%d2" % d] for d in
                              range(1, 5, 1)])
        colnames = np.append(colnames, "alpha")
        colnames = np.insert(colnames, 0, "latitude")
        df.columns = colnames
        df.to_csv("windaltfitdata.csv")
