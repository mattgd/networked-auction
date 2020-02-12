import enum
import socket
import sys
import threading

class ClientType(enum.Enum):
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


WAITING_FOR_SELLER_RESPONSE = False


class Client(threading.Thread):
    def __init__(self, conn, client_type=ClientType.BUYER):
        super(Client, self).__init__()
        self.conn = conn
        self.client_type = client_type
 
        self.data = ''
        # Change status to disconnect Buyer clients until auction begins
        if self.client_type == ClientType.SELLER:
            WAITING_FOR_SELLER_RESPONSE = True       

    def run(self):
        print('New client thread spawned')

        # Send the client their role
        self.send_msg(u'Your role is: [{}]\r\n'.format(self.client_type.name.title()))

        if self.client_type == ClientType.SELLER:
            self.send_msg(u'Please submit auction request:\r\n')
            
        while True:
            self.data = self.data + self.conn.recv(1024)
            print(self.data)

            if self.data.endswith(u'\r\n'):
                # Handle auction request
                if WAITING_FOR_SELLER_RESPONSE:
                    auction_request = self.data.split(',')

                    if len(auction_request) >= 4:
                        try:
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
                        except ValueError:
                            self.send_msg(u'Server: invalid auction request.')

                        self.send_msg(u'Auction request received: ' + self.data)
                        WAITING_FOR_SELLER_RESPONSE = False
                    else:
                        self.send_msg(u'Server: invalid auction request.')
                else:
                    pass

                print(self.data)
                self.data = ''

    def send_msg(self, msg):
        self.conn.send(msg)

    def close(self):
        self.conn.close()

class ConnectionThread(threading.Thread):
    def __init__(self, host, port):
        super(ConnectionThread, self).__init__()

        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.bind((host, port))
            self.s.listen(5)
            print('Auctioneer is ready for hosting auctions!')
        except socket.error:
            print('Failed to create socket')
            sys.exit()

        self.clients = []

    def run(self):
        while True:
            try:
                conn, address = self.s.accept()
                c = Client(conn, ClientType.BUYER if len(self.clients) else ClientType.SELLER)
                c.start()

                # print('[+] Client connected: {0}'.format(address[0]))
                c.send_msg(u'Connected to the Auctioneer server.\r\n')

                if WAITING_FOR_SELLER_RESPONSE:
                    c.send_msg(u'Server busy!\r\n')
                    c.close()
                else:
                    self.clients.append(c)
                    #c.send_msg(u'Connected to the Auctioneer server.')
            except KeyboardInterrupt:
                sys.exit()
      

def main():
    get_conns = ConnectionThread(host, port)
    get_conns.start()
    while True:
        try:
            response = raw_input() 
            for c in get_conns.clients:
                c.send_msg(response + u'\r\n')
        except KeyboardInterrupt:
            sys.exit()

if __name__ == '__main__':
    main()