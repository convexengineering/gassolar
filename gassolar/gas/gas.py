"""Jungle Hawk Owl"""
import numpy as np
from gpkitmodels.GP.aircraft.engine.gas_engine import Engine
from gpkitmodels.GP.aircraft.wing.wing import Wing as WingGP
from gpkitmodels.SP.aircraft.wing.wing import Wing as WingSP
from gpkitmodels.GP.aircraft.fuselage.elliptical_fuselage import Fuselage
from gpkitmodels.GP.aircraft.tail.empennage import Empennage
from gpkitmodels.GP.aircraft.tail.tail_boom import TailBoomState
from gpkitmodels.SP.aircraft.tail.tail_boom_flex import TailBoomFlexibility
from gpkitmodels.tools.summing_constraintset import summing_vars
from gpkit import Model, Variable, Vectorize, units
from flight_segment import FlightSegment
from loiter import Loiter

# pylint: disable=invalid-name

class Aircraft(Model):
    "the JHO vehicle"
    def setup(self, Wfueltot, sp=False):

        self.sp = sp

        self.fuselage = Fuselage(Wfueltot)
        if sp:
            self.wing = WingSP()
        else:
            self.wing = WingGP()
        self.engine = Engine()
        self.empennage = Empennage()

        components = [self.fuselage, self.wing, self.engine, self.empennage]
        self.smeared_loads = [self.fuselage, self.engine]

        Wzfw = Variable("W_{zfw}", "lbf", "zero fuel weight")
        Wpay = Variable("W_{pay}", 10, "lbf", "payload weight")
        Wavn = Variable("W_{avn}", 8, "lbf", "avionics weight")
        Wwing = Variable("W_{wing}", "lbf", "wing weight for loading")
        etaprop = Variable("\\eta_{prop}", 0.8, "-", "propulsive efficiency")

        self.empennage.substitutions["V_v"] = 0.04

        if not sp:
            self.empennage.substitutions["V_h"] = 0.45
            self.empennage.substitutions["AR_h"] = 5.0
            self.empennage.substitutions["m_h"] = 0.1

        constraints = [
            Wzfw >= sum(summing_vars(components, "W")) + Wpay + Wavn,
            Wwing >= sum(summing_vars([self.wing], "W")),
            self.empennage.horizontaltail["V_h"] <= (
                self.empennage.horizontaltail["S"]
                * self.empennage.horizontaltail["l_h"]/self.wing["S"]**2
                * self.wing["b"]),
            self.empennage.verticaltail["V_v"] <= (
                self.empennage.verticaltail["S"]
                * self.empennage.verticaltail["l_v"]/self.wing["S"]
                / self.wing["b"]),
            self.wing["\\tau"]*self.wing["c_{root}"] >= self.empennage.tailboom["d_0"]
            ]

        return components, constraints

    def flight_model(self, state):
        return AircraftPerf(self, state)

    def loading(self, Wcent, Wwing, V, CL):
        if self.sp:
            return AircraftLoadingSP(self, Wcent, Wwing, V, CL)
        else:
            return AircraftLoading(self, Wcent, Wwing, V, CL)

class AircraftLoading(Model):
    "aircraft loading model"
    def setup(self, aircraft, Wcent, Wwing, V, CL):

        loading = [aircraft.wing.loading(Wcent, Wwing, V, CL)]
        loading.append(aircraft.empennage.loading())

        return loading

class AircraftLoadingSP(Model):
    "aircraft loading model"
    def setup(self, aircraft, Wcent, Wwing, V, CL):

        loading = [aircraft.wing.loading(Wcent, Wwing, V, CL)]
        loading.append(aircraft.empennage.loading())

        tbstate = TailBoomState()
        loading.append(TailBoomFlexibility(aircraft.empennage.horizontaltail,
                                           aircraft.empennage.tailboom,
                                           aircraft.wing, tbstate))

        return loading

class AircraftPerf(Model):
    "performance model for aircraft"
    def setup(self, static, state):

        self.wing = static.wing.flight_model(state)
        self.fuselage = static.fuselage.flight_model(state)
        self.engine = static.engine.flight_model(state)
        self.htail = static.empennage.horizontaltail.flight_model(state)
        self.vtail = static.empennage.verticaltail.flight_model(state)
        self.tailboom = static.empennage.tailboom.flight_model(state)

        self.dynamicmodels = [self.wing, self.fuselage, self.engine,
                              self.htail, self.vtail, self.tailboom]
        areadragmodel = [self.fuselage, self.htail, self.vtail, self.tailboom]
        areadragcomps = [static.fuselage, static.empennage.horizontaltail,
                         static.empennage.verticaltail,
                         static.empennage.tailboom]

        Wend = Variable("W_{end}", "lbf", "vector-end weight")
        Wstart = Variable("W_{start}", "lbf", "vector-begin weight")
        CD = Variable("C_D", "-", "drag coefficient")
        CDA = Variable("CDA", "-", "area drag coefficient")
        mfac = Variable("m_{fac}", 1.0, "-", "drag margin factor")

        dvars = []
        for dc, dm in zip(areadragcomps, areadragmodel):
            if "C_f" in dm.varkeys:
                dvars.append(dm["C_f"]*dc["S"]/static.wing["S"])
            if "C_d" in dm.varkeys:
                dvars.append(dm["C_d"]*dc["S"]/static.wing["S"])

        constraints = [Wend == Wend,
                       Wstart == Wstart,
                       CDA/mfac >= sum(dvars),
                       CD >= CDA + self.wing["C_d"]]

        return self.dynamicmodels, constraints

class Cruise(Model):
    "make a cruise flight segment"
    def setup(self, aircraft, N, altitude=15000, latitude=45, percent=90,
              day=355, R=200):
        fs = FlightSegment(aircraft, N, altitude, latitude, percent, day)

        R = Variable("R", R, "nautical_miles", "Range to station")
        constraints = [R/N <= fs["V"]*fs.be["t"]]

        return fs, constraints

class Climb(Model):
    "make a climb flight segment"
    def setup(self, aircraft, N, altitude=15000, latitude=45, percent=90,
              day=355, dh=15000):
        fs = FlightSegment(aircraft, N, altitude, latitude, percent, day)

        with Vectorize(N):
            hdot = Variable("\\dot{h}", "ft/min", "Climb rate")

        deltah = Variable("\\Delta_h", dh, "ft", "altitude difference")
        hdotmin = Variable("\\dot{h}_{min}", 100, "ft/min",
                           "minimum climb rate")

        constraints = [
            hdot*fs.be["t"] >= deltah/N,
            hdot >= hdotmin,
            fs.slf["T"] >= (0.5*fs["\\rho"]*fs["V"]**2*fs["C_D"]
                            * fs.aircraft.wing["S"] + fs["W_{start}"]*hdot
                            / fs["V"]),
            ]

        return fs, constraints

class Mission(Model):
    "creates flight profile"
    def setup(self, latitude=38, percent=90, sp=False):

        mtow = Variable("MTOW", "lbf", "max-take off weight")
        Wcent = Variable("W_{cent}", "lbf", "center aircraft weight")
        Wfueltot = Variable("W_{fuel-tot}", "lbf", "total aircraft fuel weight")
        LS = Variable("(W/S)", "lbf/ft**2", "wing loading")

        JHO = Aircraft(Wfueltot, sp=sp)

        climb1 = Climb(JHO, 10, latitude=latitude, percent=percent,
                       altitude=np.linspace(0, 15000, 11)[1:])
        # cruise1 = Cruise(JHO, 1, R=200, latitude=latitude, percent=percent)
        loiter1 = Loiter(JHO, 5, latitude=latitude, percent=percent)
        # cruise2 = Cruise(JHO, 1, latitude=latitude, percent=percent)
        # mission = [climb1, cruise1, loiter1, cruise2]
        mission = [climb1, loiter1]

        loading = JHO.loading(Wcent, JHO["W_{wing}"], loiter1["V"][0], loiter1["C_L"][0])

        constraints = [
            mtow >= climb1["W_{start}"][0],
            Wfueltot >= sum(fs["W_{fuel-fs}"] for fs in mission),
            mission[-1]["W_{end}"][-1] >= JHO["W_{zfw}"],
            Wcent >= Wfueltot + JHO["W_{pay}"] + JHO["W_{avn}"] + sum(summing_vars(JHO.smeared_loads, "W")),
            LS == mtow/JHO.wing["S"]
            ]

        for i, fs in enumerate(mission[1:]):
            constraints.extend([
                mission[i]["W_{end}"][-1] == fs["W_{start}"][0]
                ])

        for vk in loading.varkeys["N_{max}"]:
            if "ChordSparL" in vk.descr["models"]:
                loading.substitutions.update({vk: 5})
            if "GustL" in vk.descr["models"]:
                loading.substitutions.update({vk: 2})

        return JHO, mission, loading, constraints

def test():
    M = Mission()
    M.substitutions.update({"t_Mission/Loiter": 6})
    M.cost = M["MTOW"]
    sol = M.solve("mosek")
    M.solve()

if __name__ == "__main__":
    M = Mission()
    M.substitutions.update({"t_Mission/Loiter": 6})
    M.cost = M["MTOW"]
    sol = M.solve("mosek")
