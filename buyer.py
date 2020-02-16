from auction import get_auction
from client import Client
from status import ServerStatus, SERVER_STATUS


class Buyer(Client):
    def __init__(self, bidder_id):
        super(Buyer, self).__init__()
        self.bidder_id = bidder_id
        self.bid = None

    def run(self):
        super().run()

        # Send the client their role
        self.send_msg('Your role is: [Buyer]\r\n')
            
        while True:
            # Receive bid until the Buyer submits a bid
            if not self.bid:
                self.data = self.data + self.conn.recv(1024)

                if self.data.endswith('\r\n'):
                    try:
                        # Submit the bid to the auction
                        self.bid = int(self.data.strip())
                        get_auction().add_bid(self.bidder_id, self.bid)
                        self.send_msg('Bid received. Please wait...\r\n')
                    except ValueError:
                        self.send_msg('Invalid bid. Please submit a positive integer!\r\n')

                    print(self.data)
                    self.data = ''
