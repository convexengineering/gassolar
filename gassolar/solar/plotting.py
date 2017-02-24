import numpy as np
import matplotlib.pyplot as plt
from gpfit.softmax_affine import softmax_affine
import os
import pandas as pd

path = os.path.abspath(__file__).replace(os.path.basename(__file__), "").replace(os.sep+"solar"+os.sep, os.sep+"environment"+os.sep)
path = "/Users/mjburton11/MIT/GPKIT/gpkit-projects/gas_solar_trade/gassolar/environment/"
DF = pd.read_csv(path + "windaltfitdata.csv")

def windalt_plot(latitude, sol1=None, sol2=None):
    plt.rcParams.update({'font.size':15})
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
    l = ax.plot(alt/1000.0, vwind*1.95384, linewidth=2)
    if sol1:
        if sol2:
            sols = [sol1, sol2]
        else:
            sols = [sol1]
        for sol in sols:
            altsol = altitude(min([sol(sv).magnitude for sv in sol("\\rho")]))
            vsol = max([sol(sv).to("knots").magnitude for sv in sol("V")])
            ax.plot(altsol/1000, vsol, "o", markersize=10, mfc="c")
    ax.set_xlabel("Altitude [kft]")
    ax.set_ylabel("90th Percentile Wind Speed [knots]")
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


from math import atan2,degrees
import numpy as np

#Label line with line2D label data
def labelLine(line,x,label=None,align=True,**kwargs):

    ax = line.get_axes()
    xdata = line.get_xdata()
    ydata = line.get_ydata()
    if (x < xdata[0]) or (x > xdata[-1]):
        print('x label location is outside data range!')
        return

    #Find corresponding y co-ordinate and angle of the
    ip = 1
    for i in range(len(xdata)):
        if x < xdata[i]:
            ip = i
            break

    y = ydata[ip-1] + (ydata[ip]-ydata[ip-1])*(x-xdata[ip-1])/(xdata[ip]-xdata[ip-1])
    if not label:
        label = line.get_label()

    if align:
        #Compute the slope
        dx = xdata[ip] - xdata[ip-1]
        dy = ydata[ip] - ydata[ip-1]
        ang = degrees(atan2(dy,dx))

        #Transform to screen co-ordinates
        pt = np.array([x,y]).reshape((1,2))
        trans_angle = ax.transData.transform_angles(np.array((ang,)),pt)[0]

    else:
        trans_angle = 0

    #Set a bunch of keyword arguments
    if 'color' not in kwargs:
        kwargs['color'] = line.get_color()

    if ('horizontalalignment' not in kwargs) and ('ha' not in kwargs):
        kwargs['ha'] = 'center'

    if ('verticalalignment' not in kwargs) and ('va' not in kwargs):
        kwargs['va'] = 'center'

    if 'backgroundcolor' not in kwargs:
        kwargs['backgroundcolor'] = ax.get_axis_bgcolor()

    if 'clip_on' not in kwargs:
        kwargs['clip_on'] = True

    if 'zorder' not in kwargs:
        kwargs['zorder'] = 2.5

    ax.text(x,y,label,rotation=trans_angle,**kwargs)

def labelLines(lines,align=True,xvals=None,zorder=[],**kwargs):

    ax = lines[0].get_axes()
    labLines = []
    labels = []

    #Take only the lines which have labels other than the default ones
    for line in lines:
        label = line.get_label()
        if "_line" not in label:
            labLines.append(line)
            labels.append(label)

    if xvals is None:
        xmin,xmax = ax.get_xlim()
        xvals = np.linspace(xmin,xmax,len(labLines)+2)[1:-1]

    for line,x,label,zo in zip(labLines,xvals,labels, zorder):
        labelLine(line,x,label,align,zorder=zo,**kwargs)
