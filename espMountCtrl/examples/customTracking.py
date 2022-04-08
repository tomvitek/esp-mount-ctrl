from ..mount import Mount, TrackPoint, MountStatus
from astropy.coordinates import SkyCoord, EarthLocation
from astropy.time import Time, TimeDelta
import astropy.units as u
from typing import List

location = EarthLocation.from_geodetic(lon=49, lat=16)
axCoord = SkyCoord(frame="altaz", az='270d', alt='45d', obstime=Time.now(), location=location)
antCoord = SkyCoord(frame="altaz", az='90d', alt='0d', obstime=Time.now(), location=location)
mount = Mount(axCoord)
mount.connect("/dev/ttyUSB1")
mount.calibrate_ant_coord(antCoord)

trackPoints: List[TrackPoint] = []

origTime = Time.now()
for i in range(180):
    trackPoints.append(TrackPoint(mount.local_altaz(20 * u.deg, i * u.deg), origTime + (i*2+100) * u.s))

def update_callback(i: int, total: int):
    print("Uploaded track point", i, "/", total)

mount.track(trackPoints, update_callback)
print("Started tracking")

while mount.get_status() != MountStatus.STOPPED:
    pos = mount.get_position().transform_to("altaz")
    print("Position:", (round(pos.alt.deg, 2), round(pos.az.deg, 2)))