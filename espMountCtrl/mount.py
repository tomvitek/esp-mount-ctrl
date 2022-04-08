from dataclasses import dataclass
from .mountConnection import MountConnection, MountStatus
from astropy.coordinates import SkyCoord, EarthLocation, AltAz
import astropy.units as u
from astropy.time import Time
from typing import Iterable, Tuple, Callable
from time import sleep

@dataclass
class TrackPoint:
    coord: SkyCoord
    t: Time

class Mount:
    def __init__(self, axCoord: SkyCoord):
        self.axCoord = axCoord
        self.mountConnection = MountConnection()

    @classmethod
    def from_ax_altaz(cls, alt, az, lon, lat, obstime=Time.now()):
        location = EarthLocation.from_geodetic(lon=lon, lat=lat)
        coord = SkyCoord(alt=alt, az=az, frame="altaz", location=location, obstime=obstime)
        return cls(coord)

    def _recalculate_fake_location(self):
        axAltAz = self.axCoord.transform_to('altaz')
        self._fakeLocation = EarthLocation.from_geodetic(lon= 0 * u.degree, lat=axAltAz.alt)

    def _coord_to_mount_pos(self, coord: SkyCoord) -> Tuple[int, int]:
        true_altaz: AltAz = coord.transform_to('altaz')
        fake_altaz = SkyCoord(alt=true_altaz.alt, az= true_altaz.az - self._axCoord.az, frame="altaz", obstime=Time.now(), location=self._fakeLocation)
        fake_hadec = fake_altaz.transform_to('hadec')
        ax1 = int((fake_hadec.ha + 180 * u.deg).wrap_at('360d').deg / 360 * self.cprRa)
        ax2 = int(fake_hadec.dec.wrap_at('360d').deg / 360 * self.cprDec)
        return ax1, ax2

    def _time_to_mount_time(self, t: Time):
        return t.to_value("unix") * 1000

    @property
    def axCoord(self) -> SkyCoord:
        return self._axCoord

    @axCoord.setter
    def axCoord(self, val: SkyCoord):
        self._axCoord = val.transform_to("altaz")
        self._recalculate_fake_location()
    
    def calibrate_ant_coord(self, antCoord: SkyCoord):
        ax1, ax2 = self._coord_to_mount_pos(antCoord)
        self.mountConnection.set_position(ax1, ax2)

    def goto(self, coord: SkyCoord) -> None:
        ax1, ax2 = self._coord_to_mount_pos(coord)
        self.mountConnection.goto(ax1, ax2)
    
    def stop(self, block: bool = False) -> None:
        self.mountConnection.stop(False)
        if block:
            while self.mountConnection.get_mount_status() != MountStatus.STOPPED:
                sleep(0.5)

    def sync_time(self) -> None:
        current_mount_time = self._time_to_mount_time(Time.now())
        self.mountConnection.set_time(current_mount_time)

    def track(self, trackPoints: Iterable[TrackPoint], update_callback: Callable[[int, int], None] = None) -> None:
        self.mountConnection.stop()
        self.mountConnection.clear_track_buffer()
        
        track_buffer_space = self.mountConnection.get_track_buffer_free_space()
        if track_buffer_space < len(trackPoints):
            raise Exception("Track point count exceeds maximum mount's buffer. It is possible to overcome this, but it is not implemented yet")
        
        for idx, point in enumerate(trackPoints):
            if update_callback != None:
                update_callback(idx, len(trackPoints))
            
            ax1, ax2 = self._coord_to_mount_pos(point.coord)
            mount_time = self._time_to_mount_time(point.t)
            self.mountConnection.add_track_point(ax1, ax2, mount_time)
        
        if update_callback != None:
            update_callback(len(trackPoints), len(trackPoints))
        
        self.mountConnection.tracking_start()

    def connect(self, device: str):
        self.mountConnection.open(device)
        self.cprRa, self.cprDec = self.mountConnection.get_cpr()
    
    def is_connected(self):
        return self.mountConnection.is_connected()

    def disconnect(self):
        self.mountConnection.close()

    def __del__(self):
        self.disconnect()
    
    