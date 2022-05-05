from espMountCtrl.gui.matplotlibTrackGui import MatplotlibTrackGUI
from espMountCtrl.mount import Mount
from espMountCtrl.satellites import SatelliteFinder, SatelliteTracker, Transit
from astropy.time import Time
from astropy.coordinates import SkyCoord
import astropy.units as u
from matplotlib import pyplot as plt

## DOWNLOAD SATELLITE INFO
name = 'grbalpha'
sat = SatelliteFinder.fromName(name, False)[0]
#sat = SatelliteFinder.fromCatalogueNumber(25544)[0]  # ISS
print("Satellite:", sat)

# SETUP MOUNT
mount = Mount.from_ax_altaz(alt='49deg', az='0deg', lon='16deg', lat='49deg', elevation='220m')
mount.connect()
mount.stop(block=True)
mount.calibrate_ant_coord(mount.local_altaz('0deg', '90deg'))

# FIND OPTIMAL TRANSIT IN THE NEAR FUTURE
satTracker = SatelliteTracker(mount)
transits = satTracker.find_transits(sat, time_to=Time.now() + 3 * u.day, min_elev=10 * u.deg)
if len(transits) == 0:
    print("No transit found!")
    exit()
best_transit: Transit = transits[0]
print("Transits:")
for transit in transits:
    print(transit)
    if best_transit.max_elev_altaz.alt < transit.max_elev_altaz.alt:
        best_transit = transit

print("Best transit:", best_transit)

# CALCULATE TRACK DATA FOR THE SELECTED TRANSIT
print("Running track preview")
track_points = best_transit.calculate_track_points(600)

# INITIALIZE GUI
trackGui = MatplotlibTrackGUI(mount, track_points)

mount.time = best_transit.time_rise - 2 * u.min

# START TRACKING
print("Uploading track points...")
mount.track(track_points, print_upload_progres=True)

# PLOT AND PRINT DATA
def print_data(pos: SkyCoord, part: float):
    columns = [
        f"Position: ({round(pos.az.deg, 2)}, {round(pos.alt.deg, 2)})",
        f"\tPart: {round(part * 100, 2)} %",
        f"\tDistance: {round(transit.get_distance(mount.time).to_value(u.km), 2)} km"
    ]
    print("{: <20} {: <20} {: <20}".format(*columns))
    
trackGui.loop(loopCallback=print_data)

print("Tracking finished")
mount.disconnect()
# KEEP THE PLOT
plt.show(block=True)