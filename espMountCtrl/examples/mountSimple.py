from ..mount import Mount
from astropy.coordinates import SkyCoord, EarthLocation
import astropy.units as u
from astropy.time import Time

location = EarthLocation.from_geodetic(48, 16)
axCoord = SkyCoord(alt=0 * u.degree, az=0 * u.degree, frame="altaz", obstime=Time.now(), location=location)
mount = Mount(axCoord)
mount.connect("/dev/ttyUSB1")
mount.stop(block=True)
mount.calibrate_ant_coord(SkyCoord(alt=0 * u.degree, az=270 * u.degree, frame="altaz", obstime=Time.now(), location=location))

mount.sync_time()

mount.disconnect()