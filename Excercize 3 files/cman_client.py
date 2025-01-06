from enum import Enum
import socket
import select
from time import sleep
from cman_utils import get_pressed_keys, clear_print
from consts import BUFFER_SIZE, CODING, ERROR, GAME_END, GAME_STATE_UPDATE, PLAYER_MOVEMENT, QUIT, MAP_PATH
from client_map import MapReader, MapConverter

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
        self.map_matrix = MapReader(MAP_PATH).read_map()
        self.map_converter = MapConverter()

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
        clear_print(self.map_converter.convert_to_string(self.map_matrix))

    def __recv_data(self):
        datas = []
        while True:
            ready, _, _ = select.select([self.socket], [], [], 0)
            if not ready:
                break
            
            raw, addr = self.socket.recvfrom(BUFFER_SIZE)
            if addr == self.server_address:
                datas.append(raw.decode(CODING))
        
        return datas
    

    def __handle_server_message(self, data):
        op_code = data[0]
        if op_code == GAME_STATE_UPDATE:
            self.__update_map(data[1:])
        elif op_code == GAME_END:
            self.__handle_game_end(data[1:])
        elif op_code == ERROR:
            self.__handle_error(data[1:])
    
    def __update_map(self, data):
        pass
    
    def __handle_game_end(self, data):
        pass

    def __handle_error(self, data):
        pass
    
    def _process_user_input(self):
        pass