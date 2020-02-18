from enum import IntEnum
import socket
import sys
import threading


host = ''

if len(sys.argv) < 2:
    print('Please specify a port for the auctioneer server.')
    sys.exit()

try:
    port = int(sys.argv[1])
except ValueError:
    print('Invalid port value.')
    sys.exit()

lock = threading.Lock()  # Lock for syncing operations

########################################
#                 Auction              #
########################################
CURRENT_AUCTION = None
SELLER = None


class Auction:
    def __init__(self, auction_type, lowest_price, num_bids, item_name):
        self.auction_type = auction_type
        self.lowest_price = lowest_price
        self.num_bids = num_bids
        self.item_name = item_name
        self.bids = []

    def add_bid(self, bidder_id, bid_amount):
        self.bids.append((bidder_id, bid_amount))

    def has_received_all_bids(self):
        return len(self.bids) == self.num_bids

    def get_winning_bid(self):
        sorted_bids = sorted(self.bids, key=lambda x: x[1], reverse=True)
        winning_bid = None

        if self.auction_type == 2:
            winning_bid = (sorted_bids[0][0], sorted_bids[1][1])
        else:
            winning_bid = sorted_bids[0]

        # Ensure bid meets lowest price requirement
        if winning_bid[1] >= self.lowest_price:
            return winning_bid
        else:
            return (None, None)


def get_auction():
    with lock:
        return CURRENT_AUCTION


def set_auction(auction):
    with lock:
        global CURRENT_AUCTION
        CURRENT_AUCTION = auction


########################################
#                 Status               #
########################################
class ServerStatus(IntEnum):
    WAITING_FOR_SELLER = 0
    WAITING_FOR_BUYER = 1


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


########################################
#                 Client               #
########################################
class Client(threading.Thread):
    def __init__(self, conn):
        super(Client, self).__init__()
        self.conn = conn
        self.data = ''

    def run(self):
        print('New client thread spawned')

        # Send client connection message
        self.send_msg('Connected to the Auctioneer server.\n')

    def send_msg(self, msg):
        self.conn.send(msg.encode())

    def close(self):
        self.conn.close()


########################################
#                 Seller               #
########################################
class Seller(Client):
    def run(self):
        super().run()

        # Send the client their role
        self.send_msg('Your role is: [Seller]\n')
        self.send_msg('Please submit auction request:\n')

        while True:
            try:
                self.data = self.data + self.conn.recv(1024).decode('utf-8')

                if self.data.endswith('\n'):
                    # Handle auction request
                    if SERVER_STATUS == ServerStatus.WAITING_FOR_SELLER:
                        auction_request = self.data.strip().split(',')

                        try:
                            if len(auction_request) < 4:
                                raise ValueError('Missing auction parameters')

                            auction_type = int(auction_request[0])
                            if auction_type not in {1, 2}:
                                raise ValueError('Auction type must be 1 for first-price or 2 for second-price')

                            auction_lowest_price = int(auction_request[1])
                            if auction_lowest_price < 0:
                                raise ValueError('Lowest price must be a positive integer')

                            auction_num_bids = int(auction_request[2])
                            if auction_num_bids < 0 or auction_num_bids > 9:
                                raise ValueError('Number of bids is must be a positive integer less than 10')

                            auction_item_name = auction_request[3]
                            if len(auction_item_name) > 255:
                                raise ValueError('Item name is longer than 255 characters')

                            set_auction(
                                Auction(
                                    auction_type=auction_type,
                                    lowest_price=auction_lowest_price,
                                    num_bids=auction_num_bids,
                                    item_name=auction_item_name.strip()
                                )
                            )
                            self.send_msg('Auction request received: ' + self.data)

                            # Update the server status to allow buyers
                            set_server_status(ServerStatus.WAITING_FOR_BUYER)

                            self.send_msg('Waiting for buyers...\n')
                        except ValueError:
                            self.send_msg('Server: invalid auction request.\n')
                    else:
                        self.send_msg('Waiting for buyers...\n')

                    self.data = ''
            except OSError:
                break


########################################
#                  Buyer               #
########################################
class Buyer(Client):
    def __init__(self, conn, bidder_id):
        super(Buyer, self).__init__(conn)
        self.bidder_id = bidder_id
        self.bid = None

    def run(self):
        super().run()

        # Send the client their role
        self.send_msg('Your role is: [Buyer]\n')

        while True:
            # Receive bid until the Buyer submits a bid
            if not self.bid:
                self.data = self.data + self.conn.recv(1024).decode('utf-8')

                if self.data.endswith('\n'):
                    try:
                        # Submit the bid to the auction
                        self.bid = int(self.data.strip())
                        get_auction().add_bid(self.bidder_id, self.bid)
                        print('Bid recieved from bidder {}: {}'.format(
                            self.bidder_id, self.bid
                        ))
                        self.send_msg('Bid received. Please wait...\n')
                    except ValueError:
                        self.send_msg(
                            'Invalid bid. Please submit a positive integer!\n'
                        )

                    self.data = ''


########################################
#            Bidding Thread            #
########################################
class BiddingThread(threading.Thread):
    def __init__(self, buyers):
        super(BiddingThread, self).__init__()
        self.buyers = buyers

    def run(self):
        print('Bidding thread spawned')

        global SELLER

        # Notify the seller that bidding is on-going
        SELLER.send_msg('Bidding has started...\n')

        # Send bidding start message to all buyers
        for buyer in self.buyers:
            buyer.send_msg('Bidding start!\n')

        while True:
            auction = get_auction()

            if auction.has_received_all_bids():
                winning_bidder_id, winning_bid = auction.get_winning_bid()
                losing_buyers = [buyer for buyer in self.buyers if buyer.bidder_id != winning_bidder_id]

                # Notify losers
                for buyer in losing_buyers:
                    buyer.send_msg('Unfortunately, you did not win the auction.\n')
                    buyer.close()

                # Notify winner, if there is one
                if winning_bidder_id is None:
                    SELLER.send_msg(
                        'Unfortunately, the item was not sold in the auction.\n'
                    )
                else:
                    SELLER.send_msg('The item {} sold for ${}.\n'.format(
                        auction.item_name, winning_bid
                    ))

                    winning_buyer = self.buyers[winning_bidder_id]
                    winning_buyer.send_msg('You won the auction for "{}" and now owe a payment of ${}.\n'.format(
                        auction.item_name, winning_bid
                    ))
                    winning_buyer.close()

                # Close seller connection
                SELLER.close()
                SELLER = None

                # Done now, reset auction and exit thread
                set_auction(None)
                set_server_status(ServerStatus.WAITING_FOR_SELLER)
                break


########################################
#      Connection/Welcoming Thread     #
########################################
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

        self.buyers = []

    def run(self):
        global SELLER

        while True:
            try:
                conn, address = self.s.accept()
                c = None

                auction = get_auction()  # Get the current auction

                if SELLER:
                    # There's already a Seller thread
                    if get_server_status() == ServerStatus.WAITING_FOR_SELLER:
                        conn.send(b'Server busy!\n')
                        conn.close()
                    else:
                        c = Buyer(conn, bidder_id=len(self.buyers))
                        self.buyers.append(c)
                        c.start()

                        if len(self.buyers) == auction.num_bids:
                            bidding = BiddingThread(self.buyers)
                            bidding.start()
                        elif len(self.buyers) > auction.num_bids:
                            c.send_msg('Bidding on-going!\n')
                            c.close()
                        else:
                            c.send_msg('Waiting for buyers...\n')
                else:
                    # No Seller thread, create one
                    c = Seller(conn)
                    SELLER = c
                    c.start()
            except (KeyboardInterrupt, socket.error):
                sys.exit()


def main():
    get_conns = ConnectionThread(host, port)
    get_conns.start()


if __name__ == '__main__':
    main()
