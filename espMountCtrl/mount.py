from dataclasses import dataclass
from .mountConnection import MountConnection, MountStatus
from astropy.coordinates import SkyCoord, EarthLocation, AltAz, Angle, BaseRADecFrame
import astropy.units as u
from astropy.units import Quantity
from astropy.time import Time
from typing import Iterable, Tuple, Callable, Union
from time import sleep
import math
import alive_progress

_MOUNT_REFRESH_INTERVAL = 0.5
@dataclass
class TrackPoint:
    coord: SkyCoord
    t: Time

class Mount:
    def __init__(self, axCoord: SkyCoord):
        self.axCoord = axCoord
        self.mountConnection = MountConnection()
        self._time_offset = 0

    @classmethod
    def from_ax_altaz(cls, alt: u.Quantity, az: u.Quantity, lon: u.Quantity, lat: u.Quantity, elevation: u.Quantity = "0m", obstime=Time.now()):
        location = EarthLocation.from_geodetic(lon=lon, lat=lat)
        coord = SkyCoord(alt=alt, az=az, frame="altaz", location=location, obstime=obstime)
        return cls(coord)

    def _recalculate_fake_location(self):
        axAltAz = self.axCoord.transform_to('altaz')
        self._fakeLocation = EarthLocation.from_geodetic(lon= 0 * u.degree, lat=axAltAz.alt)

    def _coord_to_mount_pos(self, coord: SkyCoord) -> Tuple[int, int]:
        true_altaz: AltAz = coord.transform_to('altaz')
        fake_altaz = SkyCoord(alt=true_altaz.alt, az= true_altaz.az - self._axCoord.az, frame="altaz", obstime=self.time, location=self._fakeLocation)
        fake_hadec = fake_altaz.transform_to('hadec')
        ax1 = round((fake_hadec.ha + 180 * u.deg).wrap_at('360deg').deg / 360 * self.cprRa)
        ax2 = round(fake_hadec.dec.wrap_at('180deg').deg / 360 * self.cprDec)
        return ax1, ax2

    def _mount_pos_to_coord(self, ax1: int, ax2: int) -> SkyCoord:
        ax1_angle = Angle(ax1 * 360.0 / self.cprRa - 180, u.degree)
        ax2_angle = Angle(ax2 * 360.0 / self.cprDec, u.deg)
        
        if ax2_angle > 90 * u.deg:
            ax1_angle += 180 * u.deg
            ax2_angle = 90 * u.deg - ax2_angle
        if ax2_angle < -90 * u.deg:
            ax1_angle += 180 * u.deg
            ax2_angle = -90 * u.deg - ax2_angle

        ax1_angle = ax1_angle.wrap_at('360d')
        fake_hadec = SkyCoord(frame="hadec", ha=ax1_angle, dec=ax2_angle, obstime=self.time, location=self._fakeLocation)
        fake_altaz = fake_hadec.transform_to('altaz')
        coord = SkyCoord(frame="altaz", alt=fake_altaz.alt, az=fake_altaz.az + self._axCoord.az, obstime=fake_hadec.obstime, location=fake_hadec.location)
        return coord

    def _time_to_mount_time(self, t: Time):
        return t.unix * 1000

    @property
    def time(self) -> Time:
        return Time.now() + self._time_offset

    @time.setter
    def time(self, t: Time):
        self._time_offset = t - Time.now()

    @property
    def axCoord(self) -> SkyCoord:
        return self._axCoord

    @axCoord.setter
    def axCoord(self, val: SkyCoord):
        self._axCoord = val.transform_to("altaz")
        self.location: EarthLocation = val.location
        self._recalculate_fake_location()
    
    def calibrate_ant_coord(self, antCoord: SkyCoord):
        ax1, ax2 = self._coord_to_mount_pos(antCoord)
        self.mountConnection.set_position(ax1, ax2)

    def goto(self, coord: SkyCoord, block: bool = False) -> None:
        ax1, ax2 = self._coord_to_mount_pos(coord)
        self.mountConnection.goto(ax1, ax2)
        if block:
            self.wait_for_stop()
    
    def stop(self, block: bool = False) -> None:
        self.mountConnection.stop(False)
        if block:
            self.wait_for_stop()

    def wait_for_stop(self):
        while(self.mountConnection.get_mount_status() != MountStatus.STOPPED):
            sleep(_MOUNT_REFRESH_INTERVAL)

    def sync_time(self) -> None:
        current_mount_time = self._time_to_mount_time(self.time)
        self.mountConnection.set_time(current_mount_time)
    
    def get_position(self) -> SkyCoord:
        ax1, ax2 = self.mountConnection.get_position()
        return self._mount_pos_to_coord(ax1, ax2)

    def track(self, trackPoints: Iterable[TrackPoint], update_callback: Callable[[int, int], None] = None, print_upload_progres=False) -> None:
        self.mountConnection.stop()
        self.mountConnection.clear_track_buffer()
        
        track_buffer_space = self.mountConnection.get_track_buffer_free_space()
        if track_buffer_space < len(trackPoints):
            raise Exception("Track point count exceeds maximum mount's buffer. It is possible to overcome this, but it is not implemented yet")
        point_count = len(trackPoints)
        if print_upload_progres:
            trackPoints = alive_progress.alive_it(trackPoints)
        for idx, point in enumerate(trackPoints):
            if update_callback != None:
                update_callback(idx, point_count)
            
            ax1, ax2 = self._coord_to_mount_pos(point.coord)
            mount_time = self._time_to_mount_time(point.t)
            self.mountConnection.add_track_point(ax1, ax2, mount_time)
        
        if update_callback != None:
            update_callback(point_count, point_count)
        self.sync_time()
        self.mountConnection.tracking_start()

    def get_status(self) -> MountStatus:
        return self.mountConnection.get_mount_status()

    def get_time(self) -> Time:
        time_raw = self.mountConnection.get_time()
        return Time(time_raw/1000.0, format="unix")

    def connect(self, device: str = None):
        self.mountConnection.open(device)
        self.cprRa, self.cprDec = self.mountConnection.get_cpr()
    
    def is_connected(self):
        return self.mountConnection.is_connected()

    def disconnect(self):
        self.mountConnection.close()

    def local_altaz(self, alt: Union[Quantity, str], az: Union[Quantity, str], t: Time=None) -> SkyCoord:
        if t == None:
            t = self.time
        return SkyCoord(frame="altaz", alt=alt, az=az, obstime=t, location=self.location)
    
    def local_radec(self, ra: Union[Quantity, str], dec: Union[Quantity, str], t: Time=None) -> SkyCoord:
        if t == None:
            t = self.time
        return SkyCoord(frame="radec", ra=ra, dec=dec, obstime=t, location=self.location)

    def __del__(self):
        self.disconnect()
    
