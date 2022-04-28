from abc import ABC, abstractclassmethod
from typing import Callable
from astropy.coordinates import SkyCoord

class TrackGUI(ABC):

    @abstractclassmethod
    def show(self) -> None:
        pass

    @abstractclassmethod
    def loop(self, loopCallback: Callable[[SkyCoord, float], None]) -> None:
        pass
