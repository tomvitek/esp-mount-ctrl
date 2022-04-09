from skyfield.sgp4lib import EarthSatellite

from espMountCtrl.satellites.transit import Transit
from ..mount import Mount
from astropy.time import Time
from astropy.units import Quantity
import astropy.units as u
from astropy.coordinates import AltAz
from typing import List
from skyfield.api import wgs84, Time as SFTime
from . import skyfield_load, skyfield_ts as ts

_SF_SAT_RISE = 0
_SF_SAT_CULMINATE = 1
_SF_SAT_SET = 2

class SatelliteTracker:
    def __init__(self, mount: Mount):
        self.mount = mount
    
    @property
    def mount(self):
        return self._mount
    
    @mount.setter
    def mount(self, val: Mount):
        self._mount = val
        self._loc = wgs84.latlon(self.mount.location.lat.deg, self.mount.location.lon.deg, self.mount.location.height.to(u.m).value)

    def get_sat_altaz(self, sat: EarthSatellite, t: Time) -> AltAz:
        sat_vector = sat - self._loc
        topocentric = sat_vector.at(ts.from_astropy(t))
        alt, az, dst = topocentric.altaz()
        return AltAz(alt=alt.to(u.deg), az=az.to(u.deg), obstime=t, location=self.mount.location)
    
    def _get_sat_pos(self, sat: EarthSatellite, t: SFTime):
        sat_vector = sat - self._loc
        return sat_vector.at(t)

    def find_transits(self, sat: EarthSatellite, time_to: Time,  min_elev: Quantity = Quantity('0deg'), time_from: Time = Time.now()) -> List[Transit]:
        t0 = ts.from_astropy(time_from)
        t1 = ts.from_astropy(time_to)
        sat_times, sat_events = sat.find_events(self._loc, t0, t1, min_elev.to(u.deg).value)
        
        transits: List[Transit] = []

        transit_t_rise = None
        transit_pos_rise = None
        transit_t_culm = None
        transit_pos_culm = None
        transit_alt_culm = None
        transit_t_set = None
        transit_pos_set = None
        for i in range(len(sat_times)):
            t = sat_times[i]
            event = sat_events[i]
            if event == _SF_SAT_RISE:
                transit_t_rise = t
                transit_pos_rise = self._get_sat_pos(sat, t)
            if event == _SF_SAT_CULMINATE:
                # There can be more culminations for one satellite, we want the one with the highest altitude
                pos = self._get_sat_pos(sat, t)
                alt, az, dst = pos.altaz()
                if transit_alt_culm == None or transit_alt_culm.degrees < alt.degrees:
                    transit_alt_culm = alt
                    transit_pos_culm = pos
                    transit_t_culm = t

            if event == _SF_SAT_SET:
                transit_t_set = t
                transit_pos_set = self._get_sat_pos(sat, t)
            
            if event == _SF_SAT_SET:
                if transit_t_rise != None and transit_t_culm != None and transit_t_set != None:
                    transits.append(Transit(transit_t_rise, transit_pos_rise, transit_t_culm, transit_pos_culm, transit_t_set, transit_pos_set, self._loc, sat))
                    transit_alt_culm = None
                    transit_t_rise = None
                    transit_t_set = None
        
        return transits


