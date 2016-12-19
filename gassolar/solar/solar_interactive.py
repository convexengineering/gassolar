" Simple Solar-Electric Powered Aircraft Model "
import pandas as pd
import numpy as np
from numpy import pi
import matplotlib.pyplot as plt
import os
from solar_irradiance import get_Eirr
from gpkit import Model, Variable, Vectorize
from gpkitmodels.helpers import summing_vars
from constant_taper_chord import c_bar
from gpfit.softmax_affine import softmax_affine

path = "/" + os.path.abspath(__file__).replace(os.path.basename(__file__), "").replace("/solar/", "/environment/")
DF = pd.read_csv(path + "windaltfitdata.csv")

class Aircraft(Model):
    "vehicle"
    def setup(self):

        self.solarcells = SolarCells()
        self.wing = Wing(hollow=True)
        self.battery = Battery()

        self.components = [self.solarcells, self.wing, self.battery]

        Wpay = Variable("W_{pay}", 10, "lbf", "payload")
        Wtotal = Variable("W_{total}", "lbf", "aircraft weight")
        Wwing = Variable("W_{wing}", "lbf", "wing weight")

        constraints = [
            Wtotal >= (Wpay + sum(summing_vars(self.components, "W"))),
            Wwing >= (sum(summing_vars([self.wing, self.battery], "W"))),
            self.solarcells["S"] <= self.wing["S"],
            self.wing["c_{MAC}"]**2*0.5*self.wing["\\tau"]*self.wing["b"] >= (
                self.battery["\\mathcal{V}"])]

        return constraints, self.components

    def flight_model(self, state):
        return AircraftPerf(self, state)

    def loading(self, Wcent, Wwing, V, CL):
        return AircraftLoading(self, Wcent, Wwing, V, CL)

class Wing(Model):
    "The thing that creates the lift"
    def setup(self, N=5, lam=0.5, spar="CapSpar", hollow=False):

        W = Variable("W", "lbf", "weight")
        mfac = Variable("m_{fac}", 1.2, "-", "wing weight margin factor")
        S = Variable("S", "ft^2", "surface area")
        AR = Variable("AR", "-", "aspect ratio")
        b = Variable("b", "ft", "wing span")
        tau = Variable("\\tau", 0.115, "-", "airfoil thickness ratio")
        CLmax = Variable("C_{L_{max}}", 1.39, "-", "maximum CL of JHO1")
        CM = Variable("C_M", 0.14, "-", "wing moment coefficient")
        mw = Variable("m_w", 2.0*np.pi/(1+2.0/23), "-",
                      "assumed span wise effectiveness")
        croot = Variable("c_{root}", "ft", "root chord")
        cmac = Variable("c_{MAC}", "ft", "mean aerodynamic chord")
        lamw = Variable("\\lambda", lam, "-", "wing taper ratio")
        cb, _ = c_bar(lam, N)
        with Vectorize(N):
            cbar = Variable("\\bar{c}", cb, "-",
                            "normalized chord at mid element")
        with Vectorize(N-1):
            cbave = Variable("\\bar{c}_{ave}", (cb[1:]+cb[:-1])/2, "-",
                             "normalized mid section chord")
            cave = Variable("c_{ave}", "ft", "mid section chord")

        constraints = [b**2 == S*AR,
                       lamw == lamw,
                       cbar == cbar,
                       cave == cbave*S/b,
                       croot == S/b*cb[0],
                       cmac == S/b]

        if spar == "CapSpar":
            self.spar = CapSpar(b, cave, tau, N)
        elif spar == "TubeSpar":
            self.spar = TubeSpar(b, cave, tau, N)
        self.wingskin = WingSkin(S, croot, b)
        self.components = [self.spar, self.wingskin]

        if not hollow:
            self.winginterior = WingInterior(cave, b, N)
            self.components.extend([self.winginterior])

        constraints.extend([W/mfac >= sum(c["W"] for c in self.components)])

        return self.components, constraints

    def flight_model(self, state):
        return WingAero(self, state)

    def loading(self, Wcent, Wwing=None, V=None, CL=None):
        return WingLoading(self, Wcent, Wwing, V, CL)

class WingSkin(Model):
    "wing skin model"
    def setup(self, S, croot, b):

        rhocfrp = Variable("\\rho_{CFRP}", 1.4, "g/cm^3", "density of CFRP")
        W = Variable("W", "lbf", "wing skin weight")
        g = Variable("g", 9.81, "m/s^2", "gravitational acceleration")
        t = Variable("t", "in", "wing skin thickness")
        tmin = Variable("t_{min}", 0.012, "in",
                        "minimum gague wing skin thickness")
        Jtbar = Variable("\\bar{J/t}", 0.01114, "1/mm",
                         "torsional moment of inertia")

        constraints = [W >= rhocfrp*S*2*t*g,
                       t >= tmin,
                       b == b,
                       croot == croot]

        return constraints

    def loading(self):
        return WingSkinL(self)

class WingSkinL(Model):
    "wing skin loading model for torsional loads in skin"
    def setup(self, static):

        taucfrp = Variable("\\tau_{CFRP}", 570, "MPa", "torsional stress limit")
        Cmw = Variable("C_{m_w}", 0.121, "-", "negative wing moment coefficent")
        rhosl = Variable("\\rho_{sl}", 1.225, "kg/m^3",
                         "air density at sea level")
        Vne = Variable("V_{NE}", 45, "m/s", "never exceed vehicle speed")

        constraints = [
            taucfrp >= (1/static["\\bar{J/t}"]/(static["c_{root}"])**2
                        / static["t"]*Cmw*static["S"]*rhosl*Vne**2)]

        return constraints

class CapSpar(Model):
    "cap spar model"
    def setup(self, b, cave, tau, N=5):
        self.N = N

        # phyiscal properties
        rhocfrp = Variable("\\rho_{CFRP}", 1.4, "g/cm^3", "density of CFRP")
        E = Variable("E", 2e7, "psi", "Youngs modulus of CFRP")

        with Vectorize(self.N-1):
            t = Variable("t", "in", "spar cap thickness")
            hin = Variable("h_{in}", "in", "inner spar height")
            w = Variable("w", "in", "spar width")
            I = Variable("I", "m^4", "spar x moment of inertia")
            Sy = Variable("S_y", "m**3", "section modulus")
            dm = Variable("dm", "kg", "segment spar mass")

        W = Variable("W", "lbf", "spar weight")
        w_lim = Variable("w_{lim}", 0.15, "-", "spar width to chord ratio")
        g = Variable("g", 9.81, "m/s^2", "gravitational acceleration")

        constraints = [I <= 2*w*t*(hin/2)**2,
                       dm >= rhocfrp*w*t*b/(self.N-1),
                       W >= 2*dm.sum()*g,
                       w <= w_lim*cave,
                       cave*tau >= hin + 2*t,
                       Sy*(hin + t) <= I,
                      ]

        return constraints

    def loading(self, Wcent):
        return ChordSparL(self, Wcent)

    def gustloading(self, Wcent, Wwing, V, CL):
        return GustL(self, Wcent, Wwing, V, CL)

class Beam(Model):
    "discretized beam bending model"
    def setup(self, N, qbar):

        with Vectorize(N-1):
            EIbar = Variable("\\bar{EI}", "-",
                             "normalized YM and moment of inertia")

        with Vectorize(N):
            Sbar = Variable("\\bar{S}", "-", "normalized shear")
            Mbar = Variable("\\bar{M}", "-", "normalized moment")
            th = Variable("\\theta", "-", "deflection slope")
            dbar = Variable("\\bar{\\delta}", "-", "normalized displacement")


        Sbartip = Variable("\\bar{S}_{tip}", 1e-10, "-", "Tip loading")
        Mbartip = Variable("\\bar{M}_{tip}", 1e-10, "-", "Tip moment")
        throot = Variable("\\theta_{root}", 1e-10, "-", "Base angle")
        dbarroot = Variable("\\bar{\\delta}_{root}", 1e-10, "-",
                            "Base deflection")
        dx = Variable("dx", "-", "normalized length of element")

        constraints = [
            Sbar[:-1] >= Sbar[1:] + 0.5*dx*(qbar[:-1] + qbar[1:]),
            Sbar[-1] >= Sbartip,
            Mbar[:-1] >= Mbar[1:] + 0.5*dx*(Sbar[:-1] + Sbar[1:]),
            Mbar[-1] >= Mbartip,
            th[0] >= throot,
            th[1:] >= th[:-1] + 0.5*dx*(Mbar[1:] + Mbar[:-1])/EIbar,
            dbar[0] >= dbarroot,
            dbar[1:] >= dbar[:-1] + 0.5*dx*(th[1:] + th[:-1]),
            1 == (N-1)*dx,
            ]

        return constraints

class ChordSparL(Model):
    "spar loading model"
    def setup(self, static, Wcent):

        Nmax = Variable("N_{max}", 5, "-", "max loading")
        cbar, _ = c_bar(0.5, static.N)
        sigmacfrp = Variable("\\sigma_{CFRP}", 475e6, "Pa", "CFRP max stress")
        kappa = Variable("\\kappa", 0.2, "-", "max tip deflection ratio")

        with Vectorize(static.N-1):
            Mr = Variable("M_r", "N*m", "wing section root moment")

        with Vectorize(static.N):
            qbar = Variable("\\bar{q}", cbar, "-", "normalized loading")

        beam = Beam(static.N, qbar)

        constraints = [
            # dimensionalize moment of inertia and young's modulus
            beam["\\bar{EI}"] <= (8*static["E"]*static["I"]/Nmax
                                  / Wcent/static["b"]**2),
            Mr == (beam["\\bar{M}"][:-1]*Wcent*Nmax*static["b"]/4),
            sigmacfrp >= Mr/static["S_y"],
            beam["\\bar{\\delta}"][-1] <= kappa,
            ]

        return beam, constraints

class GustL(Model):
    "spar loading model"
    def setup(self, static, Wcent, Wwing, V, CL):

        Nmax = Variable("N_{max}", 5, "-", "max loading")
        cbar, eta = c_bar(0.5, static.N)
        sigmacfrp = Variable("\\sigma_{CFRP}", 475e6, "Pa", "CFRP max stress")
        kappa = Variable("\\kappa", 0.2, "-", "max tip deflection ratio")

        with Vectorize(static.N-1):
            Mr = Variable("M_r", "N*m", "wing section root moment")

        vgust = Variable("V_{gust}", 10, "m/s", "gust velocity")
        agust = Variable("\\alpha_{gust}", "-", "gust angle of attack")

        with Vectorize(static.N):
            qbar = Variable("\\bar{q}", "-", "normalized loading")
            cosminus1 = Variable("1-cos(\\eta)", (1-np.cos(eta)/2)**2, "-",
                                 "1 minus cosine factor")

        beam = Beam(static.N, qbar)

        constraints = [
            # fit for arctan from 0 to 1, RMS = 0.055
            agust == 0.874071*(vgust/V)**0.958316,
            qbar >= 2*pi/CL*(1+Wcent/Wwing)*cosminus1*agust,
            # dimensionalize moment of inertia and young's modulus
            beam["\\bar{EI}"] <= (8*static["E"]*static["I"]/Nmax
                                  / Wwing/static["b"]**2),
            Mr == (beam["\\bar{M}"][:-1]*Wwing*Nmax*static["b"]/4),
            sigmacfrp >= Mr/static["S_y"],
            beam["\\bar{\\delta}"][-1] <= kappa,
            ]

        return beam, constraints

class WingLoading(Model):
    "wing loading cases"
    def setup(self, wing, Wcent, Wwing=None, V=None, CL=None):

        loading = [wing.wingskin.loading()]
        loading.append(wing.spar.loading(Wcent))
        if Wwing:
            loading.append(wing.spar.gustloading(Wcent, Wwing, V, CL))

        return loading

class WingAero(Model):
    "wing aerodynamic model with profile and induced drag"
    def setup(self, static, state):
        "wing drag model"
        Cd = Variable("C_d", "-", "wing drag coefficient")
        CL = Variable("C_L", "-", "lift coefficient")
        e = Variable("e", 0.9, "-", "Oswald efficiency")
        Re = Variable("Re", "-", "Reynold's number")
        cdp = Variable("c_{dp}", "-", "wing profile drag coeff")

        constraints = [
            Cd >= cdp + CL**2/np.pi/static["AR"]/e,
            cdp**3.72 >= (0.0247*CL**2.49*Re**-1.11
                          + 2.03e-7*CL**12.7*Re**-0.338
                          + 6.35e10*CL**-0.243*Re**-3.43
                          + 6.49e-6*CL**-1.9*Re**-0.681),
            Re == state["\\rho"]*state["V"]*static["c_{MAC}"]/state["\\mu"],
            ]

        return constraints

class AircraftLoading(Model):
    "aircraft loading cases"
    def setup(self, aircraft, Wcent, Wwing, V, CL):

        loading = aircraft.wing.loading(Wcent, Wwing, V, CL)

        return loading

class Battery(Model):
    "battery model"
    def setup(self):

        W = Variable("W", "lbf", "battery weight")
        eta_charge = Variable("\\eta_{charge}", 0.98, "-",
                              "Battery charging efficiency")
        eta_discharge = Variable("\\eta_{discharge}", 0.98, "-",
                                 "Battery discharging efficiency")
        E = Variable("E", "J", "total battery energy")
        g = Variable("g", 9.81, "m/s**2", "gravitational constant")
        hbatt = Variable("h_{batt}", 350, "W*hr/kg", "battery energy density")
        vbatt = Variable("(E/\\mathcal{V})", 800, "W*hr/l",
                         "volume battery energy density")
        Volbatt = Variable("\\mathcal{V}", "m**3", "battery volume")

        constraints = [W >= E/hbatt*g,
                       Volbatt >= E/vbatt,
                       eta_charge == eta_charge,
                       eta_discharge == eta_discharge]

        return constraints

    def flight_model(self, state):
        return BatteryPerf(self, state)

class BatteryPerf(Model):
    "battery performance model"
    def setup(self, static, state):

        Poper = Variable("P_{oper}", "W", "operating power")

        constraints = [
            static["E"] >= Poper*state["t_{night}"]/static["\\eta_{discharge}"]]

        return constraints

class SolarCells(Model):
    "solar cell model"
    def setup(self):

        rhosolar = Variable("\\rho_{solar}", 0.3, "kg/m^2",
                            "solar cell area density")
        g = Variable("g", 9.81, "m/s**2", "gravitational constant")
        S = Variable("S", "ft**2", "solar cell area")
        W = Variable("W", "lbf", "solar cell weight")

        constraints = [W >= rhosolar*S*g]

        return constraints

    def flight_model(self, state):
        return SolarCellPerf(self, state)

class SolarCellPerf(Model):
    "collecting solar cell energy"
    def setup(self, static, state):

        E = Variable("E", "J", "solar cell energy collected")
        etasolar = Variable("\\eta_{solar}", 0.2, "-",
                            "Solar cell efficiency")

        constraints = [
            state["(E/S)_{irr}"]*etasolar*static["S"] >= E]

        return constraints

class AircraftPerf(Model):
    "aircraft performance"
    def setup(self, static, state):

        self.wing = static.wing.flight_model(state)
        self.solarcells = static.solarcells.flight_model(state)
        self.battery = static.battery.flight_model(state)

        self.flight_models = [self.wing, self.solarcells, self.battery]

        CD = Variable("C_D", "-", "aircraft drag coefficient")
        cda0 = Variable("CDA_0", 0.005, "-", "non-wing drag coefficient")
        Pshaft = Variable("P_{shaft}", "hp", "shaft power")
        Pacc = Variable("P_{acc}", 0.0, "W", "Accessory power draw")
        constraints = [
            ]

        constraints = [
            CD >= cda0 + self.wing["C_d"],
            self.solarcells["E"] >= (
                self.battery["P_{oper}"]*state["t_{day}"]
                + self.battery["E"]/static.battery["\\eta_{discharge}"]),
            self.battery["P_{oper}"] >= Pacc + Pshaft
            ]

        return self.flight_models, constraints

class FlightState(Model):
    """
    environmental state of aircraft

    inputs
    ------
    latitude: earth latitude [deg]
    altitude: flight altitude [ft]
    percent: percentile wind speeds [%]
    day: day of the year [Jan 1st = 1]
    """
    def setup(self, latitude=45, day=355):

        df = DF[DF["latitude"] == latitude]
        esirr, td, tn = get_Eirr(latitude, day)

        Vwind = Variable("V_{wind}", "m/s", "wind velocity")
        V = Variable("V", "m/s", "true airspeed")
        rho = Variable("\\rho", "kg/m**3", "air density")
        mu = Variable("\\mu", 1.42e-5, "N*s/m**2", "viscosity")
        ESirr = Variable("(E/S)_{irr}", esirr, "W*hr/m^2",
                         "Average daytime solar energy")
        tday = Variable("t_{day}", td, "hr", "Daylight span")
        tnight = Variable("t_{night}", tn, "hr", "Night span")
        pct = Variable("p_{wind}", 0.9, "-", "percentile wind speeds")
        Vwindref = Variable("V_{wind-ref}", 100.0, "m/s",
                            "reference wind speed")
        rhoref = Variable("\\rho_{ref}", 1.0, "kg/m**3",
                          "reference air density")
        mfac = Variable("m_{fac}", 1.0, "-", "wind speed margin factor")

        constraints = [
            V/mfac >= Vwind,
            rho == rho,
            mu == mu,
            ESirr == ESirr,
            tday == tday,
            tnight == tnight,
            (Vwind/Vwindref)**df["alpha"].iloc[0] >= (
                sum([df["c%d" % i]*(rho/rhoref)**df["e%d1" % i]
                     * pct**df["e%d2" % i] for i in range(1, 5)]).iloc[0])
            ]

        return constraints

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

class FlightSegment(Model):
    "flight segment"
    def setup(self, aircraft, etap=0.7, latitude=35, day=355):

        self.aircraft = aircraft
        self.fs = FlightState(latitude=latitude, day=day)
        self.aircraftPerf = self.aircraft.flight_model(self.fs)
        self.slf = SteadyLevelFlight(self.fs, self.aircraft,
                                     self.aircraftPerf, etap)

        self.submodels = [self.fs, self.aircraftPerf, self.slf]

        return self.aircraft, self.submodels

class SteadyLevelFlight(Model):
    "steady level flight model"
    def setup(self, state, aircraft, perf, etap):

        T = Variable("T", "N", "thrust")
        etaprop = Variable("\\eta_{prop}", etap, "-", "propulsive efficiency")

        constraints = [
            aircraft["W_{total}"] <= (
                0.5*state["\\rho"]*state["V"]**2*perf["C_L"]
                * aircraft.wing["S"]),
            T >= (0.5*state["\\rho"]*state["V"]**2*perf["C_D"]
                  *aircraft.wing["S"]),
            perf["P_{shaft}"] >= T*state["V"]/etaprop]

        return constraints

class Mission(Model):
    "define mission for aircraft"
    def setup(self, latitude=35, day=355):

        Wcent = Variable("W_{cent}", "lbf", "center weight")

        self.solar = Aircraft()
        self.mission = []
        for l in range(20, latitude+1, 1):
            self.mission.append(FlightSegment(self.solar, latitude=l, day=day))
        loading = self.solar.loading(Wcent, self.solar["W_{wing}"], self.mission[-1]["V"], self.mission[-1]["C_L"])
        for vk in loading.varkeys["N_{max}"]:
            loading.substitutions.update({vk: 2})

        constraints = [Wcent >= self.solar["W_{pay}"]]

        return self.solar, self.mission, loading, constraints

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
    ax.plot(altsol/1000, vsol, "*")
    ax.set_xlabel("Altitude [kft]")
    ax.set_ylabel("Aircraft Velocity [knots]")
    ax.grid()
    ax.set_ylim([0, 200])
    fig.savefig("solaltitude%d.pdf" % latitude)

if __name__ == "__main__":
    M = Mission(latitude=21)
    M.cost = M["W_{total}"]
    sol = M.solve("mosek")

    M.cost = M["b"]
    sol = M.solve("mosek")

    M.cost = M["S_Mission, Aircraft, SolarCells"]
    sol = M.solve("mosek")

    for l in range(21, 38):
        M = Mission(latitude=l)
        M.cost = M["W_{total}"]
        sol = M.solve("mosek")
        windalt_plot(l, sol)
