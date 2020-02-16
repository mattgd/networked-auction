import threading

class Client(threading.Thread):
    def __init__(self, conn):
        super(Client, self).__init__()
        self.conn = conn
        self.data = ''

    def run(self):
        print('New client thread spawned')
        
        # Send client connection message
        self.send_msg('Connected to the Auctioneer server.\r\n')

    def send_msg(self, msg):
        self.conn.send(msg.encode())

    def close(self):
        self.conn.close()
