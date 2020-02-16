from enum import IntEnum
import threading


class ServerStatus(IntEnum):
    WAITING_FOR_SELLER = 0
    WAITING_FOR_BUYER = 1

lock = threading.Lock()
SERVER_STATUS = ServerStatus.WAITING_FOR_SELLER

def get_server_status():
    with lock:
        return SERVER_STATUS

def set_server_status(status):
    print('Setting server status to ' + status.name)
    with lock:
        global SERVER_STATUS
        SERVER_STATUS = status
        print('Server status set to ' + status.name)
