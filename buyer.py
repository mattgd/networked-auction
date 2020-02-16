from client import Client
from status import ServerStatus, SERVER_STATUS


class Buyer(Client):
    def run(self):
        super().run()
            
        while True:
            self.data = self.data + self.conn.recv(1024)

            if self.data.endswith('\r\n'):
                print(self.data)
                self.data = ''
