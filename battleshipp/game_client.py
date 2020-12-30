import socket
from collections import Sequence

from .player import BasePlayer
from . import protocol
from .exceptions import InvalidStartMessageError

_CLOSED_SOCKET_FILENO = -1


class GameClient:
    def __init__(self, player: BasePlayer):
        self._player = player
        self._connection = None

    def run_active(self, connection: socket.socket, ship_sizes: Sequence[int]):
        """
        Run an active game client, which will send the given configuration to the connection and start a game.
        The client's player will attack first.
        """

        self._connection = connection
        self._player.initialize_board(ship_sizes)

        protocol.GameConfigMessage(ship_sizes).send_to_socket(connection)
        protocol.GameStartMessage().send_to_socket(connection)

        self._wait_for_start_response(connection)
        self._attack_loop(attacking_first=False)

    def run_passive(self, connection: socket.socket):
        """
        Run a passive game client, which will wait to receive a game configuration from the connection.
        The client's player will attack second.
        """

        self._connection = connection

        ship_sizes = protocol.GameConfigMessage.recv_from_socket(connection).ship_sizes
        self._player.initialize_board(ship_sizes)
        protocol.GameStartMessage().send_to_socket(connection)

        self._wait_for_start_response(connection)
        self._attack_loop(attacking_first=True)

    def _wait_for_start_response(self, connection):
        """
        Waits for a proper game start message from the given connection

        :raise InvalidStartMessageError:
        """
        received_game_start_message = protocol.GameStartMessage.recv_from_socket(connection)
        if received_game_start_message.value != protocol.GAME_START_CONSTANT:
            self._connection.close()
            raise InvalidStartMessageError(f"Expected a value of {hex(protocol.GAME_START_CONSTANT)}, "
                                           f"got {received_game_start_message.value}")

    def _attack_loop(self, attacking_first: bool):
        """
        The game's attack loop. Will handle sending and receiving attacks in the correct order.
        """

        should_attack = attacking_first
        try:
            while self._connection.fileno() != _CLOSED_SOCKET_FILENO:
                if should_attack:
                    attack_response = self._send_attack()
                else:
                    attack_response = self._receive_attack()

                if attack_response in (protocol.AttackResponse.HIT, protocol.AttackResponse.DISABLED_SHIP):
                    if should_attack:
                        attack_response = self._send_attack()
                    else:
                        attack_response = self._receive_attack()

                if attack_response == protocol.AttackResponse.GAME_END:
                    self._connection.close()
                    break

                should_attack = not should_attack
        except ConnectionResetError:
            print("Game ended. You are the winner!")

    def _receive_attack(self):
        """
        Receive an attack from the game's connection.
        :return: The attack's result
        """

        attack_message = protocol.AttackMessage.recv_from_socket(self._connection)
        attack_response = self._player.respond_to_attack(attack_message.coordinates)
        protocol.AttackResponseMessage(attack_response).send_to_socket(self._connection)

        return attack_response

    def _send_attack(self):
        """
        Send an attack through the game's connection.
        :return: The attack's response
        """

        attack_coordinates = self._player.attack()
        protocol.AttackMessage(attack_coordinates).send_to_socket(self._connection)
        attack_response = protocol.AttackResponseMessage.recv_from_socket(self._connection).response
        self._player.process_attack_result(attack_coordinates, attack_response)

        return attack_response
