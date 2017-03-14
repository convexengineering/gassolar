"wind_speeds.py"
import pandas as pd
import numpy as np
import os
import sys
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size':15})

PATH = (os.path.abspath(__file__).replace(os.path.basename(__file__), "")
        + "windspeeds" + os.sep)

def get_windspeed(latitude, perc, altitude, day, path=PATH):
    """
    Method to return windspeeds for different latitudes
    altitudes/percentiles

    Inputs
    ------
    latitude: latitude of the earth [deg]
    perc: percentile wind speed, only accepts [70, 75, 80, 95, 90, 95, 99]
    altitude: altitude [ft] (can be array or single value)
    path: terminal path to location of windspeed files

    Returns
    -------
    wind: wind speed [m/s] (array if altitude is array)
    """

    mos = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep",
           "oct", "nov", "dec"]
    dayinmo = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    moday = [sum(dayinmo[:i+1]) for i in range(len(dayinmo))]
    for i, mo in enumerate(moday):
        if mo > day:
            month = mos[i]
            break
    path += month + os.sep

    # pressure ranges for which there is data
    pressures = [5, 10, 30] + range(50, 1050, 50)
    pressures = np.array(pressures)
    filename = None

    if not hasattr(altitude, "__len__"):
        altitude = [altitude]

    wind = []
    for a in altitude:
        h = a*0.3048
        p = 101325.0/100*(1 - 2.25577e-5*h)**5.25588
        mb = [0]*2
        for i, pres in enumerate(pressures):
            if p < pressures[0]:
                mb[0] = pressures[0]
                mb[1] = pressures[0]
                break
            elif p > pressures[-1]:
                mb[0] = pressures[-1]
                mb[1] = pressures[-1]
                break
            if pres > p:
                mb[0] = pressures[i-1]
                mb[1] = pressures[i]
                break
        w = []
        for m in mb:
            filename = "%swind%d.%s.csv" % (path, m, month)
            df = pd.read_csv(filename)
            w.append(df[df["Latitude"] == latitude]["perc%d" % perc].item())

        wind.append(interpolate(mb, w, p))

    if len(wind) == 1:
        wind = wind[0]

    return wind

def interpolate(xs, ys, x):
    "interpolates between two points at some x location"
    y = ((ys[1]-ys[0])/(xs[1]-xs[0])*x +
         (ys[0]*xs[1] - ys[1]*xs[0])/(xs[1]-xs[0]))
    return y

if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = ""

    Fig, Ax = plt.subplots()
    # Colors = ["#253B6E", "#1F5F8B", "#1891AC"]
    Colors = ["#1C226B", "#3E31AE", "#4AA9AF"]
    lat = np.arange(70)
    for al, c in zip([15000, 50000, 60000], Colors):
        Wind85 = [get_windspeed(l, 80, al, 355) for l in lat]
        Wind90 = [get_windspeed(l, 90, al, 355) for l in lat]
        Wind95 = [get_windspeed(l, 95, al, 355) for l in lat]
        Ax.fill_betweenx(np.arange(70), Wind85, Wind95, alpha=0.5, facecolor=c)
        Ax.plot(Wind90, np.arange(70), c, label="Altitude=%d" % al, lw=2)
        if al == 50000:
            Ax.annotate("80%", xy=(Wind85[np.where(lat==31)[0][0]],31),
                        xytext=(3,0.1), textcoords="offset points",
                        arrowprops=dict(arrowstyle="-"), fontsize=12)
            Ax.annotate("90%", xy=(Wind90[np.where(lat==31)[0][0]],31),
                        xytext=(3,0.1), textcoords="offset points",
                        arrowprops=dict(arrowstyle="-"), fontsize=12)
            Ax.annotate("95%", xy=(Wind95[np.where(lat==31)[0][0]],31),
                        xytext=(3,0.1), textcoords="offset points",
                        arrowprops=dict(arrowstyle="-"), fontsize=12)
    Ax.set_ylabel("Latitude [deg]")
    Ax.set_xlabel("Wind speed [m/s]")
    Ax.set_ylim([0, 70])
    Ax.grid()
    Ax.legend(loc=2, fontsize=15)
    # Ax.set_title("85%-95% Wind Speeds in Dec")
    Fig.savefig(path + "latvswind.pdf", bbox_inches="tight")

    Fig, Ax = plt.subplots()
    Alt = range(1000, 80000, 1000)
    Colors = ["#470031", "#971549", "#CF455C"]
    for l, c in zip([30, 35, 45], Colors):
        Wind85 = get_windspeed(l, 80, Alt, 355)
        Wind90 = get_windspeed(l, 90, Alt, 355)
        Wind95 = get_windspeed(l, 95, Alt, 355)
        Ax.fill_betweenx(Alt, Wind85, Wind95, alpha=0.5, facecolor=c)
        Ax.plot(Wind90, Alt, c, label="Latitude=%d" % l, lw=2)
        if l == 45:
            Ax.annotate("80%", xy=(Wind85[Alt.index(63000)], 63000),
                        xytext=(8,-0.1), textcoords="offset points",
                        arrowprops=dict(arrowstyle="-"), fontsize=12)
            Ax.annotate("90%", xy=(Wind90[Alt.index(63000)], 63000),
                        xytext=(8,-0.1), textcoords="offset points",
                        arrowprops=dict(arrowstyle="-"), fontsize=12)
            Ax.annotate("95%", xy=(Wind95[Alt.index(63000)], 63000),
                        xytext=(8,-0.1), textcoords="offset points",
                        arrowprops=dict(arrowstyle="-"), fontsize=12)

    # Ax.plot([0, 80], [15000, 15000], "k", lw=2)
    # Ax.fill_between(np.linspace(0, 80, 10), 12000, 15000, hatch="//", facecolor="None", edgecolor="k", linewidth=0.0)
    # Ax.text(64, 18000, "$h_{\\mathrm{min}}$", fontsize=15)
    Ax.set_ylabel("Altitude [ft]")
    Ax.set_xlabel("Wind speed [m/s]")
    Ax.set_ylim([0, 80000])
    Ax.set_xlim([0, 80])
    Ax.grid()
    Ax.legend(loc=1, fontsize=15)
    # Ax.set_title("85%-95% Wind Speeds in Dec")
    Fig.savefig(path + "altvswind.pdf", bbox_inches="tight")

    Fig, Ax = plt.subplots()
    Colors = ["#1C226B", "#3E31AE", "#4AA9AF"]
    Mos = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep",
           "oct", "nov", "dec", "jan"]
    Dayinmo = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    Moday = [sum(Dayinmo[:i+1]) for i in range(len(Dayinmo))]
    Mid = [(Moday[i]+Moday[i+1])/2 for i in range(len(Moday)-1)]
    for al, c in zip([15000, 50000, 60000], Colors):
        Wind85 = [get_windspeed(30, 80, al, d) for d in Mid]
        Wind90 = [get_windspeed(30, 90, al, d) for d in Mid]
        Wind95 = [get_windspeed(30, 95, al, d) for d in Mid]
        Ax.fill_between(range(13), Wind85 + [Wind85[0]], Wind95 + [Wind95[0]],
                        alpha=0.5, facecolor=c)
        Ax.plot(range(13), Wind90 + [Wind90[0]], c, label="Altitude=%d" % al, lw=2)
        if al == 50000:
            Ax.annotate("80%", xy=(1, Wind85[1]),
                        xytext=(3,0.1), textcoords="offset points",
                        arrowprops=dict(arrowstyle="-"), fontsize=12)
            Ax.annotate("90%", xy=(1, Wind90[1]),
                        xytext=(3,0.1), textcoords="offset points",
                        arrowprops=dict(arrowstyle="-"), fontsize=12)
            Ax.annotate("95%", xy=(1, Wind95[1]),
                        xytext=(3,0.1), textcoords="offset points",
                        arrowprops=dict(arrowstyle="-"), fontsize=12)
    Ax.set_xticks(np.arange(12))
    Ax.set_xticks(np.arange(12)+0.5, minor=True)
    Ax.set_xticklabels(Mos, minor=True)
    Ax.set_xticklabels([])
    Ax.set_ylabel("Wind speed [m/s]")
    Ax.set_ylim([0, 60])
    Ax.grid()
    Ax.legend(loc=1, fontsize=15)
    # Ax.set_title("85%-95% Wind Speeds at 45 deg Lat")
    Fig.savefig(path + "windvsmonth.pdf", bbox_inches="tight")
