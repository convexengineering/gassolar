" Simple Solar-Electric Powered Aircraft Model "
#pylint: disable=attribute-defined-outside-init, invalid-name, unused-variable
#pylint: disable=too-many-locals
import os
import sys
import pandas as pd
import numpy as np
from gassolar.environment.solar_irradiance import get_Eirr, twi_fits
from gpkit import Model, Variable
from gpkit.tests.helpers import StdoutCaptured
from gpkitmodels.GP.aircraft.wing.wing import Wing as WingGP
from gpkitmodels.SP.aircraft.wing.wing import Wing as WingSP
from gpkitmodels.GP.aircraft.tail.empennage import Empennage
from gpkitmodels.GP.aircraft.tail.tail_boom import TailBoomState
from gpkitmodels.SP.aircraft.tail.tail_boom_flex import TailBoomFlexibility
from gpkitmodels.tools.summing_constraintset import summing_vars
from gpkitmodels.tools.fit_constraintset import FitCS

basepath = os.path.abspath(__file__).replace(os.path.basename(__file__), "")
path = basepath.replace(os.sep+"solar"+os.sep, os.sep+"environment"+os.sep)
DF = pd.read_csv(path + "windaltfitdata.csv")
DFt = pd.read_csv(path + "solar_twlightfit.csv")
DFd = pd.read_csv(path + "solar_dayfit.csv")

class Aircraft(Model):
    "vehicle"
    def setup(self, sp=False):

        self.sp = sp
        self.solarcells = SolarCells()
        if sp:
            self.wing = WingSP(hollow=True)
        else:
            self.wing = WingGP(hollow=True)
        self.battery = Battery()
        self.empennage = Empennage()
        self.motor = Motor()

        self.components = [self.solarcells, self.wing, self.battery,
                           self.empennage, self.motor]

        Wpay = Variable("W_{pay}", 10, "lbf", "payload weight")
        Wtotal = Variable("W_{total}", "lbf", "aircraft weight")
        Wwing = Variable("W_{wing}", "lbf", "wing weight")
        Wcent = Variable("W_{cent}", "lbf", "center weight")

        self.empennage.substitutions["V_v"] = 0.04

        if not sp:
            self.empennage.substitutions["V_h"] = 0.45
            self.empennage.substitutions["AR_h"] = 5.0
            self.empennage.substitutions["m_h"] = 0.1

        constraints = [
            Wtotal >= (Wpay + sum(summing_vars(self.components, "W"))),
            Wwing >= (sum(summing_vars([self.wing, self.battery,
                                        self.solarcells], "W"))),
            Wcent >= Wpay + sum(summing_vars([self.empennage, self.motor],
                                             "W")),
            self.solarcells["S"] <= self.wing["S"],
            self.wing["c_{MAC}"]**2*0.5*self.wing["\\tau"]*self.wing["b"] >= (
                self.battery["\\mathcal{V}"]),
            self.empennage.horizontaltail["V_h"] <= (
                self.empennage.horizontaltail["S"]
                * self.empennage.horizontaltail["l_h"]/self.wing["S"]**2
                * self.wing["b"]),
            self.empennage.verticaltail["V_v"] <= (
                self.empennage.verticaltail["S"]
                * self.empennage.verticaltail["l_v"]/self.wing["S"]
                / self.wing["b"]),
            self.empennage.tailboom["d_0"] <= (
                self.wing["\\tau"]*self.wing["c_{root}"])
            ]

        return constraints, self.components

    def flight_model(self, state):
        " what happens during flight "
        return AircraftPerf(self, state)

    def loading(self, Wcent, Wwing, V, CL):
        " loading for all components "
        if self.sp:
            return AircraftLoadingSP(self, Wcent, Wwing, V, CL)
        else:
            return AircraftLoading(self, Wcent, Wwing, V, CL)

class Motor(Model):
    "the thing that provides power"
    def setup(self):

        W = Variable("W", "lbf", "motor weight")
        Pmax = Variable("P_{max}", "W", "max power")
        Bpm = Variable("B_{PM}", 4140.8, "W/kg", "power mass ratio")
        m = Variable("m", "kg", "motor mass")
        g = Variable("g", 9.81, "m/s**2", "gravitational constant")
        eta = Variable("\\eta", 0.95, "-", "motor efficiency")

        constraints = [Pmax == Bpm*m,
                       W >= m*g]

        return constraints

class AircraftLoading(Model):
    "aircraft loading cases"
    def setup(self, aircraft, Wcent, Wwing, V, CL):

        loading = [aircraft.wing.loading(Wcent, Wwing, V, CL)]
        loading.append(aircraft.empennage.loading())

        return loading

class AircraftLoadingSP(Model):
    "aircraft loading cases"
    def setup(self, aircraft, Wcent, Wwing, V, CL):

        loading = [aircraft.wing.loading(Wcent, Wwing, V, CL)]
        loading.append(aircraft.empennage.loading())

        tbstate = TailBoomState()
        loading.append(TailBoomFlexibility(aircraft.empennage.horizontaltail,
                                           aircraft.empennage.tailboom,
                                           aircraft.wing, tbstate))

        return loading

class Battery(Model):
    "battery model"
    def setup(self):

        W = Variable("W", "lbf", "battery weight")
        eta_charge = Variable("\\eta_{charge}", 0.98, "-",
                              "charging efficiency")
        eta_discharge = Variable("\\eta_{discharge}", 0.98, "-",
                                 "discharging efficiency")
        E = Variable("E", "J", "total battery energy")
        g = Variable("g", 9.81, "m/s**2", "gravitational constant")
        hbatt = Variable("h_{batt}", 350, "W*hr/kg", "battery specific energy")
        vbatt = Variable("(E/\\mathcal{V})", 800, "W*hr/l",
                         "volume battery energy density")
        Volbatt = Variable("\\mathcal{V}", "m**3", "battery volume")

        constraints = [W >= E/hbatt*g,
                       Volbatt >= E/vbatt,
                       eta_charge == eta_charge,
                       eta_discharge == eta_discharge]

        return constraints

class SolarCells(Model):
    "solar cell model"
    def setup(self):

        rhosolar = Variable("\\rho_{solar}", 0.27, "kg/m^2",
                            "solar cell area density")
        g = Variable("g", 9.81, "m/s**2", "gravitational constant")
        S = Variable("S", "ft**2", "solar cell area")
        W = Variable("W", "lbf", "solar cell weight")
        etasolar = Variable("\\eta", 0.22, "-", "solar cell efficiency")

        constraints = [W >= rhosolar*S*g]

        return constraints

class AircraftPerf(Model):
    "aircraft performance"
    def setup(self, static, state):

        self.wing = static.wing.flight_model(state)
        self.htail = static.empennage.horizontaltail.flight_model(state)
        self.vtail = static.empennage.verticaltail.flight_model(state)
        self.tailboom = static.empennage.tailboom.flight_model(state)

        self.flight_models = [self.wing, self.htail, self.vtail,
                              self.tailboom]
        areadragmodel = [self.htail, self.vtail, self.tailboom]
        areadragcomps = [static.empennage.horizontaltail,
                         static.empennage.verticaltail,
                         static.empennage.tailboom]

        CD = Variable("C_D", "-", "aircraft drag coefficient")
        cda = Variable("CDA", "-", "non-wing drag coefficient")
        Pshaft = Variable("P_{shaft}", "hp", "shaft power")
        Pacc = Variable("P_{acc}", 0.0, "W", "Accessory power draw")
        Poper = Variable("P_{oper}", "W", "operating power")

        dvars = []
        for dc, dm in zip(areadragcomps, areadragmodel):
            if "C_f" in dm.varkeys:
                dvars.append(dm["C_f"]*dc["S"]/static.wing["S"])
            if "C_d" in dm.varkeys:
                dvars.append(dm["C_d"]*dc["S"]/static.wing["S"])

        constraints = [
            state["(E/S)_{irr}"] >= (
                state["(E/S)_{day}"] + static.battery["E"]
                / static.battery["\\eta_{charge}"]
                / static.solarcells["\\eta"]/static.solarcells["S"]),
            static.battery["E"]*static.battery["\\eta_{discharge}"] >= (
                Poper*state["t_{night}"]
                + state["(E/S)_C"]*static.solarcells["\\eta"]
                * static.solarcells["S"]),
            Poper >= Pacc + Pshaft/static.motor["\\eta"],
            Poper == (state["(P/S)_{min}"]*static.solarcells["S"]
                      * static.solarcells["\\eta"]),
            cda >= sum(dvars),
            CD >= cda + self.wing["C_d"],
            Poper <= static.motor["P_{max}"]
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
    def setup(self, latitude=45, day=355, month="dec"):

        df = pd.read_csv(path + "windfits" + month +
                         "/windaltfit_lat%d.csv" % latitude)
        # df = DF[DF["latitude"] == latitude]
        # dft = DFt[DFt["latitude"] == latitude]
        # dfd = DFd[DFd["latitude"] == latitude]
        with StdoutCaptured(None):
            dft, dfd = twi_fits(latitude, day, gen=True)
        esirr, td, tn, _ = get_Eirr(latitude, day)

        Vwind = Variable("V_{wind}", "m/s", "wind velocity")
        V = Variable("V", "m/s", "true airspeed")
        rho = Variable("\\rho", "kg/m**3", "air density")
        mu = Variable("\\mu", 1.42e-5, "N*s/m**2", "viscosity")
        ESirr = Variable("(E/S)_{irr}", esirr, "W*hr/m^2",
                         "solar energy")
        PSmin = Variable("(P/S)_{min}", "W/m^2",
                         "minimum necessary solar power")
        ESday = Variable("(E/S)_{day}", "W*hr/m^2",
                         "solar cells energy during daytime")
        ESc = Variable("(E/S)_C", "W*hr/m^2",
                       "energy for batteries during sunrise/set")
        ESvar = Variable("(E/S)_{ref}", 1, "W*hr/m^2", "energy units variable")
        PSvar = Variable("(P/S)_{ref}", 1, "W/m^2", "power units variable")
        tday = Variable("t_{day}", td, "hr", "Daylight span")
        tnight = Variable("t_{night}", tn, "hr", "night duration")
        pct = Variable("p_{wind}", 0.9, "-", "percentile wind speeds")
        Vwindref = Variable("V_{wind-ref}", 100.0, "m/s",
                            "reference wind speed")
        rhoref = Variable("\\rho_{ref}", 1.0, "kg/m**3",
                          "reference air density")
        mfac = Variable("m_{fac}", 1.0, "-", "wind speed margin factor")

        constraints = [
            V/mfac >= Vwind,
            FitCS(df, Vwind/Vwindref, [rho/rhoref, pct]),
            FitCS(dfd, ESday/ESvar, [PSmin/PSvar]),
            FitCS(dft, ESc/ESvar, [PSmin/PSvar]),
            ]

        return constraints

def altitude(density):
    " find air density "
    g = 9.80665 # m/s^2
    R = 287.04 # m^2/K/s^2
    T11 = 216.65 # K
    p11 = 22532 # Pa
    p = density*R*T11
    h = (11000 - R*T11/g*np.log(p/p11))/0.3048
    return h

class FlightSegment(Model):
    "flight segment"
    def setup(self, aircraft, etap=0.8, latitude=35, day=355, month="dec"):

        self.aircraft = aircraft
        self.fs = FlightState(latitude=latitude, day=day, month=month)
        self.aircraftPerf = self.aircraft.flight_model(self.fs)
        self.slf = SteadyLevelFlight(self.fs, self.aircraft,
                                     self.aircraftPerf, etap)

        self.submodels = [self.fs, self.aircraftPerf, self.slf]

        return self.submodels

class SteadyLevelFlight(Model):
    "steady level flight model"
    def setup(self, state, aircraft, perf, etap):

        T = Variable("T", "N", "thrust")
        etaprop = Variable("\\eta_{prop}", etap, "-", "propeller efficiency")

        constraints = [
            aircraft["W_{total}"] <= (
                0.5*state["\\rho"]*state["V"]**2*perf["C_L"]
                * aircraft.wing["S"]),
            T >= (0.5*state["\\rho"]*state["V"]**2*perf["C_D"]
                  *aircraft.wing["S"]),
            perf["P_{shaft}"] >= T*state["V"]/etaprop]

        return constraints

class Flight(Model):
    "define mission for aircraft"
    def setup(self, aircraft, latitude, day, month):

        flight = FlightSegment(aircraft, latitude=latitude, day=day,
                               month=month)
        loading = aircraft.loading(aircraft["W_{cent}"], aircraft["W_{wing}"],
                                   flight["V"], flight["C_L"])
        for vk in loading.varkeys["N_{max}"]:
            if "ChordSparL" in vk.descr["models"]:
                loading.substitutions.update({vk: 5})
            if "GustL" in vk.descr["models"]:
                loading.substitutions.update({vk: 2})

        return flight, loading


class Mission(Model):
    "define mission for aircraft"
    def setup(self, latitude=35, day=355, month="dec", sp=False):

        mos = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep",
               "oct", "nov", "dec"]

        self.solar = Aircraft(sp=sp)
        mission = []
        if day == 355:
            for l in range(20, latitude+1, 1):
                mission.append(Flight(self.solar, l, day, month))
        else:
            for l in range(20, latitude+1, 1):
                mission.append(Flight(self.solar, l, day, month))
                mission.append(Flight(self.solar, l, day,
                                      mos[-mos.index(month)-2]))

        return self.solar, mission

def test():
    " test model for continuous integration "
    m = Mission(latitude=25)
    m.cost = m["W_{total}"]
    m.solve()

if __name__ == "__main__":
    M = Mission(latitude=25)
    M.cost = M["W_{total}"]
    sol = M.solve("mosek")
    mn = [max(M[sv].descr["modelnums"]) for sv in sol("(E/S)_{irr}") if
          abs(sol["sensitivities"]["constants"][sv]) > 0.01][0]
    # sol = M.localsolve("mosek")
    H = altitude(np.hstack([sol(sv).magnitude for sv in sol("\\rho")]))
