import struct
from enum import IntEnum
from socket import socket
from typing import NamedTuple, Sequence

_NETWORK_BYTE_ORDER = "big"
GAME_START_CONSTANT = 0xFF

Range = NamedTuple("Range", (("min", int), ("max", int)))
BOARD_ROW_RANGE = Range(1, 10)
BOARD_COLUMN_RANGE = Range(1, 10)

Coordinates = NamedTuple("Coordinates", (("vertical", int), ("horizontal", int)))


class AttackResponse(IntEnum):
    MISSED = 1
    HIT = 2
    DISABLED_SHIP = 3
    GAME_END = 0xFF


class GameConfigMessage:
    def __init__(self, ship_sizes: Sequence[int]):
        self.ship_sizes = list(ship_sizes)

    def send_to_socket(self, socket_: socket):
        ships = len(self.ship_sizes)
        struct_format = "!B" + "B" * ships
        encoded_message = struct.pack(struct_format, ships, *self.ship_sizes)
        socket_.sendall(encoded_message)

    @classmethod
    def recv_from_socket(cls, socket_: socket):
        ships = int.from_bytes(socket_.recv(1), byteorder=_NETWORK_BYTE_ORDER, signed=False)
        ship_sizes_format = "B" * ships
        encoded_ship_sizes = socket_.recv(struct.calcsize(ship_sizes_format))
        ship_sizes = struct.unpack(ship_sizes_format, encoded_ship_sizes)
        return cls(ship_sizes)


class GameStartMessage:
    def __init__(self, value: int = GAME_START_CONSTANT):
        self.value = value

    def send_to_socket(self, socket_: socket):
        socket_.sendall(int.to_bytes(self.value, length=1, byteorder=_NETWORK_BYTE_ORDER))

    @classmethod
    def recv_from_socket(cls, socket_: socket):
        value = int.from_bytes(socket_.recv(1), byteorder=_NETWORK_BYTE_ORDER, signed=False)
        return cls(value)


class AttackMessage:
    _struct_format = "!B"
    _vertical_bit_shift = 4

    def __init__(self, coordinates: Coordinates):
        self.coordinates = coordinates

    def send_to_socket(self, socket_: socket):
        encoded_message = struct.pack(self.__class__._struct_format,
                                      (self.coordinates.vertical << self.__class__._vertical_bit_shift) +
                                      self.coordinates.horizontal)
        socket_.sendall(encoded_message)

    @classmethod
    def recv_from_socket(cls, socket_: socket):
        struct_size = struct.calcsize(cls._struct_format)
        coordinates_byte, *_ = struct.unpack(cls._struct_format, socket_.recv(struct_size))
        coordinates = Coordinates(coordinates_byte >> cls._vertical_bit_shift,
                                  coordinates_byte & (0b11111111 >> cls._vertical_bit_shift))
        return cls(coordinates)


class AttackResponseMessage:
    _struct_format = "!B"

    def __init__(self, response: AttackResponse):
        self.response = response

    def send_to_socket(self, socket_: socket):
        encoded_message = struct.pack(self._struct_format, self.response.value)
        socket_.sendall(encoded_message)

    @classmethod
    def recv_from_socket(cls, socket_: socket):
        encoded_response = socket_.recv(struct.calcsize(cls._struct_format))
        response_value, *_ = struct.unpack(cls._struct_format, encoded_response)
        return cls(AttackResponse(response_value))
