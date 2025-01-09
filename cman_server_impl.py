import socket
import select
from enum import IntEnum

from consts import ERROR_DICT, SERVER_ADDR, MAP_PATH, BUFFER_SIZE, JOIN, PLAYER_MOVEMENT, QUIT, GAME_STATE_UPDATE, GAME_END, ERROR
import time

from cman_game import Game, Player, MAX_ATTEMPTS


class GameStatus(IntEnum):
    PREGAME = 0
    WAITING = 1
    PLAYING = 2
    START = 3
    END = 4


class CManServer:

    def __init__(self, port):
        self.port = port
        self.watchers = []
        self.cman = None
        self.ghost = None
        self.server_socket = None
        self.game = Game(MAP_PATH)
        self.game_status = GameStatus.PREGAME

    def start_server(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except socket.error as e:
            print(f'Failed to create socket. Error: {e}. Exiting...')
            exit()
        server_address = (SERVER_ADDR, self.port)
        self.server_socket.bind(server_address)

        print(f"UDP server is running on {SERVER_ADDR}:{self.port}")

        self.start_game()

    def start_game(self):
        print("Game is starting...")
        try:
            while True:
                read_sockets, _, _ = select.select([self.server_socket], [], [], 0)

                if len(read_sockets):
                    try:
                        data, client_address = self.server_socket.recvfrom(BUFFER_SIZE)
                    except socket.error as e:
                        print(f'Failed to receive data from client: {e}\nExiting...')
                        exit()
                    data_list = list(data)

                    error = self._process_data(data_list, client_address)

                    if error is not None:
                        print(f"Error: {ERROR_DICT[error]}")
                        self._send_error_message(error, client_address)

                    self._send_status_message()

        except KeyboardInterrupt:
            print("\nServer shutting down...")

        finally:
            self.server_socket.close()

    # Join requests
    def _process_data(self, data, client_address):
        prefix = _get_data_prefix(data)
        if prefix == ERROR:
            return 1

        if prefix == JOIN:
            message = self._process_join_request(data, client_address)
            return message

        if not self._verify_participants(client_address):
            return 2

        if prefix == PLAYER_MOVEMENT:
            message = self._process_player_movement_request(data, client_address)
            return message

        message = self._process_quit_request(data, client_address)

    def _process_join_request(self, data, client_address):
        if len(data) != 2 and data[1] not in [0x00, 0x01, 0x02]:
            return 2

        if self._verify_participants(client_address):
            return 3
        
        role = data[1]

        if role == 0x00:
            self.watchers.append(client_address)
            return

        message = self._fill_cman_or_ghost(role, client_address)
        if self.cman is not None and self.ghost is not None and (self.game_status == GameStatus.PREGAME):
            self.game_status = GameStatus.WAITING
            self.game.next_round()

        return message

    def _fill_cman_or_ghost(self, role, client_address):
        if role == 0x01 and not self.cman:
            print(f"Cman {client_address} joined")
            self.cman = client_address
            return

        if role == 0x02 and not self.ghost:
            print(f"Ghost {client_address} joined")
            self.ghost = client_address
            return

        return 4 if role == 0x01 else 5

    # Move requests
    def _process_player_movement_request(self, data, client_address):
        if self.game_status == GameStatus.PREGAME:
            return 6

        if len(data) != 2 and data[1] not in [0x00, 0x01, 0x02, 0x03]:
            return 7

        if client_address in self.watchers:
            return 8

        player_to_move = Player.CMAN if self.cman == client_address else Player.SPIRIT

        direction_to_move = data[1]

        move_applied, changed_status = self._has_game_change_mode(player_to_move, direction_to_move)

        if self.game.get_winner() != Player.NONE:
            self.game_status = GameStatus.END
            return

        if self.game_status == GameStatus.PLAYING and changed_status:
            self.game_status = GameStatus.START
            return

        if move_applied:
            self.game_status = GameStatus.PLAYING

    # Quit
    def _process_quit_request(self, data, client_address):
        if len(data) > 1:
            return 9

        if client_address in self.watchers:
            self.watchers.remove(client_address)

        if self.game_status == GameStatus.PREGAME:
            if client_address == self.cman:
                self.cman = None
            else:
                self.ghost = None
        else:
            winner = 1 if client_address == self.cman else 0
            self.game.declare_winner(winner)
            self.game_status = GameStatus.END

    def _verify_participants(self, client_address):
        return self.cman == client_address or self.ghost == client_address or client_address in self.watchers

    def _send_status_message(self):
        if self.game_status == GameStatus.END:
            self._send_winning_status()
            return
        self._send_game_stats()

    def _send_winning_status(self):
        print("Sending winning status")
        winner = 0x01 if self.game.get_winner() == 0 else 0x02
        lives, score = self.game.get_game_progress()

        message = _create_bytes_message(GAME_END, winner, _lives_to_catches(lives), score)

        players = [self.cman, self.ghost]

        for _ in range(10):
            for watcher in self.watchers:
                self._send_message(message, watcher)

            for player in players:
                if player is not None:
                    self._send_message(message, player)

            time.sleep(1.0)

        print("Game ended. New game starting...")
        self.game.restart_game()
        self.ghost = None
        self.cman = None
        self.watchers = []

        self.game_status = GameStatus.PREGAME

    def _send_error_message(self, error, client):
        message = _create_bytes_message(ERROR, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, error)
        self._send_message(message, client)

    def _send_game_stats(self):
        freeze_status_list = [GameStatus.PREGAME, GameStatus.WAITING, GameStatus.START]
        should_cman_freeze = 0x01 if self.game_status == GameStatus.PREGAME else 0x00
        should_ghost_freeze = 0x01 if self.game_status in freeze_status_list else 0x00

        lives, _ = self.game.get_game_progress()
        attempts = _lives_to_catches(lives)

        cords = self.game.get_current_players_coords()
        cman_cords, ghost_cords = cords[0], cords[1]

        points = self.game.get_points()
        converted_points = _convert_point_map_to_byte_stream(points)

        for watcher in self.watchers:
            message = _create_bytes_message(GAME_STATE_UPDATE, 0x01, *cman_cords, *ghost_cords, attempts, *converted_points)
            self._send_message(message, watcher)

        if self.cman is not None:
            cman_message = _create_bytes_message(GAME_STATE_UPDATE, should_cman_freeze, *cman_cords, *ghost_cords, attempts, *converted_points)
            self._send_message(cman_message, self.cman)

        if self.ghost is not None:
            ghost_message = _create_bytes_message(GAME_STATE_UPDATE, should_ghost_freeze, *cman_cords, *ghost_cords, attempts, *converted_points)
            self._send_message(ghost_message, self.ghost)

    def _send_message(self, message, client):
        try:
            self.server_socket.sendto(message, client)
        except socket.error as e:
            print(f'Failed to send message to {client}. Error: {e}\nExiting...')
            exit()

    def _has_game_change_mode(self, player_to_move, direction_to_move):
        before_lives, _ = self.game.get_game_progress()
        move_applied = self.game.apply_move(player_to_move, direction_to_move)
        after_lives, _ = self.game.get_game_progress()
        return move_applied, before_lives != after_lives


def _get_data_prefix(data):
    prefix = data[0]
    if prefix == JOIN:
        return JOIN
    elif prefix == PLAYER_MOVEMENT:
        return PLAYER_MOVEMENT
    elif prefix == QUIT:
        return QUIT
    return ERROR


def _create_bytes_message(*args):
    return bytes(args)


def _convert_point_map_to_byte_stream(points_dict):
    bit_list = []
    for coord in sorted(points_dict.keys(), key=lambda c: (c[0], c[1])):
        bit_list.append(1 - points_dict[coord])

    byte_list = [int(''.join(map(str, bit_list[i:i + 8])), 2) for i in range(0, 40, 8)]
    return byte_list


def _lives_to_catches(lives):
    return MAX_ATTEMPTS - lives

