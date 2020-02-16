CURRENT_AUCTION = None

class Auction:
    def __init__(self, auction_type, lowest_price, num_bids, item_name):
        self.auction_type = auction_type
        self.lowest_price = lowest_price
        self.num_bids = num_bids
        self.item_name = item_name