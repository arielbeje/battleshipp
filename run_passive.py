from battleshipp.player import InteractivePlayer
from battleshipp.game_client import GameClient
from battleshipp.protocol import PORT as PROTOCOL_PORT
import socket


def main():
    player = InteractivePlayer()
    player_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    player_socket.bind(("", PROTOCOL_PORT))
    player_socket.listen(1)
    enemy_socket, _ = player_socket.accept()
    game = GameClient(player)
    game.run_passive(enemy_socket)


if __name__ == "__main__":
    main()
