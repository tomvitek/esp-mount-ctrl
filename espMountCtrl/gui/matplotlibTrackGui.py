import numpy as np

from espMountCtrl.mountConnection import MountStatus
from .trackGui import TrackGUI
from ..mount import Mount, TrackPoint
from matplotlib import pyplot as plt
import math
from typing import Callable
from astropy.coordinates import SkyCoord

class MatplotlibTrackGUI(TrackGUI):
    def __init__(self, mount: Mount, points: TrackPoint):
        self.mount = mount
        self.points = points

        self.alts_real = np.array([], dtype=np.float64)
        self.azs_real = np.array([], dtype=np.float64)
        self.times_real = np.array([], dtype=np.float64)
        self.show_launched = False
    
    def show(self) -> None:
        plt.ion()

        self.alts_sim = np.fromiter([point.coord.alt.deg for point in self.points], dtype=np.float64)
        self.azs_sim = np.fromiter([point.coord.az.deg for point in self.points], dtype=np.float64)
        self.times = np.array([point.t.unix for point in self.points], dtype=np.float64)

        self.fig_altaz, self.ax_altaz = plt.subplots(subplot_kw={"projection":"polar"})
        self.ax_altaz.plot(self.azs_sim * math.pi / 180, self.alts_sim, label="Expected")
        self.ax_altaz.plot(self.azs_sim[0] * math.pi / 180, self.alts_sim[0], 'x', color="r", label="Start position")
        self.ax_altaz.plot(self.azs_sim[-1] * math.pi / 180, self.alts_sim[-1], 'x', color="g", label="End position")
        self.ax_altaz.set_ylim(0, 90)
        self.ax_altaz.set_rticks(range(0, 91, 20))
        self.ax_altaz.invert_yaxis()
        self.ax_altaz.grid(True)

        self.ax_altaz.set_title("Transit prediction - altaz")
        self.ax_altaz.legend()

        self.fig_alt = plt.figure()
        plt.plot(self.times, self.alts_sim, label="Expected")
        plt.title("Altitude")
        plt.legend()
        self.ticks_alt = plt.xticks()

        self.fig_az = plt.figure()
        plt.plot(self.times, self.azs_sim, label="Expected")
        plt.title("Azimuth")
        plt.legend()
        self.ticks_az = plt.xticks()
        plt.draw()
    
        plt.figure(self.fig_altaz)
        self.graph_altaz = plt.plot(self.azs_real, self.alts_real, label="Mount")[0]
        plt.legend()

        plt.figure(self.fig_alt)
        self.graph_alt = plt.plot(self.times_real, self.alts_real, label="Mount")[0]
        plt.legend()

        plt.figure(self.fig_az)
        self.graph_az = plt.plot(self.times_real, self.azs_real, label="Mount")[0]
        plt.legend()
    
    def loop(self, loopCallback: Callable[[SkyCoord, float], None] = None) -> None:
        if not self.show_launched:
            self.show()
        
        while self.mount.get_status() != MountStatus.STOPPED:
            time = self.mount.time
            pos = self.mount.get_position().transform_to("altaz")
            self.times_real = np.append(self.times_real, [time.unix])
            self.alts_real = np.append(self.alts_real, [pos.alt.deg])
            self.azs_real = np.append(self.azs_real, [pos.az.deg])
            
            plt.figure(self.fig_altaz)
            self.graph_altaz.set_xdata(self.azs_real * math.pi / 180)
            self.graph_altaz.set_ydata(self.alts_real)
            plt.draw()

            plt.figure(self.fig_alt)
            self.graph_alt.set_xdata(self.times_real)
            self.graph_alt.set_ydata(self.alts_real)
            plt.xticks(self.ticks_alt[0], self.ticks_alt[1])
            plt.draw()
            plt.figure(self.fig_az)
            self.graph_az.set_xdata(self.times_real)
            self.graph_az.set_ydata(np.array(self.azs_real))
            plt.xticks(self.ticks_az[0], self.ticks_az[1])
            plt.draw()

            plt.pause(0.01)

            if not loopCallback is None:
                # Number, where values 0 to 1 signalize time part of the transit
                transit_part = (time.unix - self.times[0]) / (self.times[-1] - self.times[0])
                loopCallback(pos, transit_part)