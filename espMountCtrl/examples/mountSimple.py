from ..mount import Mount
from astropy.coordinates import SkyCoord, EarthLocation
import astropy.units as u
from astropy.time import Time

location = EarthLocation.from_geodetic(48, 16)
axCoord = SkyCoord(alt=30 * u.degree, az=270 * u.degree, frame="altaz", obstime=Time.now(), location=location)
mount = Mount(axCoord)
mount.connect()
mount.sync_time()
mount.stop(block=True)
mount.calibrate_ant_coord(SkyCoord(alt=10 * u.degree, az=40 * u.degree, frame="altaz", obstime=Time.now(), location=location))
startPos = mount.get_position()

zenitCoord = SkyCoord(alt=89 * u.deg, az=180 * u.deg, frame="altaz", obstime=Time.now(), location=location)
print("Current pos:", mount.get_position())
print("Goto to zenit")
mount.goto(zenitCoord, True)
print("Goto finished")
print("Current pos:", mount.get_position())
print("Going back to first position")
mount.goto(startPos, True)
print("finished")

mount.disconnect()