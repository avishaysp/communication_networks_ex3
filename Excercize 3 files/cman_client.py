from time import sleep
from cman_utils import get_pressed_keys, clear_print
from consts import PLAYER_MOVEMENT, QUIT

class Client:
    def __init__(self, server_address):
        self.server_address = server_address

    def run(self):
        while True:
            self._process_user_input()
            self._refresh_display()

    def _refresh_display(self):
        pass

    def _process_user_input(self):
        pass