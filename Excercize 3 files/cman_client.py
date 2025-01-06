from enum import Enum
import socket
import select
from time import sleep
from cman_utils import get_pressed_keys, clear_print
from consts import BUFFER_SIZE, CODING, PLAYER_MOVEMENT, QUIT, MAP_PATH
from client_map import MapReader, MapConverter

class Client:
    class Status(Enum):
        WAITING = 0
        PLAYING = 1
        GAME_OVER = 2

    def __init__(self, server_address):
        self.server_address = server_address
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.status = Client.Status.WAITING
        self.map_matrix = MapReader(MAP_PATH).read_map()
        self.map_converter = MapConverter()

    def run(self):
        while self.status != Client.Status.GAME_OVER:
            self._process_user_input()
            self._refresh_display()

    def _refresh_display(self):
        data = self.__recv_data()
        if data is None:
            return
        self.__update_map(data)
        clear_print(self.map_converter.convert_to_string(self.map_matrix))

    def __recv_data(self):
        last_data = None
        while True:
            # we want to return the last packet, discard all packets before
            ready, _, _ = select.select([self.socket], [], [], 0)
            if not ready:
                break
            
            raw, addr = self.socket.recvfrom(BUFFER_SIZE)
            if addr == self.server_address:
                last_data = raw.decode(CODING)
        
        return last_data
    
    def __update_map(self, data):
        pass
    

    def _process_user_input(self):
        pass