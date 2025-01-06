import socket
import select
from const import SERVER_ADDR, MAP_PATH, BUFFER_SIZE, JOIN, PLAYER_MOVEMENT, QUIT, GAME_STATE_UPDATE, GAME_END, ERROR

from cman_game import Game

class CManServer:

    def __init__(self, port):
        self.port = port
        self.watchers = []
        self.cman = None
        self.ghost = None
        self.server_socket = None

    def start_server(self):

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_address = (SERVER_ADDR, self.port)
        self.server_socket.bind(server_address)

        print(f"UDP server is running on {SERVER_ADDR}:{self.port}")

        self.start_game()

    def start_game(self):

        game = Game(MAP_PATH)

        try:
            while True:
                read_sockets, _, _ = select.select([self.server_socket], [], [], 1)

                for sock in read_sockets:
                    if sock is self.server_socket:
                        data, client_address = self.server_socket.recvfrom(BUFFER_SIZE)

                        self._process_data(data, client_address)



                        # send to client
                        # server_socket.sendto(response.encode('utf-8'), client_address)

        except KeyboardInterrupt:
            print("\nServer shutting down...")
        finally:
            self.server_socket.close()

    # Join requests
    def _process_data(self, data, client_address):
        prefix = _get_data_prefix(data)
        if prefix == ERROR:
            return 'bad format error, message prefix is not correct'

        if prefix == JOIN:
            message = self._process_join_request(data, client_address)
            return message

        if not self._verify_participants(client_address):
            return 'Unknown client'

        if prefix == PLAYER_MOVEMENT:
            message = self._process_player_movement_request(data, client_address)

    def _process_join_request(self, data, client_address):
        if len(data) != 2 and data[1] not in [0x00, 0x01, 0x02]:
            return 'bad format error, join request role is not correct'

        if self._verify_participants(client_address):
            return 'Client is already in the game'

        role = data[1]

        if role == 0x00:
            self.watchers.append(client_address)
            return

        return self._fill_cman_or_ghost(data, client_address)

    def _fill_cman_or_ghost(self, role, client_address):
        if role == 0x01 and not self.cman:
            self.cman = client_address
            return

        if role == 0x02 and not self.ghost:
            self.ghost = client_address
            return

        role_name = 'cman' if role == 0x01 else 'ghost'
        return f'{role_name} position is already taken'

    # Move requests
    def _process_player_movement_request(self, data, client_address):
        if len(data) != 2 and data[1] not in [0x00, 0x01, 0x02, 0x03]:
            return 'bad format error, move is not correct'

    def _verify_participants(self, client_address):
        return self.cman == client_address or self.ghost == client_address or client_address in self.watchers


def _get_data_prefix(data):
    prefix = data[0]
    if prefix == JOIN:
        return JOIN
    elif prefix == PLAYER_MOVEMENT:
        return PLAYER_MOVEMENT
    elif prefix == QUIT:
        return QUIT
    return ERROR
