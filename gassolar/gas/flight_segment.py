" flight segment model "
from gpkit import Model, Variable, Vectorize
from gpkitmodels.aircraft.GP_submodels.breguet_endurance import BreguetEndurance
from steady_level_flight import SteadyLevelFlight
from flight_state import FlightState

class FlightSegment(Model):
    "flight segment"
    def setup(self, aircraft, N=5, altitude=15000, latitude=45, percent=90,
                 day=355):

        self.aircraft = aircraft
        with Vectorize(N):
            self.fs = FlightState(latitude, percent, altitude, day)
            self.aircraftPerf = self.aircraft.flight_model(self.fs)
            self.slf = SteadyLevelFlight(self.fs, self.aircraft,
                                         self.aircraftPerf)
            self.be = BreguetEndurance(self.aircraftPerf)

        self.submodels = [self.fs, self.aircraftPerf, self.slf, self.be]
        Wfuelfs = Variable("W_{fuel-fs}", "lbf", "flight segment fuel weight")

        self.constraints = [Wfuelfs >= self.be["W_{fuel}"].sum()]

        if N > 1:
            self.constraints.extend([self.aircraftPerf["W_{end}"][:-1] >=
                                     self.aircraftPerf["W_{start}"][1:]])

        return self.aircraft, self.submodels, self.constraints
