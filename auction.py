import threading

lock = threading.Lock()
CURRENT_AUCTION = None

class Auction:
    def __init__(self, auction_type, lowest_price, num_bids, item_name):
        self.auction_type = auction_type
        self.lowest_price = lowest_price
        self.num_bids = num_bids
        self.item_name = item_name
        self.bids = {}

    def add_bid(self, bidder_id, bid_amount):
        self.bids[bidder_id] = bid_amount


def get_auction():
    with lock:
        return CURRENT_AUCTION

def set_auction(auction):
    with lock:
        global CURRENT_AUCTION
        CURRENT_AUCTION = auction