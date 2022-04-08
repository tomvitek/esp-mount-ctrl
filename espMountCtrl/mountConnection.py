from dataclasses import dataclass
from enum import Enum
import serial
from collections.abc import Sequence
from typing import Tuple, List

_CMD_FIRST_CHAR = "+"
_CMD_STR_GET_POS = "gp"
_CMD_STR_SET_POS = "p"
_CMD_STR_SET_TIME = "t"
_CMD_STR_GET_TIME = "gt"
_CMD_STR_GOTO = "g"
_CMD_STR_STOP = "s"
_CMD_STR_GET_CPR = "gc"
_CMD_STR_GET_PROTOCOL_VERSION = "gpv"
_CMD_STR_GET_TRACK_BUFFER_FREE_SPACE = "gtbf"
_CMD_STR_GET_TRACK_BUFFER_SIZE = "gtbs"
_CMD_STR_TRACK_BUFFER_CLEAR = "tbc"
_CMD_STR_TRACK_POINT_ADD = "tp"
_CMD_STR_TRACKING_START = "tb"
_CMD_STR_TRACKING_STOP = "ts"
_CMD_STR_GET_STATUS = "gs"

_CMD_FORMATTING = "ascii"


class TrackPointAddResult(Enum):
    OK = 0
    BUFFER_FULL = 1
    INTERNAL = 2

class MountStatus(Enum):
    STOPPED = 0
    GOTO = 1
    TRACKING = 2
    BRAKING = 3

class MountConnectionError(Exception):
    """Mount has responded unexpectedly, or hasn't responded at all"""
    def __init__(self, received: str = None):
        if received == None:
            super().__init__("Mount responded incorrectly.")
        else:
            super().__init__(f"Mount responded incorrectly: {received}")

class MountConnection:
    def __init__(self):
        self.ser = serial.Serial()

    def open(self, device: str) -> bool:
        self.ser = serial.Serial(device, 115200, timeout=1)
        return self.ser.is_open

    def close(self):
        if self.ser != None and self.ser.is_open:
            self.ser.close()

    def is_connected(self):
        return self.ser.is_open

    def _sendCmd(self, cmdStr: str, *args) -> List[str]:
        if len(args) == 0:
            cmd = f"{_CMD_FIRST_CHAR}{cmdStr}\n"
        else:
            args_joined = " ".join([str(arg) for arg in args])
            cmd = f"{_CMD_FIRST_CHAR}{cmdStr} {args_joined}\n"
        self.ser.write(cmd.encode(_CMD_FORMATTING))
        line = self.ser.readline()
        line = line.replace(b'\n', b'')
        segments = line.decode(_CMD_FORMATTING).split(" ")
        if segments[0] != f"{_CMD_FIRST_CHAR}{cmdStr}":
            raise MountConnectionError(line.decode(_CMD_FORMATTING))
        return segments

    def _send_int_cmd(self, cmdStr: str, intCount: int, *args) -> Tuple:
        segments = self._sendCmd(cmdStr, *args)
        if len(segments) != intCount + 1:
            raise MountConnectionError()
        
        resultList = list()
        for i in range(0, intCount):
            resultList.append(int(segments[i + 1]))
        return tuple(resultList)

    def get_position(self) -> Tuple[int, int]:
        return self._send_int_cmd(_CMD_STR_GET_POS, 2)
    
    def set_position(self, posAx1: int, posAx2: int) -> None:
        self._sendCmd(_CMD_STR_SET_POS, str(posAx1), posAx2)
    
    def get_time(self) -> int:
        return self._send_int_cmd(_CMD_STR_GET_TIME, 1)[0]
        
    def set_time(self, time: int) -> None:
        self._sendCmd(_CMD_STR_SET_TIME, time)
    
    def goto(self, posAx1: int, posAx2: int) -> None:
        self._sendCmd(_CMD_STR_GOTO, posAx1, posAx2)
    
    def stop(self, instant: bool) -> None:
        instant_int = int(instant)
        self._sendCmd(_CMD_STR_STOP, instant_int)
    
    def get_cpr(self) -> Tuple[int, int]:
        return self._send_int_cmd(_CMD_STR_GET_CPR, 2)

    def get_protocol_version(self) -> int:
        return self._send_int_cmd(_CMD_STR_GET_PROTOCOL_VERSION, 1)[0]

    def get_track_buffer_free_space(self) -> int:
        return self._send_int_cmd(_CMD_STR_GET_TRACK_BUFFER_FREE_SPACE, 1)[0]
    
    def get_track_buffer_size(self) -> int:
        return self._send_int_cmd(_CMD_STR_GET_TRACK_BUFFER_SIZE, 1)[0]
    
    def clear_track_buffer(self) -> None:
        self._sendCmd(_CMD_STR_TRACK_BUFFER_CLEAR)
    
    def add_track_point(self, posAx1: int, posAx2: int, time: int) -> TrackPointAddResult:
        return TrackPointAddResult(self._send_int_cmd(_CMD_STR_TRACK_POINT_ADD, 1, posAx1, posAx2, time)[0])
    
    def tracking_start(self) -> None:
        self._sendCmd(_CMD_STR_TRACKING_START)
    
    def tracking_stop(self) -> None:
        self._sendCmd(_CMD_STR_TRACKING_STOP)
    
    def get_mount_status(self) -> MountStatus:
        return MountStatus(self._send_int_cmd(_CMD_STR_GET_STATUS, 1)[0])