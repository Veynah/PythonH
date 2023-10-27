import socket

target_host = "www.google.come"
target-port = 80

# create a socket object
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# connect the client
client.connect((target_host, target_port))

# send some data 
response = client.recv(4096)

print(response.decode())
client.close()
