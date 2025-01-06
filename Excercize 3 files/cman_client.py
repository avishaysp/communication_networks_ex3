from enum import Enum
import socket
import select
from time import sleep
from typing import List
from cman_utils import get_pressed_keys, clear_print
from consts import BUFFER_SIZE, ERROR, GAME_END, GAME_STATE_UPDATE, MAP_PATH
from cman_game import MAX_ATTEMPTS
from client_map import WorldMap

class Client:
    class Status(Enum):
        WAITING = 0
        PLAYING = 1
        GAME_OVER = 2
    
    class Role(Enum):
        SPECTATOR = 0
        CMAN = 1
        GHOST = 2

    def __init__(self, role: Role, server_address):
        self.server_address = server_address
        self.role = role
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.status = Client.Status.WAITING
        self.map = WorldMap(MAP_PATH)
        self.attempts = 0

    def run(self):
        while self.status != Client.Status.GAME_OVER:
            if self.role != Client.Role.SPECTATOR and self.status == Client.Status.PLAYING:
                self._process_user_input()
            self._handle_server_input()

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
        _ = data[0] # freeze - not used
        c_coords_b = data[1:3]
        s_coords_b = data[3:5]
        attempts = data[5]
        collected = data[6:] # representing 40 bit flags if the points were collected
        assert len(collected) == 5, f'Expected 5 collected bytes, got {len(collected)}'

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
        pass

    def __handle_error(self, data):
        pass
    
    def _process_user_input(self):
        pass