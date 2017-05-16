" flight segment model "
from gpkit import Model, Variable, Vectorize
from gpkitmodels.GP.aircraft.mission.breguet_endurance import BreguetEndurance
from steady_level_flight import SteadyLevelFlight
from flight_state import FlightState
from gassolar.environment.wind_speeds import get_windspeed
from gpkit.constraints.tight import Tight as TCS

class FlightSegment(Model):
    "flight segment"
    def setup(self, aircraft, N=5, altitude=15000, latitude=45, percent=90,
                 day=355):

        if not hasattr(altitude, "__len__"):
            altitude = [altitude]
        if all(x == altitude[0] for x in altitude):
            wind = get_windspeed(latitude, percent, altitude[0], day)
            Vwind = Variable("V_{wind}", wind, "m/s",
                             "wind velocity at $h_{\\mathrm{min}}$")

        self.aircraft = aircraft
        with Vectorize(N):
            if not all(x == altitude[0] for x in altitude):
                wind = get_windspeed(latitude, percent, altitude, day)
                Vwind = Variable("V_{wind}", wind, "m/s",
                                 "wind velocity at $h_{\\mathrm{min}}$")
            self.fs = FlightState(Vwind, latitude, percent, altitude, day)
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

        return self.submodels, self.constraints
