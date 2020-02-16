import socket
import sys
import threading

from auction import get_auction
from buyer import Buyer
from seller import Seller
from status import lock, ServerStatus, get_server_status


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
                    if get_server_status() == ServerStatus.WAITING_FOR_SELLER:
                        conn.sendall(b'Server busy!\r\n')
                        conn.close()
                    else:
                        c = Buyer(conn)
                        self.buyers.append(c)
                        c.start()

                        if len(self.buyers) == get_auction().num_bids:
                            # Send bidding start message to all buyers
                            for buyer in self.buyers:
                                buyer.send_msg('Bidding start!\r\n')

                            # Notify the seller that bidding is on-going
                            self.seller.send_msg('Bidding has started...\r\n')
                        elif len(self.buyers) > get_auction().num_bids:
                            c.send_msg('Bidding on-going!\r\n')
                            c.close()
                        else:
                            c.send_msg('Waiting for buyers...\r\n')
                else:
                    # No Seller thread, create one
                    c = Seller(conn)
                    self.seller = c
                    c.start() 
            except KeyboardInterrupt:
                sys.exit()


class BiddingThread(threading.Thread):
    def __init__(self, host, port, num_bids):
        super(BiddingThread, self).__init__()
        self.num_bids = num_bids

        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.bind((host, port))
            self.s.listen(num_bids)
        except socket.error:
            print('Failed to create bidding socket')
            sys.exit()

        self.bids = []
        self.buyers = []

    def run(self):
        while True:
            try:
                conn, address = self.s.accept()
                c = Buyer(conn)
                self.buyers.append(c)
                c.start()

                if len(self.buyers) == self.num_bids:
                    # Send bidding start message to all buyers
                    for buyer in self.buyers:
                        buyer.sendmsg('Bidding start!\r\n')
                else:
                    c.sendmsg('Waiting for buyers...\r\n')
            except KeyboardInterrupt:
                sys.exit()

def main():
    get_conns = ConnectionThread(host, port)
    get_conns.start()

if __name__ == '__main__':
    main()
