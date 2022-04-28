from espMountCtrl.mount import Mount
from astropy.coordinates import SkyCoord, EarthLocation
from astropy.time import Time
import astropy.units as u
from time import time

mount = Mount.from_ax_altaz(10 * u.deg, 90 * u.deg, 49 * u.deg, 16 * u.deg)

mount.cprRa = 360
mount.cprDec = 360

loc = EarthLocation.from_geodetic(16 * u.deg, 49 * u.deg)

alt_raw = 0
az_raw = 271
testPos1 = SkyCoord(alt=alt_raw * u.deg, az=az_raw * u.deg, location=loc, frame="altaz", obstime=Time.now())
print((alt_raw, az_raw), "->", mount._coord_to_mount_pos(testPos1))

t1 = time()
for i in range(0, 10):
    mount._coord_to_mount_pos(testPos1)

t2 = time()
print("Stress test time:", t2 - t1, "s")

test = Time.now()
print(test.to_value("unix") * 1000)