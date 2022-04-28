from espMountCtrl.mount import Mount, TrackPoint
from astropy.coordinates import SkyCoord, EarthLocation
from astropy.time import Time
import astropy.units as u
from typing import List
from espMountCtrl.gui import MatplotlibTrackGUI

# MOUNT SETUP
location = EarthLocation.from_geodetic(lon=49, lat=16)
axCoord = SkyCoord(frame="altaz", az='270d', alt='45d', obstime=Time.now(), location=location)
antCoord = SkyCoord(frame="altaz", az='90d', alt='0d', obstime=Time.now(), location=location)
mount = Mount(axCoord)
mount.connect()
mount.stop(block=True)
mount.calibrate_ant_coord(antCoord)

# GENERATE TRACK POINTS
print("Generating tracking points...")
trackPoints: List[TrackPoint] = []

origTime = Time.now() + 1 * u.min

alt_res = 3
alt_start = 10
time_per_degree = 1 * u.s
deltaT = 0 * u.s

for alt in range(alt_start, 91, alt_res):
    for az in range(90, 136):
        if round((alt - alt_start) / alt_res) % 2 != 0:
            az = 90 + 135 - az        
        trackPoints.append(TrackPoint(mount.local_altaz(alt=alt * u.deg, az=az * u.deg), origTime + deltaT))
        deltaT += time_per_degree
    deltaT += 10 * time_per_degree

# UPLOAD TRACK POINTS
def update_callback(i: int, total: int):
    print("Uploaded track point", i, "/", total)

mount.track(trackPoints, update_callback)
print("Started tracking")

# PLOT CURRENT STATUS
trackGui = MatplotlibTrackGUI(mount, trackPoints)
trackGui.loop()

print("Custom tracking finished")