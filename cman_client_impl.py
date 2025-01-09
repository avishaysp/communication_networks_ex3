from enum import Enum
import socket
import select
from time import sleep
from typing import List
from cman_utils import get_pressed_keys, clear_print
from consts import *
from cman_game import MAX_ATTEMPTS
from client_map import WorldMap


class Status(Enum):
    WAITING = 0
    PLAYING = 1
    GAME_OVER = 2

class Role(Enum):
    SPECTATOR = 0
    CMAN = 1
    GHOST = 2

class Client:

    def __init__(self, role, server_address: tuple):
        self.server_address = server_address
        self.role = Role(role)
        self.init_socket()
        self.status = Status.WAITING
        self.map = WorldMap(MAP_PATH)
        self.attempts = 0
        self.__msg = ''

    def close(self):
        self.socket.close()

    def exit(self, msg):
        print(msg)
        self.close()
        exit()

    def init_socket(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except socket.error as e:
            self.exit('Failed to create socket')

    def run(self):
        print('Running client...')
        get_pressed_keys()
        self.join_game()
        while self.status != Status.GAME_OVER:
            self._process_user_input()
            self._handle_server_input()

    def msg(self):
        return "Message: " + self.__msg if self.__msg else ''

    def join_game(self):
        self.__send_msg(JOIN, self.role.value.to_bytes(1, 'big'))
        print(f'Requested to join as {self.role.name}')

    def _handle_server_input(self):
        datas = self.__recv_data()
        if not len(datas):
            return
        
        for data in datas:
            self.__handle_server_message(data)
        clear_print('\n'.join([self.msg(), self.attempts_repr(), self.map.to_string()]))

    def attempts_repr(self):
        return f"Attempt: {self.attempts}/{MAX_ATTEMPTS}"

    def __recv_data(self):
        datas = []
        try:
            while True:
                ready, _, _ = select.select([self.socket], [], [], 0)
                if not ready:
                    break
                
                raw, addr = self.socket.recvfrom(BUFFER_SIZE)
                if addr == self.server_address:
                    datas.append(raw)
        except socket.error as e:
            self.exit(f'Failed to receive data from server. Error: {e}\nExiting...')
        
        return datas
    
    def __handle_server_message(self, data: bytes):
        op_code = data[0]
        if op_code == GAME_STATE_UPDATE:
            self.__update_map(data[1:])
        elif op_code == GAME_END:
            self.__handle_game_end(data[1:])
        elif op_code == ERROR:
            self.__handle_error(data[1:])
    
    def __update_map(self, data):
        freeze = data[0]
        c_coords_b = data[1:3]
        s_coords_b = data[3:5]
        attempts = data[5]
        collected = data[6:] # representing 40 bit flags if the points were collected
        assert len(collected) == 5, f'Expected 5 collected bytes, got {len(collected)}'

        if not freeze:
            self.status = Status.PLAYING
            self.__msg = 'Game started!'
        else:
            self.__msg = 'Connected to server. Cannot move.'

        self.__update_attempts(attempts)

        self.map.remove_players()
        self.__update_points(collected)
        self.__place_cman_ghost(c_coords_b, s_coords_b)

    def __update_attempts(self, attempts):
        self.attempts = attempts + 1

    def __place_cman_ghost(self, c_coords_b, s_coords_b):
        c_coords = c_coords_b[0], c_coords_b[1]
        s_coords = s_coords_b[0], s_coords_b[1]
        assert self.map.get(*c_coords) != WorldMap.Entry.WALL.value, 'Cman is in a wall!'
        assert self.map.get(*s_coords) != WorldMap.Entry.WALL.value, 'Ghost is in a wall!'
        self.map.place_cman(*c_coords)
        self.map.place_ghost(*s_coords)

    def __update_points(self, collected):
        starting_point_indexes = self.map.get_starting_points_indexes()
        points_flags = self.__get_points_flags(collected)
        for i, (row, col) in enumerate(starting_point_indexes):
            if points_flags[i]:
                self.map.remove_point(row, col)
            else:
                self.map.place_point(row, col)


    def __get_points_flags(self, collected) -> List[bool]:
        points_flags = []
        for byte in collected:
            for i in range(8):
                points_flags.append(bool(byte & (128 >> i)))
        return points_flags

    def __handle_game_end(self, data):
        winner = data[0]
        s_score = data[1]
        c_score = data[2]
        self.status = Status.GAME_OVER
        clear_print(f'Game Over!\nWinner: {Role(winner).name}\nScores: Cman points: {c_score}, Ghost catches: {s_score}')
        self.exit('Exiting...')

    def __handle_error(self, data: bytes):
        err_code = data[-1]
        self.__msg = f' Server Error: {ERROR_DICT[err_code]}' if err_code < len(ERROR_DICT) else 'Unknown error'
        if err_code <= 5:
            print(self.msg())
            self.exit('Exiting...')
    
    def _process_user_input(self):
        keys: list = get_pressed_keys()
        if not len(keys):
            return
        selected_key = keys[0].lower() # only process the first key, ignore the rest

        if selected_key in ['^C', '^D', 'q']:
            self._quit_game()

        if self.role != Role.SPECTATOR and self.status == Status.PLAYING:
            self.__send_movement(selected_key)

    def __send_msg(self, op_code: int, data: bytes):
        try:
            self.socket.sendto(bytes([op_code]) + data, self.server_address)
        except socket.error as e:
            self.exit('Failed to send message to server. Exiting...')

    def __send_movement(self, selected_key):
        if selected_key not in DIRECTION_TO_BYTE:
            print(f'Invalid key: {selected_key} Please use the WASD keys to move, Q to exit.')
            return
        self.__send_msg(PLAYER_MOVEMENT, DIRECTION_TO_BYTE[selected_key].to_bytes(1, 'big'))

    def _quit_game(self):
        self.__send_msg(QUIT, b'')
        self.exit('Quitting game...')