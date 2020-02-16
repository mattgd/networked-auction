import threading

import auction
from client import Client
import status


class Seller(Client):
    def run(self):
        super().run()
        self.send_msg('Please submit auction request:\r\n')
        
        while True:
            self.data = self.data + self.conn.recv(1024).decode('utf-8')

            if self.data.endswith('\r\n'):
                # Handle auction request
                if status.SERVER_STATUS == status.ServerStatus.WAITING_FOR_SELLER:
                    auction_request = self.data.strip().split(',')
                    
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

                            auction.CURRENT_AUCTION = auction.Auction(
                                auction_type=auction_type,
                                lowest_price=auction_lowest_price,
                                num_bids=auction_num_bids,
                                item_name=auction_item_name
                            )
                            self.send_msg('Auction request received: ' + self.data)

                            # Update the server status to allow buyers
                            lock = threading.Lock()
                            with lock:
                                status.SERVER_STATUS = status.ServerStatus.WAITING_FOR_BUYER
                        except ValueError:
                            self.send_msg('Server: invalid auction request.')
                    else:
                        self.send_msg('Server: invalid auction request.\r\n')
                else:
                    self.send_msg('Waiting for buyers...\r\n')

                print(self.data)
                self.data = ''
