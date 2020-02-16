from enum import Enum
import socket
import sys
import threading

from buyer import Buyer
from seller import Seller
from status import ServerStatus, SERVER_STATUS


class ClientType(Enum):
    SELLER = 0
    BUYER = 1



host = ''

if len(sys.argv) < 2:
    print('Please specify a port for the auctioneer server.')
    sys.exit()

try:
    port = int(sys.argv[1])
except ValueError:
    print('Invalid port value.')
    sys.exit()


class ConnectionThread(threading.Thread):
    def __init__(self, host, port):
        super(ConnectionThread, self).__init__()
        self.status = ServerStatus.WAITING_FOR_SELLER

        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.bind((host, port))
            self.s.listen(10)
            print('Auctioneer is ready for hosting auctions!')
        except socket.error:
            print('Failed to create socket')
            sys.exit()

        self.seller = None
        self.buyers = []

    def run(self):
        while True:
            try:
                conn, address = self.s.accept()
                c = None

                if self.seller:
                    # There's already a Seller thread
                    if SERVER_STATUS == ServerStatus.WAITING_FOR_SELLER:
                        conn.sendall(b'Server busy!\r\n')
                        conn.close()
                    else:
                        c = Buyer(conn)
                        self.buyers.append(c)
                        c.start()
                else:
                    # No Seller thread, create one
                    c = Seller(conn)
                    self.seller = c
                    c.start() 
            except KeyboardInterrupt:
                sys.exit()
      

def main():
    get_conns = ConnectionThread(host, port)
    get_conns.start()
    # while True:
    #     try:
    #         response = raw_input() 
    #         for c in get_conns.clients:
    #             c.send_msg(response + u'\r\n')
    #     except KeyboardInterrupt:
    #         sys.exit()

if __name__ == '__main__':
    main()
