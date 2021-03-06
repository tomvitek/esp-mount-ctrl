from time import sleep, time
from espMountCtrl.mountConnection import MountConnection, MountStatus

mountComm = MountConnection()
mountComm.open()
mountComm.set_position(1000, 0)
pos = mountComm.get_position()
print("Position:", pos)
mountTime = mountComm.get_time()
print("Time:", mountTime)
cpr = mountComm.get_cpr()
print("CPR:", cpr)
status = mountComm.get_mount_status()
print("Status:", status)
protocolVersion = mountComm.get_protocol_version()
print("Protocol version:", protocolVersion)
trackBufferFreeSpace = mountComm.get_track_buffer_free_space()
print("Track buffer - free space:", trackBufferFreeSpace)
trackBufferSize = mountComm.get_track_buffer_size()
print("Track buffer - size:", trackBufferSize)

mountComm.stop(True)
print("Initiating goto...")
mountComm.set_position(0, 0)
mountComm.goto(cpr[0] / 4, cpr[1] / 8)

t1 = time()
while mountComm.get_mount_status() == MountStatus.GOTO:
    print(mountComm.get_position()[0] / float(cpr[0]/4) * 100, "%")
    sleep(0.5)
t2 = time()
print("Goto finished. Duration:", t2 - t1)
print("Initiating tracking test...")
mountComm.set_position(0,0)
mountComm.clear_track_buffer()
mountComm.tracking_stop()
mountComm.add_track_point(6000, 6000, 5000)
mountComm.add_track_point(8000, 7000, 6500)
mountComm.add_track_point(0, 0, 1000)
mountComm.set_time(0)
print("Starting tracking")
mountComm.tracking_start()
while mountComm.get_mount_status() == MountStatus.TRACKING:
    sleep(0.5)
print("Tracking finished")

mountComm.close()