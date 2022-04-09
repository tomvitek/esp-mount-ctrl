
from ast import Load
from dataclasses import dataclass
from appdirs import user_cache_dir
from skyfield.iokit import Loader
from skyfield.sgp4lib import EarthSatellite
from os import path
from typing import List
from . import skyfield_load


_CELESTRAK_URL = "https://celestrak.com/NORAD/elements/gp.php"


def fromCatalogueNumber(catnr: int, reload: bool = True) -> List[EarthSatellite]:
    return skyfield_load.tle_file(f"{_CELESTRAK_URL}?CATNR={catnr}&FORMAT=TLE", reload=reload, filename=f"sat-catnr-{catnr}.tle")

def fromName(name: str, reload: bool = True) -> List[EarthSatellite]:
    return skyfield_load.tle_file(f"{_CELESTRAK_URL}?NAME={name}&FORMAT=TLE", reload=reload, filename=f"sat-name-{name}.tle")

def fromFile(filepath: str) -> List[EarthSatellite]:
    return skyfield_load.tle_file(filepath)
    