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
        self._connection = connection
        self._player.initialize_board(ship_sizes)

        protocol.GameConfigMessage(ship_sizes).send_to_socket(connection)
        protocol.GameStartMessage().send_to_socket(connection)

        self._wait_for_start_response(connection)
        self._attack_loop(attacking_first=True)

    def run_passive(self, connection: socket.socket):
        self._connection = connection

        ship_sizes = protocol.GameConfigMessage.recv_from_socket(connection).ship_sizes
        self._player.initialize_board(ship_sizes)
        protocol.GameStartMessage().send_to_socket(connection)

        self._wait_for_start_response(connection)
        self._attack_loop(attacking_first=False)

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
        should_receive_attack = not attacking_first
        while self._connection.fileno() != _CLOSED_SOCKET_FILENO:
            if should_receive_attack:
                attack_response = self._receive_attacks()
            else:
                attack_response = self._send_attacks()

            if attack_response == protocol.AttackResponse.GAME_END:
                self._connection.close()
                break

            should_receive_attack = not should_receive_attack

    def _receive_attacks(self):
        """
        Receive attacks from the game's connection. Will receive one attack, and if it hit will receive another one.
        :return: The response for the latest attack
        """

        attack_message = protocol.AttackMessage.recv_from_socket(self._connection)
        attack_response = self._player.respond_to_attack(attack_message.coordinates)
        protocol.AttackResponseMessage(attack_response).send_to_socket(self._connection)

        if attack_response in (protocol.AttackResponse.HIT, protocol.AttackResponse.DISABLED_SHIP):
            attack_response = self._receive_attacks()
        return attack_response

    def _send_attacks(self):
        """
        Send attacks through the game's connection. Will send one attack, and if it hit will send another one.
        :return: The response for the latest attack
        """
        protocol.AttackMessage(self._player.attack()).send_to_socket(self._connection)
        attack_response = protocol.AttackResponseMessage.recv_from_socket(self._connection)

        if attack_response in (protocol.AttackResponse.HIT, protocol.AttackResponse.DISABLED_SHIP):
            attack_response = self._send_attacks()
        return attack_response
