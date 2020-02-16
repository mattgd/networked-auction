import socket
import sys


CONNECTION_CLOSE_MSGS = [
    'Server busy!\r\n'
    'Bidding on-going!\r\n'
]

if len(sys.argv) < 3:
    print('Please specify the server host and port to connect.')
    sys.exit()

host = sys.argv[1]

try:
    port = int(sys.argv[2])
except ValueError:
    print('Invalid port value.')
    sys.exit()

# Create UDP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((host, port))

data = ''

while True:
    data = client_socket.recv(1024)

    if data.endswith(b'\r\n'):
        print(data.decode('utf-8'))

        if any(data.endswith(msg.encode()) for msg in CONNECTION_CLOSE_MSGS):
            break
        elif data.endswith(b'Please submit auction request:\r\n') or data.endswith(b'Server: invalid auction request.\r\n'):
            auction_request = input()

            # Send message over the socket
            client_socket.send((auction_request + '\r\n').encode())

        data = ''

# Close the socket
client_socket.close()
