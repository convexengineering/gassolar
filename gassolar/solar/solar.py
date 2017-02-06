" Simple Solar-Electric Powered Aircraft Model "
import pandas as pd
import numpy as np
import os
from gassolar.environment.solar_irradiance import get_Eirr
from gpkit import Model, Variable, SignomialsEnabled
from gpkitmodels.aircraft.GP_submodels.wing import WingAero, Wing
from gpkitmodels.aircraft.GP_submodels.empennage import Empennage
from gpkitmodels.aircraft.GP_submodels.tail_boom import TailBoomState
from gpkitmodels.aircraft.GP_submodels.tail_boom_flex import TailBoomFlexibility
from gpkitmodels.helpers import summing_vars

basepath = os.path.abspath(__file__).replace(os.path.basename(__file__), "")
path = basepath.replace(os.sep+"solar"+os.sep, os.sep+"environment"+os.sep)
DF = pd.read_csv(path + "windaltfitdata.csv")
DF2 = pd.read_csv(path + "solarirrdata.csv")

class Aircraft(Model):
    "vehicle"
    def setup(self):

        self.solarcells = SolarCells()
        self.wing = Wing(hollow=True)
        self.battery = Battery()
        self.empennage = Empennage()
        self.engine = Engine()

        self.components = [self.solarcells, self.wing, self.battery,
                           self.empennage, self.engine]

        Wpay = Variable("W_{pay}", 10, "lbf", "payload")
        Wtotal = Variable("W_{total}", "lbf", "aircraft weight")
        Wwing = Variable("W_{wing}", "lbf", "wing weight")
        Wcent = Variable("W_{cent}", "lbf", "center weight")

        self.empennage.substitutions["V_h"] = 0.45
        self.empennage.substitutions["V_v"] = 0.04
        self.empennage.substitutions["m_h"] = 5.514

        constraints = [
            Wtotal >= (Wpay + sum(summing_vars(self.components, "W"))),
            Wwing >= (sum(summing_vars([self.wing, self.battery,
                                        self.solarcells], "W"))),
            Wcent >= Wpay + sum(summing_vars([self.empennage, self.engine],
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
            # self.wing["C_{L_{max}}"]/self.wing["m_w"] <= (
            #     self.empennage.horizontaltail["C_{L_{max}}"]
            #     / self.empennage.horizontaltail["m_h"]),
            self.empennage.horizontaltail["C_{L_{max}}"] == 1.5,
            self.wing["\\tau"]*self.wing["c_{root}"] >= self.empennage.tailboom["d_0"]
            ]

        return constraints, self.components

    def flight_model(self, state):
        return AircraftPerf(self, state)

    def loading(self, Wcent, Wwing, V, CL):
        return AircraftLoading(self, Wcent, Wwing, V, CL)

class Engine(Model):
    "the thing that provides power"
    def setup(self):

        W = Variable("W", "lbf", "engine weight")
        Pmax = Variable("P_{max}", "W", "max power")
        Bpm = Variable("B_{PM}", 4140.8, "W/kg", "power mass ratio")
        m = Variable("m", "kg", "engine mass")
        g = Variable("g", 9.81, "m/s**2", "gravitational constant")

        constraints = [Pmax == Bpm*m,
                       W >= m*g]

        return constraints

class AircraftLoading(Model):
    "aircraft loading cases"
    def setup(self, aircraft, Wcent, Wwing, V, CL):

        loading = [aircraft.wing.loading(Wcent, Wwing, V, CL)]
        loading.append(aircraft.empennage.loading())

        # tbstate = TailBoomState()
        # loading.append(TailBoomFlexibility(aircraft.empennage.horizontaltail,
        #                                    aircraft.empennage.tailboom,
        #                                    aircraft.wing, tbstate))

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

class SolarCells(Model):
    "solar cell model"
    def setup(self):

        rhosolar = Variable("\\rho_{solar}", 0.27, "kg/m^2",
                            "solar cell area density")
        g = Variable("g", 9.81, "m/s**2", "gravitational constant")
        S = Variable("S", "ft**2", "solar cell area")
        W = Variable("W", "lbf", "solar cell weight")
        etasolar = Variable("\\eta", 0.22, "-", "Solar cell efficiency")

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
            static.battery["E"] >= (
                Poper*state["t_{night}"]/static.battery["\\eta_{discharge}"]
                + state["(E/S)_C"]*static.solarcells["\\eta"]
                * static.solarcells["S"]),
            Poper >= Pacc + Pshaft,
            Poper == (state["(P/S)_{min}"]*static.solarcells["S"]
                      * static.solarcells["\\eta"]),
            cda >= sum(dvars),
            CD >= cda + self.wing["C_d"],
            Poper <= static.engine["P_{max}"]
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
        df2 = DF2[DF2["latitude"] == latitude]
        esirr, td, tn, _ = get_Eirr(latitude, day)

        Vwind = Variable("V_{wind}", "m/s", "wind velocity")
        V = Variable("V", "m/s", "true airspeed")
        rho = Variable("\\rho", "kg/m**3", "air density")
        mu = Variable("\\mu", 1.42e-5, "N*s/m**2", "viscosity")
        ESirr = Variable("(E/S)_{irr}", esirr, "W*hr/m^2",
                         "total daytime solar energy")
        PSmin = Variable("(P/S)_{min}", "W/m^2",
                         "minimum necessary solar power")
        ESday = Variable("(E/S)_{day}", "W*hr/m^2",
                         "solar cells energy during daytime")
        ESc = Variable("(E/S)_C", "W*hr/m^2",
                       "energy for batteries during sunrise/set")
        ESvar = Variable("(E/S)_{var}", 1, "W*hr/m^2", "energy units variable")
        PSvar = Variable("(P/S)_{var}", 1, "W/m^2", "power units variable")
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
            (Vwind/Vwindref)**df["alpha"].iloc[0] >= (
                sum([df["c%d" % i]*(rho/rhoref)**df["e%d1" % i]
                     * pct**df["e%d2" % i] for i in range(1, 5)]).iloc[0]),
            ESday/ESvar == df2["Bc"].iloc[0]*(PSmin/PSvar)**df2["Be"].iloc[0],
            ESc/ESvar == df2["Cc"].iloc[0]*(PSmin/PSvar)**df2["Ce"].iloc[0]
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

class FlightSegment(Model):
    "flight segment"
    def setup(self, aircraft, etap=0.8, latitude=35, day=355):

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

        self.solar = Aircraft()
        mission = []
        for l in range(20, latitude+1, 1):
            mission.append(FlightSegment(self.solar, latitude=l, day=day))
        loading = self.solar.loading(self.solar["W_{cent}"], self.solar["W_{wing}"], mission[-1]["V"], mission[-1]["C_L"])
        for vk in loading.varkeys["N_{max}"]:
            if "ChordSparL" in vk.descr["models"]:
                loading.substitutions.update({vk: 5})
            if "GustL" in vk.descr["models"]:
                loading.substitutions.update({vk: 2})

        return self.solar, mission, loading

def test():
    M = Mission(latitude=31)
    M.cost = M["W_{total}"]
    M.solve()

if __name__ == "__main__":
    M = Mission(latitude=25)
    M.cost = M["W_{total}"]
    sol = M.solve("mosek")
    mn = [max(M[sv].descr["modelnums"]) for sv in sol("(E/S)_{irr}") if
          abs(sol["sensitivities"]["constants"][sv]) > 0.01][0]
    # sol = M.localsolve("mosek")
    h = altitude(np.hstack([sol(sv).magnitude for sv in sol("\\rho")]))
