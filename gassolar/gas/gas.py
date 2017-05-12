"""Jungle Hawk Owl"""
import numpy as np
from gpkitmodels.GP.aircraft.engine.gas_engine import Engine
from gpkitmodels.GP.aircraft.wing.wing import Wing
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
    def setup(self, Wfueltot, DF70=False):

        self.fuselage = Fuselage(Wfueltot)
        self.wing = Wing()
        self.engine = Engine(DF70)
        self.empennage = Empennage()

        components = [self.fuselage, self.wing, self.engine, self.empennage]
        self.smeared_loads = [self.fuselage, self.engine]

        Wzfw = Variable("W_{zfw}", "lbf", "zero fuel weight")
        Wpay = Variable("W_{pay}", 10, "lbf", "payload weight")
        Wavn = Variable("W_{avn}", 8, "lbf", "avionics weight")
        Wwing = Variable("W_{wing}", "lbf", "wing weight for loading")
        etaprop = Variable("\\eta_{prop}", 0.75, "-", "propulsive efficiency")

        self.empennage.substitutions["V_h"] = 0.55
        self.empennage.substitutions["V_v"] = 0.04
        self.empennage.substitutions["m_h"] = 0.4
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
            # self.wing["C_{L_{max}}"]/self.wing["m_w"] <= (
            #     self.empennage.horizontaltail["C_{L_{max}}"]
            #     / self.empennage.horizontaltail["m_h"])
            self.empennage.horizontaltail["C_{L_{max}}"] == 1.5,
            self.wing["\\tau"]*self.wing["c_{root}"] >= self.empennage.tailboom["d_0"]
            ]

        return components, constraints

    def flight_model(self, state):
        return AircraftPerf(self, state)

    def loading(self, Wcent, Wwing, V, CL):
        return AircraftLoading(self, Wcent, Wwing, V, CL)

class AircraftLoading(Model):
    "aircraft loading model"
    def setup(self, aircraft, Wcent, Wwing, V, CL):

        loading = [aircraft.wing.loading(Wcent, Wwing, V, CL)]
        loading.append(aircraft.empennage.loading())

        # tbstate = TailBoomState()
        # loading.append(TailBoomFlexibility(aircraft.empennage.horizontaltail,
        #                                    aircraft.empennage.tailboom,
        #                                    aircraft.wing, tbstate))

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
    def setup(self, DF70=False):

        mtow = Variable("MTOW", "lbf", "max-take off weight")
        Wcent = Variable("W_{cent}", "lbf", "center aircraft weight")
        Wfueltot = Variable("W_{fuel-tot}", "lbf", "total aircraft fuel weight")
        LS = Variable("(W/S)", "lbf/ft**2", "wing loading")

        JHO = Aircraft(Wfueltot, DF70)

        climb1 = Climb(JHO, 10, altitude=np.linspace(0, 15000, 11)[1:])
        cruise1 = Cruise(JHO, 1, R=200)
        loiter1 = Loiter(JHO, 5)
        cruise2 = Cruise(JHO, 1)
        mission = [climb1, cruise1, loiter1, cruise2]

        loading = JHO.loading(Wcent, JHO["W_{wing}"], loiter1["V"][0], loiter1["C_L"][0])

        constraints = [
            mtow >= climb1["W_{start}"][0],
            Wfueltot >= sum(fs["W_{fuel-fs}"] for fs in mission),
            mission[-1]["W_{end}"][-1] >= JHO["W_{zfw}"],
            Wcent >= Wfueltot + sum(summing_vars(JHO.smeared_loads, "W")),
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
    M.cost = 1/M["t_Mission/Loiter"]
    M.solve()

if __name__ == "__main__":
    M = Mission()
    M.cost = 1/M["t_Mission/Loiter"]
    sol = M.solve("mosek")
    print sol.table()
