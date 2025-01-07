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

    def __init__(self, role: Role, server_address: tuple):
        self.server_address = server_address
        self.role = role
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.status = Status.WAITING
        self.map = WorldMap(MAP_PATH)
        self.attempts = 0

    def run(self):
        self.join_game()
        while self.status != Status.GAME_OVER:
            if self.role != Role.SPECTATOR and self.status == Status.PLAYING:
                self._process_user_input()
            self._handle_server_input()

    def join_game(self):
        self.__send_msg(JOIN, self.role.value.to_bytes(1, 'big'))

    def _handle_server_input(self):
        datas = self.__recv_data()
        if not len(datas):
            return
        
        for data in datas:
            self.__handle_server_message(data)
        clear_print(self.attempts_repr() + self.map.to_string())

    def attempts_repr(self):
        return f"Attempts: {self.attempts}/{MAX_ATTEMPTS}\n"

    def __recv_data(self):
        datas = []
        while True:
            ready, _, _ = select.select([self.socket], [], [], 0)
            if not ready:
                break
            
            raw, addr = self.socket.recvfrom(BUFFER_SIZE)
            if addr == self.server_address:
                datas.append(raw)
        
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

        self.__update_attempts(attempts)

        # first add points/floor, then override with cman & ghost:
        self.__update_points(collected)
        self.__update_cman_ghost_locations(c_coords_b, s_coords_b)

    def __update_attempts(self, attempts):
        self.attempts = attempts

    def __update_cman_ghost_locations(self, c_coords_b, s_coords_b):
        c_coords = c_coords_b[0], c_coords_b[1]
        s_coords = s_coords_b[0], s_coords_b[1]
        assert self.map.get(*c_coords) != WorldMap.Entry.WALL.value, 'Cman is in a wall!'
        assert self.map.get(*s_coords) != WorldMap.Entry.WALL.value, 'Ghost is in a wall!'
        self.map.move_cman(*c_coords)
        self.map.move_ghost(*s_coords)

    def __update_points(self, collected):
        starting_point_indexes = self.map.get_starting_points_indexes()
        points_flags = self.__get_points_flags(collected)
        for i, (row, col) in enumerate(starting_point_indexes):
            if points_flags[i]:
                self.map.remove_point(row, col)


    def __get_points_flags(self, collected) -> List[bool]:
        points_flags = []
        for byte in collected:
            for i in range(8):
                points_flags.append(bool(byte & (1 << i)))

    def __handle_game_end(self, data):
        winner = data[0]
        s_score = data[1]
        c_score = data[2]
        self.status = Status.GAME_OVER
        clear_print(f'Game Over!\nWinner: {Role(winner).name}\nScores: Cman: {c_score}, Ghost: {s_score}')
        exit()

    def __handle_error(self, data: bytes):
        err_code = data[-1]
        clear_print(f'Error: {ERROR_DICT[err_code]}')
    
    def _process_user_input(self):
        keys: list = get_pressed_keys()
        if len(keys):
            self.__send_movement(keys)

    def __send_msg(self, op_code: int, data: bytes):
        self.socket.sendto(bytes([op_code]) + data, self.server_address)

    def __send_movement(self, keys):
        selected_key = keys[0]
        self.__send_msg(PLAYER_MOVEMENT, DIRECTION_TO_BYTE[selected_key].to_bytes(1, 'big'))