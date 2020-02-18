import socket
import sys


CONNECTION_CLOSE_MSGS = [
    'Server busy!\n'
    'Bidding on-going!\n'
]

PROMPT_MSGS = [
    'Please submit auction request:\n',
    'Server: invalid auction request.\n',
    'Bidding start!\n',
    'Invalid bid. Please submit a positive integer!\n'
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

    if not len(data):
        break
    elif data.endswith(b'\n'):
        print(data.decode('utf-8'))

        if any(data.endswith(msg.encode()) for msg in CONNECTION_CLOSE_MSGS):
            break
        elif any(data.endswith(msg.encode()) for msg in PROMPT_MSGS):
            input_data = input()

            # Send message over the socket
            client_socket.send((input_data + '\n').encode())

        data = ''

# Close the socket
client_socket.close()
