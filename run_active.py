from battleshipp import GameClient, InteractivePlayer
from battleshipp.protocol import PORT as PROTOCOL_PORT
from battleshipp.game_defaults import SHIP_SIZES
import socket

ENEMY_ADDRESS = "127.0.0.1"


def main():
    player = InteractivePlayer()
    player_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    player_socket.connect((ENEMY_ADDRESS, PROTOCOL_PORT))
    game = GameClient(player)
    game.run_active(player_socket, SHIP_SIZES)


if __name__ == "__main__":
    main()
