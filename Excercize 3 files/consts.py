SERVER_ADDR = '0.0.0.0'
DEFAULT_PORT = 1337
BUFFER_SIZE = 1024

#OPCODE
JOIN = 0x00
PLAYER_MOVEMENT = 0x01
QUIT = 0x0F
GAME_STATE_UPDATE = 0X80
GAME_END = 0x8F
ERROR = 0xFF

MAP_PATH = './map.txt'

ERROR_DICT = [
    'bad format error, message prefix is not correct',
    'Unknown client',
    'bad format error, join request role is not correct',
    'Client is already in the game',
    'cman position is already taken',
    'ghost position is already taken',
    "Game not started yet, can't move",
    'bad format error, move is not correct',
    'Non players are not allowed to send move commands',
    'bad format error, quit request is not correct'
]
