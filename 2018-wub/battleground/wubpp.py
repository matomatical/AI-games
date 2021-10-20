"""
Watch yoUr Back! Player Protocol

Help using a newline-delimited-message TCP-backed protocol for starting and
playing a game Watch Your Back! over a network

by Matt Farrugia, May 2018
"""

import socket

# switch for network send/recv message logging
DEBUG = False

def connect(host, port):
    """
    get a socket connected to a server so that we can play a game
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((host, port))
    return server_socket

def listen(host, port):
    """
    get a server socket you can use to easily accept new incoming connections
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen()
    return s


class WUBPlayerProtocol:
    def __init__(self, socket):
        """
        start a new Watch yoUr Back! Player Protocol on a TCP socket
        """
        self.socket = socket
        self.socketfile = socket.makefile('r')

    def disconnect(self):
        """
        close this protocol and its underlying socket
        do not call any other methods after this
        """
        self.socketfile.close()
        self.socket.close()

    def _sendmsg(self, head, *parts):
        """
        send a protocol message (line) with head and parts separated by spaces
        """
        message = (head, ) + parts
        line = ' '.join(message) + '\n'
        self.socket.sendall(line.encode())
        if DEBUG: print('SENDING:', repr(line.encode()))

    def _recvmsg(self):
        """
        receive a protocol message and split it into its head and parts
        """
        line = self.socketfile.readline()
        if not line:
            raise DisconnectException("connection lost---try again")
        line = line.strip()
        if DEBUG: print('RECVING:', repr(line), '(stripped)')

        head, parts = line[:4], line[4:].split()
        return head, parts

    def sendmsg(self, head, *parts):
        """
        send a protocol message with head head and parts parts.
        assumes a valid head and correctly ordered parts, but will take care
        of any necessary string conversions

        TODO: change to dict interface to match recvmsg,
        (e.g. only doing string conversions where necessary)
        """
        self._sendmsg(head, *[str(part) for part in parts])
        
    def recvmsg(self):
        """
        receive a protocol message and split it into its head and parts,
        and converts the head and parts to a dictionary
        """
        head, parts = self._recvmsg()
        if head == 'PLAY':
            msgdict = {
                'head': head,
                'name': parts[0], # name of player to submit to server
            }
            if len(parts) > 1:
                msgdict['key'] = parts[1] # password for matchmaking
            else:
                msgdict['key'] = ''
            return msgdict
        if head == 'GAME':
            return {
                'head': head,
                'white': parts[0], # white player name
                'black': parts[1], # black player name
            }
        if head == 'OKAY':
            return {
                'head': head,
            }
        if head == 'INIT':
            return {
                'head': head,
                'colour': parts[0], # 'black' or 'white' (which player are you)
            }
        if head == 'TURN':
            return {
                'head': head,
                'turns': int(parts[0]), # number of actions into phase
            }
        if head == 'ACTN' or head == 'UPD8':
            msgdict = {
                'head': head,
                'type': parts[0],
            }
            if msgdict['type'] == 'pass':
                pass # no additional fields
            elif msgdict['type'] == 'place':
                msgdict['x']  = int(parts[1]) # coordinates of place
                msgdict['y']  = int(parts[2])
            elif msgdict['type'] == 'move':
                msgdict['xa'] = int(parts[1]) # coordinates of move
                msgdict['ya'] = int(parts[2]) # coordinates
                msgdict['xb'] = int(parts[3])
                msgdict['yb'] = int(parts[4])
            return msgdict
        if head == 'ERRO':
            return {
                'head': head,
                'loser': parts[0],
                'reason': ' '.join(parts[1:]),
            }
        if head == 'OVER':
            return {
                'head': head,
                'winner': parts[0],
            }
        raise ProtocolException("invalid message")

class ProtocolException(Exception):
    """
    For when something goes wrong with the protocol
    (e.g. invalid header or missing message parts)
    """
class DisconnectException(Exception):
    """
    For when the connection closes while we are trying
    to recv a message
    """

# SIMPLE (SYNCHRONOUS) CLIENT-SERVER EXAMPLE PROGRAM
# 
# usage:
#   server: run `python3 wubpp.py -s`
#   client: run `python3 wubpp.py -c`

# CLIENT

# from wubpp import connect, WUBPlayerProtocol

def main_client():
    socket = connect()
    server = WUBPlayerProtocol(socket)

    # play msg
    name = input("enter your name (no spaces): ")
    server.sendmsg('PLAY', name)
    okaymsg = server.recvmsg()

    gamemsg = server.recvmsg()
    print(gamemsg)

    server.sendmsg('OKAY')

    initmsg = server.recvmsg()
    print('pretending to initialise with colour =', initmsg['colour'])

    server.sendmsg('OKAY')

# SERVER

# from wubpp import listen, WUBPlayerProtocol

def main_server():
    welcome_socket = listen()
    
    print('waiting for white player...')
    client_socket1, client_address1 = welcome_socket.accept()
    print(client_address1, 'connected')
    white_player = WUBPlayerProtocol(client_socket1)
    
    print('waiting for black player...')
    client_socket2, client_address2 = welcome_socket.accept()
    print(client_address2, 'connected')
    black_player = WUBPlayerProtocol(client_socket2)

    print('waiting for PLAY messages...')
    play_white = white_player.recvmsg()
    white_player.sendmsg('OKAY')
    play_black = black_player.recvmsg()
    black_player.sendmsg('OKAY')
    print(play_white, play_black)

    print('time to play! sending GAME message')
    white_player.sendmsg('GAME', play_white['name'], play_black['name'])
    black_player.sendmsg('GAME', play_white['name'], play_black['name'])

    print('waiting for OKAY messages...')
    okay_white = white_player.recvmsg()
    okay_black = black_player.recvmsg()
    print(okay_white, okay_black)

    print('let the game begin! sending INIT messages')
    print('(to let them know the colour they are playing)')
    white_player.sendmsg('INIT', 'white')
    black_player.sendmsg('INIT', 'black')

    print('waiting for OKAY messages...')
    okay_white = white_player.recvmsg()
    okay_black = black_player.recvmsg()
    print(okay_white, okay_black)


    print('at this point we would enter the TURN, ACTN, UPD8, OKAY loop')
    print('but let\'s finish here for today')

if __name__ == '__main__':
    import sys
    if not sys.argv[1:]:
        print('error: must specify -c (client) or -s (server)', file=sys.stderr)
    elif sys.argv[1] == '-c':
        main_client()
    elif sys.argv[1] == '-s':
        main_server()
    