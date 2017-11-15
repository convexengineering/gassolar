" loiter segment "
from gpkit import Model, Variable
from flight_segment import FlightSegment

class Loiter(Model):
    "loiter segment"
    def setup(self, aircraft, N=5, altitude=15000, latitude=45, percent=90,
                 day=355):
        self.fs = FlightSegment(aircraft, N, altitude, latitude, percent, day)

        t = Variable("t", "days", "endurance requirement")
        constraints = [self.fs.be["t"] >= t/N]

        return self.fs, constraints
