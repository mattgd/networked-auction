import socket
import sys


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
print('Socket created')

data = ''

while True:
    data = client_socket.recv(1024)

    if data.endswith(u'\r\n'):
        print(data)
        data = ''


# Prompt the user for input sentence
# sentence = raw_input('Input lowercase sentence: ')

# # Send message over the socket
# client_socket.send(sentence)

# # Receive from socket
# modified_sentence = client_socket.recv(1024)
# print('From TCP server: ' + modified_sentence)

# Close the socket
client_socket.close()
