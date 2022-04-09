from astropy.time import Time
from astropy.coordinates import EarthLocation, AltAz, SkyCoord
from astropy.units import Quantity
import astropy.units as u
from dataclasses import dataclass
from skyfield.api import EarthSatellite, Time as SFTime
from skyfield.positionlib import Geometric
from skyfield.toposlib import GeographicPosition
from typing import List
from espMountCtrl.mount import TrackPoint
from . import skyfield_ts as ts

@dataclass
class Transit:
    sf_rise_t: SFTime
    sf_rise_pos: Geometric
    sf_culm_t: SFTime
    sf_culm_pos: Geometric
    sf_set_t: SFTime
    sf_set_pos: Geometric
    sf_loc: GeographicPosition
    satellite: EarthSatellite

    def _sf_pos_to_altaz(self, pos: Geometric, t: SFTime) -> SkyCoord:
        alt, az, dst = pos.altaz()
        return SkyCoord(frame="altaz", alt=alt.to(u.deg), az=az.to(u.deg), obstime=t.to_astropy(), location=self.location)

    @property
    def time_rise(self) -> Time:
        return self.sf_rise_t.to_astropy()

    @property
    def time_set(self) -> Time:
        return self.sf_set_t.to_astropy()

    @property
    def time_culm(self) -> Time:
        return self.sf_culm_t.to_astropy()
    
    @property
    def location(self) -> EarthLocation:
        return EarthLocation.from_geodetic(self.sf_loc.longitude.degrees, self.sf_loc.latitude.degrees, self.sf_loc.elevation.m)
    
    @property
    def min_dst(self) -> Quantity:
        alt, az, dst = self.sf_culm_pos.altaz()
        return dst.to(u.km)
    
    @property
    def max_elev_altaz(self) -> SkyCoord:
        return self._sf_pos_to_altaz(self.sf_culm_pos, self.sf_culm_t)
    
    @property
    def rise_altaz(self) -> SkyCoord:
        return self._sf_pos_to_altaz(self.sf_rise_pos, self.sf_rise_t)

    @property
    def set_altaz(self) -> SkyCoord:
        return self._sf_pos_to_altaz(self.sf_set_pos, self.sf_set_t)
    
    def _altaz_to_str(self, altaz: AltAz) -> str:
        return f"{(round(altaz.alt.deg, 3), round(altaz.az.deg, 3))}"

    def get_sat_altaz(self, t: Time) -> SkyCoord:
        diff = self.satellite - self.sf_loc
        sf_time = ts.from_astropy(t)
        return self._sf_pos_to_altaz(diff.at(sf_time), sf_time)

    def calculate_track_points(self, track_point_count) -> List[TrackPoint]:
        dt = (self.time_set - self.time_rise) / track_point_count
        track_points: List[TrackPoint] = []
        for i in range(track_point_count):
            t = self.time_rise + i * dt
            pos = self.get_sat_altaz(t)
            point = TrackPoint(pos, t)
            track_points.append(point)
        return track_points

    def __str__(self) -> str:
        s1 = f"{self.satellite.name}:"
        s2 = f"{self.time_rise.fits} {self._altaz_to_str(self.rise_altaz)} -> "
        s3 = f"{self.time_culm.fits} {self._altaz_to_str(self.max_elev_altaz)} -> "
        s4 = f"{self.time_set.fits} {self._altaz_to_str(self.set_altaz)}"
        return f"{s1:<15}{s2:<50}{s3:<50}{s4:<50}"

