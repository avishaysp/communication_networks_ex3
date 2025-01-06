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

    def run(self):
        while self.status != Client.Status.GAME_OVER:
            self._process_user_input()
            self._refresh_display()

    def _refresh_display(self):
        pass

    def _process_user_input(self):
        pass