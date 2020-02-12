import select
import socket
import sys
import Queue

SERVER_PORT = 12001

def handle_bid(connection_socket, address):
  sentence = connection_socket.recv(1024)
  capitalized_sentence = sentence.upper()
  connection_socket.send(capitalized_sentence)
  connection_socket.close()


print('Auctioneer TCP server is ready to receive!')
print('Status 0: Waiting for Seller')


# print('Server busy!')


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setblocking(0)
server_socket.bind(('', SERVER_PORT))
server_socket.listen(5)

# Sockets from which we expect to read
inputs = [server_socket]

# Sockets to which we expect to write
outputs = []

# Outgoing message queues (socket:Queue)
message_queues = {}

while inputs:
  readable, writable, exceptional = select.select(inputs, outputs, inputs)

  print(readable, writable, exceptional)

  # Handle inputs
  for s in readable:
    if s is server_socket:
      # A "readable" server socket is ready to accept a connection
      connection_socket, client_address = s.accept()
      #print >>sys.stderr, 'new connection from', client_address
      connection_socket.setblocking(0)
      inputs.append(connection_socket)

      # Give the connection a queue for data we want to send
      message_queues[connection_socket] = Queue.Queue()
    else:
      data = s.recv(1024)
      if data:
        # A readable client socket has data
        #print >>sys.stderr, 'received "%s" from %s' % (data, s.getpeername())
        message_queues[s].put(data)
        # Add output channel for response
        if s not in outputs:
          outputs.append(s)
      else:
        # Interpret empty result as closed connection
        #print >>sys.stderr, 'closing', client_address, 'after reading no data'
        # Stop listening for input on the connection
        if s in outputs:
          outputs.remove(s)

        inputs.remove(s)
        s.close()

        # Remove message queue
        del message_queues[s]

    # Handle outputs
    for s in writable:
      try:
        next_msg = message_queues[s].get_nowait()
      except Queue.Empty:
        # No messages waiting so stop checking for writability.
        #print >>sys.stderr, 'output queue for', s.getpeername(), 'is empty'
        outputs.remove(s)
      else:
        #print >>sys.stderr, 'sending "%s" to %s' % (next_msg, s.getpeername())
        s.send(next_msg)

    # Handle "exceptional conditions"
    for s in exceptional:
      #print >>sys.stderr, 'handling exceptional condition for', s.getpeername()
      # Stop listening for input on the connection
      inputs.remove(s)
      if s in outputs:
        outputs.remove(s)

      s.close()

      # Remove message queue
      del message_queues[s]
