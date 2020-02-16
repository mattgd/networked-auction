from enum import IntEnum

class ServerStatus(IntEnum):
    WAITING_FOR_SELLER = 0
    WAITING_FOR_BUYER = 1

SERVER_STATUS = ServerStatus.WAITING_FOR_SELLER
