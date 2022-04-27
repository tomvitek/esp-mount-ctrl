from time import sleep
from espMountCtrl.mount import Mount
from espMountCtrl.mountConnection import MountStatus
from espMountCtrl.satellites.transit import Transit
from ..satellites import SatelliteFinder, SatelliteTracker
from astropy.coordinates import EarthLocation, AltAz
from astropy.time import Time
import astropy.units as u
from ..mount import Mount
from matplotlib import pyplot as plt
import numpy as np
import math

## DOWNLOAD SATELLITE INFO
name = 'grbalpha'
sat = SatelliteFinder.fromName(name, False)[0]
#sat = SatelliteFinder.fromCatalogueNumber(25544)[0]  # ISS
print("Satellite:", sat)

# SETUP MOUNT
mount = Mount.from_ax_altaz('90deg', '0deg', '16deg', '49deg', '220m')
mount.connect("/dev/ttyUSB0")
mount.calibrate_ant_coord(mount.local_altaz('0deg', '90deg'))

# FIND OPTIMAL TRANSIT IN THE NEAR FUTURE
satTracker = SatelliteTracker(mount)
transits = satTracker.find_transits(sat, time_to=Time.now() + 3 * u.day, min_elev=10 * u.deg)
best_transit: Transit = None
print("Transits:")
for transit in transits:
    print(transit)
    if best_transit == None or best_transit.max_elev_altaz.alt < transit.max_elev_altaz.alt:
        best_transit = transit

print("Best transit:", best_transit)


print("Running track preview")
track_points = best_transit.calculate_track_points(600)

plt.ion()


alts_sim = np.fromiter([point.coord.alt.deg for point in track_points], dtype=np.float64)
azs_sim = np.fromiter([point.coord.az.rad for point in track_points], dtype=np.float64)
times = np.array([point.t.unix for point in track_points])

fig_altaz, ax_altaz = plt.subplots(subplot_kw={'projection':'polar'})
ax_altaz.plot(azs_sim, alts_sim, label="Expected")
ax_altaz.set_ylim(0, 90)
ax_altaz.set_rticks(range(0, 91, 20))
ax_altaz.invert_yaxis()
ax_altaz.grid(True)

ax_altaz.set_title("Transit prediction - altaz")
ax_altaz.legend()

fig_alt = plt.figure()
plt.plot(times, alts_sim, label="Expected")
plt.title("Altitude")
plt.legend()
ticks_alt = plt.xticks()

fig_az = plt.figure()
plt.plot(times, azs_sim / math.pi * 180, label="Expected")
plt.title("Azimuth")
plt.legend()
ticks_az = plt.xticks()
plt.draw()
plt.pause(5)
plt.figure(fig_altaz)

mount.time = best_transit.time_rise - 2 * u.min
mount.track(track_points, lambda i, tot: print("Uploaded", i, "/", tot))

alts_real = []
azs_real = []
times_real = []
plt.figure(fig_altaz)
graph_altaz = plt.plot(azs_real, alts_real, label="Mount")[0]
plt.legend()
plt.figure(fig_alt)
graph_alt = plt.plot(times_real, alts_real, label="Mount")[0]

plt.legend()
plt.figure(fig_az)
graph_az = plt.plot(times_real, azs_real, label="Mount")[0]

plt.legend()
while mount.get_status() != MountStatus.STOPPED:
    times_real.append(mount.time.unix)
    pos = mount.get_position().transform_to("altaz")
    alts_real.append(pos.alt.deg)
    azs_real.append(pos.az.rad)

    print("Position:", (round(pos.alt.deg, 2), round(pos.az.deg, 2)))
    ax_altaz.set_rticks(range(0, 91, 20))

    plt.figure(fig_altaz)
    graph_altaz.set_xdata(azs_real)
    graph_altaz.set_ydata(alts_real)
    plt.draw()

    plt.figure(fig_alt)
    graph_alt.set_xdata(times_real)
    graph_alt.set_ydata(alts_real)
    plt.xticks(ticks_alt[0], ticks_alt[1])
    plt.draw()
    plt.figure(fig_az)
    graph_az.set_xdata(times_real)
    graph_az.set_ydata(np.array(azs_real) / math.pi * 180)
    plt.xticks(ticks_az[0], ticks_az[1])
    plt.draw()

    plt.pause(0.01)

print("Tracking finished")

plt.show(block=True)