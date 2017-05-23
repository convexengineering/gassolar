" fitting wind speed data "
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import sys
from gassolar.environment.wind_speeds import get_windspeed, interpolate
from gpfit.fit import fit
plt.rc("text", usetex=True)
plt.rcParams.update({'font.size':15})

GENERATE = False
PERCT_NORM = 100.0
WIND_NORM = 100.0
RHO_NORM = 1.0

def fit_setup(altitude=(40000, 80000), latitude=45, day=355):
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
        wind.append(np.array(get_windspeed(latitude, p, altitude, day))
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

    ax.fill_between(np.exp(x1), yfits[0], yfits[-1], alpha=0.2,
                    facecolor="#3E31AE", edgecolor="None")
    if not GENERATE:
        for i, p in enumerate(["75\%", "85\%", "95\%"]):
            ax.text(np.exp(x1)[0]+0.005, yfits[i][0]-1.0, p)
    ax.set_xlabel("Air Density [kg/m$^3$]")
    ax.set_ylabel("Wind Speed [m/s]")
    ax.legend(["ECF Wind Data", "GP approximation"], loc=2)
    ax.grid()
    return fig, ax

def make_fits(day, latrange, month, gen=False, path=""):

    for l in latrange:
        print "Fitting for %d latitude" % l
        altitudestart = range(40000, 50500, 500)
        for j, a in enumerate(altitudestart):
            print "Trying Altitude Range: %d-80000" % a
            X, Y = fit_setup(altitude=(a, 80000), latitude=l, day=day)
            rms_best = 1
            cn_best = None
            df_best = None
            yfit = None
            for K in range(2, 6):
                for ftype in ["MA", "SMA"]:
                    try:
                        cns, err = fit(X, Y, K, ftype)
                        print "Lat %d; K = %d; ftype = %s; RMS = %.4f" % (
                            l, K, ftype, err)
                    except ValueError:
                        print "Fit failed: Lat %d; K = %d; ftype = %s;" % (
                            l, K, ftype)
                        err = [0.9, 0.9]
                    if err < rms_best:
                        df = cns.get_dataframe(X)
                        if "0.0" in df.values or "inf" in df.values:
                            continue
                        rms_best = err
                        cn_best, df_best = cns, df

            if rms_best == 1:
                print "Nothing worked... trying new altitude range"
                continue
            elif rms_best < 0.05:
                print "success"
                if gen:
                    df_best.to_csv("windfits" + month
                                   + "/windaltfit_lat%d.csv" % l)
                else:
                    yfit = cn_best.evaluate(X)
                break
            else:
                print "Lowest RMS: %.3f, trying new altitude range" % rms_best
        if not gen:
            if not yfit is None:
                fig, ax = plot_fits(X, Y, yfit, l)
                fig.savefig(path + "windfitl%d.pdf" % l, bbox_inches="tight")
                plt.close()

if __name__ == "__main__":

    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = ""

    np.random.seed(0)

    mos = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep",
           "oct", "nov", "dec"]
    if GENERATE:
        latitude = range(20, 61, 1)
        for m in mos:
            make_fits(21, latitude, month=m, gen=GENERATE, path=path)
    else:
        latitude = [30]
        make_fits(355, latitude, month="dec", path=path)

