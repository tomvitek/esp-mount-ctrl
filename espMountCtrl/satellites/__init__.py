from os import path
from skyfield.iokit import Loader
from appdirs import user_cache_dir

skyfield_load = Loader(path.join(user_cache_dir("espMountCtrl"), "skyfield"))
skyfield_ts = skyfield_load.timescale()

from .satelliteTracker import SatelliteTracker
from . import satelliteFinder as SatelliteFinder
from .transit import Transit